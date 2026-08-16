"""Locale-neutral definitions for scored clinical assessments.

WHAT THIS MODULE MAY CONTAIN, AND WHY IT IS SO LITTLE
=====================================================
A generated assessment result carries **four things and no more**: the instrument's
name, a numeric score, the maximum that instrument can score, and the severity band the
score falls in.

It must NEVER carry the instrument's items, its questions, its response options, its
answer wording, or its scoring instructions — not in this module, not in a locale
package, not in a docstring, not in a test fixture, not in the README.

**Because most of these instruments are under active copyright.** A questionnaire is a
literary work: its author (or the publisher who holds the rights) controls copying,
translation and redistribution, and several of the instruments below are licensed
commercially, with translations that are separately licensed works. Reproducing the
items inside an MIT-licensed package would redistribute someone else's copyrighted text
under a licence its owner never granted, in six languages, to everyone who pips the
package.

A **score** is different in kind. "PHQ-9 = 14" is a number and a name; it is a fact
about a fictional patient, not a reproduction of the instrument, and it is what a
medical record, a research extract or a de-identification test rig actually contains —
which is what makes it the useful half for the purpose this package serves. The severity
**bands** below are the published interpretation cut-offs, which are numeric thresholds
rather than expressive content, and they are the minimum needed to label a score at all.

If you want the items, get them from the rights holder. Do not add them here, and do not
add "just the first question" as an example. A pull request that adds item text will be
closed. CONTRIBUTING.md carries the same rule.

Which instruments, and no others
--------------------------------
- **PHQ-9** — Patient Health Questionnaire, depression severity, 0-27.
- **GAD-7** — Generalised Anxiety Disorder scale, 0-21.
- **MMSE** — Mini-Mental State Examination, cognition, 0-30. **Inverted**: on this one a
  LOW score is the abnormal one, which is why `higher_is_worse` exists.
- **MADRS** — Montgomery-Åsberg Depression Rating Scale, clinician-rated, 0-60.
- **AUDIT-C** — the three-item alcohol consumption screen, 0-12.
- **CAGE** — four-item alcohol screen, 0-4.

Adding a seventh needs a maintainer decision, not just a table entry.

Classification
--------------
Conditions are named by **ICD-10** code (WHO), which is also the only classification this
package uses anywhere. Nothing here references any other diagnostic manual, and no code
or comment should introduce one.

Band sources
------------
Kroenke, Spitzer & Williams' published PHQ-9 severity cut-offs (5/10/15/20); Spitzer et
al.'s GAD-7 cut-offs (5/10/15); the conventional MMSE bands (25-30 normal, 21-24 mild,
10-20 moderate, <=9 severe); the conventional MADRS bands (0-6 symptom absent, 7-19 mild,
20-34 moderate, >=35 severe); the Public Health England AUDIT-C bands (0-4 lower risk,
5-7 increasing, 8-10 higher, 11-12 possible dependence); and CAGE's long-standing
"two or more is a positive screen".

MEDICAL DISCLAIMER: a generated score is a random number in a plausible range. It is not
an assessment of anybody, and a band label here is not a diagnosis.
"""

from .types import AssessmentInstrument


__all__ = [
    "ASSESSMENT_INSTRUMENTS",
    "ASSESSMENT_SEVERITY_TIERS",
    "CONDITION_ASSESSMENTS",
    "PSYCHIATRIC_ICD10_CHAPTER",
    "band_label_key",
    "is_clinically_significant",
]


