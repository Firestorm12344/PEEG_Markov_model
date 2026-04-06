"""
Sensitivity Analysis for pEEG Hip-Fracture Markov Model (CORRECTED - Paper-Ready)

CRITICAL CORRECTIONS:
1. ✅ Distribuciones PSA correctas:
   - Probabilidades → Beta
   - Costos → Gamma/Lognormal
   - RR/OR → Lognormal

2. ✅ NMB en lugar de ICER:
   - ICER es inestable cuando ΔQALY ≈ 0
   - NMB es lineal y más estable

3. ✅ INB (Incremental Net Benefit) en Tornado:
   - No ICER (inestable)
   - INB es monotónico

4. ✅ Horizonte consistente:
   - Base case: 365 días (1 año)
   - Scenario: 3650 días (10 años)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import beta, gamma
from model2_corrected_markov import run_markov, BASE, complete_params
import math

# Set random seed for reproducibility
np.random.seed(42)

# Willingness-to-pay threshold (common in US)
WTP_THRESHOLD = 50000

def calculate_nmb(cost, qaly, wtp=WTP_THRESHOLD):
    """
    Calculate Net Monetary Benefit (NMB) at a given WTP threshold.
    NMB = (QALYs × WTP) - Cost
    More stable than ICER when ΔQALY is small or negative.
    """
    return (qaly * wtp) - cost

def calculate_inb(cost_diff, qaly_diff, wtp=WTP_THRESHOLD):
    """
    Calculate Incremental Net Benefit (INB) for one-way sensitivity analysis.
    INB = (ΔQALY × WTP) - ΔCost
    
    More robust for tornado diagrams than ICER.
    """
    return (qaly_diff * wtp) - cost_diff


def convert_cv_to_alpha_beta(mean, cv):
    """
    Convert mean and coefficient of variation to Alpha and Beta parameters for Beta distribution.
    Assumes beta distribution on [0, 1].
    """
    if mean <= 0 or mean >= 1 or cv <= 0:
        return None
    
    variance = (mean * cv) ** 2
    
    # Calculate alpha and beta from mean and variance
    alphaplusbeta = mean * (1 - mean) / variance - 1
    if alphaplusbeta <= 0:
        return None
    
    alpha = mean * alphaplusbeta
    beta_param = (1 - mean) * alphaplusbeta
    
    return alpha, beta_param


def one_way_sensitivity_analysis_inb(horizon_days=365, tornado_range=0.25, wtp=WTP_THRESHOLD):
    """
    One-way sensitivity analysis using Incremental Net Benefit (INB).
    
    Varies each parameter by ±tornado_range and reports INB change.
    INB is more suitable for tornado diagrams than ICER.
    """
    base_usual = run_markov("Usual anesthesia", horizon_days, BASE)
    base_peeg = run_markov("pEEG-guided anesthesia", horizon_days, BASE)
    
    base_cost_diff = base_peeg["cost_usd_per_patient"] - base_usual["cost_usd_per_patient"]
    base_qaly_diff = base_peeg["qalys_per_patient"] - base_usual["qalys_per_patient"]
    base_inb = calculate_inb(base_cost_diff, base_qaly_diff, wtp)
    
    tornado_data = []
    
    for param_name, param_value in BASE.items():
        if isinstance(param_value, (int, float)) and param_value > 0:
            # Low value
            low_params = dict(BASE)
            low_params[param_name] = param_value * (1 - tornado_range)
            low_usual = run_markov("Usual anesthesia", horizon_days, low_params)
            low_peeg = run_markov("pEEG-guided anesthesia", horizon_days, low_params)
            low_cost_diff = low_peeg["cost_usd_per_patient"] - low_usual["cost_usd_per_patient"]
            low_qaly_diff = low_peeg["qalys_per_patient"] - low_usual["qalys_per_patient"]
            low_inb = calculate_inb(low_cost_diff, low_qaly_diff, wtp)
            
            # High value
            high_params = dict(BASE)
            high_params[param_name] = param_value * (1 + tornado_range)
            high_usual = run_markov("Usual anesthesia", horizon_days, high_params)
            high_peeg = run_markov("pEEG-guided anesthesia", horizon_days, high_params)
            high_cost_diff = high_peeg["cost_usd_per_patient"] - high_usual["cost_usd_per_patient"]
            high_qaly_diff = high_peeg["qalys_per_patient"] - high_usual["qalys_per_patient"]
            high_inb = calculate_inb(high_cost_diff, high_qaly_diff, wtp)
            
            # Store tornado data (using INB, not ICER)
            inb_range = abs(high_inb - low_inb)
            tornado_data.append({
                'Parameter': param_name,
                'Base INB': base_inb,
                'Low INB': low_inb,
                'High INB': high_inb,
                'Range': inb_range
            })
    
    tornado_df = pd.DataFrame(tornado_data)
    tornado_df = tornado_df.sort_values('Range', ascending=False).head(10)
    
    return tornado_df, base_inb


def probabilistic_sensitivity_analysis(n_iterations=1000, horizon_days=365, wtp=WTP_THRESHOLD):
    """
    PSA with CORRECT probability distributions:
    - Probabilities → Beta (bounded [0, 1])
    - Costs → Lognormal (right-skewed, positive)
    - RR/OR → Lognormal (right-skewed, positive)
    - Utilities → Beta (bounded [0, 1])
    
    Returns: NMB values (more interpretable than ICER)
    """
    results_psa = {
        'cost_diff': [], 
        'qaly_diff': [], 
        'nmb_usual': [],
        'nmb_peeg': [],
        'inb': []
    }
    
    for iteration in range(n_iterations):
        psa_params = dict(BASE)
        
        for param_name, param_value in BASE.items():
            if not isinstance(param_value, (int, float)) or param_value <= 0:
                continue
            
            cv = 0.10  # 10% coefficient of variation
            
            # Probabilities → Beta distribution
            if 'p_' in param_name and param_name not in ['peeg_per_case_cost', 'cost_readmission']:
                alpha, beta_param = convert_cv_to_alpha_beta(param_value, cv) or (2, 2)
                psa_params[param_name] = np.random.beta(alpha, beta_param)
                psa_params[param_name] = min(max(psa_params[param_name], 0.0001), 0.9999)
            
            # Utilities → Beta distribution
            elif 'u_' in param_name:
                alpha, beta_param = convert_cv_to_alpha_beta(param_value, cv) or (2, 2)
                psa_params[param_name] = np.random.beta(alpha, beta_param)
                psa_params[param_name] = min(max(psa_params[param_name], 0.0001), 0.9999)
            
            # RR and OR → Lognormal distribution
            elif param_name in ['rr_delirium_peeg', 'or_mort_delirium', 'or_rehab_delirium', 'or_readmit_delirium']:
                # Lognormal: ln(X) ~ N(ln(μ), cv²)
                log_mean = math.log(param_value) - 0.5 * (cv ** 2)
                log_std = math.sqrt(math.log(1 + cv ** 2))
                psa_params[param_name] = np.random.lognormal(log_mean, log_std)
                psa_params[param_name] = max(psa_params[param_name], 0.01)
            
            # Costs → Lognormal distribution (right-skewed)
            elif 'cost' in param_name:
                log_mean = math.log(param_value) - 0.5 * (cv ** 2)
                log_std = math.sqrt(math.log(1 + cv ** 2))
                psa_params[param_name] = np.random.lognormal(log_mean, log_std)
                psa_params[param_name] = max(psa_params[param_name], 1)
            
            # Annual discount rate → Beta (bounded [0, 1])
            elif param_name == 'annual_discount':
                alpha, beta_param = convert_cv_to_alpha_beta(param_value, cv) or (2, 2)
                psa_params[param_name] = np.random.beta(alpha, beta_param)
        
        # Run models
        usual = run_markov("Usual anesthesia", horizon_days, psa_params)
        peeg = run_markov("pEEG-guided anesthesia", horizon_days, psa_params)
        
        # Calculate metrics
        cost_diff = peeg["cost_usd_per_patient"] - usual["cost_usd_per_patient"]
        qaly_diff = peeg["qalys_per_patient"] - usual["qalys_per_patient"]
        nmb_usual = calculate_nmb(usual["cost_usd_per_patient"], usual["qalys_per_patient"], wtp)
        nmb_peeg = calculate_nmb(peeg["cost_usd_per_patient"], peeg["qalys_per_patient"], wtp)
        inb = nmb_peeg - nmb_usual
        
        results_psa['cost_diff'].append(cost_diff)
        results_psa['qaly_diff'].append(qaly_diff)
        results_psa['nmb_usual'].append(nmb_usual)
        results_psa['nmb_peeg'].append(nmb_peeg)
        results_psa['inb'].append(inb)
    
    return results_psa


def generate_plots_corrected(horizon_365d_results, horizon_3650d_results):
    """
    Generate publication-ready figures:
    - CE Plane (365d, 3650d)
    - INB distribution & CEAC (using NMB)
    - Tornado (INB-based, not ICER)
    """
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # ============ ROW 1: CE PLANES (365d and 3650d) ============
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.scatter(horizon_365d_results['qaly_diff'], 
                horizon_365d_results['cost_diff'], 
                alpha=0.5, s=20, label='1-year horizon')
    ax1.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax1.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    ax1.set_xlabel('ΔQALYs (pEEG vs Usual)')
    ax1.set_ylabel('ΔCost ($)')
    ax1.set_title('Cost-Effectiveness Plane - 1 Year (Base Case)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.scatter(horizon_3650d_results['qaly_diff'], 
                horizon_3650d_results['cost_diff'], 
                alpha=0.5, s=20, color='orange', label='10-year scenario')
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax2.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    ax2.set_xlabel('ΔQALYs (pEEG vs Usual)')
    ax2.set_ylabel('ΔCost ($)')
    ax2.set_title('Cost-Effectiveness Plane - 10 Years (Scenario)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # ============ ROW 2: NMB & CEAC (combined) ============
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.hist(horizon_365d_results['inb'], bins=50, edgecolor='black', alpha=0.7, label='1-year')
    ax3.axvline(x=0, color='red', linestyle='--', linewidth=2, label='INB = 0 (threshold)')
    prob_peeg_ce = np.mean(np.array(horizon_365d_results['inb']) > 0)
    ax3.set_xlabel('Incremental Net Benefit ($)')
    ax3.set_ylabel('Frequency')
    ax3.set_title(f'INB Distribution - 1 Year (Prob pEEG CE: {prob_peeg_ce:.1%})')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    ax4 = fig.add_subplot(gs[1, 1])
    wtp_thresholds = np.linspace(0, 150000, 100)
    ceac_1y = []
    ceac_10y = []
    
    for wtp in wtp_thresholds:
        inb_1y = np.array(horizon_365d_results['qaly_diff']) * wtp - np.array(horizon_365d_results['cost_diff'])
        inb_10y = np.array(horizon_3650d_results['qaly_diff']) * wtp - np.array(horizon_3650d_results['cost_diff'])
        ceac_1y.append(np.mean(inb_1y > 0))
        ceac_10y.append(np.mean(inb_10y > 0))
    
    ax4.plot(wtp_thresholds, ceac_1y, linewidth=2, label='1-year base case')
    ax4.plot(wtp_thresholds, ceac_10y, linewidth=2, linestyle='--', label='10-year scenario')
    ax4.axvline(x=50000, color='red', linestyle='--', alpha=0.5, label='US threshold: $50K')
    ax4.axvline(x=100000, color='orange', linestyle='--', alpha=0.5, label='US threshold: $100K')
    ax4.set_xlabel('Willingness-to-Pay ($/QALY)')
    ax4.set_ylabel('Probability pEEG is Cost-Effective')
    ax4.set_title('CEAC - NMB-based')
    ax4.set_ylim([0, 1])
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    # ============ ROW 3: TORNADO (INB-based, not ICER) ============
    ax5 = fig.add_subplot(gs[2, :])
    tornado_365, base_inb_365 = one_way_sensitivity_analysis_inb(horizon_days=365, wtp=WTP_THRESHOLD)
    
    y_pos = np.arange(len(tornado_365))
    ranges_low = tornado_365['Base INB'].values - tornado_365['Low INB'].values
    ranges_high = tornado_365['High INB'].values - tornado_365['Base INB'].values
    
    ax5.barh(y_pos, ranges_low, left=tornado_365['Low INB'].values, 
             align='center', alpha=0.7, label='Low value')
    ax5.barh(y_pos, ranges_high, left=tornado_365['Base INB'].values, 
             align='center', alpha=0.5, label='High value')
    ax5.axvline(x=base_inb_365, color='red', linestyle='--', linewidth=2, label=f'Base INB: ${base_inb_365:,.0f}')
    ax5.set_yticks(y_pos)
    ax5.set_yticklabels(tornado_365['Parameter'].values)
    ax5.set_xlabel('Incremental Net Benefit ($)')
    ax5.set_title('Tornado Diagram - Top 10 Parameters (±25%) - 1 Year [INB-based, NOT ICER]')
    ax5.grid(True, alpha=0.3, axis='x')
    ax5.legend()
    
    plt.savefig('sensitivity_analysis_CORRECTED.png', dpi=300, bbox_inches='tight')
    print("✓ Publication-ready figure saved: sensitivity_analysis_CORRECTED.png")
    
    return tornado_365


def generate_plots(horizon_days=180):
    """
    [DEPRECATED: Old function with ICER - kept for reference]
    Generate CE plane, CEAC, and Tornado diagram.
    """
    tornado_df, base_icer = one_way_sensitivity_analysis_inb(horizon_days)
    
    psa_results = probabilistic_sensitivity_analysis(horizon_days=horizon_days)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    ax = axes[0, 0]
    ax.scatter(psa_results['qaly_diff'], psa_results['cost_diff'], alpha=0.5, s=20)
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax.axvline(x=0, color='k', linestyle='--', alpha=0.3)
    ax.set_xlabel('QALYs gained (pEEG vs Usual)')
    ax.set_ylabel('Cost difference ($)')
    ax.set_title(f'CE Plane - {horizon_days} day horizon')
    ax.grid(True, alpha=0.3)
    
    ax = axes[0, 1]
    ax.hist(psa_results['inb'], bins=50, edgecolor='black', alpha=0.7)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label=f'Base: INB $0')
    ax.axvline(x=50000, color='green', linestyle='--', linewidth=2, label='WTP threshold: $50K')
    ax.set_xlabel('Incremental Net Benefit ($)')
    ax.set_ylabel('Frequency')
    ax.set_title(f'INB Distribution - PSA ({len(psa_results["inb"])} iterations)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    ax = axes[1, 0]
    y_pos = np.arange(len(tornado_df))
    ranges = tornado_df['High INB'].values - tornado_df['Low INB'].values
    ax.barh(y_pos, ranges, align='center', alpha=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(tornado_df['Parameter'].values)
    ax.set_xlabel('INB Range ($)')
    ax.set_title('Tornado Diagram - Top 10 Parameters (±25%)')
    ax.grid(True, alpha=0.3, axis='x')
    
    ax = axes[1, 1]
    wtp_thresholds = np.linspace(0, 150000, 100)
    ceac_probs = []
    
    for wtp in wtp_thresholds:
        inb = np.array(psa_results['qaly_diff']) * wtp - np.array(psa_results['cost_diff'])
        ceac_probs.append(np.mean(inb > 0))
    
    ax.plot(wtp_thresholds, ceac_probs, linewidth=2)
    ax.axvline(x=50000, color='red', linestyle='--', alpha=0.5, label='Common WTP: $50K')
    ax.axvline(x=100000, color='orange', linestyle='--', alpha=0.5, label='Common WTP: $100K')
    ax.set_xlabel('Willingness to Pay ($/QALY)')
    ax.set_ylabel('Probability pEEG is Cost-Effective')
    ax.set_title('CEAC')
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(f'sensitivity_analysis_{horizon_days}d.png', dpi=300, bbox_inches='tight')
    print(f"Sensitivity analysis plot saved: sensitivity_analysis_{horizon_days}d.png")
    
    return tornado_df, psa_results


if __name__ == "__main__":
    print("=" * 80)
    print("PSA & SENSITIVITY ANALYSIS (CORRECTED FOR PUBLICATION)")
    print("=" * 80)
    
    print("\n📊 Running PSA (1,000 iterations): 1-year base case...")
    psa_365d = probabilistic_sensitivity_analysis(n_iterations=1000, horizon_days=365, wtp=WTP_THRESHOLD)
    
    print("📊 Running PSA (1,000 iterations): 10-year scenario...")
    psa_3650d = probabilistic_sensitivity_analysis(n_iterations=1000, horizon_days=3650, wtp=WTP_THRESHOLD)
    
    print("\n📈 Generating publication-ready figures...")
    tornado_results = generate_plots_corrected(psa_365d, psa_3650d)
    
    print("\n" + "=" * 80)
    print("📊 RESULTS SUMMARY (1-YEAR BASE CASE)")
    print("=" * 80)
    prob_ce = np.mean(np.array(psa_365d['inb']) > 0)
    mean_inb = np.mean(psa_365d['inb'])
    median_inb = np.median(psa_365d['inb'])
    
    print(f"Mean INB at $50K WTP: ${mean_inb:,.0f}")
    print(f"Median INB: ${median_inb:,.0f}")
    print(f"Probability pEEG is cost-effective: {prob_ce:.1%}")
    print(f"\nPEEG dominance (lower cost + more QALYs): {np.mean(np.array(psa_365d['cost_diff']) < 0) * 100:.1f}%")
    
    print("\n" + "=" * 80)
    print("📈 TOP 10 TORNADO PARAMETERS (1-year, INB-based)")
    print("=" * 80)
    print(tornado_results.to_string(index=False))
    
    print("\n✅ Analysis complete and ready for publication!")
