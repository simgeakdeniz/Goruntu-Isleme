import cv2
import time
import winsound
import numpy as np
import tkinter as tk
from tkinter import messagebox

# --- 1. SİSTEM FONKSİYONU ---
def start_system():
    root.withdraw() 
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    WIN_NAME = "SafeDrive Ultra - Canli Takip Sistemi"
    cv2.namedWindow(WIN_NAME)
    
    cv2.createTrackbar('Hassasiyet (sn)', WIN_NAME, 20, 50, lambda x: None)
    cv2.createTrackbar('Parlaklik Esigi', WIN_NAME, 60, 150, lambda x: None)
    cv2.createTrackbar('CLAHE Uygula', WIN_NAME, 0, 1, lambda x: None)

    cap = cv2.VideoCapture(0)
    closed_start_time = 0
    blink_count = 0
    eye_was_open = True
    last_alarm_time = 0
    yorgunluk_seviyesi = 0
    last_frame_time = time.time()
    system_start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        current_frame_time = time.time()
        fps = 1 / (current_frame_time - last_frame_time)
        last_frame_time = current_frame_time
        
        sensitivity = cv2.getTrackbarPos('Hassasiyet (sn)', WIN_NAME) / 10.0
        if sensitivity == 0: sensitivity = 0.1
        
        avg_brightness = np.mean(gray)
        if avg_brightness < cv2.getTrackbarPos('Parlaklik Esigi', WIN_NAME) and cv2.getTrackbarPos('CLAHE Uygula', WIN_NAME):
            gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(gray)

        faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))
        eyes_detected = False
        face_detected = len(faces) > 0

        if face_detected:
            for (x, y, wf, hf) in faces:
                cv2.rectangle(frame, (x, y), (x+wf, y+hf), (200, 200, 200), 1)
                roi_gray = gray[y:y+hf//2, x:x+wf]
                eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10, minSize=(20, 20))
                
                if len(eyes) >= 2:
                    eyes_detected = True
                    if not eye_was_open: blink_count += 1
                    eye_was_open, closed_start_time = True, 0
                else:
                    eye_was_open = False
        
        # --- Göz Tespit Edilemiyor Uyarısı ---
        if face_detected and not eyes_detected:
            cv2.putText(frame, "Goz Tespit Edilemiyor", (w - 250, h - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if face_detected and not eyes_detected:
            if closed_start_time == 0: closed_start_time = time.time()
            dur = time.time() - closed_start_time
            yorgunluk_seviyesi = min(int((dur / sensitivity) * 100), 100)
            
            bar_width = int(min(dur / sensitivity, 1.0) * 180)
            cv2.rectangle(frame, (20, 200), (200, 220), (50, 50, 50), -1)
            cv2.rectangle(frame, (20, 200), (20 + bar_width, 220), (0, 0, 255), -1)

            if dur > sensitivity:
                cv2.rectangle(frame, (0,0), (w,h), (0,0,255), 15)
                cv2.putText(frame, "!!! UYANIK KALIN !!!", (w//2 - 180, h//2), 2, 1.5, (255, 255, 255), 3)
                if time.time() - last_alarm_time > 0.5:
                    winsound.Beep(2000, 100)
                    last_alarm_time = time.time()
        else:
            closed_start_time = 0
            yorgunluk_seviyesi = 0

        # Sol HUD Paneli
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (230, h), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        cv2.putText(frame, f"Sure: {int(time.time()-system_start_time)}s", (20, 90), 1, 1, (255,255,255), 1)
        cv2.putText(frame, f"Kirpma: {blink_count}", (20, 115), 1, 1, (255,255,255), 1)
        cv2.putText(frame, f"Yorgunluk: %{yorgunluk_seviyesi}", (20, 165), 1, 1, (0, 165, 255), 1)
        cv2.putText(frame, f"FPS: {int(fps)}", (20, 240), 1, 1, (0, 255, 0), 1)

        cv2.imshow(WIN_NAME, frame)
        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty(WIN_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
    root.deiconify() 

# --- 2. MODERN TKINTER ARAYÜZÜ ---
root = tk.Tk()
root.title("SafeDrive Ultra Dashboard")
root.geometry("450x400")
root.configure(bg="#1c1c1c") 

header = tk.Frame(root, bg="#2d2d2d", height=80)
header.pack(fill="x")

tk.Label(header, text="SAFEDRIVE ULTRA", font=("Verdana", 22, "bold"), fg="#00d4ff", bg="#2d2d2d").pack(pady=15)

content = tk.Frame(root, bg="#1c1c1c")
content.pack(expand=True)

tk.Label(content, text="Sürücü Analiz Sistemi Aktif", font=("Verdana", 10), fg="#888888", bg="#1c1c1c").pack(pady=5)

def on_enter(e):
    btn_start['bg'] = '#00a8cc'

def on_leave(e):
    btn_start['bg'] = '#00d4ff'

btn_start = tk.Button(content, text="SİSTEMİ BAŞLAT", font=("Verdana", 12, "bold"), bg="#00d4ff", fg="white", 
                      activebackground="#00a8cc", activeforeground="white", bd=0, width=20, height=2, 
                      cursor="hand2", command=start_system)
btn_start.pack(pady=20)
btn_start.bind("<Enter>", on_enter)
btn_start.bind("<Leave>", on_leave)

btn_exit = tk.Button(root, text="Uygulamayı Kapat", font=("Verdana", 9), bg="#1c1c1c", fg="#ff4b4b", 
                     activebackground="#1c1c1c", activeforeground="#ff0000", bd=0, cursor="hand2", command=root.quit)
btn_exit.pack(side="bottom", pady=20)

tk.Label(root, text="Sunum Modu: Haar Cascade V2", font=("Verdana", 7), fg="#444444", bg="#1c1c1c").pack(side="bottom")

root.mainloop()