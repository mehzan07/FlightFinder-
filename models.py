# models.py
from datetime import datetime
from database import db

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True, nullable=False)
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_email = db.Column(db.String(100), nullable=False)
    passenger_phone = db.Column(db.String(20), nullable=False)
    flight_data = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)