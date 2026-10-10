import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

email_ui = '''
            <div class="border-t-4 border-border pt-6 flex flex-col gap-4">
                <h3 class="text-sm font-black text-textMain uppercase tracking-widest"><i class="fa-solid fa-address-card mr-2"></i> Hồ Sơ Bệnh Nhân</h3>
                <input type="text" id="set-patient-name" placeholder="Họ và tên..." class="w-full p-3 bg-background border-2 border-textMain font-mono text-sm text-textMain outline-none focus:ring-2 ring-primary">
                <div class="flex gap-4">
                    <input type="text" id="set-patient-age" placeholder="Tuổi..." class="w-1/3 p-3 bg-background border-2 border-textMain font-mono text-sm text-textMain outline-none focus:ring-2 ring-primary">
                    <input type="text" id="set-emergency-phone" placeholder="SĐT Khẩn cấp..." class="w-2/3 p-3 bg-background border-2 border-textMain font-mono text-sm text-textMain outline-none focus:ring-2 ring-primary">
                </div>
            </div>

            <div class="border-t-4 border-border pt-6 flex flex-col gap-4">
                <h3 class="text-sm font-black text-textMain uppercase tracking-widest"><i class="fa-solid fa-envelope mr-2"></i> Cảnh Báo Qua Email</h3>
                <input type="email" id="set-receiver-email" placeholder="Nhập Email người nhận..." class="w-full p-3 bg-background border-2 border-textMain font-mono text-sm text-textMain outline-none focus:ring-2 ring-primary">
                <div class="card-ui p-4 bg-border flex flex-col gap-2 mt-2">
                    <p class="text-[10px] text-textMain font-bold uppercase tracking-wider mb-2">Cấu hình gửi (SMTP Gmail)</p>
                    <input type="email" id="set-smtp-user" placeholder="Email người gửi (vd: abc@gmail.com)" class="w-full p-2 bg-background border-2 border-textMain font-mono text-xs text-textMain outline-none">
                    <input type="password" id="set-smtp-pass" placeholder="Mật khẩu ứng dụng (App Password)" class="w-full p-2 bg-background border-2 border-textMain font-mono text-xs text-textMain outline-none">
                </div>
            </div>
'''

if 'Hồ Sơ Bệnh Nhân' not in text:
    text = text.replace('            <!-- Ntfy Setup Box -->', email_ui + '\n            <!-- Ntfy Setup Box -->')

# Update JS Loading
if 'document.getElementById(\'set-patient-name\').value' not in text:
    old_js = '''            document.getElementById('set-privacy').checked = data.privacy_mode === true;'''
    new_js = '''            document.getElementById('set-privacy').checked = data.privacy_mode === true;
            document.getElementById('set-patient-name').value = data.patient_name || '';
            document.getElementById('set-patient-age').value = data.patient_age || '';
            document.getElementById('set-emergency-phone').value = data.emergency_phone || '';
            document.getElementById('set-receiver-email').value = data.receiver_email || '';
            document.getElementById('set-smtp-user').value = data.smtp_user || '';
            document.getElementById('set-smtp-pass').value = data.smtp_pass || '';'''
    text = text.replace(old_js, new_js)

# Update JS Saving
if 'patient_name: document.getElementById' not in text:
    old_save = '''                privacy_mode: document.getElementById('set-privacy').checked,'''
    new_save = '''                privacy_mode: document.getElementById('set-privacy').checked,
                patient_name: document.getElementById('set-patient-name').value,
                patient_age: document.getElementById('set-patient-age').value,
                emergency_phone: document.getElementById('set-emergency-phone').value,
                receiver_email: document.getElementById('set-receiver-email').value,
                smtp_user: document.getElementById('set-smtp-user').value,
                smtp_pass: document.getElementById('set-smtp-pass').value,'''
    text = text.replace(old_save, new_save)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched index.html with Email UI')
