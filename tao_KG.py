import re
import pandas as pd
import urllib.parse
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD
from collections import defaultdict

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(
    "drug_ade_relations.csv",
    sep=None,
    engine="python",
    encoding="utf-8-sig"
)

print("Các cột:", df.columns.tolist())

# =========================
# GRAPH INIT
# =========================




g = Graph()

generated_triple_log = []

old_add = g.add

def add_and_log(triple):
    generated_triple_log.append(
        tuple(str(x) for x in triple)
    )
    return old_add(triple)

g.add = add_and_log

EX = Namespace("http://example.org/")
g.bind("ex", EX)

# =========================
# CLASSES
# =========================
classes = [
    # bệnh nhân
    "Patient", 
    # thuốc
    "Drug",
    # tác dụng phụ
    "AdverseEvent",
    # sự kiện điều trị
    "TreatmentEvent",
    # ngữ cảnh xung quanh câu
    "Context",
    # nhóm
    "Group",
    # bài viết
    "Post",
    # bệnh
    "Disease",
    # triệu chứng
    "Symptom",
    # phát hiện y khoa
    "Finding",
    # nội dung câu trong bìa
    "Sentence",
    # mức độ nặng nhẹ
    "SeverityLevel",
    # nhóm thuốc
    "DrugClass",

       # bằng chứng trích xuất
    "Evidence",
    # quan hệ thuốc tác dụng phụ
    "DrugADERelation"
]

for c in classes:
    g.add((EX[c], RDF.type, OWL.Class))

# quan hệ phân cấp symtom là con finđing
g.add((EX.Symptom, RDFS.subClassOf, EX.Finding))
g.add((EX.AdverseEvent, RDFS.subClassOf, EX.Finding))

# =========================
# OBJECT PROPERTIES (mối quan hệ đối tượng)
# =========================
object_properties = [

    # có bệnh nhân
    "hasPatient",
    "hasDrug",
    "hasAdverseEvent",
    "hasContext",

    # thuộc nhóm
    "belongsToGroup",
    # có quan hệ thuốc
    "mentionsDrug",
    "mentionsADE",
    # đã trải qua sự kiện
    "experiencedEvent", 
    # ảnh hưởng nguy cơ
    "influencesRiskOf",

    # extended
    "hasSymptom",
    # có phát hiện
    "hasFinding",
    # điều trị cho bệnh
    "treatedFor",
    # có xuát hiện trong câu
    "mentionedInSentence",
    # trích từ bài viết
    "extractedFromPost",

    # gây ra tác dụng phụ
    "causesADE",
    # tham gia sự kiện
    "involvedInEvent",
    # được quan sát trong sự kiện
    "observedInEvent",
    # có liên quan triệu chứng
    "relatedSymptom",
    "relatedFinding",
    # mức độ năng nhẹ
    "hasSeverity",
    # có thuộc nhóm thuốc
    "belongsToDrugClass",

    # reverse relations
    "relatedToContext",
    "relatedDrug",
    "belongsToPost",

    # có bằng chứng 
    "hasEvidence",
    #  quan hệ tổng quát
    "hasRelation",
    # hỗ trợ quan hệ
    "supportsRelation"
]

for p in object_properties:
    g.add((EX[p], RDF.type, OWL.ObjectProperty))

# =========================
# DATA PROPERTIES
# =========================
data_properties = [

    # patient/context info
    "age",
    "gender",
    # liều dùng thuốc
    "hasDosage",
    # thời gian dùng thuốc
    "hasDuration",
    # mục đích dùng
    "purpose",
     # tình trạng trước khi dùng
    "preCondition",
#    sau khi dùng thuốc
    "postCondition",
    # mức độ phản ứng
    "reactionLevel",

    # ID bài viết
    "postID",
    # nội dung câu
    "sentenceText",

    # provenance (nguồn dữ liẹu)
    # dataset gốc
    "sourceDataset",
    # diễn đàn
    "sourceForum",
    # nguồn ID bài post
    "sourcePostID",
    # ID nội dung câu
    "sentenceID",
    # cách trích xuất 
    "extractionMethod",
    # độ tin câyk
    "confidenceScore",

    # linguistic context
    # có phủ định ko
    "negationFlag",
    # yếu tố thời gian
    "temporalCue",
    #   mức độ chắc chắn
    "certaintyLevel",

    # statistics (số lần một phản ứng được báo cáo)
    "reportCount",

    # reasoning (đánh dấu dữ liẹu hợp lệ để suy luận)
    "validObservation", 
    # ID thuốc trong RxNorm
    "rxnormID",
    # ID thuốc trong drugbankID
    "drugbankID"
]

for p in data_properties:
    g.add((EX[p], RDF.type, OWL.DatatypeProperty))



# =========================
# DOMAIN / RANGE
# =========================

# quan hệ hasDrug chỉ dùng trong ngữ cảnh và nối tới Drug (nghĩa là 1 ca điều trị có thuốc)
g.add((EX.hasDrug, RDFS.domain, EX.TreatmentEvent))
g.add((EX.hasDrug, RDFS.range, EX.Drug))

g.add((EX.hasAdverseEvent, RDFS.domain, EX.TreatmentEvent))
g.add((EX.hasAdverseEvent, RDFS.range, EX.AdverseEvent))
# ca điều trị bẹnh nhân trong ngữ cảnh nào
g.add((EX.hasPatient, RDFS.domain, EX.TreatmentEvent))
g.add((EX.hasPatient, RDFS.range, EX.Patient))

# 1 ngữ cảnh có triuej chứng gì
g.add((EX.hasSymptom, RDFS.domain, EX.Context))
g.add((EX.hasSymptom, RDFS.range, EX.Symptom))

g.add((EX.hasFinding, RDFS.domain, EX.Context))
g.add((EX.hasFinding, RDFS.range, EX.Finding))

# quan hệ nhân quả
g.add((EX.causesADE, RDFS.domain, EX.Drug))
g.add((EX.causesADE, RDFS.range, EX.AdverseEvent))


# thêm
g.add((EX.hasEvidence, RDFS.domain, EX.DrugADERelation))
g.add((EX.hasEvidence, RDFS.range, EX.Evidence))

g.add((EX.supportsRelation, RDFS.domain, EX.Evidence))
g.add((EX.supportsRelation, RDFS.range, EX.DrugADERelation))

g.add((EX.mentionedInSentence, RDFS.domain, EX.Evidence))
g.add((EX.mentionedInSentence, RDFS.range, EX.Sentence))

g.add((EX.mentionsDrug, RDFS.domain, EX.Sentence))
g.add((EX.mentionsDrug, RDFS.range, EX.Drug))

g.add((EX.mentionsADE, RDFS.domain, EX.Sentence))
g.add((EX.mentionsADE, RDFS.range, EX.AdverseEvent))
# =========================
# NORMALIZATION MAPS
# =========================
# DRUG_MAP = {
#     "arthotec": "arthrotec"
# }

