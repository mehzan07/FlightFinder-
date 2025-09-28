# app.py — FlightFinder main Flask app

import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect

from travel_ui import travel_bp
from travel import travel_form_handler
from utils import extract_travel_entities
from flight_search import search_flights
from iata_codes import city_to_iata

from dotenv import load_dotenv
import os

from config import get_logger
logger = get_logger(__name__)

# === Load environment variables ===
load_dotenv()
IS_LOCAL = os.getenv("IS_LOCAL", "false").lower() == "true"
if IS_LOCAL:
    logging.info("Running in local mode.")

AFFILIATE_MARKER = os.getenv("AFFILIATE_MARKER")

FLASK_ENV = os.getenv("FLASK_ENV", "development")
PORT = int(os.getenv("PORT", 10000))
API_TOKEN = os.getenv("TRAVELPAYOUTS_API_TOKEN")
MARKER = os.getenv("TRAVELPAYOUTS_MARKER")
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"


# === Initialize Flask app ===
app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "flightfinder-secret")  # Required for session
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['ENV'] = FLASK_ENV
app.config['DEBUG'] = FLASK_ENV == "development"

# === Register Blueprints ===
app.register_blueprint(travel_bp)

# === Logging ===
logging.basicConfig(
    level=logging.DEBUG if app.config['DEBUG'] else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

# Redirects root URL ('/') to the main FlightFinder route.
@app.route("/", methods=["GET"])
def home_page():
    return redirect("/flightfinder")

# === Primary FlightFinder Route ===
@app.route("/flightfinder", methods=["GET", "POST"])
def flightfinder():
    print("FlightFinder route triggered", flush=True)

    if request.method == "POST":
        user_input = request.form.get("user_input", "").strip()
        info = extract_travel_entities(user_input)

        origin_code = city_to_iata.get(info["origin"].lower())
        destination_code = city_to_iata.get(info["destination"].lower())

        if not origin_code or not destination_code:
            return render_template("travel_results.html", message="🌍 Unknown city. Try major cities like Paris or Tokyo.")

        if not info["date_from"] or not info["date_to"]:
            return render_template("travel_results.html", message="📅 Invalid dates. Please use YYYY-MM-DD format.")

        info["date_from_str"] = info["date_from"].strftime("%Y-%m-%d")
        info["date_to_str"] = info["date_to"].strftime("%Y-%m-%d")

        # ✅ Extract dynamic values from form
        trip_type = request.form.get("trip_type", "round-trip")
        adults = int(request.form.get("passengers", 1))
        children = int(request.form.get("children", 0))
        infants = int(request.form.get("infants", 0))
        cabin_class = request.form.get("cabin_class", "economy").lower()

        # ✅ Store last search in session
        session["last_search"] = {
            "origin": origin_code,
            "destination": destination_code,
            "departure": info["date_from_str"],
            "return": info["date_to_str"],  # ✅ Renamed for clarity
            "trip_type": trip_type,
            "adults": adults,
            "children": children,
            "infants": infants,
            "cabin_class": cabin_class
        }


        # ✅ Call the search function with all required arguments
        flights = search_flights(
            origin_code, destination_code,
            info["date_from_str"], info["date_to_str"],
            trip_type=trip_type,
            adults=adults, children=children, infants=infants,
            cabin_class=cabin_class
        )

        if not flights:
            fallback_message = "😕 No flights found or API error occurred. Try again later or adjust your search."
            return render_template("travel_results.html", message=fallback_message, info=info)

        return render_template("travel_results.html", flights=flights, info=info)

   # return render_template("travel_form.html", mode="chat")
    return render_template("travel_form.html", mode="chat", form_data={})

# === Travel Results & Confirmation ===
@app.route("/results", methods=["POST"])
def results():
    destination = request.form['destination']
    departure_date = request.form['departure_date']
    return_date = request.form['return_date']
    result = travel_form_handler(destination, departure_date, return_date)
    return render_template("travel_results.html", **result)

@app.route("/confirm", methods=["POST"])
def confirm():
    selected_flight = request.form.get("selected_flight")
    if not selected_flight:
        return "No flight selected", 400
    return render_template("confirmation.html", flight=selected_flight)

# === Health Check ===
@app.route("/health", methods=["GET"])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})

# === Dev-only Debugging ===
if __name__ == "__main__" and FLASK_ENV == "development":
    import debugpy
    debugpy.listen(("0.0.0.0", 5681))
    print("Waiting for debugger connection...")
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False, use_debugger=False)

# === Show Registered Routes ===
print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(rule)