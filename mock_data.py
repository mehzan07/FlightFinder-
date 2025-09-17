from datetime import datetime, timedelta

# ✅ Airline code-to-name mapping
AIRLINE_NAMES = {
    "RY": "Ryanair",
    "LH": "Lufthansa",
    "ANA": "All Nippon Airways",
    "JAL": "Japan Airlines",
    "QF": "Qantas",
    "THY": "Turkish Airlines",
    "AF": "Air France",
    "TK": "Turkish Airlines",
    "PC": "Pegasus Airlines",
    "SAS": "Scandinavian Airlines",
    "BA": "British Airways",
    "KLM": "KLM Royal Dutch Airlines"
}

def mock_kiwi_response():
    destinations = {
        "TYO": ["RY", "LH", "ANA", "JAL", "QF"],
        "IKA": ["THY", "QF", "LH", "AF", "TK"],
        "AYT": ["THY", "LH", "PC", "TK", "QF"],
        "IST": ["THY", "TK", "LH", "AF", "PC"],
        "LON": ["SAS", "BA", "LH", "AF", "RY"],
        "MAN": ["LH", "BA", "SAS", "AF", "RY"],
        "CDG": ["AF", "LH", "RY", "BA", "SAS"],
        "AMS": ["KLM", "LH", "AF", "RY", "BA"]
    }

    base_departure = datetime(2025, 10, 10, 6, 0)
    base_return = datetime(2025, 10, 17, 18, 0)

    raw_flights = []
    flight_id = 1

    for destination, airline_codes in destinations.items():
        for i in range(5):
            airline_code = airline_codes[i % len(airline_codes)]
            airline_name = AIRLINE_NAMES.get(airline_code, airline_code)
            airline_display = f"{airline_code} - {airline_name}"  # ✅ Bonus tip: code + name

            flight_number = f"{airline_code}{100 + i}"  # Fictive flight number
            duration = f"{6 + i}h {30 + (i * 5) % 60}m"  # Fictive duration

            flight = {
                "id": flight_id,
                "origin": "STO",
                "destination": destination,
                "price": 100 + i * 10,
                "departure": base_departure + timedelta(hours=i * 2),
               "return": base_return + timedelta(minutes=(i % 16) * 60),
                "airlines": [airline_display],  # ✅ Full name with code
                "flight_number": flight_number,
                "duration": duration,
                "stops": 0,
                "cabin_class": "Economy",
                "vendor": "Kiwi",
                "deep_link": f"https://example.com/book?flight_id={flight_id}"
            }

            raw_flights.append(flight)
            flight_id += 1

    return raw_flights