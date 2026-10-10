import cv2
import numpy as np
import time
from models import PoseData
import config
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class EnvironmentAnalyzer:
    """
    Analyzes the environment to detect beds, furniture, and safe zones 
    for false positive reduction.
    """
    def __init__(self):
        self.safe_zones = config.SAFE_ZONES if hasattr(config, 'SAFE_ZONES') else []
        self.detector = None
        self.last_detection_time = 0
        self.cached_furniture_boxes = []

        if config.FURNITURE_DETECTION_ENABLED:
            base_options = python.BaseOptions(model_asset_path=config.OBJECT_MODEL_PATH)
            options = vision.ObjectDetectorOptions(
                base_options=base_options,
                score_threshold=config.FURNITURE_DETECTION_CONFIDENCE,
                category_allowlist=list(config.FURNITURE_LABELS)
            )
            self.detector = vision.ObjectDetector.create_from_options(options)

    def analyze(self, frame: np.ndarray, pose_data: PoseData) -> dict:
        """
        Phân tích khung hình để xác định người có ở trong vùng an toàn hay gần giường không.
        """
        result = {
            'is_near_bed': False,
            'is_in_safe_zone': False,
            'detected_objects': [],
            'suppress_alert': False,
            'reason': ''
        }

        if not config.ENVIRONMENT_ANALYSIS_ENABLED:
            return result

        # Check safe zones first
        if pose_data and pose_data.is_detected:
            for zone in self.safe_zones:
                if self.is_person_in_zone(pose_data, zone):
                    result['is_in_safe_zone'] = True
                    result['suppress_alert'] = True
                    result['reason'] = 'Người trong vùng an toàn (giường/sofa)'
                    return result

        # Detect bed/furniture region dynamically
        if config.FURNITURE_DETECTION_ENABLED and self.detector:
            current_time = time.time()
            if current_time - self.last_detection_time > config.FURNITURE_REFRESH_SECONDS:
                self.cached_furniture_boxes = self.detect_furniture(frame)
                self.last_detection_time = current_time

            if self.cached_furniture_boxes:
                result['detected_objects'].extend(['furniture'] * len(self.cached_furniture_boxes))
                
                if pose_data and pose_data.is_detected:
                    torso_x, torso_y = pose_data.torso_center
                    # Check if torso is within any furniture bounding box (normalized)
                    for (nx, ny, nw, nh) in self.cached_furniture_boxes:
                        if nx <= torso_x <= nx + nw and ny <= torso_y:
                            result['is_near_bed'] = True
                            result['suppress_alert'] = True
                            result['reason'] = 'Phát hiện giường/sofa, có thể đang đi ngủ'
                            break

        return result

    def set_safe_zones(self, zones: list):
        """Thiết lập các vùng an toàn từ cấu hình."""
        self.safe_zones = zones

    def detect_furniture(self, frame: np.ndarray) -> list:
        """
        Phát hiện vùng có dạng giường ngủ / sofa trong khung hình dùng MediaPipe ObjectDetector.
        Trả về list bounding box chuẩn hóa [x, y, w, h].
        """
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        detection_result = self.detector.detect(mp_image)
        
        h_frame, w_frame = frame.shape[:2]
        furniture_regions = []
        
        for detection in detection_result.detections:
            bbox = detection.bounding_box
            # Normalize coordinates
            nx = bbox.origin_x / w_frame
            ny = bbox.origin_y / h_frame
            nw = bbox.width / w_frame
            nh = bbox.height / h_frame
            
            furniture_regions.append((nx, ny, nw, nh))
                
        return furniture_regions

    def is_person_in_zone(self, pose_data: PoseData, zone: dict) -> bool:
        """Kiểm tra xem trung tâm thân người có nằm trong vùng an toàn không."""
        tx, ty = pose_data.torso_center
        return (zone.get('x1', 0) <= tx <= zone.get('x2', 1) and 
                zone.get('y1', 0) <= ty <= zone.get('y2', 1))

    def close(self):
        if self.detector:
            self.detector.close()
