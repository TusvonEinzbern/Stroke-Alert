import threading
import time
import cv2
import customtkinter as ctk
from PIL import Image
import numpy as np

import config
from camera_manager import CameraManager
from stroke_risk_engine import StrokeRiskEngine
from models import SystemStatus

# Thiết lập giao diện CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StrokeDetectionApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Stroke Detection Monitor - Pro Edition")
        self.geometry("1100x700")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Trạng thái hệ thống
        self.running = False
        self.camera = None
        self.engine = None
        self.current_frame = None
        self.system_status = None
        
        # Grid layout chính
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_main_view()
        self.setup_instructions_view()

        # Mặc định hiện trang Dashboard
        self.show_dashboard()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="STROKE AI", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="💻 Giám sát Camera", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_instructions = ctk.CTkButton(self.sidebar, text="📚 Hướng dẫn & Cài đặt", command=self.show_instructions)
        self.btn_instructions.grid(row=2, column=0, padx=20, pady=10)

        # Control Panel
        self.control_frame = ctk.CTkFrame(self.sidebar)
        self.control_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        
        self.btn_start = ctk.CTkButton(self.control_frame, text="▶ Khởi động", fg_color="green", hover_color="darkgreen", command=self.start_system)
        self.btn_start.pack(pady=10, padx=10, fill="x")

        self.btn_stop = ctk.CTkButton(self.control_frame, text="⏹ Dừng", fg_color="red", hover_color="darkred", command=self.stop_system, state="disabled")
        self.btn_stop.pack(pady=10, padx=10, fill="x")

        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Trạng thái: Đang tắt", text_color="gray")
        self.lbl_status.grid(row=5, column=0, padx=20, pady=20, sticky="s")

    def setup_main_view(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Video Section
        self.video_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.video_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.lbl_video = ctk.CTkLabel(self.video_frame, text="Video Stream Trống\nHãy nhấn 'Khởi động' để kết nối Camera")
        self.lbl_video.pack(expand=True, fill="both", padx=10, pady=10)

        # Metrics & Logs Section
        self.info_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.lbl_risk_title = ctk.CTkLabel(self.info_frame, text="MỨC ĐỘ RỦI RO", font=ctk.CTkFont(weight="bold"))
        self.lbl_risk_title.pack(pady=(20, 5))

        self.lbl_risk_value = ctk.CTkLabel(self.info_frame, text="BÌNH THƯỜNG", font=ctk.CTkFont(size=20, weight="bold"), fg_color="green", corner_radius=5)
        self.lbl_risk_value.pack(pady=5, ipadx=10, ipady=5)

        # Stats
        self.lbl_fps = ctk.CTkLabel(self.info_frame, text="FPS: 0.0")
        self.lbl_fps.pack(pady=5)
        
        self.lbl_person = ctk.CTkLabel(self.info_frame, text="Phát hiện người: Không")
        self.lbl_person.pack(pady=5)

        # History Box
        ctk.CTkLabel(self.info_frame, text="Nhật ký Sự kiện:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5))
        self.log_box = ctk.CTkTextbox(self.info_frame, width=200, height=300)
        self.log_box.pack(pady=5, padx=10, fill="both", expand=True)

    def setup_instructions_view(self):
        self.inst_frame = ctk.CTkFrame(self, corner_radius=10)
        
        # Welcome
        lbl_title = ctk.CTkLabel(self.inst_frame, text="📖 Hướng Dẫn Sử Dụng Hệ Thống", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_title.pack(pady=20)

        textbox = ctk.CTkTextbox(self.inst_frame, wrap="word", font=ctk.CTkFont(size=14))
        textbox.pack(expand=True, fill="both", padx=20, pady=20)
        
        instructions = """CHÀO MỪNG BẠN ĐẾN VỚI AI STROKE DETECTION (Phiên bản App Desktop)

Hệ thống được thiết kế chuyên nghiệp với các thuật toán học máy (MediaPipe) để phân tích cử động cơ thể và đưa ra cảnh báo sớm về các nguy cơ đột quỵ như:
1. Té ngã đột ngột.
2. Co giật cục bộ.
3. Nằm bất động trên sàn nhà quá thời gian an toàn.

⚙️ CÁCH SỬ DỤNG:
- Cột bên trái: Bấm "Khởi động" để bật camera và bắt đầu quá trình giám sát AI.
- Nếu bạn thấy có rủi ro giả (False Positive) khi nằm ngủ: Hệ thống có AI tự động nhận diện Giường/Sofa (Furniture Detection) để bỏ qua các cảnh báo khi bạn đang nghỉ ngơi trên giường.
- Bảng Nhật ký sự kiện sẽ lưu lại thời gian và mức độ rủi ro ngay khi phát hiện.

📱 CÀI ĐẶT CẢNH BÁO TỪ XA (TELEGRAM):
Để hệ thống tự động gửi tin nhắn & hình ảnh khẩn cấp về điện thoại của bạn:
1. Mở file 'config.py' trong thư mục cài đặt.
2. Sửa dòng: TELEGRAM_ENABLED = True
3. Thay thế biến TELEGRAM_BOT_TOKEN bằng mã Token từ @BotFather.
4. Thay thế biến TELEGRAM_CHAT_IDS bằng ID Telegram của bạn.
Lưu file config lại và bật lại app là xong!

📷 ĐỔI CAMERA:
Mở file 'config.py', sửa biến CAMERA_SOURCE:
- "0": Webcam laptop mặc định
- "1": Webcam USB cắm ngoài
- "rtsp://...": Camera an ninh Wi-Fi (IP Camera)

Bản quyền (C) Hệ thống phân tích chuyển động đồ án sinh viên.
"""
        textbox.insert("0.0", instructions)
        textbox.configure(state="disabled")

    def show_dashboard(self):
        self.inst_frame.grid_forget()
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_instructions(self):
        self.main_frame.grid_forget()
        self.inst_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def start_system(self):
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text="Trạng thái: Khởi động...", text_color="yellow")

        # Khởi tạo engine
        self.engine = StrokeRiskEngine()
        self.camera = CameraManager(config.CAMERA_SOURCE)
        
        if not self.camera.connect():
            self.lbl_status.configure(text="Lỗi: Không tìm thấy Camera", text_color="red")
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            return

        self.running = True
        self.lbl_status.configure(text="Trạng thái: Đang giám sát", text_color="green")
        self.log_message("Hệ thống đã bắt đầu giám sát.")

        # Thread phân tích
        self.ai_thread = threading.Thread(target=self.ai_loop)
        self.ai_thread.daemon = True
        self.ai_thread.start()

        # Bắt đầu update GUI
        self.update_gui()

    def stop_system(self):
        self.running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text="Trạng thái: Đang tắt", text_color="gray")
        self.log_message("Hệ thống đã dừng.")
        self.lbl_video.configure(image=None, text="Đã dừng kết nối Camera")

    def ai_loop(self):
        try:
            frame_count = 0
            target_process = getattr(config, 'PROCESS_EVERY_N_FRAMES', 2)
            
            while self.running:
                ret, frame = self.camera.read_frame()
                if not ret:
                    time.sleep(0.1)
                    continue

                frame_count += 1
                if frame_count % target_process == 0:
                    result = self.engine.process_frame(frame)
                    
                    # Lưu frame để hiển thị
                    self.current_frame = result['annotated_frame']
                    self.system_status = result['status']
        except Exception as e:
            import traceback
            err_msg = f"LỖI NGHIÊM TRỌNG TRONG AI LOOP:\n{str(e)}\n{traceback.format_exc()}"
            print(err_msg)
            # Dùng after để gọi an toàn trên GUI thread
            self.after(0, lambda: self.log_message(err_msg))
            self.running = False

    def update_gui(self):
        if not self.running:
            return

        # 1. Update Video
        if self.current_frame is not None:
            # Chuyển đổi BGR sang RGB cho Pillow
            frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            # Tính toán kích thước tự động phù hợp với frame
            win_width = self.video_frame.winfo_width() - 20
            win_height = self.video_frame.winfo_height() - 20
            
            if win_width > 100 and win_height > 100:
                img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(win_width, win_height))
                self.lbl_video.configure(image=img_ctk, text="")

        # 2. Update Metrics
        if self.system_status is not None:
            self.lbl_fps.configure(text=f"FPS: {self.system_status.fps:.1f}")
            self.lbl_person.configure(text="Phát hiện người: " + ("CÓ" if self.system_status.person_detected else "KHÔNG"))
            
            risk = self.system_status.current_risk_level
            colors = {
                'normal': 'green',
                'low': 'goldenrod',
                'medium': 'darkorange',
                'high': 'red',
                'critical': 'darkred'
            }
            texts = {
                'normal': 'BÌNH THƯỜNG',
                'low': 'CẢNH BÁO MỨC 1',
                'medium': 'CẢNH BÁO MỨC 2',
                'high': 'NGUY HIỂM',
                'critical': 'KHẨN CẤP !'
            }
            self.lbl_risk_value.configure(text=texts.get(risk, risk).upper(), fg_color=colors.get(risk, 'gray'))

            # In sự kiện mới vào log
            for ev in self.system_status.active_events:
                if not hasattr(ev, '_logged'):
                    t = time.strftime('%H:%M:%S', time.localtime(ev.timestamp))
                    msg = f"[{t}] {ev.event_type.upper()} ({ev.severity}): {ev.description}"
                    self.log_message(msg)
                    ev._logged = True

        self.after(30, self.update_gui)

    def log_message(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def on_closing(self):
        self.running = False
        if self.camera:
            self.camera.release()
        if self.engine:
            self.engine.shutdown()
        self.destroy()

if __name__ == "__main__":
    app = StrokeDetectionApp()
    app.mainloop()
