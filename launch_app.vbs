Set WshShell = CreateObject("WScript.Shell")

' 1. Chạy AI Server ẩn hoàn toàn không hiện bảng đen Terminal
WshShell.Run "cmd /c set PYTHONIOENCODING=utf-8 && .\.venv\Scripts\pythonw.exe main.py --dashboard --no-display", 0, False

' 2. Chờ 3 giây để server nạp mô hình AI
WScript.Sleep 3000

' 3. Mở giao diện App bằng Microsoft Edge (có sẵn trên mọi Windows) ở chế độ App Mode (không có thanh tab/URL)
WshShell.Run "msedge --app=http://localhost:5000/?v=2.0", 1, False
