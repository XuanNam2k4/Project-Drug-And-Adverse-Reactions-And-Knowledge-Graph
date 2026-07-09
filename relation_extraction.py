import pandas as pd

# df = pd.read_csv("baseline_ketqua.csv").fillna("")
df = pd.read_csv("baseline_ketqua.csv", sep=";").fillna("")
relations = []

for index, row in df.iterrows():

    drugs = str(row["Drug_Predicted"]).split(",")
    ades = str(row["ADE_Predicted"]).split(",")

    drugs = [d.strip() for d in drugs if d.strip() != ""]
    ades = [a.strip() for a in ades if a.strip() != ""]

    if len(drugs) > 0 and len(ades) > 0:

        for d in drugs:
            for a in ades:

                relations.append({
                    "File": row.get("file", ""),
                    "Drug": d,
                    "ADE": a,
                    "Sentence": row.get("sentence", "")
                })

relation_df = pd.DataFrame(relations)

relation_df = relation_df.drop_duplicates()

relation_df.to_csv("drug_ade_relations.csv",index=False,encoding="utf-8-sig")

print("kết quả drug_ade_relations.csv")


# 1. Đếm tổng số lượng thuốc (Drug) duy nhất
total_unique_drugs = relation_df["Drug"].nunique()
print(f"Tổng số lượng thuốc (Drug) khác nhau: {total_unique_drugs}")

# 2. Hiển thị danh sách tên tất cả các loại thuốc đó
unique_drugs_list = relation_df["Drug"].unique()
print("Danh sách các thuốc:")
for drug in unique_drugs_list:
    print(f"- {drug}")