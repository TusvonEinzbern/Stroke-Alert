with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Add Blackbox Button
if 'id="blackbox-toggle"' not in text:
    btn_html = '''            <button id="blackbox-toggle" class="btn-ui px-4 py-2 text-sm text-textMain hover:bg-background">
                <i class="fa-solid fa-video"></i> Hộp Đen
            </button>'''
    text = text.replace('<button id="stats-toggle"', btn_html + '\n            <button id="stats-toggle"')

# Add Blackbox Modal
modal_html = '''
    <!-- Blackbox Modal -->
    <div id="blackbox-overlay" class="fixed inset-0 bg-black/50 z-[100] hidden backdrop-blur-sm transition-opacity"></div>
    <div id="blackbox-modal" class="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-11/12 max-w-4xl bg-surface border-4 border-textMain shadow-hard z-[101] hidden flex-col max-h-[90vh]">
        <div class="p-4 border-b-4 border-textMain flex justify-between items-center bg-background">
            <h2 class="text-xl font-black text-textMain uppercase tracking-widest"><i class="fa-solid fa-tape mr-3"></i>Hộp Đen Tiền Sự Cố</h2>
            <button id="close-blackbox" class="w-10 h-10 btn-ui flex justify-center items-center text-textMain hover:bg-textMain hover:text-surface"><i class="fa-solid fa-xmark text-xl"></i></button>
        </div>
        <div class="p-6 overflow-y-auto bg-surface flex-grow flex flex-col gap-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="records-grid">
                <!-- Records injected here -->
                <p class="text-textMuted font-bold">Chưa có bản ghi nào.</p>
            </div>
        </div>
    </div>
'''

if 'id="blackbox-modal"' not in text:
    text = text.replace('<!-- Stats Modal -->', modal_html + '\n    <!-- Stats Modal -->')

# Add JS Logic
js_logic = '''
        // Blackbox Logic
        const bbModal = document.getElementById('blackbox-modal');
        const bbOverlay = document.getElementById('blackbox-overlay');
        document.getElementById('blackbox-toggle').onclick = () => {
            bbModal.classList.remove('hidden'); bbModal.classList.add('flex');
            bbOverlay.classList.remove('hidden');
            fetch('/api/records').then(r=>r.json()).then(data => {
                const grid = document.getElementById('records-grid');
                if(!data || data.length === 0) {
                    grid.innerHTML = '<p class="text-textMuted font-bold uppercase col-span-2 text-center py-8">CHƯA CÓ BẢN GHI SỰ CỐ NÀO</p>';
                    return;
                }
                let html = '';
                data.forEach(url => {
                    const filename = url.split('/').pop();
                    const ts = filename.replace('incident_', '').replace('.mp4', '');
                    const date = new Date(parseInt(ts)*1000).toLocaleString('vi-VN');
                    html += `
                    <div class="card-ui p-2 bg-background flex flex-col">
                        <div class="bg-textMain text-surface px-2 py-1 text-xs font-bold uppercase tracking-wider mb-2 flex justify-between">
                            <span>CRITICAL</span><span>${date}</span>
                        </div>
                        <video src="${url}" controls class="w-full aspect-video border-2 border-textMain bg-black"></video>
                    </div>`;
                });
                grid.innerHTML = html;
            });
        };
        const closeBB = () => { bbModal.classList.add('hidden'); bbModal.classList.remove('flex'); bbOverlay.classList.add('hidden'); };
        document.getElementById('close-blackbox').onclick = closeBB;
        bbOverlay.onclick = closeBB;
'''

if 'const bbModal' not in text:
    text = text.replace('// Stats Logic', js_logic + '\n        // Stats Logic')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Blackbox UI Patched")
