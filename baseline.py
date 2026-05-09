import pandas as pd

def baseline_decision(row):
    """
    输入：一行数据（一个case）
    输出：decision, quantity, confidence, reason
    """

    price_pos = row["Price_Position"]
    demand = row["Demand_Trend_3D"]
    inventory_age = int(row["Inventory_Age"])
    unsold_ratio = float(row["Unsold_Inventory_Ratio"])

    # --- Decision ---
    if price_pos == "low" and demand == "increasing":
        decision = "Y"
    elif price_pos == "high" and demand == "decreasing":
        decision = "N"
    elif inventory_age >= 2:
        decision = "N"
    else:
        decision = "Y"

    # --- Quantity ---
    if decision == "N":
        quantity = "None"
    else:
        if demand == "increasing" and unsold_ratio < 0.5:
            quantity = "High"
        elif demand == "stable":
            quantity = "Medium"
        else:
            quantity = "Low"

    # --- Confidence ---
    if demand == "increasing" and price_pos == "low":
        confidence = "High"
    elif demand == "decreasing":
        confidence = "High"
    else:
        confidence = "Medium"

    # --- Reason ---
    reason = f"Baseline rule: price={price_pos}, demand={demand}, inventory_age={inventory_age}"

    return decision, quantity, confidence, reason


if __name__ == "__main__":
    df = pd.read_csv("data/test_cases.csv", skiprows=[1])

    results = []

    for _, row in df.iterrows():
        decision, quantity, confidence, reason = baseline_decision(row)

        results.append({
            "Case_ID": row["Case_ID"],
            "Baseline_Decision": decision,
            "Baseline_Quantity": quantity,
            "Baseline_Confidence": confidence,
            "Baseline_Reason": reason
        })

    result_df = pd.DataFrame(results)
    print(result_df.head())