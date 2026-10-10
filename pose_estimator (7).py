import cv2
import math
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
from typing import Tuple, List

from models import PoseData
import config

class PoseEstimator:
    """
    Wrapper cho MediaPipe Pose estimation (dùng Tasks API phiên bản mới).
    Trích xuất các điểm mốc cơ thể (landmarks) và tính toán các chỉ số cơ bản.
    """
    def __init__(self):
        # Tải cấu hình và khởi tạo PoseLandmarker
        base_options = python.BaseOptions(model_asset_path=config.POSE_MODEL_PATH)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            num_poses=config.MAX_POSES,
            min_pose_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_pose_presence_confidence=config.MIN_TRACKING_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
            output_segmentation_masks=False
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def process_frame(self, frame: np.ndarray) -> PoseData:
        """
        Xử lý một khung hình, trích xuất landmarks và tính toán PoseData.
        
        Args:
            frame: Ảnh numpy array (BGR).
            
        Returns:
            PoseData: Đối tượng chứa dữ liệu tư thế.
        """
        # MediaPipe yêu cầu ảnh RGB
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        results = self.detector.detect(mp_image)
        
        pose_data = PoseData(timestamp=time.time())
        
        if not results.pose_landmarks:
            pose_data.is_detected = False
            return pose_data
            
        pose_data.is_detected = True
        
        # Lấy người đầu tiên
        landmarks = results.pose_landmarks[0]
        pose_data.landmarks = landmarks
        pose_data.detection_confidence = 0.9 
        
        # Các chỉ số điểm mốc theo chuẩn của MediaPipe Pose (0: nose, 11: left shoulder, v.v.)
        # Tham khảo: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
        def get_pt(lm_idx) -> Tuple[float, float]:
            lm = landmarks[lm_idx]
            return (lm.x, lm.y)
            
        pose_data.nose = get_pt(0)
        pose_data.left_eye = get_pt(2)
        pose_data.right_eye = get_pt(5)
        
        pose_data.left_shoulder = get_pt(11)
        pose_data.right_shoulder = get_pt(12)
        
        pose_data.left_elbow = get_pt(13)
        pose_data.right_elbow = get_pt(14)
        
        pose_data.left_wrist = get_pt(15)
        pose_data.right_wrist = get_pt(16)
        
        pose_data.left_hip = get_pt(23)
        pose_data.right_hip = get_pt(24)
        
        pose_data.left_knee = get_pt(25)
        pose_data.right_knee = get_pt(26)
        
        pose_data.left_ankle = get_pt(27)
        pose_data.right_ankle = get_pt(28)
        
        # Tính toán các chỉ số phái sinh
        shoulder_center = pose_data.shoulder_center
        hip_center = pose_data.hip_center
        ankle_center = pose_data.ankle_center
        
        # Trung tâm thân (trung bình vai + hông)
        pose_data.torso_center = (
            (shoulder_center[0] + hip_center[0]) / 2,
            (shoulder_center[1] + hip_center[1]) / 2
        )
        
        # Chiều cao cơ thể = độ trải theo phương DỌC của các keypoint.
        # Lưu ý: Bỏ qua cánh tay (wrist, elbow) để tránh việc giang tay ra khiến bbox bị rộng (sai lầm là đang nằm)
        core_keypoints = [
            pose_data.nose,
            pose_data.left_shoulder, pose_data.right_shoulder,
            pose_data.left_hip, pose_data.right_hip,
            pose_data.left_knee, pose_data.right_knee,
            pose_data.left_ankle, pose_data.right_ankle
        ]
        xs = [p[0] for p in core_keypoints]
        ys = [p[1] for p in core_keypoints]
        pose_data.body_height = max(ys) - min(ys)

        # Tỷ lệ khung bao (rộng / cao)
        bbox_w = max(xs) - min(xs)
        pose_data.bbox_aspect = bbox_w / pose_data.body_height if pose_data.body_height > 1e-6 else 0.0

        # Góc thân người so với mặt phẳng ngang (vai → hông), quy về [0°, 90°]:
        dx = abs(shoulder_center[0] - hip_center[0])
        dy = abs(shoulder_center[1] - hip_center[1])
        pose_data.body_angle = math.degrees(math.atan2(dy, dx))

        return pose_data

    def draw_landmarks(self, frame: np.ndarray, pose_data: PoseData) -> np.ndarray:
        """
        Vẽ khung xương lên hình ảnh (Mượt mà + Nịnh mắt / Glowing Aesthetic).
        """
        output_frame = frame.copy()
        if pose_data.is_detected and pose_data.landmarks:
            h, w = output_frame.shape[:2]

            # Khởi tạo mảng lưu trữ landmarks đã làm mượt (Smoothing bằng EMA)
            if not hasattr(self, 'smoothed_landmarks') or self.smoothed_landmarks is None:
                self.smoothed_landmarks = [(lm.x, lm.y, lm.visibility) for lm in pose_data.landmarks]
            else:
                alpha = 0.6 # Hệ số làm mượt (0 < alpha <= 1, nhỏ thì mượt hơn nhưng chậm hơn)
                new_smoothed = []
                for i, lm in enumerate(pose_data.landmarks):
                    old_x, old_y, old_v = self.smoothed_landmarks[i]
                    # Nếu điểm ảnh vừa xuất hiện trở lại, không làm mượt (tránh bóng mờ)
                    if lm.visibility > config.MIN_LANDMARK_VISIBILITY and old_v < config.MIN_LANDMARK_VISIBILITY:
                        new_smoothed.append((lm.x, lm.y, lm.visibility))
                    else:
                        sx = old_x + alpha * (lm.x - old_x)
                        sy = old_y + alpha * (lm.y - old_y)
                        new_smoothed.append((sx, sy, lm.visibility))
                self.smoothed_landmarks = new_smoothed

            # --- KHỞI TẠO LỚP ĐỔ BÓNG (GLOW LAYER) ---
            overlay = output_frame.copy()

            # Các định nghĩa nối xương
            connections_body = [
                (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # tay và vai
                (11, 23), (12, 24), (23, 24), # thân
                (23, 25), (25, 27), (24, 26), (26, 28) # chân
            ]
            
            # Khuôn mắt trái (1,2,3), Mắt phải (4,5,6), Khuôn miệng (9,10)
            connections_face = [
                (1, 2), (2, 3), # Mắt trái
                (4, 5), (5, 6), # Mắt phải
                (9, 10)         # Miệng
            ]

            # Helper function để lấy tọa độ
            def get_pt(idx):
                x, y, v = self.smoothed_landmarks[idx]
                return (int(x * w), int(y * h)) if v > config.MIN_LANDMARK_VISIBILITY else None

            # 1. Vẽ các đường nối thân (Neon Teal) - Viền mỏng lại
            for connection in connections_body:
                p1, p2 = get_pt(connection[0]), get_pt(connection[1])
                if p1 and p2:
                    # Đường Glow mỏng
                    cv2.line(overlay, p1, p2, (255, 191, 0), 4, cv2.LINE_AA) 
                    # Đường Core 
                    cv2.line(output_frame, p1, p2, (255, 255, 100), 1, cv2.LINE_AA)

            # 2. Vẽ các đường nối khuôn mặt (Neon Pink/Purple) - Phân tách rõ ràng
            for connection in connections_face:
                p1, p2 = get_pt(connection[0]), get_pt(connection[1])
                if p1 and p2:
                    cv2.line(overlay, p1, p2, (200, 0, 255), 2, cv2.LINE_AA)
                    cv2.line(output_frame, p1, p2, (255, 100, 255), 1, cv2.LINE_AA)

            # --- TRỘN LỚP GLOW VỚI FRAME GỐC ---
            cv2.addWeighted(overlay, 0.4, output_frame, 0.6, 0, output_frame)

            # 3. Vẽ các chấm khớp cực kỳ thanh mảnh (Loại bỏ chấm to)
            for i in range(len(self.smoothed_landmarks)):
                pt = get_pt(i)
                if not pt: continue

                if i in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
                    # Mắt, mũi, miệng -> Chấm siêu nhỏ
                    cv2.circle(output_frame, pt, 2, (255, 100, 255), -1, cv2.LINE_AA)
                
                elif i in [15, 16, 17, 18, 19, 20, 21, 22]:
                    # Bàn tay, ngón tay -> Chấm nhỏ màu cam
                    cv2.circle(output_frame, pt, 3, (0, 165, 255), -1, cv2.LINE_AA) 
                    cv2.circle(output_frame, pt, 1, (255, 255, 255), -1, cv2.LINE_AA)

                else:
                    # Các khớp thân/chân -> Chấm nhỏ tinh tế
                    cv2.circle(output_frame, pt, 3, (255, 191, 0), -1, cv2.LINE_AA)
                    cv2.circle(output_frame, pt, 1, (255, 255, 255), -1, cv2.LINE_AA)

        return output_frame

    def close(self):
        """Giải phóng tài nguyên."""
        self.detector.close()
