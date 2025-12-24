import cv2
import time
import winsound
import numpy as np
import tkinter as tk
from tkinter import messagebox

def start_system():
    # Ana pencereyi gizle
    root.withdraw()
    
    # Modelleri yükle
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    # Ayarlar ve Pencere
    WIN_NAME = "SafeDrive Ultra - Canli Takip Sistemi"
    cv2.namedWindow(WIN_NAME)
    
    cv2.createTrackbar('Hassasiyet (sn)', WIN_NAME, 20, 50, lambda x: None)
    cv2.createTrackbar('Parlaklik Esigi', WIN_NAME, 60, 150, lambda x: None)
    cv2.createTrackbar('CLAHE Uygula', WIN_NAME, 1, 1, lambda x: None) # Varsayılan Açık

    # Değişkenleri Başlat
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

        # FPS Hesapla
        current_frame_time = time.time()
        fps = 1 / (current_frame_time - last_frame_time)
        last_frame_time = current_frame_time

        # Ayarları Oku
        sensitivity = cv2.getTrackbarPos('Hassasiyet (sn)', WIN_NAME) / 10.0
        if sensitivity == 0: sensitivity = 0.1
        
        # Karanlık Ortam İyileştirme (CLAHE)
        avg_brightness = np.mean(gray)
        if avg_brightness < cv2.getTrackbarPos('Parlaklik Esigi', WIN_NAME) and cv2.getTrackbarPos('CLAHE Uygula', WIN_NAME):
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)

        # Tespit İşlemleri
        faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))
        eyes_detected = False
        face_detected = len(faces) > 0
        dur = 0

        if face_detected:
            for (x, y, wf, hf) in faces:
                cv2.rectangle(frame, (x, y), (x+wf, y+hf), (200, 200, 200), 1)
                
                # Sadece yüzün üst kısmında göz ara (ROI)
                roi_gray = gray[y:y+hf//2, x:x+wf]
                eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10, minSize=(20, 20))

                if len(eyes) >= 2:
                    eyes_detected = True
                    if not eye_was_open:
                        blink_count += 1
                    eye_was_open, closed_start_time = True, 0
                else:
                    eye_was_open = False

        # Yorgunluk Analizi ve Zamanlayıcı
        if face_detected and not eyes_detected:
            if closed_start_time == 0: closed_start_time = time.time()
            dur = time.time() - closed_start_time
            yorgunluk_seviyesi = min(int((dur / sensitivity) * 100), 100)

            # Görsel Bar
            bar_width = int(min(dur / sensitivity, 1.0) * 180)
            cv2.rectangle(frame, (25, 200), (205, 220), (50, 50, 50), -1)
            cv2.rectangle(frame, (25, 200), (25 + bar_width, 220), (0, 0, 255), -1)

            # KRİTİK DURUM: Alarm ve Fotoğraf Kaydı
            if dur > sensitivity:
                cv2.rectangle(frame, (0,0), (w,h), (0,0,255), 15)
                cv2.putText(frame, "!!! UYANIK KALIN !!!", (w//2 - 180, h//2), 2, 1.2, (255, 255, 255), 3)
                
                if time.time() - last_alarm_time > 2.0:
                    # Fotoğrafı Kaydet
                    dosya_adi = f"ihlal_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(dosya_adi, frame)
                    # Sesi Çal
                    winsound.Beep(2000, 400)
                    last_alarm_time = time.time()
        else:
            yorgunluk_seviyesi = max(0, yorgunluk_seviyesi - 2) # Göz açılınca seviyeyi düşür

        # Bilgi Paneli (HUD)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (230, h), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        cv2.putText(frame, f"Sure: {int(time.time()-system_start_time)}s", (20, 90), 1, 1, (255,255,255), 1)
        cv2.putText(frame, f"Kirpma: {blink_count}", (20, 115), 1, 1, (255,255,255), 1)
        cv2.putText(frame, f"Yorgunluk: %{yorgunluk_seviyesi}", (20, 165), 1, 1, (0, 165, 255), 1)
        cv2.putText(frame, f"FPS: {int(fps)}", (20, 240), 1, 1, (0, 255, 0), 1)

        cv2.imshow(WIN_NAME, frame)

        # Çıkış Kontrolü
        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty(WIN_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
    root.deiconify() # Arayüzü geri getir

# --- TKINTER ARAYÜZÜ ---
root = tk.Tk()
root.title("SafeDrive Ultra Dashboard")
root.geometry("450x400")
root.configure(bg="#1c1c1c")

# Başlık Paneli
header = tk.Frame(root, bg="#2d2d2d", height=80)
header.pack(fill="x")
tk.Label(header, text="SAFEDRIVE ULTRA", font=("Verdana", 20, "bold"), fg="#00d4ff", bg="#2d2d2d").pack(pady=20)

# İçerik
content = tk.Frame(root, bg="#1c1c1c")
content.pack(expand=True)
tk.Label(content, text="Sürücü Analiz Sistemi Aktif", font=("Verdana", 10), fg="#888888", bg="#1c1c1c").pack(pady=5)

# Buton Efektleri
def on_enter(e): btn_start['bg'] = '#00a8cc'
def on_leave(e): btn_start['bg'] = '#00d4ff'

btn_start = tk.Button(content, text="SİSTEMİ BAŞLAT", font=("Verdana", 12, "bold"), bg="#00d4ff", fg="white", 
                      activebackground="#00a8cc", bd=0, width=20, height=2, cursor="hand2", command=start_system)
btn_start.pack(pady=20)
btn_start.bind("<Enter>", on_enter)
btn_start.bind("<Leave>", on_leave)

btn_exit = tk.Button(root, text="Uygulamayı Kapat", font=("Verdana", 9), bg="#1c1c1c", fg="#ff4b4b", 
                     bd=0, cursor="hand2", command=root.quit)
btn_exit.pack(side="bottom", pady=20)

tk.Label(root, text="Sunum Modu: Haar Cascade + Foto Kayit", font=("Verdana", 7), fg="#444444", bg="#1c1c1c").pack(side="bottom")

root.mainloop()