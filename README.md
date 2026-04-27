# 👁️ Visual Navigator: AI-Powered Assistance for the Visually Impaired

## 🚀 Project Overview
This repository contains the **AI Backend** and **Edge Inference** logic for the Visual Navigator project. We use state-of-the-art Computer Vision to provide real-time navigation and object detection for visually impaired users.

## 🛠️ Tech Stack
- **AI Core:** YOLOv8 (Ultralytics) for Object Segmentation & Detection.
- **Backend Framework:** FastAPI (Asynchronous API).
- **Mobile Inference:** TensorFlow Lite (TFLite) for high-speed performance.
- **Cloud Hosting:** Railway (with CI/CD integration).
- **Communication:** Twilio API for emergency SOS protocols.

## 📂 File Structure Guide (For the Team)
- `app.py`: The main entry point of the FastAPI server. Contains the `/predict` endpoint.
- `yolov8s-seg_float16.tflite`: Optimized model for production/mobile use.
- `yolov8s-seg.pt`: Original PyTorch model for research and further training.
- `requirements.txt`: List of all Python dependencies needed to run the server.
- `Dockerfile`: Containerization setup for cloud deployment.
- `.env`: (Private) Stores sensitive API keys (Twilio, Gemini, etc.).

## ⚙️ How to Run Locally
1. Clone the repo: `git clone https://github.com/zakariayahia/visual-navigation.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run server: `uvicorn app:app --reload`
4. Access docs: `http://127.0.0.1:8000/docs`

## 👥 Graduation Project Team (Sinai University)
Built by a dedicated team of 5 engineers specialized in AI, Mobile Development (Flutter)
