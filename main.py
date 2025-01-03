# main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# Initialize FastAPI
app = FastAPI()

# --- 1. Define the allowed origins ---
# If you only trust your Vercel domain, replace "*" with the exact domain(s),
# like "https://disney-frontend.vercel.app" 
origins = [
    "*",
    "http://localhost:3000",  # if you ever do local dev
]

# --- 2. Add the CORS middleware configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],            # or specify ["GET", "POST", ...]
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Pydantic models
class ItineraryRequest(BaseModel):
    travel_dates: str
    number_of_adults: int
    number_of_children: int
    children_ages: list[int]
    preferences: str

class ItineraryResponse(BaseModel):
    itinerary_text: str

@app.get("/")
def read_root():
    return {"message": "Hello from the Disney Trip Planner API (ChatCompletion)!"}

@app.post("/generate-itinerary", response_model=ItineraryResponse)
def generate_itinerary(request: ItineraryRequest):
    # Construct a system + user message approach for ChatCompletion
    system_content = (
        "You are a helpful Disney World trip planner. Provide concise, friendly, and accurate itineraries."
    )
    user_content = f"""
Travel Dates: {request.travel_dates}
Number of Adults: {request.number_of_adults}
Number of Children: {request.number_of_children}
Children Ages: {request.children_ages}
Preferences: {request.preferences}

Create a 3-day itinerary for Disney World Florida, including recommended parks,
rides suitable for these ages, meal options, and any useful tips.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            max_tokens=2500,
            temperature=0.7,
        )
        # Extract the assistant's reply
        itinerary_text = response.choices[0].message.content.strip()
        return ItineraryResponse(itinerary_text=itinerary_text)

    except Exception as e:
        # Log the error in the server logs
        print("Error calling OpenAI ChatCompletion:", e)
        raise HTTPException(status_code=500, detail=str(e))
