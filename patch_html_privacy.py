import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

toggle_html = """
            <div class="flex items-center justify-between border-t-4 border-border pt-6">
                <label class="text-xs font-bold text-textMain uppercase tracking-widest flex items-center gap-2">
                    <i class="fa-solid fa-ghost"></i> Chế độ riêng tư
                </label>
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" id="set-privacy" class="sr-only peer">
                    <div class="w-14 h-7 bg-border border-2 border-textMain peer-focus:outline-none peer-checked:bg-primary after:content-[''] after:absolute after:top-[4px] after:left-[4px] after:bg-textMain after:border-2 after:border-textMain after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-7"></div>
                </label>
            </div>
"""

if 'id="set-privacy"' not in text:
    text = text.replace('            <div class="border-t-4 border-border pt-6 flex flex-col gap-2">', toggle_html + '\n            <div class="border-t-4 border-border pt-6 flex flex-col gap-2">')

# JS Loading
if "document.getElementById('set-privacy').checked" not in text:
    text = text.replace("document.getElementById('set-camera-src').value = data.camera_source !== undefined ? data.camera_source : '';", "document.getElementById('set-camera-src').value = data.camera_source !== undefined ? data.camera_source : '';\n            document.getElementById('set-privacy').checked = data.privacy_mode === true;")

# JS Saving
if "privacy_mode: document.getElementById('set-privacy').checked" not in text:
    text = text.replace("camera_source: document.getElementById('set-camera-src').value,", "camera_source: document.getElementById('set-camera-src').value,\n                privacy_mode: document.getElementById('set-privacy').checked,")

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('UI Patched with Privacy Toggle')
