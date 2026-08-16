"""Display labels for the locale-neutral clinical values (es_ES).

Words only: the numbers, units and reference intervals live once in
`faker_healthcare/clinical_values.py` and are never translated. The key set must match
the base catalogue exactly (`faker_healthcare/clinical_labels.py`); see
`tests/test_locales.py::TestClinicalLabelParity`.
"""

CLINICAL_LABELS: dict[str, str] = {
    # Constantes vitales
    "systolic_bp": "Presión arterial sistólica",
    "diastolic_bp": "Presión arterial diastólica",
    "heart_rate": "Frecuencia cardíaca",
    "respiratory_rate": "Frecuencia respiratoria",
    "temperature_c": "Temperatura corporal",
    "oxygen_saturation": "Saturación de oxígeno",
    # Hematología
    "haemoglobin": "Hemoglobina",
    "wbc": "Recuento de leucocitos",
    "platelets": "Recuento de plaquetas",
    "ferritin": "Ferritina",
    "inr": "INR (razón internacional normalizada)",
    # Función renal
    "sodium": "Sodio",
    "potassium": "Potasio",
    "urea": "Urea",
    "creatinine": "Creatinina",
    "egfr": "Filtrado glomerular estimado (FGe)",
    # Función hepática
    "alt": "Alanina aminotransferasa (ALT)",
    "ast": "Aspartato aminotransferasa (AST)",
    "alkaline_phosphatase": "Fosfatasa alcalina",
    "bilirubin_total": "Bilirrubina total",
    "albumin": "Albúmina",
    # Metabolismo
    "fasting_glucose": "Glucosa en ayunas",
    "hba1c": "Hemoglobina glucosilada (HbA1c)",
    # Tiroides
    "tsh": "Hormona estimulante del tiroides (TSH)",
    "free_t4": "Tiroxina libre (T4 libre)",
    # Lípidos
    "total_cholesterol": "Colesterol total",
    "ldl": "Colesterol LDL",
    "hdl": "Colesterol HDL",
    "triglycerides": "Triglicéridos",
    # Marcadores inflamatorios
    "crp": "Proteína C reactiva (PCR)",
    # Indicadores del resultado
    "flag_low": "Bajo",
    "flag_normal": "Normal",
    "flag_high": "Alto",
    # Consumo semanal de alcohol
    "alcohol_none": "No bebedor",
    "alcohol_low_risk": "Riesgo bajo",
    "alcohol_increasing_risk": "Riesgo creciente",
    "alcohol_higher_risk": "Riesgo alto",
}
