import cv2
import time
import winsound
import numpy as np

# Modeller
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

def nothing(x): pass

# Pencere Hazırlığı
win_name = "SafeDrive Ultra - Final Projesi"
cv2.namedWindow(win_name)
cv2.createTrackbar('Hassasiyet', win_name, 15, 50, nothing)

cap = cv2.VideoCapture(0)
closed_start = 0
alarm_count = 0
start_time = time.time()
blink_count = 0
eye_was_open = True

while True:
    ret, frame = cap.read()
    if not ret or cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) < 1: break
    
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 1. Parlaklık Analizi (Hocaya teknik detay olur)
    avg_brightness = np.mean(gray)
    light_status = "IYI" if avg_brightness > 70 else "DUSUK"
    
    limit = cv2.getTrackbarPos('Hassasiyet', win_name) / 10.0
    if limit == 0: limit = 0.1

    # Arayüz Panelleri
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (220, h), (20, 20, 20), -1) # Sol panel
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    faces = face_cascade.detectMultiScale(gray, 1.2, 5)
    eyes_detected = False

    for (x, y, wf, hf) in faces:
        cv2.rectangle(frame, (x, y), (x+wf, y+hf), (200, 200, 200), 1)
        roi_gray = gray[y:y+hf, x:x+wf]
        roi_color = frame[y:y+hf, x:x+wf]
        
        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10)
        
        if len(eyes) >= 2:
            eyes_detected = True
            if not eye_was_open: # Göz yeni açıldıysa kırpma say
                blink_count += 1
                eye_was_open = True
            for (ex, ey, ew, eh) in eyes:
                cv2.circle(roi_color, (ex + ew//2, ey + eh//2), int(ew/5), (0, 255, 0), -1)
        else:
            eye_was_open = False

    # Analitik Veriler
    uptime = int(time.time() - start_time)
    
    # Bilgi Paneli Yazıları
    cv2.putText(frame, "SISTEM VERILERI", (20, 30), 1, 1.2, (255, 255, 255), 2)
    cv2.putText(frame, f"Sure: {uptime}sn", (20, 70), 1, 1, (200, 200, 200), 1)
    cv2.putText(frame, f"Goz Kirpma: {blink_count}", (20, 100), 1, 1, (200, 200, 200), 1)
    cv2.putText(frame, f"Isik: {light_status}", (20, 130), 1, 1, (200, 200, 200), 1)
    cv2.putText(frame, f"Alarm: {alarm_count}", (20, 160), 1, 1, (0, 165, 255), 1)

    # Alarm Mantığı
    if len(faces) > 0 and not eyes_detected:
        if closed_start == 0: closed_start = time.time()
        dur = time.time() - closed_start
        
        # Yorgunluk Barı
        bar = int(min(dur / limit, 1.0) * 180)
        cv2.rectangle(frame, (20, 200), (200, 220), (50, 50, 50), -1)
        cv2.rectangle(frame, (20, 200), (20 + bar, 220), (0, 0, 255), -1)
        
        if dur > limit:
            alarm_count += 1
            cv2.rectangle(frame, (0,0), (w,h), (0,0,255), 15)
            cv2.putText(frame, "!!! DIKKAT !!!", (w//2-100, h//2), 2, 1.5, (255, 255, 255), 3)
            winsound.Beep(2000, 100)
    else:
        closed_start = 0

    cv2.imshow(win_name, frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()