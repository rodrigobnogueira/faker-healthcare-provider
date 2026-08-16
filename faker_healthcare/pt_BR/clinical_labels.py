"""Display labels for the locale-neutral clinical values (pt_BR).

Words only: the numbers, units and reference intervals live once in
`faker_healthcare/clinical_values.py` and are never translated. The key set must match
the base catalogue exactly (`faker_healthcare/clinical_labels.py`); see
`tests/test_locales.py::TestClinicalLabelParity`.
"""

CLINICAL_LABELS: dict[str, str] = {
    # Sinais vitais
    "systolic_bp": "Pressão arterial sistólica",
    "diastolic_bp": "Pressão arterial diastólica",
    "heart_rate": "Frequência cardíaca",
    "respiratory_rate": "Frequência respiratória",
    "temperature_c": "Temperatura corporal",
    "oxygen_saturation": "Saturação de oxigênio",
    # Hematologia
    "haemoglobin": "Hemoglobina",
    "wbc": "Contagem de leucócitos",
    "platelets": "Contagem de plaquetas",
    "ferritin": "Ferritina",
    "inr": "INR (RNI)",
    # Função renal
    "sodium": "Sódio",
    "potassium": "Potássio",
    "urea": "Ureia",
    "creatinine": "Creatinina",
    "egfr": "Taxa de filtração glomerular estimada (TFGe)",
    # Função hepática
    "alt": "Alanina aminotransferase (ALT/TGP)",
    "ast": "Aspartato aminotransferase (AST/TGO)",
    "alkaline_phosphatase": "Fosfatase alcalina",
    "bilirubin_total": "Bilirrubina total",
    "albumin": "Albumina",
    # Metabolismo
    "fasting_glucose": "Glicemia de jejum",
    "hba1c": "Hemoglobina glicada (HbA1c)",
    # Tireoide
    "tsh": "Hormônio tireoestimulante (TSH)",
    "free_t4": "Tiroxina livre (T4 livre)",
    # Lipídios
    "total_cholesterol": "Colesterol total",
    "ldl": "Colesterol LDL",
    "hdl": "Colesterol HDL",
    "triglycerides": "Triglicerídeos",
    # Marcadores inflamatórios
    "crp": "Proteína C reativa (PCR)",
    # Sinalização do resultado
    "flag_low": "Baixo",
    "flag_normal": "Normal",
    "flag_high": "Alto",
    # Consumo semanal de álcool
    "alcohol_none": "Não bebedor",
    "alcohol_low_risk": "Baixo risco",
    "alcohol_increasing_risk": "Risco crescente",
    "alcohol_higher_risk": "Risco alto",
}
