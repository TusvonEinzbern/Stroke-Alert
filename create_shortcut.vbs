Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oShellLink = WshShell.CreateShortcut(strDesktop & "\Du An Nguoi Bat An.lnk")
oShellLink.TargetPath = "wscript.exe"
oShellLink.Arguments = "D:\ASD\launch_app.vbs"
oShellLink.WindowStyle = 1
oShellLink.IconLocation = "D:\ASD\static\icon.ico"
oShellLink.WorkingDirectory = "D:\ASD"
oShellLink.Save
WScript.Echo "Shortcut created successfully on " & strDesktop
