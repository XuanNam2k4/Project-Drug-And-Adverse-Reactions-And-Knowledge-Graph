import os
import re
import spacy
import pandas as pd


nlp = spacy.load("en_core_web_sm")

def clean_text(text):
    text = text.lower()

    replacements = {
        r"\bgp'?s?\b": "doctor",
        r"\bdr\.?\b": "doctor",
        r"\bmeds\b": "medicines",
        r"\bmg\b": "milligrams",
        r"&": "and",
        r"\bu\b": "you",
        r"\bdocs\b": "doctors"
    }

    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)

    text = re.sub(r"[^\w\s\.,!?'-]", " ", text)

    text = re.sub(r"\s+", " ", text).strip()

    return text

text_folder = r"D:\DoanTN\data\cadec\text"
data = []


if not os.path.exists(text_folder):
    print(f"Lỗi: Không tìm thấy thư mục {text_folder}")
else:
    for file in os.listdir(text_folder):
        if file.endswith(".txt"):
            path = os.path.join(text_folder, file)

            with open(path, "r", encoding="utf-8") as f:
                raw_text = f.read()

            doc = nlp(raw_text)

            for i, sent in enumerate(doc.sents):
                original_sentence = sent.text.strip()

                if original_sentence == "":
                    continue
         
                cleaned_sentence = clean_text(original_sentence)
        
                tokens = [token.text for token in nlp.tokenizer(cleaned_sentence)]

                data.append({
                    "file": file,
                    "sentence_id": i + 1,
                    "before_preprocess": original_sentence,
                    "after_preprocess": cleaned_sentence,
                    "tokens": tokens
                })

    df = pd.DataFrame(data)
    df.to_csv("cadec_tienxuly.csv", index=False, encoding="utf-8-sig")
    print("Đã tạo file cadec_tienxuly.csv")