with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start = -1
end = -1
for i, l in enumerate(lines):
    if 'btnPip.onclick = async () => {' in l:
        start = i
    if start != -1 and i > start and '};' in l:
        end = i
        break

if start != -1 and end != -1:
    new_js = '''        btnPip.onclick = async () => {
            if (window.documentPictureInPicture) {
                try {
                    const pipWindow = await window.documentPictureInPicture.requestWindow({
                        width: 640,
                        height: 480
                    });
                    
                    const pipCanvasLocal = document.createElement('canvas');
                    pipCanvasLocal.width = 640; pipCanvasLocal.height = 480;
                    pipCanvasLocal.style.width = '100%';
                    pipCanvasLocal.style.height = '100%';
                    pipCanvasLocal.style.objectFit = 'cover';
                    pipWindow.document.body.style.margin = '0';
                    pipWindow.document.body.appendChild(pipCanvasLocal);
                    const pipCtxLocal = pipCanvasLocal.getContext('2d');
                    
                    function pipLoopLocal() {
                        pipCtxLocal.drawImage(videoEl, 0, 0, pipCanvasLocal.width, pipCanvasLocal.height);
                        safeZones.forEach(z => {
                            const w = pipCanvasLocal.width; const h = pipCanvasLocal.height;
                            pipCtxLocal.fillStyle = "rgba(16, 185, 129, 0.2)";
                            pipCtxLocal.strokeStyle = "#10b981";
                            pipCtxLocal.lineWidth = 2;
                            pipCtxLocal.strokeRect(z.x1*w, z.y1*h, (z.x2-z.x1)*w, (z.y2-z.y1)*h);
                        });
                        if (!pipWindow.closed) requestAnimationFrame(pipLoopLocal);
                    }
                    pipLoopLocal();
                } catch (err) {
                    alert("Lỗi PiP: " + err.message);
                }
            } else {
                alert("Trình duyệt Edge của bạn không hỗ trợ tính năng Document PiP mới nhất (Yêu cầu bản cập nhật mới)!");
            }
        };
'''
    lines[start:end+1] = [new_js]
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('Patched correctly via python script!')
else:
    print('Failed to find bounds!')
