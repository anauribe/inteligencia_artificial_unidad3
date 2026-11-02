"""
graficos.py - Figuras del informe (matplotlib).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

from modelo import ACCESOS, U

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 9.5, "axes.titleweight": "bold",
})

# Paleta apta para daltonismo (Okabe-Ito)
COLOR = {"BFS": "#0072B2", "UCS": "#56B4E9", "Codiciosa": "#E69F00",
         "A*": "#009E73", "Plan fijo": "#7F7F7F"}
TINTA = "#263238"


def mil(x):
    """Número con separador de miles en español (punto)."""
    return f"{x:,.0f}".replace(",", ".")


# ---------------------------------------------------------------------------
def figura_representacion(problema, ruta):
    """Fig. 1: intersección abstracta + primeros niveles del árbol de búsqueda."""
    fig = plt.figure(figsize=(7.2, 3.3), dpi=220)
    ax1 = fig.add_axes([0.0, 0.0, 0.36, 1.0])
    ax2 = fig.add_axes([0.37, 0.0, 0.63, 1.0])

    # --- (a) intersección
    ax1.set_xlim(0, 10); ax1.set_ylim(0, 10); ax1.axis("off"); ax1.set_aspect("equal")
    ax1.add_patch(Rectangle((4, 0.6), 2, 8.8, fc="#ECEFF1", ec="none"))
    ax1.add_patch(Rectangle((0.2, 4), 9.6, 2, fc="#ECEFF1", ec="none"))
    q = problema.inicial.en_vehiculos()
    cap = problema.p.capacidad
    escala = 3.4 / cap
    # N (llega desde arriba), S (desde abajo), E (desde la derecha), O (desde la izq.)
    ax1.add_patch(Rectangle((4.15, 6.05), 0.8, q[0] * escala, fc="#D55E00", alpha=.85))
    ax1.add_patch(Rectangle((5.05, 3.95 - q[1] * escala), 0.8, q[1] * escala, fc="#D55E00", alpha=.85))
    ax1.add_patch(Rectangle((6.05, 5.05), q[2] * escala, 0.8, fc="#CC79A7", alpha=.85))
    ax1.add_patch(Rectangle((3.95 - q[3] * escala, 4.15), q[3] * escala, 0.8, fc="#CC79A7", alpha=.85))
    kw = dict(fontsize=7.5, ha="center", va="center", color=TINTA)
    ax1.text(3.3, 8.6, f"N\n{q[0]:.0f} veh", **kw)
    ax1.text(6.7, 1.4, f"S\n{q[1]:.0f} veh", **kw)
    ax1.text(8.9, 6.6, f"E\n{q[2]:.0f} veh", **kw)
    ax1.text(1.1, 3.4, f"O\n{q[3]:.0f} veh", **kw)
    ax1.text(5, 5, "control\n(agente)", fontsize=6.5, ha="center", va="center",
             color="white", bbox=dict(boxstyle="round,pad=0.3", fc=TINTA, ec="none"))
    ax1.text(5, 9.85, "(a) Intersección de dos fases", fontsize=8.5,
             fontweight="bold", ha="center", va="top", color=TINTA)
    ax1.text(5, 0.15, "fase NS: N y S  ·  fase EO: E y O", fontsize=6.8,
             ha="center", va="bottom", color=TINTA)

    # --- (b) árbol de búsqueda real (nivel 1 completo y una rama del nivel 2)
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis("off")
    ax2.text(5, 9.85, "(b) Espacio de búsqueda: primeros niveles (valores reales del escenario E1)",
             fontsize=8.5, fontweight="bold", ha="center", va="top", color=TINTA)

    def caja(x, y, txt, fc="#FFFFFF", ec=TINTA, w=1.25, h=1.15, fs=5.6, lw=0.7):
        ax2.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                      boxstyle="round,pad=0.04,rounding_size=0.12", fc=fc, ec=ec, lw=lw))
        ax2.text(x, y, txt, fontsize=fs, ha="center", va="center", color=TINTA, linespacing=1.15)

    s0 = problema.inicial
    caja(5, 8.0, f"s0 = (42, 30, 16, 12)\nfase NS · h = {mil(problema.h(s0))}", fc="#FFF3E0", w=2.6, h=1.0, fs=6.2)
    hijos = list(problema.sucesores(s0))
    xs = [0.75 + i * 1.42 for i in range(len(hijos))]
    elegido = ruta[0] if ruta else None
    for x, (a, s2, c) in zip(xs, hijos):
        v = s2.en_vehiculos()
        es_opt = elegido is not None and a == elegido
        ax2.annotate("", xy=(x, 5.95), xytext=(5, 7.48),
                     arrowprops=dict(arrowstyle="-|>", lw=1.1 if es_opt else 0.55,
                                     color="#009E73" if es_opt else "#90A4AE"))
        ax2.text((x + 5) / 2 + (0.15 if x > 5 else -0.15), 6.95, f"{a.verde}s", fontsize=5.6,
                 ha="center", color="#009E73" if es_opt else "#607D8B")
        caja(x, 5.35,
             f"({v[0]:.0f},{v[1]:.0f},{v[2]:.0f},{v[3]:.0f})\ng={mil(c)}\nh={mil(problema.h(s2))}",
             fc="#E8F5E9" if es_opt else "#FFFFFF", ec="#009E73" if es_opt else TINTA,
             lw=1.2 if es_opt else 0.7)
    # segundo nivel bajo la acción elegida
    if elegido is not None:
        i = [a for a, _, _ in hijos].index(elegido)
        s1 = hijos[i][1]
        nietos = list(problema.sucesores(s1))
        xs2 = [1.4 + j * 1.2 for j in range(len(nietos))]
        for x, (a, s2, c) in zip(xs2, nietos):
            ax2.annotate("", xy=(x, 2.75), xytext=(xs[i], 4.75),
                         arrowprops=dict(arrowstyle="-|>", lw=0.45, color="#B0BEC5"))
            v = s2.en_vehiculos()
            caja(x, 2.25, f"EO:{a.verde}s\n({v[0]:.0f},{v[1]:.0f},{v[2]:.0f},{v[3]:.0f})",
                 w=1.08, h=0.9, fs=5.0)
    ax2.text(5, 1.05, "Cada nodo: colas (N, S, E, O) en vehículos · g = demora acumulada (veh·s) · "
             "h = heurística.\nLas fases se alternan; el agente elige 1 de 7 verdes (10–40 s) en cada "
             "nivel → factor de ramificación b = 7.", fontsize=6.0, ha="center", va="center",
             color="#455A64")
    return fig


# ---------------------------------------------------------------------------
def figura_resultados(filas):
    """Fig. 2: (a) nodos expandidos, (b) demora total, por escenario."""
    algos = ["BFS", "UCS", "Codiciosa", "A*"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.7), dpi=220)
    n = len(filas)
    ancho = 0.18
    etiquetas = [f["escenario"]["nombre"].split(".")[0] for f in filas]

    for j, alg in enumerate(algos):
        vals = [f["resultados"][alg].expandidos for f in filas]
        xs = [i + (j - 1.5) * ancho for i in range(n)]
        a1.bar(xs, vals, ancho, color=COLOR[alg], label=alg)
        for x, v in zip(xs, vals):
            a1.text(x, v * 1.12, mil(v), ha="center", va="bottom",
                    fontsize=5.2, rotation=90, color=TINTA)
    a1.set_yscale("log"); a1.set_ylim(1, 4e5)
    a1.set_xticks(range(n)); a1.set_xticklabels(etiquetas)
    a1.set_ylabel("nodos expandidos (escala log)")
    a1.set_title("(a) Esfuerzo de búsqueda")

    series = algos + ["Plan fijo"]
    ancho2 = 0.15
    for j, alg in enumerate(series):
        if alg == "Plan fijo":
            vals = [f["plan_fijo"]["costo"] / 3600 for f in filas]
        else:
            vals = [f["resultados"][alg].costo / 3600 for f in filas]
        xs = [i + (j - 2) * ancho2 for i in range(n)]
        a2.bar(xs, vals, ancho2, color=COLOR[alg], label=alg)
    a2.set_xticks(range(n)); a2.set_xticklabels(etiquetas)
    a2.set_ylabel("demora total (veh·h)")
    a2.set_title("(b) Calidad de la solución (menor es mejor)")
    a2.legend(fontsize=6.5, frameon=False, ncol=1, loc="upper left")
    fig.tight_layout(w_pad=1.5)
    return fig


def _curva_cola(problema, acciones):
    """Cola total (veh) en cada instante de decisión del plan."""
    s, t = problema.inicial, 0
    ts, qs = [0], [sum(s.colas) / U]
    for a in acciones:
        s, _ = problema.transicion(s, a)
        t += a.verde + problema.p.perdido
        ts.append(t); qs.append(sum(s.colas) / U)
    return ts, qs


def figura_evolucion(fila):
    """Fig. 3: evolución de la cola total con cada plan (escenario E2)."""
    prob = fila["problema"]
    fig, ax = plt.subplots(figsize=(7.2, 2.2), dpi=220)
    planes = [("Plan fijo", fila["plan_fijo"]["acciones"]),
              ("BFS", fila["resultados"]["BFS"].acciones),
              ("Codiciosa", fila["resultados"]["Codiciosa"].acciones),
              ("A*", fila["resultados"]["A*"].acciones)]
    for nombre, acc in planes:
        ts, qs = _curva_cola(prob, acc)
        ax.plot(ts, qs, marker="o", ms=2.4, lw=1.6 if nombre == "A*" else 1.1,
                color=COLOR[nombre], label=f"{nombre} ({mil(ts[-1])} s)")
    ax.set_xlabel("tiempo (s)"); ax.set_ylabel("vehículos en cola (total)")
    ax.set_title(f"Evolución de la cola total — {fila['escenario']['nombre']}")
    ax.legend(fontsize=6.5, frameon=False, ncol=4, loc="upper right")
    fig.tight_layout()
    return fig


def guardar(fig, ruta):
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta
