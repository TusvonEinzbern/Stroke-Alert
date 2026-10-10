with open('dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

records_route = '''
    @app.route('/api/records')
    def get_records():
        import os
        records_dir = 'static/records'
        if not os.path.exists(records_dir):
            return jsonify([])
        files = [f for f in os.listdir(records_dir) if f.endswith('.mp4')]
        files.sort(reverse=True)
        return jsonify([f"/static/records/{f}" for f in files])
'''

if '/api/records' not in text:
    text = text.replace('return app', records_route + '\n    return app')
    with open('dashboard.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Dashboard patched with records route")
