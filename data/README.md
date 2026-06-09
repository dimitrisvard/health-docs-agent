# Seed Corpus — Provenance Index

Public, non-PII digital-health documents assembled for a RAG demo. All content was fetched from public APIs/websites (openFDA, ClinicalTrials.gov API v2, WHO fact sheets) and reproduced as clean markdown. No patient-level data is included. This README is intentionally ignored by the ingester.

| File | Kind | Source URL |
| --- | --- | --- |
| Metformin_Hydrochloride_Label.md | drug_label | https://api.fda.gov/drug/label.json?search=openfda.generic_name:"metformin"&limit=1 |
| Lisinopril_Label.md | drug_label | https://api.fda.gov/drug/label.json?search=openfda.generic_name:"lisinopril"&limit=1 |
| Atorvastatin_Calcium_Label.md | drug_label | https://api.fda.gov/drug/label.json?search=openfda.generic_name:"atorvastatin"&limit=1 |
| Type2Diabetes_Trial_NCT05563987.md | trial | https://clinicaltrials.gov/study/NCT05563987 |
| Hypertension_Trial_NCT00666536.md | trial | https://clinicaltrials.gov/study/NCT00666536 |
| HeartFailure_Trial_NCT01900600.md | trial | https://clinicaltrials.gov/study/NCT01900600 |
| WHO_Diabetes_Guideline.md | guideline | https://www.who.int/news-room/fact-sheets/detail/diabetes |
| WHO_Hypertension_Guideline.md | guideline | https://www.who.int/news-room/fact-sheets/detail/hypertension |

## Notes on drug-label sources
- The openFDA `limit=1` query for **metformin** returned a combination product (sitagliptin and metformin hydrochloride tablets, brand "ZITUVIMET"); excerpts feature metformin's renal/hepatic dosing, lactic-acidosis boxed warning, and metformin drug interactions.
- The openFDA `limit=1` query for **lisinopril** returned a combination product (lisinopril and hydrochlorothiazide tablets, USP); excerpts include the fetal-toxicity boxed warning and renal-impairment dosing.
- The **atorvastatin** query returned a single-ingredient atorvastatin calcium tablets, USP label.
- Per-section text was trimmed to roughly 250 words where needed; trimmed sections end with "… (excerpt)".
