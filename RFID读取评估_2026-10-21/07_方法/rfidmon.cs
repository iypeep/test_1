// rfidmon.cs - remote-controllable LLRP reader client (MultiReader replacement).
//
// The Impinj reader accepts exactly one LLRP client. This tool connects once and
// holds the session, records every tag it sees to the share, and lets the
// operator pause/release remotely. If another client takes the session, it
// retries until it gets it back.
//
// Build on the machine (SDK lives at D:\Ben Read RFID):
//   csc /nologo /target:exe /platform:anycpu /optimize+ /main:RfidMon /out:rfidmon.exe
//       /r:Impinj.OctaneSdk.dll /r:LLRP.dll /r:LLRP.Impinj.dll rfidmon.cs
//
// Run:
//   rfidmon.exe --ip 192.168.1.100 --dir "<share>\machines\<M>\rfid"
//
//   <dir>\control.json  {"mode":"record"|"pause"|"stop"}   (we write this remotely)
//   <dir>\status.json    health, rewritten every cycle
//   <dir>\live.txt       last 40 reads, plain text
//   <dir>\records-YYYYMMDD.jsonl  every tag read, one JSON object per line

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Threading;
using Impinj.OctaneSdk;

static class RfidMon
{
    static string Ip = "192.168.1.100";
    static string OutDir = "";
    static string LocalDir = "";
    static string Mode = "record";

    static ImpinjReader _r = null;
    static string _state = "starting";
    static string _err = "";
    static long _total = 0;
    static long _sinceStatus = 0;
    static string _lastTag = "";
    static readonly Dictionary<string, int> _distinct = new Dictionary<string, int>();
    static readonly List<string> _live = new List<string>();
    static readonly object _lk = new object();
    static readonly string _started = DateTime.Now.ToString("s");
    static int _batches = 0;

    static void Log(string m)
    {
        try
        {
            if (LocalDir == null || LocalDir.Length == 0) return;
            Directory.CreateDirectory(LocalDir);
            File.AppendAllText(Path.Combine(LocalDir, "rfidmon.log"),
                DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + " " + m + "\r\n", Encoding.ASCII);
        }
        catch { }
    }

    static string Esc(string s)
    {
        return s == null ? "" : s.Replace("\\", "\\\\").Replace("\"", "\\\"");
    }

