# Especificación del modelo · Survival Engine

Este documento resume el modelo matemático y lógico del proyecto. Las funciones de reparación y de curación con pociones forman parte de la especificación, pero todavía no están implementadas en el código; el resto lo calcula `src/survival_engine.py`.

## 1. Variables y dominios

| Variable | Símbolo | Conjunto | Dominio |
|---|---|---|---|
| Vida del jugador | v | Reales | v ∈ [0, 100] |
| Energía | e | Reales | e ∈ [0, 100] |
| Inventario ocupado | x | Naturales con cero | x ∈ [0, 30] ∩ ℕ₀ |
| Nivel del personaje | n | Naturales | n ∈ [1, 50] ∩ ℕ |
| Tiempo de partida (min) | t | Reales no negativos | t ∈ [0, +∞) |
| Nivel del enemigo | k | Naturales | k ∈ [1, 10] ∩ ℕ |
| Madera | m | Naturales con cero | m ∈ [0, 99] ∩ ℕ₀ |
| Piedra | p | Naturales con cero | p ∈ [0, 99] ∩ ℕ₀ |

Las cantidades de objetos son naturales porque no se puede cargar una fracción de herramienta. La vida y la energía son reales para admitir daños y consumos con decimales.

**Control de bordes:** `v_nuevo = min(100, max(0, v_calculado))`. Un daño de 150 deja la vida en 0, no en −50, y eso dispara la regla de derrota.

## 2. Funciones

| Función | Fórmula | Tipo |
|---|---|---|
| Energía al correr | `E_correr(t) = 5·t` | Lineal |
| Costo de la antorcha | 2 de madera + 1 de piedra | Lineal |
| Reparación de herramientas | `C(d) = 0,5·d² + 2·d`, con d ∈ [0, 100] | Cuadrática |
| Curación con pociones | `v_nuevo = min(100, v_actual + 15·q)` | Compuesta |
| Costo del refugio | `C_total(t) = 150 + 2,5·t` | Lineal |

La reparación es cuadrática a propósito: arreglar una herramienta casi rota (d = 100, costo 5200) cuesta más de 74 veces lo que cuesta un desgaste leve (d = 10, costo 70), lo que desalienta postergar el mantenimiento.

## 3. Progresiones

- **Experiencia por nivel (aritmética):** `aₙ = 100 + (n − 1)·50` → 100, 150, 200, … 550 XP para pasar del nivel 10 al 11.
- **Daño de enemigos (geométrica):** `Dₖ = 10·2^(k − 1)` → 10, 20, 40, … 160 en el nivel 5, letal para una vida de 100.

## 4. Teoría de conjuntos

- Universo: U = {madera, piedra, comida, metal, antorcha, espada, poción, mineral, hacha, pico}
- Recursos del entorno: R = {madera, piedra, comida, metal}
- Requisitos de la antorcha: C = {madera, piedra}

Con un inventario I = {madera, piedra, antorcha}:

| Operación | Uso en el juego | Resultado |
|---|---|---|
| I ∩ R | Materias primas que tiene el jugador | {madera, piedra} |
| I − C | Inventario después de craftear | {antorcha} |
| Iᶜ = U − I | Ítems que todavía no consiguió (logros) | {comida, metal, espada, poción, mineral, hacha, pico} |

## 5. Reglas lógicas

**Acceso a la zona peligrosa:** `p ∧ q → Z`, con p: energía ≥ 50 y q: tiene antorcha.

| p | q | Z |
|---|---|---|
| V | V | V |
| V | F | F |
| F | V | F |
| F | F | F |

**Alerta de cansancio:** `r ∧ ¬s → A`, con r: energía < 20 y s: tiene comida. Se activa solo con energía crítica y sin comida.

**Derrota:** `u ∨ (w ∧ ¬s) → D`, con u: vida = 0, w: energía = 0 y s: tiene comida. Se pierde con la vida en 0, o con la energía en 0 sin comida para recuperarla. De las 8 combinaciones posibles, 5 terminan en derrota.

## 6. Ecuaciones

**Punto de equilibrio del refugio:** el consumo `8·t` iguala a la regeneración `200 + 3·t` cuando `5·t = 200`, es decir, a los **t\* = 40 minutos**.

**Sistema 2×2 (crafteo sin sobrantes):** con 55 de madera y 30 de piedra, ¿cuántas antorchas (x₁) y picos (x₂) se pueden fabricar usando todo?

```
2·x₁ + 3·x₂ = 55
1·x₁ + 2·x₂ = 30
```

Por la regla de Cramer: Δ = 1, Δx₁ = 20, Δx₂ = 5 → **20 antorchas y 5 picos**.

**Sistema 3×3 (presupuesto del motor):** reparto de 1200 unidades entre física (y₁), IA (y₂) e interfaz (y₃).

```
y₁ + y₂ + y₃ = 1200
2·y₁ − y₂    = 200
3·y₂ − 2·y₃  = 200
```

Por sustitución: **y₁ = 300, y₂ = 400, y₃ = 500**.

## 7. Matriz de casos de prueba

| Caso | Escenario | Resultado esperado |
|---|---|---|
| 1 | Corre 4 minutos con energía 80 | Energía 60, estado estable |
| 2 | Intenta entrar a la cueva con energía 40 y sin antorcha | Acceso denegado |
| 3 | Craftea una antorcha con energía 75 y entra a la cueva | Acceso concedido |
| 4 | Combate contra un enemigo de nivel 3 con vida 100 | Vida 60, necesita 150 XP para el nivel 3 |
| 5 | Vida 10, energía 0 y sin comida | Derrota por inanición |

Los cinco casos se ejecutan con `python src/survival_engine.py` y dan los resultados esperados.
