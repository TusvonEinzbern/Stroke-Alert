import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_header = '''<div class="p-4 border-b-4 border-textMain flex justify-between items-center bg-background">
            <h2 class="text-xl font-black text-textMain uppercase tracking-widest"><i class="fa-solid fa-chart-line mr-3"></i>Hồ Sơ Y Tế & Thống Kê</h2>
            <button id="close-stats" class="w-10 h-10 btn-ui flex justify-center items-center text-textMain hover:bg-textMain hover:text-surface"><i class="fa-solid fa-xmark text-xl"></i></button>
        </div>'''

new_header = '''<div class="p-4 border-b-4 border-textMain flex justify-between items-center bg-background">
            <h2 class="text-xl font-black text-textMain uppercase tracking-widest"><i class="fa-solid fa-chart-line mr-3"></i>Hồ Sơ Y Tế & Thống Kê</h2>
            <div class="flex items-center gap-4">
                <a href="/api/export_csv" class="btn-ui px-4 py-2 text-sm text-textMain hover:bg-textMain hover:text-surface bg-primary font-bold">
                    <i class="fa-solid fa-file-csv mr-2"></i> Xuất Excel (CSV)
                </a>
                <button id="close-stats" class="w-10 h-10 btn-ui flex justify-center items-center text-textMain hover:bg-textMain hover:text-surface"><i class="fa-solid fa-xmark text-xl"></i></button>
            </div>
        </div>'''

if 'Xuất Excel' not in text:
    text = text.replace(old_header, new_header)
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Patched index.html with Export button')
else:
    print('Export button already exists')