DRUG_MAP = {

    # spelling variants
    "arthotec": "arthrotec",
    "advil": "ibuprofen",
    "motrin": "ibuprofen",
    "voltaren": "diclofenac",

    # lowercase normalization
    "IBUPROFEN": "ibuprofen"
}

# DRUG_MAP = {
#     # --- MISSPELL / VARIANTS ---
#     "arthotec": "Arthrotec",
#     "glucoasamine": "glucosamine",
#     "alleve": "Aleve",
#     "amlodiphine": "amlodipine",
#     "satin": "statin",
#     "lipiltor": "Lipitor",
#     "liptior": "Lipitor",
#     "liptor": "Lipitor",
#     "insalin": "insulin",
#     "actose": "Actos",
#     "cq10": "CoQ10",
#     "co q 10": "CoQ10",
#     "coenzyme10": "CoQ10",
#     "darvacet": "Darvocet",
#     "gemfibrosil": "gemfibrozil",
#     "relefen": "Relafen",
#     "codine": "codeine",
#     "provachol": "Pravachol",
#     "gasx": "Gas-X",
#     "inergy": "Vytorin",
#     "cortison shots": "cortisone shots",
#     "capsacian": "capsaicin",
#     "vitorin": "Vytorin",
#     "simvostatin": "simvastatin",
#     "baycor": "Baycol",
#     "lasiks": "Lasix",
#     "testonrone": "testosterone",
#     "trazadone": "trazodone",
#     "metoptolol": "metoprolol",
#     "zorloft": "Zoloft",
#     "asprin": "aspirin",
#     "tylonol": "Tylenol",
#     "vicodine": "Vicodin",
#     "co codamol": "co-codamol",
#     "lopids": "Lopid",

#     # --- NORMALIZATION ---
#     "ibuprofen": "ibuprofen",
#     "naproxen": "naproxen",
#     "diclofenac": "diclofenac",
#     "paracetamol": "paracetamol"
# }

# ADE_MAP = {
#     "bleed": "bleeding",
#     "painful": "pain",
#     "painfull": "pain"
# }

ADE_MAP = {

    "stomach ache": "abdominal_pain",
    "stomach pain": "abdominal_pain",
    "belly pain": "abdominal_pain",

    "throwing up": "vomiting",
    "threw up": "vomiting",

    "dizzy": "dizziness",
    "lightheaded": "dizziness"
}

# ánh xạ
DRUG_ONTOLOGY = {

    "ibuprofen": {
        "rxnorm": "5640",
        "drugbank": "DB01050"
    },

    "diclofenac": {
        "rxnorm": "2556",
        "drugbank": "DB00586"
    },

    "naproxen": {
        "rxnorm": "7258",
        "drugbank": "DB00788"
    }
}


GROUP_MAP = {

    # Digestive
    "abdominal_pain": "DigestiveSystem",
    "stomach_pain": "DigestiveSystem",
    "abdominal_gas": "DigestiveSystem",
    "abdominal_flu_symptoms": "DigestiveSystem",
    "severe_abdominal_pain": "DigestiveSystem",
    "enlarged_liver": "DigestiveSystem",
    "nausea": "DigestiveSystem",
    "vomiting": "DigestiveSystem",
    "diarrhea": "DigestiveSystem",
    "constipation": "DigestiveSystem",
    "loss_of_appetite": "DigestiveSystem",
    "indigestion": "DigestiveSystem",
    "bloating": "DigestiveSystem",

    # Musculoskeletal
    "muscle_pain": "MusculoskeletalSystem",
    "muscle_cramps": "MusculoskeletalSystem",
    "muscle_pain_in_the_shoulder": "MusculoskeletalSystem",
    "knee_pain": "MusculoskeletalSystem",
    "leg_pain": "MusculoskeletalSystem",
    "neck_pain": "MusculoskeletalSystem",
    "painfull_stiff_joints": "MusculoskeletalSystem"
}

# =========================
# SYMPTOM LIST
# =========================
SYMPTOM_LIST = [
    "fever",
    "headache",
    "dizziness",
    "fatigue",
    "nausea",
    "vomiting",
    "abdominal pain",
    "chest pain",
    "shortness of breath",
    "cough",
    "diarrhea",
    "rash",
    "itching",
    "swelling",
    "insomnia",
    "loss of appetite",
    "malaise",
    "palpitations"
]

# =========================
# FINDING LIST
# =========================
# danh sách kết quả khám , chỉ số y khoa
FINDING_LIST = [
    "hypertension",
    "hypotension",
    "tachycardia",
    "bradycardia",
    "edema",
    "inflammation",
    "abnormal lab result",
    "elevated liver enzymes",
    "elevated blood pressure",
    "decreased blood pressure",
    "increased heart rate",
    "decreased white blood cell count",
    "abnormal liver function test",
    "leukocytosis",
    "leukopenia",
    "anemia"
]

# phân loại thuốc theo nhóm
# =========================
# DRUG CLASS MAP
# =========================
DRUG_CLASS_MAP = {
    "diclofenac": "NSAID",
    "ibuprofen": "NSAID",
    "naproxen": "NSAID",
    "prednisone": "Steroid"
}

# =========================
# NORMALIZATION FUNCTIONS
# =========================
def normalize_drug(name):
    return DRUG_MAP.get(
        str(name).lower().strip(),
        str(name).lower().strip()
    )

def normalize_ade(name):
    name = str(name).lower().strip()
    name = re.sub(r"\s+", "_", name)
    name = name.replace("ade_", "")
    return ADE_MAP.get(name, name)

def safe_uri(text):
    text = str(text)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\\", "")
    text = text.replace('"', "")
    text = text.replace("'", "")

    text = text.strip().replace(" ", "_")

    return urllib.parse.quote(text)

# =========================
# STORAGE
# =========================
post_texts = defaultdict(list)
report_counter = defaultdict(int)

# =========================
# NEGATION PATTERNS
# =========================
NEG_PATTERNS = [
    r"\bno\b",
    r"\bnot\b",
    r"\bnever\b",
    r"\bwithout\b",
    r"\bdenies\b",
    r"\bdid not\b",
    r"\babsence of\b"
]