    static int Main(string[] args)
    {
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--ip" && i + 1 < args.Length) Ip = args[++i];
            else if (args[i] == "--dir" && i + 1 < args.Length) OutDir = args[++i];
            else if (args[i] == "--local" && i + 1 < args.Length) LocalDir = args[++i];
        }
        if (OutDir.Length == 0) { Console.Error.WriteLine("need --dir"); return 2; }
        if (LocalDir.Length == 0)
            LocalDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "OMPRemote", "rfid");
        try { Directory.CreateDirectory(OutDir); } catch { }
        try { Directory.CreateDirectory(LocalDir); } catch { }

        // single instance
        string lockFile = Path.Combine(LocalDir, "rfidmon.lock");
        try
        {
            if (File.Exists(lockFile))
            {
                int oldPid = 0;
                int.TryParse(File.ReadAllText(lockFile).Trim().Split(' ')[0], out oldPid);
                if (oldPid > 0)
                {
                    try { System.Diagnostics.Process.GetProcessById(oldPid); Console.Error.WriteLine("already running"); return 0; }
                    catch { }
                }
            }
            File.WriteAllText(lockFile, System.Diagnostics.Process.GetCurrentProcess().Id + " " + DateTime.Now.ToString("s"));
        }
        catch { }

        Log("start ip=" + Ip + " dir=" + OutDir);
        WriteStatus();

        while (true)
        {
            ReadControl();
            if (Mode == "stop") { Log("stop requested"); Release("stop"); break; }

            if (Mode == "pause")
            {
                if (_r != null) Release("pause");
                _state = "paused";
                WriteStatus();
                Thread.Sleep(1500);
                continue;
            }

            try
            {
                if (_r == null)
                {
                    _state = "connecting";
                    WriteStatus();
                    _r = new ImpinjReader();
                    _r.Connect(Ip);
                    try { ApplyReportSettings(); } catch (Exception se) { _err = "settings: " + se.Message; }
                    _state = "recording";
                    _err = "";
                    Log("connected " + Ip);
                }

                TagReport rep = _r.QueryTags(1.0);
                _batches++;
                if (rep != null && rep.Tags != null)
                {
                    foreach (Tag t in rep.Tags) Emit(t);
                }
                WriteLive();
                WriteStatus();
            }
            catch (Exception ex)
            {
                _err = ex.Message;
                _state = "error";
                Log("query error: " + ex.Message);
                Release("error");
                WriteStatus();
                Thread.Sleep(2500);
            }
        }

        try { File.Delete(lockFile); } catch { }
        return 0;
    }

    static void ApplyReportSettings()
    {
        Settings st = _r.QueryDefaultSettings();
        st.Report.IncludeAntennaPortNumber = true;
        st.Report.IncludePeakRssi = true;
        st.Report.IncludeSeenCount = true;
        st.Report.IncludeFirstSeenTime = true;
        st.Report.IncludeLastSeenTime = true;
        _r.ApplySettings(st);
    }

    static void ReadControl()
    {
        try
        {
            string p = Path.Combine(OutDir, "control.json");
            if (!File.Exists(p)) return;
            string txt = File.ReadAllText(p);
            string m = Grab(txt, "mode");
            if (m == "record" || m == "pause" || m == "stop") Mode = m;
        }
        catch { }
    }

    static string Grab(string json, string key)
    {
        int i = json.IndexOf("\"" + key + "\"", StringComparison.Ordinal);
        if (i < 0) return "";
        int c = json.IndexOf(':', i);
        if (c < 0) return "";
        int q1 = json.IndexOf('"', c + 1);
        if (q1 < 0) return "";
        int q2 = json.IndexOf('"', q1 + 1);
        if (q2 < 0) return "";
        return json.Substring(q1 + 1, q2 - q1 - 1);
    }

    static void Emit(Tag t)
    {
        try
        {
            string raw = t.Epc != null ? t.Epc.ToString() : "";
            string hex = raw.Replace(" ", "").ToUpperInvariant();
            string ascii = HexToAscii(hex);
            string now = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
            string line = "{\"t\":\"" + now + "\",\"epc\":\"" + hex + "\",\"ascii\":\"" + Esc(ascii) + "\"" +
                          ",\"ant\":" + t.AntennaPortNumber + ",\"rssi\":" + SafeRssi(t) + ",\"seen\":" + SafeSeen(t) + "}";
            File.AppendAllText(Path.Combine(OutDir, "records-" + DateTime.Now.ToString("yyyyMMdd") + ".jsonl"),
                line + "\r\n", Encoding.UTF8);
            lock (_lk)
            {
                _live.Add(now.Substring(11) + "  " + hex + (ascii.Length > 0 ? " (" + ascii + ")" : "") +
                          "  ant" + t.AntennaPortNumber + "  " + SafeRssi(t) + "dBm  x" + SafeSeen(t));
                while (_live.Count > 40) _live.RemoveAt(0);
                if (!_distinct.ContainsKey(hex)) _distinct[hex] = 0;
                _distinct[hex]++;
            }
            Interlocked.Increment(ref _total);
            Interlocked.Increment(ref _sinceStatus);
            _lastTag = now;
        }
        catch (Exception ex) { _err = "emit: " + ex.Message; }
    }

    static string HexToAscii(string hex)
    {
        try
        {
            if (hex.Length < 4 || hex.Length % 2 != 0) return "";
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i + 1 < hex.Length; i += 2)
            {
                int v = Convert.ToInt32(hex.Substring(i, 2), 16);
                if (v == 0) break;
                if (v < 32 || v > 126) return "";
                sb.Append((char)v);
            }
            return sb.ToString();
        }
        catch { return ""; }
    }

    static string SafeRssi(Tag t)
    {
        try { return t.IsPeakRssiInDbmPresent ? t.PeakRssiInDbm.ToString("0.0", CultureInfo.InvariantCulture) : ""; }
        catch { return ""; }
    }

    static string SafeSeen(Tag t)
    {
        try { return t.IsSeenCountPresent ? t.TagSeenCount.ToString() : ""; }
        catch { return ""; }
    }

    static void WriteLive()
    {
        try
        {
            string txt;
            lock (_lk) { txt = string.Join("\r\n", _live.ToArray()); }
            File.WriteAllText(Path.Combine(OutDir, "live.txt"), txt + "\r\n", Encoding.UTF8);
        }
        catch { }
    }

    static void WriteStatus()
    {
        try
        {
            long since = Interlocked.Exchange(ref _sinceStatus, 0);
            int distinct;
            lock (_lk) { distinct = _distinct.Count; }
            StringBuilder sb = new StringBuilder();
            sb.Append("{");
            sb.Append("\"ah\":1,\"ip\":\"").Append(Ip).Append("\",");
            sb.Append("\"mode\":\"").Append(Mode).Append("\",");
            sb.Append("\"state\":\"").Append(_state).Append("\",");
            sb.Append("\"connected\":").Append(_r != null && _r.IsConnected ? "true" : "false").Append(",");
            sb.Append("\"tags_total\":").Append(Interlocked.Read(ref _total)).Append(",");
            sb.Append("\"tags_last_poll\":").Append(since).Append(",");
            sb.Append("\"polls\":").Append(_batches).Append(",");
            sb.Append("\"distinct_epcs\":").Append(distinct).Append(",");
            sb.Append("\"last_tag_at\":\"").Append(_lastTag).Append("\",");
            sb.Append("\"last_error\":\"").Append(Esc(_err)).Append("\",");
            sb.Append("\"started_at\":\"").Append(_started).Append("\",");
            sb.Append("\"now\":\"").Append(DateTime.Now.ToString("s")).Append("\"");
            sb.Append("}");
            File.WriteAllText(Path.Combine(OutDir, "status.json"), sb.ToString() + "\r\n", Encoding.UTF8);
        }
        catch { }
    }

    static void Release(string why)
    {
        try
        {
            if (_r != null)
            {
                try { _r.Stop(); } catch { }
                try { _r.Disconnect(); } catch { }
            }
        }
        catch { }
        _r = null;
        _state = "released:" + why;
        Log("released (" + why + ")");
    }
}