import pandas as pd
from baseline import baseline_decision
from llm_decision import gemini_decision
from hybrid_decision import hybrid_decision


def main():
    df = pd.read_csv("data/test_cases.csv", skiprows=[1], keep_default_na=False)

    results = []

    for _, row in df.iterrows():
        b_decision, b_quantity, _, _ = baseline_decision(row)
        g_decision, g_quantity, _, _ = gemini_decision(row)
        h_decision, h_quantity, _, _ = hybrid_decision(row)

        gt_decision = row["Ground_Truth_Decision"]
        gt_quantity = row["Ground_Truth_Quantity"]

        results.append({
            "Case_ID": row["Case_ID"],

            "GT_Decision": gt_decision,
            "Baseline_Decision": b_decision,
            "Gemini_Decision": g_decision,
            "Hybrid_Decision": h_decision,

            "GT_Quantity": gt_quantity,
            "Baseline_Quantity": b_quantity,
            "Gemini_Quantity": g_quantity,
            "Hybrid_Quantity": h_quantity,
        })

    result_df = pd.DataFrame(results)

    def accuracy(pred_col, gt_col):
        return (result_df[pred_col] == result_df[gt_col]).mean()

    print("\n=== Evaluation Results ===")
    print(f"Baseline Decision Accuracy: {accuracy('Baseline_Decision', 'GT_Decision'):.2%}")
    print(f"Gemini Decision Accuracy:   {accuracy('Gemini_Decision', 'GT_Decision'):.2%}")
    print(f"Hybrid Decision Accuracy:   {accuracy('Hybrid_Decision', 'GT_Decision'):.2%}")

    print(f"Baseline Quantity Accuracy: {accuracy('Baseline_Quantity', 'GT_Quantity'):.2%}")
    print(f"Gemini Quantity Accuracy:   {accuracy('Gemini_Quantity', 'GT_Quantity'):.2%}")
    print(f"Hybrid Quantity Accuracy:   {accuracy('Hybrid_Quantity', 'GT_Quantity'):.2%}")

    result_df.to_csv("outputs/compare_results.csv", index=False)
    print("\nSaved results to outputs/compare_results.csv")


if __name__ == "__main__":
    main()