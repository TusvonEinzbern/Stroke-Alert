import re

with open('dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add to GET
text = text.replace("'camera_source': camera_src", "'camera_source': camera_src,\n                    'privacy_mode': getattr(app_config, 'PRIVACY_MODE', False)")

# Add to POST
post_code = '''                if 'camera_source' in data:'''
new_post_code = '''                if 'privacy_mode' in data:
                    app_config.PRIVACY_MODE = bool(data['privacy_mode'])
                if 'camera_source' in data:'''
text = text.replace(post_code, new_post_code)

with open('dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched dashboard.py for privacy_mode')