# =========================
# BUILD KG
# =========================
for idx, row in df.iterrows():

    if pd.isna(row["Drug"]) or pd.isna(row["ADE"]) or pd.isna(row["File"]):
        continue

    # =========================
    # BASIC INFO
    # =========================
    drug = normalize_drug(row["Drug"])
    ade = normalize_ade(row["ADE"])
    post = str(row["File"]).strip()

    report_counter[(drug, ade)] += 1

    # patient id
    if "PatientID" in df.columns and pd.notna(row["PatientID"]):
        patient_id = str(row["PatientID"]).strip()
    else:
        patient_id = f"Patient_{idx+1}"

    # =========================
    # URIs
    # =========================
    patient_uri = EX["Patient_" + safe_uri(patient_id)]
    drug_uri = EX["Drug_" + safe_uri(drug)]
    ade_uri = EX["ADE_" + safe_uri(ade)]
    post_uri = EX["Post_" + safe_uri(post)]

    event_id = f"{patient_id}_{drug}_{ade}"

    event_uri = EX[
        "TreatmentEvent_" + safe_uri(event_id)
    ]

    context_uri = EX[
        "Context_" + safe_uri(event_id)
    ]

    # =========================
    # TYPES
    # =========================
    g.add((patient_uri, RDF.type, EX.Patient))
    g.add((drug_uri, RDF.type, EX.Drug))
   
    g.add((ade_uri, RDF.type, EX.AdverseEvent))
    g.add((post_uri, RDF.type, EX.Post))
    g.add((event_uri, RDF.type, EX.TreatmentEvent))
    g.add((context_uri, RDF.type, EX.Context))

    # =========================
    # LABELS
    # =========================
    g.add((patient_uri, RDFS.label, Literal(patient_id)))
    g.add((drug_uri, RDFS.label, Literal(drug)))
    g.add((ade_uri, RDFS.label, Literal(ade)))
    g.add((post_uri, RDFS.label, Literal(post)))

    # =========================
    # CORE RELATIONS
    # =========================
    g.add((event_uri, EX.hasPatient, patient_uri))
    g.add((event_uri, EX.hasDrug, drug_uri))
    g.add((event_uri, EX.hasAdverseEvent, ade_uri))
    g.add((event_uri, EX.hasContext, context_uri))

    g.add((patient_uri, EX.experiencedEvent, event_uri))

    # direct semantic relation
    # =========================
    # RELATION NODE
    # =========================
    relation_uri = EX[
        "Relation_" + safe_uri(event_id)
    ]

    g.add((relation_uri, RDF.type, EX.DrugADERelation))

    g.add((relation_uri, EX.hasDrug, drug_uri))
    g.add((relation_uri, EX.hasAdverseEvent, ade_uri))

    # semantic shortcut
    g.add((drug_uri, EX.causesADE, ade_uri))

    # link event -> relation
    g.add((event_uri, EX.hasRelation, relation_uri))

    # inverse relation
    g.add((drug_uri, EX.involvedInEvent, event_uri))
    g.add((ade_uri, EX.observedInEvent, event_uri))

    # patient uses drug
    g.add((patient_uri, EX.treatedFor, drug_uri))

    
    # =========================
    # TEXT PROCESSING (FIXED)
    # =========================
    # raw_sentence = str(row.get("Sentence", "")).strip()
    # # sentence = raw_sentence.lower()
    # sentence = re.sub(r"\s+", " ", sentence.lower())
    raw_sentence = str(row.get("Sentence", "")).strip()

    sentence = re.sub(
        r"\s+",
        " ",
        raw_sentence.lower()
    )

    sentence_id = row.get(
        "SentenceID",
        f"{post}_{idx}"
    )

    sentence_uri = EX[
        "Sentence_" + safe_uri(sentence_id)
    ]

    # =========================
    # EVIDENCE NODE
    # =========================
    evidence_uri = EX[
        "Evidence_" + safe_uri(f"{event_id}_{idx}")
    ]

    g.add((evidence_uri, RDF.type, EX.Evidence))
    
    g.add((
    evidence_uri,
    EX.sentenceText,
    Literal(sentence)
    ))
   

    g.add((sentence_uri, RDF.type, EX.Sentence))
    # evidence supports relation
    g.add((relation_uri, EX.hasEvidence, evidence_uri))

    g.add((evidence_uri, EX.supportsRelation, relation_uri))

    g.add((evidence_uri, EX.mentionedInSentence, sentence_uri))

    # =========================
    # NEGATION
    # =========================
    negation_flag = any(
        re.search(pattern, sentence)
        for pattern in NEG_PATTERNS
    )

    # =========================
    # TEMPORAL
    # =========================
    # temporal_words = [
    #     "after",
    #     "before",
    #     "during",
    #     "since",
    #     "when",
    #     "within"
    # ]

    # found_temporal = [
    #     w for w in temporal_words
    #     if w in sentence
    # ]
    # =========================
    # =========================
    # TEMPORAL EXTRACTION
    # =========================

    TEMPORAL_PATTERNS = [

        # after 3 days / after two weeks
        r"(after\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|a|an)\s+(?:hour|hours|day|days|week|weeks|month|months|year|years))",

        # within 2 weeks
        r"(within\s+(?:\d+|one|two|three|four|five|a|an)\s+(?:hour|hours|day|days|week|weeks|month|months|year|years))",

        # for 5 days
        r"(for\s+(?:\d+|one|two|three|four|five|several|many|few)\s+(?:hour|hours|day|days|week|weeks|month|months|year|years))",

        # since yesterday / since starting medication
        r"(since\s+[a-zA-Z\s]+?)(?=[,.]|$)",

        # during treatment
        r"(during\s+[a-zA-Z\s]+?)(?=[,.]|$)",

        # developed after 3 days
        r"(developed\s+after\s+(?:\d+|one|two|three|four|five)\s+(?:day|days|week|weeks|month|months))",

        # started after 2 weeks
        r"(started\s+after\s+(?:\d+|one|two|three|four|five)\s+(?:day|days|week|weeks|month|months))"
    ]

    found_temporal = []

    for pattern in TEMPORAL_PATTERNS:

        matches = re.findall(pattern, sentence)

        for match in matches:

            if isinstance(match, tuple):
                found_temporal.append(match[0].strip())
            else:
                found_temporal.append(match.strip())

    found_temporal = list(set(found_temporal))

    
    # =========================
    # CERTAINTY
    # =========================
    if "may" in sentence or "might" in sentence:
        certainty = "low"

    elif "likely" in sentence:
        certainty = "medium"

    else:
        certainty = "high"

    # =========================
    # SENTENCE METADATA
    # =========================
    g.add((sentence_uri, EX.sentenceText, Literal(sentence)))
    g.add((sentence_uri, EX.mentionsDrug, drug_uri))
    g.add((sentence_uri, EX.mentionsADE, ade_uri))
    g.add((sentence_uri, EX.hasContext, context_uri))

    g.add((
        sentence_uri,
        EX.negationFlag,
        Literal(negation_flag, datatype=XSD.boolean)
    ))

    g.add((
        sentence_uri,
        EX.certaintyLevel,
        Literal(certainty)
    ))

    # =========================
    # CONTEXT LINGUISTIC INFO
    # =========================
    g.add((
        context_uri,
        EX.negationFlag,
        Literal(negation_flag, datatype=XSD.boolean)
    ))

    g.add((
        context_uri,
        EX.certaintyLevel,
        Literal(certainty)
    ))

    if found_temporal:
        g.add((
            context_uri,
            EX.temporalCue,
            Literal(",".join(found_temporal))
        ))

    # =========================
    # CONTEXT INFO
    # =========================
    if "Age" in df.columns and pd.notna(row["Age"]):

        g.add((
            context_uri,
            EX.age,
            Literal(
                int(row["Age"]),
                datatype=XSD.integer
            )
        ))

    if "Gender" in df.columns and pd.notna(row["Gender"]):

        g.add((
            context_uri,
            EX.gender,
            Literal(str(row["Gender"]).lower())
        ))

    # =========================
    # DISEASE
    # =========================
    if "Disease" in df.columns and pd.notna(row["Disease"]):

        disease = str(row["Disease"]).lower().strip()

        disease_uri = EX[
            "Disease_" + safe_uri(disease)
        ]

        g.add((disease_uri, RDF.type, EX.Disease))
        g.add((disease_uri, RDFS.label, Literal(disease)))

        g.add((context_uri, EX.treatedFor, disease_uri))

    # =========================
    # DOSAGE / DURATION
    # =========================
    if "Dosage" in df.columns and pd.notna(row["Dosage"]):

        g.add((
            context_uri,
            EX.hasDosage,
            Literal(str(row["Dosage"]))
        ))

    if "Duration" in df.columns and pd.notna(row["Duration"]):

        g.add((
            context_uri,
            EX.hasDuration,
            Literal(str(row["Duration"]))
        ))

    if "Purpose" in df.columns and pd.notna(row["Purpose"]):

        g.add((
            context_uri,
            EX.purpose,
            Literal(str(row["Purpose"]))
        ))

    # =========================
    # SEVERITY
    # =========================
    if "Severity" in df.columns and pd.notna(row["Severity"]):

        severity = str(
            row["Severity"]
        ).lower().strip()

        severity_uri = EX[
            "Severity_" + safe_uri(severity)
        ]

        g.add((severity_uri, RDF.type, EX.SeverityLevel))
        g.add((severity_uri, RDFS.label, Literal(severity)))

        g.add((context_uri, EX.hasSeverity, severity_uri))

        g.add((
            context_uri,
            EX.reactionLevel,
            Literal(severity)
        ))

    # =========================
    # DRUG CLASS
    # =========================
    drug_class = DRUG_CLASS_MAP.get(drug)

    if drug_class:

        class_uri = EX[
            "DrugClass_" + safe_uri(drug_class)
        ]

        g.add((class_uri, RDF.type, EX.DrugClass))
        g.add((class_uri, RDFS.label, Literal(drug_class)))

        g.add((drug_uri, EX.belongsToDrugClass, class_uri))


    # =========================
    # ONTOLOGY MAPPING
    # =========================
    ontology_info = DRUG_ONTOLOGY.get(drug)

    if ontology_info:

        if "rxnorm" in ontology_info:

            g.add((
                drug_uri,
                EX.rxnormID,
                Literal(ontology_info["rxnorm"])
            ))

        if "drugbank" in ontology_info:

            g.add((
                drug_uri,
                EX.drugbankID,
                Literal(ontology_info["drugbank"])
            ))

    # =========================
    # PROVENANCE
    # =========================
    source_dataset = (
        str(row["SourceDataset"])
        if "SourceDataset" in df.columns
        and pd.notna(row["SourceDataset"])
        else "Drug-ADE Forum Corpus"
    )

    source_forum = "AskaPatient"

    source_post_id = post

    sentence_id_value = str(
        row.get("SentenceID", f"{post}_{idx}")
    )

    g.add((
        relation_uri,
        EX.sourceDataset,
        Literal(source_dataset)
    ))

    g.add((
        relation_uri,
        EX.sourceForum,
        Literal(source_forum)
    ))

    g.add((
        relation_uri,
        EX.sourcePostID,
        Literal(source_post_id)
    ))

    g.add((
        relation_uri,
        EX.sentenceID,
        Literal(sentence_id_value)
    ))

    g.add((
        relation_uri,
        EX.extractionMethod,
        Literal("rule-based")
    ))

    # =========================
    # CONFIDENCE SCORE
    # =========================
     # =========================

     # =========================
    # CONFIDENCE SCORE
    # =========================

    # default confidence
    if "Confidence" in df.columns and pd.notna(row["Confidence"]):

        base_conf = float(row["Confidence"])

    else:

        base_conf = 0.70

    # =========================
    # NEGATION PENALTY
    # =========================
    if negation_flag:

        # strong penalty
        base_conf -= 0.50

    # =========================
    # CERTAINTY PENALTY
    # =========================
    if certainty == "low":

        # may / might
        base_conf -= 0.20

    elif certainty == "medium":

        # likely
        base_conf -= 0.10

    # =========================
    # SEVERITY BONUS
    # =========================
    if "Severity" in df.columns and pd.notna(row["Severity"]):

        severity_text = str(
            row["Severity"]
        ).lower().strip()

        if severity_text in [
            "severe",
            "serious",
            "critical"
        ]:

            base_conf += 0.15

        elif severity_text == "moderate":

            base_conf += 0.05

    # =========================
    # CAUSAL TRIGGER BONUS
    # =========================
    causal_triggers = [
        "caused",
        "induced",
        "triggered",
        "due to",
        "resulted in",
        "developed after"
    ]

    if any(
        trigger in sentence
        for trigger in causal_triggers
    ):

        base_conf += 0.10

    # =========================
    # TEMPORAL BONUS
    # =========================
    if found_temporal:

        base_conf += 0.05

    # =========================
    # FINAL NORMALIZATION
    # =========================
    conf = round(
        max(0.05, min(1.0, base_conf)),
        2
    )

    # save confidence
    g.add((
        relation_uri,
        EX.confidenceScore,
        Literal(conf, datatype=XSD.float)
    ))

    # =========================
    # VALID OBSERVATION
    # =========================
    # g.add((
    #     relation_uri,
    #     EX.validObservation,
    #     Literal(True, datatype=XSD.boolean)
    # ))
    is_valid = not negation_flag
    g.add((
        relation_uri,
        EX.validObservation,
        Literal(is_valid, datatype=XSD.boolean)
    ))

    # =========================
    # SYMPTOM EXTRACTION
    # =========================
    for s in SYMPTOM_LIST:
        pattern = r"\b" + re.escape(s.lower()) + r"\b"
        if re.search(pattern, sentence):

            symptom_uri = EX[
                "Symptom_" + safe_uri(s)
            ]

            g.add((symptom_uri, RDF.type, EX.Symptom))
            g.add((symptom_uri, RDFS.label, Literal(s)))

            g.add((context_uri, EX.hasSymptom, symptom_uri))

            g.add((ade_uri, EX.relatedSymptom, symptom_uri))

            # reverse relation
            g.add((symptom_uri, EX.relatedToContext, context_uri))
            g.add((symptom_uri, EX.relatedDrug, drug_uri))

    # =========================
    # FINDING EXTRACTION
    # =========================
    for f in FINDING_LIST:
        pattern = r"\b" + re.escape(f.lower()) + r"\b"
        if re.search(pattern, sentence):

            finding_uri = EX[
                "Finding_" + safe_uri(f)
            ]

            g.add((finding_uri, RDF.type, EX.Finding))
            g.add((finding_uri, RDFS.label, Literal(f)))

            g.add((context_uri, EX.hasFinding, finding_uri))

            g.add((drug_uri, EX.relatedFinding, finding_uri))

    # =========================
    # RISK RELATION
    # =========================
    if not negation_flag and certainty != "low":

        g.add((
            context_uri,
            EX.influencesRiskOf,
            ade_uri
        ))

    # =========================
    # GROUP
    # =========================
    group_name = GROUP_MAP.get(ade, "Other")

    group_uri = EX[
        "Group_" + safe_uri(group_name)
    ]

    g.add((group_uri, RDF.type, EX.Group))

    g.add((ade_uri, EX.belongsToGroup, group_uri))

    # =========================
    # POST RELATIONS
    # =========================
    g.add((post_uri, EX.mentionsDrug, drug_uri))
    g.add((post_uri, EX.mentionsADE, ade_uri))

    g.add((post_uri, EX.postID, Literal(post)))

    g.add((post_uri, EX.extractedFromPost, context_uri))

    g.add((post_uri, EX.mentionedInSentence, sentence_uri))

    g.add((context_uri, EX.belongsToPost, post_uri))

    # =========================
    # STORE POST TEXT
    # =========================
    if pd.notna(row.get("Sentence")):

        text = re.sub(
            r"\s+",
            " ",
            str(row["Sentence"])
            .replace("\n", " ")
            .replace("\r", " ")
        ).strip()

        post_texts[post_uri].append(text)

