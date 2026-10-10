import time
import requests
import threading
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import cv2
import numpy as np
import platform

from models import AlertInfo
import config

class AlertManager:
    """
    Quản lý việc gửi cảnh báo qua Telegram, Email, và âm thanh tại chỗ.
    """
    def __init__(self):
        self.last_alert_time = 0.0

    def send_alert(self, alert: AlertInfo) -> bool:
        """Gửi cảnh báo qua tất cả các kênh được kích hoạt."""
        if not self._check_cooldown():
            return False

        self.last_alert_time = time.time()
        alert.alert_sent = True
        alert.alert_time = self.last_alert_time
        
        message = alert.format_message()
        photo_bytes = None
        
        if config.ALERT_INCLUDE_SNAPSHOT and alert.frame_snapshot is not None:
            photo_bytes = self._encode_frame(alert.frame_snapshot)

        # Sử dụng thread để không block luồng xử lý video chính
        if config.SOUND_ALERT_ENABLED:
            threading.Thread(target=self._play_sound_alert, daemon=True).start()

        # Always send NTFY if configured (no need for token/chat_id)
        if hasattr(config, 'NTFY_TOPIC') and config.NTFY_TOPIC:
            threading.Thread(target=self._send_ntfy, args=(message, photo_bytes), daemon=True).start()

        if config.TELEGRAM_ENABLED and config.TELEGRAM_BOT_TOKEN:
            threading.Thread(target=self._send_telegram, args=(message, photo_bytes), daemon=True).start()

        if config.EMAIL_ENABLED and config.EMAIL_TO:
            subject = f"CẢNH BÁO ĐỘT QUỴ - {alert.event.event_type.upper()}"
            threading.Thread(target=self._send_email, args=(subject, message, photo_bytes), daemon=True).start()

        return True

    def _send_telegram(self, message: str, photo_bytes: bytes = None) -> bool:
        """Gửi cảnh báo qua Telegram Bot API."""
        success = True
        for chat_id in config.TELEGRAM_CHAT_IDS:
            try:
                if photo_bytes:
                    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto"
                    files = {'photo': ('snapshot.jpg', photo_bytes, 'image/jpeg')}
                    data = {'chat_id': chat_id, 'caption': message}
                    res = requests.post(url, files=files, data=data, timeout=10)
                else:
                    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
                    data = {'chat_id': chat_id, 'text': message}
                    res = requests.post(url, data=data, timeout=10)
                
                if not res.ok:
                    print(f"Telegram API Error: {res.text}")
                    success = False
            except Exception as e:
                print(f"Telegram exception: {e}")
                success = False
        return success

    def _send_ntfy(self, message: str, photo_bytes: bytes = None) -> bool:
        """Gửi cảnh báo qua Ntfy.sh (Miễn phí, không cần đăng ký)."""
        try:
            url = f"https://ntfy.sh/{config.NTFY_TOPIC}"
            headers = {
                "Title": "🚨 HEALTHGUARD AI: CẢNH BÁO ĐỘT QUỴ",
                "Priority": "urgent",
                "Tags": "warning,skull"
            }
            if photo_bytes:
                requests.post(url, data=photo_bytes, headers=headers, timeout=10)
            else:
                requests.post(url, data=message.encode('utf-8'), headers=headers, timeout=10)
            return True
        except Exception as e:
            print(f"Ntfy exception: {e}")
            return False

    def _send_email(self, subject: str, body: str, attachment: bytes = None) -> bool:
        """Gửi cảnh báo qua Email SMTP."""
        try:
            msg = MIMEMultipart()
            msg['From'] = config.EMAIL_FROM
            msg['To'] = ", ".join(config.EMAIL_TO)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if attachment:
                img = MIMEImage(attachment, name="snapshot.jpg")
                msg.attach(img)
                
            server = smtplib.SMTP(config.EMAIL_SMTP_SERVER, config.EMAIL_SMTP_PORT)
            server.starttls()
            server.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Email exception: {e}")
            return False

    def _play_sound_alert(self):
        """Phát âm thanh cảnh báo tại chỗ (Windows)."""
        if platform.system() == "Windows":
            try:
                import winsound
                # Play 3 rapid beeps
                for _ in range(3):
                    winsound.Beep(2000, 400)
                    time.sleep(0.1)
            except ImportError:
                pass

    def _check_cooldown(self) -> bool:
        """Kiểm tra thời gian chờ giữa các lần cảnh báo để tránh spam."""
        return (time.time() - self.last_alert_time) >= config.ALERT_COOLDOWN

    def _encode_frame(self, frame: np.ndarray) -> bytes:
        """Mã hóa frame thành JPEG bytes."""
        success, encoded = cv2.imencode('.jpg', frame)
        if success:
            return encoded.tobytes()
        return b""
