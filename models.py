"""
Stroke Detection System - Data Models
Các mô hình dữ liệu dùng chung cho hệ thống phát hiện đột quỵ.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any
import numpy as np
import time


@dataclass
class PoseData:
    """
    Dữ liệu tư thế cơ thể được trích xuất từ một khung hình.
    Tọa độ được chuẩn hóa (normalized): x trong [0,1], y trong [0,1].
    Lưu ý: y=0 là đỉnh khung hình, y=1 là đáy khung hình.
    """
    landmarks: Any = None                # Raw MediaPipe landmarks

    # Key body points (x, y) normalized
    nose: tuple = (0.0, 0.0)
    left_eye: tuple = (0.0, 0.0)
    right_eye: tuple = (0.0, 0.0)
    left_shoulder: tuple = (0.0, 0.0)
    right_shoulder: tuple = (0.0, 0.0)
    left_elbow: tuple = (0.0, 0.0)
    right_elbow: tuple = (0.0, 0.0)
    left_wrist: tuple = (0.0, 0.0)
    right_wrist: tuple = (0.0, 0.0)
    left_hip: tuple = (0.0, 0.0)
    right_hip: tuple = (0.0, 0.0)
    left_knee: tuple = (0.0, 0.0)
    right_knee: tuple = (0.0, 0.0)
    left_ankle: tuple = (0.0, 0.0)
    right_ankle: tuple = (0.0, 0.0)

    # Derived metrics
    torso_center: tuple = (0.0, 0.0)    # Trung tâm thân (trung bình vai + hông)
    body_height: float = 0.0             # Độ trải dọc của cơ thể (normalized) - giảm mạnh khi nằm
    body_angle: float = 90.0             # Góc thân người so với mặt phẳng ngang [0-90°], 90 = đứng
    bbox_aspect: float = 0.0             # Tỷ lệ rộng/cao khung bao cơ thể: đứng < 0.6, nằm > 1.0

    # Status
    is_detected: bool = False
    detection_confidence: float = 0.0
    timestamp: float = 0.0

    @property
    def nose_y(self) -> float:
        return self.nose[1]

    @property
    def torso_y(self) -> float:
        return self.torso_center[1]

    @property
    def hip_center(self) -> tuple:
        return (
            (self.left_hip[0] + self.right_hip[0]) / 2,
            (self.left_hip[1] + self.right_hip[1]) / 2
        )

    @property
    def shoulder_center(self) -> tuple:
        return (
            (self.left_shoulder[0] + self.right_shoulder[0]) / 2,
            (self.left_shoulder[1] + self.right_shoulder[1]) / 2
        )

    @property
    def ankle_center(self) -> tuple:
        return (
            (self.left_ankle[0] + self.right_ankle[0]) / 2,
            (self.left_ankle[1] + self.right_ankle[1]) / 2
        )

    def all_keypoints(self) -> list:
        """Trả về danh sách tất cả các điểm mấu chốt để tính toán chuyển động."""
        return [
            self.nose, self.left_shoulder, self.right_shoulder,
            self.left_elbow, self.right_elbow,
            self.left_wrist, self.right_wrist,
            self.left_hip, self.right_hip,
            self.left_knee, self.right_knee,
            self.left_ankle, self.right_ankle
        ]


@dataclass
class DetectionEvent:
    """
    Một sự kiện phát hiện bất thường.
    Được tạo bởi các detector khi phát hiện dấu hiệu nguy hiểm.
    """
    event_type: str              # 'fall', 'seizure', 'immobility'
    confidence: float            # 0.0 - 1.0
    severity: str                # 'low', 'medium', 'high', 'critical'
    timestamp: float = field(default_factory=time.time)
    description: str = ""
    suppressed: bool = False     # True nếu bị chặn bởi phân tích môi trường
    suppression_reason: str = ""

    def to_dict(self) -> dict:
        return {
            'event_type': self.event_type,
            'confidence': round(self.confidence, 3),
            'severity': self.severity,
            'timestamp': self.timestamp,
            'description': self.description,
            'suppressed': self.suppressed,
            'suppression_reason': self.suppression_reason
        }


@dataclass
class AlertInfo:
    """Thông tin cảnh báo được gửi đến thiết bị di động / cơ sở y tế."""
    event: DetectionEvent
    location: str = "Không xác định"
    camera_id: str = "cam_01"
    frame_snapshot: Optional[np.ndarray] = None
    alert_sent: bool = False
    alert_time: float = 0.0

    def format_message(self) -> str:
        """Tạo nội dung tin nhắn cảnh báo."""
        severity_emoji = {
            'low': '⚠️',
            'medium': '🟠',
            'high': '🔴',
            'critical': '🚨'
        }
        event_name = {
            'fall': 'NGÃ ĐỘT NGỘT',
            'seizure': 'CO GIẬT',
            'immobility': 'BẤT ĐỘNG TRÊN SÀN'
        }

        emoji = severity_emoji.get(self.event.severity, '⚠️')
        name = event_name.get(self.event.event_type, self.event.event_type.upper())
        time_str = time.strftime('%H:%M:%S', time.localtime(self.event.timestamp))

        msg = (
            f"{emoji} CẢNH BÁO NGUY CƠ ĐỘT QUỴ {emoji}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 Loại sự kiện: {name}\n"
            f"📊 Mức độ: {self.event.severity.upper()}\n"
            f"🎯 Độ tin cậy: {self.event.confidence:.0%}\n"
            f"⏰ Thời gian: {time_str}\n"
            f"📍 Vị trí: {self.location}\n"
            f"📷 Camera: {self.camera_id}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 Chi tiết: {self.event.description}\n"
            f"\n⚡ Vui lòng kiểm tra ngay!"
        )
        return msg


@dataclass
class SystemStatus:
    """Trạng thái toàn hệ thống để hiển thị trên dashboard."""
    is_running: bool = False
    camera_connected: bool = False
    person_detected: bool = False
    current_risk_level: str = "normal"    # normal, low, medium, high, critical
    active_events: List[DetectionEvent] = field(default_factory=list)
    event_history: List[dict] = field(default_factory=list)
    total_alerts_sent: int = 0
    uptime_seconds: float = 0.0
    fps: float = 0.0
    last_update: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            'is_running': self.is_running,
            'camera_connected': self.camera_connected,
            'person_detected': self.person_detected,
            'current_risk_level': self.current_risk_level,
            'active_events': [e.to_dict() for e in self.active_events],
            'event_history': self.event_history[-50:],  # Last 50 events
            'total_alerts_sent': self.total_alerts_sent,
            'uptime_seconds': round(self.uptime_seconds, 1),
            'fps': round(self.fps, 1),
            'last_update': self.last_update
        }
