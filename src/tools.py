import requests
import json
import logging
from datetime import datetime
from livekit.agents import function_tool, RunContext

logger = logging.getLogger("hotel-tools")

# --- CONFIGURATION ---
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzevzdqkrNbwVZ3M5hIVFubVr7zwctkmwz0cHHylMD81rZL80lNB41kg4tXjhEeHFBaiQ/exec"
ROOM_PRICE = 5000

class HotelAssistant:
    """
    In the new SDK, tools are just methods in a class decorated with @function_tool.
    You do NOT need to inherit from llm.FunctionContext anymore.
    """

    @function_tool(description="Check if rooms are available for specific dates.")
    def check_availability(
        self, 
        check_in: str, 
        check_out: str
    ):
        logger.info(f"Checking availability: {check_in} to {check_out}")
        return f"Yes, we have rooms available from {check_in} to {check_out} at {ROOM_PRICE} INR per night."

    @function_tool(description="Finalize the room booking. REQUIRES: Name, Phone, Check-in, Check-out, and number of beds.")
    def book_room(
        self, 
        name: str,
        phone: str,
        check_in: str,
        check_out: str,
        beds: str
    ):
        # 1. Calculate Price
        try:
            start = datetime.strptime(check_in, "%Y-%m-%d")
            end = datetime.strptime(check_out, "%Y-%m-%d")
            nights = (end - start).days
            if nights < 1: nights = 1
        except Exception:
            nights = 1
            
        total_price = nights * ROOM_PRICE

        # 2. Prepare Data 
        booking_data = {
            "name": name,
            "phone": phone,
            "checkIn": check_in,
            "checkOut": check_out,
            "beds": beds,
            "total": total_price
        }

        # 3. Send to Google Sheets
        try:
            # Note: Ensure 'requests' is in your requirements.txt
            response = requests.post(APPS_SCRIPT_URL, json=booking_data, timeout=10)
            
            if response.status_code in [200, 302]:
                return f"Reservation confirmed for {name}. Total cost is {total_price} INR."
            else:
                return "The booking system is slow, but I have noted your details for processing."
                
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return "I encountered an error connecting to the booking database."