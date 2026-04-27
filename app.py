from fastapi import FastAPI, File, UploadFile
from ultralytics import YOLO
import io
from PIL import Image

app = FastAPI()

# تحميل موديل الـ TFLite اللي حولناه (أو الـ .pt)
model = YOLO("yolov8s-seg_int8.tflite") 

@app.get("/")
def home():
    return {"message": "Visual Navigator API is Running!"}

@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    # 1. قراءة الصورة المبعوثة من الموبايل
    request_object_content = await file.read()
    img = Image.open(io.BytesIO(request_object_content))

    # 2. تشغيل الموديل على الصورة
    results = model(img)
    
    # 3. استخراج البيانات (أسماء الأجسام)
    detections = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            detections.append(label)

    return {"detected_objects": detections}