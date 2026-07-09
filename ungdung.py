#mới đây nha

import streamlit as st
from rdflib import Graph, Namespace
import pandas as pd
from collections import Counter
import plotly.express as px
from deep_translator import GoogleTranslator
import re
# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Drug ADE Knowledge Graph Explorer",
    page_icon="💊",
    layout="wide"
)
# =========================================================
# NGÔN NGỮ & DỊCH THUẬT (TRANSLATION MODULE)
# =========================================================
# Khởi tạo trạng thái ngôn ngữ mặc định
if "lang" not in st.session_state:
    st.session_state.lang = "vi"

LANG_UI = {
    "vi": {
        "label": "🌐 Ngôn ngữ",
        "vi": "Tiếng Việt",
        "en": "Tiếng Anh"
    },
    "en": {
        "label": "🌐 Language",
        "vi": "Vietnamese",
        "en": "English"
    }
}

lang_ui = LANG_UI[st.session_state.lang]

# Cập nhật ngôn ngữ (đã xóa tham số 'key' để tránh xung đột làm mất dấu đỏ)
selected_lang = st.sidebar.radio(
    label=lang_ui["label"],
    options=["vi", "en"], 
    format_func=lambda x: lang_ui[x], 
    index=0 if st.session_state.lang == "vi" else 1
)

# NẾU PHÁT HIỆN THAY ĐỔI NGÔN NGỮ -> CẬP NHẬT VÀ TẢI LẠI TRANG NGAY LẬP TỨC
if st.session_state.lang != selected_lang:
    st.session_state.lang = selected_lang
    st.rerun()
#  # Dùng st.experimental_rerun() nếu bạn xài Streamlit phiên bản cũ
# Hàm dịch thuật có sử dụng cache để tối ưu tốc độ
@st.cache_data(show_spinner=False)
def translate_text(text, target_lang):
    if not text or target_lang == "en":
        return text
    try:
        # Dịch tự động từ ngôn ngữ bất kỳ sang ngôn ngữ đích (vi)
        return GoogleTranslator(source='auto', target=target_lang).translate(str(text))
    except Exception as e:
        return text  # Nếu lỗi mạng/API thì trả về text gốc

# Hàm bọc ngắn gọn để dùng ở khắp mọi nơi trong code
def _t(text):
    return translate_text(text, st.session_state.lang)

# =========================================================
# LOAD KNOWLEDGE GRAPH
# =========================================================
@st.cache_resource(show_spinner=_t("Đang tải Knowledge Graph..."))
def load_graph():
    g = Graph()
    try:
        g.parse("drug_ade_kg.ttl", format="turtle")
    except Exception as e:
        st.error(_t("Không tìm thấy file 'drug_ade_kg.ttl' hoặc file bị lỗi định dạng."))
    return g

g = load_graph()
EX = Namespace("http://example.org/")


# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown("""
<style>
.main { background-color: #F8FAFC; }
h1, h2, h3 { color: #1E3A8A; }
.block-container { padding-top: 2rem; }
.metric-card { background-color: white; padding: 12px; border-radius: 10px; border: 1px solid #E5E7EB; }
.evidence-box { background-color: #F9FAFB; color: #111827; padding: 15px; border-radius: 10px; border-left: 5px solid #2563EB; margin-bottom: 15px; }
.rdf-box { background-color: #111827; color: #F9FAFB; padding: 15px; border-radius: 10px; margin-top: 10px; margin-bottom: 20px; font-size: 14px; }
</style>
""", unsafe_allow_html=True)



# =========================================================
# CAUSALITY ASSESSMENT (ĐÃ CẬP NHẬT LỖI CAPSACIAN/LIPITOR)
# =========================================================
def assess_causality(sentence, ade_name):
    sentence = str(sentence).lower()
    ade = str(ade_name).lower().strip()
    CAUSAL = "CAUSAL"
    INDICATION = "INDICATION"
    UNCERTAIN = "UNCERTAIN"
    
    # 0. BỘ LỌC NGOẠI LỆ (EXCEPTIONS / OVERRIDES)
    # Cập nhật ngoại lệ cho trường hợp Capsacian (Capsaicin) và Lipitor
    if ("capsacian" in sentence or "capsaicin" in sentence) and ("burning feet" in ade or "neuropathy" in ade):
        return INDICATION # Capsacian dùng để ĐIỀU TRỊ triệu chứng này
        
    if "lipitor" in sentence and ("burning feet" in ade or "neuropathy" in ade):
        return CAUSAL # Lipitor GÂY RA triệu chứng này
        
    if "clonidine" in sentence and "bring down bp" in sentence and "headache" in ade:
        return INDICATION
    if "for high bp" in sentence and "high bp" in ade:
        return INDICATION
    if "for high blood pressure" in sentence and "high blood pressure" in ade:
        return INDICATION
    
    

    if "safer" in sentence and ade in sentence:
        return INDICATION
    if "no aspirin" in sentence and ade in sentence:
        return INDICATION
        
    if "cortisone" in sentence and ("went away" in sentence or "didn't respond" in sentence):
        return INDICATION
        
    if "for inflamation" in sentence and "inflamation" in ade:
        return INDICATION
    # 0. BỘ LỌC NGOẠI LỆ (EXCEPTIONS / OVERRIDES)
    # Thêm 2 dòng này để xử lý câu "eliminated the pain" và cụm "cause of my pain"
    if "eliminated" in sentence:
        return INDICATION
    if "cause of my" in sentence and ade in sentence:
        return INDICATION

    # Các bộ lọc cũ của bạn giữ nguyên bên dưới...
    if ("capsacian" in sentence or "capsaicin" in sentence) and ("burning feet" in ade or "neuropathy" in ade):
        return INDICATION # Capsacian dùng để ĐIỀU TRỊ triệu chứng này
    # THÊM MỚI TẠI ĐÂY: Xử lý các câu mang ý nghĩa phủ định (không có triệu chứng) 
    # hoặc bị cắt cụt vế sau
    if "no symptoms" in sentence:
        return UNCERTAIN
    # THÊM MỚI TẠI ĐÂY: Xử lý cấu trúc "taking [thuốc] for [triệu chứng]" (VD: taking gasx for bloating)
    if f"for {ade}" in sentence or f"for my {ade}" in sentence or f"to treat {ade}" in sentence:
        return INDICATION

    # Xử lý các câu mang ý nghĩa phủ định (không có triệu chứng) hoặc bị cắt cụt vế sau
    if "no symptoms" in sentence:
        return UNCERTAIN
    # Các ngoại lệ hiện tại của bạn giữ nguyên bên dưới...
    if ("capsacian" in sentence or "capsaicin" in sentence) and ("burning feet" in ade or "neuropathy" in ade):
        return INDICATION # Capsacian dùng để ĐIỀU TRỊ triệu chứng này
    # 1. TỪ KHÓA TÁC DỤNG PHỤ (Causal / True ADE Keywords)
    # 1. TỪ KHÓA TÁC DỤNG PHỤ (Xóa "is gone", "disappeared", "have lifted", "has left")
    # 1. TỪ KHÓA TÁC DỤNG PHỤ (Causal / True ADE Keywords)
    # THÊM MỚI TẠI ĐÂY: Xử lý cấu trúc "waiting to see if"
    if "waiting to see if" in sentence and ade in sentence:
        return UNCERTAIN

    # Xử lý cấu trúc "taking [thuốc] for [triệu chứng]" (VD: taking gasx for bloating)
    if f"for {ade}" in sentence or f"for my {ade}" in sentence or f"to treat {ade}" in sentence:
        return INDICATION
    causal_keywords = [
        "upset my", "upset by", "gave me", "caused", "resulted in", "side effect", "side effects",
        "gastro effects", "made me", "developed with", "experienced", 
        "linked to", "days on it", "severe abdominal pain",
        "reaction to", "reacted", "allergic to", "started having", "brought on",
        "like it did with", "cause", "thought this was the cause", "thought it was",
        "was back", "came back", "returned", "switch from", "switched from", "stopped because",
        "stopped taken", "stopped taking", "is not good", "been off drug", "off the drug", 
        "symptoms of", "khiến tôi bị", 
        "gây ra", "liên quan đến", "tác dụng phụ", "triệu chứng khó chịu", "phản ứng với", 
        "bắt đầu xuất hiện", "gây nhạy cảm", "nguyên nhân",
        "induce", "induced", "sudden onset" # <--- THÊM 3 TỪ KHÓA MỚI NÀY VÀO CUỐI
    ]

    # 2. TỪ KHÓA CHỈ ĐỊNH / BỆNH LÝ NỀN (Thêm "eliminated", "is gone", "disappeared",...)
    indication_keywords = [
        "prescribed for", "for my", "to treat", "diagnosed with", "suffering from",
        "combat the", "to combat", "due to my", "history of", "to relieve", "quell the",
        "greatly reduced", "took away my", "works very well for", "works better for",
        "helped it", "take advil", "take aleve", "put me on", 
        "relieved with", "offset the", "diminish", "protector for", "protect against", "reduce", "to reduce",
        "to bring down", "because of", "trying to eleviate", "eleviate", "alleviate", "prescribed",
        "for high bp", "for high blood pressure", "to bring down bp", "for inflamation", "went away",
        "được kê đơn để", "điều trị", "dập tắt tình trạng", "để thử và chống lại",
        "vì tôi bị", "giảm chứng", "chống lại cơn đau", "bác sĩ cho tôi dùng",
        "eliminated", "is gone", "disappeared", "have lifted", "has left" # <--- THÊM MỚI TẠI ĐÂY
    ]

    # 3. TỪ KHÓA THUỐC KHÔNG CÓ TÁC DỤNG (Ineffective)
    ineffective_keywords = [
        "didn't help", "did not help", "didn't work", "wasn't touching", "didn't respond",
        "no relief", "still hurts", "doesn't work", "did nothing for",
        "relieve any", "no aleve", "no effect at all",
        "không có tác dụng", "không làm tôi giảm", "không thể uống thuốc giảm đau", 
        "hoàn toàn không có tác dụng", "không giúp tôi giảm"
    ]
    
    if ade not in sentence:
        for cause in causal_keywords:
            if re.search(r'\b' + re.escape(cause) + r'\b', sentence):
                return CAUSAL
        for ind in indication_keywords + ineffective_keywords:
            if re.search(r'\b' + re.escape(ind) + r'\b', sentence):
                return INDICATION
        return UNCERTAIN

    # HÀM TÍNH KHOẢNG CÁCH NÂNG CAO
    def get_min_distance(keywords, is_indication=False):
        min_dist = float('inf')
        
        ade_pattern = r'\b' + re.escape(ade) + r'\b'
        ade_positions = [m.start() for m in re.finditer(ade_pattern, sentence)]
        if not ade_positions:
            ade_positions = [m.start() for m in re.finditer(re.escape(ade), sentence)]
            
        strong_indicators = [
            "because of", "to bring down", "prescribed", "diagnosed with", 
            "trying to eleviate", "eleviate", "alleviate", "for high", "for inflamation",
            "went away", "didn't respond"
        ]

        for kw in keywords:
            kw_pattern = r'\b' + re.escape(kw) + r'\b'
            kw_positions = [m.start() for m in re.finditer(kw_pattern, sentence)]
            
            for k_pos in kw_positions:
                for a_pos in ade_positions:
                    dist = abs(a_pos - k_pos)
                    
                    if is_indication and kw in strong_indicators:
                        dist = dist * 0.2  
                        
                    if dist < min_dist:
                        min_dist = dist
        return min_dist

    dist_causal = get_min_distance(causal_keywords, is_indication=False)
    dist_ind = get_min_distance(indication_keywords, is_indication=True)
    dist_ineff = get_min_distance(ineffective_keywords, is_indication=True)

    min_all = min(dist_causal, dist_ind, dist_ineff)

    if min_all == float('inf'):
        return UNCERTAIN

    MAX_DISTANCE_THRESHOLD = 120

    if dist_causal == min_all:
        if dist_causal > MAX_DISTANCE_THRESHOLD:
            return UNCERTAIN
        return CAUSAL
    else:
        if min_all > MAX_DISTANCE_THRESHOLD:
            return UNCERTAIN
        return INDICATION

CAUSALITY_LABELS = {
    "vi": {
        "CAUSAL": "✅ Phản ứng tác dụng phụ",
        "INDICATION": "❌ Bệnh lý nền",
        "UNCERTAIN": "⚠️ Không chắc chắn/ Cần xác minh thêm"
    },
    "en": {
        "CAUSAL": "✅ side effects",
        "INDICATION": "❌ Underlying condition",
        "UNCERTAIN": "⚠️ Unsure/Needs further verification"
    }
}
# =========================================================
# HELPER FUNCTIONS
# =========================================================
def normalize_name(name):
    return str(name).replace("_", " ").title()

def render_rdf_path(drug, ade, confidence, sentence, source_post):
    # GIỮ NGUYÊN TOÀN BỘ CÂU, KHÔNG CẮT NGẮN NỮA
    full_sentence = str(sentence)

    return f"""(Drug) {drug}
 └── [hasDrug] ──> (TreatmentEvent)
      ├── [hasAdverseEvent] ──> (ADE) {ade}
      └── [hasRelation] ────> (DrugADERelation)
           ├── [confidenceScore] ──> {confidence}
           └── [hasEvidence] ──────> (Evidence)
                ├── [sourcePostID] ──> {source_post}
                └── [sentenceText]
                    \"\"\"{full_sentence}\"\"\"
"""
# =========================================================
# LOAD ENTITY SETS
# =========================================================
@st.cache_data
def extract_entities():
    d_set = sorted({normalize_name(str(s).split("Drug_")[-1]) for s, p, o in g if "Drug_" in str(s)})
    a_set = sorted({normalize_name(str(s).split("ADE_")[-1]) for s, p, o in g if "ADE_" in str(s)})
    return d_set, a_set

drug_set, ade_set = extract_entities()

# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.markdown("## 👋 " + _t("Welcome to the Graduation Thesis"))
    st.markdown("---")
    st.success(_t("EXTRACTING ADVERSE DRUG REACTIONS FROM MEDICAL FORUMS AND CONSTRUCTING DRUG-SIDE EFFECT KNOWLEDGE GRAPHS"))
    st.markdown("---")
    st.markdown("## 📌 " + _t("Modules"))
    st.write("🔍 " + _t("Drug Search"))
    # st.write("⚠️ " + _t("Risk Analysis"))
    # st.write("❓ " + _t("KG Question Answering"))
    st.markdown("---")
    st.caption("🎓 Huỳnh Xuân Nam - 64131375 - Graduation Thesis - 2026")

# =========================================================
# HEADER
# =========================================================
st.title("💊 " + _t("Knowledge Graph Drug–observed adverse"))



# =========================================================
# GLOBAL METRICS
# =========================================================
col1, col2, col3 = st.columns(3)
col1.metric(_t("Total RDF Triples"), len(g))
col2.metric(_t("Total Drugs"), len(drug_set))
col3.metric(_t("Total ADEs"), len(ade_set))
st.markdown("---")

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "🔍 " + _t("Drug Search"),
    " " + _t(""),
    " " + _t("")
])

# =========================================================
# TỪ ĐIỂN PHÂN LOẠI NHÓM THUỐC (DRUG CATEGORIES)
# =========================================================
# Phân loại các thuốc bạn đã cung cấp vào các nhóm tương ứng
DRUG_CATEGORIES = {
    

    "thuốc cảm": [
    "allegra",
    "rhinocort",
    "steroid nasal sprays",
    "flu jab"
]
    ,
      # =========================
    # 1. THUỐC GIẢM ĐAU (opioid + paracetamol + codeine)
    # =========================
    "thuốc giảm đau": [
        "paracetamol", "tylenol 3", "co-codamol", "co codamol",
        "morphine", "codeine", "vicodine", "darvacet", "darvocet",
        "demerol", "zipsor", "capsaicin", "capsacian",
        "flexeril", "relafen", "relefen","pamprin"
    ],

    # =========================
    # 2. THUỐC KHÁNG VIÊM (NSAIDs + steroid)
    # =========================
    "thuốc kháng viêm": [
        "ibuprofen",
        "aspirin", "asprin",
        "aleve",
        "cataflam", "voltaren", "voltaren-xr", "voltaren rapid",
        "celebrex", "mobic", "naproxen",
        "prednisone",
        "cortisone shot", "cortisone shots", "cortison shots",
        "enbrel injections"
    ],

    # =========================
    # 3. THUỐC DẠ DÀY
    # =========================
    "thuốc dạ dày": [
        "gas-x", "gasx",
        "tums",
        "zantac",
        "nexium",
        "prilosec",
        "arthrotec", "arthotec", "arthrotec 50"
    ],

    # =========================
    # 4. THUỐC MỠ MÁU (statins + fibrates + lipid agents)
    # =========================
    "thuốc mỡ máu": [
        "lipitor", "lipitor 20mg", "lipitor atorvastatin", "lipitor's",
        "atorvastatin",
        "statins", "satin",
        "simvastatin", "simvostatin",
        "pravachol", "provachol", "pravastatin",
        "crestor", "zocor", "mevacor",
        "lopid", "lopids",
        "tricor", "tricor",
        "gemfibrosil",
        "zetia",
        "vitorin",
        "baycol", "baycor",
        "lipidil", "lipidil micro",
        "lipex",
        "simcor",
        "lopid"
    ],

    # =========================
    # 5. THUỐC HUYẾT ÁP / TIM MẠCH
    # =========================
    "thuốc huyết áp": [
        "clonidine",
        "vasotec",
        "norvasc", "amlodiphine",
        "toprol", "metoptolol",
        "prinivil", "ramipril",
        "diovan",
        "bisoprolol",
        "cozaar",
        "atacand",
        "noten",
        "lasiks",
        "niacin"
    ],

    # =========================
    # 6. NỘI TIẾT / ĐÁI THÁO ĐƯỜNG
    # =========================
    "thuốc nội tiết ": [
        "avandia",
        "actose",
        "glyburide",
        "insalin",
        "thyroid",
        "testosterone",
        "testonrone",
        "estrace",
        "estratest"
    ],

    # =========================
    # 7. THUỐC THẦN KINH / TÂM THẦN
    # =========================
    "thuốc thần kinh": [
        "cymbalta",
        "neurontin",
        "gabapentin",
        "zoloft", "zorloft",
        "lexapro",
        "effexor",
        "trazadone",
        "ambien",
        "melatonin"
    ],

    # =========================
    # 8. THỰC PHẨM CHỨC NĂNG / SUPPLEMENTS
    # =========================
    "thực phẩm chức năng": [
        "vitamin c crystals", "vit c",
        "b complex",
        "folic acid",
        "magnesium orotate",
        "potassium",
        "chlorella",
        "alpha lipoic acid",
        "coq10", "co q 10", "coenzyme q10", "coenzyme10", "cq10", "q10",
        "fish oil", "fish oils", "fish oil salmon",
        "flaxseed",
        "st john's wort",
        "saw palmetto",
        "glucosamine", "glucoasamine", "glucosamine sulfate",
        "chondroitin",
        "msm",
        "caffeine"
    ],
    
    # =========================
    # 9. THUỐC KHÁC / KHÁNG SINH
    # =========================
    "thuốc kháng sinh": [
        "antibiotic",
    ]
}



# cũ mà đúng
# def get_target_drugs(keyword):
#     """Hàm xác định xem người dùng nhập nhóm thuốc hay 1 thuốc cụ thể"""
#     keyword_lower = keyword.lower().strip()
#     # Nếu từ khóa khớp với tên nhóm, trả về toàn bộ danh sách thuốc trong nhóm đó
#     for cat_name, drugs in DRUG_CATEGORIES.items():
#         if keyword_lower == cat_name:
#             return drugs
#     # Nếu không phải nhóm, xem như người dùng tra 1 loại thuốc cụ thể
#     return [keyword_lower]


# Bản đồ ánh xạ: Hỗ trợ tiếng Anh và tiếng Việt cùng trỏ về 1 nhóm
CATEGORY_ALIASES = {
    # Tiếng Anh
    "painkillers": "thuốc giảm đau",
    # "pain reliever": "thuốc giảm đau",
    "cold medicine": "thuốc cảm",
    "anti-inflammatory": "thuốc kháng viêm",
    "stomach medicine": "thuốc dạ dày",
    # "stomach": "thuốc dạ dày",
    "blood lipid": "thuốc mỡ máu",
    # "cholesterol": "thuốc mỡ máu",
    # "blood pressure": "thuốc huyết áp",
    "hypertension": "thuốc huyết áp",
    # "dietary supplements": "thực phẩm chức năng",
    "supplements": "thực phẩm chức năng",
    "psychiatric drugs": "thuốc thần kinh",
    # "mental health": "thuốc thần kinh",
    
    # Tiếng Việt (Alias nếu bạn muốn người dùng nhập tắt)
    "giảm đau": "thuốc giảm đau",
    "kháng viêm": "thuốc kháng viêm",
    "cảm": "thuốc cảm",
    "dạ dày": "thuốc dạ dày",
    "mỡ máu": "thuốc mỡ máu",
    "huyết áp": "thuốc huyết áp",
    "thực phẩm chức năng": "thực phẩm chức năng",
    "thần kinh": "thuốc thần kinh"
}

def get_target_drugs(keyword):
    """
    Hàm xác định danh sách thuốc dựa trên từ khóa (hỗ trợ Alias).
    """
    if not keyword:
        return []
        
    k = keyword.lower().strip()
    
    # 1. Kiểm tra trong Alias (để xử lý tiếng Anh/Từ khóa tắt)
    if k in CATEGORY_ALIASES:
        target_cat = CATEGORY_ALIASES[k]
        return DRUG_CATEGORIES.get(target_cat, [])
    
    # 2. Kiểm tra trực tiếp trong Category (nếu nhập đúng tên nhóm)
    if k in DRUG_CATEGORIES:
        return DRUG_CATEGORIES[k]
    
    # 3. Nếu không thuộc nhóm nào, trả về danh sách chứa đúng từ khóa đó
    # (Để hệ thống tìm kiếm 1 loại thuốc cụ thể)
    return [k]

# =========================================================
# UI_LABELS = {
#     "Nhập tên thuốc:": {"vi": "Nhập tên thuốc:", "en": "Enter drug name:"},
#     "Gợi ý": {"vi": "Gợi ý", "en": "Suggestions"},
#     "Search Drug Effects": {"vi": "Tìm kiếm", "en": "Search Drug Effects"},
#     # Thêm các nhãn khác vào đây...
#     "MSG_FOUND_SINGLE": {
#         "vi": "Đã tìm thấy",
#         "en": "Found {n} ADE and drug: {drug}"
#     }
# }

UI_LABELS = {
    "Nhập tên thuốc:": {"vi": "Nhập tên thuốc:", "en": "Enter drug name:"},
    "Gợi ý": {"vi": "Gợi ý", "en": "Suggestions"},
    "Search Drug Effects": {"vi": "Tìm kiếm", "en": "Search Drug Effects"},
    "MSG_FOUND_MULTI": {
        "vi": "Đã tìm thấy ADEs với thuốc",
        "en": "Found ADE and drug"
    },
    "MSG_FOUND_SINGLE": {
        "vi": "Đã tìm thấy ADE với thuốc",
        "en": "Found ADE and drug"
    },
    # --- THÊM MỚI TỪ ĐÂY ---
    "Phân loại": {"vi": "Phân loại", "en": "Causality Status"},
    "thuốc giảm đau": {"vi": "thuốc giảm đau", "en": "painkillers"},
    "thuốc kháng viêm": {"vi": "thuốc kháng viêm", "en": "anti-inflammatory"},
    "thuốc cảm": {"vi": "thuốc cảm", "en": "cold medicine"},
    "thuốc dạ dày": {"vi": "thuốc dạ dày", "en": "stomach medicine"},
    "thực phẩm chức năng": {"vi": "thực phẩm chức năng", "en": "supplements"},
    "thuốc thần kinh": {"vi": "thuốc thần kinh", "en": "psychiatric drugs"},
    "thuốc huyết áp": {"vi": "thuốc huyết áp", "en": "hypertension"},
    
    "PURPOSE_TEXT": {
        "vi": """
Module này cung cấp giao diện tương tác để tìm kiếm thuốc và khám phá các phản ứng có hại (ADE) được trích xuất từ đồ thị tri thức RDF...
""",
        "en": """
This module provides an interactive interface for searching drugs and exploring adverse drug events (ADEs) extracted from the RDF knowledge graph...
"""
    },
    "FEATURE_TEXT": {
        "vi": """
- Tìm kiếm tác dụng phụ theo thuốc gây ra  
- Minh hoạ truy vết đường dẫn RDF  
- Thống kê tần suất tác dụng phụ 
- Danh sách bằng chứng phản ứng tác dụng phụ  
- Xuất dữ liệu CSV  
""",
        "en": """
- Search ADE by drug effects causes 
- Illustration of RDF path tracing
- Show side effects frequency statistics  
- List of side effects evidence 
- Export CSV data  
"""
    }
}

# def _t(text):
#     # Trả về giá trị trong từ điển nếu có, nếu không thì trả về text gốc
#     if text in UI_LABELS:
#         return UI_LABELS[text].get(st.session_state.lang, text)
#     return text

def _t(key, **kwargs):
    # 1. Kiểm tra trong từ điển UI_LABELS trước
    if key in UI_LABELS:
        text = UI_LABELS[key].get(st.session_state.lang, key)
    # 2. Nếu không có trong từ điển, sử dụng GoogleTranslator (như cách cũ của bạn)
    else:
        text = translate_text(key, st.session_state.lang)
    
    # 3. Nếu có truyền tham số (kwargs), thực hiện format chuỗi
    if kwargs:
        return text.format(**kwargs)
    return text
# TAB 1 — DRUG SEARCH
# =========================================================
# =========================================================
# TAB 1 — DRUG SEARCH
# =========================================================
with tab1:
    st.header("🔍 " + _t("Drug search interface and commonly observed adverse reaction"))
    
    st.markdown(f"""
    ### 🎯 {_t("Purpose")}

    {_t("PURPOSE_TEXT")}

    ---

    ### ⚙️ {_t("Features")}

    {_t("FEATURE_TEXT")}
    """)
    TOP_K = 1

    # 1. Khởi tạo session_state để lưu lại từ khóa tìm kiếm (TRÁNH MẤT DỮ LIỆU KHI RERUN)
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""

    # Giao diện Nhập tay
    user_input = st.text_input(
        "🔍 " + _t("Nhập tên thuốc:"), 
       
    )

    # # 2. Hiển thị gợi ý trên 1 hàng ngang bằng st.caption hoặc st.markdown
    # st.markdown(
    #     """
    #     <div style="margin-top: -10px; margin-bottom: 15px; font-size: 13px; color: #64748b;">
    #         <b>Gợi ý:</b> <i>thuốc giảm đau, thuốc kháng viêm, thuốc cảm, thuốc dạ dày, thực phẩm chức năng, thuốc thần kinh, thuốc tim mạch huyết áp</i>
    #     </div>
    #     """, 
    #     unsafe_allow_html=True
    # )
    # 1. Định nghĩa danh sách gợi ý theo ngôn ngữ
    suggestions_data = {
        "vi": ["thuốc giảm đau", "thuốc kháng viêm", "thuốc cảm", "thuốc dạ dày", "thực phẩm chức năng", "thuốc thần kinh", "thuốc huyết áp"],
        "en": ["painkillers", "anti-inflammatory", "cold medicine", "stomach medicine", "supplements", "psychiatric drugs", "hypertension"]
    }
    
    # 2. Lấy danh sách gợi ý dựa trên ngôn ngữ hiện tại
    current_suggestions = suggestions_data.get(st.session_state.lang, suggestions_data["vi"])
    suggestion_str = ", ".join(current_suggestions)
    
    # 3. Hiển thị (Sử dụng _t() để dịch nhãn "Gợi ý")
    # st.markdown(
    #     f"""
    #     <div style="margin-top: -10px; margin-bottom: 15px; font-size: 13px; color: #64748b;">
    #         <b>{_t("Gợi ý")}:</b> <i>{suggestion_str}</i>
    #     </div>
    #     """, 
    #     unsafe_allow_html=True
    # )
    st.markdown(
    f"""
    <div style="margin-top: -10px; margin-bottom: 15px; font-size: 17px; color: #64748b;">
        <b>{_t("Gợi ý")}:</b> <i>{suggestion_str}</i>
    </div>
    """, 
    unsafe_allow_html=True
    )

    # 2. Cập nhật từ khóa vào session_state khi bấm nút
    if st.button(_t("Search Drug Effects")):
        if not user_input.strip():
            st.warning(_t("Vui lòng nhập tên thuốc!"))
            st.session_state.search_query = "" # Reset nếu rỗng
        else:
            st.session_state.search_query = user_input.strip()

    # 3. Chạy logic hiển thị dựa trên session_state thay vì dựa vào if st.button
    if st.session_state.search_query:
        query = st.session_state.search_query
        # Lấy danh sách thuốc dựa trên từ khóa đã lưu
        target_drugs = get_target_drugs(query)
        
        results = []
        evidence_rows = []

        # =====================================================
        # RDF TRAVERSAL CHO TỪNG THUỐC TRONG DANH SÁCH
        # =====================================================
        for d in target_drugs:
            normalized_drug = d.replace(" ", "_")
            drug_uri = EX["Drug_" + normalized_drug]

            for event_uri, _, _ in g.triples((None, EX.hasDrug, drug_uri)):
                for _, _, ade_uri in g.triples((event_uri, EX.hasAdverseEvent, None)):
                    ade_name = normalize_name(str(ade_uri).split("ADE_")[-1])
                    results.append(ade_name)

                    for _, _, relation_uri in g.triples((event_uri, EX.hasRelation, None)):
                        confidence = "N/A"
                        for _, _, conf in g.triples((relation_uri, EX.confidenceScore, None)):
                            confidence = str(conf)

                        source_post = "Unknown"
                        for _, _, post in g.triples((relation_uri, EX.sourcePostID, None)):
                            source_post = str(post)

                        for _, _, evidence_uri in g.triples((relation_uri, EX.hasEvidence, None)):
                            sentence_text = "No evidence sentence available"
                            for _, _, sent in g.triples((evidence_uri, EX.sentenceText, None)):
                                sentence_text = str(sent)

                            # Cập nhật logic dịch và đánh giá
                            translated_ade = _t(ade_name)
                            translated_sentence = _t(sentence_text)

                            # ---> GỌI HÀM ĐÁNH GIÁ TẠI ĐÂY <---
                            # causality_status = assess_causality(sentence_text)
                            # ---> GỌI HÀM ĐÁNH GIÁ TẠI ĐÂY <---
                            # causality_status = assess_causality(sentence_text, ade_name)
                            raw_status = assess_causality(sentence_text, ade_name)

                            causality_status = CAUSALITY_LABELS[st.session_state.lang][raw_status]

                            evidence_rows.append({
                                _t("Search Query"): _t(query), # Hàm _t giờ sẽ dùng UI_LABELS để dịch chính xác nhóm thuốc
                                # _t("Drug"): _t(d.title()), cái này có dịch tiếng viet
                                _t("Drug"): d.title(),
                                _t("ADE"): translated_ade,
                                _t("Phân loại"): causality_status,  # <--- Đổi "Phân loại" thành _t("Phân loại")
                                _t("Evidence Sentence"): translated_sentence,
                                _t("Confidence"): confidence,
                                _t("Source Post"): source_post,
                                "RDF Path": render_rdf_path(d.title(), ade_name, confidence, sentence_text, source_post)
                            })

        # Lọc trùng lặp danh sách ADE
        results = sorted(list(set(results)))
                # =========================
      
        # if results:
        #     if len(target_drugs) > 1:
        #         # st.success(_t(f"Đã tìm thấy {len(results)} ADEs cho nhóm: {query} ({len(target_drugs)} loại thuốc)"))
        #         st.success(_t(f"Đã tìm thấy "))
        #     else:
        #         # st.success(_t(f"Tìm thấy {len(results)} ADEs cho thuốc: {target_drugs[0].title()}"))
        #          st.success(_t(f"Đã tìm thấy "))
        if results:
            if len(target_drugs) > 1:
                # Gọi với key và tham số (kwargs)
                st.success(_t("MSG_FOUND_MULTI", 
                            count=len(results), 
                            query=query, 
                            num_drugs=len(target_drugs)))
            else:
                # Gọi với key và tham số
                st.success(_t("MSG_FOUND_SINGLE", 
                            count=len(results), 
                            drug=target_drugs[0].title()))

            # =================================================
            # METRICS
            # =================================================
            m1, m2, m3 = st.columns(3)
            # m1.metric(_t("Total Unique ADEs"), len(results))
            # m2.metric(_t("Total Evidence Found"), len(evidence_rows))

            # avg_conf = 0
            # try:
            #     conf_values = [float(r[_t("Confidence")]) for r in evidence_rows if r[_t("Confidence")] != "N/A"]
            #     if conf_values:
            #         avg_conf = round(sum(conf_values) / len(conf_values), 2)
            # except:
            #     avg_conf = 0
            # m3.metric(_t("Average Confidence"), avg_conf)

            # st.markdown("---")

            # =================================================
            # EVIDENCE VIEWER 
            # =================================================
            # =================================================
            # EVIDENCE VIEWER 
            # =================================================
            st.markdown("---")

            # =================================================
            # RDF PATH VIEWER
            # =================================================
            st.subheader("🧾 " + _t("Illustrative example of an RDF Path"))

            # Sắp xếp theo độ tin cậy để lấy kết quả tốt nhất làm mặc định
            def get_conf(x):
                try: return float(x.get(_t("Confidence"), 0))
                except: return 0
            
            evidence_rows = sorted(evidence_rows, key=get_conf, reverse=True)

            # Hiển thị RDF Path cho từng kết quả tìm thấy
            for i, row in enumerate(evidence_rows[:1], start=1): # Chỉ hiển thị 5 kết quả đầu tiên để tránh tràn trang
               
                    # st.code(row.get("RDF Path", ""), wrap_lines=True)
                    st.code(row.get("RDF Path", ""), language="text", wrap_lines=True)

            # =========================
            # FULL TABLE SECTION
            # =========================
            st.subheader("📑 " + _t("List of side effects of the medication"))

            # Checkbox lọc kết quả chuẩn
            # Tạo chuỗi cho Checkbox tùy theo ngôn ngữ
            checkbox_label = "🎯 Chỉ hiển thị phản ứng tác dụng phụ được xác nhận (✅)" if st.session_state.lang == "vi" else "🎯 Only show confirmed adverse reactions (✅)"
            filter_true_ade = st.checkbox(checkbox_label, value=False)

            evidence_df = pd.DataFrame(evidence_rows).drop_duplicates()
            if "RDF Path" in evidence_df.columns:
                display_df = evidence_df.drop(columns=["RDF Path"])
            else:
                display_df = evidence_df
           

            display_df = evidence_df.drop(columns=["RDF Path"])

            # Lấy tên cột "Phân loại" đã được dịch
            col_causality = _t("Phân loại")
            
            # Lấy giá trị chính xác của nhãn "CAUSAL" (Phản ứng phụ) theo ngôn ngữ hiện tại
            target_label = CAUSALITY_LABELS[st.session_state.lang]["CAUSAL"]

            # Lọc DataFrame nếu người dùng tích vào Checkbox
            if filter_true_ade and col_causality in display_df.columns:
                display_df = display_df[display_df[col_causality] == target_label]
            # Giao diện Minimalist hiện đại - Đã canh chỉnh thẳng hàng
            # Giao diện Minimalist hiện đại - Đã canh chỉnh thẳng hàng
            modern_css = """
            <style>
            /* Làm tiêu đề giống "Purpose" nổi bật hơn */
            .stTabs [data-baseweb="tab-panel"] h2,
            .stTabs [data-baseweb="tab-panel"] h3 {
                font-size: 26px !important;
                font-weight: 800 !important;
                color: #1E3A8A !important;
            }
            /* Tùy chỉnh thanh cuộn */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 4px; }
            ::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 4px; }
            ::-webkit-scrollbar-thumb:hover { background: #a8a8a8; }

            .table-wrapper {
                max-height: 600px;
                overflow: auto;
                border: 1px solid #E5E7EB !important; /* Thêm lại viền mỏng để bảng có khung rõ ràng */
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                background-color: white;
                margin-bottom: 20px;
            }
            
            .modern-table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                table-layout: fixed; /* QUAN TRỌNG: Khóa layout để chia tỷ lệ % cố định */
            }
            
            /* CĂN CHỈNH HEADER (TIÊU ĐỀ BẢNG) */
            .modern-table thead th {
                position: sticky;
                top: 0;
                background-color: #F9FAFB;
                color: #4B5563; 
                font-size: 12px;
                font-weight: 600; 
                text-transform: uppercase;
                letter-spacing: 0.05em;
                padding: 12px 10px; 
                border-bottom: 2px solid #E5E7EB;
                z-index: 1;
                text-align: left; 
            }
            
            /* CĂN CHỈNH DỮ LIỆU BÊN TRONG */
            .modern-table tbody td {
                padding: 12px 10px; 
                font-size: 14px;
                color: #374151;
                border-bottom: 1px solid #F3F4F6;
                vertical-align: middle; /* Căn giữa theo chiều dọc cho đều và đẹp */
                line-height: 1.5;
                word-wrap: break-word; /* Tự động xuống dòng đúng cách */
                overflow-wrap: break-word;
            }
            
            .modern-table tbody tr:hover {
                background-color: #F8FAFC;
            }

            /* CHIA TỶ LỆ CỘT CỤ THỂ (Tổng 100%) - Dành cho 7 cột */
            .modern-table th:nth-child(1), .modern-table td:nth-child(1) { width: 12%; } /* Search Query */
            .modern-table th:nth-child(2), .modern-table td:nth-child(2) { width: 10%; } /* Drug */
            .modern-table th:nth-child(3), .modern-table td:nth-child(3) { width: 13%; } /* ADE */
            .modern-table th:nth-child(4), .modern-table td:nth-child(4) { width: 16%; } /* Causality Status */
            .modern-table th:nth-child(5), .modern-table td:nth-child(5) { width: 31%; } /* Evidence Sentence */
            .modern-table th:nth-child(6), .modern-table td:nth-child(6) { width: 8%; }  /* Confidence */
            .modern-table th:nth-child(7), .modern-table td:nth-child(7) { width: 10%; } /* Source Post */
            </style>
            """
            
            st.markdown(modern_css, unsafe_allow_html=True)
            html_table = display_df.to_html(classes="modern-table", index=False, escape=True)
            st.markdown(f'<div class="table-wrapper">{html_table}</div>', unsafe_allow_html=True)
            st.subheader("📊 " + _t("Statistical showing the number of reactive ADEs"))

            if not display_df.empty:
                ade_col = _t("ADE")

                if ade_col in display_df.columns:
                    ade_table_counts = (
                        display_df[ade_col]
                        .value_counts()
                        .reset_index()
                    )
                    ade_table_counts.columns = ["ADE", "Count"]

                    top_table_ades = ade_table_counts.head(10)

                    fig2 = px.bar(
                        top_table_ades,
                        x="ADE",
                        y="Count",
                        title=_t("Count the number of ADEs that appear in the table"),
                        text="Count"
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            # =========================
            # EXPORT
            # =========================
            csv = display_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=" " + _t("Export CSV results"),
                data=csv,
                file_name="drug_ade_evidence.csv",
                mime="text/csv"
            )
        else:
            st.warning(_t("No ADEs found for this input in the Knowledge Graph."))
with tab2:

    st.header("⚠️ Patient-Based Drug Risk Analysis")

    

    st.markdown("""
    ### 🎯 Purpose  
This module provides personalized drug risk assessment for an individual patient by integrating knowledge graph-based adverse drug event (ADE) evidence 
with patient-specific clinical attributes such as age, gender, and underlying disease.The system aims to support explainable clinical decision-making by estimating how risky a drug is for a specific patient profile.



   
### ⚙️ Features  
- 👤 Show the entire interface patient profile modeling (age, gender, underlying disease)  
- 📊 Rule-based risk scoring and high-risk alerts  
- 📋 Displays analyzed list of drug–adverse drug reaction (ADE) risk associations  
- 🔗 Confidence-weighted Knowledge Graph integration for risk computation  
- 🧾 Explainable risk reasoning for patient-specific adverse reaction interpretation
    """)

    col1, col2 = st.columns(2)

    with col1:
        drug_choice = st.selectbox("Select Drug", drug_set, key="tab2_drug_select")

    with col2:
        drug_input = st.text_input("Or Enter Drug Name", placeholder="e.g. Arthrotec")

    drug = drug_input.strip() if drug_input.strip() else drug_choice

    col1, col2, col3 = st.columns(3)

    with col1:
        condition = st.selectbox(
            "Underlying Disease",
            ["Digestive Disease", "Musculoskeletal Disease"]
        )

    with col2:
        gender = st.selectbox("Gender", ["Male", "Female"])

    with col3:
        age = st.number_input("Age", 0, 120, 25)

    # =========================
    # AGE GROUP
    # =========================
    if age < 18:
        age_group = "Child"
    elif age <= 40:
        age_group = "Adult"
    elif age <= 60:
        age_group = "Middle"
    else:
        age_group = "Elderly"

    st.info(f"""
👤 Patient Profile:
- Drug: {drug}
- Gender: {gender}
- Age: {age} ({age_group})
- Condition: {condition}
""")

    if st.button("Analyze Risk"):

        normalized_drug = drug.lower().replace(" ", "_")
        drug_uri = EX["Drug_" + normalized_drug]

        results = []

        seen_ade = {}
        st.subheader("📋 Drug List Display Table - ADE")
        for event_uri, _, _ in g.triples((None, EX.hasDrug, drug_uri)):

            for _, _, ade_uri in g.triples((event_uri, EX.hasAdverseEvent, None)):

                ade_name = normalize_name(str(ade_uri).split("ADE_")[-1])

                # =========================
                # KG CONFIDENCE + EVIDENCE
                # =========================
                confidence_score = 0.0
                evidence_sentence = None

                for _, _, relation_uri in g.triples((event_uri, EX.hasRelation, None)):

                    for _, _, conf in g.triples((relation_uri, EX.confidenceScore, None)):
                        try:
                            confidence_score = float(conf)
                        except:
                            confidence_score = 0.0

                    for _, _, evidence_uri in g.triples((relation_uri, EX.hasEvidence, None)):
                        for _, _, sent in g.triples((evidence_uri, EX.sentenceText, None)):
                            evidence_sentence = str(sent)

                # ❌ bỏ luôn nếu không có evidence
                if not evidence_sentence:
                    continue

                # =========================
                # BASE RISK
                # =========================
                # =========================
                # NORMALIZED RISK SCORING
                # =========================

                risk_score = 0.0
                reasons = set()   # tránh trùng reasoning

                # =========================
                # BASE KG SCORE (normalized)
                # =========================
                base_score = 0.6 + (confidence_score * 0.8)
                risk_score += base_score

                # =========================
                # PATIENT FACTORS (WEIGHTED)
                # =========================
                if condition == "Digestive Disease":
                    if any(x in drug.lower() for x in ["ibuprofen", "aspirin", "arthrotec"]):
                        risk_score += 0.8
                        reasons.add("Patient has digestive disease → NSAID increases GI risk")

                if condition == "Musculoskeletal Disease":
                    if "steroid" in drug.lower():
                        risk_score += 0.5
                        reasons.add("Musculoskeletal condition + steroid → interaction risk")

                if age_group == "Elderly":
                    risk_score += 0.5
                    reasons.add("Elderly patient → higher drug sensitivity")

                elif age_group == "Child":
                    risk_score += 0.4
                    reasons.add("Pediatric patient → increased pharmacological sensitivity")

                

                # =========================
                # ADE SEMANTIC FACTORS
                # =========================
                ade_lower = ade_name.lower()

                if "pain" in ade_lower:
                    risk_score += 0.3
                    reasons.add("ADE: pain-related adverse effect")

                if "cramp" in ade_lower:
                    risk_score += 0.4
                    reasons.add("ADE: cramping-related adverse effect")

                if "bleed" in ade_lower:
                    risk_score += 0.9
                    reasons.add("ADE: bleeding is high-risk complication")

                # =========================
                # EVIDENCE FACTORS
                # =========================
                ev = evidence_sentence.lower()

                if "pain" in ev:
                    risk_score += 0.2
                    reasons.add("Evidence mentions pain symptoms")

                if "cramp" in ev:
                    risk_score += 0.3
                    reasons.add("Evidence reports cramping")

                if "bleed" in ev or "stool" in ev:
                    risk_score += 0.8
                    reasons.add("Evidence indicates possible bleeding event")

                # =========================
                # NORMALIZE SCORE (IMPORTANT FIX)
                # =========================
                risk_score = min(risk_score, 4.0)   # cap để tránh phình score

                # =========================
                # RISK LEVEL (CALIBRATED)
                # =========================
                if risk_score >= 3.0:
                    risk_level = "🔴 HIGH"
                elif risk_score >= 2.0:
                    risk_level = "🟠 MEDIUM"
                else:
                    risk_level = "🟢 LOW"

                # =========================
                # 🔥 MERGE DUPLICATES BY ADE
                # =========================
                


                if ade_name in seen_ade:
                    # keep highest risk only
                    if risk_score > seen_ade[ade_name]["Risk Score"]:
                        seen_ade[ade_name] = {
                            "Drug": drug,
                            "ADE": ade_name,
                            "Confidence Score": round(confidence_score, 3),
                            "Risk Score": round(risk_score, 2),
                            "Risk Level": risk_level,
                            "Evidence": evidence_sentence,
                            "Reasoning": reasons
                        }
                else:
                    seen_ade[ade_name] = {
                        "Drug": drug,
                        "ADE": ade_name,
                        "Confidence Score": round(confidence_score, 3),
                        "Risk Score": round(risk_score, 2),
                        "Risk Level": risk_level,
                        "Evidence": evidence_sentence,
                        "Reasoning": reasons
                    }

        # convert dict → list
        results = list(seen_ade.values())

        # =========================
        # OUTPUT
        # =========================
        # =========================
        # OUTPUT
        # =========================
        if results:

            df = pd.DataFrame(results)

            st.success(f"Risk analysis completed for {drug}")

            st.dataframe(df, use_container_width=True)

            # =========================
            # EXPORT CSV (FIXED)
            # =========================
            csv = df.to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                label="📥 Export Drug-ADE Table (CSV)",
                data=csv,
                file_name=f"{drug}_drug_ade_report.csv",
                mime="text/csv"
            )
            # =========================
            # CHART
            # =========================
            st.subheader("📊 Risk Distribution")

            fig = px.bar(
                df,
                x="ADE",
                y="Risk Score",
                color="Risk Level",
                text_auto=True,
                title=f"Risk Profile: {drug}"
            )

            st.plotly_chart(fig, use_container_width=True)
            # =========================
      
       # =========================
        # =========================
      # =========================
        # EXPLANATION VIEW
        # =========================
        st.subheader("🧠 Example Explanation Risk Analysis:")

        df_exp = df.sort_values("Risk Score", ascending=False).head(5)

        if df_exp is None or df_exp.empty:
            st.warning(f"No risk data found for {drug}")
        else:
            for i, (_, row) in enumerate(df_exp.iterrows(), start=1):

                drug_name = row.get("Drug", "N/A")
                ade = row.get("ADE", "N/A")
                confidence = row.get("Confidence Score", "N/A")
                risk_level = row.get("Risk Level", "N/A")
                risk_score = row.get("Risk Score", "N/A")
                evidence = row.get("Evidence", "No evidence")

                reasoning = row.get("Reasoning", None)

                # =========================
                # FIX REASONING DISPLAY
                # =========================
                if isinstance(reasoning, list) and len(reasoning) > 0:
                    reasoning_text = "\n• " + "\n• ".join(reasoning)
                elif isinstance(reasoning, set) and len(reasoning) > 0:
                    reasoning_text = "\n• " + "\n• ".join(list(reasoning))
                else:
                    reasoning_text = "No specific risk factors"


                st.markdown("---")
                st.markdown(f"""
### 📌  Example {i}:

**💊 Drug:** {drug_name}  
**⚠️ ADE:** {ade}  

**🎯 Confidence Score:** {confidence}  
**📊 Risk Level:** {risk_level}  
**📈 Risk Score:** {risk_score}  

**🧠 Reasoning:**  
{reasoning_text}

**📚 Evidence:**  
{evidence}
""")

# =========================================================
# TAB 3 — KG QUESTION ANSWERING
# =========================================================
with tab3:

    st.header("❓ Knowledge Graph Question Answering")

    
    st.markdown("""
**Purpose**
This module provides a simple question-answering interface for exploring
drug–adverse event relationships from the pharmacovigilance knowledge graph.

**Example Questions**
- What adverse events are commonly associated with Arthrotec?
- Which digestive-related ADE group appears most frequently with Lipitor?
- Which drugs are commonly linked to digestive adverse events?
""")

    question = st.selectbox(
        "Select Question",
        [
            "What ADEs are associated with Arthrotec?",
            "Which ADE groups appear with Lipitor?",
            "Which drugs are linked to digestive ADEs?"
        ]
    )
#     question = st.selectbox(
#     "Select Question",
#     [
#         # Existing Queries
#         "What ADEs are associated with Arthrotec?",
#         "Which ADE groups appear with Lipitor?",
#         "Which drugs are linked to digestive ADEs?",

#         # Knowledge Discovery Queries
#         "Top drugs with highest digestive ADE risk",
#         "Most frequent ADEs in the KG",
#         "Drugs with highest average confidence score",

#     ]
# )
    if st.button("Run Query"):

    # =====================================================
    # QUESTION 1
    # =====================================================
        if "Arthrotec" in question:

            drug_uri = EX.Drug_arthrotec

            ade_list = []

            for event_uri, _, _ in g.triples(
                (None, EX.hasDrug, drug_uri)
            ):

                for _, _, ade_uri in g.triples(
                    (event_uri, EX.hasAdverseEvent, None)
                ):

                    ade_list.append(
                        normalize_name(
                            str(ade_uri).split("ADE_")[-1]
                        )
                    )

            df = pd.DataFrame({
                "ADE": sorted(set(ade_list))
            })

            st.success("Query executed successfully.")
            st.dataframe(df, use_container_width=True)

        # =====================================================
        # QUESTION 2
        # =====================================================
        elif "Lipitor" in question:

            drug_uri = EX.Drug_lipitor

            groups = []

            for event_uri, _, _ in g.triples(
                (None, EX.hasDrug, drug_uri)
            ):

                for _, _, ade_uri in g.triples(
                    (event_uri, EX.hasAdverseEvent, None)
                ):

                    for _, _, group_uri in g.triples(
                        (ade_uri, EX.belongsToGroup, None)
                    ):

                        groups.append(
                            normalize_name(
                                str(group_uri)
                                .split("Group_")[-1]
                            )
                        )

            count_data = Counter(groups)

            df = pd.DataFrame({
                "ADE Group": list(count_data.keys()),
                "Frequency": list(count_data.values())
            })

            st.success("ADE group analysis completed.")

            st.dataframe(df, use_container_width=True)

            fig = px.bar(
                df,
                x="ADE Group",
                y="Frequency",
                text_auto=True
            )

            st.plotly_chart(fig, use_container_width=True)

        # =====================================================
        # QUESTION 3
        # =====================================================
        elif "linked to digestive ADEs" in question:

            target_group = EX.Group_DigestiveSystem

            drugs = set()

            for ade_uri, _, _ in g.triples(
                (None, EX.belongsToGroup, target_group)
            ):

                for event_uri, _, _ in g.triples(
                    (None, EX.hasAdverseEvent, ade_uri)
                ):

                    for _, _, drug_uri in g.triples(
                        (event_uri, EX.hasDrug, None)
                    ):

                        drugs.add(
                            normalize_name(
                                str(drug_uri)
                                .split("Drug_")[-1]
                            )
                        )

            df = pd.DataFrame({
                "Drug": sorted(drugs)
            })

            st.success("Digestive ADE query completed.")
            st.dataframe(df, use_container_width=True)

             
    

