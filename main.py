import argparse
import logging
import cv2
import threading
import json
import time
from typing import Optional, Dict

import config
from models import SystemStatus
from camera_manager import CameraManager
from stroke_risk_engine import StrokeRiskEngine


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def parse_args():
    parser = argparse.ArgumentParser(description="Hệ Thống Phát Hiện Đột Quỵ (Stroke Detection System)")
    parser.add_argument('--source', type=str, default=str(config.CAMERA_SOURCE),
                        help='Camera source (default: config.CAMERA_SOURCE)')
    parser.add_argument('--dashboard', action='store_true',
                        help='Enable web dashboard')
    parser.add_argument('--no-display', action='store_true',
                        help='Disable OpenCV window')
    parser.add_argument('--config', type=str,
                        help='Path to config override (optional)')
    parser.add_argument('--safe-zones', type=str,
                        help='Path to JSON file with safe zone definitions')
    return parser.parse_args()

class SafeZoneDrawer:
    def __init__(self):
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.zone = None

    def draw_rectangle(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.zone = (self.ix, self.iy, x, y)
            print(f"Safe zone recorded: {self.zone}")

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    args = parse_args()
    
    # Load safe zones if provided
    if args.safe_zones:
        try:
            with open(args.safe_zones, 'r') as f:
                zones = json.load(f)
                config.SAFE_ZONES = zones
                logger.info(f"Loaded safe zones from {args.safe_zones}")
        except Exception as e:
            logger.error(f"Error loading safe zones: {e}")

    logger.info("=" * 50)
    logger.info("  KHỞI ĐỘNG HỆ THỐNG PHÁT HIỆN ĐỘT QUỴ")
    logger.info("  Stroke Detection System v1.0")
    logger.info("=" * 50)

    # Initialize components
    try:
        # Convert source to int if it's a digit (webcam index)
        source = int(args.source) if args.source.isdigit() else args.source
        camera = CameraManager(source)
        if not camera.connect():
            logger.error("Không thể kết nối camera. Kiểm tra lại nguồn camera.")
            return
        logger.info(f"Camera info: {camera.get_info()}")
        
        engine = StrokeRiskEngine()
        engine.camera = camera
        logger.info("Đã khởi tạo StrokeRiskEngine thành công.")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}", exc_info=True)
        return

    dashboard_thread = None
    if args.dashboard:
        try:
            from dashboard import create_app
            app = create_app(engine)
            dashboard_thread = threading.Thread(
                target=app.run,
                kwargs={'host': config.DASHBOARD_HOST, 'port': config.DASHBOARD_PORT, 'use_reloader': False},
                daemon=True
            )
            dashboard_thread.start()
            logger.info(f"Dashboard started on {config.DASHBOARD_HOST}:{config.DASHBOARD_PORT}")
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")

    # Setup display and interaction
    window_name = "Stroke Detection System"
    if not args.no_display:
        cv2.namedWindow(window_name)
        drawer = SafeZoneDrawer()
        cv2.setMouseCallback(window_name, drawer.draw_rectangle)

    frame_count = 0
    engine.status.is_running = True
    start_time = time.time()

    try:
        while True:
            # Kiểm tra xem UI có còn hoạt động không (Heartbeat)
            if hasattr(engine, 'last_heartbeat') and time.time() - engine.last_heartbeat > 30.0:
                logger.info("Mất kết nối với giao diện (App đã tắt). Tự động tắt hệ thống AI ngầm...")
                break

            ret, frame = camera.read_frame()
            if not ret or frame is None:
                logger.warning("Failed to grab frame.")
                time.sleep(0.1)
                continue
                
            engine.status.camera_connected = True
            frame_count += 1

            if frame_count % config.PROCESS_EVERY_N_FRAMES == 0:
                # Process frame through detection pipeline
                result = engine.process_frame(frame)
                annotated_frame = result.get('annotated_frame', frame)
                
                # Update status
                engine.status.uptime_seconds = time.time() - start_time
                engine.status.last_update = time.time()
                
                if not args.no_display:
                    display_frame = annotated_frame.copy()
                    
                    # Draw safe zone in progress
                    if hasattr(drawer, 'zone') and drawer.zone:
                        cv2.rectangle(display_frame, 
                                      (drawer.zone[0], drawer.zone[1]),
                                      (drawer.zone[2], drawer.zone[3]),
                                      (0, 255, 0), 2)
                        cv2.putText(display_frame, "Safe Zone",
                                    (drawer.zone[0], drawer.zone[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        
                    cv2.imshow(window_name, display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("Thoát theo yêu cầu người dùng.")
                break
            elif key == ord('s'):
                filename = f"snapshot_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                logger.info(f"Đã lưu ảnh: {filename}")
            elif key == ord('r'):
                engine.reset()
                logger.info("Đã reset toàn bộ detector.")
            elif key == ord('z'):
                if hasattr(drawer, 'zone') and drawer.zone:
                    # Normalized coords
                    h, w = frame.shape[:2]
                    x1, y1, x2, y2 = drawer.zone
                    normalized_zone = {
                        'x1': min(x1, x2) / w,
                        'y1': min(y1, y2) / h,
                        'x2': max(x1, x2) / w,
                        'y2': max(y1, y2) / h,
                        'label': 'user_defined'
                    }
                    config.SAFE_ZONES.append(normalized_zone)
                    logger.info(f"Safe zone added: {normalized_zone}")
                    drawer.zone = None

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
    finally:
        engine.status.is_running = False
        camera.release()
        if not args.no_display:
            cv2.destroyAllWindows()
        logger.info("System shutdown complete.")

if __name__ == "__main__":
    main()
