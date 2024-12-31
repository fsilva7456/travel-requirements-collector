import os
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
from supabase import create_client, Client

app = FastAPI()

# ---------------------------------------------------------
# Environment Variables
# ---------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")  # Your Supabase project URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Your Supabase service role or anon key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API key

# Validate environment variables
if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
    raise Exception("Missing one or more required environment variables.")

# Initialize Supabase and OpenAI clients
openai.api_key = OPENAI_API_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------
# Conversation Context
# ---------------------------------------------------------
conversation_messages: List[Dict[str, str]] = [
    {
        "role": "system",
        "content": (
            "You are a helpful Disney travel planner. "
            "Your job is to collect these essential trip requirements from the user: "
            "1) Number of travelers, 2) Length of stay or travel dates, "
            "3) Origin, and 4) What's most important (budget, luxury, etc.). "
            "Ask questions until you have all four pieces of data. "
            "Once you have them, confirm with the user and provide a short summary. "
            "After that, the system will store it in the database."
        )
    }
]

class UserMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat_with_gpt(user_msg: UserMessage):
    """
    User sends a message; GPT asks questions or acknowledges info.
    Once GPT has all required details, the system inserts it into Supabase.
    """
    # Add user message to conversation history
    conversation_messages.append({"role": "user", "content": user_msg.message})

    # Call OpenAI's ChatCompletion endpoint
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",  # Replace with the correct model you're using
            messages=conversation_messages,
            temperature=0.7
        )
        gpt_reply = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Add GPT reply to conversation
    conversation_messages.append({"role": "assistant", "content": gpt_reply})

    # Check if GPT provided a final summary
    if "Summary of your trip details" in gpt_reply:
        # Attempt to parse details
        num_travelers = None
        length_of_stay = None
        origin = None
        importance = None

        for line in gpt_reply.splitlines():
            lower_line = line.lower()
            if "number of travelers" in lower_line:
                parts = line.split(":")
                if len(parts) > 1:
                    val = parts[1].strip()
                    num_travelers = val if val.isdigit() else None
            elif "length of stay" in lower_line or "travel dates" in lower_line:
                parts = line.split(":")
                if len(parts) > 1:
                    length_of_stay = parts[1].strip()
            elif "origin" in lower_line:
                parts = line.split(":")
                if len(parts) > 1:
                    origin = parts[1].strip()
            elif "important" in lower_line:
                parts = line.split(":")
                if len(parts) > 1:
                    importance = parts[1].strip()

        # Insert into Supabase if all fields are present
        if num_travelers and length_of_stay and origin and importance:
            try:
                insert_response = supabase.table("TripRequests").insert({
                    "num_travelers": int(num_travelers) if num_travelers.isdigit() else None,
                    "length_of_stay": length_of_stay,
                    "origin": origin,
                    "importance": importance
                }).execute()

                if insert_response.get("status_code") and insert_response["status_code"] >= 400:
                    print("Supabase insert error:", insert_response)
            except Exception as e:
                print("Error inserting into Supabase:", e)

    return {"assistant_reply": gpt_reply}

@app.get("/messages")
async def get_messages():
    """
    Debug endpoint showing the entire conversation history.
    """
    return {"conversation": conversation_messages}


@app.get("/test-openai")
async def test_openai():
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello!"}
            ],
            temperature=0.7
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        logger.error("Error testing OpenAI API: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