# =========================
# MERGE POST TEXT
# =========================
for post_uri, texts in post_texts.items():

    g.add((
        post_uri,
        EX.sentenceText,
        Literal(
            " ".join(texts),
            datatype=XSD.string
        )
    ))

# =========================
# REPORT STATISTICS
# =========================
for (drug, ade), count in report_counter.items():

    drug_uri = EX[
        "Drug_" + safe_uri(drug)
    ]

    ade_uri = EX[
        "ADE_" + safe_uri(ade)
    ]

    pair_uri = EX[
        "DrugADE_" + safe_uri(f"{drug}_{ade}")
    ]

    g.add((pair_uri, RDF.type, EX.TreatmentEvent))

    g.add((pair_uri, EX.hasDrug, drug_uri))

    g.add((pair_uri, EX.hasAdverseEvent, ade_uri))

    g.add((
        pair_uri,
        EX.reportCount,
        Literal(count, datatype=XSD.integer)
    ))

# =========================
# SAVE KG
# =========================
g.serialize(
    "drug_ade_kg.ttl",
    format="turtle"
)

print("Đã tạo file drug_ade_kg.ttl")
print("Tổng số triples:", len(g)) 

# ĐÁNH GIÁ KNOWLEDGE GRAPH
# =========================

def norm(x):
    return str(x).lower().strip().replace("_", " ")



