"""
busqueda.py - Algoritmos de búsqueda no informada e informada.

Todos trabajan como BÚSQUEDA EN GRAFO (recuerdan los estados alcanzados para
no repetirlos) y devuelven un objeto Resultado con las métricas que se
comparan en el informe:

    costo            demora total del plan (veh·s)
    acciones         secuencia de acciones (plan)
    expandidos       nodos sacados de la frontera y expandidos  -> esfuerzo
    generados        nodos creados                              -> esfuerzo
    max_frontera     tamaño máximo de la frontera              -> memoria
    tiempo_ms        tiempo de CPU

Como protección, cada búsqueda se detiene si expande más de LIMITE nodos.

Algoritmos (Russell y Norvig, 2021, cap. 3):
    bfs          búsqueda en anchura  (no informada; óptima en N.º de acciones)
    ucs          costo uniforme       (no informada; óptima en costo)
    codiciosa    codiciosa del mejor primero, f = h (informada; no óptima)
    a_estrella   A*, f = g + h        (informada; óptima con h admisible)
"""

import heapq
import itertools
import time
from collections import deque
from dataclasses import dataclass, field

LIMITE = 300_000          # nodos expandidos como máximo por búsqueda


@dataclass(slots=True)
class Nodo:
    estado: object
    padre: "Nodo" = None
    accion: object = None
    g: float = 0.0                 # costo acumulado desde el inicio
    profundidad: int = 0

    def camino(self):
        nodo, acciones, estados = self, [], []
        while nodo is not None:
            estados.append(nodo.estado)
            if nodo.accion is not None:
                acciones.append(nodo.accion)
            nodo = nodo.padre
        return acciones[::-1], estados[::-1]


@dataclass
class Resultado:
    algoritmo: str
    exito: bool
    costo: float = float("inf")
    acciones: list = field(default_factory=list)
    estados: list = field(default_factory=list)
    expandidos: int = 0
    generados: int = 0
    max_frontera: int = 0
    tiempo_ms: float = 0.0
    limite_alcanzado: bool = False

    @property
    def n_acciones(self):
        return len(self.acciones)


def _hijos(problema, nodo):
    for a, s2, c in problema.sucesores(nodo.estado):
        yield Nodo(s2, nodo, a, nodo.g + c, nodo.profundidad + 1)


# ---------------------------------------------------------------------------
# Búsqueda no informada 1: búsqueda en anchura (BFS)
# ---------------------------------------------------------------------------
def bfs(problema) -> Resultado:
    t0 = time.perf_counter()
    raiz = Nodo(problema.inicial)
    res = Resultado("Búsqueda en anchura (BFS)", False)
    if problema.es_objetivo(raiz.estado):
        return _cerrar(res, raiz, t0)
    frontera = deque([raiz])
    alcanzados = {raiz.estado}
    while frontera:
        res.max_frontera = max(res.max_frontera, len(frontera))
        nodo = frontera.popleft()
        res.expandidos += 1
        if res.expandidos > LIMITE:
            res.limite_alcanzado = True
            break
        for hijo in _hijos(problema, nodo):
            res.generados += 1
            if problema.es_objetivo(hijo.estado):       # prueba temprana
                return _cerrar(res, hijo, t0)
            if hijo.estado not in alcanzados:
                alcanzados.add(hijo.estado)
                frontera.append(hijo)
    return _cerrar(res, None, t0)


# ---------------------------------------------------------------------------
# Búsqueda primero el mejor (base de UCS, codiciosa y A*)
# ---------------------------------------------------------------------------
def primero_el_mejor(problema, f, nombre, reabrir=True) -> Resultado:
    t0 = time.perf_counter()
    res = Resultado(nombre, False)
    raiz = Nodo(problema.inicial)
    desempate = itertools.count()          # FIFO entre nodos con igual f
    frontera = [(f(raiz), next(desempate), raiz)]
    alcanzados = {raiz.estado: raiz}
    while frontera:
        res.max_frontera = max(res.max_frontera, len(frontera))
        _, _, nodo = heapq.heappop(frontera)
        if alcanzados.get(nodo.estado) is not nodo:   # entrada obsoleta
            continue
        if problema.es_objetivo(nodo.estado):         # prueba al expandir
            return _cerrar(res, nodo, t0)
        res.expandidos += 1
        if res.expandidos > LIMITE:
            res.limite_alcanzado = True
            break
        for hijo in _hijos(problema, nodo):
            res.generados += 1
            previo = alcanzados.get(hijo.estado)
            if previo is None or (reabrir and hijo.g < previo.g - 1e-9):
                alcanzados[hijo.estado] = hijo
                heapq.heappush(frontera, (f(hijo), next(desempate), hijo))
    return _cerrar(res, None, t0)


def ucs(problema) -> Resultado:
    return primero_el_mejor(problema, lambda n: n.g, "Búsqueda de costo uniforme (UCS)")


def codiciosa(problema) -> Resultado:
    return primero_el_mejor(problema, lambda n: problema.h(n.estado),
                            "Búsqueda codiciosa del mejor primero", reabrir=False)


def a_estrella(problema) -> Resultado:
    return primero_el_mejor(problema, lambda n: n.g + problema.h(n.estado), "A*")


def _cerrar(res, nodo, t0):
    res.tiempo_ms = (time.perf_counter() - t0) * 1000
    if nodo is not None:
        res.exito = True
        res.costo = nodo.g
        res.acciones, res.estados = nodo.camino()
    return res


ALGORITMOS = {
    "BFS": bfs,
    "UCS": ucs,
    "Codiciosa": codiciosa,
    "A*": a_estrella,
}
