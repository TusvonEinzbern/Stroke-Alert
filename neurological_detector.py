import time
import numpy as np
from collections import deque
from typing import Optional, Dict

from models import PoseData, DetectionEvent
import config

class NeurologicalDetector:
    """
    Phát hiện các dấu hiệu thần kinh:
    1. Động kinh / Co giật toàn thân (Seizure - ngã rải rác)
    2. Rối loạn vận động / Tiền đột quỵ (TIA / Ataxia - rung giật tay khi ngồi/đứng)
    """
    def __init__(self):
        self.history: Dict[str, deque] = {
            'left_wrist': deque(maxlen=60),
            'right_wrist': deque(maxlen=60),
            'left_ankle': deque(maxlen=60),
            'right_ankle': deque(maxlen=60),
            'left_knee': deque(maxlen=60),
            'right_knee': deque(maxlen=60),
            'head': deque(maxlen=60)
        }
        self.window_size = config.SEIZURE_WINDOW_SECONDS

    def reset(self):
        for k in self.history.keys():
            self.history[k].clear()

    def update(self, pose_data: PoseData, frame: np.ndarray = None) -> Optional[DetectionEvent]:
        if not pose_data.is_detected:
            return None
            
        current_time = pose_data.timestamp
        is_lying = pose_data.body_angle < config.LYING_ANGLE or pose_data.bbox_aspect > config.LYING_ASPECT_RATIO
        
        # Cập nhật lịch sử
        self.history['left_wrist'].append((current_time, *pose_data.left_wrist))
        self.history['right_wrist'].append((current_time, *pose_data.right_wrist))
        self.history['left_ankle'].append((current_time, *pose_data.left_ankle))
        self.history['right_ankle'].append((current_time, *pose_data.right_ankle))
        self.history['left_knee'].append((current_time, *pose_data.left_knee))
        self.history['right_knee'].append((current_time, *pose_data.right_knee))
        self.history['head'].append((current_time, *pose_data.nose))
        
        # Xóa frame cũ
        cutoff_time = current_time - self.window_size
        for part in self.history:
            while self.history[part] and self.history[part][0][0] < cutoff_time:
                self.history[part].popleft()

        # Tính toán đặc trưng dao động
        body_len = pose_data.body_height if pose_data.body_height > 1e-6 else 1.0
        min_amplitude = config.SEIZURE_HYSTERESIS * body_len
        min_direction_changes = config.SEIZURE_FREQUENCY_MIN * self.window_size * 2

        oscillating_parts = 0
        max_oscillations = 0
        wrist_tremors = 0
        
        for part_name, hist in self.history.items():
            if len(hist) < 15:
                continue
            
            analysis = self._analyze_body_part(list(hist))
            
            # Kiểm tra rung tay (Ataxia/Tremor)
            if 'wrist' in part_name:
                # Vận động tinh: rung giật biên độ nhỏ nhưng tần số cực cao
                if analysis['oscillations'] >= (min_direction_changes * 1.2) and (min_amplitude * 0.5 < analysis['amplitude'] < min_amplitude * 2.0):
                    # Kiểm tra xem cánh tay có đang di chuyển xa không (nếu di chuyển xa thì là tập thể dục)
                    spatial_spread = self._calculate_spatial_spread(list(hist))
                    if spatial_spread < body_len * 0.5: # Tay chỉ rung tại chỗ
                        wrist_tremors += 1

            # Kiểm tra co giật mạnh toàn thân
            if analysis['oscillations'] >= min_direction_changes and analysis['amplitude'] >= min_amplitude:
                oscillating_parts += 1
                max_oscillations = max(max_oscillations, analysis['oscillations'])

        # Logic 1: TIA / Rối loạn vận động (khi ĐỨNG/NGỒI)
        if not is_lying and wrist_tremors > 0:
            return DetectionEvent(
                event_type='tia_ataxia',
                confidence=0.85,
                severity='high',
                timestamp=current_time,
                description=f"Cảnh báo Tiền Đột Quỵ (TIA): Phát hiện tay mất phối hợp vận động (rung giật) khi ngồi/đứng."
            )

        # Logic 2: Co giật (khi NẰM)
        if is_lying and oscillating_parts >= config.SEIZURE_MIN_BODY_PARTS:
            base_conf = min(1.0, max_oscillations / (min_direction_changes * 1.5))
            extra_boost = (oscillating_parts - config.SEIZURE_MIN_BODY_PARTS) * 0.1
            confidence = min(1.0, base_conf + extra_boost)
            
            return DetectionEvent(
                event_type='seizure',
                confidence=confidence,
                severity='critical' if confidence >= 0.8 else 'high',
                timestamp=current_time,
                description=f"Phát hiện co giật toàn thân. {oscillating_parts} bộ phận dao động mạnh."
            )
            
        return None

    def _analyze_body_part(self, history: list) -> dict:
        positions_y = [item[2] for item in history]
        return {
            'oscillations': self._count_oscillations(positions_y),
            'amplitude': self._calculate_amplitude(positions_y)
        }

    def _count_oscillations(self, positions: list) -> int:
        if len(positions) < 3: return 0
        directions = []
        for i in range(1, len(positions)):
            diff = positions[i] - positions[i-1]
            if abs(diff) > 0.003: # Rất nhạy để bắt micro-tremor
                directions.append(1 if diff > 0 else -1)
        if not directions: return 0
        
        changes = 0
        current_dir = directions[0]
        for d in directions[1:]:
            if d != current_dir:
                changes += 1
                current_dir = d
        return changes

    def _calculate_amplitude(self, positions: list) -> float:
        if not positions: return 0.0
        return max(positions) - min(positions)
        
    def _calculate_spatial_spread(self, history: list) -> float:
        # Khoảng cách tối đa mà bộ phận đó đã di chuyển trong lịch sử (Euclidean)
        xs = [item[1] for item in history]
        ys = [item[2] for item in history]
        return np.sqrt((max(xs) - min(xs))**2 + (max(ys) - min(ys))**2)
