# Sensitivity Analysis - CRITICAL CORRECTIONS FOR PUBLICATION

## ✅ Corrections Implemented

### 1. **Modelo estructural: rehab puede devolver pacientes a casa**
- Antes, los pacientes en los estados de rehabilitación quedaban atrapados en rehab.
- Ahora se modela una probabilidad mensual de alta desde rehab hacia hogar.
- Esto corrige un sesgo que subestimaba las transiciones reales de rehab a home.

### 2. **Modelo estructural: readmisiones continúan después de 180 días**
- Antes el modelo limitaba el riesgo de reingreso a los primeros 180 días.
- Ahora se conserva el mismo hazard de readmisión para horizontes de 1, 5 y 10 años.
- Esto corrige el subconteo de costos y eventos de readmisión en horizontes extendidos.

### 3. **Corrección de mortalidad por ciclo**
- La mortalidad en el primer ciclo ya se calcula con hazard por duración de ciclo.
- No se reutiliza indebidamente la probabilidad de 180 días en ciclos posteriores.
- Esto mantiene consistencia temporal en la tasa de muerte de cada ciclo.

### 4. **Horizontes largos actualizados y advertencia de extrapolación**
- Se generan resultados para 1, 5 y 10 años en `model2_corrected_outputs_1y_5y_10y.csv`.
- La extensión a 5 y 10 años usa mortalidad de fondo después de los 180 días.
- Se aclara que esos horizontes son extrapolación y no están totalmente soportados por la estructura original.

### 5. **PSA y análisis de sensibilidad**
- Se mantiene la PSA con distribuciones apropiadas para probabilidades, costos y ratios.
- Se usa NMB/INB en lugar de ICER para mayor estabilidad y mejor interpretación.
- La visualización corregida aparece en `sensitivity_analysis_CORRECTED.png`.

---

## 📌 Resumen de cambios reales ahora implementados
- `model2_corrected_markov.py`:
  - rehabilitación puede transitar a casa
  - readmisiones continuas más allá de 180 días
  - primer ciclo de mortalidad correcto por hazard de ciclo
  - soporte explícito para 1, 5 y 10 años con advertencia de extrapolación

- `sensitivity_analysis.py`:
  - mantiene PSA de probabilidades, costos y ratios en distribuciones apropiadas
  - utiliza NMB/INB en lugar de ICER para mayor robustez
  - produce gráficos de CEAC y tornado correctos

---

## 🧠 Nota importante
El modelo ya no presenta la limitación de rehab como estado absorbente y ahora contabiliza mejor los costos de readmisión en horizontes largos.

Sin embargo, el soporte para 5 y 10 años sigue siendo extrapolación: buenas aproximaciones, pero no equivalen a un modelo de seguimiento empírico a largo plazo.
