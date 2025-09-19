from datetime import datetime
import requests
import os
from dotenv import load_dotenv
from mock_data import mock_kiwi_response
import time
import json
import hashlib

load_dotenv()

AFFILIATE_MARKER = os.getenv("AFFILIATE_MARKER")
API_TOKEN = os.getenv("API_TOKEN")
HOST = os.getenv("HOST", "localhost")
USER_IP = os.getenv("USER_IP", "127.0.0.1")
USE_REAL_API = os.getenv("USE_REAL_API", "False").lower() == "true"

def search_flights(origin_code, destination_code, date_from_str, date_to_str, trip_type, adults=1, children=0, infants=0, cabin_class="economy"):
    if USE_REAL_API:
        return search_flights_api(origin_code, destination_code, date_from_str, date_to_str,
                                  trip_type, adults, children, infants, cabin_class)
    else:
        return search_flights_mock(origin_code, destination_code, date_from_str, date_to_str, trip_type)

def map_cabin_class(cabin_class):
    return {
        "economy": "Y",
        "business": "C",
        "first": "F"
    }.get(cabin_class.lower(), "Y")

def generate_flight_id(link, airline, departure):
    raw = f"{airline}_{departure}_{link}"
    return hashlib.md5(raw.encode()).hexdigest()

def generate_signature(token, marker, host, user_ip, locale, trip_class, passengers, segments):
    values = []

    values.append(host)
    values.append(locale)
    values.append(marker)

    for key in ["adults", "children", "infants"]:
        values.append(str(passengers.get(key, 0)))

    for segment in segments:
        for key in ["date", "destination", "origin"]:
            values.append(str(segment.get(key)))

    values.append(trip_class)
    values.append(user_ip)

    raw_string = f"{token}:" + ":".join(values)
    print("🔐 Raw signature string:", raw_string)  # ✅ Add this line
    return hashlib.md5(raw_string.encode()).hexdigest()

def search_flights_api(origin_code, destination_code, date_from_str, date_to_str=None,
                       trip_type="round-trip", adults=1, children=0, infants=0, cabin_class="economy"):

    init_url = "https://api.travelpayouts.com/v1/flight_search"

    segments = [
    {
        "date": date_from_str,
        "destination": destination_code,
        "origin": origin_code
    }
]
    if trip_type == "round-trip" and date_to_str:
     segments.append({
        "date": date_to_str,
        "destination": origin_code,
        "origin": destination_code
    })

    payload = {
        "marker": AFFILIATE_MARKER,
        "host": HOST,
        "user_ip": USER_IP,
        "locale": "en",
        "trip_class": map_cabin_class(cabin_class),
        "passengers": {
            "adults": int(adults),
            "children": int(children),
            "infants": int(infants)
        },
        "segments": segments
    }

    payload["signature"] = generate_signature(
        token=API_TOKEN,
        marker=AFFILIATE_MARKER,
        host=HOST,
        user_ip=USER_IP,
        locale="en",
        trip_class=cabin_class.upper(),
        passengers=payload["passengers"],
        segments=payload["segments"]
    )

    headers = {
        "Content-Type": "application/json"
    }

    print(f"🌐 Initiating search: {init_url}")
    print("📦 Final JSON payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(init_url, json=payload, headers=headers)
        print(f"📥 Raw response: {response.text}")
        if response.status_code != 200:
            print(f"❌ API error: {response.status_code}")
            return []
        search_id = response.json().get("search_id") or response.json().get("uuid")
        if not search_id:
            print("❌ No search_id returned")
            return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return []

    results_url = f"https://api.travelpayouts.com/v1/flight_search_results?uuid={search_id}"
    print(f"🔄 Polling results from: {results_url}")

    proposals = []
    for attempt in range(5):
        try:
            time.sleep(3)
            results_response = requests.get(results_url)
            print(f"📥 Results response: {results_response.text}")
            if results_response.status_code == 200:
                proposals = results_response.json()
                if proposals:
                    break
            else:
                print(f"⚠️ Attempt {attempt+1}: Status {results_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Polling failed: {e}")
            return []
    else:
        print("❌ No results after polling")
        return []

    filtered = []
    print(f"\n🌐 API returned {len(proposals)} proposals")

    for item in proposals:
        for proposal in item.get("proposals", []):
            terms = proposal.get("terms", {})
            for gate_id, term_data in terms.items():
                price = term_data.get("price")
                currency = term_data.get("currency")
                url_code = term_data.get("url")
                airline = proposal.get("carriers", ["Unknown"])[0]
                segment = proposal.get("segment", [])
                departure = segment[0]["flight"][0]["departure"] if segment else "Unknown"

                booking_link = f"https://www.travelpayouts.com/redirect/{url_code}"

                print(f"✅ API Flight link: {booking_link}")

                filtered.append({
                    "id": generate_flight_id(booking_link, airline, departure),
                    "airline": airline,
                    "price": price,
                    "currency": currency,
                    "depart": departure,
                    "vendor": "Travelpayouts",
                    "link": booking_link,
                    "trip_type": trip_type
                })

    print(f"\n🎯 Total matching flights from API: {len(filtered)}")
    return filtered

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
        return_date = flight.get("return").date() if trip_type == "round-trip" and flight.get("return") else None
        flight_price = flight.get("price")
        deep_link = flight.get("deep_link")

        if flight_origin != origin_code or flight_destination != destination_code:
            continue
        if not departure_date or departure_date != date_from:
            continue
        if date_to and (not return_date or return_date != date_to):
            continue

        if not deep_link or not isinstance(deep_link, str) or deep_link.strip() == "":
            print(f"⚠️ Skipping flight with missing or invalid deep_link: {flight}")
            skipped_flights.append(flight)
            continue
        if not deep_link.startswith("http"):
            deep_link = "https://" + deep_link.strip()

        missing_fields = [key for key in ["flight_number", "duration", "stops", "cabin_class"] if key not in flight]
        if missing_fields:
            print(f"⚠️ Missing fields in flight {flight.get('id', 'Unknown')}: {missing_fields}")

        print(f"✅ Flight link: {deep_link}")

        filtered.append({
            "id": generate_flight_id(deep_link, flight.get("airlines", ["Unknown"])[0], flight.get("departure")),
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


