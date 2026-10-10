with open('config.py', 'a', encoding='utf-8') as f:
    f.write('''
# --- DATA MANAGEMENT & EMAIL ---
PATIENT_NAME = ""
PATIENT_AGE = ""
EMERGENCY_PHONE = ""
RECEIVER_EMAIL = ""
SMTP_USER = ""
SMTP_PASS = ""
''')
print("Added config fields")
