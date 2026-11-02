"""
experimentos.py - Ejecución de los algoritmos y registro de resultados.

1. Tres escenarios representativos del corredor (seco, lluvia, evento).
2. Línea base: plan de tiempos fijos actual (NS 30 s / EO 20 s).
3. 100 instancias aleatorias (semilla fija) para comparar con estadística.
4. Verificación empírica de que la heurística es admisible y consistente.
"""

import random
import statistics as st

from busqueda import ALGORITMOS, ucs
from modelo import Accion, Parametros, ProblemaSemaforo

ESCENARIOS = [
    {
        "nombre": "E1. Hora pico, vía seca",
        "colas": (42, 30, 16, 12),
        "params": Parametros(),
    },
    {
        "nombre": "E2. Hora pico con lluvia",
        "colas": (42, 30, 16, 12),
        "params": Parametros(saturacion=0.64),
    },
    {
        "nombre": "E3. Salida de evento masivo",
        "colas": (20, 15, 45, 38),
        "params": Parametros(llegadas=(0.22, 0.18, 0.20, 0.16)),
    },
]

PLAN_FIJO = {"NS": 30, "EO": 20}


# ---------------------------------------------------------------------------
def plan_fijo(problema, max_ciclos=60):
    """Simula el plan de tiempos fijos hasta despejar (o desbordar)."""
    s, costo, acciones, estados = problema.inicial, 0.0, [], [problema.inicial]
    for _ in range(2 * max_ciclos):
        if problema.es_objetivo(s):
            return {"exito": True, "costo": costo, "acciones": acciones, "estados": estados}
        a = Accion(s.fase, PLAN_FIJO[s.fase])
        s2, c = problema.transicion(s, a)
        if s2 is None:
            return {"exito": False, "costo": float("inf"), "acciones": acciones,
                    "estados": estados, "motivo": "desborde"}
        s, costo = s2, costo + c
        acciones.append(a)
        estados.append(s)
    return {"exito": False, "costo": float("inf"), "acciones": acciones,
            "estados": estados, "motivo": "no despeja"}


def factor_ramificacion_efectivo(expandidos, d, tol=1e-6):
    """b* tal que N + 1 = 1 + b* + b*^2 + ... + b*^d (Russell y Norvig)."""
    if d == 0 or expandidos <= 0:
        return float("nan")
    n = expandidos

    def total(b):
        return sum(b ** i for i in range(1, d + 1))

    lo, hi = 1.0, max(2.0, float(n))
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if total(mid) < n:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------------------
def correr_escenarios():
    filas = []
    for esc in ESCENARIOS:
        prob = ProblemaSemaforo(esc["colas"], esc["params"])
        resultados = {k: f(prob) for k, f in ALGORITMOS.items()}
        optimo = resultados["UCS"].costo
        assert abs(resultados["A*"].costo - optimo) < 1e-6, "A* debe ser óptimo"
        base = plan_fijo(prob)
        filas.append({"escenario": esc, "problema": prob,
                      "resultados": resultados, "plan_fijo": base, "optimo": optimo})
    return filas


def instancia_aleatoria(rng):
    """Instancia del mismo corredor con demanda y colas al azar.

    Se descartan demandas casi saturadas (grado de saturación > 0.75), porque
    en ellas ningún plan despeja la intersección en un tiempo razonable.
    """
    while True:
        lleg = (rng.randint(20, 32) / 100, rng.randint(10, 22) / 100,
                rng.randint(6, 16) / 100, rng.randint(5, 14) / 100)
        sat = rng.choice((0.80, 0.64))
        params = Parametros(llegadas=lleg, saturacion=sat)
        if params.grado_saturacion() > 0.75:
            continue
        colas = (rng.randint(15, 45), rng.randint(10, 35),
                 rng.randint(5, 30), rng.randint(5, 25))
        prob = ProblemaSemaforo(colas, params)
        if not prob.es_objetivo(prob.inicial):
            return prob


def correr_aleatorios(n=100, semilla=2026):
    rng = random.Random(semilla)
    registros = {k: [] for k in ALGORITMOS}
    descartadas = 0
    while len(registros["A*"]) < n:
        prob = instancia_aleatoria(rng)
        res = {k: f(prob) for k, f in ALGORITMOS.items()}
        if any(r.limite_alcanzado or not r.exito for r in res.values()):
            descartadas += 1                 # alguna búsqueda superó el límite
            continue
        optimo = res["UCS"].costo
        assert abs(res["A*"].costo - optimo) < 1e-6
        for k, r in res.items():
            registros[k].append({
                "costo": r.costo, "brecha": 100 * (r.costo - optimo) / optimo,
                "expandidos": r.expandidos, "generados": r.generados,
                "frontera": r.max_frontera, "tiempo": r.tiempo_ms,
                "acciones": r.n_acciones,
                "b": factor_ramificacion_efectivo(r.expandidos, r.n_acciones),
            })
    resumen = {}
    for k, lista in registros.items():
        resumen[k] = {
            "optimos": sum(1 for x in lista if x["brecha"] < 1e-6),
            "brecha_media": st.mean(x["brecha"] for x in lista),
            "brecha_max": max(x["brecha"] for x in lista),
            "exp_mediana": st.median(x["expandidos"] for x in lista),
            "exp_media": st.mean(x["expandidos"] for x in lista),
            "frontera_mediana": st.median(x["frontera"] for x in lista),
            "tiempo_mediana": st.median(x["tiempo"] for x in lista),
            "tiempo_max": max(x["tiempo"] for x in lista),
            "b_mediana": st.median(x["b"] for x in lista),
            "acciones_media": st.mean(x["acciones"] for x in lista),
        }
    return n, registros, resumen, descartadas


# ---------------------------------------------------------------------------
def verificar_heuristica(n_estados=150, semilla=7):
    """Comprueba h(s) <= h*(s) (admisible) y h(s) <= c + h(s') (consistente)."""
    rng = random.Random(semilla)
    peor_ratio, violaciones_adm, violaciones_cons, aristas = 0.0, 0, 0, 0
    for _ in range(n_estados):
        prob = instancia_aleatoria(rng)
        res = ucs(prob)
        if not res.exito:
            continue
        h0, h_real = prob.h(prob.inicial), res.costo
        if h0 > h_real + 1e-6:
            violaciones_adm += 1
        peor_ratio = max(peor_ratio, h0 / h_real if h_real else 0)
        for s in res.estados:                      # estados del camino óptimo
            for a, s2, c in prob.sucesores(s):     # y todas sus aristas
                aristas += 1
                if prob.h(s) > c + prob.h(s2) + 1e-6:
                    violaciones_cons += 1
    return {"estados": n_estados, "aristas": aristas,
            "violaciones_admisible": violaciones_adm,
            "violaciones_consistente": violaciones_cons,
            "max_h_sobre_hreal": peor_ratio}
