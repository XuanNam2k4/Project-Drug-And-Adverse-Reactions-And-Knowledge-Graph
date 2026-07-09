import os
import pandas as pd
import re

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


ann_folder = r"D:\DoanTN\data\cadec\original"

drug_dict = set()
ade_dict = set()
gt_drug_doc = {}
gt_ade_doc = {}


for file in os.listdir(ann_folder):
    if file.endswith(".ann"):
        name = file.replace(".ann", "")
        path = os.path.join(ann_folder, file)
        gt_drug_doc[name] = set()
        gt_ade_doc[name] = set()
        with open(path, "r", encoding="utf8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) < 3:
                    continue
                label = parts[1].split()[0]
                entity = clean_text(parts[2])
                if len(entity) < 3:
                    continue
                if label == "Drug":
                    drug_dict.add(entity)
                    gt_drug_doc[name].add(entity)
                if label == "ADR":
                    ade_dict.add(entity)
                    gt_ade_doc[name].add(entity)


sorted_drugs = sorted(drug_dict, key=len, reverse=True)
sorted_ades = sorted(ade_dict, key=len, reverse=True)

drug_pattern = r'\b(?:' + '|'.join(map(re.escape, sorted_drugs)) + r')\b'
ade_pattern = r'\b(?:' + '|'.join(map(re.escape, sorted_ades)) + r')\b'

drug_regex = re.compile(drug_pattern, re.IGNORECASE)
ade_regex = re.compile(ade_pattern, re.IGNORECASE)

stop_ade = {"week","day","year","month","time","today","bit","thing","something","lot","hours",
"mins","minutes"}


df = pd.read_csv("cadec_tienxuly.csv")
df = df.dropna(subset=["after_preprocess"])


pred_drug_doc = {}
pred_ade_doc = {}
results = []

for index, row in df.iterrows():
    text = str(row["after_preprocess"]).lower()
    file_name = str(row["file"]).replace(".txt", "")
    if file_name not in pred_drug_doc:
        pred_drug_doc[file_name] = set()
        pred_ade_doc[file_name] = set()
    drug_found = {x.lower() for x in drug_regex.findall(text)}
    ade_found = {x.lower() for x in ade_regex.findall(text)}
    ade_found = {x for x in ade_found if x not in stop_ade}
    pred_drug_doc[file_name].update(drug_found)
    pred_ade_doc[file_name].update(ade_found)
    results.append({
        "file": file_name,
        "sentence": text,
        "Drug_Predicted": ", ".join(sorted(drug_found)),
        "ADE_Predicted": ", ".join(sorted(ade_found))
    })


result_df = pd.DataFrame(results)
result_df.to_csv("baseline_ketqua.csv", index=False, encoding="utf-8-sig")


def evaluate_ner(gt_dict, pred_dict):
    total_tp = 0
    total_fp = 0
    total_fn = 0
    for file_name in gt_dict.keys():
        gt_set = gt_dict.get(file_name, set())
        pred_set = pred_dict.get(file_name, set())
        tp = len(gt_set.intersection(pred_set))
        fp = len(pred_set - gt_set)
        fn = len(gt_set - pred_set)
        total_tp += tp
        total_fp += fp
        total_fn += fn
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return precision, recall, f1, total_tp, total_fp, total_fn


p_drug, r_drug, f1_drug, tp_drug, fp_drug, fn_drug = evaluate_ner(gt_drug_doc, pred_drug_doc)

p_ade, r_ade, f1_ade, tp_ade, fp_ade, fn_ade = evaluate_ner(gt_ade_doc, pred_ade_doc)


print("="*60)
print("{:^40}".format("Đánh giá NER"))
print("="*60)
print(f"{'Entity':<10}{'TP':>5}{'FP':>5}{'FN':>5}{'Precision':>10}{'Recall':>10}{'F1':>10}")
print("-"*60)
print(f"{'Drug':<10}{tp_drug:>5}{fp_drug:>5}{fn_drug:>5}{p_drug:>10.3f}{r_drug:>10.3f}{f1_drug:>10.3f}")
print(f"{'ADE':<10}{tp_ade:>5}{fp_ade:>5}{fn_ade:>5}{p_ade:>10.3f}{r_ade:>10.3f}{f1_ade:>10.3f}")


ner_eval_results = []
for file_name in gt_drug_doc.keys():
    gt_set = gt_drug_doc.get(file_name, set())
    pred_set = pred_drug_doc.get(file_name, set())
    tp = len(gt_set.intersection(pred_set))
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    ner_eval_results.append({
        "file": file_name, "TP": tp, "FP": fp, "FN": fn,
        "Precision": round(precision, 3), "Recall": round(recall, 3), "F1": round(f1, 3)
    })
pd.DataFrame(ner_eval_results).to_csv("ner_evaluation_per_file.csv", index=False, encoding="utf-8-sig")
print("đã tạo kết quả ner_evaluation_per_file.csv")

import matplotlib.pyplot as plt

metrics = ["Precision", "Recall", " F1-score"]
drug_scores = [p_drug, r_drug, f1_drug]
ade_scores = [p_ade, r_ade, f1_ade]

x = range(len(metrics))
width = 0.35   # giảm lại cho đẹp

plt.figure(figsize=(8,5))

plt.bar([i - width/2 for i in x], drug_scores, width, label="Drug")
plt.bar([i + width/2 for i in x], ade_scores, width, label="ADE")

# hiện số
for i in range(len(metrics)):
    plt.text(i - width/2, drug_scores[i] + 0.01, f"{drug_scores[i]:.2f}", ha='center')
    plt.text(i + width/2, ade_scores[i] + 0.01, f"{ade_scores[i]:.2f}", ha='center')

plt.xticks(x, metrics)
plt.ylim(0.1, 1.25)
plt.title("Baseline NER Precision - Recall - F1-score")
plt.ylabel("Score")

# ===== CHỖ QUAN TRỌNG =====
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)

plt.tight_layout()
plt.show()