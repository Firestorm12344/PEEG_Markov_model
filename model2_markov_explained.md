# Corrected Model 2 Explained in Simple Terms

## 1) What is this study about?
This study evaluates whether using pEEG (processed electroencephalography during anesthesia) is worth it for older adults undergoing hip fracture surgery.

The clinical idea is:
- if anesthesia is better guided with pEEG,
- there may be less postoperative delirium,
- and with less delirium,
- there may be fewer institutional rehabilitation stays, lower mortality, and better quality of life.

In health economics, this is summarized by two main outcomes:
- **costs** in USD
- **QALYs** (quality-adjusted life years)

---

## 2) What is a Markov model?
A Markov model follows a cohort of patients over time.
At each cycle, each patient can stay in the same state or move to another state.

In this model, the health states include:
- acute postoperative without delirium
- acute postoperative with delirium
- home recovery
- rehabilitation recovery
- readmission
- death

At each cycle the model asks:
- is the patient still alive?
- are they at home, in rehab, or readmitted?
- what utility does that state have?
- what cost does that state generate?

Then the model accumulates:
- costs
- QALYs
- deaths
- rehab discharges

The model does not track individual patients one by one.
It follows an average cohort of patients.

---

## 3) What does the code do?

### A. Define parameters
The code stores the model parameters, such as:
- delirium probability
- mortality risk
- rehab probability
- delirium episode cost
- pEEG per-case cost
- state utilities for QALY calculation

### B. Convert OR to probability
If a study reports an odds ratio, the code converts it to an absolute probability using:

p1 = OR * p0 / (1 - p0 + OR * p0)

This converts a relative effect into an absolute risk.

### C. Run the Markov model
The function `run_markov()`:
1. sets up the initial cohort distribution
2. assigns patients to delirium or no delirium states
3. in the first cycle, calculates deaths and discharge to home or rehab
4. in later cycles, accumulates QALYs, readmissions, and deaths
5. returns total cost and QALYs per patient

### D. Compare strategies
The model compares:
- usual anesthesia
- pEEG-guided anesthesia

Then it calculates:
- incremental cost = cost_pEEG - cost_usual
- incremental QALY = qaly_pEEG - qaly_usual

If:
- incremental cost < 0
- incremental QALY > 0

then pEEG is dominant.

---

## 4) What analysis is performed in this project?
This project compares two anesthesia strategies for older adults with hip fracture:
- usual anesthesia
- pEEG-guided anesthesia

The main model is a deterministic Markov model that follows a cohort through discrete cycles. Health states include acute postoperative with or without delirium, home recovery, rehabilitation recovery, readmission, and death.

The analysis includes:
- a 180-day base-case horizon aligned with typical clinical follow-up
- a 365-day scenario to evaluate one-year outcomes
- costs, QALYs, delirium cases, rehab discharges, deaths, and readmissions

A complementary sensitivity script (`sensitivity_analysis.py`) also:
- runs probabilistic sensitivity analysis (PSA) using appropriate distributions for probabilities, costs, and ratios
- calculates NMB/INB instead of ICER for stability
- generates CEAC and tornado diagrams

---

## 5) How to read the results?
- **USD**: expected cost per patient
- **QALY**: health benefit adjusted for quality
- **Incremental**:
  - negative cost difference = saves money
  - positive QALY difference = improves health

---

## 6) What is a tornado diagram?
A tornado diagram is a one-way sensitivity analysis.
It varies one parameter at a low and high value to see how much the economic result changes.

The parameters that move the result the most are the most important.

---

## 7) What is PSA?
PSA stands for probabilistic sensitivity analysis.

It does not use a single fixed value for each parameter.
It uses distributions such as:
- Beta for probabilities
- Gamma for costs
- Lognormal for odds ratios and relative ratios

Then it runs many simulations.

This produces:
- the cost-effectiveness plane
- the CEAC (cost-effectiveness acceptability curve)

---

## 8) Methodological note
This explanation is useful to understand the model and provides a working foundation.
For a stronger paper, it is still advisable to:
- validate local pEEG costs
- justify the 180-day base-case choice
- justify any extension to 1, 5, or 10 years
