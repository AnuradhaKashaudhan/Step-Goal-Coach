"""
agent.py
--------
The "agentic" part of the project. We hand the Gemini model three Python
functions as tools:

    log_steps, get_progress, get_weekly_summary

Gemini decides on its own, per user message, whether it needs to call one
(or several) of these tools, calls them with the right arguments, reads the
results, and then writes a specific, encouraging nudge back to the user
(e.g. "Nice, that's 3,200 steps logged — only 4,800 to go today!").

Uses the current `google-genai` SDK (`pip install google-genai`). Passing
raw Python functions in `tools=[...]` turns on automatic function calling:
the SDK handles the call -> execute -> feed-result-back loop for us.
"""

import os
from google import genai
from google.genai import types

from storage import log_steps, get_progress, get_weekly_summary

SYSTEM_INSTRUCTION = """
You are Stride, an upbeat, encouraging daily step-goal coach.

You have three tools:
- log_steps(count): call this whenever the user tells you they walked,
  ran, or logged some number of steps.
- get_progress(): call this to check today's steps, goal, and remaining
  steps. Call it after logging steps, or whenever the user asks how
  they're doing today.
- get_weekly_summary(): call this to check the rolling 7-day total and
  whether a weekly milestone (10k / 25k / 50k / 75k / 100k) was just
  reached, or when the user asks about their week.

Rules for your replies:
1. Always ground your reply in real numbers from the tools — never guess.
2. When steps are logged, always state the exact number of steps
   remaining to hit today's goal (or congratulate them if the goal is
   met).
3. If get_weekly_summary() reports a newly_reached_milestone, celebrate
   it specifically by name (e.g. "You just crossed 25,000 steps this
   week!").
4. Keep replies short — 1 to 3 sentences, warm, specific, never generic
   filler like "great job!" without a number attached to it.
5. If the user's message isn't about steps at all, gently steer them
   back to their step goal.
"""

MODEL_NAME = "gemini-3.6-flash"

_client = None
_chat = None


def _get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Please set the GEMINI_API_KEY environment variable or put it in a .env file.")
    _client = genai.Client(api_key=api_key)
    return _client


def _get_chat():
    """One chat session per server process — fine for this single-user demo.
    (Swap for a per-user session dict if you add real auth/multi-user
    support.)"""
    global _chat
    if _chat is None:
        client = _get_client()
        _chat = client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[log_steps, get_progress, get_weekly_summary],
            ),
        )
    return _chat


def run_agent(user_message: str) -> str:
    """Sends the user's message to the agent and returns its text reply.
    The SDK transparently runs any tool calls Gemini decides to make along
    the way (automatic function calling)."""
    chat = _get_chat()
    response = chat.send_message(user_message)
    return response.text
