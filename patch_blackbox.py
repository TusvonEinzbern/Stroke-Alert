import re
import os

with open('stroke_risk_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Make sure imports exist
if 'import collections' not in text:
    text = text.replace('import time', 'import time\nimport collections\nimport threading\nimport cv2\nimport os')

# Make sure buffer exists
if 'self.frame_buffer' not in text:
    text = text.replace('self.latest_frame = None', 'self.latest_frame = None\n        self.frame_buffer = collections.deque(maxlen=150) # 5s\n        self.last_record_time = 0\n        if not os.path.exists("static/records"):\n            os.makedirs("static/records")')

# Make sure frame append exists
if 'self.frame_buffer.append' not in text:
    text = text.replace('def process_frame(self, frame: np.ndarray) -> dict:', 'def process_frame(self, frame: np.ndarray) -> dict:\n        self.frame_buffer.append(frame.copy())')

# Add the Blackbox Method
if 'def _save_blackbox_record(self, frames):' not in text:
    method = '''
    def _save_blackbox_record(self, frames):
        try:
            if not frames: return
            timestamp = int(time.time())
            filename = f"static/records/incident_{timestamp}.mp4"
            h, w = frames[0].shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(filename, fourcc, 30.0, (w, h))
            for f in frames:
                out.write(f)
            out.release()
            logger.info(f"Blackbox record saved: {filename}")
        except Exception as e:
            logger.error(f"Blackbox Error: {e}")
'''
    text = text + method

# Hook the recording trigger
old_trigger = '''            if self._should_send_alert(events):
                highest_risk_event = max(events, key=lambda e: e.confidence)
                alert_info = AlertInfo(event=highest_risk_event, frame_snapshot=frame)
                if self.alert_manager.send_alert(alert_info):
                    alert_sent = True
                    self.status.total_alerts_sent += 1'''

new_trigger = '''            if self._should_send_alert(events):
                highest_risk_event = max(events, key=lambda e: e.confidence)
                alert_info = AlertInfo(event=highest_risk_event, frame_snapshot=frame)
                if self.alert_manager.send_alert(alert_info):
                    alert_sent = True
                    self.status.total_alerts_sent += 1
                    
                if risk_level == 'critical' and (time.time() - getattr(self, 'last_record_time', 0) > 60):
                    self.last_record_time = time.time()
                    frames_to_save = list(self.frame_buffer)
                    threading.Thread(target=self._save_blackbox_record, args=(frames_to_save,), daemon=True).start()'''

text = text.replace(old_trigger, new_trigger)

with open('stroke_risk_engine.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Blackbox patched successfully")
