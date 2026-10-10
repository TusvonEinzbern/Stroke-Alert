import threading
import time
import webview
import socket
import sys

# Đảm bảo main.py sẽ bật dashboard và không bật cv2.imshow
sys.argv.extend(['--dashboard', '--no-display'])

from main import main as start_flask_engine

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

if __name__ == '__main__':
    # Start the backend (Flask + MediaPipe Engine) in a background thread
    # Note: We will modify main.py slightly so it can take a port argument
    import config
    import dashboard
    
    # Run the engine
    backend_thread = threading.Thread(target=start_flask_engine, daemon=True)
    backend_thread.start()
    
    # Wait a bit for the server to spin up
    time.sleep(2)
    
    url = f"http://localhost:{config.DASHBOARD_PORT}"
    
    # Create the webview window
    window = webview.create_window(
        'AI Stroke Detection System',
        url,
        width=1280,
        height=800,
        min_size=(1000, 600),
        background_color='#F9FAFB' # Tailwind gray-50
    )
    
    webview.start(private_mode=False)
