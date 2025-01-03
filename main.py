# main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai

# 1) Initialize FastAPI app
app = FastAPI()

# 2) Configure OpenAI (reads from an environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set!")

# 3) Create request/response data models using Pydantic
class ItineraryRequest(BaseModel):
    travel_dates: str
    number_of_adults: int
    number_of_children: int
    children_ages: list[int]
    preferences: str  # e.g. "Minimal walking, wants to see fireworks, etc."

class ItineraryResponse(BaseModel):
    itinerary_text: str

# 4) Root endpoint for a quick health check
@app.get("/")
def read_root():
    return {"message": "Hello from the Disney Trip Planner API!"}

# 5) Post endpoint to generate an itinerary using OpenAI
@app.post("/generate-itinerary", response_model=ItineraryResponse)
def generate_itinerary(request: ItineraryRequest):
    # Construct a prompt for OpenAI using request data
    prompt = f"""
You are a helpful Disney World trip planner. The user has the following info:
- Travel Dates: {request.travel_dates}
- Number of Adults: {request.number_of_adults}
- Number of Children: {request.number_of_children}
- Children Ages: {request.children_ages}
- Preferences: {request.preferences}

Please create a short, 3-day itinerary for their trip to Disney World in Florida, 
including which parks to visit on each day, suggested rides (especially for the children's ages),
meal recommendations, and any relevant tips.
Provide the itinerary in a concise format.
"""

    try:
        # Call the OpenAI API (GPT-3.5 or GPT-4, whichever you prefer)
        response = openai.Completion.create(
            engine="text-davinci-003",  # or "gpt-3.5-turbo" if using ChatCompletion
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
        )
        itinerary_text = response["choices"][0]["text"].strip()

        return ItineraryResponse(itinerary_text=itinerary_text)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
