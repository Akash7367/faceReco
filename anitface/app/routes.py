import os
import cv2
import time
import math
from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint, current_app, jsonify
from .extensions import db
from .models import User, Attendance, KnownFace
from datetime import datetime
import face_recognition
import numpy as np
from ultralytics import YOLO

app = Blueprint("app", __name__)

@app.route('/attendance', methods=['GET'])
def get_attendance():
    selected_date = request.args.get('date')
    if not selected_date:
        return jsonify({'error': 'Date parameter is required'}), 400

    try:
        date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    attendance = Attendance.query.filter_by(date=date).all()
    attendance_list = [
        {'name': record.user.name, 'roll': record.user.roll, 'time': record.time.strftime("%H:%M:%S")}
        for record in attendance
    ]
    attendance_count = len(attendance_list)

    return jsonify({'attendance': attendance_list, 'attendance_count': attendance_count})


faces_directory = 'faces'
if not os.path.exists(faces_directory):
    os.makedirs(faces_directory)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/main')
def main():
    today = datetime.now().date()
    attendance = Attendance.query.filter_by(date=today).all()
    today_attendance_count = len(attendance)
    total_registered = User.query.count()
    datetoday2 = today.strftime("%Y-%m-%d")
    return render_template('main.html', attendance=attendance, total_registered=total_registered,today_attendance_count=today_attendance_count, datetoday2=datetoday2)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        new_name = request.form.get('newusername')
        new_roll = request.form.get('newuserid')

        existing_user = User.query.filter_by(roll=new_roll).first()
        if existing_user:
            flash("Roll number already exists. Please try again.", "error")
            return redirect(url_for('app.main'))

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        ret, frame = cap.read()
        cap.release()
        cv2.destroyAllWindows()

        if not ret:
            flash("Error capturing image from webcam. Please try again.", "error")
            return redirect(url_for('app.main'))

        resized_frame = cv2.resize(frame, (480, 480))
        rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if len(face_encodings) == 0:
            flash("No face detected. Please ensure proper lighting and face visibility.", "error")
            return redirect(url_for('app.main'))
        elif len(face_encodings) > 1:
            flash("Multiple faces detected. Please ensure only one person is in the frame.", "error")
            return redirect(url_for('app.main'))

        try:
            image_path = os.path.join(faces_directory, f'{new_name}_{new_roll}.jpg')
            cv2.imwrite(image_path, resized_frame)

            new_user = User(name=new_name, roll=new_roll)
            db.session.add(new_user)

            new_known_face = KnownFace(name=new_name, encoding=face_encodings[0])
            db.session.add(new_known_face)

            db.session.commit()

            flash("New user added successfully!", "success")
        except Exception as e:
            db.session.rollback() 
            flash(f"An error occurred while saving the user: {e}", "error")
        return redirect(url_for('app.main'))

    return render_template('main.html')


@app.route('/start')
def start():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    
    model = YOLO("m_version_1_149.pt")
    classNames = ["fake", "real"]
    confidence_threshold = 0.6

    known_faces = KnownFace.query.all()
    if not known_faces:
        flash("There are no users. Please add users first.", "error")
        return redirect(url_for('app.main'))
        
    known_face_encodings = [face.encoding for face in known_faces]
    known_face_names = [face.name for face in known_faces]

    students = set(known_face_names)
    marked_attendance = set()
    prev_frame_time = 0

    while True:
        success, img = cap.read()
        if not success:
            flash("Failed to access the webcam.", "error")
            break

        new_frame_time = time.time()
        results = model(img, stream=True, verbose=False)

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                if conf > confidence_threshold and classNames[cls] == 'real':
                    face_frame = img[y1:y2, x1:x2]
                    small_frame = cv2.resize(face_frame, (0, 0), fx=0.25, fy=0.25)
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                    face_locations = face_recognition.face_locations(rgb_small_frame)
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                    for face_encoding in face_encodings:
                        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)

                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]

                            if name not in marked_attendance:
                                marked_attendance.add(name)
                                students.discard(name)

                                current_user = User.query.filter_by(name=name).first()
                                if current_user:
                                    attendance = Attendance(user_id=current_user.id, date=datetime.now().date())
                                    db.session.add(attendance)
                                    db.session.commit()
                                
                                display_text = f"{name}: Attendance Done"
                            else:
                                display_text = f"{name}: Already Marked"

                            color = (0, 255, 0)
                        else:
                            name = "Unknown"
                            display_text = "Unknown Person"
                            color = (0, 0, 255)

                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                        text_size = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        text_x = x1 + (x2 - x1 - text_size[0]) // 2
                        text_y = y2 + 20
                        cv2.putText(img, display_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                else:
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(img, "Fake Face", (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        fps_text = f"{int(fps)}"
        cv2.putText(img, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

        cv2.imshow("Image", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return redirect(url_for('app.main'))



SECURE_PASSWORD = "panda"

@app.route('/new_add', methods=['POST'])
def clear_all():
    try:
        data = request.json
        password = data.get('password')

        if password != SECURE_PASSWORD:
            return jsonify({"status": "error", "message": "Unauthorized access"}), 401

        User.query.delete()
        Attendance.query.delete()
        KnownFace.query.delete()
        db.session.commit()

        global known_faces, known_names
        known_faces = []
        known_names = []

        for filename in os.listdir(faces_directory):
            file_path = os.path.join(faces_directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        flash("All data cleared successfully!", "success")
        return jsonify({"status": "success", "redirect_url": url_for('admin.index')}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/adminn')
def admin():
    return render_template('destroy.html')