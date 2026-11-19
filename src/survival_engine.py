"""
================================================================================
 SURVIVAL ENGINE - Prototipo funcional
 Proyecto ABP - Elementos de Matemática y Lógica
 Tecnicatura Superior en Desarrollo de Software (ISPC)

 Implementa de forma literal el modelo matemático-lógico especificado en el
 documento de diseño:
   - Restricciones de dominio e intervalos (control de bordes / truncamiento)
   - Funciones matemáticas explícitas (consumo de energía, costo de crafteo)
   - Sucesiones y progresiones (XP por nivel, daño de enemigos)
   - Teoría de conjuntos (inventario, recursos, recetas)
   - Lógica proposicional (reglas de negocio Z, A, D)
   - Sistemas de ecuaciones lineales (crafteo 2x2, presupuesto 3x3)
   - Matriz de simulación con casos de prueba
================================================================================
"""

from dataclasses import dataclass, field
from typing import Set, Dict, List, Tuple
from fractions import Fraction


# ==============================================================================
# 1. RESTRICCIONES DE DOMINIO E INTERVALOS
# ==============================================================================

def clamp(valor: float, minimo: float, maximo: float) -> float:
    """Control de bordes (truncamiento). Ej: v_nuevo = min(100, max(0, v))."""
    return min(maximo, max(minimo, valor))


def validar_natural_con_cero(valor: int, maximo: int, nombre: str) -> int:
    """Valida que una variable discreta (N0) esté en [0, maximo]."""
    if not float(valor).is_integer():
        raise ValueError(f"{nombre} debe ser un número natural, se recibió {valor}")
    valor = int(valor)
    if valor < 0 or valor > maximo:
        raise ValueError(f"{nombre} fuera de dominio [0, {maximo}]: {valor}")
    return valor


# ==============================================================================
# 2. ENTIDAD JUGADOR (variables de estado con sus dominios formales)
# ==============================================================================

@dataclass
class Jugador:
    v: float = 100.0          # Vida        v ∈ [0, 100] ⊂ R
    e: float = 100.0          # Energía     e ∈ [0, 100] ⊂ R
    x: int = 0                # Inventario ocupado   x ∈ [0, 30] ∩ N0
    n: int = 1                # Nivel       n ∈ [1, 50] ∩ N
    t: float = 0.0            # Tiempo de partida (min)  t ∈ [0, +inf)
    m: int = 0                # Madera      m ∈ [0, 99] ∩ N0
    p: int = 0                # Piedra      p ∈ [0, 99] ∩ N0
    inventario: Set[str] = field(default_factory=set)  # I ⊆ U
    derrotado: bool = False
    alerta_cansancio: bool = False

    def aplicar_dano(self, dano: float):
        """Aplica daño con control de bordes (truncamiento en [0,100])."""
        self.v = clamp(self.v - dano, 0.0, 100.0)
        self._evaluar_derrota()

    def curar(self, cantidad: float):
        self.v = clamp(self.v + cantidad, 0.0, 100.0)

    def correr(self, minutos: float):
        """Aplica la función E_correr(t) = 5 * t."""
        gasto = SurvivalEngineMath.energia_correr(minutos)
        self.e = clamp(self.e - gasto, 0.0, 100.0)
        self.t += minutos
        self._evaluar_alerta()
        self._evaluar_derrota()

    def _evaluar_alerta(self):
        """Regla de negocio 2: r ∧ ¬s → A"""
        r = self.e < 20
        s = "comida" in self.inventario
        self.alerta_cansancio = LogicaProposicional.regla_alerta_cansancio(r, s)

    def _evaluar_derrota(self):
        """Regla de negocio 3: u ∨ (w ∧ ¬s) → D"""
        u = self.v == 0
        w = self.e == 0
        s = "comida" in self.inventario
        self.derrotado = LogicaProposicional.regla_derrota(u, w, s)

    def puede_acceder_zona_peligrosa(self) -> bool:
        """Regla de negocio 1: p ∧ q → Z"""
        p_energia = self.e >= 50
        q_antorcha = "antorcha" in self.inventario
        return LogicaProposicional.regla_acceso_zona(p_energia, q_antorcha)


