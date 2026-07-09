
import re
import pandas as pd
import urllib.parse
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD
from collections import defaultdict

# ======================================================
# LOAD DATA
# ======================================================
import re

def norm_final(x):
    x = str(x).lower().strip()
    x = re.sub(r"\s+", "_", x)
    return x

df = pd.read_csv(
    "drug_ade_relations.csv",
    sep=None,
    engine="python",
    encoding="utf-8-sig"
)

print("Các cột:", df.columns.tolist())

# ======================================================
# INIT GRAPH
# ======================================================

g = Graph()
EX = Namespace("http://example.org/")
g.bind("ex", EX)

generated_triple_log = []

old_add = g.add

def add_and_log(triple):
    generated_triple_log.append(
        tuple(str(x) for x in triple)
    )
    return old_add(triple)

g.add = add_and_log
# ======================================================
# ONTOLOGY
# ======================================================

g.add((EX.Drug, RDF.type, OWL.Class))
g.add((EX.AdverseEvent, RDF.type, OWL.Class))
g.add((EX.Post, RDF.type, OWL.Class))
g.add((EX.Group, RDF.type, OWL.Class))

g.add((EX.causesADE, RDF.type, OWL.ObjectProperty))
g.add((EX.causesADE, RDFS.domain, EX.Drug))
g.add((EX.causesADE, RDFS.range, EX.AdverseEvent))

g.add((EX.mentionsDrug, RDF.type, OWL.ObjectProperty))
g.add((EX.mentionsDrug, RDFS.domain, EX.Post))
g.add((EX.mentionsDrug, RDFS.range, EX.Drug))

g.add((EX.mentionsADE, RDF.type, OWL.ObjectProperty))
g.add((EX.mentionsADE, RDFS.domain, EX.Post))
g.add((EX.mentionsADE, RDFS.range, EX.AdverseEvent))

g.add((EX.belongsToGroup, RDF.type, OWL.ObjectProperty))
g.add((EX.belongsToGroup, RDFS.domain, EX.AdverseEvent))
g.add((EX.belongsToGroup, RDFS.range, EX.Group))

g.add((EX.postID, RDF.type, OWL.DatatypeProperty))
g.add((EX.postID, RDFS.domain, EX.Post))
g.add((EX.postID, RDFS.range, XSD.string))

g.add((EX.sentenceText, RDF.type, OWL.DatatypeProperty))
g.add((EX.sentenceText, RDFS.domain, EX.Post))
g.add((EX.sentenceText, RDFS.range, XSD.string))

# ======================================================
# MAPS
# ======================================================

DRUG_MAP = {"arthotec": "arthrotec"}

ADE_MAP = {
    "bleed": "bleeding",
    "painful": "pain",
    "painfull": "pain"
}

GROUP_MAP = {
    "abdominal_pain": "DigestiveSystem",
    "stomach_pain": "DigestiveSystem",
    "abdominal_gas": "DigestiveSystem",
    "abdominal_flu_symptoms": "DigestiveSystem",
    "severe_abdominal_pain": "DigestiveSystem",
    "enlarged_liver": "DigestiveSystem",

    "muscle_pain": "MusculoskeletalSystem",
    "muscle_cramps": "MusculoskeletalSystem",
    "muscle_pain_in_the_shoulder": "MusculoskeletalSystem",
    "knee_pain": "MusculoskeletalSystem",
    "leg_pain": "MusculoskeletalSystem",
    "neck_pain": "MusculoskeletalSystem",
    "painful_stiff_joints": "MusculoskeletalSystem"
}

def normalize_drug(name):
    return DRUG_MAP.get(str(name).lower().strip(), str(name).lower().strip())

def normalize_ade(name):
    name = str(name).lower().strip()
    name = re.sub(r"\s+", "_", name)
    return ADE_MAP.get(name, name)

def safe_uri(text):
    clean = str(text)
    clean = clean.replace("\n", " ")
    clean = clean.replace("\r", " ")
    clean = clean.replace("\\", "")
    clean = clean.replace('"', '')
    clean = clean.replace("'", "")
    clean = clean.strip().replace(" ", "_")
    return urllib.parse.quote(clean)

# ======================================================
# BUILD GRAPH
# ======================================================

seen_drugs = set()
seen_ades = set()
seen_posts = set()
seen_groups = set()

post_texts = defaultdict(list)

for _, row in df.iterrows():

    if pd.isna(row["Drug"]) or pd.isna(row["ADE"]) or pd.isna(row["File"]):
        continue

    drug = normalize_drug(row["Drug"])
    ade = normalize_ade(row["ADE"])
    post = str(row["File"]).strip()

    drug_uri = EX["Drug_" + safe_uri(drug)]
    ade_uri = EX["ADE_" + safe_uri(ade)]
    post_uri = EX["Post_" + safe_uri(post)]

    if drug_uri not in seen_drugs:
        g.add((drug_uri, RDF.type, EX.Drug))
        seen_drugs.add(drug_uri)

    if ade_uri not in seen_ades:
        g.add((ade_uri, RDF.type, EX.AdverseEvent))
        seen_ades.add(ade_uri)

    if post_uri not in seen_posts:
        g.add((post_uri, RDF.type, EX.Post))
        seen_posts.add(post_uri)

    g.add((drug_uri, EX.causesADE, ade_uri))
    g.add((post_uri, EX.mentionsDrug, drug_uri))
    g.add((post_uri, EX.mentionsADE, ade_uri))

    group_name = GROUP_MAP.get(ade, "Other")
    group_uri = EX["Group_" + safe_uri(group_name)]

    if group_uri not in seen_groups:
        g.add((group_uri, RDF.type, EX.Group))
        seen_groups.add(group_uri)

    g.add((ade_uri, EX.belongsToGroup, group_uri))

    g.add((post_uri, EX.postID, Literal(post, datatype=XSD.string)))

    if "Sentence" in df.columns and not pd.isna(row["Sentence"]):
        text = str(row["Sentence"])
        text = re.sub(r"\s+", " ", text).strip()
        post_texts[post_uri].append(text)

