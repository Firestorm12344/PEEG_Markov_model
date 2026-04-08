# Sensitivity Analysis - CRITICAL CORRECTIONS FOR PUBLICATION

## ✅ Corrections Implemented

### 1. **Corrección de mortalidad por ciclo**
- La mortalidad en el primer ciclo ya se calcula con hazard por duración de ciclo.
- No se reutiliza indebidamente la probabilidad de 180 días en ciclos posteriores.
- Esto mantiene consistencia temporal en la tasa de muerte de cada ciclo.

### 2. **Horizontes soportados restaurados**
- El modelo principal vuelve a generar solo el base case de 180 días y el escenario opcional de 365 días.
- Se removió la reintroducción de resultados a 1, 5 y 10 años desde el script principal.
- Esto mantiene la implementación alineada con la estructura y evidencia soportadas por el modelo.

### 3. **PSA y análisis de sensibilidad**
- Se mantiene la PSA con distribuciones apropiadas para probabilidades, costos y ratios.
- Se usa NMB/INB en lugar de ICER para mayor estabilidad y mejor interpretación.
- La visualización corregida permanece limitada a 180 días y 365 días en `sensitivity_analysis_CORRECTED.png`.

---

## 📌 Resumen de cambios reales ahora implementados
- `model2_corrected_markov.py`:
  - primer ciclo de mortalidad correcto por hazard de ciclo
  - readmission cost correctamente acumulado por ciclo
  - horizontes de salida limitados nuevamente a 180 y 365 días

- `sensitivity_analysis.py`:
  - mantiene PSA de probabilidades, costos y ratios en distribuciones apropiadas
  - utiliza NMB/INB en lugar de ICER para mayor robustez
  - produce gráficos de CEAC y tornado correctos para 180 días y 365 días

---

## 🧠 Nota importante
El modelo mantiene los horizontes clínicamente soportados por la especificación original: 180 días como base case y 365 días como escenario opcional.

La extensión a 5 y 10 años quedó removida del flujo principal hasta que exista una estructura de largo plazo explícitamente validada.
