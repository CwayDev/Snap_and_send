import os
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

from src.gemma_engine import GemmaEngine
from src.snowflake_client import SnowflakeClient
from src.web_scraper import search_web_fallback

load_dotenv()

st.set_page_config(
    page_title="Snap & Understand | Multimodal AI",
    page_icon="📸",
    layout="wide"
)

# Initialize engines
@st.cache_resource
def get_engines():
    gemma = GemmaEngine()
    snowflake = SnowflakeClient()
    return gemma, snowflake

# UI Header
st.title("📸 Snap & Understand")
st.caption("Powered by **Gemma 4** (Google AI Studio) • Grounded in **Snowflake** (`SNOWFLAKE_SAMPLE_DATA`) & Real-Time Web Fallback • Multilingual (Hausa, French, English)")

# Sidebar Configuration
st.sidebar.header("⚙️ Configuration")
target_languages_raw = os.getenv("TARGET_LANGUAGES", "Hausa,French")
available_languages = ["English"] + [l.strip() for l in target_languages_raw.split(",") if l.strip() and l.strip() != "English"]
selected_language = st.sidebar.selectbox("🌐 Explanatory Language", available_languages, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 🧠 Architecture
- **Model:** Gemma 4 (`gemma-4-26b-a4b-it`)
- **Warehouse:** `SNOWFLAKE_LEARNING_WH`
- **Dataset:** `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`
- **Audit Table:** `SNAP_DB.APP.SNAP_LOGS`
- **Fallback:** Live Web Scraper
""")

# Tabs
tab1, tab2 = st.tabs(["🔍 Snap & Understand", "📊 Snowflake CoCo Dashboard"])

with tab1:
    col_input, col_result = st.columns([1, 1], gap="medium")

    with col_input:
        st.subheader("1. Take or Upload a Photo")
        input_mode = st.radio("Input Source", ["Camera Snap", "File Upload"], horizontal=True)
        
        image_file = None
        if input_mode == "Camera Snap":
            image_file = st.camera_input("Capture item")
        else:
            image_file = st.file_uploader("Upload product, receipt, or label", type=["jpg", "jpeg", "png", "webp"])

        if image_file:
            img = Image.open(image_file)
            st.image(img, caption="Captured Image", use_container_width=True)

    with col_result:
        st.subheader("2. Grounded Understanding")
        if image_file:
            if st.button("🚀 Analyze & Understand with Gemma 4", type="primary", use_container_width=True):
                with st.spinner("Classifying and extracting entities with Gemma 4..."):
                    try:
                        gemma, sf_client = get_engines()
                        
                        # Step 1: Gemma 4 Visual Classification & Extraction
                        analysis = gemma.analyze_image(img)
                        category = analysis.get("category", "Product Label")
                        item_name = analysis.get("item_name", "Detected Item")
                        search_term = analysis.get("search_term", item_name)
                        extracted = analysis.get("extracted_attributes", {})

                        st.success(f"**Identified:** {item_name} ({category})")
                        
                        with st.expander("🔍 Visual Extraction Details", expanded=False):
                            st.json(analysis)

                        # Step 2: Grounding Lookup in Snowflake Dataset
                        grounding_source = "Snowflake (TPCH_SF1)"
                        grounding_context = ""
                        snowflake_results = []

                        with st.spinner(f"Grounding against Snowflake `{category}` dataset..."):
                            if category == "Product Label":
                                snowflake_results = sf_client.lookup_product(search_term)
                            elif category == "Receipt / Invoice":
                                snowflake_results = sf_client.lookup_receipt(extracted.get("code_or_sku") or search_term)
                            else: # Supplier / Vendor Document
                                snowflake_results = sf_client.lookup_supplier(search_term)

                        if snowflake_results:
                            grounding_source = "Snowflake Dataset (Authoritative)"
                            st.info(f"✅ Grounded in **Snowflake Enterprise Dataset** ({len(snowflake_results)} matching records found)")
                            grounding_context = f"Authoritative Snowflake Database Records:\n{snowflake_results}"
                            with st.expander("📊 Snowflake Matched Records"):
                                st.write(snowflake_results)
                        else:
                            # Step 3: Web Fallback Scraper if entity is not in enterprise sample catalog
                            st.warning("ℹ️ Item not in sample Snowflake catalog. Activating **Web Scraping Grounding Tool**...")
                            with st.spinner("Scraping live web context..."):
                                web_data = search_web_fallback(f"{item_name} {extracted.get('brand', '')}".strip())
                                grounding_source = "Web Scraper Fallback"
                                grounding_context = f"Live Web Grounded Knowledge:\n{web_data.get('summary')}"
                                with st.expander("🌐 Scraped Web Intelligence"):
                                    st.write(web_data)

                        # Step 4: Gemma 4 Multilingual Explanation
                        with st.spinner(f"Generating clear explanation in {selected_language}..."):
                            explanation = gemma.explain_multilingual(
                                item_name=item_name,
                                category=category,
                                grounding_data=grounding_context,
                                target_lang=selected_language
                            )

                        # Display Multilingual Output
                        st.markdown(f"### 🗣️ Grounded Explanation ({selected_language})")
                        st.markdown(explanation)

                        # Step 5: Audit Log to Snowflake
                        sf_client.log_snap(
                            category=category,
                            language=selected_language,
                            source=grounding_source,
                            item_identified=item_name
                        )
                        st.caption(f"🔒 Snap audit logged to `SNAP_DB.APP.SNAP_LOGS` (Source: {grounding_source})")

                    except Exception as err:
                        st.error(f"Error during processing: {str(err)}")
        else:
            st.info("Please capture a photo or upload an image to begin.")

with tab2:
    st.subheader("📊 Snowflake Audit Analytics Dashboard")
    st.caption("Auto-generated reporting powered by Snowflake Cortex Code (CoCo) logging")
    
    if st.button("🔄 Refresh Dashboard Metrics"):
        st.rerun()

    try:
        _, sf_client = get_engines()
        metrics = sf_client.get_dashboard_metrics()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Snaps Logged", metrics["total_snaps"])
        m2.metric("Categories Monitored", len(metrics["by_category"]))
        m3.metric("Languages Served", len(metrics["by_language"]))

        st.markdown("---")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### 📦 Snaps by Category")
            if metrics["by_category"]:
                cat_data = {row[0]: row[1] for row in metrics["by_category"]}
                st.bar_chart(cat_data)
            else:
                st.info("No category audit logs yet.")

        with c2:
            st.markdown("#### 🌐 Snaps by Language")
            if metrics["by_language"]:
                lang_data = {row[0]: row[1] for row in metrics["by_language"]}
                st.bar_chart(lang_data)
            else:
                st.info("No language audit logs yet.")

        st.markdown("#### 📡 Grounding Source Distribution")
        if metrics["by_source"]:
            st.write(dict(metrics["by_source"]))

        st.markdown("#### 🕒 Recent Snap Audit Trail")
        if metrics["recent"]:
            st.dataframe(
                metrics["recent"],
                column_config={
                    "0": "ID",
                    "1": "Category",
                    "2": "Language",
                    "3": "Grounding Source",
                    "4": "Item Identified",
                    "5": "Timestamp"
                },
                use_container_width=True
            )
        else:
            st.info("No audit logs recorded yet. Take a snap to see live data!")

    except Exception as e:
        st.error(f"Could not load dashboard: {e}")
