with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Add button
if 'id="stats-toggle"' not in text:
    btn_html = '''            <button id="stats-toggle" class="btn-ui px-4 py-2 text-sm text-textMain hover:bg-background">
                <i class="fa-solid fa-chart-simple"></i> Báo Cáo
            </button>'''
    text = text.replace('<button id="settings-toggle"', btn_html + '\n            <button id="settings-toggle"')

# Add Modal
modal_html = '''
    <!-- Stats Modal -->
    <div id="stats-overlay" class="fixed inset-0 bg-black/50 z-[100] hidden backdrop-blur-sm transition-opacity"></div>
    <div id="stats-modal" class="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-11/12 max-w-4xl bg-surface border-4 border-textMain shadow-hard z-[101] hidden flex-col max-h-[90vh]">
        <div class="p-4 border-b-4 border-textMain flex justify-between items-center bg-background">
            <h2 class="text-xl font-black text-textMain uppercase tracking-widest"><i class="fa-solid fa-chart-line mr-3"></i>Hồ Sơ Y Tế & Thống Kê</h2>
            <button id="close-stats" class="w-10 h-10 btn-ui flex justify-center items-center text-textMain hover:bg-textMain hover:text-surface"><i class="fa-solid fa-xmark text-xl"></i></button>
        </div>
        <div class="p-6 overflow-y-auto bg-surface flex-grow flex flex-col gap-6">
            <div class="card-ui p-4 bg-background">
                <h3 class="text-sm font-bold text-textMain uppercase mb-4 tracking-wider">Tần suất sự cố (7 ngày qua)</h3>
                <div class="w-full h-64">
                    <canvas id="stats-chart"></canvas>
                </div>
            </div>
        </div>
    </div>
'''

if 'id="stats-modal"' not in text:
    text = text.replace('<!-- Settings Drawer -->', modal_html + '\n    <!-- Settings Drawer -->')

# Add JS logic
js_logic = '''
        // Stats Logic
        const statsModal = document.getElementById('stats-modal');
        const statsOverlay = document.getElementById('stats-overlay');
        let chartInstance = null;

        document.getElementById('stats-toggle').onclick = () => {
            statsModal.classList.remove('hidden');
            statsModal.classList.add('flex');
            statsOverlay.classList.remove('hidden');
            
            fetch('/api/stats').then(r=>r.json()).then(data => {
                const labels = Object.keys(data);
                const criticalData = labels.map(l => data[l].critical || 0);
                const highData = labels.map(l => data[l].high || 0);
                const medData = labels.map(l => data[l].medium || 0);
                
                const ctx = document.getElementById('stats-chart').getContext('2d');
                if(chartInstance) chartInstance.destroy();
                
                chartInstance = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'CRITICAL (Ngã/Đột quỵ)', data: criticalData, backgroundColor: '#dc2626', borderWidth: 2, borderColor: '#3e2a14' },
                            { label: 'HIGH (Cần chú ý)', data: highData, backgroundColor: '#ea580c', borderWidth: 2, borderColor: '#3e2a14' },
                            { label: 'MEDIUM (Bất thường nhẹ)', data: medData, backgroundColor: '#f59e0b', borderWidth: 2, borderColor: '#3e2a14' }
                        ]
                    },
                    options: {
                        responsive: true, maintainAspectRatio: false,
                        scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true, ticks: { stepSize: 1 } } },
                        plugins: { legend: { labels: { font: { family: 'Space Grotesk', weight: 'bold' } } } }
                    }
                });
            });
        };
        const closeStats = () => { statsModal.classList.add('hidden'); statsModal.classList.remove('flex'); statsOverlay.classList.add('hidden'); };
        document.getElementById('close-stats').onclick = closeStats;
        statsOverlay.onclick = closeStats;
'''

if 'const statsModal' not in text:
    text = text.replace('// 6. Dashboard Updates & Visual Alarms', js_logic + '\n        // 6. Dashboard Updates & Visual Alarms')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('UI Patched')
