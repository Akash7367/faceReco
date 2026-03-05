from .extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(250), nullable=True)

    attendance_records = db.relationship('Attendance', back_populates='user', lazy=True)

    def __repr__(self):
        return f"User('{self.name}', '{self.roll}')"

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    time = db.Column(db.Time, default=datetime.utcnow().time)

    user = db.relationship('User', back_populates='attendance_records', lazy=True)

    def __repr__(self):
        return f"Attendance('{self.user_id}', '{self.date}', '{self.time}')"



class KnownFace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    encoding = db.Column(db.PickleType, nullable=False)
