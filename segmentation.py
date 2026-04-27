import cv2
from ultralytics import YOLO
from gtts import gTTS
import os
import time
import threading
import queue
from playsound import playsound
import speech_recognition as sr  # مكتبة التعرف على الصوت
import numpy as np               # مكتبة للعمليات الحسابية لحساب الإضاءة
import sounddevice as sd         # المكتبة البديلة لتسجيل الصوت
from scipy.io.wavfile import write # لحفظ الصوت في ملف مؤقت

from twilio.rest import Client
import requests
import io


# ==========================================
# 1. إعداد نظام الصوت العادي
# ==========================================
audio_queue = queue.Queue()

def speech_worker():
    while True:
        text = audio_queue.get()
        if text is None:
            break
        try:
            filename = f"temp_voice_{int(time.time())}.mp3"
            tts = gTTS(text=text, lang='en')
            tts.save(filename)
            playsound(filename)
            os.remove(filename)
        except Exception as e:
            print(f"❌ Audio Error: {e}")
        audio_queue.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

# ==========================================
# 1.5 نظام الطوارئ (SOS System)
# ==========================================
sos_active = False  # عشان نمنع تكرار الطوارئ وهي شغالة
def get_location_link():
    """دالة بتجيب موقع اللابتوب التقريبي وتعمل لينك جوجل ماب"""
    print("📍 جاري تحديد الموقع عبر الشبكة...")
    try:
        # بنكلم سيرفر مجاني يجيب موقعنا من الـ IP
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json()
        if 'loc' in data:
            lat_lon = data['loc']  # بتجيب خط الطول والعرض (مثلاً: 26.5, 31.7)
            google_maps_url = f"https://www.google.com/maps?q={lat_lon}"
            print("✅ تم تحديد الموقع بنجاح!")
            return google_maps_url
    except Exception as e:
        print(f"⚠️ لم نتمكن من تحديد الموقع: {e}")
    
    return "الموقع غير متاح حالياً"

def send_emergency_message():
    """إرسال رسالة طوارئ حقيقية عبر SMS باستخدام Twilio"""
    print("\n" + "="*50)
    print("🚨🚨🚨 إرسال رسالة طوارئ: المستخدم لا يستجيب! 🚨🚨🚨")
    
    # ⚠️ حط بياناتك اللي جبتها من موقع Twilio هنا (بين علامات التنصيص)
    account_sid = 'ACcbbbdd69b81693b03b828dc719a7794c'
    auth_token = 'b94110c9a164c7df5f42cdaac4fd459c'
    twilio_number = '+13185798966' # مثال: '+1234567890'
    
    # ⚠️ حط رقم الموبايل اللي هيستقبل الرسالة (لازم يكون متأكد في الموقع ومكتوب بكود البلد)
    target_number = '+201017421158' # مثال مصر: '+201012345678'
    
    try:
        # الاتصال بسيرفر Twilio
        client = Client(account_sid, auth_token)
        
        # صياغة الرسالة وإرسالها
        message = client.messages.create(
            body="🚨 إنذار طوارئ من تطبيق Visual Navigator! المستخدم لا يستجيب وقد يكون تعرض لسقوط أو خطر. يرجى التواصل معه والاطمئنان عليه فوراً.",
            from_=twilio_number,
            to=target_number
        )
        print(f"✅ تم إرسال رسالة الطوارئ بنجاح على تليفون ولي الأمر!")
        print(f"Message ID: {message.sid}")
        
    except Exception as e:
        print(f"❌ فشل إرسال الرسالة. السبب: {e}")
        
    print("="*50 + "\n")







# ==========================================
# 1.5 نظام الطوارئ (os_process
# ==========================================

def sos_process():
    global sos_active
    recognizer = sr.Recognizer()
    
    audio_queue.put("Emergency detected. Are you okay? Say yes to cancel.")
    time.sleep(4)
    
    try:
        print("🎤 Listening (In-Memory)...")
        # 1. تسجيل الصوت في مصفوفة (Array)
        fs = 44100
        seconds = 5
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        
        # 2. تحويل المصفوفة لملف وهمي في الرامات (BytesIO) بدل الهارد
        byte_io = io.BytesIO()
        write(byte_io, fs, recording) # بنكتب في الذاكرة مش في ملف .wav
        byte_io.seek(0) # بنرجع لأول "الملف الوهمي" عشان نقراه
        
        # 3. قراءة الصوت من الرامات مباشرة
        with sr.AudioFile(byte_io) as source:
            audio = recognizer.record(source)
            
        reply = recognizer.recognize_google(audio, language="en-US").lower()
        print(f"🗣️ User said: {reply}")
        
        if any(word in reply for word in ["yes", "okay", "fine", "yeah"]):
            audio_queue.put("Emergency cancelled.")
        else:
            raise Exception("No positive response")
            
    except Exception as e:
        print(f"🚨 Triggering SOS: {e}")
        send_emergency_message()
    finally:
        sos_active = False
        # هنا مفيش os.remove لأن مفيش ملف اتخلق أصلاً!

# ==========================================
# 2. دالة تقدير المسافة
# ==========================================
FRAME_AREA = 640 * 480

def estimate_distance(box_area_ratio):
    import math
    if box_area_ratio <= 0:
        return 999, "far"
    
    K = 0.35
    estimated_meters = K / math.sqrt(box_area_ratio)
    estimated_meters = round(estimated_meters, 1)
    
    if estimated_meters < 0.8:
        label = "very close"
    elif estimated_meters < 1.5:
        label = "close"
    elif estimated_meters < 3.0:
        label = "nearby"
    else:
        label = "far"
    
    return estimated_meters, label

# ==========================================
# 3. إعدادات الكاميرا والموديل
# ==========================================
print("⏳ Loading Segmentation Model...")
model = YOLO("yolov8s-seg.pt")
cap = cv2.VideoCapture(0)

# 🛑 القائمة البيضاء: العوائق المهمة فقط
IMPORTANT_OBSTACLES = {
    "person", "bicycle", "car", "motorcycle", "bus", "train", "truck", 
    "stop sign", "fire hydrant", "bench", "chair", "couch", "potted plant", 
    "bed", "dining table", "door"
}

last_spoken_text = ""
last_add_time = 0
COOLDOWN = 5.0
dark_frames_count = 0  # العداد لازم يكون بره اللوب!

print("✅ System Ready. Objects will be announced nearest-first!")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # ── استشعار العوائق التامة / وقوع الكاميرا ──
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray_frame)
    
    if brightness < 20:  # لو الشاشة ضلمت
        dark_frames_count += 1
    else:
        dark_frames_count = 0
        
    # لو ضلمت لمدة ثانيتين (حوالي 60 فريم) ومش في حالة طوارئ
    if dark_frames_count > 60 and not sos_active:
        sos_active = True
        dark_frames_count = 0
        threading.Thread(target=sos_process, daemon=True).start()

    # ── التعرف على الأجسام ──
    frame = cv2.resize(frame, (640, 480))
    results = model(frame, verbose=False, stream=True)

    detected_objects = [] 
    annotated_frame = frame.copy()

    for r in results:
        annotated_frame = r.plot()

        if r.boxes:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf < 0.8:
                    continue

                cls_id = int(box.cls[0])
                label = model.names[cls_id]

                # 🛑 الفلترة الذكية
                if label not in IMPORTANT_OBSTACLES:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                center_x = (x1 + x2) // 2
                if center_x < 213:
                    pos = "left"
                elif center_x > 426:
                    pos = "right"
                else:
                    pos = "center"

                box_w = x2 - x1
                box_h = y2 - y1
                box_area = box_w * box_h
                area_ratio = box_area / FRAME_AREA

                dist_m, dist_label = estimate_distance(area_ratio)

                detected_objects.append({
                    "label":      label,
                    "position":   pos,
                    "distance_m": dist_m,
                    "dist_label": dist_label,
                    "box":        (x1, y1, x2, y2),
                    "area_ratio": area_ratio,
                })

                dist_text = f"{dist_m}m ({dist_label})"
                cv2.putText(
                    annotated_frame, dist_text,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (0, 255, 255), 2
                )

    # ── الترتيب وتكوين الجملة ──
    unique_objects = {}
    for obj in detected_objects:
        key = obj["label"]
        if key not in unique_objects or obj["distance_m"] < unique_objects[key]["distance_m"]:
            unique_objects[key] = obj

    sorted_objects = sorted(unique_objects.values(), key=lambda x: x["distance_m"])

    current_time = time.time()

    if sorted_objects:
        parts = []
        for obj in sorted_objects:
            part = f"{obj['label']} on the {obj['position']}, {obj['distance_m']} meters"
            parts.append(part)

        sentence = ". Then, ".join(parts)

        is_new_content   = (sentence != last_spoken_text)
        is_worker_free   = audio_queue.empty()
        # نوقف الكلام العادي لو نظام الطوارئ شغال عشان الأصوات متدخلش في بعض
        is_cooldown_over = (current_time - last_add_time > COOLDOWN) and not sos_active 

        if is_new_content and is_worker_free and not sos_active:
            print(f"🎤 Nearest first: {sentence}")
            audio_queue.put(sentence)
            last_spoken_text = sentence
            last_add_time = current_time

        elif not is_new_content and is_cooldown_over and is_worker_free:
            print(f"♻️ Reminding: {sentence}")
            audio_queue.put(sentence)
            last_add_time = current_time

    # ── عرض الفريم ──
    cv2.imshow("Visual Navigator - Final Edition", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
audio_queue.put(None)