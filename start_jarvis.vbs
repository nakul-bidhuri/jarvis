' start_jarvis.vbs
' Launches Jarvis silently in background mode without a console window.
' Controls: Press [Ctrl + Alt + J] to start listening; press [Ctrl + Alt + J] to close.

Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
objShell.CurrentDirectory = scriptDir
objShell.Run "pythonw main.pyw", 0, False
