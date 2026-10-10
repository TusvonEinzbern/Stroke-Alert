import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import config
import logging
from models import AlertInfo

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self):
        self.last_alert_time = 0
        self.alert_cooldown = 10.0 # Không gửi liên tục
        
    def send_alert(self, alert_info: AlertInfo) -> bool:
        import time
        current_time = time.time()
        if current_time - self.last_alert_time < self.alert_cooldown:
            return False
            
        self.last_alert_time = current_time
        logger.warning(f"!!! PHÁT ĐI CẢNH BÁO: {alert_info.event.event_type} - Mức độ: {alert_info.event.severity}")
        
        # 1. Gửi qua Ntfy (Điện thoại)
        if getattr(config, 'NTFY_TOPIC', ''):
            threading.Thread(target=self._send_ntfy, args=(alert_info,), daemon=True).start()
            
        # 2. Gửi qua Email
        if getattr(config, 'RECEIVER_EMAIL', '') and getattr(config, 'SMTP_USER', '') and getattr(config, 'SMTP_PASS', ''):
            threading.Thread(target=self._send_email, args=(alert_info,), daemon=True).start()
            
        return True

    def _get_patient_info_str(self):
        name = getattr(config, 'PATIENT_NAME', 'Chưa cập nhật')
        age = getattr(config, 'PATIENT_AGE', 'N/A')
        phone = getattr(config, 'EMERGENCY_PHONE', 'Chưa cập nhật')
        return f"Bệnh nhân: {name} ({age} tuổi)\\nSĐT Khẩn cấp: {phone}"

    def _send_ntfy(self, alert_info: AlertInfo):
        import requests
        try:
            topic = config.NTFY_TOPIC
            patient_info = self._get_patient_info_str()
            message = f"Phát hiện: {alert_info.event.description}\\nMức độ: {alert_info.event.severity.upper()}\\n\\n{patient_info}"
            
            headers = {
                "Title": f"CẢNH BÁO Y TẾ ĐỎ: {alert_info.event.event_type.upper()}",
                "Priority": "high",
                "Tags": "warning,skull"
            }
            requests.post(f"https://ntfy.sh/{topic}", data=message.encode('utf-8'), headers=headers, timeout=5)
            logger.info("Đã gửi cảnh báo Ntfy")
        except Exception as e:
            logger.error(f"Lỗi Ntfy: {e}")

    def _send_email(self, alert_info: AlertInfo):
        try:
            sender = config.SMTP_USER
            password = config.SMTP_PASS
            receiver = config.RECEIVER_EMAIL
            
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = receiver
            msg['Subject'] = f"[KHẨN CẤP] CẢNH BÁO Y TẾ - {alert_info.event.event_type.upper()}"
            
            patient_info = self._get_patient_info_str()
            body = f"""
            HỆ THỐNG GIÁM SÁT Y TẾ AI PHÁT HIỆN SỰ CỐ:
            
            - Loại sự cố: {alert_info.event.description}
            - Mức độ: {alert_info.event.severity.upper()}
            - Độ tin cậy AI: {alert_info.event.confidence*100:.1f}%
            
            THÔNG TIN BỆNH NHÂN:
            {patient_info}
            
            Vui lòng kiểm tra ngay lập tức!
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Đã gửi cảnh báo Email tới {receiver}")
        except Exception as e:
            logger.error(f"Lỗi gửi Email: {e}")
