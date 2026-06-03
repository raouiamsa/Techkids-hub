# compare_runs.py
import pandas as pd
from pathlib import Path

OUT = Path("apps/ai-brain/benchmarking/outputs")

# Remplace ces chemins si nécessaire
ped_writer = OUT / "comp2_Python_age12_levelbeginner_writer_models-20260520_120447.csv"
raw_writer = OUT / "comp2_Python_age12_levelbeginner_writer_models-20260520_104931.csv"

assert ped_writer.exists(), ped_writer
assert raw_writer.exists(), raw_writer

def normalise(df):
    df = df.copy()
    numcols = ["final_score","agent_score","llm_score","content_coverage","hallucination_rate","ragas_avg","citations_count","citation_coverage","ttft_ms","latency","response_length"]
    for c in numcols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "critic_approved" in df.columns:
        df["critic_approved"] = df["critic_approved"].map({True:1,False:0,"True":1,"False":0}).fillna(df.get("critic_approved"))
    return df

ped = normalise(pd.read_csv(ped_writer))
raw = normalise(pd.read_csv(raw_writer))

keys = ["topic","age","level","model","run_index","seed"]
pair = pd.merge(
    ped, raw, on=keys, suffixes=("_ped","_raw"), how="outer", indicator=True
)

metrics = ["final_score","content_coverage","hallucination_rate","ragas_avg","citations_count","critic_approved"]
for m in metrics:
    pair[f"{m}_delta"] = pair.get(f"{m}_ped") - pair.get(f"{m}_raw")

# Summary by model (means)
ped_summary = ped.groupby("model")[metrics].mean().add_suffix("_ped")
raw_summary = raw.groupby("model")[metrics].mean().add_suffix("_raw")
summary = ped_summary.join(raw_summary, how="outer")
for m in metrics:
    summary[f"{m}_delta"] = summary[f"{m}_ped"] - summary[f"{m}_raw"]

# Save outputs
pair.to_csv(OUT / "comparison_pairwise.csv", index=False)
summary.to_csv(OUT / "comparison_summary_by_model.csv")

print("Saved: outputs/comparison_pairwise.csv and comparison_summary_by_model.csv")
print(summary)