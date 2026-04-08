# pEEG Hip-Fracture Markov Model

## Model Overview

This is a **hospital-perspective cost-effectiveness model** comparing pEEG-guided anesthesia versus usual anesthesia in elderly patients undergoing hip fracture repair. The model evaluates the impact on postoperative delirium, mortality, rehabilitation disposition, and readmission risk over a **180-day base case** (with a 365-day scenario analysis).

## Key Model Features

### Time Horizon & Cycles
- **Base Case:** 180 days
- **Scenario:** 365 days (1-year follow-up)
- **Cycle Structure:** 
  - Phase A (Acute): Days 0-84 using **weekly cycles** (7-day cycles)
  - Phase B (Post-acute): Days 85-180 using **monthly cycles** (~30.44 days)
  
This piecewise design reflects the acute nature of delirium and captures rapid changes in the early postoperative period.

### Model States
1. Acute postoperative without delirium
2. Acute postoperative with delirium
3. Home recovery without delirium history
4. Home recovery with delirium history
5. Facility/rehabilitation without delirium history
6. Facility/rehabilitation with delirium history
7. Readmitted (temporary state during hospital readmission)
8. Death

### Key Parameters
- **p_delirium_usual:** 20.34% baseline delirium risk (usual anesthesia)
- **rr_delirium_peeg:** 0.81 relative risk reduction with pEEG
- **p_mort_180_no_delirium:** 12.4% 180-day mortality (no delirium history)
- **or_mort_delirium:** 1.69 odds ratio for delirium patients
- **p_rehab_no_delirium:** 29.8% discharge to rehabilitation (no delirium)
- **or_rehab_delirium:** 2.8 odds ratio for delirium patients
- **p_readmit_180_no_delirium:** 36% 180-day hospital readmission (no delirium history)
- **or_readmit_delirium:** 1.79 odds ratio for delirium patients
- **Annual discount rate:** 3%

---

## Costs Included (Hospital Perspective)

### ✅ INCLUDED Costs
1. **Delirium Management Cost:** $8,286 per delirium episode (applied at time of diagnosis)
2. **pEEG Intervention Cost:** $120 per case (applied to pEEG-guided strategies only)
3. **Readmission Cost:** $5,000 per hospitalization event (applied each time patient is readmitted)

### ❌ NOT INCLUDED Costs
1. **Acute hospitalization costs** (offset in both arms)
2. **Rehabilitation facility costs** (structured as outcome, not costed in this model)
3. **Home care costs** (assumption: not applicable in hospital perspective)
4. **Long-term nursing home/institutionalization costs** (beyond 180-day horizon)
5. **Outpatient or primary care costs** (post-discharge follow-up)
6. **Indirect costs** (productivity loss, caregiver burden)
7. **Quality of life loss during delirium** (captured in utilities, not costs)

---

## Quality of Life (Utilities)

### QALYs Accumulated
Utilities are combined with cycle-specific durations (in days) to compute QALYs:

- **Month 1 post-trauma (days 0-30):** 0.46 (acute recovery period, high disability)
- **Home months 2-4 (days 31-120):** Linear interpolation between 0.46 and 0.65
- **Home 4+ months (days 120+):** 0.65 (stable home recovery)
- **Rehabilitation (any duration):** 0.37 (structured facility environment, activity restrictions)
- **During readmission:** 0.20 (in-hospital admission, high disability)

**Note:** These utilities represent "health state" valuations. Delirium does NOT incur an explicit utility multiplier in this model; its impact is through mortality, rehab disposition, and readmission effects.

---

## Key Model Assumptions

1. **Delirium is acute:** Assigned at time zero; does not persist as a chronic state beyond the initial discharge decision.
2. **Readmission is temporary:** Patients who are readmitted return to home after the cycle (tunnel state model).
3. **Delirium effects are persistent:** Delirium history affects rehab disposition, mortality, and readmission risk for the full 180 days.
4. **365-day scenario handling:** Mortality switches to background annual risk after day 180, and readmission risk is not extrapolated beyond the supported 180-day evidence window.
5. **Cycle-specific probabilities:** All multi-period probabilities are converted via daily hazard rates to respect cycle lengths (weekly early, monthly late).
6. **Discounting:** Applied per-cycle at the cycle midpoint, using daily compounding.
7. **Hospital perspective:** No indirect costs; payer is the hospital/health system.

---

## Model Outputs (CSV)

**File:** `model2_corrected_outputs_180d_1y.csv`

