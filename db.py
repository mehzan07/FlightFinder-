# db.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import os
from sqlalchemy.exc import SQLAlchemyError

from database import db

# === Load environment variables ===
load_dotenv()

# === Ensure DATABASE_URL is set ===
if not os.getenv("DATABASE_URL"):
    raise ValueError("DATABASE_URL environment variable is not set.")

# --------------------------
# Booking Helper Functions
# --------------------------

def save_booking(reference, passenger, flight_json):
    from models import Booking  # Lazy import to avoid circular dependencies

    try:
        new_booking = Booking(
            reference=reference,
            passenger_name=passenger["name"],
            passenger_email=passenger["email"],
            passenger_phone=passenger["phone"],
            flight_data=flight_json,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_booking)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving booking: {e}")
        raise e
    finally:
        db.session.close()

def get_booking_history():
    from models import Booking
    try:
        return Booking.query.order_by(Booking.timestamp.desc()).all()
    except SQLAlchemyError as e:
        print(f"Error fetching booking history: {e}")
        return []