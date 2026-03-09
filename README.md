<div align="center">
  <img src="https://img.icons8.com/nolan/256/facial-recognition-scan.png" alt="Logo" width="100"/>
  <h1>🛡️ Anti-Spoofing Face Recognition Attendance System</h1>
  <p><i>A secure, AI-powered Smart Attendance System that distinguishes between real human faces and printed photos/digital screens.</i></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
    <img src="https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
    <img src="https://img.shields.io/badge/YOLOv8-19FF19?style=for-the-badge&logo=YOLO&logoColor=black" alt="YOLOv8">
    <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  </p>
</div>

---

## 📖 Overview

Traditional face-recognition attendance systems are easily fooled by students or employees simply showing a photograph or playing a video on their phone. 

This **Anti-Spoofing Face Recognition System** solves that problem by integrating a **YOLOv8** model to classify faces as `real` or `fake` (photos/screens) before performing the identification match using the `face_recognition` library. Supported by a comprehensive Flask Admin Dashboard, this is a complete solution for schools, universities, and businesses.

## ✨ Key Features

- **🤖 Liveness Detection (Anti-Spoofing)**: Uses a trained YOLOv8 model (`m_version_1_149.pt`) to detect spoof attempts (fake faces).
- **👤 Robust Face Recognition**: Uses `dlib` and `face_recognition` to accurately identify the `real` person against registered encodings.
- **🛡️ Duplicate Prevention**: Prevents duplicate attendance entries on the same day.
- **📊 Admin Dashboard**: A secure control panel to view daily attendance stats, student records, and overall system health.
- **📈 CSV Export**: One-click export of monthly or all-time attendance records in CSV format.
- **🐳 Docker Support**: Comes with `Dockerfile` and `docker-compose.yml` for containerized environments.
- **✨ Beautiful Web Interface**: A sleek, user-friendly frontend built with Flask templates and CSS.

---

## 🛠️ Project Architecture

```plaintext
anitface/
├── app/
│   ├── static/               # CSS, JS, and Image assets
│   ├── templates/            # HTML Dashboard & Frontend templates
│   ├── __init__.py           # Flask App and Database init
│   ├── extensions.py         # SQLAlchemy & Admin extensions
│   ├── models.py             # User, Attendance, and KnownFace Schema
│   └── routes.py             # Main Logic: Capturing, Recognition & Admin APIs
├── faces/                    # Stored user profile images for encodings
├── instance/
│   └── database.db           # SQLite DB for attendance & users
├── m_version_1_149.pt        # YOLOv8 weights for Real vs. Fake detection
├── requirements.txt          # Python dependencies
├── run.py                    # Entry point logic
├── Dockerfile                # Docker Image config
└── docker-compose.yml        # Docker composition map
```

---

## 🚀 Two-Step Workflow

1. **Anti-Spoofing Check**: The webcam feed is passed through YOLOv8. If a face is detected as a spoof (e.g., photo on phone), it is framed in **Red** and marked as `Fake Face`. Attendance is denied.
2. **Recognition Match**: If the face is confirmed as `real`, it is framed in **Green**. The system then computes 128-d encodings and determines the identity. Attendance is saved to the SQLite database with the current date/time.

---

## ⚙️ Installation & Local Setup

### 1. Prerequisites
- Python 3.10 or 3.11 installed.
- A working webcam.

### 2. Clone the Repository
```bash
git clone https://github.com/Akash7367/faceReco.git
cd faceReco/anitface
```

### 3. Create a Virtual Environment
**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```
**Linux / macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
> **Note for Windows Users**: Installing `dlib` from pip can be tricky due to C++ build requirements. A pre-compiled `.whl` file is provided in the root directory for Python 3.11.

```bash
# If on Windows + Python 3.11:
pip install dlib-19.24.1-cp311-cp311-win_amd64.whl

# Then install the rest:
pip install -r requirements.txt
```

### 5. Running the Application
```bash
python run.py
```
Open your browser and navigate to: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

> **Pro-Tip**: For maximum FPS during recognition, ensure you have PyTorch compiled with NVIDIA CUDA support.

---

## 🐳 Docker Setup

An easier option if you don't want to deal with local python environments.
```bash
# Build and start via Docker Compose
docker-compose up --build
```
> **Note:** Accessing the host's webcam from a docker container may require additional proxying (e.g., sharing `/dev/video0` on Linux) inside `docker-compose.yml`.

---

## 🔐 Admin Usage

The system features a protected admin site.

- **Route:** `/admin_login`
- **Default Username:** `admin` *(Can be overridden via `ADMIN_USERNAME` in `.env`)*
- **Default Password:** `panda` *(Can be overridden via `ADMIN_PASSWORD` in `.env`)*

From the admin panel, you can view analytics, export CSVs, delete specific errant records, or wipe the entire database if running a fresh session.

---

## 📜 License & Credits

This project was built by [Akash7367](https://github.com/Akash7367).

**License**: MIT License. Feel free to fork, modify, and use this in your institutions!