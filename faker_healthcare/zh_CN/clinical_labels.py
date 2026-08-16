"""Display labels for the locale-neutral clinical values (zh_CN).

Words only: the numbers, units and reference intervals live once in
`faker_healthcare/clinical_values.py` and are never translated. The key set must match
the base catalogue exactly (`faker_healthcare/clinical_labels.py`); see
`tests/test_locales.py::TestClinicalLabelParity`, which also re-runs the Japanese-kana
check over these labels — a katakana drug name once reached the Simplified Chinese
catalogue that way.
"""

CLINICAL_LABELS: dict[str, str] = {
    # 生命体征
    "systolic_bp": "收缩压",
    "diastolic_bp": "舒张压",
    "heart_rate": "心率",
    "respiratory_rate": "呼吸频率",
    "temperature_c": "体温",
    "oxygen_saturation": "血氧饱和度",
    # 血液学
    "haemoglobin": "血红蛋白",
    "wbc": "白细胞计数",
    "platelets": "血小板计数",
    "ferritin": "铁蛋白",
    "inr": "国际标准化比值 (INR)",
    # 肾功能
    "sodium": "血钠",
    "potassium": "血钾",
    "urea": "尿素",
    "creatinine": "肌酐",
    "egfr": "估算肾小球滤过率 (eGFR)",
    # 肝功能
    "alt": "丙氨酸氨基转移酶 (ALT)",
    "ast": "天门冬氨酸氨基转移酶 (AST)",
    "alkaline_phosphatase": "碱性磷酸酶",
    "bilirubin_total": "总胆红素",
    "albumin": "白蛋白",
    # 代谢
    "fasting_glucose": "空腹血糖",
    "hba1c": "糖化血红蛋白 (HbA1c)",
    # 甲状腺
    "tsh": "促甲状腺激素 (TSH)",
    "free_t4": "游离甲状腺素 (FT4)",
    # 血脂
    "total_cholesterol": "总胆固醇",
    "ldl": "低密度脂蛋白胆固醇 (LDL-C)",
    "hdl": "高密度脂蛋白胆固醇 (HDL-C)",
    "triglycerides": "甘油三酯",
    # 炎症标志物
    "crp": "C反应蛋白 (CRP)",
    # 结果标记
    "flag_low": "偏低",
    "flag_normal": "正常",
    "flag_high": "偏高",
    # 每周饮酒量
    "alcohol_none": "不饮酒",
    "alcohol_low_risk": "低风险",
    "alcohol_increasing_risk": "风险增加",
    "alcohol_higher_risk": "高风险",
}
