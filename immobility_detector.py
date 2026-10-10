import time
import math
import numpy as np
from typing import Optional

from models import PoseData, DetectionEvent
import config

class ImmobilityDetector:
    """
    Phát hiện bất động: người nằm yên trên sàn trong một khoảng thời gian dài.
    """
    def __init__(self):
        self.immobility_start_time = 0.0
        self.is_tracking = False
        self.prev_pose: Optional[PoseData] = None

    def reset(self):
        self.immobility_start_time = 0.0
        self.is_tracking = False
        self.prev_pose = None

    def update(self, pose_data: PoseData, frame: np.ndarray = None) -> Optional[DetectionEvent]:
        if not pose_data.is_detected:
            # Có thể người đã ra khỏi khung hình -> không đo bất động nữa hoặc tạm dừng
            return None

        current_time = pose_data.timestamp
        
        if self.prev_pose is None:
            self.prev_pose = pose_data
            return None
            
        total_movement = self._calculate_total_movement(pose_data)
        on_floor = self._is_on_floor(pose_data)
        
        import logging
        logger = logging.getLogger('immobility')
        
        # CHỈ báo động bất động khi đang ở tư thế NẰM (Tránh báo động giả khi ngồi im trên ghế làm việc)
        if not on_floor:
            if self.is_tracking:
                logger.info("Broke tracking! Person is not lying down/on floor.")
            self.reset()
            self.prev_pose = pose_data
            return None
        
        if total_movement < config.IMMOBILITY_MOVEMENT_THRESHOLD:
            if not self.is_tracking:
                self.is_tracking = True
                self.immobility_start_time = current_time
                logger.info(f"Started tracking immobility. total_movement: {total_movement:.3f}, body_angle: {pose_data.body_angle:.1f}, bbox_aspect: {pose_data.bbox_aspect:.2f}")
            else:
                duration = current_time - self.immobility_start_time
                logger.info(f"Tracking immobility: {duration:.1f}s. movement: {total_movement:.3f}")
                if duration >= config.IMMOBILITY_TIMEOUT:
                    # Tính toán severity theo độ dài thời gian (Lấy từ cấu hình config.py)
                    severity = 'low'
                    for step_duration, step_severity in config.IMMOBILITY_SEVERITY_STEPS:
                        if duration >= step_duration:
                            severity = step_severity
                            
                    # Confidence tăng dần theo thời gian
                    base_conf = 0.5 + (duration / (config.IMMOBILITY_SEVERITY_STEPS[-1][0] * 2))
                    confidence = min(0.95, base_conf)
                    
                    self.prev_pose = pose_data
                    return DetectionEvent(
                        event_type='immobility',
                        confidence=confidence,
                        severity=severity,
                        timestamp=current_time,
                        description=f"Bất động trên sàn suốt {int(duration)} giây."
                    )
        else:
            # Có chuyển động nhiều -> Reset tracker
            if total_movement >= config.IMMOBILITY_MOVEMENT_THRESHOLD:
                if self.is_tracking:
                    logger.info(f"Broke tracking! movement: {total_movement:.3f} >= {config.IMMOBILITY_MOVEMENT_THRESHOLD}")
                self.is_tracking = False
                self.immobility_start_time = 0.0
                
        self.prev_pose = pose_data
        return None

    def _calculate_total_movement(self, current: PoseData) -> float:
        """Tổng hợp chuyển động của tất cả các keypoint."""
        if not self.prev_pose:
            return 0.0
            
        curr_kp = current.all_keypoints()
        prev_kp = self.prev_pose.all_keypoints()
        
        total_dist = 0.0
        for pt1, pt2 in zip(curr_kp, prev_kp):
            dist = math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
            total_dist += dist
            
        return total_dist

    def _is_on_floor(self, pose_data: PoseData) -> bool:
        # Sử dụng góc thân người hoặc tỷ lệ khung bao để xác định tư thế nằm
        return pose_data.body_angle < config.LYING_ANGLE or pose_data.bbox_aspect > config.LYING_ASPECT_RATIO