def norm_final(x):
    x = str(x).lower().strip()
    x = re.sub(r"\s+", "_", x)
    return x

print("\n========== ĐÁNH GIÁ KNOWLEDGE GRAPH ==========")

# ==========================================
# 1. TỔNG SỐ TRIPLES
# ==========================================
all_triples = list(g)

tong_triples = len(all_triples)

print("Tổng số triples:", tong_triples)

# ==========================================
# 2. DUPLICATE RATE (DR)
# ==========================================
# RDFLib tự loại bỏ duplicate,
# nên phần này kiểm tra mức dư thừa logic
# ==========================================

# generated_triples = []

# for triple in all_triples:
#     generated_triples.append(triple)

# so_triples_trung = (
#     len(generated_triples)
#     - len(set(generated_triples))
# )

# duplicate_rate = (
#     so_triples_trung / len(generated_triples)
#     if len(generated_triples) > 0
#     else 0
# )

# print("\n[Duplicate Rate - DR]")
# print("Số triples trùng lặp:", so_triples_trung)

# print("DR =", round(duplicate_rate, 4))

# tỉ lệ trùng lặp triple sinh ra
# ban đàu dếm tất cả sinh ra, cái thứ 2 set chỉ lấy cái khác nhau (trung lặp bỏ)
# ==========================================
# DUPLICATE RATE (DR)
# DR = duplicate triples / total generated triples
# ==========================================

print("\n[Duplicate Rate - DR]")

total_generated = len(generated_triple_log)

unique_generated = len(set(generated_triple_log))

duplicate_count = total_generated - unique_generated

DR = (
    duplicate_count / total_generated
    if total_generated > 0
    else 0
)

print("Generated triples:", total_generated)
print("Unique triples:", unique_generated)
print("Duplicate triples:", duplicate_count)
print("DR =", round(DR,4))
# ==========================================
# CONSISTENCY RATE (CR) tỉ lệ nhất quán
# CR = 1 - (violations / checked_constraints)
# ==========================================
print("\n[Consistency Rate - CR]")

so_vi_pham = 0
tong_rang_buoc = 0

gioi_tinh_hop_le = ["male", "female", "other"]

for s, p, o in g:

    # ======================
    # AGE CHECK
    # ======================
    if p == EX.age:
        tong_rang_buoc += 1
        try:
            tuoi = int(o)
            if tuoi < 0 or tuoi > 120:
                so_vi_pham += 1
        except:
            so_vi_pham += 1

    # ======================
    # GENDER CHECK
    # ======================
    if p == EX.gender:
        tong_rang_buoc += 1
        if str(o).lower() not in gioi_tinh_hop_le:
            so_vi_pham += 1

# ======================
# EVENT VALIDATION (FIX)
# ======================
for event in g.subjects(RDF.type, EX.TreatmentEvent):

    tong_rang_buoc += 1

    co_drug = len(list(g.objects(event, EX.hasDrug))) > 0
    co_ade = len(list(g.objects(event, EX.hasAdverseEvent))) > 0

    if not co_drug or not co_ade:
        so_vi_pham += 1

CR = 1 - (so_vi_pham / tong_rang_buoc) if tong_rang_buoc > 0 else 0

print("Số ràng buộc:", tong_rang_buoc)
print("Vi phạm:", so_vi_pham)
print("CR =", round(CR, 4))

# ==========================================
# 4. TRIPLE PRECISION / RECALL / F1
# ==========================================
# Mô phỏng tập đối chiếu (gold standard)
# ==========================================
# =========================
# TẠO GOLD STANDARD
# =========================

# ==========================================
# 4. TRIPLE PRECISION / RECALL / F1
# ==========================================

print("\n========== TRIPLE EVALUATION ==========")

# ==========================================
# TẠO GOLD STANDARD
# ==========================================

# =========================
# CLEAN GOLD STANDARD (FIXED VERSION)
# =========================
# mục đích làm dữ liệu chuẩn gold stanrdas

gold_pairs = df[["Drug", "ADE"]].dropna().copy()

# normalize giống KG
gold_pairs["Drug"] = gold_pairs["Drug"].apply(normalize_drug)
gold_pairs["ADE"] = gold_pairs["ADE"].apply(normalize_ade)