Columns:
- **strategy:** "Usual anesthesia" or "pEEG-guided anesthesia"
- **horizon_days:** 180 or 365
- **cost_usd_per_patient:** Total discounted cost per patient (includes delirium, pEEG, readmission)
- **qalys_per_patient:** Total discounted QALYs per patient
- **delirium_cases_per_patient:** Proportion of patients developing delirium
- **rehab_discharges_per_patient:** Proportion discharged to rehabilitation facility
- **deaths_per_patient:** Proportion who died during the time horizon
- **readmissions_per_patient:** Average number of hospital readmissions per patient

---

## Sensitivity Analysis

### One-Way Sensitivity (Tornado)
Varies each parameter by ±25% and reports the resulting range in INB (incremental net benefit), which is more stable than ICER.

### Probabilistic Sensitivity Analysis (PSA)
Samples 1,000 parameter sets from distributions (10% coefficient of variation for all parameters):
- **Probabilities & Utilities:** Beta distribution, bounded [0, 1]
- **Costs:** Lognormal distribution (natural skew for healthcare costs)
- **RRs and ORs:** Lognormal distribution (positive, right-skewed)

Outputs:
- Cost-effectiveness plane (cost difference vs QALY difference)
- INB distribution
- Cost-effectiveness acceptability curve (CEAC) at willingness-to-pay thresholds ($50K, $100K)

---

## Interpretation Guide

### Is pEEG Cost-Effective?

**Typical thresholds for US healthcare decision-making:**
- **< $50,000/QALY:** Generally considered cost-effective
- **$50,000–$100,000/QALY:** Often considered cost-effective, context-dependent
- **> $100,000/QALY:** Rarely considered cost-effective

Check the CE plane: 
- **Quadrant I (NE):** pEEG costs more AND gains QALYs (incremental cost-effectiveness)
- **Quadrant IV (SE):** pEEG costs less AND gains QALYs (dominant; always prefer)
- **Quadrant II (NW):** pEEG costs more AND loses QALYs (dominated; never prefer)
- **Quadrant III (SW):** pEEG costs less AND loses QALYs (trade-off)

---

## Files in This Directory

- **model2_corrected_markov.py**: Main model code (180d base + 365d scenario)
- **model2_corrected_outputs_180d_1y.csv**: Model results (costs, QALYs, outcomes)
- **sensitivity_analysis.py**: One-way, PSA, and CE figures
- **sensitivity_analysis_CORRECTED.png**: Combined 180-day/365-day publication-style sensitivity figure
- **sensitivity_analysis_180d.png** and **sensitivity_analysis_365d.png**: Plots
- **README.md** (this file): Documentation
- **CHANGELOG.md**: History of model modifications

---

## Clinical Context

**Population:** Elderly (typically 65+) undergoing hip fracture repair

**Intervention:** pEEG-guided anesthesia maintenance during surgery
- Reduces severe delirium by 19% (RR 0.81) relative to usual anesthesia
- Adds $120 per case

**Clinical Outcomes Modeled:**
- Acute postoperative delirium (days 0-14)
- Discharge disposition (home vs rehabilitation)
- Hospital readmission within 180 days
- 180-day mortality
- QALYs based on functional status and setting

**Evidence Base:**
- Delirium probabilities and effects derived from hip-fracture literature
- pEEG efficacy from intervention trials (e.g., RCTs on processed EEG)
- Rehab/readmission/mortality relationships from prospective cohort data

---

## Limitations & Future Directions

### Current Limitations
1. **No long-term structure:** Model supports a 180-day base case and an optional 365-day scenario only; no expanded chronic institutionalization or recurrent delirium risk beyond 1 year.
2. **Readmission modeled simply:** Assumes single readmission tunnel state; does not capture multiplicity or cascade effects.
3. **Delirium is binary:** "Acute" only; does not model subsyndromal or prolonged delirium subgroups.
4. **No adverse events modeled:** pEEG itself has no complications; focuses only on delirium reduction.

### Recommendations for Enhancement
1. Add **persistent institutionalization state** beyond 180 days if longer follow-up data becomes available.
2. **Expand readmission logic:** Model as recurring state with escalating costs or transition probabilities.
3. **Subgroup analyses:** Stratify by age, frailty, or baseline cognitive status if heterogeneous treatment effects exist.
4. **Budget impact analysis:** Estimate cost savings/burden if pEEG is adopted hospital-wide.

---

## How to Run

```bash
# Base model (generates CSV)
python model2_corrected_markov.py

# Sensitivity analysis (generates plots)
python sensitivity_analysis.py
```

---

## Contact & Questions

For questions about model assumptions, parameter sources, or updates, contact the analysis team.

**Version:** 2.0 (Updated April 2026)  
**Last Modified:** April 5, 2026
