from typing import Any

from faker.providers import BaseProvider, ElementsType

from .disease_correlations import DISEASE_CORRELATIONS


class HealthcareProvider(BaseProvider):
    """Faker provider for generating healthcare/medical fake data.

    This provider generates correlated clinical data based on medical relationships
    between diseases, symptoms, medications, and ICD-10 codes.

    MEDICAL DISCLAIMER: This data is for TESTING AND DEVELOPMENT PURPOSES ONLY.
    It should NOT be used for actual medical diagnosis, treatment, or healthcare decisions.
    """

    @property
    def diseases(self) -> tuple[str, ...]:
        """All disease names (derived from DISEASE_CORRELATIONS)."""
        return tuple(DISEASE_CORRELATIONS.keys())

    @property
    def icd10_codes(self) -> tuple[str, ...]:
        """All ICD-10 codes (derived from DISEASE_CORRELATIONS)."""
        codes = {data["icd10"] for data in DISEASE_CORRELATIONS.values()}
        return tuple(sorted(codes))

    @property
    def symptoms(self) -> tuple[str, ...]:
        """All unique symptoms across all diseases (derived from DISEASE_CORRELATIONS)."""
        all_symptoms = set()
        for data in DISEASE_CORRELATIONS.values():
            all_symptoms.update(data["symptoms"])
        return tuple(sorted(all_symptoms))

    @property
    def generic_drugs(self) -> tuple[str, ...]:
        """All unique medications (derived from DISEASE_CORRELATIONS)."""
        all_meds = set()
        for data in DISEASE_CORRELATIONS.values():
            all_meds.update(data["medications"])
        return tuple(sorted(all_meds))

    medical_specialties: ElementsType[str] = (
        "Cardiology",
        "Dermatology",
        "Endocrinology",
        "Gastroenterology",
        "Hematology",
        "Infectious Disease",
        "Nephrology",
        "Neurology",
        "Oncology",
        "Pulmonology",
        "Rheumatology",
        "Allergy and Immunology",
        "Family Medicine",
        "Internal Medicine",
        "Pediatrics",
        "Psychiatry",
        "Obstetrics and Gynecology",
        "Orthopedics",
        "Urology",
        "Ophthalmology",
        "Otolaryngology",
        "Anesthesiology",
        "Radiology",
        "Pathology",
        "Emergency Medicine",
        "General Surgery",
        "Plastic Surgery",
        "Neurosurgery",
        "Physical Medicine and Rehabilitation",
        "Vascular Surgery",
        "Thoracic Surgery",
        "Cardiac Surgery",
        "Colorectal Surgery",
        "Transplant Surgery",
        "Pediatric Surgery",
        "Neonatology",
        "Geriatrics",
        "Pain Management",
        "Palliative Care",
        "Sports Medicine",
        "Occupational Medicine",
        "Preventive Medicine",
        "Medical Genetics",
        "Nuclear Medicine",
        "Interventional Radiology",
    )

    hospital_departments: ElementsType[str] = (
        "Emergency Department",
        "Intensive Care Unit (ICU)",
        "Cardiac Care Unit (CCU)",
        "Operating Room",
        "Labor and Delivery",
        "Pediatrics",
        "Maternity Ward",
        "Oncology",
        "Radiology",
        "Laboratory",
        "Pharmacy",
        "Physical Therapy",
        "Occupational Therapy",
        "Respiratory Therapy",
        "Surgery",
        "Inpatient Ward",
        "Outpatient Clinic",
        "Psychiatric Ward",
        "Rehabilitation Unit",
        "Endoscopy Suite",
        "Neonatal Intensive Care Unit (NICU)",
        "Burn Unit",
        "Dialysis Unit",
        "Sleep Lab",
        "Wound Care Center",
        "Infusion Center",
        "Cardiology Unit",
        "Neurology Unit",
        "Medical Observation Unit",
        "Post-Anesthesia Care Unit (PACU)",
    )

    brand_drugs: ElementsType[str] = (
        "Lipitor",
        "Synthroid",
        "Prinivil",
        "Glucophage",
        "Norvasc",
        "Lopressor",
        "Prilosec",
        "Zocor",
        "Cozaar",
        "Neurontin",
        "Zoloft",
        "Prozac",
        "Effexor",
        "Lexapro",
        "Cymbalta",
        "Plavix",
        "Eliquis",
        "Ozempic",
        "Jardiance",
        "Farxiga",
        "Crestor",
        "Januvia",
        "Victoza",
        "Trulicity",
        "Mounjaro",
        "Zepbound",
        "Lantus",
        "Humalog",
        "NovoLog",
        "Toujeo",
        "Basaglar",
        "Levemir",
        "Tresiba",
        "Zestril",
        "Altace",
        "Vasotec",
        "Accupril",
        "Diovan",
        "Avapro",
        "Benicar",
        "Micardis",
        "Coreg",
        "Tenormin",
        "Inderal",
        "Lopressor",
        "Toprol XL",
        "Catapres",
        "Cardizem",
        "Procardia",
        "Norvasc",
        "Plendil",
        "DynaCirc",
        "Aldactone",
        "Lasix",
        "Bumex",
        "Demadex",
        "Zaroxolyn",
        "Cordarone",
        "Lanoxin",
        "Tambocor",
        "Rythmol",
        "Betapace",
        "Xarelto",
        "Pradaxa",
        "Savaysa",
        "Macrobid",
        "Cipro",
        "Levaquin",
        "Zithromax",
        "Biaxin",
        "Vibramycin",
        "Keflex",
        "Ceftin",
        "Rocephin",
        "Cleocin",
        "Flagyl",
        "Vancocin",
        "Zyvox",
        "Zovirax",
        "Valtrex",
        "Tamiflu",
        "Diflucan",
        "Vfend",
        "AmBisome",
        "Lamisil",
        "Wellbutrin",
        "Pristiq",
        "Remeron",
        "Pamelor",
        "Elavil",
        "Paxil",
        "Luvox",
        "Anafranil",
        "Eskalith",
        "Depakote",
        "Lamictal",
        "Tegretol",
        "Trileptal",
        "Topamax",
        "Keppra",
        "Dilantin",
        "Luminal",
        "Mysoline",
        "Vimpat",
        "Zonegran",
        "Aricept",
        "Exelon",
        "Razadyne",
        "Namenda",
        "Sinemet",
        "Mirapex",
        "Requip",
        "Azilect",
        "Eldepryl",
        "Lioresal",
        "Zanaflex",
        "Flexeril",
        "Soma",
        "Robaxin",
        "Xanax",
        "Ativan",
        "Valium",
        "Klonopin",
        "Restoril",
        "Ambien",
        "Lunesta",
        "Sonata",
        "Rozerem",
        "Belsomra",
        "Ritalin",
        "Concerta",
        "Focalin",
        "Vyvanse",
        "Strattera",
        "Intuniv",
        "Abilify",
        "Seroquel",
        "Zyprexa",
        "Risperdal",
        "Geodon",
        "Invega",
        "Latuda",
        "Haldol",
        "Thorazine",
        "Trilafon",
        "Flomax",
        "Proscar",
        "Avodart",
        "Viagra",
        "Cialis",
        "Levitra",
        "Ditropan",
        "Detrol",
        "Vesicare",
        "Enablex",
        "Slow-Fe",
        "Folvite",
        "Nascobal",
        "Rocaltrol",
        "Caltrate",
        "Zantac",
        "Pepcid",
        "Nexium",
        "Prevacid",
        "Aciphex",
        "Zyloprim",
        "Colcrys",
        "Benemid",
        "Uloric",
        "Krystexxa",
        "Celebrex",
        "Voltaren",
        "Indocin",
        "Toradol",
        "Feldene",
        "OxyContin",
        "Vicodin",
        "MS Contin",
        "Duragesic",
        "Tylenol #3",
        "Dilaudid",
        "Opana",
        "Dolophine",
        "Suboxone",
        "Narcan",
        "Advair",
        "Symbicort",
        "Spiriva",
        "Singulair",
        "Dulera",
        "ProAir",
        "Ventolin",
        "Xopenex",
        "Flovent",
        "Pulmicort",
        "Keytruda",
        "Opdivo",
        "Yervoy",
        "Tecentriq",
        "Imfinzi",
        "Humira",
        "Enbrel",
        "Remicade",
        "Stelara",
        "Cosentyx",
        "Dupixent",
        "Xolair",
        "Skyrizi",
        "Tapeze" + "ntis",
        "Entyvio",
    )

    blood_types: ElementsType[str] = (
        "A+",
        "A-",
        "B+",
        "B-",
        "AB+",
        "AB-",
        "O+",
        "O-",
    )

    allergies: ElementsType[str] = (
        "Penicillin",
        "Peanuts",
        "Tree Nuts",
        "Shellfish",
        "Fish",
        "Milk",
        "Eggs",
        "Soy",
        "Wheat",
        "Sesame",
        "Latex",
        "Bee Sting",
        "Pollen",
        "Dust Mites",
        "Pet Dander",
        "Sulfa Drugs",
        "Aspirin",
        "Ibuprofen",
        "Codeine",
        "Morphine",
        "Contrast Dye",
        "Anesthesia",
        "Nickel",
        "Adhesive",
        "Fragrance",
        "Insect Bites",
        "Mold",
        "Cockroaches",
        "Grass",
        "Ragweed",
        "Corn",
        "Mustard",
        "Celery",
        "Lupin",
        "Sulfites",
        "MSG",
        "Red Dye",
        "Gluten",
        "Lactose",
        "Fructose",
    )

    medical_procedures: ElementsType[str] = (
        "Blood Test",
        "MRI Scan",
        "CT Scan",
        "X-Ray",
        "Ultrasound",
        "Colonoscopy",
        "Endoscopy",
        "Appendectomy",
        "Cholecystectomy",
        "C-Section",
        "Hysterectomy",
        "Knee Replacement",
        "Hip Replacement",
        "Cataract Surgery",
        "Biopsy",
        "Physical Therapy Session",
        "Electrocardiogram (ECG)",
        "Echocardiogram",
        "Vaccination",
        "Wound Debridement",
        "Angioplasty",
        "Cardiac Catheterization",
        "Coronary Artery Bypass Graft",
        "Pacemaker Insertion",
        "Defibrillator Implantation",
        "Ablation",
        "Tonsillectomy",
        "Adenoidectomy",
        "Mastectomy",
        "Lumpectomy",
        "Prostatectomy",
        "Nephrectomy",
        "Splenectomy",
        "Gastrectomy",
        "Colectomy",
        "Ileostomy",
        "Colostomy",
        "Hernia Repair",
        "Gallbladder Removal",
        "Liver Biopsy",
        "Kidney Biopsy",
        "Bone Marrow Biopsy",
        "Lymph Node Biopsy",
        "Skin Biopsy",
        "Bronchoscopy",
        "Thoracentesis",
        "Paracentesis",
        "Lumbar Puncture",
        "Joint Aspiration",
        "Epidural Injection",
        "Nerve Block",
        "Trigger Point Injection",
        "Joint Injection",
        "Botox Injection",
        "Filler Injection",
        "Laser Hair Removal",
        "Chemical Peel",
        "Microdermabrasion",
        "Dermabrasion",
        "Skin Tag Removal",
        "Mole Removal",
        "Wart Removal",
        "Cryotherapy",
        "Electrocautery",
        "Excision",
        "Incision and Drainage",
        "Suturing",
        "Stapling",
        "Skin Graft",
        "Flap Surgery",
        "LASIK Surgery",
        "Glaucoma Surgery",
        "Retinal Detachment Repair",
        "Corneal Transplant",
        "Vitrectomy",
        "Tympanoplasty",
        "Stapedectomy",
        "Cochlear Implant",
        "Rhinoplasty",
        "Septoplasty",
        "Sinus Surgery",
        "Thyroidectomy",
        "Parathyroidectomy",
        "Adrenalectomy",
        "Pancreatectomy",
        "Whipple Procedure",
        "Liver Resection",
        "Liver Transplant",
        "Kidney Transplant",
        "Heart Transplant",
        "Lung Transplant",
        "Pancreas Transplant",
        "Bone Marrow Transplant",
        "Stem Cell Transplant",
        "Dialysis",
        "Hemodialysis",
        "Peritoneal Dialysis",
        "Plasmapheresis",
        "IVIG Infusion",
        "Chemotherapy",
        "Radiation Therapy",
        "Immunotherapy",
        "Hormone Therapy",
        "Targeted Therapy",
        "CAR T-Cell Therapy",
    )

    insurance_plans: ElementsType[str] = (
        "PPO",
        "HMO",
        "EPO",
        "POS",
        "Medicare",
        "Medicaid",
        "High-Deductible Health Plan (HDHP)",
        "Private Insurance",
        "Employer-Sponsored",
        "Medicare Advantage",
        "TRICARE",
        "Veterans Affairs (VA)",
        "CHIP",
        "ACA Marketplace",
        "Medigap",
        "Medicare Part A",
        "Medicare Part B",
        "Medicare Part C",
        "Medicare Part D",
        "Dental Insurance",
        "Vision Insurance",
        "Long-Term Care Insurance",
        "Disability Insurance",
        "Critical Illness Insurance",
        "Catastrophic Insurance",
    )

    vital_signs: ElementsType[str] = (
        "Blood Pressure",
        "Heart Rate",
        "Respiratory Rate",
        "Body Temperature",
        "Oxygen Saturation",
        "Body Mass Index (BMI)",
        "Blood Glucose",
        "Pain Level",
        "Pulse",
        "Peak Flow",
    )

    def disease(self) -> str:
        """Return a random disease name."""
        return self.random_element(self.diseases)

    def icd10_code(self, disease: str | None = None) -> str:
        """Return an ICD-10 code.

        Args:
            disease: Optional disease name. If provided, returns the correct ICD-10 code for that disease.
                    If None, returns a random ICD-10 code.
        """
        if disease and disease in DISEASE_CORRELATIONS:
            return DISEASE_CORRELATIONS[disease]["icd10"]
        return self.random_element(self.icd10_codes)

    def medical_specialty(self) -> str:
        return self.random_element(self.medical_specialties)

    def hospital_department(self) -> str:
        return self.random_element(self.hospital_departments)

    def generic_drug(self) -> str:
        return self.random_element(self.generic_drugs)

    def brand_drug(self) -> str:
        return self.random_element(self.brand_drugs)

    def symptom(self, disease: str | None = None) -> str:
        """Return a symptom.

        Args:
            disease: Optional disease name. If provided, returns a symptom associated with that disease.
                    If None, returns a random symptom.
        """
        if disease and disease in DISEASE_CORRELATIONS:
            return self.random_element(DISEASE_CORRELATIONS[disease]["symptoms"])
        return self.random_element(self.symptoms)

    def disease_symptoms(self, disease: str, count: int = 3) -> list[str]:
        """Return multiple symptoms for a specific disease.

        Args:
            disease: Disease name to get symptoms for.
            count: Number of symptoms to return (1-5). Defaults to 3.
                  Will be capped at the number of available symptoms for the disease.

        Returns:
            List of symptom strings for the disease.

        Raises:
            ValueError: If disease is not found in correlations.
        """
        if disease not in DISEASE_CORRELATIONS:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")

        disease_symptoms = DISEASE_CORRELATIONS[disease]["symptoms"]
        actual_count = min(count, len(disease_symptoms))
        return self.random_elements(disease_symptoms, length=actual_count, unique=True)

    def medication(self, disease: str | None = None) -> str:
        """Return a medication.

        Args:
            disease: Optional disease name. If provided, returns a medication for that disease.
                    If None, returns a random medication.
        """
        if disease and disease in DISEASE_CORRELATIONS:
            return self.random_element(DISEASE_CORRELATIONS[disease]["medications"])
        return self.random_element(self.generic_drugs)

    def medications(self, disease: str, count: int = 2) -> list[str]:
        """Return multiple medications for a specific disease.

        Args:
            disease: Disease name to get medications for.
            count: Number of medications to return. Defaults to 2.
                  Will be capped at the number of available medications for the disease.

        Returns:
            List of medication strings for the disease.

        Raises:
            ValueError: If disease is not found in correlations.
        """
        if disease not in DISEASE_CORRELATIONS:
            raise ValueError(f"Disease '{disease}' not found in disease correlations")

        disease_meds = DISEASE_CORRELATIONS[disease]["medications"]
        actual_count = min(count, len(disease_meds))
        return self.random_elements(disease_meds, length=actual_count, unique=True)

    def diseases_by_symptom(self, symptom: str) -> list[str]:
        """Return all diseases that have a specific symptom.

        Args:
            symptom: Symptom to search for.

        Returns:
            List of disease names that include this symptom.
        """
        return [disease_name for disease_name, data in DISEASE_CORRELATIONS.items() if symptom in data["symptoms"]]

    def patient_scenario(self, disease: str | None = None) -> dict[str, Any]:
        """Generate a complete patient scenario with correlated clinical data.

        Args:
            disease: Optional specific disease. If None, a random disease is selected.

        Returns:
            Dictionary containing:
                - disease: The disease name
                - icd10: The correct ICD-10 code
                - symptoms: List of 3-5 correlated symptoms
                - medications: List of 2-3 correlated medications
                - specialty: The primary medical specialty
        """
        if disease is None:
            disease = self.disease()
        elif disease not in DISEASE_CORRELATIONS:
            raise ValueError(f"Disease '{disease}' not found in diseases list")

        disease_data = DISEASE_CORRELATIONS[disease]
        num_symptoms = self.random_int(min=1, max=min(5, len(disease_data["symptoms"])))
        num_meds = self.random_int(min=2, max=min(3, len(disease_data["medications"])))

        return {
            "disease": disease,
            "icd10": disease_data["icd10"],
            "symptoms": self.disease_symptoms(disease, count=num_symptoms),
            "medications": self.medications(disease, count=num_meds),
            "specialty": disease_data["specialty"],
        }

    def blood_type(self) -> str:
        return self.random_element(self.blood_types)

    def allergy(self) -> str:
        return self.random_element(self.allergies)

    def medical_procedure(self) -> str:
        return self.random_element(self.medical_procedures)

    def insurance_plan(self) -> str:
        return self.random_element(self.insurance_plans)

    def vital_sign(self) -> str:
        return self.random_element(self.vital_signs)

    def diagnosis(self) -> str:
        """Return a diagnosis with correlated disease and ICD-10 code."""
        disease = self.disease()
        icd10 = self.icd10_code(disease=disease)
        return f"{disease} ({icd10})"
