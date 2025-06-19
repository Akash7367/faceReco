# Smart Attendance System 🧠📸

This is a Smart Attendance System that uses face recognition to automatically mark attendance of individuals in real-time. Built using Python, OpenCV, and face recognition libraries.

## 🚀 Features

- 🎯 Face recognition-based attendance
- 🕒 Real-time webcam integration
- 🗂️ Automatic CSV file generation for attendance logs
- 🧠 Trained model for recognizing known faces
- 🔔 Duplicate attendance prevention
- 📊 Easy to use and modify for institutions, classrooms, or office setups

## 🛠️ Tech Stack

- Python 🐍
- OpenCV 📷
- face_recognition 🤖
- NumPy
- Pandas
- CSV Module
- Tkinter (for GUI) [optional]

## 📸 Demo

![Demo](demo.gif) <!-- Add a demo video/gif or image -->

## 🧾 How it Works

1. Capture images of users and store them in a folder (e.g., `Images`).
2. Encode faces and store data.
3. Start webcam and compare live frames with known encodings.
4. When a face is recognized, log their name with a timestamp.
5. Save attendance to a CSV file.

## 🧰 Installation

```bash
git clone https://github.com/yourusername/Smart-Attendance-System.git
cd Smart-Attendance-System
pip install -r requirements.txt
python main.py
