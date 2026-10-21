# -*- coding: utf-8 -*-
"""用本机 PowerPoint 把 pptx 导出为 PNG（每页一张），供视觉核对"""
import os, sys, glob
import win32com.client

PPTX = sys.argv[1] if len(sys.argv) > 1 else r"E:\Desktop\RFID读取评估_2026-10-21\09_报告\RFID读取能力评估_2026-10-21.pptx"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else r"E:\Desktop\RFID读取评估_2026-10-21\09_报告\_render"

os.makedirs(OUTDIR, exist_ok=True)
for f in set(glob.glob(os.path.join(OUTDIR, "*.PNG")) + glob.glob(os.path.join(OUTDIR, "*.png"))):
    os.remove(f)

app = win32com.client.Dispatch("PowerPoint.Application")
pres = app.Presentations.Open(os.path.abspath(PPTX), ReadOnly=True, WithWindow=False)
pres.Export(os.path.abspath(OUTDIR), "PNG", 1600, 900)
pres.Close()
app.Quit()
files = sorted(glob.glob(os.path.join(OUTDIR, "*.PNG")) + glob.glob(os.path.join(OUTDIR, "*.png")))
print(len(files), "pages exported")
for f in files:
    print(f, os.path.getsize(f))
