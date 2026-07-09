import pandas as pd
import re
import os




def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


pred_df = pd.read_csv("drug_ade_relations.csv").fillna("")
# pred_df = pd.read_csv("drug_ade_relations_bosung.csv").fillna("")

pred_df['Drug'] = pred_df['Drug'].apply(clean_text)
pred_df['ADE'] = pred_df['ADE'].apply(clean_text)
pred_df['File'] = pred_df['File'].astype(str)


gt_relations = [
    {"File": "ARTHROTEC.1", "Drug": "arthrotec", "ADE": "bit drowsy"},
    {"File": "ARTHROTEC.1", "Drug": "arthrotec", "ADE": "little blurred vision"},
    {"File": "ARTHROTEC.1", "Drug": "arthrotec", "ADE": "gastric problems"},
    {"File": "ARTHROTEC.2", "Drug": "arthrotec", "ADE": "heartburn"},
    {"File": "ARTHROTEC.2", "Drug": "arthrotec", "ADE": "nausea"},
    {"File": "ARTHROTEC.2", "Drug": "arthrotec", "ADE": "voracious hunger"},
    {"File": "ARTHROTEC.2", "Drug": "arthrotec", "ADE": "sharp unbearable cramping pains in lower gut"},
    {"File": "ARTHROTEC.6", "Drug": "arthrotec", "ADE": "stomach pain"},
    {"File": "ARTHROTEC.6", "Drug": "arthrotec", "ADE": "slight nausea"},
    {"File": "ARTHROTEC.6", "Drug": "arthrotec", "ADE": "reflux"},
    {"File": "ARTHROTEC.6", "Drug": "arthrotec", "ADE": "abdominal cramps and pain"},
    {"File": "ARTHROTEC.6", "Drug": "arthrotec", "ADE": "abdominal gas"},
    {"File": "ARTHROTEC.6", "Drug": "arthrotec", "ADE": "abdominal cramps"},
    {"File": "ARTHROTEC.6", "Drug": "arthrotec", "ADE": "abdominal discomfort"},
    {"File": "ARTHROTEC.6", "Drug": "tylenol", "ADE": "stomach pain"},
    {"File": "ARTHROTEC.6", "Drug": "tylenol", "ADE": "slight nausea"},
    {"File": "ARTHROTEC.6", "Drug": "tylenol", "ADE": "reflux"},
    {"File": "ARTHROTEC.6", "Drug": "tylenol", "ADE": "abdominal cramps and pain"},
    {"File": "ARTHROTEC.6", "Drug": "tylenol", "ADE": "abdominal gas"},
    {"File": "ARTHROTEC.6", "Drug": "tylenol", "ADE": "abdominal cramps"},
    {"File": "ARTHROTEC.6", "Drug": "tylenol", "ADE": "abdominal discomfort"},
    {"File": "ARTHROTEC.7", "Drug": "clonidine", "ADE": "severe sudden onset headache in the back of head"},
    {"File": "ARTHROTEC.7", "Drug": "clonidine", "ADE": "BP was extrememly high"},
    {"File": "ARTHROTEC.7", "Drug": "clonidine", "ADE": "pulse was high"},
    {"File": "ARTHROTEC.7", "Drug": "clonidine", "ADE": "high BP"},
    {"File": "ARTHROTEC.7", "Drug": "clonidine", "ADE": "pulse is still extremely high"},
    {"File": "ARTHROTEC.7", "Drug": "clonidine", "ADE": "tachycardia"},
    {"File": "ARTHROTEC.18", "Drug": "arthrotec", "ADE": "slightly heavier menstrual cycle"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "nausea"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "dizziness"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "stomach pains"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "chest pains"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "anxiety"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "fatigue"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "headache"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "erratic heart beat", "Sentence": "Stomach pains, chest pains, anxiety, fatigue, headache, erratic heart beat, raised blood pressure, dizziness, nausea (even when taken with food), blurred vision."},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "raised blood pressure"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "blurred vision"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "period like cramps" , "Sentence": "The first day I took both pills, I experienced some dizziness and some nausea and some serious period like cramps."},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "cramps"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "elevated heart rate" , "Sentence": "On the evening of 4/30, I suddenly got some serious chest pains, an elevated heart rate... hot flashes, dizziness, sever stomach cramps, and weakness in my legs."},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "hot flashes"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "sever stomach cramps"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "weakness in my legs"},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "thought I was dying", "Sentence": "I literally thought I was dying."},
    {"File": "ARTHROTEC.42", "Drug": "arthrotec", "ADE": "inhibiting my menstrual cycle", "Sentence": "After about two days (two doses), the cramps continued and began inhibiting my menstrual cycle (which I was due to start)."},
    {"File": "ARTHROTEC.103", "Drug": "arthrotec", "ADE": "bleeding"},
    {"File": "ARTHROTEC.103", "Drug": "arthrotec", "ADE": "so much pain"},
    {"File": "ARTHROTEC.103", "Drug": "arthrotec", "ADE": "feel weak and almost fainted"},
    {"File": "ARTHROTEC.3", "Drug": "Arthrotec", "ADE": "Constipation"},
    {"File": "ARTHROTEC.3", "Drug": "Arthrotec", "ADE": "joint pain"},
    {"File": "ARTHROTEC.3", "Drug": "Arthrotec", "ADE": "Pain"},
    {"File": "ARTHROTEC.3", "Drug": "Arthrotec", "ADE": "extreme itching on legs and arms"},
    {"File": "ARTHROTEC.3", "Drug": "Arthrotec", "ADE": "mobility has DECREASED"},
    {"File": "ARTHROTEC.3", "Drug": "Arthrotec", "ADE": "constipation"},
    {"File": "ARTHROTEC.3", "Drug": "Arthrotec", "ADE": "muscle pain"}, 
    {"File": "ARTHROTEC.3", "Drug": "co-codamol", "ADE": "Constipation"},
    {"File": "ARTHROTEC.3", "Drug": "co-codamol", "ADE": "joint pain"},
    {"File": "ARTHROTEC.3", "Drug": "co-codamol", "ADE": "Pain"},
    {"File": "ARTHROTEC.3", "Drug": "co-codamol", "ADE": "extreme itching on legs and arms"},
    {"File": "ARTHROTEC.3", "Drug": "co-codamol", "ADE": "mobility has DECREASED"},
    {"File": "ARTHROTEC.3", "Drug": "co-codamol", "ADE": "constipation"},
    {"File": "ARTHROTEC.3", "Drug": "co-codamol", "ADE": "muscle pain"},
    {"File": "ARTHROTEC.4", "Drug": "Arthrotec", "ADE": "menstruating with heavy bleeding every 11 days"},
    {"File": "ARTHROTEC.4", "Drug": "Arthrotec", "ADE": "horrific cramps"},
    {"File": "ARTHROTEC.16", "Drug": "arthrotec", "ADE": "headache"},
    {"File": "ARTHROTEC.16", "Drug": "arthrotec", "ADE": "heavy vaginal bleeding"},
]

