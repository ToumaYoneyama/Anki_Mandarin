import pandas as pd
from gtts import gTTS
import os
import random
import time
import json
import requests
import base64

# ================= CONFIGURATION =================
CSV_FILENAME = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTPQsKYyOczAJD92VrY1J5OGXK8DIjRIOcRc213NvqYmtzDBJAyPyVoiUAYI2LDlyKa9dWEeCa6aQjm/pub?gid=85788518&single=true&output=csv"

# ANKI SETTINGS
ANKI_DECK_NAME = "簡体中文::My Generated Mandarin Deck"
ANKI_MODEL_NAME = "Mandarin Romantic Model" 

# CSS STYLING
STYLE = """
.card { font-family: "Helvetica", "Arial", "Microsoft YaHei", sans-serif; text-align: center; font-size: 20px; background-color: white; color: black; }
.vocab { font-size: 48px; font-weight: bold; margin-bottom: 5px; color: #000; }
.vocab-pinyin { color: #DAA520; font-size: 24px; font-style: italic; margin-bottom: 10px; }
.definition { color: #4682B4; font-weight: bold; font-size: 20px; margin: 15px 0; line-height: 1.4; }
ul { display: inline-block; text-align: left; margin: 0; padding: 0 10px; list-style-type: none; width: 95%; }
li { margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
.sent-hanzi { font-size: 22px; color: #222; display: block; font-weight: bold; }
.sent-pinyin { font-size: 16px; color: #DAA520; display: block; margin-top: 2px; } 
.sent-lit { font-size: 14px; color: #888; display: block; margin-top: 4px; font-family: "Courier New", monospace; }
.sent-lit::before { content: "【直訳】 "; opacity: 0.5; }
.sent-nat { font-size: 16px; color: #2E8B57; display: block; margin-top: 2px; font-weight: bold; }
"""

# ================= HELPER FUNCTIONS =================

def invoke(action, **params):
    requestJson = json.dumps(request(action, **params))
    try:
        response = requests.post('http://localhost:8765', data=requestJson).json()
    except requests.exceptions.ConnectionError:
        raise Exception("Unable to connect to Anki. Is Anki running and AnkiConnect installed?")
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']

def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}

def process_audio(text, filename):
    try:
        tts = gTTS(text, lang='zh-cn')
        tts.save(filename)
        with open(filename, "rb") as audio_file:
            encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')
        invoke('storeMediaFile', filename=filename, data=encoded_string)
        os.remove(filename)
        return True
    except Exception as e:
        print(f"Audio Error: {e}")
        return False

def update_css(model_name, css_code):
    try:
        invoke('updateModelStyling', model={"name": model_name, "css": css_code})
    except Exception:
        pass

# ================= MAIN SCRIPT =================

try:
    print("Fetching Google Sheet...")
    df = pd.read_csv(CSV_FILENAME)
    df.columns = [c.strip() for c in df.columns]
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit()

# --- 1. SETUP ANKI ---
try:
    if ANKI_DECK_NAME not in invoke('deckNames'):
        invoke('createDeck', deck=ANKI_DECK_NAME)
    if ANKI_MODEL_NAME not in invoke('modelNames'):
        print(f"!! FATAL: Model '{ANKI_MODEL_NAME}' missing.")
        exit()
    update_css(ANKI_MODEL_NAME, STYLE)
except Exception as e:
    print(f"Setup Error: {e}")
    exit()

# --- 2. ROW NUMBER FILTER ---
print(f"\nLoaded {len(df)} rows (Sheet Rows 2 to {len(df)+1}).")
print("-" * 50)
print("FILTER OPTIONS:")
print("1. Press ENTER to process ALL rows.")
print("2. Type ROW NUMBERS (e.g., '5' or '2, 5, 8' or '10-15')")
print("-" * 50)

user_input = input("Rows > ").strip()

if user_input:
    selected_indices = []
    # Split by comma first
    parts = user_input.replace('，', ',').split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Handle ranges like "10-15"
            try:
                start, end = map(int, part.split('-'))
                # range is inclusive for user convenience
                # Google Row X -> DataFrame Index X-2
                selected_indices.extend(range(start - 2, end - 2 + 1))
            except ValueError:
                print(f"!! Invalid range format: {part}")
        else:
            # Handle single numbers
            try:
                row_num = int(part)
                selected_indices.append(row_num - 2)
            except ValueError:
                print(f"!! Invalid number: {part}")

    # Remove duplicates and invalid indices
    valid_indices = sorted(list(set([i for i in selected_indices if 0 <= i < len(df)])))
    
    if not valid_indices:
        print("!! No valid rows selected (check your numbers).")
        exit()
        
    df = df.iloc[valid_indices]
    print(f"--> Processing {len(df)} specific rows...")

