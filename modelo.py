"""
modelo.py - Formulación del problema de búsqueda del agente SemaforIA-BOG.

El agente controla una intersección semaforizada de dos fases de un corredor
arterial de Bogotá:
    fase NS: verde para los accesos Norte y Sur
    fase EO: verde para los accesos Este y Oeste
y debe encontrar la secuencia de duraciones de verde que despeja las colas
acumuladas con la MENOR DEMORA TOTAL posible.

Modelo de colas: fluido determinista (valores esperados), el mismo supuesto
del método clásico de Webster (1958): mientras un acceso tiene verde su cola
baja a la tasa (s - lambda); en rojo o en tiempo perdido sube a la tasa lambda.

Para evitar errores de redondeo, las colas se guardan como ENTEROS en
centésimas de vehículo (1 veh = 100 unidades). Así dos estados iguales se
reconocen siempre como iguales y la búsqueda en grafo es exacta.
"""

from dataclasses import dataclass, field
from typing import Iterator, NamedTuple, Optional, Sequence

ACCESOS = ("N", "S", "E", "O")
FASES = {"NS": (0, 1), "EO": (2, 3)}           # índices de los accesos servidos
SIGUIENTE = {"NS": "EO", "EO": "NS"}            # el controlador alterna fases
U = 100                                          # 1 vehículo = 100 centésimas


# ----------------------------------------------------------------------------
# Parámetros del entorno (lo que el agente percibe con sus sensores)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Parametros:
    """Datos percibidos/estimados del entorno.

    llegadas  : tasa de llegada por acceso, en veh/s (cámaras + espiras)
    saturacion: tasa de descarga de un acceso con verde, en veh/s
                (0.80 en seco; 0.64 con lluvia, pluviómetro)
    verdes    : duraciones de verde permitidas, en s (verde mínimo peatonal 10 s)
    perdido   : ámbar + todo rojo al final de cada fase, en s
    capacidad : cola máxima por acceso antes de bloquear la intersección
                anterior (desborde), en vehículos
    meta      : cola residual máxima para considerar la intersección despejada
    """
    llegadas: Sequence[float] = (0.30, 0.20, 0.12, 0.10)
    saturacion: float = 0.80
    verdes: Sequence[int] = (10, 15, 20, 25, 30, 35, 40)
    perdido: int = 5
    capacidad: float = 60
    meta: float = 8

    # versiones enteras (centésimas de vehículo) para cálculos exactos
    @property
    def lam(self):
        return tuple(round(x * U) for x in self.llegadas)

    @property
    def sat(self):
        return round(self.saturacion * U)

    @property
    def cap(self):
        return round(self.capacidad * U)

    @property
    def q_meta(self):
        return round(self.meta * U)

    def grado_saturacion(self) -> float:
        """Suma de razones de flujo críticas (Webster). Debe ser < 1."""
        l = self.llegadas
        return max(l[0], l[1]) / self.saturacion + max(l[2], l[3]) / self.saturacion


# ----------------------------------------------------------------------------
# Estado y acción
# ----------------------------------------------------------------------------
class Estado(NamedTuple):
    colas: tuple          # (N, S, E, O) en centésimas de vehículo
    fase: str             # fase que recibirá el próximo verde

    def en_vehiculos(self):
        return tuple(c / U for c in self.colas)

    def __str__(self):
        c = ", ".join(f"{a}={v:.1f}" for a, v in zip(ACCESOS, self.en_vehiculos()))
        return f"[{c} | próxima fase {self.fase}]"


class Accion(NamedTuple):
    fase: str
    verde: int            # segundos de verde

    def __str__(self):
        return f"{self.fase}:{self.verde}s"


