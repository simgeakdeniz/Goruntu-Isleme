import cv2

# Hazır sınıflandırıcıları yüklüyoruz (OpenCV ile otomatik gelir)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret: break
    
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Yüz tespiti
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(frame, "Insan Yuzu", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Sadece yüz bölgesi içinde gülümseme ara (ROI - Region of Interest)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        
        # Gülümseme tespiti (scaleFactor ve minNeighbors değerleri hassasiyet içindir)
        smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)
        
        status = "Ciddi/Normal"
        color = (0, 255, 255) # Sarı
        
        if len(smiles) > 0:
            status = "Gulumseme Tespit Edildi! :)"
            color = (0, 255, 0) # Yeşil
            for (sx, sy, sw, sh) in smiles:
                cv2.rectangle(roi_color, (sx, sy), (sx+sw, sy+sh), color, 1)

        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

    cv2.imshow('Gercek Zamanli Gulumseme Analizi', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()