else:
    print("--> Processing ALL rows...")


# --- 3. MAIN LOOP ---
count_new = 0
count_updated = 0

for index, row in df.iterrows():
    # Identify 'Word' column dynamically
    col_word = next((c for c in df.columns if 'Word' in c or 'Vocabulary' in c), None)
    if not col_word:
        print("!! Error: Could not find 'Word' column.")
        break
        
    word = str(row[col_word]).strip()
    print(f"Processing: {word} ... ", end="")
    
    try:
        # Find other columns
        col_pinyin = next((c for c in df.columns if 'Pinyin' in c and 'Example' not in c), None)
        col_def    = next((c for c in df.columns if ('Definition' in c or 'Meaning' in c) and 'Sentence' not in c), None)

        vocab_pinyin = str(row[col_pinyin]) if col_pinyin and pd.notna(row[col_pinyin]) else ""
        raw_def = str(row[col_def]) if col_def and pd.notna(row[col_def]) else ""
        vocab_def = raw_def.replace('；', '<br>').replace(';', '<br>')

        # Sentences
        c_hanzi = next((c for c in df.columns if 'Example' in c and 'Hanzi' in c), None)
        c_pinyin = next((c for c in df.columns if 'Example' in c and 'Pinyin' in c), None)
        c_lit = next((c for c in df.columns if 'Literal' in c), None)
        c_nat = next((c for c in df.columns if 'Natural' in c), None)

        raw_hanzi = str(row[c_hanzi]) if c_hanzi and pd.notna(row[c_hanzi]) else ""
        raw_pinyin = str(row[c_pinyin]) if c_pinyin and pd.notna(row[c_pinyin]) else ""
        raw_lit = str(row[c_lit]) if c_lit and pd.notna(row[c_lit]) else ""
        raw_nat = str(row[c_nat]) if c_nat and pd.notna(row[c_nat]) else ""

        list_hanzi = [s.strip() for s in raw_hanzi.replace('；', ';').split(';') if s.strip()]
        list_pinyin = [s.strip() for s in raw_pinyin.replace('；', ';').split(';') if s.strip()]
        list_lit = [s.strip() for s in raw_lit.replace('；', ';').split(';') if s.strip()]
        list_nat = [s.strip() for s in raw_nat.replace('；', ';').split(';') if s.strip()]

        user_sentence = "<ul>"
        for i, sentence in enumerate(list_hanzi):
            s_p = list_pinyin[i] if i < len(list_pinyin) else ""
            s_l = list_lit[i] if i < len(list_lit) else ""
            s_n = list_nat[i] if i < len(list_nat) else ""
            user_sentence += f"<li><span class='sent-hanzi'>{sentence}</span>"
            if s_p: user_sentence += f"<span class='sent-pinyin'>{s_p}</span>"
            if s_l: user_sentence += f"<span class='sent-lit'>{s_l}</span>"
            if s_n: user_sentence += f"<span class='sent-nat'>{s_n}</span>"
            user_sentence += "</li>"
        user_sentence += "</ul>"

        # Check Anki
        query = f'deck:"{ANKI_DECK_NAME}" "Vocabulary:{word}"'
        existing_notes = invoke('findNotes', query=query)

        if existing_notes:
            for note_id in existing_notes:
                invoke('updateNoteFields', note={
                    "id": note_id,
                    "fields": {
                        "Pinyin": vocab_pinyin,
                        "Definition": vocab_def,
                        "Sentences": user_sentence
                    }
                })
            count_updated += 1
            print("UPDATED.")
        else:
            audio_filename = f"audio_{word}_{random.randint(100,999)}.mp3"
            audio_field_content = ""
            if process_audio(word, audio_filename):
                audio_field_content = f"[sound:{audio_filename}]"

            note_data = {
                "deckName": ANKI_DECK_NAME,
                "modelName": ANKI_MODEL_NAME,
                "fields": {
                    "Vocabulary": word,
                    "Pinyin": vocab_pinyin,
                    "Definition": vocab_def,
                    "Picture": "", 
                    "Sentences": user_sentence,
                    "Audio": audio_field_content
                },
                "tags": ["auto-generated"]
            }
            invoke('addNote', note=note_data)
            count_new += 1
            print("ADDED.")

    except Exception as e:
        print(f"\n!! CRITICAL ERROR processing '{word}': {e}")
    
print(f"\nDone! Added {count_new}, Updated {count_updated}.")