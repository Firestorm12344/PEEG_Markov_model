# Markov Model - Actualización 180 Días / 1 Año

**Version:** 2.0  
**Date:** April 5, 2026  
**Status:** ✅ Complete per "peeg_model_modification_spec.docx"

## Resumen Ejecutivo de Cambios

Se ha refactorizado completamente el modelo Markov de hip-fracture con delirium para:
1. **Cambiar de horizonte anual (1, 5, 10 años) → 180 días (base case) + 365 días (scenario)**
2. **Implementar ciclos bifásicos**: semanales en fase aguda (días 0-84) + mensuales en fase post-aguda (días 85-180)
3. **Agregar manejo explícito de readmission**: nuevo estado "Readmitted" con transiciones y costos
4. **Mejorar cálculo probabilístico**: conversión correcta via hazard diario (funciona con cualquier duración de ciclo)
5. **Hacer utilities y descuento conscientes del ciclo**: QALYs = utility × (cycle_days/365), no hardcodeado /12

## Cambios Principales (Sección por Sección del Documento)

### 1. Temporal Horizon (Sección 4.1)
**Anterior:**
```python
for years in [1, 5, 10]:
    usual = run_markov("Usual anesthesia", years, BASE)
    peeg = run_markov("pEEG-guided anesthesia", years, BASE)
```

**Nuevo:**
```python
for horizon_days in [180, 365]:
    usual = run_markov("Usual anesthesia", horizon_days, BASE)
    peeg = run_markov("pEEG-guided anesthesia", horizon_days, BASE)
```

**Justificación:**
- 180 días: Captura la trayectoria completa de delirium agudo, decisión de egreso, rehabilitación, y readmisión
- 365 días: Escenario opcional para evaluar si los beneficios persisten más allá del período de seguimiento clínico
- **Removidos:** 5 y 10 años (recomendado en documento: no presentar sin estructura de largo plazo adicional)

---

### 2. Ciclos Bifásicos (Sección 4.2 & 3.1)

**Función Nueva: `build_cycle_schedule(horizon_days)`**

```python
def build_cycle_schedule(horizon_days):
    cycles = []
    # Phase A: 12 ciclos semanales (0-84 días)
    for week in range(12):
        cycles.append(7)
    
    # Phase B: Ciclos mensuales (85-horizon_days)
    remaining_days = horizon_days - 84
    num_months = int(np.ceil(remaining_days / 30.44))
    days_per_month = remaining_days / num_months
    for _ in range(num_months):
        cycles.append(days_per_month)
    
    return cycles
```

**Ventajas:**
- Resolución fina (semanal) en fase aguda donde ocurren cambios rápidos de delirium
- Resolución coarser (mensual) en fase post-aguda más estable
- Modelado clínicamente más defensible
- **Nota:** 180d → 12 semanales + 4-5 mensuales ≈ 16-17 ciclos totales

---

### 3. Conversión de Probabilidades via Hazard Diario (Sección 4.3)

**Anterior (INCORRECTO):**
```python
p_mort_month = monthly_prob_from_cumulative(p_cum=0.124, months=6)
# Asumía siempre 6 meses iguales: p_month ≈ 0.0214 (2.14%)
# Luego se multiplicaba siempre /12 en acumulación de QALYs
```

**Nuevo (CORRECTO):**
```python
def cycle_prob_from_cumulative_hazard(p_cum, period_days, cycle_days):
    daily_hazard = -math.log(1 - p_cum) / period_days
    return 1 - math.exp(-daily_hazard * cycle_days)

# Ejemplo: Mortalidad 180d = 12.4%
# Daily hazard = -ln(0.876) / 180 = 0.000695 / día
# P(muerte en semana 1) = 1 - exp(-0.000695 × 7) = 0.486%
# P(muerte en mes 5) = 1 - exp(-0.000695 × 30) = 2.06%
```

**Ventajas:**
- Matemáticamente correcto: respeta el concepto de "hazard rate" 
- **Flexible:** Funciona con cualquier duración de ciclo
- Evita hardcoding de "6 meses" o "12 meses"

---

### 4. Utilities Conscientes del Ciclo (Sección 4.4)

**Anterior:**
```python
total_qaly += survivors * utility / 12 * discount
# Asume siempre que el ciclo es 1 mes (1/12 del año)
```

**Nuevo:**
```python
total_qaly += survivors * utility * (cycle_days / 365.0) * discount
# Escalado dinámico: 7-day cycle = 7/365, 30-day cycle = 30/365
```

**Nueva Función: `utility_home_by_days(elapsed_days, params)`**
- Mapea utilidades a días en lugar de meses
- Interpolación lineal días 30→120 (corresponde a meses 1→4)

**Descuento También Mejorado:**
```python
cycle_midpoint_days = elapsed_days + cycle_days / 2.0
discount = 1 / ((1 + rate) ** (cycle_midpoint_days / 365.0))
# Basado en días exactos, no meses
```

---

### 5. Manejo Explícito de Readmission (Sección 4.5 & 3.2)

**Cambio 1: Nuevo Estado**
```python
STATES = [..., 'readmitted', 'death']  # Agregado 'readmitted'
```

