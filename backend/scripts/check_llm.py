"""
scripts/check_llm.py
--------------------
Quick health check for the Gemini connection: which key is used, which model,
and whether one tiny request works. It shows the raw error if it does not.

Usage (from the backend/ folder):
    python -m scripts.check_llm
"""

import os
import time

from dotenv import load_dotenv

# load_dotenv() never overwrites a variable that is already set in the terminal,
# so check where the key comes from BEFORE loading the .env file.
already_in_environment = bool(os.environ.get("GEMINI_API_KEY"))
load_dotenv()

key = os.environ.get("GEMINI_API_KEY", "")
if not key:
    raise SystemExit("No GEMINI_API_KEY found. Put it in backend/.env as:  GEMINI_API_KEY=your-key")

source = (
    "the terminal / Windows environment variable (this OVERRIDES the .env file!)"
    if already_in_environment
    else "the .env file"
)
print(f"Key in use : {key[:4]}...{key[-4:]}  (from {source})")

from google.genai import types  # noqa: E402

from rag import answerer  # noqa: E402

print(f"Model      : {answerer.MODEL}")
print("Sending one tiny request...")

started = time.perf_counter()
try:
    response = answerer._get_client().models.generate_content(
        model=answerer.MODEL,
        contents="Reply with the single word: ready",
        config=types.GenerateContentConfig(max_output_tokens=200),
    )
    took = time.perf_counter() - started
    print(f"OK in {took:.1f}s -> {(response.text or '(empty reply)').strip()!r}")
except Exception as error:
    took = time.perf_counter() - started
    print(f"FAILED after {took:.1f}s")
    print(f"{type(error).__name__}: {error}")