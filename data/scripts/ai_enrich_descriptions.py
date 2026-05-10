"""
Uses the Google Gemini API to validate and improve descriptions in
places_enriched.csv.

For each place, Gemini checks whether the existing description is accurate
and relevant to the place name/category, then rewrites it if needed.

Steps:
  1. Load places_enriched.csv (or resume from places_final.csv if it exists)
  2. Process each place with gemini-2.0-flash-lite (cheap + fast)
  3. Save progress every 50 rows so the script is safe to interrupt/resume
  4. Final output → cleaned/places_final.csv

Rate limiting: free tier allows 30 requests/min; script sleeps 2 s between
calls (~30/min). Increase DELAY if you hit quota errors.

Usage:
    export GEMINI_API_KEY="AIza..."
    python ai_enrich_descriptions.py
"""

import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../py_packages"))

from google import genai
from google.genai import types
from google.genai import errors as genai_errors
import pandas as pd

BASE = os.path.dirname(__file__)
CLEANED = os.path.join(BASE, "../cleaned")
INPUT_CSV = os.path.join(CLEANED, "places_enriched.csv")
OUTPUT_CSV = os.path.join(CLEANED, "places_final.csv")

MODEL = "gemini-3.1-flash-lite-preview"
DELAY = 6.0    # seconds between requests (~10 RPM, well under 15 RPM cap)
SAVE_EVERY = 50
MAX_RETRIES = 3


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a cultural heritage writer specialising in Melbourne, Australia.
Your task is to validate and, where necessary, improve descriptions of public
places — memorials, sculptures, artworks, fountains, parks, galleries,
libraries, theatres, cemeteries, bridges, and other landmarks in the City
of Melbourne.

VALIDATION RULES
A description is VALID if ALL of the following hold:
  • It specifically describes the named place (not a different artwork or city).
  • It contains at least two informative sentences about the place itself.
  • It does not consist only of generic category labels
    (e.g. "Pedestrian and cyclist bridge").
  • It does not describe something obviously unrelated (a sports team, a
    person's biography unrelated to the artwork, a disambiguation page, etc.).
  • It does not contain raw metadata labels such as "Location:", "Medium:".

If valid, respond with exactly one word:
    VALID

REWRITING RULES
If invalid, write a new description of 2–4 sentences that:
  • Opens with the place name and what kind of place it is.
  • Mentions its location in Melbourne (suburb or street if known).
  • Includes the artist and/or year if provided in the metadata.
  • Uses plain, warm language suitable for older adult visitors.
  • Does NOT fabricate specific facts not given in the metadata.

Respond with exactly this format (no extra text):
    REWRITE: <your new description here>
"""


# ── Helpers ────────────────────────────────────────────────────────────────────

def build_user_message(row) -> str:
    def val(col):
        v = str(row.get(col, "")).strip()
        return "" if v.lower() in ("nan", "none", "") else v

    return "\n".join([
        f"Name: {val('name')}",
        f"Category: {val('category')}",
        f"Sub-category: {val('sub_category')}",
        f"Address: {val('address')}",
        f"Artist: {val('artist')}",
        f"Year: {val('year')}",
        f"Current description: {val('description')}",
    ])


def parse_response(text: str) -> tuple[bool, str]:
    text = text.strip()
    if text.upper().startswith("VALID"):
        return True, ""
    if text.upper().startswith("REWRITE:"):
        return False, text[len("REWRITE:"):].strip()
    return True, ""  # unexpected format → keep original


# ── Setup ──────────────────────────────────────────────────────────────────────

client = genai.Client(api_key="AIzaSyAiRed7dZ-IAYu39oF_Y4EleZjuqjGMXbA")


# ── Load data (resume from OUTPUT_CSV if it exists) ───────────────────────────

if os.path.exists(OUTPUT_CSV):
    df = pd.read_csv(OUTPUT_CSV, encoding="utf-8")
    print(f"Resuming from {OUTPUT_CSV} ({len(df)} places).")
else:
    df = pd.read_csv(INPUT_CSV, encoding="utf-8")
    df["ai_validated"] = False
    print(f"Loaded {len(df)} places from {INPUT_CSV}.")

if "ai_validated" not in df.columns:
    df["ai_validated"] = False

pending = df[~df["ai_validated"]].index.tolist()
print(f"Pending: {len(pending)}  |  Already done: {(df['ai_validated']).sum()}\n")


# ── Main loop ──────────────────────────────────────────────────────────────────

rewritten = kept = errors = 0

for i, idx in enumerate(pending):
    row = df.loc[idx]
    user_msg = build_user_message(row)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=300,
                    temperature=0.2,
                ),
            )
            text = response.text or ""
            is_valid, new_desc = parse_response(text)

            if is_valid:
                kept += 1
            else:
                df.at[idx, "description"] = new_desc
                rewritten += 1

            df.at[idx, "ai_validated"] = True
            break  # success

        except Exception as e:
            msg = str(e)
            # Parse retry delay from 429 response if available
            m = re.search(r"retryDelay.*?(\d+)s", msg)
            if "429" in msg or "503" in msg:
                wait = int(m.group(1)) + 2 if m else 30
                if attempt < MAX_RETRIES - 1:
                    print(f"  {'429' if '429' in msg else '503'} — waiting {wait}s before retry (attempt {attempt+1}/{MAX_RETRIES})...")
                    time.sleep(wait)
                else:
                    print(f"  ERROR [{row['name']}]: {e}")
                    errors += 1
                    break
            else:
                print(f"  ERROR [{row['name']}]: {e}")
                errors += 1
                break

    # Progress update every 10 rows
    if (i + 1) % 10 == 0:
        print(f"  [{i + 1}/{len(pending)}] kept={kept} rewritten={rewritten} errors={errors}")

    # Save checkpoint
    if (i + 1) % SAVE_EVERY == 0:
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
        print(f"  Checkpoint saved → {OUTPUT_CSV}")

    time.sleep(DELAY)


# ── Save final output ──────────────────────────────────────────────────────────

df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

avg_len = df["description"].fillna("").str.len().mean()
print(f"\nDone.")
print(f"  Kept original: {kept}  |  Rewritten: {rewritten}  |  Errors: {errors}")
print(f"  Avg description length: {avg_len:.0f} chars")
print(f"  Saved → {OUTPUT_CSV}")
print("\nCategory breakdown:")
for cat in df["category"].unique():
    sub = df[df["category"] == cat]
    avg = sub["description"].fillna("").str.len().mean()
    print(f"  {cat}: {len(sub)} places, avg desc {avg:.0f} chars")