# ==============================================================================
# 3. FUNCIONES MATEMÁTICAS EXPLÍCITAS
# ==============================================================================

class SurvivalEngineMath:

    @staticmethod
    def energia_correr(t_min: float) -> float:
        """E_correr(t) = 5 * t   (t en R>=0, minutos)"""
        if t_min < 0:
            raise ValueError("t debe ser >= 0")
        return 5 * t_min

    @staticmethod
    def costo_antorcha(m: int, p: int) -> bool:
        """
        C_antorcha(m, p) = 2*m + 1*p  -> requiere exactamente 2 madera y 1 piedra.
        Devuelve True si hay insumos suficientes para craftear.
        """
        return m >= 2 and p >= 1

    @staticmethod
    def xp_requerida(n: int) -> int:
        """Progresión aritmética: a_n = 100 + (n-1)*50, a_1 = 100, d = 50"""
        return 100 + (n - 1) * 50

    @staticmethod
    def dano_enemigo(k: int) -> float:
        """Progresión geométrica: D_k = 10 * 2^(k-1), D_1 = 10, r = 2"""
        return 10 * (2 ** (k - 1))

    @staticmethod
    def costo_total_refugio(t_min: float) -> float:
        """C_total(t) = 150 + 2.5*t"""
        return 150 + 2.5 * t_min

    @staticmethod
    def punto_equilibrio_refugio() -> float:
        """
        Resuelve E_cons(t) = E_regen(t)
        8t = 200 + 3t  ->  5t = 200  ->  t* = 40
        """
        e_cons_coef, e_regen_base, e_regen_coef = 8, 200, 3
        t_star = e_regen_base / (e_cons_coef - e_regen_coef)
        return t_star


# ==============================================================================
# 4. LÓGICA PROPOSICIONAL (reglas de negocio formalizadas)
# ==============================================================================

class LogicaProposicional:

    @staticmethod
    def regla_acceso_zona(p_energia_suficiente: bool, q_tiene_antorcha: bool) -> bool:
        """Z: p ∧ q → Z  (acceso permitido si energía>=50 Y tiene antorcha)"""
        return p_energia_suficiente and q_tiene_antorcha

    @staticmethod
    def regla_alerta_cansancio(r_energia_critica: bool, s_tiene_comida: bool) -> bool:
        """A: r ∧ ¬s → A  (alerta si energía<20 Y NO tiene comida)"""
        return r_energia_critica and (not s_tiene_comida)

    @staticmethod
    def regla_derrota(u_vida_cero: bool, w_energia_cero: bool, s_tiene_comida: bool) -> bool:
        """D: u ∨ (w ∧ ¬s) → D  (derrota si vida=0, O (energía=0 Y sin comida))"""
        return u_vida_cero or (w_energia_cero and (not s_tiene_comida))

    @staticmethod
    def generar_tabla_verdad(regla, variables: List[str]) -> List[Tuple]:
        """Genera exhaustivamente la tabla de verdad de una regla de N variables."""
        n = len(variables)
        filas = []
        for i in range(2 ** n):
            combinacion = [bool((i >> (n - 1 - j)) & 1) for j in range(n)]
            resultado = regla(*combinacion)
            filas.append((*combinacion, resultado))
        return filas


# ==============================================================================
# 5. TEORÍA DE CONJUNTOS
# ==============================================================================

class ConjuntosJuego:
    UNIVERSO: Set[str] = {"madera", "piedra", "comida", "metal", "antorcha",
                           "espada", "pocion", "mineral", "hacha", "pico"}
    RECURSOS_ENTORNO: Set[str] = {"madera", "piedra", "comida", "metal"}
    REQUISITOS_ANTORCHA: Set[str] = {"madera", "piedra"}

    @staticmethod
    def interseccion_inventario_recursos(inventario: Set[str]) -> Set[str]:
        """I ∩ R"""
        return inventario & ConjuntosJuego.RECURSOS_ENTORNO

    @staticmethod
    def diferencia_tras_crafteo(inventario: Set[str], requisitos: Set[str]) -> Set[str]:
        """I - C_antorcha"""
        return inventario - requisitos

    @staticmethod
    def complemento_inventario(inventario: Set[str]) -> Set[str]:
        """I^c = U - I  (ítems que el jugador todavía no posee)"""
        return ConjuntosJuego.UNIVERSO - inventario


