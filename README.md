# Snap & Understand 📸🔍

An intelligent, grounded multimodal assistant that bridges visual recognition and enterprise data intelligence. Snap a photo of an item (product label, medicine box, receipt/invoice, document), classify and extract key attributes using **Gemma 4** (via Google AI Studio), ground the details against a verified **Snowflake dataset** (with real-time web scraping fallback), and receive an accurate explanation in the user's preferred language.

Built with **Snowflake Cortex Code (CoCo)**, **Snowflake Marketplace / Sample Data**, and **Google AI Studio Gemma**.

---

## 🎯 Architecture & Workflow

1. **Snap & Ingest:** Capture or upload an image via the Streamlit UI.
2. **Visual Classification & Extraction (Gemma 4):** Classify the image into one of 3 structured categories and extract entity markers (name, SKU/UPC, brand, dosage, total, etc.).
3. **Snowflake Grounding Lookup:** Query the target Snowflake dataset to retrieve authoritative data.
4. **Web Fallback Scraper:** If the entity is not found in the Snowflake dataset, a web scraper tool fetches current web context to ground the result.
5. **Multilingual Explanation (Gemma):** Translate and explain the findings clearly in the selected language (e.g., English, Hausa, French).
6. **Snap Audit Logging & Dashboard:** Every snap is logged into a Snowflake audit table (`category`, `language`, `timestamp`) with an interactive analytics dashboard.

---

## 📊 Snowflake Dataset Used

- **Dataset Name:** *(To be determined during dataset discovery)*
- **Source:** Snowflake Sample Data / Marketplace Free Listing
- **Access Details:** Free listing / sample data accessible via standard Snowflake accounts.

---

## 🤖 Cortex Code (CoCo) Usage

Snowflake Cortex Code CLI (`cortex`) was used to explore datasets, inspect schemas, author lookup queries, and generate the snap-logging dashboard views.
Detailed prompts and generated queries are logged in [`docs/coco-log.md`](docs/coco-log.md).

---

## 🛠️ Setup Instructions (Windows CMD)

### Prerequisites
- Windows OS (using Command Prompt `cmd.exe`)
- Python 3.12+ installed
- Snowflake Account (with browser login enabled)
- Google AI Studio API Key (`GEMINI_API_KEY`)

### 1. Clone & Configure
```cmd
git clone <repo_url>
cd Snap_and_send
copy .env.example .env
```
Edit `.env` and fill in your `GEMINI_API_KEY`, `SNOWFLAKE_ACCOUNT`, and `SNOWFLAKE_USER`.

### 2. Set Up Virtual Environment & Dependencies
```cmd
py -3.12 -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 3. Run Multilingual Language Quality Test
```cmd
python -m tests.test_language
```
Outputs are recorded in [`docs/language-test.md`](docs/language-test.md).

### 4. Run the Streamlit Application
```cmd
streamlit run app.py
```

---

## 🌐 Supported Languages & Verification Status

- **English:** Verified
- **Hausa:** Verified (documented in `docs/language-test.md`)
- **French:** Verified (documented in `docs/language-test.md`)

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
