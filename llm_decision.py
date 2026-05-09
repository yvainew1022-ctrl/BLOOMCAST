import json
import time
from google import genai


client = genai.Client()


def clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()
    return text


def gemini_decision(row):
    prompt = f"""
You are BloomCast, a procurement decision assistant for a small e-commerce flower seller.

Return ONLY valid JSON with these fields:
{{
  "decision": "Y" or "N",
  "quantity": "High" or "Medium" or "Low" or "None",
  "confidence": "High" or "Medium" or "Low",
  "reason": "one concise business explanation"
}}

Decision rules:
- If inventory age >= 2 OR unsold inventory ratio > 1.5, recommend decision = "N".
- If price is high AND demand is decreasing, recommend decision = "N".
- If demand is increasing OR event demand multiplier >= 1.5, recommend decision = "Y".
- If decision = "N", quantity must be "None".

Quantity rules:
- Start from "Medium" as the default quantity when decision = "Y".
- Increase quantity to "High" when:
  - demand is increasing,
  - inventory is fresh or low-risk,
  - unsold inventory ratio < 0.5,
  - and event demand multiplier >= 1.3 OR price position is low.
- Reduce quantity to "Low" when:
  - substitution pressure is high,
  - OR price position is high,
  - OR demand is decreasing.
- If both strong demand and high risk exist, use "Medium".
- If price is high but event demand is strong, do not automatically reject; reduce quantity instead.
- Do NOT be overly conservative. Many valid buy cases should be "Medium" or "High".

Confidence rules:
- Use "High" for clear cases where signals agree.
- Use "Medium" for mixed signals.
- Use "Low" for highly conflicting cases.

Case:
SKU_ID: {row["SKU_ID"]}
Flower_Type: {row["Flower_Type"]}
Variety_Name: {row["Variety_Name"]}
Color: {row["Color"]}
Origin: {row["Origin"]}
Grade: {row["Flower_Grade"]}
Today_Price: {row["Today_Price"]}
Past_avg_Price_7d: {row["Past_avg_Price_7d"]}
Price_Position: {row["Price_Position"]}
Sales_Past_3d: {row["Sales_Past_3d"]}
Demand_Trend_3D: {row["Demand_Trend_3D"]}
Sales_Last_Year_Same_Period: {row["Sales_Last_Year_Same_Period"]}
Current_Inventory: {row["Current_Inventory"]}
Inventory_Age: {row["Inventory_Age"]}
Last_Purchase_Days: {row["Last_Purchase_Days"]}
Unsold_Inventory_Ratio: {row["Unsold_Inventory_Ratio"]}
Event_Name: {row["Event_Name"]}
Days_to_Event: {row["Days_to_Event"]}
Event_Demand_Multiplier: {row["Event_Demand_Multiplier"]}
Substitution_Group: {row["Substitution_Group"]}
Substitution_Tier: {row["Substitution_Tier"]}
Reference_Competitor_Price: {row["Reference_Competitor_Price"]}
Substitution_Pressure: {row["Substitution_Pressure"]}
"""

    models_to_try = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
    last_error = None

    for model_name in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )

                text = clean_json_text(response.text)
                result = json.loads(text)

                decision = result.get("decision", "N")
                quantity = result.get("quantity", "None")
                confidence = result.get("confidence", "Low")
                reason = result.get("reason", "")

                if decision not in ["Y", "N"]:
                    decision = "N"

                if quantity not in ["High", "Medium", "Low", "None"]:
                    quantity = "None"

                if confidence not in ["High", "Medium", "Low"]:
                    confidence = "Low"

                if decision == "N":
                    quantity = "None"

                return decision, quantity, confidence, reason

            except Exception as e:
                last_error = e
                time.sleep(2)

    return (
        "N",
        "None",
        "Low",
        f"Gemini API failed after retries: {last_error}"
    )