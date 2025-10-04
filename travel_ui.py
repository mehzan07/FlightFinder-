from flask import Blueprint, render_template, request, jsonify
from travel import travel_chatbot
from datetime import datetime
from config import DEBUG_MODE, FEATURED_FLIGHT_LIMIT
import json

from config import get_logger
logger = get_logger(__name__)


offers_db = {}
travel_bp = Blueprint("travel", __name__)

def format_datetime(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        return dt.strftime("%b %d, %H:%M")
    except Exception:
        return "Not available"

@travel_bp.route("/travel-ui", methods=["GET", "POST"])
def travel_ui():
    logger.info("travel_ui route hit")
    logger.debug(f"Request method: {request.method}")
    print("DEBUG_MODE is:", DEBUG_MODE)

    if request.method == "POST":
        limit = request.form.get("limit", FEATURED_FLIGHT_LIMIT, type=int)
    else:
        limit = request.args.get("limit", FEATURED_FLIGHT_LIMIT, type=int)

    if request.method == "POST":
        origin_code = request.form.get("origin_code", "").strip()
        destination_code = request.form.get("destination_code", "").strip()
        date_from_raw = request.form.get("date_from", "").strip()
        date_to_raw = request.form.get("date_to", "").strip()
        passengers_raw = request.form.get("passengers", "1").strip()
        cabin_class = request.form.get("cabin_class", "").strip()
        trip_type = request.form.get("trip_type", "round-trip").strip()
        direct_only = request.form.get("direct_only") == "on"

        errors = []
        if trip_type != "one-way" and not date_to_raw:
            errors.append("Return date is required for round-trip.")

        form_data = request.form

        date_from = date_to = None
        if not origin_code:
            errors.append("Origin airport is required.")
            if DEBUG_MODE:
                print("⚠️ Origin airport is required.")
        if not destination_code:
            errors.append("Destination airport is required.")
            if DEBUG_MODE:
                print("⚠️  Destination airport is required.")
        if not date_from_raw:
            errors.append("Departure date is required.")
        if trip_type != "one-way" and not date_to_raw:
            errors.append("Return date is required for round-trip.")
        if not cabin_class:
            errors.append("Cabin class is required.")

        try:
            date_from = datetime.strptime(date_from_raw, "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid departure date format.")
            if DEBUG_MODE:
                print("⚠️  date_from: Invalid departure date format.")

        if trip_type != "one-way" and date_to_raw:
            try:
                date_to = datetime.strptime(date_to_raw, "%Y-%m-%d")
                if date_from and date_to and date_from > date_to:
                    errors.append("Return date must be after departure date.")
            except ValueError:
                errors.append("Invalid return date format.")
                
                form_data = request.form.copy()
                form_data["direct_only"] = direct_only

        try:
            passengers = int(passengers_raw)
            if passengers < 1:
                errors.append("Number of passengers must be at least 1.")
        except ValueError:
            errors.append("Invalid number of passengers.")
            passengers = 1

        if errors:
            return render_template("travel_form.html", errors=errors, form_data=form_data)

        if trip_type == "one-way":
            user_input = (
                f"Fly one-way from {origin_code} to {destination_code} on {date_from_raw} "
                f"for {passengers} passengers in {cabin_class} class via {origin_code} to {destination_code}"
            )
        else:
            user_input = (
                f"Fly from {origin_code} to {destination_code} from {date_from_raw} to {date_to_raw} "
                f"for {passengers} passengers in {cabin_class} class via {origin_code} to {destination_code}"
            )

        try:
            result = travel_chatbot( user_input,trip_type=trip_type, limit=limit, direct_only=direct_only)
        except Exception as e:
            error_msg = f"WARNING: Something went wrong while processing your request: {str(e)}"
            return render_template("travel_form.html", errors=[error_msg], form_data=form_data)

        offers_db.clear()
        trip_info = result.get("trip_info", {})
        flights = result.get("flights", [])

        for prepared_flight in flights:
            prepared_flight["origin"] = trip_info.get("origin", origin_code)
            prepared_flight["destination"] = trip_info.get("destination", destination_code)
            prepared_flight["depart_formatted"] = format_datetime(prepared_flight.get("depart", ""))
            prepared_flight["return_formatted"] = format_datetime(prepared_flight.get("return", ""))
            offers_db[prepared_flight["id"]] = prepared_flight

        DISPLAY_LIMIT = 3
        top_offers = flights[:DISPLAY_LIMIT]
        show_more = len(flights) > len(top_offers)

        debug_mode = request.args.get("debug") == "true"
        print("DEBUG MODE:", debug_mode)

        return render_template(
            "travel_results.html",
            top_offers=top_offers,
            flights=flights,
            message=result.get("message"),
            summary=result.get("summary"),
            affiliate_link=result.get("affiliate_link"),
            trip_info=trip_info,
            show_more=show_more,
            debug_payload=result if debug_mode else None,
            direct_only=direct_only
        )

    return render_template("travel_form.html")

@travel_bp.route("/offer/<offer_id>")
def view_offer(offer_id):
    offer = offers_db.get(offer_id)
    if offer is None:
        error_msg = f" Warning No offer found for ID: {offer_id}"
        return render_template("travel_form.html", errors=[error_msg])
    return render_template("travel_offer_details.html", offer=offer)


@travel_bp.route("/autocomplete-airports")
def autocomplete_airports():
    logger.info("Autocomplete route hit!")
    query = request.args.get("query", "").strip().lower()
    logger.debug(f"Query received: '{query}'")

    with open("airports.json", "r", encoding="utf-8") as f:
        airports = json.load(f)

    tokens = query.replace("(", "").replace(")", "").replace("-", "").split()

    matches = [a for a in airports if any(
        is_token_match(token, a) for token in tokens if len(token) >= 1
    )]

    logger.debug(f"Matched airports: {[a['iata'] for a in matches]}")

    results = [{
        "value": f'{a["city"]} ({a["iata"]})',
        "label": f'{a["name"]} — {a["city"]} ({a["iata"]})'
    } for a in matches]

    return jsonify(results)


def is_token_match(token, airport):
    return (
        airport["city"].lower().startswith(token) or
        airport["name"].lower().startswith(token) or
        airport["iata"].lower().startswith(token)
    )