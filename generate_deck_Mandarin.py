import genanki
import pandas as pd
from gtts import gTTS
import requests
import os
import random
import time
import shutil

# ================= CONFIGURATION =================
# 1. Google API Credentials (PASTE YOURS HERE)
GOOGLE_API_KEY = "AIzaSyCrwzc0nLMqGChnhYjG0iDOn0MFsENKASQ" 
SEARCH_ENGINE_ID = "77df10be511d24618"

# 2. Files
# Expected Columns: 
# Word | Pinyin | Definition | Examples (Hanzi) | Examples (Pinyin) | Examples (Literal Japanese) | Examples (Natural Japanese)
CSV_FILENAME = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTPQsKYyOczAJD92VrY1J5OGXK8DIjRIOcRc213NvqYmtzDBJAyPyVoiUAYI2LDlyKa9dWEeCa6aQjm/pub?gid=85788518&single=true&output=csv"
DECK_FILENAME = "My_Mandarin_Deck.apkg"
HISTORY_FILE = "history.log" 

# 3. Anki Deck Settings
DECK_NAME = "簡体中文::My Generated Mandarin Deck"
MODEL_ID = 1639582042
DECK_ID = 2059183510

# 4. Styling (CSS)
STYLE = """
.card {
 font-family: "Helvetica", "Arial", "Microsoft YaHei", sans-serif;
 text-align: center;
 font-size: 20px;
 background-color: white; 
 color: black;
}

/* Main Word Section */
.vocab { font-size: 48px; font-weight: bold; margin-bottom: 5px; color: #000; }
.vocab-pinyin { color: #DAA520; font-size: 24px; font-style: italic; margin-bottom: 10px; }
.definition { color: #4682B4; font-weight: bold; font-size: 20px; margin: 10px 0; }

/* Sentence List */
ul { display: inline-block; text-align: left; margin: 0; padding: 0 10px; list-style-type: none; width: 95%; }
li { margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 10px; }

/* Sentence Components */
.sent-hanzi { font-size: 22px; color: #222; display: block; font-weight: bold; }
.sent-pinyin { font-size: 16px; color: #DAA520; display: block; margin-top: 2px; } 

/* Literal Japanese (Structural) */
.sent-lit { 
    font-size: 14px; 
    color: #888; 
    display: block; 
    margin-top: 4px; 
    font-family: "Courier New", monospace; /* Monospace to emphasize structure */
}
.sent-lit::before { content: "【直訳】 "; opacity: 0.5; }

/* Natural Japanese (Translation) */
.sent-nat { 
    font-size: 16px; 
    color: #2E8B57; /* SeaGreen for Natural flow */
    display: block; 
    margin-top: 2px; 
    font-weight: bold;
}

img { max-height: 250px; margin-top: 10px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
"""

# ================= HELPER FUNCTIONS =================

def get_history():
    if not os.path.exists(HISTORY_FILE): return set()
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def append_to_history(word):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(word + "\n")

def get_image_url(query):
    if not GOOGLE_API_KEY or "YOUR_GOOGLE" in GOOGLE_API_KEY:
        print("   (API Key missing or default)")
        return None

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query + " meaning", 
        'cx': SEARCH_ENGINE_ID,
        'key': GOOGLE_API_KEY,
        'searchType': 'image',
        'num': 1,
        'safe': 'active'
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if 'items' in data:
            return data['items'][0]['link']
    except Exception as e:
        print(f"   (Network Error: {e})")
    return None

def download_image(url, filename):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            return True
    except: pass
    return False

def generate_audio(text, filename):
    try:
        tts = gTTS(text, lang='zh-cn')
        tts.save(filename)
        return True
    except: return False

# ================= MAIN SCRIPT =================

try:
    print("Fetching Google Sheet...")
    df = pd.read_csv(CSV_FILENAME)
    # Normalize columns (remove extra spaces)
    df.columns = [c.strip() for c in df.columns]
except Exception as e:
    print(f"Error loading CSV: {e}")
    exit()

history = get_history()

