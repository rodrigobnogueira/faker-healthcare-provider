"""Display labels for the locale-neutral clinical values (English base catalogue).

The numbers, units and reference intervals live once in
`faker_healthcare/clinical_values.py`; this module — and its counterpart in each locale
package — carries **only the words**. Every locale must define exactly the same key set:
one key per vital sign ID, one per analyte ID, the three flag words, and the four
alcohol-intake categories. `tests/test_locales.py::TestClinicalLabelParity` fails if a
locale is missing a key or invents one, which is what stops a new analyte from shipping
translated in one language and untranslated in five.

The IDs use international spelling (`haemoglobin`) because they are locale-neutral;
this English catalogue is US English, like the rest of the base data, so its labels use
US spelling (`Hemoglobin`).
"""

CLINICAL_LABELS: dict[str, str] = {
    # Vital signs
    "systolic_bp": "Systolic Blood Pressure",
    "diastolic_bp": "Diastolic Blood Pressure",
    "heart_rate": "Heart Rate",
    "respiratory_rate": "Respiratory Rate",
    "temperature_c": "Body Temperature",
    "oxygen_saturation": "Oxygen Saturation",
    # Haematology
    "haemoglobin": "Hemoglobin",
    "wbc": "White Blood Cell Count",
    "platelets": "Platelet Count",
    "ferritin": "Ferritin",
    "inr": "INR",
    # Renal
    "sodium": "Sodium",
    "potassium": "Potassium",
    "urea": "Urea",
    "creatinine": "Creatinine",
    "egfr": "Estimated GFR (eGFR)",
    # Liver
    "alt": "Alanine Aminotransferase (ALT)",
    "ast": "Aspartate Aminotransferase (AST)",
    "alkaline_phosphatase": "Alkaline Phosphatase",
    "bilirubin_total": "Total Bilirubin",
    "albumin": "Albumin",
    # Metabolic
    "fasting_glucose": "Fasting Glucose",
    "hba1c": "Hemoglobin A1c (HbA1c)",
    # Thyroid
    "tsh": "Thyroid-Stimulating Hormone (TSH)",
    "free_t4": "Free Thyroxine (Free T4)",
    # Lipids
    "total_cholesterol": "Total Cholesterol",
    "ldl": "LDL Cholesterol",
    "hdl": "HDL Cholesterol",
    "triglycerides": "Triglycerides",
    # Inflammatory
    "crp": "C-Reactive Protein (CRP)",
    # Result flags
    "flag_low": "Low",
    "flag_normal": "Normal",
    "flag_high": "High",
    # Weekly alcohol intake categories
    "alcohol_none": "Non-drinker",
    "alcohol_low_risk": "Low risk",
    "alcohol_increasing_risk": "Increasing risk",
    "alcohol_higher_risk": "Higher risk",
}