# ----------------------------------------------------------------------------
# Problema de búsqueda (estado inicial, acciones, transición, objetivo, costo)
# ----------------------------------------------------------------------------
class ProblemaSemaforo:
    def __init__(self, colas_iniciales_veh, params: Parametros = Parametros(),
                 fase_inicial: str = "NS"):
        self.p = params
        colas = tuple(round(c * U) for c in colas_iniciales_veh)
        self.inicial = Estado(colas, fase_inicial)
        self._lam = params.lam
        self._sat = params.sat
        # tasa máxima a la que puede bajar cada cola (s - lambda), para h(n)
        self._r = tuple(self._sat - l for l in self._lam)
        if min(self._r) <= 0:
            raise ValueError("Algún acceso recibe más vehículos de los que puede descargar")

    # --- ACCIONES(s): el agente elige cuánto verde dar a la fase que sigue
    def acciones(self, s: Estado) -> Iterator[Accion]:
        for g in self.p.verdes:
            yield Accion(s.fase, g)

    # --- RESULTADO(s, a) y COSTO(s, a, s'): simulación exacta del modelo fluido
    def transicion(self, s: Estado, a: Accion):
        """Devuelve (estado_siguiente, costo) o (None, None) si hay desborde.

        Costo = demora total en vehículo-segundo = área bajo la curva de cola
        de los 4 accesos durante la acción (verde + tiempo perdido).
        """
        servidos = FASES[a.fase]
        g, L = a.verde, self.p.perdido
        nuevas, area = [], 0.0
        for i, q in enumerate(s.colas):
            lam = self._lam[i]
            if i in servidos:                       # acceso con verde
                r = self._sat - lam
                t0 = q / r                           # instante en que la cola se vacía
                if t0 >= g:
                    area += (q + (q - r * g)) * g / 2
                    q = q - r * g
                else:                                # se vacía y queda en 0
                    area += q * t0 / 2
                    q = 0
            else:                                    # acceso en rojo
                area += q * g + lam * g * g / 2
                q = q + lam * g
            # tiempo perdido (ámbar + todo rojo): todos los accesos acumulan
            area += q * L + lam * L * L / 2
            q = q + lam * L
            if q > self.p.cap:
                return None, None                    # desborde: acción inválida
            nuevas.append(int(q))
        return Estado(tuple(nuevas), SIGUIENTE[a.fase]), area / U   # veh·s

    def sucesores(self, s: Estado):
        for a in self.acciones(s):
            s2, c = self.transicion(s, a)
            if s2 is not None:
                yield a, s2, c

    # --- PRUEBA DE OBJETIVO
    def es_objetivo(self, s: Estado) -> bool:
        return all(q <= self.p.q_meta for q in s.colas)

    # --- HEURÍSTICA ADMISIBLE h(n)
    def h(self, s: Estado) -> float:
        """Cota inferior de la demora que falta (veh·s).

        Ninguna cola puede bajar más rápido que r = s - lambda y la búsqueda no
        termina hasta que cada cola q llegue a la meta m. Por eso el área bajo
        su curva es, como mínimo, la del triángulo/trapecio que baja de q a m a
        tasa r:  (q^2 - m^2) / (2 r).  Sumar los 4 accesos sigue siendo una
        cota inferior (cada acceso aporta su propia área al costo), luego h es
        ADMISIBLE; además es consistente porque cada acción real tarda al menos
        lo que tarda la recta ideal.
        """
        m = self.p.q_meta
        total = 0.0
        for q, r in zip(s.colas, self._r):
            if q > m:
                total += (q * q - m * m) / (2 * r)
        return total / U


# ----------------------------------------------------------------------------
# Agente (ciclo percibir -> formular -> buscar -> actuar)
# ----------------------------------------------------------------------------
@dataclass
class AgenteSemaforIA:
    """Agente basado en objetivos/utilidad que planifica con búsqueda."""
    algoritmo: callable
    plan: list = field(default_factory=list)
    ultimo_resultado: Optional[object] = None

    def percibir(self, sensores: dict):
        """Convierte las lecturas de sensores en un problema de búsqueda."""
        lluvia = sensores.get("lluvia_mm_h", 0) > 2
        params = Parametros(llegadas=tuple(sensores["llegadas_veh_s"]),
                            saturacion=0.64 if lluvia else 0.80)
        return ProblemaSemaforo(sensores["colas_veh"], params)

    def decidir(self, sensores: dict):
        problema = self.percibir(sensores)
        self.ultimo_resultado = self.algoritmo(problema)
        self.plan = list(self.ultimo_resultado.acciones)
        return self.plan

    def actuar(self):
        """Envía al controlador semafórico la siguiente acción del plan."""
        return self.plan.pop(0) if self.plan else None
