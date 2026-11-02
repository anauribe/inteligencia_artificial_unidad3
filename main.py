"""
main.py - Ejecuta todo el estudio y genera el informe PDF.

Uso:
    python main.py            (100 instancias aleatorias, ~3 minutos)
    python main.py --rapido   (20 instancias, para probar)

Salidas en la carpeta resultados/:
    escenarios.csv, aleatorios.csv, resumen.json, figuras PNG e informe PDF.
"""

import csv
import inspect
import io
import json
import os
import statistics as st
import sys
from contextlib import redirect_stdout

import experimentos as ex
import graficos as gr
import informe
from busqueda import a_estrella
from modelo import AgenteSemaforIA, ProblemaSemaforo

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")


def demo_agente():
    """Muestra el ciclo percibir -> decidir -> actuar del agente."""
    sensores = {                       # lecturas simuladas de los sensores
        "colas_veh": (42, 30, 16, 12),             # cámaras con visión por computador
        "llegadas_veh_s": (0.30, 0.20, 0.12, 0.10),  # espiras inductivas
        "lluvia_mm_h": 8.5,                        # pluviómetro
    }
    agente = AgenteSemaforIA(algoritmo=a_estrella)
    print(">> PERCIBIR   ", {k: v for k, v in sensores.items()})
    prob = agente.percibir(sensores)
    print(f"   lluvia > 2 mm/h -> tasa de descarga {prob.p.saturacion} veh/s")
    print(f"   estado inicial {prob.inicial}")
    plan = agente.decidir(sensores)
    r = agente.ultimo_resultado
    print(f">> DECIDIR    A* encontró un plan de {len(plan)} acciones, demora "
          f"{r.costo / 3600:.2f} veh·h, {r.expandidos} nodos expandidos")
    print(">> ACTUAR     órdenes enviadas al controlador semafórico:")
    s = prob.inicial
    paso = 1
    while (a := agente.actuar()) is not None:
        s, _ = prob.transicion(s, a)
        print(f"   {paso:>2}. verde {a.fase} {a.verde:>2} s  ->  {s}")
        paso += 1
    print(f"   objetivo alcanzado: {prob.es_objetivo(s)}")


def guardar_csv(filas, registros):
    with open(os.path.join(SALIDA, "escenarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["escenario", "metodo", "demora_veh_s", "acciones", "expandidos",
                    "generados", "frontera_max", "tiempo_ms", "plan"])
        for fila in filas:
            for k, r in fila["resultados"].items():
                w.writerow([fila["escenario"]["nombre"], k, round(r.costo, 1), r.n_acciones,
                            r.expandidos, r.generados, r.max_frontera, round(r.tiempo_ms, 2),
                            " ".join(map(str, r.acciones))])
            pf = fila["plan_fijo"]
            w.writerow([fila["escenario"]["nombre"], "Plan fijo", round(pf["costo"], 1),
                        len(pf["acciones"]), "", "", "", "", " ".join(map(str, pf["acciones"]))])
    with open(os.path.join(SALIDA, "aleatorios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["instancia", "metodo", "demora_veh_s", "brecha_pct", "expandidos",
                    "generados", "frontera_max", "tiempo_ms", "acciones", "b_efectivo"])
        for k, lista in registros.items():
            for i, x in enumerate(lista, 1):
                w.writerow([i, k, round(x["costo"], 1), round(x["brecha"], 3), x["expandidos"],
                            x["generados"], x["frontera"], round(x["tiempo"], 2), x["acciones"],
                            round(x["b"], 3)])


def main():
    n = 20 if "--rapido" in sys.argv else 100
    os.makedirs(SALIDA, exist_ok=True)

    print("1/5 Escenarios E1-E3 y plan fijo...")
    filas = ex.correr_escenarios()
    for f in filas:
        print(f"    {f['escenario']['nombre']}: óptimo {f['optimo'] / 3600:.2f} veh·h")

    print(f"2/5 {n} instancias aleatorias (puede tardar unos minutos)...")
    aleatorios = ex.correr_aleatorios(n=n)
    _, registros, resumen, _ = aleatorios

    print("3/5 Verificación de la heurística...")
    ver = ex.verificar_heuristica(n_estados=100)
    print(f"    {ver}")
    # fracción h(s0) / costo óptimo en las instancias aleatorias
    import random
    rng = random.Random(2026)
    fr = []
    for _ in range(30):
        p = ex.instancia_aleatoria(rng)
        r = a_estrella(p)
        if r.exito:
            fr.append(p.h(p.inicial) / r.costo)
    h_fraccion = st.mean(fr)

    print("4/5 Figuras y registro de resultados...")
    figs = {
        "representacion": gr.guardar(gr.figura_representacion(
            filas[0]["problema"], filas[0]["resultados"]["A*"].acciones),
            os.path.join(SALIDA, "fig1_representacion.png")),
        "resultados": gr.guardar(gr.figura_resultados(filas),
                                 os.path.join(SALIDA, "fig2_resultados.png")),
        "evolucion": gr.guardar(gr.figura_evolucion(filas[1]),
                                os.path.join(SALIDA, "fig3_evolucion.png")),
    }
    guardar_csv(filas, registros)
    with open(os.path.join(SALIDA, "resumen.json"), "w", encoding="utf-8") as f:
        json.dump({"aleatorios": resumen, "verificacion_heuristica": ver,
                   "h_s0_sobre_optimo": h_fraccion}, f, ensure_ascii=False, indent=2)

    buf = io.StringIO()
    with redirect_stdout(buf):
        demo_agente()
    agente_log = buf.getvalue()
    print(agente_log)

    codigo = (inspect.getsource(ProblemaSemaforo.transicion) + "\n" +
              inspect.getsource(ProblemaSemaforo.h))

    print("5/5 Informe PDF...")
    ruta = informe.construir(os.path.join(SALIDA, "Informe_U3_Busqueda_SemaforIA.pdf"), {
        "escenarios": filas, "aleatorios": aleatorios, "verificacion": ver,
        "figuras": figs, "agente_log": agente_log, "codigo_clave": codigo,
        "h_fraccion": h_fraccion,
    })
    print(f"Listo: {ruta}")


if __name__ == "__main__":
    main()