# Every band label key used below is defined in all six clinical_labels.py files, and a
# test asserts the two sets agree. The alcohol keys are the ones `alcohol_intake_category`
# already uses: AUDIT-C bands the same risk ladder in the same words, so it reuses them
# instead of shipping a second, subtly different set of risk labels.
ASSESSMENT_INSTRUMENTS: dict[str, AssessmentInstrument] = {
    "phq9": {
        "name": "PHQ-9",
        "max_score": 27,
        "higher_is_worse": True,
        "bands": ((4, "assessment_minimal"), (9, "assessment_mild"), (14, "assessment_moderate"), (19, "assessment_moderately_severe"), (27, "assessment_severe")),
        "significant_from": 10,
    },
    "gad7": {
        "name": "GAD-7",
        "max_score": 21,
        "higher_is_worse": True,
        "bands": ((4, "assessment_minimal"), (9, "assessment_mild"), (14, "assessment_moderate"), (21, "assessment_severe")),
        "significant_from": 10,
    },
    "mmse": {
        # The inverted one: 30 is a normal examination and 0 is the worst possible score,
        # so the bands run from severe upwards and `significant_from` is a ceiling rather
        # than a floor. A generator that assumed "bigger is worse" would hand back a
        # cognitively intact score for a dementia record.
        "name": "MMSE",
        "max_score": 30,
        "higher_is_worse": False,
        "bands": ((9, "assessment_severe"), (20, "assessment_moderate"), (24, "assessment_mild"), (30, "assessment_normal_cognition")),
        "significant_from": 24,
    },
    "madrs": {
        "name": "MADRS",
        "max_score": 60,
        "higher_is_worse": True,
        "bands": ((6, "assessment_symptoms_absent"), (19, "assessment_mild"), (34, "assessment_moderate"), (60, "assessment_severe")),
        "significant_from": 20,
    },
    "audit_c": {
        "name": "AUDIT-C",
        "max_score": 12,
        "higher_is_worse": True,
        "bands": ((0, "alcohol_none"), (4, "alcohol_low_risk"), (7, "alcohol_increasing_risk"), (10, "alcohol_higher_risk"), (12, "alcohol_possible_dependence")),
        "significant_from": 5,
    },
    "cage": {
        "name": "CAGE",
        "max_score": 4,
        "higher_is_worse": True,
        "bands": ((1, "assessment_screen_negative"), (4, "assessment_screen_positive")),
        "significant_from": 2,
    },
}

# ICD-10 chapter V, mental and behavioural disorders. Used instead of the specialty
# string because "Psychiatry" is translated in all six catalogues ("Psychiatrie",
# "精神科") while the code chapter is the same everywhere — the same reason
# CONDITION_LAB_EFFECTS is keyed by code.
PSYCHIATRIC_ICD10_CHAPTER = "F"

# Which instrument a condition is actually screened or rated with, keyed by ICD-10 code.
# Same bar as every other correlation table in this package: only associations that are
# textbook for the unqualified condition. A psychiatric condition with no entry gets a
# random instrument rather than a wrong one.
#
# Deliberately absent, as worked examples of the bar:
#   * F31.9 (bipolar disorder), F20.9 (schizophrenia): rated with instruments this
#     package does not ship (YMRS, PANSS), and a PHQ-9 would misrepresent what is
#     measured;
#   * F84.0 (autism), F90.9 (ADHD): the diagnostic instruments are structured
#     observations and rating scales, not a 0-27 self-report score;
#   * F43.1 (PTSD): the usual scales (PCL-5, CAPS-5) are, again, not in the six.
CONDITION_ASSESSMENTS: dict[str, tuple[str, ...]] = {
    "F32.9": ("phq9", "madrs"),  # Depression
    "F41.9": ("gad7",),  # Anxiety disorder
    "F19.9": ("audit_c", "cage"),  # Substance use disorder (the alcohol screens)
    "G30.9": ("mmse",),  # Alzheimer's disease
}

# How a score is placed inside its range: mostly near the healthy pole, occasionally far
# from it. (cumulative percentile, lowest fraction of the range, highest). The same shape
# as SEVERITY_TIERS in clinical_values.py and for the same reason — a flat draw would
# make the average PHQ-9 in a screening population 13, i.e. moderately depressed.
ASSESSMENT_SEVERITY_TIERS: tuple[tuple[int, float, float], ...] = (
    (60, 0.0, 0.2),
    (90, 0.2, 0.55),
    (100, 0.55, 1.0),
)


def band_label_key(instrument: str, score: int) -> str:
    """Return the label key for a score's severity band.

    Bands are listed by ascending score and the first one the score fits is its band,
    which is what makes the MMSE's inversion a property of the data rather than of this
    function: its lowest band is the severe one.

    Raises:
        ValueError: if the instrument is unknown, or the score is outside 0..max_score.
    """
    if instrument not in ASSESSMENT_INSTRUMENTS:
        raise ValueError(f"Unknown assessment instrument '{instrument}'; expected one of: {', '.join(ASSESSMENT_INSTRUMENTS)}")
    definition = ASSESSMENT_INSTRUMENTS[instrument]
    if not 0 <= score <= definition["max_score"]:
        raise ValueError(f"Score {score} is outside the range of {definition['name']} (0-{definition['max_score']})")
    return next(key for upper_bound, key in definition["bands"] if score <= upper_bound)


def is_clinically_significant(instrument: str, score: int) -> bool:
    """Whether a score is at or past the instrument's published cut-off.

    Honours the inversion: on the MMSE a score at or BELOW the cut-off is the significant
    one, on every other instrument it is a score at or above it.
    """
    definition = ASSESSMENT_INSTRUMENTS[instrument]
    if definition["higher_is_worse"]:
        return score >= definition["significant_from"]
    return score <= definition["significant_from"]
