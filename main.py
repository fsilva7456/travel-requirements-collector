import os
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
from supabase import create_client, Client

app = FastAPI()

# ---------------------------------------------------------
# Environment Variables (set in Railway)
# ---------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")   # e.g. "https://xyzcompany.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")   # anon or service role key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
    raise Exception("Missing one or more required environment variables.")

openai.api_key = OPENAI_API_KEY

# Create the Supabase client (built-in REST interface)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------
# Simple In-Memory Conversation
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
    Once GPT has all required details, we insert them into Supabase.
    """
    # Add user message to conversation history
    conversation_messages.append({"role": "user", "content": user_msg.message})

    # Call GPT-4 (or another model if needed)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or e.g. "gpt-3.5-turbo"
            messages=conversation_messages,
            temperature=0.7
        )
        gpt_reply = response["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Add GPT reply to conversation
    conversation_messages.append({"role": "assistant", "content": gpt_reply})

    # Naive check if GPT included a final "Summary of your trip details"
    if "Summary of your trip details" in gpt_reply:
        # Attempt to parse the essential data
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

        # If we have all fields, insert into Supabase
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
                print("Error inserting to Supabase:", e)

    return {"assistant_reply": gpt_reply}

@app.get("/messages")
async def get_messages():
    """
    Debug endpoint showing entire conversation history.
    """
    return {"conversation": conversation_messages}

@app.get("/")
def health_check():
    return {"status": "ok"}
