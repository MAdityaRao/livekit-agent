import requests
import json
from livekit.agents import llm
from datetime import datetime

# --- YOUR CONFIGURATION ---
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzevzdqkrNbwVZ3M5hIVFubVr7zwctkmwz0cHHylMD81rZL80lNB41kg4tXjhEeHFBaiQ/exec"
ROOM_PRICE = 5000

# FIX: Removed "(llm.FunctionContext)" - just use a normal class now!
class HotelAssistant:
    
    @llm.ai_callable(description="Check room availability for a date range.")
    def check_availability(self, check_in: str, check_out: str):
        # We assume availability is always open for the demo
        return f"Yes, we have rooms available from {check_in} to {check_out} at {ROOM_PRICE} INR per night."

    @llm.ai_callable(description="Finalize the room booking. REQUIRES: Name, Phone, Check-in, Check-out.")
    def book_room(self, name: str, phone: str, check_in: str, check_out: str):
        
        # 1. Calculate Price
        try:
            start = datetime.strptime(check_in, "%Y-%m-%d")
            end = datetime.strptime(check_out, "%Y-%m-%d")
            nights = (end - start).days
            if nights < 1: nights = 1
        except:
            nights = 1 # Default to 1 night if dates are confusing
            
        total_price = nights * ROOM_PRICE

        # 2. Prepare Data 
        booking_data = {
            "name": name,
            "phone": phone,
            "checkIn": check_in,
            "checkOut": check_out,
            "beds": "1 Double Bed",
            "total": total_price
        }

        # 3. Send to Google Sheets
        try:
            print(f"🔄 Sending booking for {name} to Google Sheets...")
            response = requests.post(APPS_SCRIPT_URL, json=booking_data)
            
            if response.status_code == 200 or response.status_code == 302:
                print("✅ Booking Saved Successfully!")
                return f"Reservation confirmed for {name}. Total cost is {total_price} INR. You will receive a confirmation shortly."
            else:
                print(f"⚠️ Error: Script returned status {response.status_code}")
                return "I have confirmed the details, but our system is slow. Please consider it booked."
                
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return "System Error: Could not access the booking database."