gt_df = pd.DataFrame(gt_relations)


gt_df['Drug'] = gt_df['Drug'].apply(clean_text)
gt_df['ADE'] = gt_df['ADE'].apply(clean_text)
gt_df['File'] = gt_df['File'].astype(str)


pred_set = set([tuple(x) for x in pred_df[['File','Drug','ADE']].values])
gt_set = set([tuple(x) for x in gt_df[['File','Drug','ADE']].values])

tp = len(pred_set & gt_set)
fp = len(pred_set - gt_set)
fn = len(gt_set - pred_set)
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0


print("="*60)
print("{:^60}".format("Đánh giá Relation Extraction"))
print("="*60)
print(f"{'TP':>5}{'FP':>6}{'FN':>6}{'Precision':>10}{'Recall':>10}{'F1':>10}")
print("-"*60)
print(f"{tp:>5}{fp:>6}{fn:>6}{precision:>10.3f}{recall:>10.3f}{f1:>10.3f}")


relation_eval_results = []
for file in gt_df['File'].unique():
    gt_file_set = set([tuple(x) for x in gt_df[gt_df['File']==file][['Drug','ADE']].values])
    pred_file_set = set([tuple(x) for x in pred_df[pred_df['File']==file][['Drug','ADE']].values])

    tp_file = len(gt_file_set & pred_file_set)
    fp_file = len(pred_file_set - gt_file_set)
    fn_file = len(gt_file_set - pred_file_set)

    precision_file = tp_file / (tp_file + fp_file) if (tp_file + fp_file) > 0 else 0
    recall_file = tp_file / (tp_file + fn_file) if (tp_file + fn_file) > 0 else 0
    f1_file = 2 * precision_file * recall_file / (precision_file + recall_file) if (precision_file + recall_file) > 0 else 0

    relation_eval_results.append({
        "File": file, "TP": tp_file, "FP": fp_file, "FN": fn_file,
        "Precision": round(precision_file,3),
        "Recall": round(recall_file,3),
        "F1": round(f1_file,3)
    })

