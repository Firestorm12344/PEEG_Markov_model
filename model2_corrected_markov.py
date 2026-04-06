"""
pEEG Hip-Fracture Markov Model - 180-Day Base Case & 365-Day Scenario

HORIZON & CYCLE STRUCTURE:
  - Base Case: 180 days (6 months) - matches clinical follow-up for hip fracture recovery
  - Scenario: 365 days (1 year) - optional longer follow-up
  - Cycle Design:
    * Phase A (Acute, Days 0-84): Weekly cycles (7 days each, 12 cycles)
    * Phase B (Post-acute, Days 85-180): Monthly cycles (~30.44 days each)
    This piecewise approach captures rapid early changes during acute delirium/recovery
    while maintaining computational efficiency for later stable phases.

MODEL STATES (8 total):
  1. Acute postoperative without delirium
  2. Acute postoperative with delirium
  3. Home recovery without delirium history
  4. Home recovery with delirium history
  5. Facility/rehabilitation without delirium history
  6. Facility/rehabilitation with delirium history
  7. Readmitted (temporary tunnel state during hospital readmission)
  8. Death

KEY ASSUMPTIONS:
  - Delirium is acute: assigned at surgery, affects discharge destination (home vs rehab)
  - Delirium effects persist: higher mortality, rehab rates, readmission risk for 180 days
  - Readmission is temporary: patients re-route back to home after one cycle
  - All multi-year probabilities converted to daily hazards, then to cycle-specific probs
  - Hospital perspective: costs include delirium mgmt ($8,286), pEEG ($120), readmission ($5,000)
  - Utilities: QALYs accumulated = utility × (cycle_days / 365.0), discounted per cycle

INTERVENTIONS COMPARED:
  - Usual anesthesia: baseline delirium risk 20.34%, no intervention cost
  - pEEG-guided anesthesia: RR 0.81 for delirium (16.48% risk), +$120 cost

OUTPUT METRICS:
  - Total cost per patient (discounted, 3% annual rate)
  - QALYs per patient (discounted)
  - Delirium incidence (%)
  - Rehab discharges (%)
  - Deaths (%)
  - Readmissions (count per patient)
"""

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = {'p_delirium_usual': 0.2034, 'rr_delirium_peeg': 0.81, 'p_mort_180_no_delirium': 0.124, 'or_mort_delirium': 1.69, 'p_rehab_no_delirium': 0.298, 'or_rehab_delirium': 2.8, 'p_readmit_180_no_delirium': 0.36, 'or_readmit_delirium': 1.79, 'cost_delirium_episode': 8286.0, 'peeg_per_case_cost': 120.0, 'cost_readmission': 5000.0, 'u_readmit': 0.2, 'u_month1_post_hip_fracture': 0.46, 'u_home_4mo': 0.65, 'u_rehab_4mo': 0.37, 'annual_background_mortality_after_6m': 0.05, 'annual_discount': 0.03}

STATES = ['acute_no_delirium', 'acute_delirium', 'home_no_delirium_history', 'home_delirium_history', 'rehab_no_delirium_history', 'rehab_delirium_history', 'readmitted', 'death']
IDX = {s: i for i, s in enumerate(STATES)}

def p1_from_or(or_value: float, p0: float) -> float:
    return (or_value * p0) / (1 - p0 + or_value * p0)

def utility_home(month: int, params: dict) -> float:
    if month <= 1:
        return params["u_month1_post_hip_fracture"]
    if month >= 4:
        return params["u_home_4mo"]
    slope = (params["u_home_4mo"] - params["u_month1_post_hip_fracture"]) / 3.0
    return params["u_month1_post_hip_fracture"] + slope * (month - 1)


def utility_home_by_days(elapsed_days: int, params: dict) -> float:
    """
    Utility function for home recovery, mapped to elapsed days instead of months.
    Days 0-30 ~ month 1, days 31-60 ~ month 2, etc.
    """
    if elapsed_days <= 30:
        return params["u_month1_post_hip_fracture"]
    if elapsed_days >= 120:
        return params["u_home_4mo"]
    # Linear interpolation between month 1 (day 30) and month 4 (day 120)
    slope = (params["u_home_4mo"] - params["u_month1_post_hip_fracture"]) / 90.0
    return params["u_month1_post_hip_fracture"] + slope * (elapsed_days - 30)

