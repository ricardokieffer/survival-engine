"""
================================================================================
 SURVIVAL ENGINE - Consola interactiva
 Proyecto ABP - Elementos de Matemática y Lógica (ISPC)

 Versión jugable por teclado, sin dependencias externas ni conexión a internet.
 Reutiliza el mismo modelo matemático-lógico documentado en el proyecto:
   variables y dominios, funciones explícitas, progresiones, teoría de
   conjuntos y lógica proposicional (reglas Z, A, D).

 Ejecutar con:   python3 survival_engine_console.py
================================================================================
"""

import os
import sys


# ==============================================================================
# FUNCIONES MATEMÁTICAS EXPLÍCITAS (idénticas al documento)
# ==============================================================================

def clamp(valor, minimo, maximo):
    return min(maximo, max(minimo, valor))


def energia_correr(t_min):
    """E_correr(t) = 5 * t"""
    return 5 * t_min


def xp_requerida(n):
    """Progresión aritmética: a_n = 100 + (n-1)*50"""
    return 100 + (n - 1) * 50


def dano_enemigo(k):
    """Progresión geométrica: D_k = 10 * 2^(k-1)"""
    return 10 * (2 ** (k - 1))


# ==============================================================================
# LÓGICA PROPOSICIONAL
# ==============================================================================

def regla_acceso_zona(p, q):
    """Z: p ∧ q → Z"""
    return p and q


def regla_alerta(r, s):
    """A: r ∧ ¬s → A"""
    return r and (not s)


def regla_derrota(u, w, s):
    """D: u ∨ (w ∧ ¬s) → D"""
    return u or (w and (not s))


# ==============================================================================
# ESTADO DEL JUGADOR
# ==============================================================================

class Estado:
    def __init__(self):
        self.v = 100.0      # vida
        self.e = 100.0      # energía
        self.n = 1          # nivel
        self.xp = 0
        self.t = 0.0        # tiempo (min)
        self.m = 0          # madera
        self.p = 0          # piedra
        self.c = 0          # comida
        self.inventario = {}   # ítems craftados: {"antorcha": 1, ...}
        self.derrotado = False
        self.log = []

    def registrar(self, msg):
        self.log.append(f"[t={self.t:.0f}min] {msg}")
        if len(self.log) > 6:
            self.log.pop(0)

    def tiene(self, item):
        if item in ("comida",):
            return self.c > 0
        return self.inventario.get(item, 0) > 0

    def evaluar_alerta(self):
        r = self.e < 20
        s = self.tiene("comida")
        return regla_alerta(r, s)

    def evaluar_derrota(self):
        u = self.v <= 0
        w = self.e <= 0
        s = self.tiene("comida")
        if regla_derrota(u, w, s) and not self.derrotado:
            self.derrotado = True
            razon = "vida = 0" if u else "energía = 0 y sin comida"
            self.registrar(f"REGLA D: u∨(w∧¬s)→D — {razon} ⇒ DERROTA")
        return self.derrotado


ESTADO = Estado()


# ==============================================================================
# UTILIDADES DE PANTALLA
# ==============================================================================

def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def barra(valor, ancho=20):
    llenas = int(round((valor / 100) * ancho))
    return "█" * llenas + "░" * (ancho - llenas)


def mostrar_estado():
    s = ESTADO
    print("=" * 62)
    print(" SURVIVAL ENGINE — consola interactiva".center(62))
    print("=" * 62)
    print(f" Nivel: {s.n}   XP: {s.xp}/{xp_requerida(s.n)}   Tiempo: {s.t:.0f} min")
    print(f" Vida    [{barra(s.v)}] {s.v:5.1f}/100")
    print(f" Energía [{barra(s.e)}] {s.e:5.1f}/100")
    print(f" Recursos -> Madera: {s.m}  Piedra: {s.p}  Comida: {s.c}")
    items = ", ".join(f"{k} x{v}" for k, v in s.inventario.items() if v > 0)
    print(f" Inventario craftado -> {items if items else '(vacío)'}")
    if s.evaluar_alerta():
        print(" ⚠  ALERTA DE CANSANCIO EXTREMO (r ∧ ¬s → A = V)")
    print("-" * 62)
    if s.log:
        print(" Registro del analista funcional:")
        for linea in s.log:
            print("  " + linea)
    print("-" * 62)


def pausa():
    input("\n(Enter para continuar) ")


# ==============================================================================
# ACCIONES
# ==============================================================================

def accion_recolectar():
    print("\n¿Qué querés recolectar?")
    print(" 1) Madera (+3)   2) Piedra (+3)   3) Comida (+1)")
    op = input("> ").strip()
    s = ESTADO
    if op == "1":
        s.m = clamp(s.m + 3, 0, 99); s.registrar("Recolectaste +3 madera.")
    elif op == "2":
        s.p = clamp(s.p + 3, 0, 99); s.registrar("Recolectaste +3 piedra.")
    elif op == "3":
        s.c = clamp(s.c + 1, 0, 99); s.registrar("Recolectaste +1 comida.")
    else:
        print("Opción inválida.")


