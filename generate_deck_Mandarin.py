import genanki
import pandas as pd
from gtts import gTTS
import os
import random
import time

# ================= CONFIGURATION =================
# 1. Files
# Expected Columns: 
# Word | Pinyin | Definition | Examples (Hanzi) | Examples (Pinyin) | Examples (Literal Japanese) | Examples (Natural Japanese)
CSV_FILENAME = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTPQsKYyOczAJD92VrY1J5OGXK8DIjRIOcRc213NvqYmtzDBJAyPyVoiUAYI2LDlyKa9dWEeCa6aQjm/pub?gid=85788518&single=true&output=csv"
DECK_FILENAME = "My_Mandarin_Deck.apkg"
HISTORY_FILE = "history.log" 

# 2. Anki Deck Settings
DECK_NAME = "簡体中文::My Generated Mandarin Deck"
MODEL_ID = 1639582042
DECK_ID = 2059183510

# 3. Styling (CSS)
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

/* Definition Section */
.definition { 
    color: #4682B4; 
    font-weight: bold; 
    font-size: 20px; 
    margin: 15px 0; 
    line-height: 1.4; /* Better spacing for multi-line defs */
}

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
    font-family: "Courier New", monospace; 
}
.sent-lit::before { content: "【直訳】 "; opacity: 0.5; }

/* Natural Japanese (Translation) */
.sent-nat { 
    font-size: 16px; 
    color: #2E8B57; 
    display: block; 
    margin-top: 2px; 
    font-weight: bold;
}
"""

# ================= HELPER FUNCTIONS =================

def get_history():
    if not os.path.exists(HISTORY_FILE): return set()
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def append_to_history(word):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(word + "\n")

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
    # 1. Clean Column Names (Strip spaces)
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
        {'name': 'Sentences'}, 
        {'name': 'Audio'},
    ],
    templates=[{
        'name': 'Card 1',
        # FRONT: Vocabulary only
        'qfmt': '<div class="vocab">{{Vocabulary}}</div>',
        
        # BACK: Audio, Pinyin, Definition, Sentences
        'afmt': '''{{FrontSide}}
                   <hr id=answer>
                   {{Audio}}<br>
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
    # --- SMART COLUMN FINDER ---
    col_word   = next((c for c in df.columns if 'Word' in c or 'Vocabulary' in c), None)
    col_pinyin = next((c for c in df.columns if 'Pinyin' in c and 'Example' not in c), None)
    col_def    = next((c for c in df.columns if ('Definition' in c or 'Meaning' in c) and 'Sentence' not in c), None)
    
    if not col_word: 
        print("!! Error: Could not find a 'Word' column.")
        break
        
    word = str(row[col_word]).strip()
    if word in history: continue 
    
    print(f"Processing: {word}")
    
    try:
        # --- 1. BASIC DATA ---
        vocab_pinyin = str(row[col_pinyin]) if col_pinyin and pd.notna(row[col_pinyin]) else ""
        
        # DEFINITION FIX: Replace semicolons with HTML line breaks
        raw_def = str(row[col_def]) if col_def and pd.notna(row[col_def]) else ""
        vocab_def = raw_def.replace('；', '<br>').replace(';', '<br>')

        # --- 2. COMPLEX SENTENCES (4 Columns) ---
        c_hanzi = next((c for c in df.columns if 'Example' in c and 'Hanzi' in c), None)
        c_pinyin = next((c for c in df.columns if 'Example' in c and 'Pinyin' in c), None)
        c_lit = next((c for c in df.columns if 'Literal' in c), None)
        c_nat = next((c for c in df.columns if 'Natural' in c), None)

        raw_hanzi = str(row[c_hanzi]) if c_hanzi and pd.notna(row[c_hanzi]) else ""
        raw_pinyin = str(row[c_pinyin]) if c_pinyin and pd.notna(row[c_pinyin]) else ""
        raw_lit = str(row[c_lit]) if c_lit and pd.notna(row[c_lit]) else ""
        raw_nat = str(row[c_nat]) if c_nat and pd.notna(row[c_nat]) else ""

        # Split all by semicolon
        list_hanzi = [s.strip() for s in raw_hanzi.replace('；', ';').split(';') if s.strip()]
        list_pinyin = [s.strip() for s in raw_pinyin.replace('；', ';').split(';') if s.strip()]
        list_lit = [s.strip() for s in raw_lit.replace('；', ';').split(';') if s.strip()]
        list_nat = [s.strip() for s in raw_nat.replace('；', ';').split(';') if s.strip()]

        # Generate HTML List
        user_sentence = "<ul>"
        for i, sentence in enumerate(list_hanzi):
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

        # --- 3. MEDIA (Disabled) ---
        image_html = "" 

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
    
if count_new > 0:
    my_package.media_files = media_files
    my_package.write_to_file(DECK_FILENAME)
    for f in media_files:
        try: os.remove(f)
        except: pass
    print(f"Done! Created {count_new} cards.")
else:
    print("No new cards found.")