# =========================
# FIX COMMON TYPOS (QUAN TRỌNG)
# =========================

DRUG_FIX = {
    "arthotec": "arthrotec",
    "provachol": "pravachol",
    "liptor": "lipitor",
    "co q 10": "coq10"
}

ADE_FIX = {
    "storke": "stroke",
    "severe_headaces": "severe_headaches",
    "heart_palpatations": "heart_palpitations",
    "inflamation": "inflammation",
    "irregullar_heartbeat": "irregular_heartbeat"
}

def fix_drug(x):
    x = str(x).lower().strip()
    return DRUG_FIX.get(x, x)

def fix_ade(x):
    x = str(x).lower().strip()
    x = re.sub(r"\s+", "_", x)
    return ADE_FIX.get(x, x)

gold_pairs["Drug"] = gold_pairs["Drug"].apply(fix_drug)
gold_pairs["ADE"] = gold_pairs["ADE"].apply(fix_ade)

# =========================
# REMOVE INVALID ENTRIES
# =========================

gold_pairs = gold_pairs[
    (gold_pairs["Drug"] != "") &
    (gold_pairs["ADE"] != "") &
    (~gold_pairs["ADE"].str.contains("shit|fuck|damn", case=False, na=False))
]

# =========================
# REMOVE DUPLICATES AGAIN
# =========================
gold_pairs = gold_pairs.drop_duplicates()

# =========================
# SAMPLE (SAFE VERSION)
# =========================

if len(gold_pairs) > 100:
    gold_pairs = gold_pairs.sample(n=100, random_state=42)

# =========================
# SAVE GOLD STANDARD
# =========================
gold_pairs["Valid"] = 1

gold_pairs.to_csv(
    "gold_standard.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Đã tạo gold_standard.csv")
print("Số cặp:", len(gold_pairs))
# ==========================================
# LOAD GOLD STANDARD
# ==========================================

gold_df = pd.read_csv(
    "gold_standard.csv",
    encoding="utf-8-sig"
)

# ==========================================
# CHỈ GIỮ TRIPLE ĐÚNG
# ==========================================

if "Valid" in gold_df.columns:

    gold_df = gold_df[
        gold_df["Valid"] == 1
    ]

# ==========================================
# GOLD TRIPLES
# ==========================================
def normalize_entity(x):
    x = str(x).lower().strip()
    x = re.sub(r"\s+", " ", x)
    x = x.replace("_", " ")
    return x


gold_triples = set()

for _, row in gold_df.iterrows():
    if pd.isna(row["Drug"]) or pd.isna(row["ADE"]):
        continue

    drug = normalize_drug(row["Drug"])
    ade = normalize_ade(row["ADE"])

    drug = norm_final(drug)
    ade = norm_final(ade)

    gold_triples.add((drug, "causesADE", ade))
# ==========================================
# GENERATED TRIPLES
# lấy từ semantic relation:
# Drug --causesADE--> ADE
# ==========================================

# generated_triples = []

# for drug_uri, _, ade_uri in g.triples(
#     (None, EX.causesADE, None)
# ):

#     # -------------------
#     # DRUG
#     # -------------------
#     drug = str(drug_uri).split("Drug_")[-1]

#     drug = urllib.parse.unquote(drug)

#     drug = drug.replace("_", " ")

#     drug = drug.lower().strip()

#     # -------------------
#     # ADE
#     # -------------------
#     ade = str(ade_uri).split("ADE_")[-1]

#     ade = urllib.parse.unquote(ade)

#     ade = ade.replace("_", " ")

#     ade = ade.lower().strip()

#     generated_triples.append(
#         (
#             drug,
#             "causesADE",
#             ade
#         )
#     )


generated_triples = set()

for drug_uri, _, ade_uri in g.triples((None, EX.causesADE, None)):

    drug = norm_final(str(drug_uri).split("Drug_")[-1])
    ade = norm_final(str(ade_uri).split("ADE_")[-1])

    generated_triples.add((drug, "causesADE", ade))
# ==========================================
# TP / FP / FN
# ==========================================

TP = len(generated_triples & gold_triples)
FP = len(generated_triples - gold_triples)
FN = len(gold_triples - generated_triples)

# ==========================================
# TRIPLE PRECISION
# KGP = đúng sinh ra / tổng sinh ra
# ==========================================

KGP = TP / len(generated_triples) if generated_triples else 0
# ==========================================
# TRIPLE RECALL
# KGR = đúng sinh ra / tổng đúng trong gold
# ==========================================

KGR = TP / len(gold_triples) if gold_triples else 0
# ==========================================
# KG F1
# ==========================================

KGF1 = (
    2 * KGP * KGR / (KGP + KGR)
    if (KGP + KGR) > 0 else 0
)

# ==========================================
# IN KẾT QUẢ
# ==========================================

print("\n========== TRIPLE EVALUATION ==========")

print("Generated triples:", len(generated_triples))

print("Gold triples:", len(gold_triples))

print("TP =", TP)

print("FP =", FP)

print("FN =", FN)

print("\n[Triple Precision - KGP]")
print("KGP =", round(KGP, 4))

print("\n[Triple Recall - KGR]")
print("KGR =", round(KGR, 4))

print("\n[KG F1]")
print("KGF1 =", round(KGF1, 4))

# ==========================================
# PRINT
# ==========================================
triple_dung_rate = (
    TP / len(gold_triples)
    if len(gold_triples) > 0
    else 0
)
print("\n========== QUERY SUCCESS RATE ==========")