# Define Model
my_model = genanki.Model(
    MODEL_ID, 'Mandarin Romantic Model',
    fields=[
        {'name': 'Vocabulary'}, 
        {'name': 'Pinyin'}, 
        {'name': 'Definition'},
        {'name': 'Picture'}, 
        {'name': 'Sentences'}, # Combined HTML field
        {'name': 'Audio'},
    ],
    templates=[{
        'name': 'Card 1',
        'qfmt': '<div class="vocab">{{Vocabulary}}</div><br>{{Audio}}',
        'afmt': '''{{FrontSide}}
                   <hr id=answer>
                   <div class="vocab-pinyin">{{Pinyin}}</div>
                   <div class="definition">{{Definition}}</div>
                   <br>{{Picture}}
                   <br><br>
                   {{Sentences}}'''
    }],
    css=STYLE
)

my_deck = genanki.Deck(DECK_ID, DECK_NAME)
my_package = genanki.Package(my_deck)
media_files = []

print(f"Found {len(df)} words. Checking history...")

count_new = 0
for index, row in df.iterrows():
    word = str(row['Word']).strip()
    if word in history: continue 
    
    print(f"Processing: {word}")
    
    try:
        # --- 1. BASIC DATA ---
        vocab_pinyin = str(row['Pinyin']) if pd.notna(row['Pinyin']) else ""
        vocab_def = str(row['Definition']) if pd.notna(row['Definition']) else ""

        # --- 2. COMPLEX SENTENCES (4 Columns) ---
        # Get raw strings
        raw_hanzi = str(row['Examples (Hanzi)']) if pd.notna(row['Examples (Hanzi)']) else ""
        raw_pinyin = str(row['Examples (Pinyin)']) if pd.notna(row['Examples (Pinyin)']) else ""
        raw_lit = str(row['Examples (Literal Japanese)']) if pd.notna(row['Examples (Literal Japanese)']) else ""
        raw_nat = str(row['Examples (Natural Japanese)']) if pd.notna(row['Examples (Natural Japanese)']) else ""

        # Split all by semicolon
        # We replace Chinese semicolon '；' just in case, then split
        list_hanzi = [s.strip() for s in raw_hanzi.replace('；', ';').split(';') if s.strip()]
        list_pinyin = [s.strip() for s in raw_pinyin.replace('；', ';').split(';') if s.strip()]
        list_lit = [s.strip() for s in raw_lit.replace('；', ';').split(';') if s.strip()]
        list_nat = [s.strip() for s in raw_nat.replace('；', ';').split(';') if s.strip()]

        # Generate HTML List
        user_sentence = "<ul>"
        # We loop through the Hanzi list as the "master" list
        for i, sentence in enumerate(list_hanzi):
            # Safe indexing (if other columns have fewer items, use empty string)
            s_p = list_pinyin[i] if i < len(list_pinyin) else ""
            s_l = list_lit[i] if i < len(list_lit) else ""
            s_n = list_nat[i] if i < len(list_nat) else ""

            user_sentence += f"<li>"
            user_sentence += f"<span class='sent-hanzi'>{sentence}</span>"
            if s_p: user_sentence += f"<span class='sent-pinyin'>{s_p}</span>"
            if s_l: user_sentence += f"<span class='sent-lit'>{s_l}</span>"
            if s_n: user_sentence += f"<span class='sent-nat'>{s_n}</span>"
            user_sentence += "</li>"
        user_sentence += "</ul>"

        # --- 3. MEDIA ---
        image_html = ""
        img_url = get_image_url(word)
        if img_url:
            img_filename = f"img_{word}_{random.randint(100,999)}.jpg"
            if download_image(img_url, img_filename):
                media_files.append(img_filename)
                image_html = f'<img src="{img_filename}">'
            else: print("   (Warning: Image download failed.)")
        else: print("   (Warning: API returned no image.)")

        # --- 4. AUDIO ---
        audio_filename = f"audio_{word}_{random.randint(100,999)}.mp3"
        audio_html = ""
        if generate_audio(word, audio_filename):
            media_files.append(audio_filename)
            audio_html = f"[sound:{audio_filename}]"

        # --- 5. ADD NOTE ---
        note = genanki.Note(
            model=my_model,
            fields=[word, vocab_pinyin, vocab_def, image_html, user_sentence, audio_html]
        )
        my_deck.add_note(note)
        append_to_history(word)
        count_new += 1

    except Exception as e:
        print(f"!! CRITICAL ERROR processing '{word}': {e}")
    
    time.sleep(0.5)

if count_new > 0:
    my_package.media_files = media_files
    my_package.write_to_file(DECK_FILENAME)
    for f in media_files:
        try: os.remove(f)
        except: pass
    print(f"Done! Created {count_new} cards.")
else:
    print("No new cards found.")