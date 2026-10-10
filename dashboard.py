from flask import Flask, render_template, Response, jsonify
import cv2
import threading
import time

def create_app(engine_ref):
    """
    Creates and configures the Flask application for the dashboard.
    engine_ref: Reference to the StrokeRiskEngine instance for data access.
    """
    app = Flask(__name__)
    lock = threading.Lock()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/status')
    def get_status():
        with lock:
            if engine_ref and hasattr(engine_ref, 'status'):
                return jsonify(engine_ref.status.to_dict())
            return jsonify({'error': 'Status not available'})

    @app.route('/api/events')
    def get_events():
        with lock:
            if engine_ref and hasattr(engine_ref, 'status'):
                # Return active events and history
                return jsonify({
                    'active': [e.to_dict() for e in engine_ref.status.active_events],
                    'history': engine_ref.status.event_history[-10:] # recent 10
                })
            return jsonify({'error': 'Events not available'})

    def generate_frames():
        while True:
            with lock:
                if engine_ref and hasattr(engine_ref, 'latest_frame') and engine_ref.latest_frame is not None:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', engine_ref.latest_frame)
                    if ret:
                        frame = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.05)  # Max ~20fps for dashboard to save resources

    @app.route('/api/video_feed')
    def video_feed():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    import config as app_config
    from flask import request

    @app.route('/api/settings', methods=['GET', 'POST'])
    def settings_api():
        with lock:
            if request.method == 'GET':
                safe_zones = []
                if engine_ref and hasattr(engine_ref, 'env_analyzer'):
                    safe_zones = engine_ref.env_analyzer.safe_zones
                
                camera_src = ""
                if engine_ref and hasattr(engine_ref, 'camera'):
                    camera_src = engine_ref.camera.source

                return jsonify({
                    'immobility_timeout': app_config.IMMOBILITY_SEVERITY_STEPS[-1][0],
                    'sound_enabled': getattr(app_config, 'SOUND_ALERT_ENABLED', True),
                    'ntfy_topic': getattr(app_config, 'NTFY_TOPIC', ''),
                    'safe_zones': safe_zones,
                    'camera_source': camera_src
                })
                
            elif request.method == 'POST':
                data = request.json
                if not data:
                    return jsonify({'error': 'No data'})
                
                if 'immobility_timeout' in data:
                    val = float(data['immobility_timeout'])
                    app_config.IMMOBILITY_SEVERITY_STEPS = [
                        (val * 0.3, "low"),
                        (val * 0.6, "medium"),
                        (val * 1.0, "high"),
                        (val * 1.5, "critical"),
                    ]
                if 'sound_enabled' in data:
                    app_config.SOUND_ALERT_ENABLED = bool(data['sound_enabled'])
                if 'ntfy_topic' in data:
                    app_config.NTFY_TOPIC = data['ntfy_topic']
                if 'safe_zones' in data:
                    if engine_ref and hasattr(engine_ref, 'env_analyzer'):
                        engine_ref.env_analyzer.set_safe_zones(data['safe_zones'])
                if 'camera_source' in data:
                    if engine_ref and hasattr(engine_ref, 'camera'):
                        new_src = data['camera_source']
                        if str(new_src).isdigit():
                            new_src = int(new_src)
                        if engine_ref.camera.source != new_src:
                            engine_ref.camera.source = new_src
                            engine_ref.camera.connect()
                            # Lưu vào file config.py để lưu trữ vĩnh viễn
                            app_config.CAMERA_SOURCE = new_src
                            try:
                                with open('config.py', 'r', encoding='utf-8') as f:
                                    content = f.read()
                                import re
                                if isinstance(new_src, int):
                                    content = re.sub(r'CAMERA_SOURCE\s*=\s*.*', f'CAMERA_SOURCE = {new_src}', content)
                                else:
                                    content = re.sub(r'CAMERA_SOURCE\s*=\s*.*', f'CAMERA_SOURCE = "{new_src}"', content)
                                with open('config.py', 'w', encoding='utf-8') as f:
                                    f.write(content)
                            except Exception as e:
                                print("Lỗi lưu config:", e)
                            
                return jsonify({'status': 'ok'})

    return app