# ==============================================================================
# 6. SISTEMAS DE ECUACIONES LINEALES
# ==============================================================================

class AlgebraLineal:

    @staticmethod
    def resolver_2x2_cramer(a: float, b: float, c: float,
                             d: float, e: float, f: float) -> Tuple[float, float]:
        """
        Resuelve:  a*x1 + b*x2 = e
                   c*x1 + d*x2 = f
        mediante la Regla de Cramer. Devuelve (x1, x2).
        """
        det_principal = a * d - b * c
        if det_principal == 0:
            raise ValueError("Sistema sin solución única (determinante = 0)")
        det_x1 = e * d - b * f
        det_x2 = a * f - e * c
        return det_x1 / det_principal, det_x2 / det_principal

    @staticmethod
    def resolver_crafteo(madera_disp: int, piedra_disp: int) -> Tuple[float, float]:
        """
        Sistema del documento:
          2*x1 + 3*x2 = madera_disp
          1*x1 + 2*x2 = piedra_disp
        x1 = antorchas, x2 = picos de piedra
        """
        return AlgebraLineal.resolver_2x2_cramer(2, 3, 1, 2, madera_disp, piedra_disp)

    @staticmethod
    def resolver_presupuesto_3x3(total: float) -> Tuple[float, float, float]:
        """
        Sistema del documento (sustitución):
          y1 + y2 + y3 = total
          2*y1 - y2 = 200
          3*y2 - 2*y3 = 200
        Devuelve (y1, y2, y3) generalizado para 'total'.
        """
        # y2 = 2y1 - 200 ; y3 = 3y1 - 400  (derivado algebraicamente, ver documento)
        # y1 + (2y1-200) + (3y1-400) = total  ->  6y1 - 600 = total
        y1 = (total + 600) / 6
        y2 = 2 * y1 - 200
        y3 = 3 * y1 - 400
        return y1, y2, y3


# ==============================================================================
# 7. MATRIZ DE SIMULACIÓN (5 casos de prueba del documento, reproducidos)
# ==============================================================================

def ejecutar_caso(nombre: str, jugador: Jugador, accion):
    print(f"\n--- {nombre} ---")
    print(f"Estado inicial: v={jugador.v}, e={jugador.e}, x={jugador.x}, "
          f"n={jugador.n}, t={jugador.t}, inventario={jugador.inventario}")
    accion(jugador)
    estado = "DERROTA (Game Over)" if jugador.derrotado else (
        "Alerta de cansancio activa" if jugador.alerta_cansancio else "Estable")
    print(f"Estado final:   v={jugador.v}, e={jugador.e}, x={jugador.x}, "
          f"t={jugador.t} -> {estado}")


def caso_1_huir_amenaza():
    j = Jugador(v=100, e=80, x=2, n=1, t=0, inventario={"madera", "piedra"})
    ejecutar_caso("Caso 1: Huir de amenaza", j, lambda jug: jug.correr(4))


def caso_2_acceso_denegado():
    j = Jugador(v=100, e=40, x=1, n=1, t=10, inventario={"madera"})

    def accion(jug):
        acceso = jug.puede_acceder_zona_peligrosa()
        print(f"¿Acceso a Zona Peligrosa concedido? {acceso}")

    ejecutar_caso("Caso 2: Intento de acceso denegado", j, accion)


def caso_3_crafteo_y_acceso():
    j = Jugador(v=90, e=75, x=3, n=1, t=15, m=2, p=1,
                inventario={"madera", "piedra"})

    def accion(jug):
        if SurvivalEngineMath.costo_antorcha(jug.m, jug.p):
            jug.m -= 2
            jug.p -= 1
            jug.inventario.discard("madera")
            jug.inventario.discard("piedra")
            jug.inventario.add("antorcha")
            jug.x = 1
        acceso = jug.puede_acceder_zona_peligrosa()
        print(f"Antorcha crafteada. ¿Acceso concedido? {acceso}")

    ejecutar_caso("Caso 3: Crafteo y acceso exitoso", j, accion)


