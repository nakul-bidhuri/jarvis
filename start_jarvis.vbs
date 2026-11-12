' start_jarvis.vbs
' Double-click this (or put a shortcut to it in shell:startup) and Jarvis
' launches completely invisibly — no console window, no taskbar icon,
' mic listening only for "Hey Jarvis" until you speak.

Set objShell = CreateObject("WScript.Shell")
projectPath = "D:\Jarvis"
objShell.CurrentDirectory = projectPath
objShell.Run "pythonw main.pyw", 0, False
