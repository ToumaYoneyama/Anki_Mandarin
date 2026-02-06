# 🇨🇳 Anki Mandarin Sync

A powerful Python automation tool that syncs Mandarin vocabulary from **Google Sheets** directly to **Anki**.

Unlike standard CSV importers, this tool features a **Smart Sync** system: it adds new cards, updates existing definitions/sentences for old cards, and preserves your study history without creating duplicates.

## ✨ Key Features

* **🔄 Smart "Upsert" Logic**:
    * **New Words:** Automatically generates audio (Google TTS), formats the card, and adds it to Anki.
    * **Existing Words:** Detects them in your deck and updates the text fields (Definition, Pinyin, Sentences) *without* overwriting your learning progress or re-generating audio (for speed).
* **🎯 Interactive Filtering**: Choose exactly what to sync.
    * Press `Enter` to sync the whole sheet.
    * Type row numbers (e.g., `5, 8, 12-15`) to sync specific targets.
* **🔊 Auto-Audio**: Automatically generates `zh-cn` audio for every new vocabulary word using Google Text-to-Speech (gTTS).
* **🛡️ Non-Destructive**: Rows deleted from the Google Sheet are *ignored* (not deleted) in Anki, preserving your study data safety.
* **🎨 Embedded Styling**: Automatically applies custom CSS for clean, readable cards with separate fields for Pinyin, Definitions, and Example Sentences.

## 🛠️ Prerequisites

1. **Anki Desktop App** (Running in the background).
2. **AnkiConnect Add-on**:
    * Open Anki → Tools → Add-ons → Get Add-ons.
    * Code: `2055492159`.
    * *Restart Anki after installing.*
3. **Python 3.x**.

## 📦 Installation

1. Clone this repository:
    ```bash
    git clone [https://github.com/ToumaYoneyama/Anki_Mandarin.git](https://github.com/ToumaYoneyama/Anki_Mandarin.git)
    cd Anki_Mandarin
    ```

2. Install required Python libraries:
    ```bash
    pip install pandas gtts requests
    ```

## ⚙️ Configuration

Open `update_anki.py` and ensure the settings match your Anki setup:

```python
# The URL to your published Google Sheet CSV
CSV_FILENAME = "YOUR_GOOGLE_SHEET_CSV_LINK"

# Must match your Anki Deck/Note Type exactly
ANKI_DECK_NAME = "簡体中文::My Generated Mandarin Deck"
ANKI_MODEL_NAME = "Mandarin Romantic Model"

### 📊 Google Sheet Format
The script expects a Google Sheet with the following headers (order doesn't matter, names must be close):
* `Word` / `Vocabulary`
* `Pinyin`
* `Definition`
* `Example Hanzi`
* `Example Pinyin`
* `Literal Meaning`
* `Natural Translation`

## 🚀 Usage

1. **Open Anki** (The script needs to talk to the app).
2. Run the script:
    ```bash
    python update_anki.py
    ```
3. **Choose your sync mode** at the prompt:
    * **Press Enter:** Scans and syncs the entire spreadsheet.
    * **Type Numbers:** Sync specific rows (e.g., `20` or `10-15` or `5, 8, 10`).

## 📝 License
[MIT](https://choosealicense.com/licenses/mit/)
