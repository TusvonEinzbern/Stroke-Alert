import re
with open('dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Update GET
old_get = '''                return jsonify({
                    'immobility_timeout': app_config.IMMOBILITY_SEVERITY_STEPS[-1][0],
                    'sound_enabled': getattr(app_config, 'SOUND_ALERT_ENABLED', True),
                    'ntfy_topic': getattr(app_config, 'NTFY_TOPIC', ''),
                    'safe_zones': safe_zones,
                    'camera_source': camera_src,
                    'privacy_mode': getattr(app_config, 'PRIVACY_MODE', False)
                })'''
new_get = '''                return jsonify({
                    'immobility_timeout': app_config.IMMOBILITY_SEVERITY_STEPS[-1][0],
                    'sound_enabled': getattr(app_config, 'SOUND_ALERT_ENABLED', True),
                    'ntfy_topic': getattr(app_config, 'NTFY_TOPIC', ''),
                    'safe_zones': safe_zones,
                    'camera_source': camera_src,
                    'privacy_mode': getattr(app_config, 'PRIVACY_MODE', False),
                    'patient_name': getattr(app_config, 'PATIENT_NAME', ''),
                    'patient_age': getattr(app_config, 'PATIENT_AGE', ''),
                    'emergency_phone': getattr(app_config, 'EMERGENCY_PHONE', ''),
                    'receiver_email': getattr(app_config, 'RECEIVER_EMAIL', ''),
                    'smtp_user': getattr(app_config, 'SMTP_USER', ''),
                    'smtp_pass': getattr(app_config, 'SMTP_PASS', '')
                })'''
if "'patient_name'" not in text:
    text = text.replace(old_get, new_get)

# Update POST
new_post = '''                if 'privacy_mode' in data:
                    app_config.PRIVACY_MODE = bool(data['privacy_mode'])
                if 'patient_name' in data: app_config.PATIENT_NAME = data['patient_name']
                if 'patient_age' in data: app_config.PATIENT_AGE = data['patient_age']
                if 'emergency_phone' in data: app_config.EMERGENCY_PHONE = data['emergency_phone']
                if 'receiver_email' in data: app_config.RECEIVER_EMAIL = data['receiver_email']
                if 'smtp_user' in data: app_config.SMTP_USER = data['smtp_user']
                if 'smtp_pass' in data: app_config.SMTP_PASS = data['smtp_pass']
'''
text = text.replace("                if 'privacy_mode' in data:\n                    app_config.PRIVACY_MODE = bool(data['privacy_mode'])", new_post)

with open('dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Dashboard settings API updated")