**Cambio 2: Probabilidades de Readmission**
```python
# Readmission risk (conditional on delirium history)
p_readmit_180_no_delirium = 0.36  # agregado a BASE
or_readmit_delirium = 1.79         # ya existía

# Convertir a hazards diarios
p_readmit_daily_nd = -ln(1 - 0.36) / 180
p_readmit_cycle_nd = 1 - exp(-p_readmit_daily_nd * cycle_days)
```

**Cambio 3: Transiciones de Readmission**
```python
# Competing risks en ciclos posteriores: readmit vs death vs stay home
readmits = pop * p_readmit
non_readmits = pop * (1 - p_readmit)
deaths = non_readmits * p_mort
survivors = non_readmits * (1 - p_mort)

new[IDX["readmitted"]] += readmits
new[IDX["death"]] += deaths
new[IDX[state]] += survivors

# Readmitted tunnel state: revierte a home después de 1 ciclo
readmit_survivors = readmit_pop * (1 - p_mort)
new[IDX["home_no_delirium_history"]] += readmit_survivors
```

**Cambio 4: Costos de Readmission**
```python
BASE['cost_readmission'] = 5000.0  # agregado
BASE['u_readmit'] = 0.2             # agregado

total_cost += readmits * cost_readmission
total_qaly += readmit_survivors * u_readmit * (cycle_days / 365.0) * discount
```

**Cambio 5: Outputs**
```python
# Nuevo campo en CSV
"readmissions_per_patient": float(total_readmit)
```

---

## Archivos Modificados y Nuevos

### Modificados
- **model2_corrected_markov.py**: Refactorizado completamente con nuevas funciones y lógica de ciclos

### Nuevos
- **model2_corrected_outputs_180d_1y.csv**: Salidas para 180d + 365d
- **sensitivity_analysis.py**: Análisis PSA, tornado, CE plane, CEAC
- **sensitivity_analysis_180d.png**: Figuras para base case (180d)
- **sensitivity_analysis_365d.png**: Figuras para scenario (365d)
- **README.md**: Documentación completa (costos incluidos/excluidos, asunciones, interpretación)
- **CHANGELOG.md**: Este documento

---

## Validation & Testing

✅ **Modelo Ejecutable**
```
180-day base case: ✅ Runs, ~0.22 QALYs, ~$1,685-1,935 cost
365-day scenario: ✅ Runs, ~0.46-0.47 QALYs, ~$1,788-2,060 cost
4 escenarios procesados exitosamente
```

✅ **Lógica de Readmission**
- Readmissions reportadas: 0.41-0.80 por paciente (depend en horizon)
- Transiciones correctas: pop → readmit → home (tunnel state)
- Costos y utilidades aplicadas adecuadamente

✅ **Sensibilidad**
- PSA: 1,000 iteraciones, 10+ parámetros con variabilidad
- CE plane: Mayoría pEEG es "dominated" o better (lower cost, better QALYs)
- CEAC: pEEG probablemente cost-effective en thresholds comunes ($50K-$100K)
- Tornado: Top parámetros sensibles = RR delirium, utilidades, costos

---

## Resultados Base Case (180 Días)

| Métrica | Usual | pEEG | Diferencia |
|---------|-------|------|------------|
| Costo | $1,934.89 | $1,687.26 | -$247.63 (pEEG menor) |
| QALYs | 0.2200 | 0.2209 | +0.0009 |
| Delirium | 20.34% | 16.48% | -3.86% |
| Rehab % | 34.57% | 33.64% | -0.93% |
| Muertes | 8.44% | 8.31% | -0.13% |
| Readmit | 0.416 | 0.411 | -0.005 |
| **ICER** | - | - | **pEEG DOMINANTE** (menor costo, más QALYs) |

---

## Próximos Pasos Recomendados

1. **Validación clínica**: Presentar a equipo clínico para feedback sobre plausibilidad
2. **Análisis de subgrupos**: Edad, fragilidad, comorbilidades
3. **Budget impact**: Estimación de ahorro si se adopta pEEG hospital-wide
4. **Extensión de horizonte**: Si hay datos de largo plazo, agregar institutionalización persistente
5. **Readmission mejorada**: Modelar como estado recurrente (not just tunnel) si hay evidencia de re-readmisión

---

## Cumplimiento de Requisitos del Documento

✅ Sección 4.1: Remover año hardcoded (for years in [1,5,10])  
✅ Sección 4.2: Generalizar manejo de ciclos  
✅ Sección 4.3: Conversión correcta de probabilidades  
✅ Sección 4.4: Utilidades conscientes del ciclo  
✅ Sección 4.5: Manejo explícito de readmission  
✅ Sección 5: Plan de implementación completado  
✅ Sección 7 (Deliverables):
  - ✅ Revised Python script con comentarios
  - ✅ CSV outputs para 180d + 365d
  - ✅ PSA, CE plane, CEAC, Tornado figures
  - ✅ README especificando costos incluidos/excluidos
  - ✅ CHANGELOG (este documento)

---

## Notas Técnicas

- Probabilidades convertidas usando CDF inverso (hazard rate constante)
- Descuento aplicado per-cycle en punto medio
- Matriz trace: 17 filas (16 ciclos + inicial) × 8 columnas (estados)
- Sem cycles: siempre 12 (0-84 días)
- Monthly cycles: variable (depends en horizon_days)
  - 180d: ~4 meses (96 días restantes)
  - 365d: ~11 meses (281 días restantes)

---

**End of Changelog**

