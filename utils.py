import re
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any

import dateparser
from word2number import w2n
import spacy

logger = logging.getLogger(__name__)
nlp = spacy.load("en_core_web_sm")

def normalize_passenger_count(text: str) -> int:
    text = text.lower()

    if "me and my" in text or "my partner" in text:
        return 2
    if "family" in text:
        return 4
    if "group" in text:
        return 5

    match = re.search(r"(\d+)\s*(passenger|people|adults|persons)?", text)
    if match:
        return int(match.group(1))

    try:
        return w2n.word_to_num(text)
    except:
        return 1



def parse_date(text: str):
    """
    Parses a natural language date string (e.g. 'Oct 5', 'next Monday') into a datetime object.
    Returns None if parsing fails.
    """
    parsed = dateparser.parse(text)
    if not parsed:
        return None
    return parsed


def extract_travel_entities(user_input: str) -> Dict[str, Any]:
    info = {}
    input_lower = user_input.lower()

    print(f"🔍 Raw input: {user_input}")

    # 📅 Extract travel dates
    date_range_match = re.search(r'from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})', input_lower)
    one_way_match = re.search(r'(?:on|departing)\s+(\d{4}-\d{2}-\d{2})', input_lower)

    try:
     if date_range_match:
        info["date_from"] = datetime.strptime(date_range_match.group(1), "%Y-%m-%d")
        info["date_to"] = datetime.strptime(date_range_match.group(2), "%Y-%m-%d")
        info["trip_type"] = "round-trip"
     elif one_way_match:
        info["date_from"] = datetime.strptime(one_way_match.group(1), "%Y-%m-%d")
        info["trip_type"] = "one-way"    
    except ValueError:
     print("⚠️ Invalid date format detected.") 

    print(f"📅 Parsed dates: from={info.get('date_from')} to={info.get('date_to')}")

    # ✈️ Extract origin and destination
    from_match = re.search(r'from\s+([a-zA-Z\s]+?)\s+(?:to|until)', input_lower)
    to_match = re.search(r'to\s+([a-zA-Z\s]+?)\s+(?:from|on|until)', input_lower)
    if from_match:
        info["origin"] = from_match.group(1).strip()
    if to_match:
        info["destination"] = to_match.group(1).strip()

    # 👥 Extract number of passengers
    passengers_match = re.search(r'for\s+(\d+)\s+passengers?', input_lower)
    if passengers_match:
        info["passengers"] = int(passengers_match.group(1))

    print(f"✅ Extracted info: {info}")
    return info

def generate_flight_id(link: str, airline: str, departure: datetime) -> str:
    raw = f"{link}-{airline}-{departure}"
    return hashlib.md5(raw.encode()).hexdigest()
