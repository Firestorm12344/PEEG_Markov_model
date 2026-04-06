# Modelo 2 corregido explicado en lenguaje simple

## 1) ¿De qué trata el estudio?
El estudio pregunta si usar pEEG (electroencefalografía procesada durante la anestesia)
vale la pena en pacientes mayores con cirugía de fractura de cadera.

La idea clínica es esta:
- si la anestesia se guía mejor con pEEG,
- podría haber menos delirium postoperatorio,
- y si hay menos delirium,
- entonces podría haber menos rehabilitación institucional, menos mortalidad y mejor calidad de vida.

En economía de la salud eso se resume en dos resultados:
- **costos** en USD
- **QALYs**, que son años de vida ajustados por calidad

---

## 2) ¿Qué es un modelo de Markov?
Un modelo de Markov es un modelo que sigue a una cohorte de pacientes en el tiempo.
En cada ciclo, cada paciente puede quedarse en su estado o pasar a otro estado.

Aquí los estados son:
- postoperatorio sin delirium
- postoperatorio con delirium
- recuperación en casa
- recuperación en rehabilitación
- muerte

Cada mes el modelo pregunta:
- ¿sigue vivo?
- ¿está en casa o en rehab?
- ¿qué utilidad tiene ese estado?
- ¿qué costo genera?

Entonces el modelo va sumando:
- costos
- QALYs
- muertes
- altas a rehabilitación

No sigue a una persona real una por una.
Sigue a una **cohorte promedio** de pacientes.

---

## 3) ¿Qué hace el código?
### A. Define los parámetros
Se guardan probabilidades, costos y utilidades:
- probabilidad de delirium
- riesgo de muerte
- probabilidad de rehab
- costo del delirium
- costo por caso de pEEG
- utilidades para calcular QALYs

### B. Convierte OR a probabilidad
Si un paper te da odds ratio, el código usa:

p1 = OR * p0 / (1 - p0 + OR * p0)

Eso sirve para convertir un efecto relativo a una probabilidad absoluta.

### C. Corre el Markov
La función `run_markov()`:
1. arma la cohorte inicial
2. distribuye pacientes según tengan delirium o no
3. en el primer ciclo calcula muertes y paso a casa/rehab
4. en los ciclos siguientes acumula QALYs y muertes
5. devuelve costo total y QALYs por paciente

### D. Compara estrategias
Se corre el modelo para:
- anestesia usual
- anestesia guiada con pEEG

Luego se calcula:
- costo incremental = costo pEEG - costo usual
- QALY incremental = QALY pEEG - QALY usual

Si:
- costo incremental < 0
- QALY incremental > 0

entonces pEEG es dominante.

---

## 4) ¿Qué corregí respecto al modelo anterior?
El gráfico CEAC anterior salía plano en 1.0.
Eso significaba que en prácticamente todas las simulaciones pEEG era perfecto.

Para corregirlo hice 3 cambios:
1. usé un efecto más conservador para pEEG:
   RR = 0.81 en vez del efecto absoluto muy grande
2. amplié la incertidumbre en la PSA
3. agregué un costo por caso de pEEG más realista como escenario de implementación
   (sensor + monitor amortizado + overhead)

Así el CEAC deja de ser artificialmente perfecto.

---

## 5) ¿Cómo leer los resultados?
- **USD**: costo esperado por paciente
- **QALY**: beneficio en salud ajustado por calidad
- **Incremental**:
  - negativo en costo = ahorra dinero
  - positivo en QALY = mejora salud

---

## 6) ¿Qué es el tornado?
Es un análisis de sensibilidad de una vía.
Se mueve un parámetro a un valor bajo y alto para ver cuánto cambia el resultado económico.

Los parámetros que más mueven el resultado son los más importantes.

---

## 7) ¿Qué es la PSA?
PSA = probabilistic sensitivity analysis

No usa un solo valor fijo por parámetro.
Usa distribuciones:
- Beta para probabilidades
- Gamma para costos
- Lognormal para OR

Luego corre miles de simulaciones.

Con eso se construyen:
- el cost-effectiveness plane
- la CEAC

---

## 8) Advertencia metodológica
Este archivo corregido es útil para entender el modelo y tener una base de trabajo.
Pero si quieres paper fuerte, todavía conviene:
- validar costos locales reales de pEEG
- decidir si usarás 180 días como base-case principal
- justificar mejor la extensión a 1, 5 y 10 años
