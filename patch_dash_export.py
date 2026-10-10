with open('dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

export_route = '''
    @app.route('/api/export_csv')
    def export_csv():
        import csv
        import io
        from datetime import datetime
        import database as db_mod
        
        rows = db_mod.get_all_events_for_export()
        
        si = io.StringIO()
        # UTF-8 with BOM so Excel opens it with correct Vietnamese encoding
        si.write('\\ufeff')
        cw = csv.writer(si)
        cw.writerow(['Thời gian', 'Loại Sự Cố', 'Mức Độ', 'Độ Tin Cậy', 'Mô Tả Chi Tiết'])
        
        for r in rows:
            ts, ev_type, sev, conf, desc = r
            dt_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            cw.writerow([dt_str, ev_type.upper(), sev.upper(), f"{conf*100:.1f}%", desc])
            
        output = si.getvalue()
        from flask import Response
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=bao_cao_y_te_đột_quỵ.csv"}
        )
'''

if '/api/export_csv' not in text:
    text = text.replace('return app', export_route + '\n    return app')
    with open('dashboard.py', 'w', encoding='utf-8') as f:
        f.write(text)
print('Patched dashboard.py')
