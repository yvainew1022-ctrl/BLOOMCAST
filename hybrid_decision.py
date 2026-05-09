from llm_decision import gemini_decision


def hybrid_decision(row):
    """
    Hybrid system:
    - Gemini provides decision, confidence, and explanation.
    - Rule-based guardrails correct the quantity recommendation.
    """

    llm_decision, llm_quantity, llm_confidence, llm_reason = gemini_decision(row)

    price_pos = row["Price_Position"]
    demand = row["Demand_Trend_3D"]
    inventory_age = int(row["Inventory_Age"])
    unsold_ratio = float(row["Unsold_Inventory_Ratio"])
    event_multiplier = float(row["Event_Demand_Multiplier"])
    substitution_pressure = row["Substitution_Pressure"]

    # Hard safety rule: do not buy if inventory risk is too high
    if inventory_age >= 2 or unsold_ratio > 1.5:
        return (
            "N",
            "None",
            "High",
            "Hybrid guardrail: inventory is aging or unsold inventory risk is too high."
        )

    # If Gemini says no, keep no-buy unless strong demand clearly supports buying
    if llm_decision == "N":
        if demand == "increasing" and unsold_ratio < 0.7:
            decision = "Y"
        else:
            return (
                "N",
                "None",
                llm_confidence,
                llm_reason
            )
    else:
        decision = "Y"

    # Quantity guardrails
    quantity = "Medium"

    # Strong buy conditions
    if (
        demand == "increasing"
        and unsold_ratio < 0.5
        and inventory_age <= 1
        and (event_multiplier >= 1.3 or price_pos == "low")
        and substitution_pressure != "high"
    ):
        quantity = "High"

    # Risk reduction conditions
    if (
        substitution_pressure == "high"
        or price_pos == "high"
        or demand == "decreasing"
    ):
        quantity = "Low"

    # Mixed strong demand + risk = Medium
    if (
        demand == "increasing"
        and (event_multiplier >= 1.3 or unsold_ratio < 0.5)
        and (substitution_pressure == "high" or price_pos == "high")
    ):
        quantity = "Medium"

    # Extreme risk but still buy = Low
    if substitution_pressure == "high" and price_pos == "high":
        quantity = "Low"

    reason = (
        f"Hybrid recommendation: {llm_reason} "
        f"Quantity adjusted using business guardrails based on price={price_pos}, "
        f"demand={demand}, unsold_ratio={unsold_ratio}, event_multiplier={event_multiplier}, "
        f"and substitution_pressure={substitution_pressure}."
    )

    return decision, quantity, llm_confidence, reason