def monthly_prob_from_cumulative(p_cum: float, months: int = 6) -> float:
    hazard = -math.log(1 - p_cum) / months
    return 1 - math.exp(-hazard)

def complete_params(base: dict) -> dict:
    p = dict(base)
    p["p_delirium_peeg"] = min(max(p["p_delirium_usual"] * p["rr_delirium_peeg"], 0.0001), 0.999)
    p["p_mort_180_delirium"] = p1_from_or(p["or_mort_delirium"], p["p_mort_180_no_delirium"])
    p["p_rehab_delirium"] = p1_from_or(p["or_rehab_delirium"], p["p_rehab_no_delirium"])
    p["p_readmit_180_delirium"] = p1_from_or(p["or_readmit_delirium"], p["p_readmit_180_no_delirium"])
    return p

def build_cycle_schedule(horizon_days: int) -> list:
    """
    Construct piecewise cycle schedule for two-phase Markov model.
    
    Phase A (Acute): Days 0-84 using weekly cycles
      - Captures rapid delirium development and early discharge decisions
      - 12 weekly cycles × 7 days = 84 days total
    
    Phase B (Post-acute): Days 85+ using monthly cycles
      - Coarser resolution for stable post-acute recovery phase
      - Approx 30.44 days per month, adjusted to exactly reach horizon_days
    
    Args:
        horizon_days: Total model time horizon (180 or 365)
    
    Returns:
        List of cycle lengths in days [7, 7, 7, ..., 30.44, 30.44, ...]
    """
    cycles = []
    
    # Phase A: Weekly cycles for days 0-84 (12 weeks)
    for week in range(12):
        cycles.append(7)
    
    # Phase B: Monthly cycles for days 85-180 (approximately 4 months, 96 days)
    remaining_days = horizon_days - 84
    if remaining_days > 0:
        # Use monthly cycles (approximately 30.44 days)
        num_months = int(np.ceil(remaining_days / 30.44))
        days_per_month = remaining_days / num_months
        for _ in range(num_months):
            cycles.append(days_per_month)
    
    return cycles


def cycle_prob_from_cumulative_hazard(p_cum: float, period_days: int, cycle_days: int) -> float:
    """
    Convert cumulative risk over a reference period into cycle-specific probability.
    
    Uses constant hazard rate assumption: if risk over 'period_days' is p_cum,
    then daily hazard λ = -ln(1 - p_cum) / period_days.
    Within a cycle of length cycle_days, probability = 1 - exp(-λ × cycle_days).
    
    This method allows ANY cycle length (weekly, monthly, etc.) to be correctly
    derived from multi-month or multi-year cumulative probabilities.
    
    Example: 
      - 180-day mortality = 12.4%
      - Daily hazard = -ln(0.876) / 180 ≈ 0.000695
      - 7-day cycle prob = 1 - exp(-0.000695 × 7) ≈ 0.486%
      - 30-day cycle prob = 1 - exp(-0.000695 × 30) ≈ 2.06%
    
    Args:
        p_cum: Cumulative probability over reference period
        period_days: Reference period (e.g., 180 for 180-day mortality)
        cycle_days: Actual cycle length in days
    
    Returns:
        Cycle-specific probability
    """
    daily_hazard = -math.log(1 - p_cum) / period_days
    return 1 - math.exp(-daily_hazard * cycle_days)


