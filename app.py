import streamlit as st
import pandas as pd
from llm_decision import gemini_decision


st.set_page_config(page_title="BloomCast", layout="centered")

st.title("🌸 BloomCast: Flower Procurement Assistant")
st.markdown("A GenAI decision-support tool for daily flower purchasing decisions.")

df = pd.read_csv("data/test_cases.csv", skiprows=[1], keep_default_na=False)

mode = st.radio("Choose Mode", ["Test Case Mode", "Manual Input Mode"])


def show_recommendation(row, show_ground_truth=False):
    st.subheader("📊 Decision Context")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Flower", f'{row["Variety_Name"]} {row["Flower_Type"]}')
        st.metric("Origin", row["Origin"])
        st.metric("Grade", row["Flower_Grade"])
        st.metric("Today Price", row["Today_Price"])

    with col2:
        st.metric("Price Position", row["Price_Position"])
        st.metric("Demand Trend", row["Demand_Trend_3D"])
        st.metric("Unsold Ratio", round(float(row["Unsold_Inventory_Ratio"]), 2))
        st.metric("Event", row["Event_Name"])

    if st.button("Get Recommendation"):
        decision, quantity, confidence, reason = gemini_decision(row)

        st.subheader("🤖 Gemini Recommendation")

        if decision == "Y":
            st.success(f"✅ BUY — Suggested Quantity: {quantity}")
        else:
            st.error("❌ DO NOT BUY")

        st.info(f"Confidence: {confidence}")

        st.markdown("**Reason:**")
        st.write(reason)

        if show_ground_truth:
            st.subheader("📌 Ground Truth")
            st.write({
                "Decision": row["Ground_Truth_Decision"],
                "Quantity": row["Ground_Truth_Quantity"],
                "Confidence": row["Ground_Truth_Confidence"],
                "Reason": row["Ground_Truth_Reason"]
            })


if mode == "Test Case Mode":
    st.subheader("🧪 Test Case Evaluation Mode")

    selected_case = st.selectbox("Select a test case", df["Case_ID"].tolist())
    row = df[df["Case_ID"] == selected_case].iloc[0]

    show_recommendation(row, show_ground_truth=True)


else:
    st.subheader("✍️ Manual Input Mode")

    st.markdown(
        "Enter the core information a seller would know in the morning. "
        "The system will infer supporting signals using reference values from the dataset."
    )

    flower_type = st.selectbox(
        "Flower Type",
        sorted(df["Flower_Type"].unique())
    )

    filtered = df[df["Flower_Type"] == flower_type]

    variety_name = st.selectbox(
        "Variety Name",
        sorted(filtered["Variety_Name"].unique())
    )

    filtered = filtered[filtered["Variety_Name"] == variety_name]

    origin = st.selectbox(
        "Origin",
        sorted(filtered["Origin"].unique())
    )

    filtered = filtered[filtered["Origin"] == origin]

    grade = st.selectbox(
        "Flower Grade",
        sorted(filtered["Flower_Grade"].unique())
    )

    matched = filtered[filtered["Flower_Grade"] == grade]

    if matched.empty:
        st.warning("No matching SKU found in the dataset.")
    else:
        template = matched.iloc[0].copy()

        today_price = st.number_input(
            "Today Price",
            min_value=0.0,
            value=float(template["Today_Price"]),
            step=0.5
        )

        current_inventory = st.number_input(
            "Current Inventory",
            min_value=0,
            value=int(template["Current_Inventory"]),
            step=10
        )

        inventory_age = st.selectbox(
            "Inventory Age",
            [0, 1, 2],
            index=int(template["Inventory_Age"]) if int(template["Inventory_Age"]) in [0, 1, 2] else 0
        )

        sales_past_3d = st.number_input(
            "Sales in Past 3 Days",
            min_value=0,
            value=int(template["Sales_Past_3d"]),
            step=10
        )

        event_name = st.selectbox(
            "Event",
            ["None", "Valentine", "MothersDay", "Graduation", "Spring"]
        )

        # Build manual row from template
        row = template.copy()
        row["Today_Price"] = today_price
        row["Current_Inventory"] = current_inventory
        row["Inventory_Age"] = inventory_age
        row["Last_Purchase_Days"] = inventory_age
        row["Sales_Past_3d"] = sales_past_3d
        row["Event_Name"] = event_name

        # Derived price position
        avg_price = float(row["Past_avg_Price_7d"])

        if today_price < avg_price:
            row["Price_Position"] = "low"
        elif today_price > avg_price:
            row["Price_Position"] = "high"
        else:
            row["Price_Position"] = "normal"

        # Derived unsold ratio
        if sales_past_3d > 0:
            row["Unsold_Inventory_Ratio"] = round(current_inventory / sales_past_3d, 2)
        else:
            row["Unsold_Inventory_Ratio"] = 999

        # Simple event multiplier logic
        if event_name == "None":
            row["Days_to_Event"] = 999
            row["Event_Demand_Multiplier"] = 1.0
        elif event_name == "Valentine":
            row["Days_to_Event"] = 2
            if flower_type == "Rose":
                row["Event_Demand_Multiplier"] = 2.0 if row["Color"] == "Red" else 1.5
            elif flower_type == "Tulip":
                row["Event_Demand_Multiplier"] = 1.2
            else:
                row["Event_Demand_Multiplier"] = 1.0
        elif event_name == "MothersDay":
            row["Days_to_Event"] = 4
            row["Event_Demand_Multiplier"] = 2.0 if flower_type == "Carnation" else 1.1
        elif event_name == "Graduation":
            row["Days_to_Event"] = 5
            row["Event_Demand_Multiplier"] = 1.5 if flower_type in ["Sunflower", "Lily"] else 1.1
        elif event_name == "Spring":
            row["Days_to_Event"] = 0
            row["Event_Demand_Multiplier"] = 1.3 if flower_type in ["Tulip", "Iris"] else 1.0

        show_recommendation(row, show_ground_truth=False)