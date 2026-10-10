import cv2
import time
import config

class CameraManager:
    """
    Quản lý kết nối với camera (webcam hoặc IP camera qua RTSP).
    """
    def __init__(self, source=None):
        self.source = source if source is not None else config.CAMERA_SOURCE
        self.cap = None

    def connect(self) -> bool:
        """Mở kết nối camera."""
        if self.cap is not None:
            self.cap.release()
            
        src = int(self.source) if str(self.source).isdigit() else self.source
        if isinstance(src, int):
            self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(src)
            
        if not self.cap.isOpened():
            print(f"Lỗi: Không thể kết nối tới nguồn camera: {self.source}")
            return False
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
        print(f"Đã kết nối camera: {self.source}")
        return True

    def read_frame(self) -> tuple:
        """
        Đọc một frame từ camera.
        Returns: (success_bool, frame_array)
        """
        if not self.is_opened():
            if not self.reconnect():
                return False, None
                
        success, frame = self.cap.read()
        if not success:
            print("Cảnh báo: Không thể đọc frame, đang thử kết nối lại...")
            if self.reconnect():
                success, frame = self.cap.read()
            
        return success, frame if success else None

    def release(self):
        """Giải phóng camera."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("Đã giải phóng kết nối camera.")

    def is_opened(self) -> bool:
        """Kiểm tra trạng thái kết nối."""
        return self.cap is not None and self.cap.isOpened()

    def reconnect(self) -> bool:
        """Thử kết nối lại khi mất kết nối (tối đa 3 lần)."""
        for attempt in range(3):
            print(f"Thử kết nối lại lần {attempt + 1}/3...")
            time.sleep(2.0)
            if self.connect():
                print("Kết nối lại thành công.")
                return True
        print("Kết nối lại thất bại sau 3 lần thử.")
        return False

    def get_info(self) -> dict:
        """Lấy thông tin của camera hiện tại."""
        if not self.is_opened():
            return {"status": "disconnected"}
            
        return {
            "source": self.source,
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)),
            "status": "connected"
        }