pd.DataFrame(relation_eval_results).to_csv("relation_evaluation_per_file.csv", index=False, encoding="utf-8-sig")

print("\n===== TP =====")
tp_list = list(pred_set & gt_set)
for x in tp_list[:10]:
    print(x)

print("\n===== FP =====")
fp_list = list(pred_set - gt_set)
for x in fp_list[:10]:
    print(x)

print("\n===== FN =====")
fn_list = list(gt_set - pred_set)
for x in fn_list[:10]:
    print(x)






sent_map = {}


for _, row in pred_df.iterrows():
    key = (row['File'], row['Drug'], row['ADE'])
    if key not in sent_map or not sent_map[key]:
        sent_map[key] = row.get('Sentence', '')

for _, row in gt_df.iterrows():
    key = (row['File'], row['Drug'], row['ADE'])
    if key not in sent_map or not sent_map[key]:
        sent_map[key] = row.get('Sentence', '')
        
def tao_bang_danh_gia(tp_list, fp_list, fn_list, sent_map):
    rows = []

   
    for file, drug, ade in tp_list[:5]:
        rows.append({
            "File": file,
            "Sentence": sent_map.get((file, drug, ade), ""),
            "Drug": drug,
            "ADE": ade,
            "Gold": "Yes",
            "Predicted": "Yes",
            "Kết luận": "Đúng",
            "Giải thích": "Model dự đoán đúng quan hệ Drug-ADE"
        })

   
    for file, drug, ade in fp_list[:5]:
        rows.append({
            "File": file,
            "Sentence": sent_map.get((file, drug, ade), ""),
            "Drug": drug,
            "ADE": ade,
            "Gold": "No",
            "Predicted": "Yes",
            "Kết luận": "Sai (FP)",
            "Giải thích": "Model nhầm lẫn do Drug và ADE cùng xuất hiện nhưng không có quan hệ nhân quả rõ ràng hoặc ngữ cảnh gây nhiễu"
        })

    
    for file, drug, ade in fn_list[:5]:
        rows.append({
            "File": file,
            "Sentence": sent_map.get((file, drug, ade), ""),
            "Drug": drug,
            "ADE": ade,
            "Gold": "Yes",
            "Predicted": "No",
            "Kết luận": "Sai (FN)",
            "Giải thích": "Model bỏ sót do biểu đạt ADE đa dạng, không khớp từ điển hoặc câu có cấu trúc phức tạp"
        })

    return pd.DataFrame(rows)


df_eval = tao_bang_danh_gia(tp_list, fp_list, fn_list, sent_map)

df_eval.to_csv("danh_gia_dinh_tinh.csv", index=False, encoding="utf-8-sig")

