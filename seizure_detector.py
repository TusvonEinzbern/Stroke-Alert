import time
import numpy as np
from collections import deque
from typing import Optional, Dict

from models import PoseData, DetectionEvent
import config

class SeizureDetector:
    """
    Phát hiện co giật bằng cách phân tích tần số dao động của các bộ phận cơ thể.
    """
    def __init__(self):
        # Lưu vết theo từng điểm (x, y)
        self.history: Dict[str, deque] = {
            'left_wrist': deque(),
            'right_wrist': deque(),
            'left_ankle': deque(),
            'right_ankle': deque(),
            'left_knee': deque(),
            'right_knee': deque(),
            'head': deque()
        }
        self.window_size = config.SEIZURE_WINDOW_SECONDS

    def reset(self):
        for k in self.history.keys():
            self.history[k].clear()

    def update(self, pose_data: PoseData, frame: np.ndarray = None) -> Optional[DetectionEvent]:
        if not pose_data.is_detected:
            return None
            
        current_time = pose_data.timestamp
        
        # Ngăn chặn báo động giả (False Positive) do đi lại:
        # Nếu đang đi lại/đứng thẳng -> không phân tích co giật
        if getattr(config, 'SEIZURE_REQUIRE_LOW_POSTURE', True):
            is_lying = pose_data.body_angle < config.LYING_ANGLE or pose_data.bbox_aspect > config.LYING_ASPECT_RATIO
            if not is_lying:
                self.reset()
                return None
        
        # Cập nhật lịch sử
        self.history['left_wrist'].append((current_time, *pose_data.left_wrist))
        self.history['right_wrist'].append((current_time, *pose_data.right_wrist))
        self.history['left_ankle'].append((current_time, *pose_data.left_ankle))
        self.history['right_ankle'].append((current_time, *pose_data.right_ankle))
        self.history['left_knee'].append((current_time, *pose_data.left_knee))
        self.history['right_knee'].append((current_time, *pose_data.right_knee))
        self.history['head'].append((current_time, *pose_data.nose))
        
        # Loại bỏ dữ liệu cũ khỏi window
        cutoff_time = current_time - self.window_size
        for part in self.history:
            while self.history[part] and self.history[part][0][0] < cutoff_time:
                self.history[part].popleft()
                
        # Tính ngưỡng số lần đổi chiều tối thiểu dựa trên tần số
        # 1 Hz = 2 lần đổi chiều / giây
        min_direction_changes = config.SEIZURE_FREQUENCY_MIN * self.window_size * 2
        
        # Lấy body_height làm hệ quy chiếu cho biên độ dao động
        body_len = pose_data.body_height if pose_data.body_height > 1e-6 else 1.0
        min_amplitude = config.SEIZURE_HYSTERESIS * body_len
                
        # Phân tích từng bộ phận
        oscillating_parts = 0
        max_oscillations = 0
        
        for part_name, hist in self.history.items():
            if len(hist) < 10:
                continue
                
            analysis = self._analyze_body_part(list(hist))
            if analysis['oscillations'] >= min_direction_changes and \
               analysis['amplitude'] >= min_amplitude:
                oscillating_parts += 1
                max_oscillations = max(max_oscillations, analysis['oscillations'])

        if oscillating_parts >= config.SEIZURE_MIN_BODY_PARTS:
            # Tính độ tin cậy (confidence)
            base_conf = min(1.0, max_oscillations / (min_direction_changes * 1.5))
            # Boost 0.1 cho mỗi bộ phận dao động thêm
            extra_boost = (oscillating_parts - config.SEIZURE_MIN_BODY_PARTS) * 0.1
            confidence = min(1.0, base_conf + extra_boost)
            
            # Đánh giá độ nghiêm trọng
            severity = 'low'
            if confidence >= 0.9:
                severity = 'critical'
            elif confidence >= 0.8:
                severity = 'high'
            elif confidence >= 0.6:
                severity = 'medium'
                
            return DetectionEvent(
                event_type='seizure',
                confidence=confidence,
                severity=severity,
                timestamp=current_time,
                description=f"Phát hiện co giật. {oscillating_parts} bộ phận dao động, số lần đổi chiều: {max_oscillations}."
            )
            
        return None

    def _analyze_body_part(self, history: list) -> dict:
        """Phân tích chuyển động của một bộ phận cơ thể."""
        if len(history) < 3:
            return {'oscillations': 0, 'amplitude': 0.0}
            
        positions = [item[2] for item in history] # Lấy danh sách tọa độ y
        
        oscillations = self._count_oscillations(positions)
        amplitude = self._calculate_amplitude(positions)
        
        return {
            'oscillations': oscillations,
            'amplitude': amplitude
        }

    def _count_oscillations(self, positions: list) -> int:
        """Đếm số lần thay đổi hướng (đảo dấu vận tốc)."""
        if len(positions) < 3:
            return 0
            
        directions = []
        for i in range(1, len(positions)):
            diff = positions[i] - positions[i-1]
            # Loại bỏ nhiễu nhỏ
            if abs(diff) > 0.005:
                directions.append(1 if diff > 0 else -1)
                
        if not directions:
            return 0
            
        changes = 0
        current_dir = directions[0]
        for d in directions[1:]:
            if d != current_dir:
                changes += 1
                current_dir = d
                
        return changes

    def _calculate_amplitude(self, positions: list) -> float:
        """Tính biên độ dao động (max y - min y)."""
        if not positions:
            return 0.0
        return max(positions) - min(positions)