for post_uri, lst in post_texts.items():
    g.add((post_uri, EX.sentenceText, Literal(" ".join(lst), datatype=XSD.string)))

g.serialize("drug_ade_kg2.ttl", format="turtle")

print("Tổng triples:", len(g))


# ======================================================
# 5. QUERY SUCCESS RATE (QSR)
# ======================================================



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

# ======================================================
# 1. QUERY SUCCESS RATE (QSR)
# ======================================================

def run_qsr(g, queries):
    success = 0

    for i, q in enumerate(queries):
        try:
            result = list(g.query(q))

            if len(result) > 0:
                success += 1
                print(f"Query {i+1}: SUCCESS ({len(result)})")
            else:
                print(f"Query {i+1}: EMPTY RESULT")

        except Exception as e:
            print(f"Query {i+1}: ERROR {e}")

    qsr = success / len(queries) if queries else 0
    print("\nQSR =", round(qsr, 4))
    return qsr


QSR = run_qsr(g, queries)


# ======================================================
# 2. CONSISTENCY RATE (CR)
# ======================================================

violations = 0
checks = 0

# ---- causesADE constraint ----
for s, p, o in g.triples((None, EX.causesADE, None)):
    checks += 1

    if (s, RDF.type, EX.Drug) not in g:
        violations += 1

    if (o, RDF.type, EX.AdverseEvent) not in g:
        violations += 1

# ---- belongsToGroup constraint ----
for s, p, o in g.triples((None, EX.belongsToGroup, None)):
    checks += 1

    if (s, RDF.type, EX.AdverseEvent) not in g:
        violations += 1

    if (o, RDF.type, EX.Group) not in g:
        violations += 1

CR = 1 - (violations / (checks * 2)) if checks > 0 else 0

print("\nConsistency Rate (CR) =", round(CR, 4))
print("Violations =", violations)
print("Checks =", checks * 2)


# ======================================================
# 3. DUPLICATE RATE (DR) - CORRECT VERSION
# ======================================================

# RDFLib không lưu duplicate → phải dùng log tự sinh
# if 'generated_triple_log' in globals():
#     total_gen = len(generated_triple_log)
#     unique_gen = len(set(generated_triple_log))

#     DR = (total_gen - unique_gen) / total_gen if total_gen else 0

# else:
#     DR = 0  # fallback

# print("\nDuplicate Rate (DR) =", round(DR, 4))
total_generated = len(generated_triple_log)

unique_generated = len(set(generated_triple_log))

duplicate_count = total_generated - unique_generated

DR = duplicate_count / total_generated if total_generated else 0

print("\n[Duplicate Rate - DR]")
print("Generated triples:", total_generated)
print("Unique triples:", unique_generated)
print("Duplicate triples:", duplicate_count)
print("DR =", round(DR, 4))

# ======================================================
# 4. TRIPLE PRECISION / RECALL / F1
# ======================================================

gold_df = pd.read_csv(
    "gold_standard.csv",
    encoding="utf-8-sig"
)

gold_triples = set()

for _, row in gold_df.iterrows():
    if pd.isna(row["Drug"]) or pd.isna(row["ADE"]):
        continue

    drug = normalize_drug(row["Drug"])
    ade = normalize_ade(row["ADE"])

    drug = norm_final(drug)
    ade = norm_final(ade)

    gold_triples.add((drug, "causesADE", ade))


generated_triples = set()

for s, p, o in g.triples((None, EX.causesADE, None)):
    drug = norm_final(str(s).split("Drug_")[-1])
    ade = norm_final(str(o).split("ADE_")[-1])

    generated_triples.add((drug, "causesADE", ade))


TP = len(generated_triples & gold_triples)
FP = len(generated_triples - gold_triples)
FN = len(gold_triples - generated_triples)

KGP = TP / len(generated_triples) if generated_triples else 0
KGR = TP / len(gold_triples) if gold_triples else 0
KGF1 = (2 * KGP * KGR / (KGP + KGR)) if (KGP + KGR) else 0

print("\nTriple Evaluation")
print("TP =", TP, "FP =", FP, "FN =", FN)
# print("Precision =", round(KGP, 4))
# print("Recall =", round(KGR, 4))
# print("F1 =", round(KGF1, 4))


# ======================================================
# 5. ONTOLOGY SIZE
# ======================================================

num_classes = len(set(g.subjects(RDF.type, OWL.Class)))
num_obj = len(set(g.subjects(RDF.type, OWL.ObjectProperty)))
num_data = len(set(g.subjects(RDF.type, OWL.DatatypeProperty)))

print("\nOntology Stats")
print("Triples =", len(g))
print("Classes =", num_classes)
print("Object Properties =", num_obj)
print("Datatype Properties =", num_data)
print("KGP =", round(KGP, 4))
print("KGR =", round(KGR, 4))
print("KGF1 =", round(KGF1, 4))