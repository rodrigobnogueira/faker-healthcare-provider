"""Display labels for the locale-neutral clinical values (fr_FR).

Words only: the numbers, units and reference intervals live once in
`faker_healthcare/clinical_values.py` and are never translated. The key set must match
the base catalogue exactly (`faker_healthcare/clinical_labels.py`); see
`tests/test_locales.py::TestClinicalLabelParity`.

Note that fr_FR keeps *medication* names in English by convention (see AGENTS.md); that
convention is about drug names only. Analyte and vital-sign names are translated here,
with the French enzyme abbreviations (ALAT, ASAT) rather than the English ones.
"""

CLINICAL_LABELS: dict[str, str] = {
    # Signes vitaux
    "systolic_bp": "Pression artérielle systolique",
    "diastolic_bp": "Pression artérielle diastolique",
    "heart_rate": "Fréquence cardiaque",
    "respiratory_rate": "Fréquence respiratoire",
    "temperature_c": "Température corporelle",
    "oxygen_saturation": "Saturation en oxygène",
    # Hématologie
    "haemoglobin": "Hémoglobine",
    "wbc": "Numération leucocytaire",
    "platelets": "Numération plaquettaire",
    "ferritin": "Ferritine",
    "inr": "INR (rapport international normalisé)",
    # Fonction rénale
    "sodium": "Sodium",
    "potassium": "Potassium",
    "urea": "Urée",
    "creatinine": "Créatinine",
    "egfr": "Débit de filtration glomérulaire estimé (DFGe)",
    # Fonction hépatique
    "alt": "Alanine aminotransférase (ALAT)",
    "ast": "Aspartate aminotransférase (ASAT)",
    "alkaline_phosphatase": "Phosphatases alcalines",
    "bilirubin_total": "Bilirubine totale",
    "albumin": "Albumine",
    # Métabolisme
    "fasting_glucose": "Glycémie à jeun",
    "hba1c": "Hémoglobine glyquée (HbA1c)",
    # Thyroïde
    "tsh": "Thyréostimuline (TSH)",
    "free_t4": "Thyroxine libre (T4 libre)",
    # Lipides
    "total_cholesterol": "Cholestérol total",
    "ldl": "Cholestérol LDL",
    "hdl": "Cholestérol HDL",
    "triglycerides": "Triglycérides",
    # Marqueurs inflammatoires
    "crp": "Protéine C réactive (CRP)",
    # Interprétation du résultat
    "flag_low": "Bas",
    "flag_normal": "Normal",
    "flag_high": "Élevé",
    # Consommation hebdomadaire d'alcool
    "alcohol_none": "Non-buveur",
    "alcohol_low_risk": "Risque faible",
    "alcohol_increasing_risk": "Risque croissant",
    "alcohol_higher_risk": "Risque élevé",
}