def accion_correr():
    s = ESTADO
    gasto = energia_correr(5)
    s.e = clamp(s.e - gasto, 0, 100)
    s.t += 5
    s.registrar(f"Corriste 5 min → E_correr(5)=5·5={gasto} energía consumida.")
    s.evaluar_derrota()


def accion_descansar():
    s = ESTADO
    s.e = clamp(s.e + 15, 0, 100)
    s.t += 2
    s.registrar("Descansaste 2 min → energía +15.")


def accion_comer():
    s = ESTADO
    if s.c <= 0:
        s.registrar("Intentaste comer pero no tenés comida (s=F).")
        return
    s.c -= 1
    s.e = clamp(s.e + 25, 0, 100)
    s.registrar("Comiste 1 unidad de comida → energía +25.")


def accion_craftear():
    s = ESTADO
    if s.m >= 2 and s.p >= 1:
        s.m -= 2
        s.p -= 1
        s.inventario["antorcha"] = s.inventario.get("antorcha", 0) + 1
        s.registrar("C_antorcha(m,p)=2m+1p satisfecha → crafteaste 1 antorcha.")
    else:
        s.registrar(f"Crafteo rechazado: se requieren 2 madera+1 piedra (tenés {s.m}m,{s.p}p).")


def accion_acceso_zona():
    s = ESTADO
    p = s.e >= 50
    q = s.tiene("antorcha")
    z = regla_acceso_zona(p, q)
    resultado = "V (Acceso concedido)" if z else "F (Acceso denegado)"
    s.registrar(f"Regla Z: p∧q→Z — p(e≥50)={'V' if p else 'F'}, q(antorcha∈I)={'V' if q else 'F'} ⇒ Z={resultado}")


def accion_combatir():
    s = ESTADO
    try:
        k = int(input("Nivel del enemigo (1-10): ").strip())
        k = max(1, min(10, k))
    except ValueError:
        print("Valor inválido, se usa k=3 por defecto.")
        k = 3
    dano = dano_enemigo(k)
    s.v = clamp(s.v - dano, 0, 100)
    s.t += 3
    s.registrar(f"Combate k={k} → D_k=10·2^({k}-1)={dano} de daño recibido.")

    if s.evaluar_derrota():
        return

    xp_ganada = 30 * k
    s.xp += xp_ganada
    s.registrar(f"Enemigo derrotado → +{xp_ganada} XP.")
    subio = False
    while s.xp >= xp_requerida(s.n):
        s.xp -= xp_requerida(s.n)
        s.n += 1
        subio = True
    if subio:
        s.registrar(f"¡Subiste a nivel {s.n}! Próximo requerimiento: {xp_requerida(s.n)} XP.")


# ==============================================================================
# BUCLE PRINCIPAL
# ==============================================================================

MENU = """
 ACCIONES DISPONIBLES
  1) Recolectar recursos
  2) Correr 5 min (consume energía)
  3) Descansar (+15 energía)
  4) Comer
  5) Craftear antorcha
  6) Intentar acceder a la zona peligrosa
  7) Enfrentar enemigo
  8) Reiniciar simulación
  0) Salir
"""


def game_over():
    print("\n" + "#" * 62)
    print(" DERROTA — el simulador bloqueó las acciones del jugador.".center(62))
    print("#" * 62)
    print("\n¿Reiniciar? (s/n)")
    return input("> ").strip().lower() == "s"


def main():
    global ESTADO
    limpiar()
    print("Motor iniciado. Dominios: v,e∈[0,100]⊂R · m,p,c∈[0,99]∩N0 · n∈[1,50]∩N.\n")
    pausa()

    while True:
        limpiar()
        mostrar_estado()

        if ESTADO.derrotado:
            if game_over():
                ESTADO = Estado()
                continue
            else:
                print("Gracias por jugar la demo del Survival Engine.")
                sys.exit(0)

        print(MENU)
        op = input("Elegí una acción > ").strip()

        if op == "1":
            accion_recolectar()
        elif op == "2":
            accion_correr()
        elif op == "3":
            accion_descansar()
        elif op == "4":
            accion_comer()
        elif op == "5":
            accion_craftear()
        elif op == "6":
            accion_acceso_zona()
        elif op == "7":
            accion_combatir()
        elif op == "8":
            ESTADO = Estado()
        elif op == "0":
            print("Gracias por jugar la demo del Survival Engine.")
            sys.exit(0)
        else:
            print("Opción inválida.")
            pausa()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulación interrumpida. ¡Hasta la próxima!")