def caso_4_combate():
    j = Jugador(v=100, e=60, x=1, n=2, t=20, inventario={"antorcha"})

    def accion(jug):
        dano = SurvivalEngineMath.dano_enemigo(k=3)
        jug.aplicar_dano(dano)
        xp_necesaria = SurvivalEngineMath.xp_requerida(n=2)
        print(f"Daño recibido de enemigo nivel 3: {dano}. "
              f"XP requerida para subir de nivel: {xp_necesaria}")

    ejecutar_caso("Caso 4: Combate en cueva con enemigo", j, accion)


def caso_5_derrota_inanicion():
    j = Jugador(v=10, e=0, x=0, n=2, t=30, inventario=set())

    def accion(jug):
        jug._evaluar_alerta()
        jug._evaluar_derrota()

    ejecutar_caso("Caso 5: Crítico y derrota por inanición", j, accion)


# ==============================================================================
# 8. DEMO / PUNTO DE ENTRADA
# ==============================================================================

def demo_completa():
    print("=" * 70)
    print(" SURVIVAL ENGINE - Demostración del modelo lógico-matemático")
    print("=" * 70)

    # --- Progresiones ---
    print("\n[Progresión aritmética - XP por nivel]")
    for n in [1, 2, 3, 10]:
        print(f"  Nivel {n} -> {n+1}: {SurvivalEngineMath.xp_requerida(n)} XP")

    print("\n[Progresión geométrica - Daño de enemigos]")
    for k in [1, 2, 3, 5]:
        print(f"  Enemigo nivel {k}: {SurvivalEngineMath.dano_enemigo(k)} de daño")

    # --- Punto de equilibrio ---
    print("\n[Punto de equilibrio del refugio]")
    t_star = SurvivalEngineMath.punto_equilibrio_refugio()
    print(f"  t* = {t_star} minutos")

    # --- Sistema 2x2 ---
    print("\n[Sistema 2x2 - Balance de crafteo]")
    x1, x2 = AlgebraLineal.resolver_crafteo(55, 30)
    print(f"  Antorchas: {x1}, Picos de piedra: {x2}")

    # --- Sistema 3x3 ---
    print("\n[Sistema 3x3 - Asignación de presupuesto]")
    y1, y2, y3 = AlgebraLineal.resolver_presupuesto_3x3(1200)
    print(f"  Física: {y1}, IA Enemigos: {y2}, UI/Inventario: {y3}")

    # --- Conjuntos ---
    print("\n[Teoría de conjuntos]")
    inv = {"madera", "piedra", "antorcha"}
    print(f"  I ∩ R = {ConjuntosJuego.interseccion_inventario_recursos(inv)}")
    print(f"  I - C_antorcha = {ConjuntosJuego.diferencia_tras_crafteo(inv, ConjuntosJuego.REQUISITOS_ANTORCHA)}")
    print(f"  I^c = {ConjuntosJuego.complemento_inventario(inv)}")

    # --- Tabla de verdad regla Z ---
    print("\n[Tabla de verdad - Regla de acceso a Zona Peligrosa]")
    tabla = LogicaProposicional.generar_tabla_verdad(
        LogicaProposicional.regla_acceso_zona, ["p (e>=50)", "q (antorcha)"])
    for fila in tabla:
        print(f"  p={fila[0]!s:5} q={fila[1]!s:5} -> Z={fila[2]}")

    # --- Matriz de simulación (5 casos) ---
    print("\n" + "=" * 70)
    print(" MATRIZ DE SIMULACIÓN - 5 CASOS DE PRUEBA")
    print("=" * 70)
    caso_1_huir_amenaza()
    caso_2_acceso_denegado()
    caso_3_crafteo_y_acceso()
    caso_4_combate()
    caso_5_derrota_inanicion()


if __name__ == "__main__":
    demo_completa()