queries = [

    # ======================================
    # Query 1
    # Thuốc xuất hiện nhiều nhất
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT ?drug (COUNT(?post) AS ?count)
    WHERE {
      ?post a ex:Post ;
            ex:mentionsDrug ?drug .
    }
    GROUP BY ?drug
    ORDER BY DESC(?count)
    LIMIT 10
    """,

    # ======================================
    # Query 2
    # Thuốc thường đi kèm ADE nào
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT ?drug ?ade (COUNT(?post) AS ?count)
    WHERE {
      ?post a ex:Post ;
            ex:mentionsDrug ?drug ;
            ex:mentionsADE ?ade .
    }
    GROUP BY ?drug ?ade
    ORDER BY DESC(?count)
    LIMIT 20
    """,

    # ======================================
    # Query 3
    # ADE xuất hiện với thuốc nào
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT DISTINCT ?drug
    WHERE {
      ?post a ex:Post ;
            ex:mentionsDrug ?drug ;
            ex:mentionsADE ?ade .

      FILTER(?ade = ex:ADE_nausea)
    }
    """,

    # ======================================
    # Query 4
    # Bài viết nhắc tới thuốc cụ thể
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT DISTINCT ?post ?drug ?text
    WHERE {

      ?post a ex:Post ;
            ex:mentionsDrug ex:Drug_arthrotec .

      BIND(ex:Drug_arthrotec AS ?drug)

      OPTIONAL {
          ?post ex:sentenceText ?text
      }

      FILTER NOT EXISTS {
          ?post ex:mentionsDrug ?otherDrug .
          FILTER(?otherDrug != ex:Drug_arthrotec)
      }
    }
    """,

    # ======================================
    # Query 5
    # ADE thuộc nhóm tiêu hóa/cơ-xương
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT DISTINCT ?ade
    WHERE {

      ?ade a ex:AdverseEvent .
      ?ade ex:belongsToGroup ?group .
      ?group a ex:Group .

      FILTER(
          ?group = ex:Group_DigestiveSystem ||
          ?group = ex:Group_MusculoskeletalSystem
      )
    }
    """
]
expected_min_rows = [1, 1, 1, 1, 1]
tong_query = len(queries)
query_thanh_cong = 0

for i, q in enumerate(queries):

    try:

        result = list(g.query(q))

        # query hợp lệ nếu:
        # - chạy được
        # - có ít nhất 1 dòng

        if len(result) > 0:

            query_thanh_cong += 1

    except Exception as e:

        print("Query lỗi:")
        print(e)

QSR = query_thanh_cong / tong_query if tong_query > 0 else 0

print("\nTổng query:", tong_query)

print("Query thành công:", query_thanh_cong)

print("QSR =", round(QSR, 4))
print("Tỉ lệ triple đúng =", round(triple_dung_rate, 4))

# so sánh qurery
def run_queries(query_list):
    success = 0
    total = len(query_list)

    for q in query_list:
        try:
            res = list(g.query(q))
            if len(res) > 0:
                success += 1
        except:
            pass

    return success, total, success / total if total else 0

def query_stats(query_list):

    success = 0
    total_rows = 0

    for q in query_list:

        try:
            res = list(g.query(q))

            if len(res) > 0:
                success += 1

            total_rows += len(res)

        except:
            pass

    total = len(query_list)

    qsr = success / total if total else 0

    avg_rows = total_rows / total if total else 0

    return success, total, qsr, avg_rows

simple_queries = [
    # ======================================
    # Query 1
    # Thuốc xuất hiện nhiều nhất
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT ?drug (COUNT(?post) AS ?count)
    WHERE {
      ?post a ex:Post ;
            ex:mentionsDrug ?drug .
    }
    GROUP BY ?drug
    ORDER BY DESC(?count)
    LIMIT 10
    """,

    # ======================================
    # Query 2
    # Thuốc thường đi kèm ADE nào
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT ?drug ?ade (COUNT(?post) AS ?count)
    WHERE {
      ?post a ex:Post ;
            ex:mentionsDrug ?drug ;
            ex:mentionsADE ?ade .
    }
    GROUP BY ?drug ?ade
    ORDER BY DESC(?count)
    LIMIT 20
    """,

    # ======================================
    # Query 3
    # ADE xuất hiện với thuốc nào
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT DISTINCT ?drug
    WHERE {
      ?post a ex:Post ;
            ex:mentionsDrug ?drug ;
            ex:mentionsADE ?ade .

      FILTER(?ade = ex:ADE_nausea)
    }
    """,

    # ======================================
    # Query 4
    # Bài viết nhắc tới thuốc cụ thể
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT DISTINCT ?post ?drug ?text
    WHERE {

      ?post a ex:Post ;
            ex:mentionsDrug ex:Drug_arthrotec .

      BIND(ex:Drug_arthrotec AS ?drug)

      OPTIONAL {
          ?post ex:sentenceText ?text
      }

      FILTER NOT EXISTS {
          ?post ex:mentionsDrug ?otherDrug .
          FILTER(?otherDrug != ex:Drug_arthrotec)
      }
    }
    """,

    # ======================================
    # Query 5
    # ADE thuộc nhóm tiêu hóa/cơ-xương
    # ======================================
    """
    PREFIX ex: <http://example.org/>

    SELECT DISTINCT ?ade
    WHERE {

      ?ade a ex:AdverseEvent .
      ?ade ex:belongsToGroup ?group .
      ?group a ex:Group .

      FILTER(
          ?group = ex:Group_DigestiveSystem ||
          ?group = ex:Group_MusculoskeletalSystem
      )
    }
    """
]

context_queries = [

# ==================================================
# Query 1 - Drug ADE có độ tin cậy cao
# ==================================================
"""
PREFIX ex: <http://example.org/>

SELECT ?drug ?ade ?conf
WHERE {

    ?rel a ex:DrugADERelation ;
         ex:hasDrug ?drug ;
         ex:hasAdverseEvent ?ade ;
         ex:confidenceScore ?conf .

    FILTER(?conf > 0.8)
}
ORDER BY DESC(?conf)
""",

# ==================================================
# Query 2 - Loại bỏ các câu phủ định
# ==================================================
"""
PREFIX ex: <http://example.org/>

SELECT ?drug ?ade ?neg
WHERE {

    ?sentence ex:mentionsDrug ?drug ;
              ex:mentionsADE ?ade ;
              ex:negationFlag ?neg .

    FILTER(?neg = false)
}
""",

# ==================================================
# Query 3 - ADE theo nhóm cơ quan + thống kê số lần xuất hiện
# ==================================================
"""
PREFIX ex: <http://example.org/>

SELECT
    ?group
    (COUNT(?ade) AS ?numADE)
WHERE {

    ?ade a ex:AdverseEvent ;
         ex:belongsToGroup ?group .

}
GROUP BY ?group
ORDER BY DESC(?numADE)
""",

# ==================================================
# Query 4 - ADE có ngữ cảnh thời gian
# ==================================================
"""
PREFIX ex: <http://example.org/>

SELECT ?drug ?ade ?time
WHERE {

    ?sentence ex:mentionsDrug ?drug ;
              ex:mentionsADE ?ade ;
              ex:hasContext ?context .

    ?context ex:temporalCue ?time .

    FILTER(bound(?time))
}
ORDER BY ?time
""",

# ==================================================
# Query 5 - ADE có mức độ chắc chắn cao
# ==================================================
"""
PREFIX ex: <http://example.org/>

SELECT ?drug ?ade ?certainty
WHERE {

    ?sentence ex:mentionsDrug ?drug ;
              ex:mentionsADE ?ade ;
              ex:certaintyLevel ?certainty .

    FILTER(?certainty = "high")
}
"""
]


simple_success, simple_total, simple_qsr, simple_avg = query_stats(simple_queries)

context_success, context_total, context_qsr, context_avg = query_stats(context_queries)
df_compare = pd.DataFrame({
    "Loại KG": [
        "Simple KG",
        "Context KG"
    ],
    "Số query": [
        simple_total,
        context_total
    ],
    "QSR": [
        round(simple_qsr,4),
        round(context_qsr,4)
    ],
    "Avg Results": [
        round(simple_avg,2),
        round(context_avg,2)
    ]
})

# print(df_compare)

context_features = [
    EX.confidenceScore,
    EX.negationFlag,
    EX.temporalCue,
    EX.certaintyLevel,
    EX.belongsToGroup
]

feature_count = 0

for p in context_features:

    if len(list(g.triples((None, p, None)))) > 0:
        feature_count += 1

print("Context features:", feature_count)

comparison_table = pd.DataFrame({

    "Tiêu chí": [
        "Query Success Rate",
        "Avg Results",
        "Confidence Score",
        "Negation Context",
        "Temporal Context",
        "Certainty Context",
        "Semantic Group",
        "Context Features"
    ],

    "Simple KG": [
        round(simple_qsr, 2),
        round(simple_avg, 1),
        "No",
        "No",
        "No",
        "No",
        "No",
        0
    ],

    "Context KG": [
        round(context_qsr, 2),
        round(context_avg, 1),
        "Yes",
        "Yes",
        "Yes",
        "Yes",
        "Yes",
        feature_count
    ]
})

print("\n========== SO SÁNH SIMPLE KG VÀ CONTEXT KG ==========")
print(comparison_table.to_string(index=False))


raw_entities = []
norm_entities = []

for _, row in df.iterrows():

    # DRUG
    if pd.notna(row["Drug"]):
        raw = str(row["Drug"]).strip().lower()
        norm = normalize_drug(row["Drug"])

        raw_entities.append(raw)
        norm_entities.append(norm)

    # ADE
    if pd.notna(row["ADE"]):
        raw = str(row["ADE"]).strip().lower()
        norm = normalize_ade(row["ADE"])

        raw_entities.append(raw)
        norm_entities.append(norm)

# =========================
# BASIC STATS (RAW)
# =========================
raw_total = len(raw_entities)
raw_unique = len(set(raw_entities))
raw_duplicates = raw_total - raw_unique
raw_dup_rate = raw_duplicates / raw_total if raw_total else 0

# =========================
# BASIC STATS (NORMALIZED)
# =========================
norm_total = len(norm_entities)
norm_unique = len(set(norm_entities))
norm_duplicates = norm_total - norm_unique
norm_dup_rate = norm_duplicates / norm_total if norm_total else 0

# =========================
# IMPROVEMENT METRICS (IMPORTANT FIX)
# =========================

# UNIQUE IMPROVEMENT (quan trọng nhất)
# unique_improvement = (
#     (norm_unique - raw_unique) / raw_unique
#     if raw_unique else 0
# )
# entity_reduction = (
#     (raw_unique - norm_unique)
#     / raw_unique
#     if raw_unique else 0
# )

# # DUPLICATE REDUCTION
# duplicate_reduction = (
#     (raw_dup_rate - norm_dup_rate)
#     if raw_dup_rate else 0
# )

# # ABSOLUTE DUPLICATES REDUCED
# absolute_duplicate_reduction = raw_duplicates - norm_duplicates

# # =========================
# # PRINT REPORT
# # =========================

# print("\n========== ĐÁNH GIÁ CHUẨN HÓA THỰC THỂ ==========")

# print("\n[TRƯỚC CHUẨN HÓA]")
# print(f"Tổng số thực thể      : {raw_total}")
# print(f"Số thực thể duy nhất  : {raw_unique}")
# print(f"Số thực thể trùng     : {raw_duplicates}")
# print(f"Tỷ lệ trùng lặp       : {raw_dup_rate:.4f}")

# print("\n[SAU CHUẨN HÓA]")
# print(f"Tổng số thực thể      : {norm_total}")
# print(f"Số thực thể duy nhất  : {norm_unique}")
# print(f"Số thực thể trùng     : {norm_duplicates}")
# print(f"Tỷ lệ trùng lặp       : {norm_dup_rate:.4f}")

# print("\n[MỨC CẢI THIỆN]")
# print(f"Giảm số thực thể unique : {entity_reduction:.2%}")
# print(f"Giảm duplicate rate     : {duplicate_reduction:.4f}")
# print(f"Số thực thể được gộp    : {raw_unique - norm_unique}")

total_triples = len(g)

# số class
num_classes = len(list(g.subjects(RDF.type, OWL.Class)))

# số object properties
num_object_properties = len(list(g.subjects(RDF.type, OWL.ObjectProperty)))

# số data properties
num_data_properties = len(list(g.subjects(RDF.type, OWL.DatatypeProperty)))

# tổng thực thể ontology (schema)
ontology_elements = num_classes + num_object_properties + num_data_properties

print("\n========== THỐNG KÊ ONTOLOGY ==========")

print("Tổng số triples trong KG:", total_triples)
print("Số lớp (Classes):", num_classes)
print("Số Object Properties:", num_object_properties)
print("Số Data Properties:", num_data_properties)
print("Tổng phần tử ontology (schema):", ontology_elements)


# from rdflib.namespace import RDF, OWL

print("\n===== KIỂM TRA PROPERTY =====")

all_properties = []

# ObjectProperty
for p in g.subjects(RDF.type, OWL.ObjectProperty):
    all_properties.append(("ObjectProperty", p))

# DatatypeProperty
for p in g.subjects(RDF.type, OWL.DatatypeProperty):
    all_properties.append(("DatatypeProperty", p))

result = []

for ptype, prop in all_properties:

    count = len(list(g.triples((None, prop, None))))

    status = (
        "Instance-level"
        if count > 0
        else "Schema-level only"
    )

    result.append([
        prop.split("/")[-1],
        ptype,
        count,
        status
    ])

df_check = pd.DataFrame(
    result,
    columns=[
        "Property",
        "Type",
        "TripleCount",
        "Status"
    ]
)

print(df_check.sort_values("TripleCount"))

from rdflib import URIRef

# ==========================================
# KG STATISTICS
# ==========================================

# 1. TRIPLES
num_triples = len(g)

# 2. RELATIONS
num_object_properties = len(
    list(g.subjects(RDF.type, OWL.ObjectProperty))
)

num_data_properties = len(
    list(g.subjects(RDF.type, OWL.DatatypeProperty))
)

num_relations = (
    num_object_properties +
    num_data_properties
)

# 3. ENTITIES (INSTANCE NODES)
entities = set()

for s, p, o in g:

    if isinstance(s, URIRef):
        entities.add(s)

    if isinstance(o, URIRef):
        entities.add(o)

# loại bỏ schema
classes = set(
    g.subjects(RDF.type, OWL.Class)
)

obj_props = set(
    g.subjects(RDF.type, OWL.ObjectProperty)
)

data_props = set(
    g.subjects(RDF.type, OWL.DatatypeProperty)
)

entities = entities - classes - obj_props - data_props

num_entities = len(entities)

# 4. SUCCESSFUL QUERIES
successful_queries = query_thanh_cong

# ==========================================
# PRINT
# ==========================================

print("\n========== KG thống kê ==========")

print("Entities            :", num_entities)

print("Relations           :", num_relations)

print("Triples             :", num_triples)

print("Successful Queries  :", successful_queries)

print("Total Queries       :", tong_query)

print("QSR                 :", round(QSR,4))