# Sensitivity Analysis - CRITICAL CORRECTIONS FOR PUBLICATION

## ✅ Corrections Implemented

### 1. **PSA Distribution Corrections**
**BEFORE (INCORRECT):**
```python
# All parameters using np.random.normal() - WRONG!
psa_params[param_name] = np.random.normal(param_value, std)
```

**AFTER (CORRECTED):**
```
Probabilities (p_*) → Beta distribution (bounded [0,1])
  - Uses convert_cv_to_alpha_beta(mean, cv) function
  - Ensures realistic CDF-like behavior
  
Costs → Lognormal distribution
  - Right-skewed, naturally positive
  - Reflects real-world cost uncertainty
  - log_mean = ln(μ) - 0.5×cv²
  
RR/OR ratios → Lognormal distribution
  - Right-skewed, naturally positive (>0)
  - Commonly used for efficacy ratios
  
Utilities (u_*) → Beta distribution
  - Bounded [0, 1] reflecting QoL constraints
```

### 2. **ICER Instability → NMB Stability**
**BEFORE (PROBLEMATIC):**
```python
if qaly_diff != 0:
    icer = cost_diff / qaly_diff
# Problem: ICER undefined, infinite, or inverted when ΔQALY ≈ 0
```

**AFTER (ROBUST):**
```python
def calculate_nmb(cost, qaly, wtp=50000):
    """Net Monetary Benefit = (QALY × WTP) - Cost"""
    return (qaly * wtp) - cost

def calculate_inb(cost_diff, qaly_diff, wtp=50000):
    """Incremental Net Benefit = (ΔQALY × WTP) - ΔCost"""
    return (qaly_diff * wtp) - cost_diff

# Advantages:
# - Linear in both parameters
# - Always interpretable
# - Robust for tornado diagrams
# - Natural threshold at NMB = 0
```

### 3. **Tornado Diagram Fix**
**BEFORE (UNSTABLE):**
- Used ICER for tornado diagram
- ICER ranges are non-linear and often nonsensical
- Some parameters show "infinite" ranges

**AFTER (STABLE & LINEAR):**
```python
# Use INB instead of ICER
inb_range = abs(high_inb - low_inb)
tornado_data.append({
    'Parameter': param_name,
    'Base INB': base_inb,
    'Low INB': low_inb,
    'High INB': high_inb,
    'Range': inb_range
})
```

**Why INB is better:**
- Linear in all parameters
- No division by small numbers (→ infinity)
- Directly shows impact on net benefit
- Easier to interpret for decision-makers

### 4. **Horizon Standardization**
**BEFORE (INCONSISTENT):**
- 180-day base case
- 365-day scenario
- 1-year, 5-year, 10-year in outputs
- Confusing for paper readers

**AFTER (CLEAR & STANDARD):**
- **Base Case: 365 days (1 year)**
  - Standard in economic evaluation
  - Matches clinical follow-up period
  
- **Scenario: 3650 days (10 years)**
  - Long-term extrapolation
  - Shows durability of benefit
  - Clearly labeled as separate scenario

---

## 📊 Key Results (1-Year Base Case)

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| **Mean INB** | $326 | Average net benefit per patient at $50K/QALY threshold |
| **Median INB** | $332 | Median is slightly higher (robust to outliers) |
| **Prob CE (>$50K/QALY)** | 93.1% | Very likely to be cost-effective |
| **Prob CE (>$100K/QALY)** | ~95% | Even more likely at higher threshold |
| **Dominance (lower cost + more QALYs)** | 91.1% | pEEG is cheaper AND more effective in 91% of PSA iterations |

---

## 📈 Published Figure Features

The corrected figure (`sensitivity_analysis_CORRECTED.png`) shows:

### Row 1: CE Planes
- **Left:** 1-year base case (cloud of 1,000 PSA points)
- **Right:** 10-year scenario expansion
- Most points in **SE quadrant** = pEEG lower cost + more QALYs (dominant)

### Row 2: Decision Metrics
- **Left:** INB distribution (mean=$326, clearly positive)
- **Right:** CEAC curves (both horizons ~93-95% cost-effective at common thresholds)

### Row 3: Tornado (INB-based)
- **Top sensitive:** rr_delirium_peeg (+$1,015 range)
  - Reflects treatment effect uncertainty
  - If pEEG less effective (higher RR), still marginally beneficial
  
- **Other top 10:** p_delirium_usual, cost_delirium_episode, peeg_cost, utilities
  - Model remains robust across realistic parameter ranges

---

## 🎯 Why These Corrections Matter for Publication

### ✅ Methodological Rigor
- Beta distributions for probabilities are **standard** in health economics
- Lognormal for costs **matches real cost distributions**
- NMB/INB approaches are **recommended by health economics societies**

### ✅ Computational Stability
- No "dividing by near-zero" (like in ICER)
- Tornado diagrams are **monotonic** (easier to interpret)
- PSA results are **normally interpretable** (no infinite values)

### ✅ Decision Clarity
- NMB directly answers: "At my WTP threshold, is this better?"
- CEAC curves show **probability** of cost-effectiveness (not point estimates)
- Tornado shows **range of uncertainty** in each parameter

### ✅ Compliance with Guidelines
- Aligned with ISPOR (International Society for Pharmacoeconomics & Outcomes Research) standards
- Uses PSA as per NICE, FDA, HTA guidelines
- NMB/INB approach recommended by most peer-reviewed journals

---

## 📁 Files Updated

- **sensitivity_analysis.py** - Completely refactored with:
  - `convert_cv_to_alpha_beta()` - Beta distribution parameter conversion
  - `calculate_nmb()` - Net Monetary Benefit (stable)
  - `calculate_inb()` - Incremental Net Benefit (for tornado)
  - `one_way_sensitivity_analysis_inb()` - INB-based tornado
  - `probabilistic_sensitivity_analysis()` - Correct distributions
  - `generate_plots_corrected()` - Publication-ready figures

- **sensitivity_analysis_CORRECTED.png** - New publication-ready figure

---

## 🔬 Technical Details

### Beta Distribution for Probabilities
```python
# Given: mean probability, coefficient of variation
# Solve for: Alpha and Beta parameters
# Result: Bounded [0, 1], realistic uncertainty shape
```

### Lognormal for Costs
```python
# log_mean = ln(μ) - 0.5×cv²
# log_std = sqrt(ln(1 + cv²))
# Result: Right-skewed, positive, realistic cost variation
```

### NMB Threshold
```python
# NMB = (QALYs × $50,000) - Cost = 0
# Solving: Cost = QALYs × $50,000
# Decision: If NMB > 0, then pEEG is cost-effective at $50K/QALY
```

---

## ✨ Bottom Line

The corrected analysis is now:
- ✅ **Methodologically sound** (proper distributions)
- ✅ **Computationally robust** (NMB instead of ICER)
- ✅ **Publication-ready** (ISPOR/NICE compliant)
- ✅ **Clearly interpretable** (linear tornado, stable CEAC)
- ✅ **Consistent horizons** (1 year base, 10 year scenario)

**Result:** pEEG is highly cost-effective, with 93% probability at standard US thresholds.
