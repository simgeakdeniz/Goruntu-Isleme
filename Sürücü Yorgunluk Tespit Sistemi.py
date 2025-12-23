import cv2
import time
import winsound
import numpy as np

# --- 1. Modelleri Yükleme ---
# Mevcut Haar Cascade'ler, hızlı ve her sistemde çalışan temel tespit için.
# Daha yüksek doğruluk için Dlib veya Mediapipe de kullanılabilir (sunumda bahsedilmeli).
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# --- 2. Yardımcı Fonksiyonlar ---
def play_alarm_sound(frequency=2500, duration=150):
    """Belirtilen frekansta ve sürede bip sesi çalar."""
    winsound.Beep(frequency, duration)

def log_event(event_type, message):
    """Olayları bir log dosyasına kaydeder."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open("surucu_raporu.txt", "a") as f:
        f.write(f"[{timestamp}] [{event_type}] {message}\n")

# --- 3. Arayüz ve Ayar Penceresi ---
WIN_NAME = "SafeDrive Ultra - Sürücü Yorgunluk Tespit Sistemi"
cv2.namedWindow(WIN_NAME)
# Hassasiyet: Gözlerin kapalı kalma süresinin eşiği (saniye).
cv2.createTrackbar('Hassasiyet (sn)', WIN_NAME, 20, 50, lambda x: None) # 2.0 saniye varsayılan
cv2.createTrackbar('Parlaklık Esigi', WIN_NAME, 60, 150, lambda x: None) # Ortalama parlaklık eşiği
cv2.createTrackbar('CLAHE Uygula', WIN_NAME, 0, 1, lambda x: None) # CLAHE açık/kapalı

# --- 4. Video Yakalama ve Değişkenler ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Kamera açılamadı! Lütfen başka bir uygulama tarafından kullanılmadığından emin olun.")
    exit()

# Durum Değişkenleri
closed_start_time = 0      # Gözlerin kapanmaya başladığı zaman
blink_count = 0            # Toplam göz kırpma sayısı
eye_was_open = True        # Bir önceki karede gözler açıktı mı?
alarm_active = False       # Alarm şu an aktif mi?
last_alarm_time = 0        # Son alarmın çaldığı zaman
alarm_frequency_hz = 1500  # Alarmın başlangıç frekansı
alarm_duration_ms = 100    # Alarmın başlangıç süresi
yorgunluk_seviyesi = 0     # 0-100 arası yorgunluk seviyesi
last_frame_time = time.time() # FPS hesaplaması için

system_start_time = time.time() # Sistem başlangıç zamanı

# Log dosyasına başlangıç bilgisi
log_event("BILGI", "SafeDrive Ultra Sistemi başlatıldı.")

# --- 5. Ana Döngü ---
while True:
    ret, frame = cap.read()
    if not ret or cv2.getWindowProperty(WIN_NAME, cv2.WND_PROP_VISIBLE) < 1:
        log_event("BILGI", "Kullanıcı pencereyi kapattı veya akış bitti. Sistem durduruluyor.")
        break

    frame = cv2.flip(frame, 1) # Aynalama
    h, w, _ = frame.shape
    
    # FPS Hesaplama
    current_frame_time = time.time()
    fps = 1 / (current_frame_time - last_frame_time)
    last_frame_time = current_frame_time

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Dinamik Eşik Değerleri
    sensitivity_seconds = cv2.getTrackbarPos('Hassasiyet (sn)', WIN_NAME) / 10.0
    if sensitivity_seconds == 0: sensitivity_seconds = 0.1 # Sıfır bölümleme hatasını önle
    
    brightness_threshold = cv2.getTrackbarPos('Parlaklık Esigi', WIN_NAME)
    apply_clahe = cv2.getTrackbarPos('CLAHE Uygula', WIN_NAME) == 1

    # Parlaklık Analizi
    avg_brightness = np.mean(gray)
    light_status = "IYI" if avg_brightness > brightness_threshold else "DUSUK"

    # Düşük ışıkta CLAHE uygulama
    if light_status == "DUSUK" and apply_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        cv2.putText(frame, "CLAHE AKTIF", (w - 180, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)

    faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))
    eyes_detected_in_frame = False

    for (x, y, wf, hf) in faces:
        cv2.rectangle(frame, (x, y), (x+wf, y+hf), (200, 200, 200), 1) # Yüz çerçevesi

        # Gözler için ROI (Region of Interest)
        roi_gray = gray[y:y+hf//2, x:x+wf] # Yüzün üst yarısı, gözlerin olası konumu
        roi_color = frame[y:y+hf//2, x:x+wf]

        eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 10, minSize=(20, 20)) # Min göz boyutu

        if len(eyes) >= 2: # En az iki göz tespit edilirse
            eyes_detected_in_frame = True
            if not eye_was_open: # Gözler yeni açıldıysa, göz kırpma sayısını artır
                blink_count += 1
                log_event("BILGI", f"Göz kırpma tespit edildi. Toplam: {blink_count}")
                eye_was_open = True
            
            # Gözleri işaretle
            for (ex, ey, ew, eh) in eyes[:2]: # Sadece ilk iki gözü işaretle
                cv2.circle(roi_color, (ex + ew//2, ey + eh//2), int(ew/4), (0, 255, 0), -1)

        else: # Gözler tespit edilemedi
            eye_was_open = False # Gözler şu an kapalı veya tespit edilemiyor

    # --- 6. Alarm Mantığı ve Yorgunluk Analizi ---
    if len(faces) > 0 and not eyes_detected_in_frame:
        if closed_start_time == 0:
            closed_start_time = time.time() # Gözler yeni kapandı
            log_event("UYARI", "Gözler kapalı olarak algılandı.")

        closed_duration = time.time() - closed_start_time
        
        # Yorgunluk Seviyesi Hesaplama (0-100)
        yorgunluk_seviyesi = min(int((closed_duration / sensitivity_seconds) * 100), 100)

        # Yorgunluk Barı (Kırmızıya doğru artar)
        bar_width = int(min(closed_duration / sensitivity_seconds, 1.0) * 180)
        cv2.rectangle(frame, (20, 200), (200, 220), (50, 50, 50), -1) # Arka plan
        cv2.rectangle(frame, (20, 200), (20 + bar_width, 220), (0, 0, 255), -1) # İlerleme çubuğu

        if closed_duration > sensitivity_seconds:
            if not alarm_active: # Alarm yeni başlıyorsa
                log_event("ALARM", f"Sürücü {closed_duration:.2f} saniye gözlerini kapalı tuttu. Alarm aktif!")
                alarm_active = True
                alarm_frequency_hz = 2500 # Başlangıçta daha yüksek frekans
                alarm_duration_ms = 150

            # Alarmın şiddetini ve frekansını artır
            if time.time() - last_alarm_time > 0.5: # Her 0.5 saniyede bir çal
                play_alarm_sound(alarm_frequency_hz, alarm_duration_ms)
                last_alarm_time = time.time()
                # Frekansı ve süreyi artır (daha acil hale getir)
                alarm_frequency_hz = min(alarm_frequency_hz + 100, 4000)
                alarm_duration_ms = min(alarm_duration_ms + 10, 300)

            # Ekranı kırmızı çerçeve ile vurgula
            cv2.rectangle(frame, (0,0), (w,h), (0,0,255), 15)
            cv2.putText(frame, "!!! UYANIK KALIN !!!", (w//2 - 180, h//2), 2, 1.5, (255, 255, 255), 3)

    else: # Gözler açık veya yüz tespit edilemiyor
        closed_start_time = 0 # Sayacı sıfırla
        yorgunluk_seviyesi = 0 # Yorgunluk seviyesini sıfırla
        if alarm_active: # Alarm kapanıyorsa
            log_event("BILGI", "Gözler açıldı/yüz tespit edildi. Alarm deaktif.")
            alarm_active = False
            alarm_frequency_hz = 1500 # Alarm ayarlarını sıfırla
            alarm_duration_ms = 100

    # --- 7. Arayüz Çizimi (HUD - Head-Up Display) ---
    # Sol panel için şeffaf overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (230, h), (20, 20, 20), -1) # Daha geniş panel
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Metinler
    cv2.putText(frame, "SafeDrive Ultra", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.putText(frame, "--- Sistem Verileri ---", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    uptime = int(time.time() - system_start_time)
    cv2.putText(frame, f"Calisma Suresi: {uptime} sn", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(frame, f"Goz Kirpma: {blink_count}", (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(frame, f"Isik Durumu: {light_status}", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(frame, f"Yorgunluk Seviyesi: {yorgunluk_seviyesi}%", (20, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
    cv2.putText(frame, f"FPS: {int(fps)}", (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.putText(frame, f"Hassasiyet: {sensitivity_seconds:.1f} sn", (20, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)

    # --- 8. Görüntüyü Göster ---
    cv2.imshow(WIN_NAME, frame)

    # 'q' tuşuna basınca çıkış
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 9. Kaynakları Serbest Bırakma ---
cap.release()
cv2.destroyAllWindows()
log_event("BILGI", "SafeDrive Ultra Sistemi başarıyla kapatıldı.")
print("\nSafeDrive Ultra başarıyla kapatıldı.")
print("Alarm ve sistem raporları 'surucu_raporu.txt' dosyasında bulunmaktadır.")