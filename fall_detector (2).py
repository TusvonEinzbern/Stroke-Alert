import time
import math
import numpy as np
from collections import deque
from typing import Optional

from models import PoseData, DetectionEvent
import config

class FallDetector:
    """
    Phát hiện té ngã bằng phân tích vận tốc theo phương dọc và vị trí cơ thể.
    """
    def __init__(self):
        # Lưu trữ lịch sử: (timestamp, nose_y, torso_y, body_height)
        self.history = deque(maxlen=30)
        self.state = "STANDING" # STANDING, FALLING, ON_FLOOR, CONFIRMED_FALL, RECOVERED
        self.fall_start_time = 0.0
        self.on_floor_time = 0.0

    def reset(self):
        """Xóa trạng thái và dữ liệu lịch sử."""
        self.history.clear()
        self.state = "STANDING"
        self.fall_start_time = 0.0
        self.on_floor_time = 0.0

    def update(self, pose_data: PoseData, frame: np.ndarray = None) -> Optional[DetectionEvent]:
        """
        Logic chính phát hiện ngã.
        """
        if not pose_data.is_detected:
            return None

        current_time = pose_data.timestamp
        self.history.append((current_time, pose_data.nose_y, pose_data.torso_y, pose_data.body_height))

        if len(self.history) < 5:
            return None

        # Trạng thái hiện tại
        velocity = self._calculate_velocity()
        is_floor = self._is_on_floor(pose_data)
        
        # Máy trạng thái (State Machine)
        if self.state == "STANDING":
            if velocity > config.FALL_VELOCITY_THRESHOLD and pose_data.body_angle < config.UPRIGHT_ANGLE:
                if getattr(config, 'GRADUAL_MOVEMENT_ANALYSIS', True) and self._is_gradual_descent():
                    pass # Chuyển động chậm, có thể đang ngồi xuống
                else:
                    self.state = "FALLING"
                    self.fall_start_time = current_time

        elif self.state == "FALLING":
            # Nếu đang rơi, kiểm tra xem đã tới sàn chưa
            if is_floor:
                # Kiểm tra thêm tỷ lệ chiều cao
                # Tìm body_height lớn nhất trong history
                max_height = max(item[3] for item in self.history) if self.history else pose_data.body_height
                height_ratio = pose_data.body_height / max_height if max_height > 0 else 1.0
                
                if height_ratio < config.FALL_HEIGHT_RATIO_THRESHOLD:
                    self.state = "ON_FLOOR"
                    self.on_floor_time = current_time
            # Nếu hết fall mà không ở trên sàn, có thể là do nhiễu -> reset
            elif current_time - self.fall_start_time > 2.0:
                self.state = "STANDING"

        elif self.state == "ON_FLOOR":
            if not is_floor:
                # Nếu không còn trên sàn nữa -> Đã phục hồi (đứng dậy)
                self.state = "RECOVERED"
            elif current_time - self.on_floor_time >= config.FALL_RECOVERY_TIMEOUT:
                # Hết thời gian chờ phục hồi -> Xác nhận ngã
                self.state = "CONFIRMED_FALL"
                
                # Tính toán confidence
                base_conf = 0.5
                if velocity > config.FALL_VELOCITY_THRESHOLD * 2:
                    base_conf += 0.2
                if pose_data.body_angle < (config.FALL_ANGLE_THRESHOLD * 0.5):
                    base_conf += 0.15
                    
                max_height = max(item[3] for item in self.history)
                height_ratio = pose_data.body_height / max_height if max_height > 0 else 1.0
                if height_ratio < (config.FALL_HEIGHT_RATIO_THRESHOLD * 0.8):
                    base_conf += 0.15
                    
                final_conf = min(1.0, config.get_adjusted_confidence(base_conf))
                
                return DetectionEvent(
                    event_type='fall',
                    confidence=final_conf,
                    severity='critical' if final_conf > 0.8 else 'high',
                    timestamp=current_time,
                    description=f"Phát hiện ngã đột ngột. Velocity: {velocity:.2f}, Angle: {pose_data.body_angle:.1f}"
                )

        elif self.state == "RECOVERED":
            # Chờ một lúc rồi reset về STANDING
            self.state = "STANDING"
            
        elif self.state == "CONFIRMED_FALL":
            # Giữ trạng thái nếu người dùng chưa đứng dậy
            if not is_floor:
                self.state = "STANDING"

        return None

    def _calculate_velocity(self) -> float:
        """Tính vận tốc dọc của cơ thể (torso_y) từ lịch sử."""
        if len(self.history) < 5:
            return 0.0
            
        # Lấy 5 frame gần nhất
        recent = list(self.history)[-5:]
        start_item = recent[0]
        end_item = recent[-1]
        
        delta_y = end_item[2] - start_item[2] # torso_y
        delta_t = end_item[0] - start_item[0]
        
        if delta_t <= 0:
            return 0.0
            
        # Vận tốc dương nghĩa là đang đi xuống (do y=0 ở đỉnh)
        return delta_y / delta_t

    def _is_on_floor(self, pose_data: PoseData) -> bool:
        """Kiểm tra xem người có đang ở gần/trên sàn không."""
        return pose_data.body_angle < config.LYING_ANGLE or pose_data.bbox_aspect > config.LYING_ASPECT_RATIO

    def _is_gradual_descent(self) -> bool:
        """Phân biệt ngồi xuống (chậm) và ngã (nhanh)."""
        velocity = self._calculate_velocity()
        # Nếu vận tốc chỉ ở mức vừa phải (không quá ngưỡng mạnh)
        # và có sự ổn định
        return (velocity < config.FALL_VELOCITY_THRESHOLD * 1.5)
