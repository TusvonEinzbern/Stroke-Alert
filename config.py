"""
Stroke Detection System - Configuration
Cấu hình trung tâm cho hệ thống phát hiện đột quỵ.
Điều chỉnh các tham số tại đây để tinh chỉnh độ nhạy của hệ thống.

Quy ước đơn vị:
  - Tọa độ ảnh được chuẩn hóa [0, 1]; y = 0 là đỉnh khung hình.
  - "L" = chiều dài khung xương 2D (mũi→vai→hông→gối→mắt cá) của người đang theo dõi.
    Các ngưỡng chuyển động tính theo L nên KHÔNG phụ thuộc khoảng cách tới camera.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")      # Chứa file model tải về tự động
DATA_DIR = os.path.join(BASE_DIR, "data")          # Chứa safe zones, cache cơ sở y tế


def _float_env(name: str):
    try:
        return float(os.getenv(name, ""))
    except ValueError:
        return None


# ╔══════════════════════════════════════════════════════════╗
# ║                    CAMERA SETTINGS                       ║
# ╚══════════════════════════════════════════════════════════╝
CAMERA_SOURCE = 0
# "0" = webcam mặc định, "1" = webcam thứ 2,
# "rtsp://admin:password@192.168.1.100:554/stream" = IP camera,
# "video.mp4" = file video (dùng để thử nghiệm với dataset té ngã)
CAMERA_ID = "cam_01"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
TARGET_PROCESS_FPS = 15               # Số frame xử lý mỗi giây (tiết kiệm CPU)
PROCESS_EVERY_N_FRAMES = max(1, int(CAMERA_FPS / TARGET_PROCESS_FPS))
CAMERA_OFFLINE_ALERT_SECONDS = 120    # Mất camera quá lâu → gửi thông báo (hệ thống "mù")
LOW_LIGHT_THRESHOLD = 40              # Độ sáng trung bình < giá trị này → cảnh báo thiếu sáng

# ╔══════════════════════════════════════════════════════════╗
# ║                 POSE ESTIMATION (MediaPipe)              ║
# ╚══════════════════════════════════════════════════════════╝
POSE_MODEL_COMPLEXITY = 2             # 0 = lite (máy yếu), 1 = full, 2 = heavy (chính xác nhất)
POSE_MODEL_VARIANT = {0: "lite", 1: "full", 2: "heavy"}.get(POSE_MODEL_COMPLEXITY, "full")
POSE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    f"pose_landmarker_{POSE_MODEL_VARIANT}/float16/latest/pose_landmarker_{POSE_MODEL_VARIANT}.task"
)
POSE_MODEL_PATH = os.path.join(ASSETS_DIR, f"pose_landmarker_{POSE_MODEL_VARIANT}.task")
MAX_POSES = 2                         # Nhận diện tối đa 2 người, theo dõi người gần vị trí cũ nhất
MIN_DETECTION_CONFIDENCE = 0.75
MIN_TRACKING_CONFIDENCE = 0.75
MIN_LANDMARK_VISIBILITY = 0.5         # Bỏ qua điểm bị che khuất khi phân tích co giật / cử chỉ

# ╔══════════════════════════════════════════════════════════╗
# ║                  POSTURE CLASSIFICATION                  ║
# ║  height_ratio = độ cao theo phương dọc / L               ║
# ║  Đứng ≈ 0.9-1.0 | Ngồi ghế ≈ 0.7 | Nằm ≈ 0.1-0.35         ║
# ╚══════════════════════════════════════════════════════════╝
UPRIGHT_ANGLE = 60.0                  # Góc thân ≥ 60° và height_ratio ≥ 0.8 → đứng
UPRIGHT_HEIGHT_RATIO = 0.8
LYING_ANGLE = 45.0                    # Góc thân < 45° → thân nằm ngang
LYING_HEIGHT_RATIO = 0.55             # height_ratio < 0.55 (kèm thân ngang) → nằm
LYING_ASPECT_RATIO = 1.0              # Khung bao rộng > cao → nằm
CRUMPLED_HEIGHT_RATIO = 0.35          # height_ratio rất thấp → gục/co quắp dù góc thân bất kỳ

# ╔══════════════════════════════════════════════════════════╗
# ║                  FALL DETECTION                          ║
# ║  Ngã = hạ thấp NHANH + kết thúc ở tư thế nằm/gục         ║
# ╚══════════════════════════════════════════════════════════╝
FALL_VELOCITY_THRESHOLD = 0.9         # Tốc độ rơi của thân (L/giây). Ngồi xuống ≈ 0.2-0.6, ngã > 1.0
FALL_VELOCITY_WINDOW = 0.3            # Khoảng thời gian dùng để đo vận tốc (giây)
FALL_DETECTION_WINDOW = 2.0           # Từ lúc rơi nhanh đến lúc nằm phải ≤ 2 giây
FALL_RECOVERY_TIMEOUT = 3.0           # Chờ tự đứng dậy trước khi xác nhận ngã (giây)
FALL_GETUP_CONFIRM = 1.0              # Phải đứng thẳng liên tục ≥ 1 giây mới tính là đã dậy
FALL_LOST_TIMEOUT = 5.0               # Mất dấu người ngay sau khi rơi nhanh quá 5 giây → cảnh báo

# ╔══════════════════════════════════════════════════════════╗
# ║                SEIZURE DETECTION                         ║
# ║  Co giật = tay/chân dao động nhịp nhàng, tần số cao,     ║
# ║  trong khi thân người nằm yên một chỗ                    ║
# ╚══════════════════════════════════════════════════════════╝
SEIZURE_WINDOW_SECONDS = 3.0          # Cửa sổ trượt phân tích (giây)
SEIZURE_FREQUENCY_MIN = 2.0           # Tần số dao động tối thiểu (Hz)
SEIZURE_HYSTERESIS = 0.04             # Biên độ đảo chiều tối thiểu (L) - lọc nhiễu rung landmark
SEIZURE_MIN_BODY_PARTS = 2            # Số bộ phận dao động đồng thời tối thiểu
SEIZURE_MIN_DURATION = 2.0            # Phải kéo dài thêm ≥ 2 giây mới xác nhận
SEIZURE_MAX_TORSO_SHIFT = 0.25        # Thân di chuyển > 0.25 L trong cửa sổ → đang đi lại, không phải co giật
SEIZURE_REQUIRE_LOW_POSTURE = True    # Chỉ xét khi nằm/gục → loại bỏ vỗ tay, tập thể dục, đi bộ
SEIZURE_MIN_FPS = 8.0                 # FPS thấp hơn → không đủ dữ liệu để đo tần số
SEIZURE_REPEAT_INTERVAL = 15.0        # Co giật kéo dài → phát lại sự kiện mỗi 15 giây

# ╔══════════════════════════════════════════════════════════╗
# ║              IMMOBILITY DETECTION                        ║
# ║  Nằm bất động (ngoài giường/sofa) → leo thang theo thời gian ║
# ╚══════════════════════════════════════════════════════════╝
IMMOBILITY_MOVEMENT_THRESHOLD = 0.15  # Dịch chuyển trung bình > 0.05 L so với tư thế ban đầu → có cử động
IMMOBILITY_SEVERITY_STEPS = [         # (giây bất động, mức độ). Cảnh báo ra ngoài từ mức 'high'
    (3, "low"),
    (6, "medium"),
    (10, "high"),
    (15, "critical"),
]
IMMOBILITY_TIMEOUT = IMMOBILITY_SEVERITY_STEPS[0][0]

# ╔══════════════════════════════════════════════════════════╗
# ║             ENVIRONMENT ANALYSIS                         ║
# ║  Giường / sofa (tự động nhận diện) + vùng an toàn tự vẽ  ║
# ╚══════════════════════════════════════════════════════════╝
ENVIRONMENT_ANALYSIS_ENABLED = True
FURNITURE_DETECTION_ENABLED = True    # Dùng MediaPipe ObjectDetector (EfficientDet-Lite0, COCO)
OBJECT_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/object_detector/"
    "efficientdet_lite0/float16/latest/efficientdet_lite0.tflite"
)
OBJECT_MODEL_PATH = os.path.join(ASSETS_DIR, "efficientdet_lite0.tflite")
FURNITURE_LABELS = {"bed", "couch", "bench"}   # Bề mặt nằm nghỉ hợp lệ
FURNITURE_DETECTION_CONFIDENCE = 0.35
FURNITURE_REFRESH_SECONDS = 5.0       # Đồ nội thất ít di chuyển → chỉ quét lại mỗi 5 giây
FURNITURE_MEMORY_SECONDS = 600.0      # Nhớ vị trí giường kể cả khi bị người nằm che khuất
FURNITURE_ON_TOP_MARGIN = 0.10        # Phần thấp nhất của cơ thể phải cao hơn mép dưới giường 10%
                                      # → phân biệt "nằm TRÊN giường" với "ngã xuống sàn TRƯỚC giường"
SAFE_ZONES_FILE = os.path.join(DATA_DIR, "safe_zones.json")
SAFE_ZONES = []                       # [{'x1':0.1,'y1':0.5,'x2':0.4,'y2':0.9,'label':'bed'}]

# ╔══════════════════════════════════════════════════════════╗
# ║              RISK ASSESSMENT                             ║
# ╚══════════════════════════════════════════════════════════╝
CONFIDENCE_THRESHOLD = 0.55           # Độ tin cậy tối thiểu để tính là sự kiện hợp lệ
MULTI_SIGNAL_BOOST = 0.15             # Nhiều loại tín hiệu cùng lúc → tăng độ tin cậy
POST_FALL_ESCALATION_WINDOW = 300.0   # Bất động trong 5 phút sau cú ngã → tăng 1 mức nghiêm trọng
RISK_HOLD_SECONDS = 30.0              # Giữ mức rủi ro trên màn hình trong 30 giây sau sự kiện

# ╔══════════════════════════════════════════════════════════╗
# ║                 ALERT SYSTEM                             ║
# ╚══════════════════════════════════════════════════════════╝
ALERT_COOLDOWN = 60                   # Giây giữa 2 cảnh báo CÙNG LOẠI (mức nặng hơn thì gửi ngay)
ALERT_CONFIRM_SECONDS = 15            # Đếm ngược trước khi gửi: còi tại chỗ, người dùng có thể hủy
ALERT_IMMEDIATE_TYPES = {"seizure"}   # Các loại gửi NGAY, không đếm ngược
CANCEL_GESTURE_SECONDS = 2.0          # Giơ 2 tay lên quá đầu trong 2 giây = "Tôi ổn" → hủy cảnh báo
AUTO_CANCEL_IF_UPRIGHT_SECONDS = 3.0  # Đứng dậy vững trong 3 giây khi đang đếm ngược → hủy
SEND_INFO_NOTIFICATIONS = True        # Gửi tin "thông tin" (ngã nhưng đã dậy, hủy cảnh báo, mất camera)
ALERT_INCLUDE_SNAPSHOT = True         # Gửi kèm ảnh chụp camera
ALERT_RETRY = 2                       # Số lần thử lại khi gửi thất bại

# --- Telegram Bot (kênh chính tới điện thoại) ---
TELEGRAM_ENABLED = True
TELEGRAM_BOT_TOKEN = os.getenv("STROKE_TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_IDS = [
    cid.strip() for cid in os.getenv("STROKE_TELEGRAM_CHAT_IDS", "").split(",") if cid.strip()
]

# --- Email (SMTP) ---
EMAIL_ENABLED = bool(os.getenv("STROKE_EMAIL_FROM"))
EMAIL_SMTP_SERVER = os.getenv("STROKE_SMTP_SERVER", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("STROKE_SMTP_PORT", "587"))
EMAIL_FROM = os.getenv("STROKE_EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("STROKE_EMAIL_PASSWORD", "")   # Gmail: dùng App Password
EMAIL_TO = [a.strip() for a in os.getenv("STROKE_EMAIL_TO", "").split(",") if a.strip()]

# --- Âm thanh tại chỗ ---
SOUND_ALERT_ENABLED = True

# ╔══════════════════════════════════════════════════════════╗
# ║          LOCATION & NEAREST MEDICAL FACILITY             ║
# ╚══════════════════════════════════════════════════════════╝
HOME_ADDRESS = os.getenv("STROKE_HOME_ADDRESS", "")
HOME_LATITUDE = _float_env("STROKE_HOME_LAT")
HOME_LONGITUDE = _float_env("STROKE_HOME_LON")
EMERGENCY_NUMBER = "115"
MEDICAL_FACILITIES = [
    # Khai báo thủ công (ưu tiên). Có email/telegram_chat_id → cơ sở đó nhận cảnh báo trực tiếp.
    # {"name": "Bệnh viện ABC", "lat": 10.77, "lon": 106.69, "phone": "028...",
    #  "email": "capcuu@abc.vn", "telegram_chat_id": "", "type": "hospital"},
]
AUTO_FIND_FACILITIES = True           # Tự tìm bệnh viện gần nhất qua OpenStreetMap (miễn phí)
FACILITY_SEARCH_RADIUS_M = 5000
FACILITIES_CACHE_FILE = os.path.join(DATA_DIR, "facilities_cache.json")
FACILITIES_CACHE_DAYS = 30
NOTIFY_NEAREST_FACILITY = True        # Gửi cảnh báo tới cơ sở gần nhất nếu có thông tin liên hệ

# ╔══════════════════════════════════════════════════════════╗
# ║                  DASHBOARD                               ║
# ╚══════════════════════════════════════════════════════════╝
DASHBOARD_ENABLED = True
DASHBOARD_HOST = "0.0.0.0"            # 0.0.0.0 = xem được từ điện thoại cùng mạng WiFi
DASHBOARD_PORT = 5000
DASHBOARD_PASSWORD = os.getenv("STROKE_DASHBOARD_PASSWORD", "")  # Đặt để bảo vệ quyền riêng tư

# ╔══════════════════════════════════════════════════════════╗
# ║                 LOGGING                                  ║
# ╚══════════════════════════════════════════════════════════╝
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(BASE_DIR, "stroke_detection.log")

# --- NTFY.SH Báo động từ xa ---
NTFY_TOPIC = "healthguard_batan_888"
