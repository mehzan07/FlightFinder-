# test_signature.py:this to test creating of Generated signature:
#  Constructs the exact raw string used for hashing 
# Calls your generate_signature() function 
# Prints both the raw string and the resulting MD5 hash

from dotenv import load_dotenv
import os

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")


from flight_search import generate_signature

def test_signature():
    token = API_TOKEN
    marker = "665788"
    host = "localhost"
    user_ip = "127.0.0.1"
    locale = "en"
    trip_class = "Y"
    passengers = {
        "adults": 1,
        "children": 0,
        "infants": 0
    }
    segments = [
        {
            "date": "2025-10-10",
            "destination": "TYO",
            "origin": "STO"
        },
        {
            "date": "2025-10-17",
            "destination": "STO",
            "origin": "TYO"
        }
    ]

    raw_string = f"{token}:{host}:{locale}:{marker}:{passengers['adults']}:{passengers['children']}:{passengers['infants']}:" \
                 f"{segments[0]['date']}:{segments[0]['destination']}:{segments[0]['origin']}:" \
                 f"{segments[1]['date']}:{segments[1]['destination']}:{segments[1]['origin']}:" \
                 f"{trip_class}:{user_ip}"

    expected_signature = generate_signature(
        token, marker, host, user_ip, locale, trip_class, passengers, segments
    )

    print("🔐 Raw signature string:")
    print(raw_string)
    print("\n✅ Generated signature:")
    print(expected_signature)

if __name__ == "__main__":
    test_signature()