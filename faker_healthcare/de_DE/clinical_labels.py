"""Display labels for the locale-neutral clinical values (de_DE).

Words only: the numbers, units and reference intervals live once in
`faker_healthcare/clinical_values.py` and are never translated. The key set must match
the base catalogue exactly (`faker_healthcare/clinical_labels.py`); see
`tests/test_locales.py::TestClinicalLabelParity`.
"""

CLINICAL_LABELS: dict[str, str] = {
    # Vitalzeichen
    "systolic_bp": "Systolischer Blutdruck",
    "diastolic_bp": "Diastolischer Blutdruck",
    "heart_rate": "Herzfrequenz",
    "respiratory_rate": "Atemfrequenz",
    "temperature_c": "Körpertemperatur",
    "oxygen_saturation": "Sauerstoffsättigung",
    # Hämatologie
    "haemoglobin": "Hämoglobin",
    "wbc": "Leukozytenzahl",
    "platelets": "Thrombozytenzahl",
    "ferritin": "Ferritin",
    "inr": "INR (International Normalized Ratio)",
    # Nierenwerte
    "sodium": "Natrium",
    "potassium": "Kalium",
    "urea": "Harnstoff",
    "creatinine": "Kreatinin",
    "egfr": "Geschätzte glomeruläre Filtrationsrate (eGFR)",
    # Leberwerte
    "alt": "Alanin-Aminotransferase (ALT/GPT)",
    "ast": "Aspartat-Aminotransferase (AST/GOT)",
    "alkaline_phosphatase": "Alkalische Phosphatase",
    "bilirubin_total": "Gesamtbilirubin",
    "albumin": "Albumin",
    # Stoffwechsel
    "fasting_glucose": "Nüchternblutzucker",
    "hba1c": "Hämoglobin A1c (HbA1c)",
    # Schilddrüse
    "tsh": "Thyreoidea-stimulierendes Hormon (TSH)",
    "free_t4": "Freies Thyroxin (fT4)",
    # Blutfette
    "total_cholesterol": "Gesamtcholesterin",
    "ldl": "LDL-Cholesterin",
    "hdl": "HDL-Cholesterin",
    "triglycerides": "Triglyzeride",
    # Entzündungsmarker
    "crp": "C-reaktives Protein (CRP)",
    # Befundkennzeichnung
    "flag_low": "Niedrig",
    "flag_normal": "Normal",
    "flag_high": "Hoch",
    # Wöchentlicher Alkoholkonsum
    "alcohol_none": "Kein Alkoholkonsum",
    "alcohol_low_risk": "Geringes Risiko",
    "alcohol_increasing_risk": "Erhöhtes Risiko",
    "alcohol_higher_risk": "Hohes Risiko",
}
