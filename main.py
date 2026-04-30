from fastapi import FastAPI, File, UploadFile
from ultralytics import YOLO
from PIL import Image
import easyocr
import numpy as np
import io

app = FastAPI()

# تحميل الموديل
model = YOLO("yolov8n.pt")

# OCR
reader = easyocr.Reader(['en'])

# labels
labels = [
    "person","bicycle","car","motorcycle","airplane","bus","train","truck"
]

@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    contents = await image.read()

    img = Image.open(io.BytesIO(contents))
    img_np = np.array(img)

    # YOLO
    results = model(img_np)
    detections = []

    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            label = labels[class_id]

            detections.append({
                "label": label,
                "confidence": confidence
            })

    # OCR
    ocr_result = reader.readtext(img_np)
    text = " ".join([res[1] for res in ocr_result])

    return {
        "detections": detections,
        "text": text
    }