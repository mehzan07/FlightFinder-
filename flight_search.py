from flask import request

from datetime import datetime
import requests
import os
from dotenv import load_dotenv
from mock_data import mock_kiwi_response
from utils import generate_flight_id


load_dotenv()

API_TOKEN = os.getenv("TRAVELPAYOUTS_API_TOKEN")
USE_REAL_API = False  # Change to True when ready


def search_flights(origin_code, destination_code, date_from_str, date_to_str, trip_type):
    if USE_REAL_API:
        return search_flights_api(origin_code, destination_code, date_from_str, date_to_str, trip_type)
    else:
        return search_flights_mock(origin_code, destination_code, date_from_str, date_to_str, trip_type)
    
    # Update the mock function to accept trip_typ
def search_flights_mock(origin_code, destination_code, date_from_str, date_to_str, trip_type):
    try:
        date_from = datetime.strptime(date_from_str, "%Y-%m-%d").date()
        date_to = datetime.strptime(date_to_str, "%Y-%m-%d").date() if date_to_str else None
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD.")
        return []

    flights = mock_kiwi_response()
    filtered = []
    skipped_flights = []

    print(f"\n🔍 Searching flights from {origin_code} to {destination_code}")
    print(f"📅 Departure date: {date_from}" + (f" | Return date: {date_to}" if date_to else " (One-way trip)"))

    for flight in flights:
        flight_origin = flight.get("origin")
        flight_destination = flight.get("destination")
        departure_date = flight.get("departure").date() if flight.get("departure") else None
         #Only define return_date if it's a round-trip
        return_date = flight.get("return").date() if trip_type == "round-trip" and flight.get("return") else None
        flight_price = flight.get("price")
        deep_link = flight.get("deep_link")
        trip_type= trip_type

        if flight_origin != origin_code or flight_destination != destination_code:
            continue
        if not departure_date or departure_date != date_from:
            continue
        if date_to and (not return_date or return_date != date_to):
          continue
        

        # Validate and sanitize deep_link
        if not deep_link or not isinstance(deep_link, str) or deep_link.strip() == "":
            print(f"⚠️ Skipping flight with missing or invalid deep_link: {flight}")
            skipped_flights.append(flight)
            continue
        if not deep_link.startswith("http"):
            deep_link = "https://" + deep_link.strip()

        # Diagnostic check for missing fields
        missing_fields = [key for key in ["flight_number", "duration", "stops", "cabin_class"] if key not in flight]
        if missing_fields:
            print(f"⚠️ Missing fields in flight {flight.get('id', 'Unknown')}: {missing_fields}")

        print(f"✅ Flight link: {deep_link}")

        filtered.append({
            "id": flight.get("id"),
            "airlines": flight.get("airlines", ["Unknown"]),
            "flight_number": flight.get("flight_number", "N/A"),
            "duration": flight.get("duration", "N/A"),
            "stops": flight.get("stops", 0),
            "cabin_class": flight.get("cabin_class", "Economy"),
            "price": flight_price,
            "departure": flight.get("departure"),
            "return": flight.get("return") if trip_type == "round-trip" else None,
            "vendor": flight.get("vendor", "MockVendor"),
            "deep_link": deep_link, 
            "trip_type": trip_type
        })
        

    print(f"\n🎯 Total matching flights: {len(filtered)}")

    if skipped_flights:
        print(f"\n🚫 Total skipped flights due to invalid deep_link: {len(skipped_flights)}")
        for i, f in enumerate(skipped_flights, 1):
            print(f"{i}. {f}")

    return filtered


def search_flights_api(origin_code, destination_code, date_from_str, date_to_str=None, trip_type="round-trip"):
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

    # Build parameters dynamically
    params = {
        "origin": origin_code,
        "destination": destination_code,
        "departure_at": date_from_str,
        "token": API_TOKEN,
        "currency": "eur"
    }

    if date_to_str:
        params["return_at"] = date_to_str

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ API error: {response.status_code}")
        return []

    data = response.json().get("data", [])
    filtered = []

    print(f"\n🌐 API returned {len(data)} flights")

    for flight in data:
        price = flight.get("value")
        departure = flight.get("departure_at")
        return_date = flight.get("return_at")  # May be None for one-way
        airline = flight.get("airline", "Unknown")
        deep_link = flight.get("link")

        # Validate and sanitize deep_link
        if not deep_link or not isinstance(deep_link, str) or deep_link.strip() == "":
            print(f"⚠️ Skipping flight with missing or invalid deep_link: {flight}")
            continue

        if not deep_link.startswith("http"):
            deep_link = "https://" + deep_link.strip()

        print(f"✅ API Flight link: {deep_link}")

        filtered.append({
            "id": generate_flight_id(deep_link, airline, departure),
            "airline": airline,
            "price": price,
            "depart": departure,
            "return": return_date,
            "vendor": "Travelpayouts",
            "link": deep_link,
        })

    print(f"\n🎯 Total matching flights from API: {len(filtered)}")
    return filtered