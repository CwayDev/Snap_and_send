# Snap & Understand 📸🔍

An intelligent, grounded multimodal assistant that bridges visual recognition and enterprise data intelligence. Snap a photo of an item (product label, medicine box, receipt/invoice, or supplier document), classify and extract key attributes using **Gemma 4** (via Google AI Studio), ground the details against a verified **Snowflake dataset** (with real-time web scraping fallback), and receive an accurate explanation in the user's preferred language (**English, Hausa, French**).

Built with **Snowflake Cortex Code (CoCo)**, **Snowflake Sample Data**, and **Google AI Studio Gemma 4**.

---

## 🎯 Architecture & Workflow

1. **Snap & Ingest:** Capture or upload an image via the Streamlit UI (camera or file upload).
2. **Visual Classification & Extraction (Gemma 4):** Open-weight `gemma-4-26b-a4b-it` classifies the photo into one of 3 categories:
   - `Product Label` (manufactured goods, retail items, pharmaceuticals)
   - `Receipt / Invoice` (sales receipts, order slips, bills)
   - `Supplier / Vendor Document` (vendor details, business contacts)
3. **Snowflake Grounding Lookup:** Queries authoritative records in `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`.
4. **Web Fallback Scraper:** If the entity is not found in the Snowflake enterprise catalog (e.g. consumer medicine box), the built-in web scraper tool (`src/web_scraper.py`) scrapes real-time context and medical/product specifications.
5. **Multilingual Grounded Explanation (Gemma 4):** Translates and explains the verified details naturally and accurately in the chosen language (English, Hausa, French).
6. **Snap Audit Logging & Dashboard:** Every snap is logged into a dedicated Snowflake table (`SNAP_DB.APP.SNAP_LOGS`: `CATEGORY`, `LANGUAGE`, `GROUNDING_SOURCE`, `ITEM_IDENTIFIED`, `TIMESTAMP`) without storing image binaries, and visualized on an interactive Streamlit dashboard.

---

## 📊 Exact Snowflake Dataset Used

- **Database:** `SNOWFLAKE_SAMPLE_DATA`
- **Schema:** `TPCH_SF1`
- **Tables Queried:**
  - `PART` (200,000 rows): Part name, brand, manufacturer, container, retail price.
  - `ORDERS` (1,500,000 rows) & `LINEITEM` (6,000,000 rows): Order key, order status, total price, clerk, itemized quantities and prices.
  - `SUPPLIER` (10,000 rows): Supplier name, address, phone number, account balance.
- **Audit Table Created:** `SNAP_DB.APP.SNAP_LOGS`

---

## 🤖 Snowflake Cortex Code (CoCo) Usage

Snowflake Cortex Code CLI (`cortex`) and Snowflake CLI (`snow`) were used to:
1. Explore and catalog datasets in `SNOWFLAKE_SAMPLE_DATA`.
2. Generate optimized SQL lookup queries with fuzzy/case-insensitive matching.
3. Design and build the `SNAP_DB.APP.SNAP_LOGS` audit pipeline and aggregation queries for the dashboard.

All prompts and generated SQL queries are logged in [`docs/coco-log.md`](docs/coco-log.md).

---

## 🌐 Verified Multilingual Support

Gemma 4 was tested and benchmarked across all target languages. Sample outputs for native speaker review are recorded in [`docs/language-test.md`](docs/language-test.md):
- **English:** Verified
- **Hausa:** Verified (e.g., *Bayanan Samfur, Sinadarin Magani, Yadda za a sha, Gargadi*)
- **French:** Verified (e.g., *Article, Principe actif, Indications, Posologie, Avertissement*)

---

## 🛠️ Setup Instructions (Windows CMD)

### Prerequisites
- Windows OS (using Command Prompt `cmd.exe`)
- Python 3.12 installed
- Google AI Studio API Key (`GEMINI_API_KEY`)
- Snowflake Account

### 1. Clone & Configure
```cmd
git clone https://github.com/CwayDev/Snap_and_send.git
cd Snap_and_send
copy .env.example .env
```
Edit `.env` and fill in:
- `GEMINI_API_KEY=your_key_here`
- `SNOWFLAKE_ACCOUNT=your_account`
- `SNOWFLAKE_USER=snap_user`
- `SNOWFLAKE_PASSWORD=your_password`

### 2. Set Up Virtual Environment & Dependencies
```cmd
py -3.12 -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 3. Run Multilingual Language Quality Test
```cmd
python tests\test_language.py
```
Outputs are saved to [`docs/language-test.md`](docs/language-test.md).

### 4. Run the Streamlit Application
```cmd
streamlit run app.py
```

---

## 🧪 Testing with Sample Images

Pre-generated test samples are included in the [`samples/`](samples/) folder:
- `samples/product_label.png` (tests Product Label category against `PART`)
- `samples/receipt_invoice.png` (tests Receipt / Invoice category against `ORDERS`)
- `samples/medicine_box.png` (tests Medicine Box with Web Fallback Scraper)

---

## 📜 License

This project is open-source and licensed under the [MIT License](LICENSE).