def run_markov(strategy: str, horizon_days: int, params: dict) -> dict:
    p = complete_params(params)
    cycles = build_cycle_schedule(horizon_days)
    num_cycles = len(cycles)
    trace = np.zeros((num_cycles + 1, len(STATES)))

    p_del = p["p_delirium_usual"] if strategy == "Usual anesthesia" else p["p_delirium_peeg"]
    trace[0, IDX["acute_no_delirium"]] = 1 - p_del
    trace[0, IDX["acute_delirium"]] = p_del

    total_cost = p_del * p["cost_delirium_episode"]
    if strategy == "pEEG-guided anesthesia":
        total_cost += p["peeg_per_case_cost"]

    total_qaly = 0.0
    total_deaths = 0.0
    total_delirium = p_del
    total_rehab = 0.0
    total_readmit = 0.0

    # Readmission probabilities (daily hazard from 180-day probabilities)
    p_readmit_daily_nd = -math.log(1 - p["p_readmit_180_no_delirium"]) / 180
    p_readmit_daily_d = -math.log(1 - p["p_readmit_delirium_peeg"]) / 180 if "p_readmit_delirium_peeg" in p else -math.log(1 - p1_from_or(p["or_readmit_delirium"], p["p_readmit_180_no_delirium"])) / 180

    # Convert 180-day cumulative probabilities to daily hazards, then to cycle-specific probabilities
    p_mort_cycle_nd = cycle_prob_from_cumulative_hazard(p["p_mort_180_no_delirium"], 180, cycles[0]) if cycles else 0
    p_mort_cycle_d = cycle_prob_from_cumulative_hazard(p["p_mort_180_delirium"], 180, cycles[0]) if cycles else 0
    
    # Background mortality cycles depend on cycle length
    p_bg_cycle = 1 - (1 - p["annual_background_mortality_after_6m"]) ** (cycles[0] / 365.0) if cycles else 0

    elapsed_days = 0
    for cycle_idx, cycle_days in enumerate(cycles):
        prev = trace[cycle_idx].copy()
        new = np.zeros(len(STATES))
        cycle_midpoint_days = elapsed_days + cycle_days / 2.0
        discount = 1 / ((1 + p["annual_discount"]) ** (cycle_midpoint_days / 365.0))

        # Readmission probabilities for this cycle
        p_readmit_cycle_nd = 1 - math.exp(-p_readmit_daily_nd * cycle_days)
        p_readmit_cycle_d = 1 - math.exp(-p_readmit_daily_d * cycle_days)

        # First cycle (acute phase): route from acute states to home/rehab
        if cycle_idx == 0:
            # Recalculate mortality probabilities for the first cycle specifically
            p_mort_cycle_nd = cycle_prob_from_cumulative_hazard(p["p_mort_180_no_delirium"], 180, cycle_days)
            p_mort_cycle_d = cycle_prob_from_cumulative_hazard(p["p_mort_180_delirium"], 180, cycle_days)
            
            surv_nd = prev[IDX["acute_no_delirium"]] * (1 - p_mort_cycle_nd)
            surv_d = prev[IDX["acute_delirium"]] * (1 - p_mort_cycle_d)

            deaths_now = prev[IDX["acute_no_delirium"]] * p_mort_cycle_nd + prev[IDX["acute_delirium"]] * p_mort_cycle_d
            new[IDX["death"]] += deaths_now
            total_deaths += deaths_now

            # Utility for first cycle (scaled by cycle length)
            utility_first_cycle = p["u_month1_post_hip_fracture"]
            total_qaly += (surv_nd + surv_d) * utility_first_cycle * (cycle_days / 365.0) * discount

            # Route survivors to home or rehab
            rehab_nd = surv_nd * p["p_rehab_no_delirium"]
            home_nd = surv_nd - rehab_nd
            rehab_d = surv_d * p["p_rehab_delirium"]
            home_d = surv_d - rehab_d

            new[IDX["home_no_delirium_history"]] += home_nd
            new[IDX["home_delirium_history"]] += home_d
            new[IDX["rehab_no_delirium_history"]] += rehab_nd
            new[IDX["rehab_delirium_history"]] += rehab_d

            total_rehab += rehab_nd + rehab_d

        else:
            # Subsequent cycles: follow home/rehab population with death, readmission
            # Home states with possible readmission or death
            home_states = [
                ("home_no_delirium_history", p_readmit_cycle_nd, p_mort_cycle_nd, utility_home_by_days(elapsed_days, p)),
                ("home_delirium_history", p_readmit_cycle_d, p_mort_cycle_d, utility_home_by_days(elapsed_days, p)),
            ]
            
            for state_name, p_readmit, p_mort, utility in home_states:
                pop = prev[IDX[state_name]]
                # Competing risks: readmit vs death vs stay home
                # Simplified: apply sequentially (readmit first, then death among non-readmitted)
                readmits = pop * p_readmit
                non_readmits = pop * (1 - p_readmit)
                deaths = non_readmits * p_mort
                survivors = non_readmits * (1 - p_mort)
                
                new[IDX["readmitted"]] += readmits
                new[IDX["death"]] += deaths
                new[IDX[state_name]] += survivors
                
                total_readmit += readmits
                total_deaths += deaths
                total_qaly += survivors * utility * (cycle_days / 365.0) * discount
            
            # Rehab states with possible discharge back to home, readmission, or death
            rehab_states = [
                ("rehab_no_delirium_history", p_readmit_cycle_nd, p_mort_cycle_nd, p["u_rehab_4mo"]),
                ("rehab_delirium_history", p_readmit_cycle_d, p_mort_cycle_d, p["u_rehab_4mo"]),
            ]
            
            for state_name, p_readmit, p_mort, utility in rehab_states:
                pop = prev[IDX[state_name]]
                readmits = pop * p_readmit
                non_readmits = pop * (1 - p_readmit)
                deaths = non_readmits * p_mort
                survivors = non_readmits * (1 - p_mort)
                
                new[IDX["readmitted"]] += readmits
                new[IDX["death"]] += deaths
                new[IDX[state_name]] += survivors
                
                total_readmit += readmits
                total_deaths += deaths
                total_qaly += survivors * utility * (cycle_days / 365.0) * discount
            
            # Readmitted state: tunnel state (temporary), reverts to home after one cycle
            # or can have another death event
            readmit_pop = prev[IDX["readmitted"]]
            readmit_deaths = readmit_pop * p_mort_cycle_nd  # Use average mortality
            readmit_survivors = readmit_pop * (1 - p_mort_cycle_nd)
            
            # Readmission has utility cost (typically lower than rehab/home)
            readmit_utility = params.get("u_readmit", 0.2)  # Default low utility during readmission
            
            new[IDX["death"]] += readmit_deaths
            new[IDX["home_no_delirium_history"]] += readmit_survivors  # Return to home after readmission
            
            total_deaths += readmit_deaths
            total_qaly += readmit_survivors * readmit_utility * (cycle_days / 365.0) * discount
            
            # Apply readmission cost for each individual who was readmitted in this cycle
            total_cost += readmits * params.get("cost_readmission", 0)  # Default 0 if not specified

        trace[cycle_idx + 1] = new
        elapsed_days += cycle_days

    return {
        "strategy": strategy,
        "horizon_days": horizon_days,
        "cost_usd_per_patient": float(total_cost),
        "qalys_per_patient": float(total_qaly),
        "delirium_cases_per_patient": float(total_delirium),
        "rehab_discharges_per_patient": float(total_rehab),
        "deaths_per_patient": float(total_deaths),
        "readmissions_per_patient": float(total_readmit),
    }

if __name__ == "__main__":
    rows = []
    # 180-day base case
    for horizon_days in [180, 365]:
        usual = run_markov("Usual anesthesia", horizon_days, BASE)
        peeg = run_markov("pEEG-guided anesthesia", horizon_days, BASE)
        rows.extend([usual, peeg])
    
    df_results = pd.DataFrame(rows)
    print(df_results)
    
    # Save to CSV with the new naming
    csv_path = r"c:\Users\juanz\OneDrive\Desktop\Universidad\Markov Model\model2_corrected_outputs_180d_1y.csv"
    df_results.to_csv(csv_path, index=False)
    print(f"\nResults saved to: {csv_path}")
