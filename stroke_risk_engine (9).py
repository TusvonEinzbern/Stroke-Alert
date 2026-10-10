import time
import cv2
import numpy as np
import logging

from pose_estimator import PoseEstimator
from fall_detector import FallDetector
from seizure_detector import SeizureDetector
from immobility_detector import ImmobilityDetector
from environment_analyzer import EnvironmentAnalyzer
from alert_manager import AlertManager
from models import PoseData, DetectionEvent, AlertInfo, SystemStatus
import config

logger = logging.getLogger(__name__)

class StrokeRiskEngine:
    """
    Hệ thống điều phối chính, kết nối các detector và đánh giá rủi ro tổng thể.
    """
    def __init__(self):
        self.pose_estimator = PoseEstimator()
        self.fall_detector = FallDetector()
        self.seizure_detector = SeizureDetector()
        self.immobility_detector = ImmobilityDetector()
        self.environment_analyzer = EnvironmentAnalyzer()
        self.alert_manager = AlertManager()
        
        self.status = SystemStatus(is_running=True)
        self.frame_count = 0
        self.start_time = time.time()

    def process_frame(self, frame: np.ndarray) -> dict:
        """Xử lý một frame ảnh qua toàn bộ pipeline phát hiện."""
        self.frame_count += 1
        current_time = time.time()
        self.status.uptime_seconds = current_time - self.start_time
        
        if self.status.uptime_seconds > 0:
            self.status.fps = self.frame_count / self.status.uptime_seconds

        annotated_frame = frame.copy()
        
        # 1. Trích xuất tư thế cơ thể
        pose_data = self.pose_estimator.process_frame(frame)
        self.status.person_detected = pose_data is not None and getattr(pose_data, 'is_detected', False)
        
        events = []
        alert_sent = False
        risk_level = 'normal'
        
        if self.status.person_detected:
            # Vẽ skeleton lên frame
            annotated_frame = self.pose_estimator.draw_landmarks(annotated_frame, pose_data)
            
            # 2a. Chạy các module phát hiện (fall, seizure, immobility)
            fall_event = self.fall_detector.update(pose_data, frame)
            seizure_event = self.seizure_detector.update(pose_data, frame)
            immobility_event = self.immobility_detector.update(pose_data, frame)
            
            raw_events = [e for e in [fall_event, seizure_event, immobility_event] if e is not None]
            
            # 2b. Phân tích môi trường (tránh báo động giả)
            env_result = self.environment_analyzer.analyze(frame, pose_data)
            
            # 2c & 2d. Đánh dấu sự kiện bị chặn và lọc theo độ tin cậy
            filtered_events = []
            for event in raw_events:
                if env_result.get('suppress_alert', False):
                    event.suppressed = True
                    event.suppression_reason = env_result.get('reason', 'Đã chặn do phân tích môi trường')
                
                if not event.suppressed and event.confidence >= config.CONFIDENCE_THRESHOLD:
                    filtered_events.append(event)
                    
            events = filtered_events
            
            # 2e. Multi-signal boost (tăng độ tin cậy nếu có nhiều dấu hiệu cùng lúc)
            if len(events) >= 2:
                for event in events:
                    event.confidence = min(1.0, event.confidence + config.MULTI_SIGNAL_BOOST)
                    
            # 2f. Đánh giá mức độ rủi ro tổng hợp
            risk_level = self._assess_risk(events)
            
            # Cập nhật trạng thái
            self.status.current_risk_level = risk_level
            self.status.active_events = events
            for event in events:
                self.status.event_history.append(event.to_dict())
                
            # 2g. Quyết định gửi cảnh báo
            if self._should_send_alert(events):
                highest_risk_event = max(events, key=lambda e: e.confidence)
                alert_info = AlertInfo(event=highest_risk_event, frame_snapshot=frame)
                if self.alert_manager.send_alert(alert_info):
                    alert_sent = True
                    self.status.total_alerts_sent += 1

        # 3. Vẽ thông tin trạng thái lên frame
        self._draw_status_overlay(annotated_frame, risk_level, events)
        self.status.last_update = time.time()
        
        # Lưu frame mới nhất cho dashboard streaming
        self.latest_frame = annotated_frame

        return {
            'pose_data': pose_data,
            'events': events,
            'risk_level': risk_level,
            'alert_sent': alert_sent,
            'annotated_frame': annotated_frame,
            'status': self.status
        }

    def _assess_risk(self, events: list) -> str:
        """Xác định mức độ rủi ro từ danh sách các sự kiện hiện tại."""
        if not events:
            return 'normal'
            
        severities = [e.severity for e in events]
        if 'critical' in severities:
            return 'critical'
            
        if 'high' in severities:
            return 'high'
            
        med_count = severities.count('medium')
        low_count = severities.count('low')
        
        # Nhiều sự kiện vừa/nhỏ kết hợp lại tạo thành rủi ro cao
        if len(events) >= 2 and (med_count > 0 or low_count > 1):
            return 'high'
            
        if med_count > 0:
            return 'medium'
            
        return 'low'

    def _should_send_alert(self, events: list) -> bool:
        """Kiểm tra có nên gửi cảnh báo ra ngoài không (tùy theo mức độ nghiêm trọng)."""
        if not events:
            return False
        return any(e.severity in ['high', 'critical'] for e in events)

    def _draw_status_overlay(self, frame: np.ndarray, risk_level: str, events: list):
        """Vẽ HUD trực quan lên frame (mức độ rủi ro, FPS, sự kiện)."""
        colors = {
            'normal': (0, 255, 0),      # Xanh lá
            'low': (0, 255, 255),       # Vàng
            'medium': (0, 165, 255),    # Cam
            'high': (0, 0, 255),        # Đỏ
            'critical': (0, 0, 255)     # Đỏ
        }
        color = colors.get(risk_level, (255, 255, 255))
        
        # Mức độ rủi ro (Top-left)
        cv2.rectangle(frame, (10, 10), (220, 50), color, -1)
        text_color = (0, 0, 0) if risk_level in ['normal', 'low'] else (255, 255, 255)
        cv2.putText(frame, f"Risk: {risk_level.upper()}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
                    
        # Thông số FPS (Top-right)
        fps_text = f"FPS: {self.status.fps:.1f}"
        (tw, th), _ = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.putText(frame, fps_text, (frame.shape[1] - tw - 20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    
        # Hiển thị các sự kiện (Bottom)
        y_pos = frame.shape[0] - 30
        for event in events:
            event_text = f"{event.event_type.upper()} ({event.severity}): {event.confidence:.0%}"
            cv2.putText(frame, event_text, (20, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            y_pos -= 30

    def get_status(self) -> SystemStatus:
        """Trả về trạng thái hiện tại của toàn hệ thống."""
        return self.status

    def reset(self):
        """Khởi động lại toàn bộ các bộ dò và trạng thái."""
        self.fall_detector.reset()
        self.seizure_detector.reset()
        self.immobility_detector.reset()
        self.status = SystemStatus(is_running=True)
        self.frame_count = 0
        self.start_time = time.time()
