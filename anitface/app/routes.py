import os
import cv2
import time
import math
import io
import csv
import calendar
from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint, current_app, jsonify, session, Response
from .extensions import db
from .models import User, Attendance, KnownFace
from datetime import datetime
from sqlalchemy import func, extract
import face_recognition
import numpy as np
from ultralytics import YOLO

import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "panda")

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
        new_phone = request.form.get('newphone', '')
        new_email = request.form.get('newemail', '')
        new_address = request.form.get('newaddress', '')

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

            new_user = User(name=new_name, roll=new_roll, phone=new_phone, email=new_email, address=new_address)
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
    # Pre-load today's already-marked attendance from the database
    today = datetime.now().date()
    already_marked_today = db.session.query(User.name).join(Attendance).filter(
        Attendance.date == today
    ).all()
    marked_attendance = set(name for (name,) in already_marked_today)
    students -= marked_attendance
    prev_frame_time = 0

    # Create a named window and bring it to the foreground
    window_name = "Face Recognition - Attendance"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)

    # Bring the window to the front on Windows
    try:
        import ctypes
        import ctypes.wintypes
        hwnd = ctypes.windll.user32.FindWindowW(None, window_name)
        if hwnd:
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    except Exception:
        pass

    # Auto-close timer: close camera N seconds after last attendance is marked
    auto_close_delay = 3  # seconds after attendance marked
    last_marked_time = None
    attendance_just_marked = False

    while True:
        success, img = cap.read()
        if not success:
            flash("Failed to access the webcam.", "error")
            break

        new_frame_time = time.time()

        # Check auto-close: if attendance was marked and delay has passed
        if last_marked_time and (time.time() - last_marked_time) >= auto_close_delay:
            break

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
                                last_marked_time = time.time()
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

        fps = 1 / (new_frame_time - prev_frame_time) if (new_frame_time - prev_frame_time) > 0 else 0
        prev_frame_time = new_frame_time
        fps_text = f"{int(fps)}"
        cv2.putText(img, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

        # Show auto-close countdown if attendance was marked
        if last_marked_time:
            remaining = max(0, auto_close_delay - (time.time() - last_marked_time))
            countdown_text = f"Closing in {remaining:.1f}s..."
            cv2.putText(img, countdown_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Show instruction text
        cv2.putText(img, "Press 'Q' to quit", (10, img.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow(window_name, img)

        # Bring window to front on the first frame
        if prev_frame_time == new_frame_time:
            try:
                hwnd = ctypes.windll.user32.FindWindowW(None, window_name)
                if hwnd:
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    if marked_attendance:
        flash(f"Attendance marked for: {', '.join(marked_attendance)}", "success")
    return redirect(url_for('app.main'))



SECURE_PASSWORD = os.environ.get("SECURE_PASSWORD", "panda")

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


# ═══════════════════════════════════════════
# Admin Panel Routes
# ═══════════════════════════════════════════

def admin_required(f):
    """Decorator to check if user is logged in as admin."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('app.admin_login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('app.admin_dashboard'))
        else:
            error = 'Invalid username or password'
    return render_template('admin_login.html', error=error)


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('app.admin_login'))


@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    today = datetime.now().date()
    today_attendance = Attendance.query.filter_by(date=today).all()
    today_count = len(today_attendance)
    total_registered = User.query.count()
    total_records = Attendance.query.count()
    today_rate = round((today_count / total_registered * 100), 1) if total_registered > 0 else 0
    all_users = User.query.all()

    # Get available years for yearly report
    years_query = db.session.query(extract('year', Attendance.date)).distinct().all()
    years = sorted([int(y[0]) for y in years_query if y[0]], reverse=True)
    current_year = datetime.now().year
    if current_year not in years:
        years.insert(0, current_year)

    return render_template('admin_dashboard.html',
        today_attendance=today_attendance,
        today_count=today_count,
        total_registered=total_registered,
        total_records=total_records,
        today_rate=today_rate,
        all_users=all_users,
        years=years,
        current_year=current_year,
        current_date=today.strftime('%Y-%m-%d')
    )


@app.route('/admin/monthly_report')
@admin_required
def monthly_report():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    if not year or not month:
        return jsonify({'error': 'Year and month required'}), 400

    records = db.session.query(Attendance, User).join(User).filter(
        extract('year', Attendance.date) == year,
        extract('month', Attendance.date) == month
    ).order_by(Attendance.date, Attendance.time).all()

    records_list = [{
        'name': user.name,
        'roll': user.roll,
        'date': att.date.strftime('%Y-%m-%d'),
        'time': att.time.strftime('%I:%M:%S %p') if att.time else ''
    } for att, user in records]

    unique_dates = set(att.date for att, user in records)
    unique_students = set(user.id for att, user in records)

    return jsonify({
        'records': records_list,
        'total_entries': len(records_list),
        'working_days': len(unique_dates),
        'unique_students': len(unique_students)
    })


@app.route('/admin/yearly_report')
@admin_required
def yearly_report():
    year = request.args.get('year', type=int, default=datetime.now().year)

    monthly_counts = []
    for m in range(1, 13):
        count = Attendance.query.filter(
            extract('year', Attendance.date) == year,
            extract('month', Attendance.date) == m
        ).count()
        monthly_counts.append(count)

    total_entries = sum(monthly_counts)
    unique_students = db.session.query(func.count(func.distinct(Attendance.user_id))).filter(
        extract('year', Attendance.date) == year
    ).scalar() or 0

    active_days = db.session.query(func.count(func.distinct(Attendance.date))).filter(
        extract('year', Attendance.date) == year
    ).scalar() or 0

    return jsonify({
        'monthly_counts': monthly_counts,
        'total_entries': total_entries,
        'unique_students': unique_students,
        'active_days': active_days
    })


@app.route('/admin/student_report/<int:user_id>')
@admin_required
def student_report(user_id):
    user = User.query.get_or_404(user_id)
    records = Attendance.query.filter_by(user_id=user.id).order_by(Attendance.date.desc()).all()

    total_days_in_system = db.session.query(func.count(func.distinct(Attendance.date))).scalar() or 1
    total_present = len(records)
    percentage = round((total_present / total_days_in_system * 100), 1) if total_days_in_system > 0 else 0

    records_list = [{
        'date': r.date.strftime('%Y-%m-%d'),
        'time': r.time.strftime('%I:%M:%S %p') if r.time else ''
    } for r in records]

    last_seen = records[0].date.strftime('%Y-%m-%d') if records else None

    return jsonify({
        'name': user.name,
        'roll': user.roll,
        'phone': user.phone or '',
        'email': user.email or '',
        'address': user.address or '',
        'total_present': total_present,
        'attendance_percentage': percentage,
        'last_seen': last_seen,
        'records': records_list
    })


@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        # Delete attendance records
        Attendance.query.filter_by(user_id=user.id).delete()
        # Delete known face
        KnownFace.query.filter_by(name=user.name).delete()
        # Delete face image
        for filename in os.listdir(faces_directory):
            if user.roll in filename:
                os.remove(os.path.join(faces_directory, filename))
        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/admin/clear_all', methods=['POST'])
@admin_required
def admin_clear_all():
    try:
        Attendance.query.delete()
        KnownFace.query.delete()
        User.query.delete()
        db.session.commit()

        for filename in os.listdir(faces_directory):
            file_path = os.path.join(faces_directory, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/admin/export_csv')
@admin_required
def export_csv():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    query = db.session.query(Attendance, User).join(User)

    if year and month:
        query = query.filter(
            extract('year', Attendance.date) == year,
            extract('month', Attendance.date) == month
        )
        filename = f'attendance_{year}_{month:02d}.csv'
    else:
        filename = 'attendance_all.csv'

    records = query.order_by(Attendance.date, Attendance.time).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['#', 'Name', 'Roll No', 'Date', 'Time'])
    for i, (att, user) in enumerate(records, 1):
        writer.writerow([
            i,
            user.name,
            user.roll,
            att.date.strftime('%Y-%m-%d'),
            att.time.strftime('%I:%M:%S %p') if att.time else ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )