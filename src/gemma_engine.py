import os
import json
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()

class GemmaEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment or .env file!")
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemma-4-26b-a4b-it"

    def analyze_image(self, image: Image.Image) -> dict:
        """
        Gemma 4 visual classification & entity extraction:
        Classifies image into one of 3 categories:
          1. 'Product Label'
          2. 'Receipt / Invoice'
          3. 'Supplier / Vendor Document'
        Extracts key identifying terms to query Snowflake or the web fallback.
        """
        prompt = (
            "You are the visual understanding core of 'Snap & Understand'. "
            "Examine this image carefully and classify it into EXACTLY ONE of the following 3 categories:\n"
            "1. 'Product Label' (e.g. food, manufactured parts, medicine box, retail item, merchandise)\n"
            "2. 'Receipt / Invoice' (e.g. store receipts, order invoices, billings, cash slips)\n"
            "3. 'Supplier / Vendor Document' (e.g. business card, vendor directory, company letterhead, supplier spec)\n\n"
            "Return a clean JSON object ONLY (no markdown fences, no extra text) with the following keys:\n"
            "{\n"
            "  \"category\": \"Product Label\" | \"Receipt / Invoice\" | \"Supplier / Vendor Document\",\n"
            "  \"item_name\": \"Brief name of the primary item or document title\",\n"
            "  \"search_term\": \"Best 1-3 keyword phrase to search in database or web\",\n"
            "  \"extracted_attributes\": {\n"
            "     \"brand\": \"brand or manufacturer if visible\",\n"
            "     \"price_or_total\": \"price or total sum if visible\",\n"
            "     \"code_or_sku\": \"any SKU, order number, or barcode if visible\",\n"
            "     \"key_text\": \"summary of visible text on the image\"\n"
            "  }\n"
            "}"
        )
        candidate_models = [self.model, "models/gemma-4-31b-it", "gemini-2.5-flash"]
        for model in candidate_models:
            for attempt in range(2):
                try:
                    resp = self.client.models.generate_content(
                        model=model,
                        contents=[prompt, image]
                    )
                    raw = resp.text.strip()
                    # Clean markdown code blocks if returned
                    if raw.startswith("```json"):
                        raw = raw[7:]
                    if raw.startswith("```"):
                        raw = raw[3:]
                    if raw.endswith("```"):
                        raw = raw[:-3]
                    data = json.loads(raw.strip())
                    return data
                except Exception:
                    import time
                    time.sleep(1.0)
        except Exception as e:
            # Safe structured fallback
            return {
                "category": "Product Label",
                "item_name": "Unclassified Visual Item",
                "search_term": "Product",
                "extracted_attributes": {
                    "brand": "Unknown",
                    "price_or_total": "N/A",
                    "code_or_sku": "N/A",
                    "key_text": f"Gemma vision analysis error: {str(e)}"
                }
            }

    def explain_multilingual(self, item_name: str, category: str, grounding_data: str, target_lang: str) -> str:
        """
        Uses Gemma 4 to explain the grounded results clearly and naturally
        in the user's preferred language (e.g. English, Hausa, French).
        Includes automatic retries for transient Google API 500 internal hiccups.
        """
        prompt = (
            f"You are the multilingual explainer for 'Snap & Understand'. "
            f"Explain what this item is, its verified details, and what the user should know about it, "
            f"grounded in the factual data provided below. "
            f"Respond clearly and fluently in **{target_lang}**.\n\n"
            f"ITEM: {item_name}\n"
            f"CATEGORY: {category}\n"
            f"FACTUAL GROUNDING DATA:\n{grounding_data}\n\n"
            f"Format with clean headings, bullet points, and practical advice in {target_lang}."
        )

        candidate_models = [self.model, "models/gemma-4-31b-it", "gemini-2.5-flash"]
        last_error = ""

        for model in candidate_models:
            for attempt in range(2):
                try:
                    resp = self.client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    if resp and resp.text:
                        return resp.text.strip()
                except Exception as e:
                    last_error = str(e)
                    import time
                    time.sleep(1.0)

        return f"Explanation temporarily unavailable ({last_error}). Please click Analyze again."
