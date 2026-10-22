Option Explicit
Dim a, p
Set a = CreateObject("PowerPoint.Application")
Set p = a.Presentations.Open("C:\Users\100550934\AppData\Local\Temp\deck_check.pptx", True, False, False)
WScript.Echo "slides=" & p.Slides.Count
p.Export "C:\Users\100550934\AppData\Local\Temp\deck_png", "PNG", 1600, 900
p.SaveAs "C:\Users\100550934\AppData\Local\Temp\deck_check.pdf", 32
p.Close
a.Quit
WScript.Echo "ok"
