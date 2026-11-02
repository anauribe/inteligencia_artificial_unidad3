"""
informe.py - Genera el informe PDF en formato APA 7 (trabajo de estudiante).

Formato aplicado (APA 7.ª ed., adaptado a las condiciones del curso):
  - Portada de estudiante en página aparte.
  - Arial 11, interlineado 1,5 (condición del curso), márgenes de 2,54 cm.
  - Número de página arriba a la derecha en todas las páginas.
  - Título repetido en la primera página del texto; encabezados APA
    (nivel 1 centrado en negrita, nivel 2 alineado a la izquierda en negrita).
  - Párrafos alineados a la izquierda con sangría de 1,27 cm en la primera línea.
  - Tablas y figuras: número en negrita, título en cursiva, nota debajo;
    tablas solo con líneas horizontales.
  - Referencias en página nueva con sangría francesa; anexos en páginas aparte.
  - Todo el texto en negro (las figuras conservan sus colores).

Todos los números del texto, tablas y figuras salen de la ejecución real de
los algoritmos, por lo que si se cambian parámetros el informe se actualiza solo.
"""

import os
import statistics as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak,
                                Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

# ---------------------------------------------------------------------------
# >>> datos personales
# ---------------------------------------------------------------------------
NOMBRE = "Ana Milena Uribe"
INSTITUCION = "Politecnico Gran Colombiano"
CURSO = "Inteligencia Artificial"
TUTOR = "Carlos Cañon Romero"
FECHA = "02 de Noviembre de 2026"

# ---------------------------------------------------------------------------
# Tipografía: Arial si existe (Windows/macOS) o Helvetica (incluida en ReportLab).
# ---------------------------------------------------------------------------
_CANDIDATAS = [
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf",
     "C:/Windows/Fonts/ariali.ttf", "C:/Windows/Fonts/arialbi.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf",
     "/Library/Fonts/Arial Italic.ttf", "/Library/Fonts/Arial Bold Italic.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf",
     "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
     "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
     "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"),
]


def _registrar_fuente():
    from reportlab.lib.fonts import addMapping
    for r, b, i, bi in _CANDIDATAS:
        if all(os.path.exists(p) for p in (r, b, i, bi)):
            for nombre, ruta in (("F", r), ("F-B", b), ("F-I", i), ("F-BI", bi)):
                pdfmetrics.registerFont(TTFont(nombre, ruta))
            addMapping("F", 0, 0, "F"); addMapping("F", 1, 0, "F-B")
            addMapping("F", 0, 1, "F-I"); addMapping("F", 1, 1, "F-BI")
            return "F", "F-B"
    return "Helvetica", "Helvetica-Bold"


FUENTE, NEGRITA = _registrar_fuente()
NEGRO = colors.black
TAM = 11                    # Arial 11
INTER = TAM * 1.5           # interlineado 1,5
SANGRIA = 1.27 * cm         # sangría APA de primera línea
MARGEN = 2.54 * cm          # márgenes APA de 1 pulgada
ANCHO_TEXTO = letter[0] - 2 * MARGEN

E = {
    "cuerpo": ParagraphStyle("cuerpo", fontName=FUENTE, fontSize=TAM, leading=INTER,
                             alignment=TA_LEFT, firstLineIndent=SANGRIA, textColor=NEGRO),
    "sin_sangria": ParagraphStyle("sin_sangria", fontName=FUENTE, fontSize=TAM, leading=INTER,
                                  alignment=TA_LEFT, textColor=NEGRO),
    "centrado": ParagraphStyle("centrado", fontName=FUENTE, fontSize=TAM, leading=INTER,
                               alignment=TA_CENTER, textColor=NEGRO),
    "titulo": ParagraphStyle("titulo", fontName=NEGRITA, fontSize=TAM, leading=INTER,
                             alignment=TA_CENTER, textColor=NEGRO),
    "h1": ParagraphStyle("h1", fontName=NEGRITA, fontSize=TAM, leading=INTER,
                         alignment=TA_CENTER, spaceBefore=6, keepWithNext=True, textColor=NEGRO),
    "h2": ParagraphStyle("h2", fontName=NEGRITA, fontSize=TAM, leading=INTER,
                         alignment=TA_LEFT, spaceBefore=2, keepWithNext=True, textColor=NEGRO),
    "tabla": ParagraphStyle("tabla", fontName=FUENTE, fontSize=9, leading=11, textColor=NEGRO),
    "tabla_c": ParagraphStyle("tabla_c", fontName=FUENTE, fontSize=9, leading=11,
                              alignment=TA_CENTER, textColor=NEGRO),
    "tabla_h": ParagraphStyle("tabla_h", fontName=NEGRITA, fontSize=9, leading=11,
                              alignment=TA_CENTER, textColor=NEGRO),
    "rotulo": ParagraphStyle("rotulo", fontName=FUENTE, fontSize=TAM, leading=INTER,
                             spaceBefore=6, spaceAfter=2, keepWithNext=True, textColor=NEGRO),
    "nota": ParagraphStyle("nota", fontName=FUENTE, fontSize=9.5, leading=12.5,
                           spaceBefore=3, spaceAfter=8, textColor=NEGRO),
    "ref": ParagraphStyle("ref", fontName=FUENTE, fontSize=TAM, leading=INTER,
                          leftIndent=SANGRIA, firstLineIndent=-SANGRIA, alignment=TA_LEFT,
                          textColor=NEGRO),
    "codigo": ParagraphStyle("codigo", fontName="Courier", fontSize=7.6, leading=9.2,
                             textColor=NEGRO),
}


# ---------------------------------------------------------------------------
def num(x, d=0):
    """Formato numérico en español: 12.345,6"""
    s = f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def P(texto, estilo="cuerpo"):
    return Paragraph(texto, E[estilo])


def tabla(datos, anchos, centrar_desde=1, separar_filas=()):
    """Tabla APA: sin líneas verticales ni sombreado; solo reglas horizontales."""
    filas = []
    for i, fila in enumerate(datos):
        celdas = []
        for j, c in enumerate(fila):
            if i == 0:
                celdas.append(Paragraph(str(c), E["tabla_h"]))
            else:
                celdas.append(Paragraph(str(c), E["tabla_c" if j >= centrar_desde else "tabla"]))
        filas.append(celdas)
    t = Table(filas, colWidths=anchos, repeatRows=1)
    estilo = [
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, NEGRO),     # sobre el encabezado
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, NEGRO),     # bajo el encabezado
        ("LINEBELOW", (0, -1), (-1, -1), 1.0, NEGRO),   # cierre de la tabla
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    for f in separar_filas:                             # separa grupos de filas
        estilo.append(("LINEABOVE", (0, f), (-1, f), 0.3, NEGRO))
    t.setStyle(TableStyle(estilo))
    return t


def rotulo(tipo_num, titulo):
    """Rótulo APA 7: número en negrita y, en la línea siguiente, título en cursiva."""
    return P(f"<b>{tipo_num}</b><br/><i>{titulo}</i>", "rotulo")


def nota(texto):
    return P(f"<i>Nota.</i> {texto}", "nota")


def figura(ruta, ancho_cm):
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(ruta).getSize()
    ancho = ancho_cm * cm
    return Image(ruta, width=ancho, height=ancho * h / w)


def _numero_pagina(canvas, doc):
    """APA 7: número de página arriba a la derecha, desde la portada."""
    canvas.saveState()
    canvas.setFont(FUENTE, TAM)
    canvas.setFillColor(NEGRO)
    canvas.drawRightString(letter[0] - MARGEN, letter[1] - 1.27 * cm, str(doc.page))
    canvas.restoreState()


TITULO = ("Búsqueda de Soluciones a partir de Algoritmos: Planificación de Tiempos "
          "Semafóricos con el Agente SemaforIA-BOG")


# ---------------------------------------------------------------------------
def portada():
    """Portada de trabajo de estudiante (APA 7, sección 2.3)."""
    return [
        Spacer(1, 5.2 * cm),
        P(TITULO, "titulo"),
        Spacer(1, INTER),
        P(NOMBRE, "centrado"),
        P(INSTITUCION, "centrado"),
        P(f"{CURSO}: Unidad 3, Actividad formativa", "centrado"),
        P(TUTOR, "centrado"),
        P(FECHA, "centrado"),
        PageBreak(),
    ]


# ---------------------------------------------------------------------------
def construir(ruta_pdf, datos):
    filas = datos["escenarios"]
    n_al, reg, resumen, descartadas = datos["aleatorios"]
    ver = datos["verificacion"]
    figs = datos["figuras"]
    agente_log = datos["agente_log"]
    params = filas[0]["problema"].p
    e1, e2, e3 = filas

    # --- cifras derivadas que se citan en el texto
    def ahorro(f):
        return 100 * (1 - f["resultados"]["A*"].costo / f["plan_fijo"]["costo"])

    def red_nodos(f, a="A*", b="UCS"):
        return 100 * (1 - f["resultados"][a].expandidos / f["resultados"][b].expandidos)

    ratio_a_ucs = st.median(a["expandidos"] / u["expandidos"]
                            for a, u in zip(reg["A*"], reg["UCS"]))
    gap_bfs, gap_cod = resumen["BFS"], resumen["Codiciosa"]
    h_frac = datos["h_fraccion"]
    dur_a = sum(a.verde + params.perdido for a in e2["resultados"]["A*"].acciones)
    dur_fijo = sum(a.verde + params.perdido for a in e2["plan_fijo"]["acciones"])
    n_acc = [f["resultados"]["UCS"].n_acciones for f in filas]
    a_vs_ucs = [red_nodos(f) for f in filas]

    h = portada()

    # ===================== PRIMERA PÁGINA DEL TEXTO =====================
    h += [P(TITULO, "titulo"),
          P("Se retoma el agente SemaforIA-BOG trabajado en la unidad anterior: un agente basado en utilidad "
            "que apoya a los operadores del Centro de Gestión de Tránsito (CGT) ajustando los "
            "semáforos de un corredor arterial de Bogotá, ciudad donde un conductor perdió cerca de "
            "122 horas en trancones en 2022 (Redacción Bogotá, 2023). Sus sensores (cámaras, espiras "
            "y pluviómetro) le entregan la cola de cada acceso, la tasa de llegada de vehículos y si "
            "llueve; su actuador es el controlador semafórico. En esta unidad se construye su módulo "
            "de decisión: cuando una intersección queda congestionada, por ejemplo tras un aguacero, "
            "el agente debe encontrar la secuencia de tiempos de verde que la devuelve a operación "
            "normal con la menor demora total para los usuarios. Hoy esa tarea la resuelve un operador "
            "por ensayo y error o un plan de tiempos fijos; formulada como problema de búsqueda, el "
            "agente puede resolverla de forma sistemática (Cano Niño, s. f.; Russell y Norvig, 2021).")]

    # ===================== MODELO =====================
    h += [P("Modelo del Problema de Búsqueda", "h1"),
          P("La Tabla 1 define los cinco elementos del problema. Las colas se modelan como un "
            "fluido determinista (valores esperados), el mismo supuesto del método de Webster "
            "(1958) para el cálculo de semáforos."),
          rotulo("Tabla 1", "Elementos del espacio de búsqueda")]
    lam = "; ".join(f"{x:.2f}".replace(".", ",") for x in params.llegadas)
    h.append(tabla([
        ["Elemento", "Definición en el agente SemaforIA-BOG"],
        ["Estado", "<i>s</i> = (<i>q</i><sub>N</sub>; <i>q</i><sub>S</sub>; <i>q</i><sub>E</sub>; "
                   "<i>q</i><sub>O</sub>; <i>f</i>): cola de cada acceso en vehículos y fase <i>f</i> "
                   "que recibe el próximo verde (NS: norte-sur; EO: este-oeste)."],
        ["Estado inicial", "Lo que percibe el agente. En el escenario E1: (42; 30; 16; 12; NS), con "
                           f"llegadas λ = ({lam}) veh/s y tasa de descarga <i>s</i> = 0,80 veh/s "
                           "(0,64 con lluvia)."],
        ["Acciones", "Dar verde a la fase <i>f</i> durante <i>g</i> = 10, 15, …, 40 s: siete acciones. "
                     "10 s es el verde mínimo peatonal y 40 s el máximo para no dejar en rojo "
                     "indefinido a los demás accesos."],
        ["Modelo de transición", "Durante <i>g</i> s los accesos con verde bajan su cola a la tasa "
                                 "(<i>s</i> − λ) hasta vaciarse y los demás acumulan λ·<i>g</i>; luego "
                                 "hay 5 s de ámbar y todo rojo en los que todos acumulan, y la fase "
                                 f"cambia. Si una cola supera {params.capacidad:.0f} veh (desborde "
                                 "hacia la intersección anterior), la acción no es válida."],
        ["Estado objetivo", f"Toda cola ≤ {params.meta:.0f} veh: la intersección opera sin cola "
                            "residual significativa."],
        ["Función de costo", "Demora en vehículo-segundo: área bajo la curva de cola de los cuatro "
                             "accesos durante la acción. El costo del camino es la demora total."],
    ], [3.3 * cm, ANCHO_TEXTO - 3.3 * cm], centrar_desde=99))

    h += [Spacer(1, 6),
          P("El problema es un grafo dirigido de estados (Figura 1). Las características que más "
            "pesan en la elección del algoritmo son: (a) los costos de las acciones no son uniformes, "
            "pues un verde de 40 s causa más demora que uno de 10 s pero despeja más, así que el plan "
            "con menos acciones no es necesariamente el más barato; (b) hay estados repetidos, porque "
            "distintos órdenes de verdes llevan a las mismas colas, lo que exige búsqueda en grafo; "
            f"(c) el factor de ramificación es <i>b</i> = 7 y las soluciones tienen entre {min(n_acc)} y "
            f"{max(n_acc)} acciones, por lo que la frontera puede crecer como 7<super><i>d</i></super>; "
            "(d) el objetivo es un conjunto de estados, no uno solo; y (e) el dominio permite "
            "construir una heurística admisible, porque se conoce la tasa máxima a la que puede bajar "
            "cada cola."),
          rotulo("Figura 1", "Representación abstracta del problema y primeros niveles del árbol de búsqueda"),
          figura(figs["representacion"], 16.5),
          nota("Las colas se expresan en vehículos (N, S, E, O); <i>g</i> = demora acumulada (veh·s) y "
               "<i>h</i> = heurística. En verde, la primera acción del plan óptimo hallado por A* y por "
               "costo uniforme.")]

    # ===================== ALGORITMOS =====================
    h += [P("Selección y Justificación de los Algoritmos", "h1"),
          P("Se eligieron dos algoritmos no informados y dos informados para medir cuánto aporta la "
            "heurística (Tabla 2). El criterio principal es la optimalidad en costo, porque la demora "
            "es lo que sufren los ciudadanos; el secundario es la eficiencia, porque el agente debe "
            "decidir en pocos segundos con el cómputo del armario semafórico."),
          rotulo("Tabla 2", "Algoritmos seleccionados y su justificación técnica")]
    h.append(tabla([
        ["Algoritmo", "Tipo", "¿Óptimo en este problema?", "Papel en el estudio"],
        ["Búsqueda en anchura (BFS)", "No informada", "No: minimiza el número de acciones, no la demora",
         "Línea base: plan con menos cambios de fase"],
        ["Costo uniforme (UCS)", "No informada", "Sí, con costos positivos (Dijkstra, 1959)",
         "Referencia del óptimo y del esfuerzo sin heurística"],
        ["Codiciosa del mejor primero", "Informada, <i>f</i> = <i>h</i>", "No",
         "Muy rápida; útil si el tiempo de decisión es crítico"],
        ["A*", "Informada, <i>f</i> = <i>g</i> + <i>h</i>",
         "Sí, si <i>h</i> es admisible (Hart et al., 1968)", "Solución propuesta"],
    ], [3.7 * cm, 2.9 * cm, 4.4 * cm, ANCHO_TEXTO - 11.0 * cm], centrar_desde=1))
    h += [Spacer(1, 6),
          P("Se descartaron la búsqueda en profundidad (no es óptima), la profundidad iterativa (ignora "
            "los costos, como BFS) y la bidireccional (el objetivo es un conjunto de estados y la "
            "transición no es invertible)."),
          P("Para la heurística se usó que ninguna cola puede bajar más rápido que <i>r</i><sub>i</sub> = "
            "<i>s</i> − λ<sub>i</sub> y que la búsqueda no termina hasta que cada cola llega a la meta "
            "<i>m</i>. Por tanto, la demora mínima que aún aportará cada acceso es el área del "
            "trapecio que baja de <i>q</i><sub>i</sub> a <i>m</i> a esa tasa:"),
          P("<i>h</i>(<i>n</i>) = Σ (<i>q</i><sub>i</sub><super>2</super> − <i>m</i><super>2</super>) / "
            "(2<i>r</i><sub>i</sub>), para cada acceso con <i>q</i><sub>i</sub> &gt; <i>m</i>", "centrado"),
          P("La cota ignora que las fases compiten por el verde y el tiempo perdido, así que nunca "
            "sobreestima: es admisible y además consistente. El programa lo verifica: en "
            f"{ver['estados']} instancias y {num(ver['aristas'])} transiciones hubo "
            f"{ver['violaciones_admisible']} violaciones de admisibilidad y "
            f"{ver['violaciones_consistente']} de consistencia. En promedio, <i>h</i> del estado inicial "
            f"equivale al {num(100 * h_frac)} % del costo óptimo real, es decir, informa pero de forma "
            "conservadora.")]

    # ===================== IMPLEMENTACIÓN =====================
    h += [P("Implementación en Python", "h1"),
          P("El código se organiza en módulos (Anexo C): <font name='Courier'>modelo.py</font> define "
            "el problema y la clase <font name='Courier'>AgenteSemaforIA</font> (percibir, decidir y "
            "actuar); <font name='Courier'>busqueda.py</font>, los cuatro algoritmos como búsqueda en grafo; "
            "<font name='Courier'>experimentos.py</font>, las pruebas. Las colas se guardan como enteros (centésimas de vehículo) para "
            "reconocer sin error los estados repetidos. Todo se reproduce con "
            "<font name='Courier'>python main.py</font>, que guarda los resultados en CSV; las figuras se "
            "hicieron con Matplotlib (Hunter, 2007). El Anexo B muestra al agente en ejecución.")]

    # ===================== RESULTADOS =====================
    h += [P("Resultados y Comparación", "h1"),
          P("Se evaluaron tres escenarios del corredor: E1, hora pico con vía seca; E2, el mismo "
            "estado inicial con lluvia, que hace la descarga 20 % más lenta; y E3, la salida de un "
            "evento masivo, con colas largas en los accesos este y oeste. Como línea base se simuló el "
            "plan de tiempos fijos actual (30 s NS y 20 s EO). La Figura 2 y la Tabla 3 resumen el "
            "desempeño."),
          rotulo("Figura 2", "Esfuerzo de búsqueda y calidad de la solución por escenario"),
          figura(figs["resultados"], 16.5),
          nota("En (a) el eje vertical está en escala logarítmica. Elaboración propia."),
          rotulo("Tabla 3", "Desempeño de los algoritmos en los tres escenarios")]
    t3 = [["Escenario", "Método", "Demora (veh·h)", "Brecha frente al óptimo",
           "Acciones / duración", "Nodos expandidos", "Frontera máxima", "Tiempo (ms)"]]
    separar, spans = [], []
    for f in filas:
        inicio = len(t3)
        for alg in ("BFS", "UCS", "Codiciosa", "A*"):
            r = f["resultados"][alg]
            dur = sum(a.verde + params.perdido for a in r.acciones)
            t3.append(["", alg, num(r.costo / 3600, 2),
                       f"{num(100 * (r.costo - f['optimo']) / f['optimo'], 1)} %",
                       f"{r.n_acciones} / {num(dur)} s", num(r.expandidos), num(r.max_frontera),
                       num(r.tiempo_ms, 1)])
        pf = f["plan_fijo"]
        dur = sum(a.verde + params.perdido for a in pf["acciones"])
        t3.append(["", "Plan fijo", num(pf["costo"] / 3600, 2),
                   f"{num(100 * (pf['costo'] - f['optimo']) / f['optimo'], 1)} %",
                   f"{len(pf['acciones'])} / {num(dur)} s", "—", "—", "—"])
        t3[inicio][0] = f["escenario"]["nombre"]
        if inicio > 1:
            separar.append(inicio)
        spans.append(("SPAN", (0, inicio), (0, len(t3) - 1)))
    t = tabla(t3, [2.6 * cm, 1.9 * cm, 1.75 * cm, 1.9 * cm, 2.15 * cm, 2.3 * cm, 1.85 * cm,
                   ANCHO_TEXTO - 14.45 * cm], centrar_desde=1, separar_filas=separar)
    t.setStyle(TableStyle(spans))
    h += [t, nota("Brecha = exceso de demora frente al plan óptimo. Los tiempos corresponden a un solo "
                  "hilo de Python y pueden variar según el equipo.")]

    h += [P(f"Para comprobar que las diferencias no dependen de tres casos, se resolvieron {n_al} "
            "instancias aleatorias del mismo corredor (Tabla 4)."),
          rotulo("Tabla 4", f"Resumen sobre {n_al} instancias aleatorias")]
    t4 = [["Algoritmo", "Soluciones óptimas", "Brecha media / máxima", "Nodos expandidos (mediana)",
           "Ramificación efectiva <i>b</i>* (mediana)", "Tiempo mediana / máximo (ms)"]]
    for alg in ("BFS", "UCS", "Codiciosa", "A*"):
        r = resumen[alg]
        t4.append([alg, f"{r['optimos']} de {n_al}",
                   f"{num(r['brecha_media'], 1)} % / {num(r['brecha_max'], 1)} %",
                   num(r["exp_mediana"]), num(r["b_mediana"], 2),
                   f"{num(r['tiempo_mediana'], 1)} / {num(r['tiempo_max'])}"])
    h.append(tabla(t4, [2.4 * cm, 2.4 * cm, 2.9 * cm, 2.9 * cm, 3.0 * cm,
                        ANCHO_TEXTO - 13.6 * cm]))
    txt_desc = (f" Se descartaron {descartadas} instancias en las que alguna búsqueda superó el "
                "límite de 300.000 nodos." if descartadas else "")
    h.append(nota("Instancias generadas con semilla 2026; <i>b</i>* es el factor de ramificación "
                  "efectivo (Russell y Norvig, 2021)." + txt_desc))

    h += [P("En eficiencia, la heurística sí reduce el esfuerzo: A* expandió entre "
            f"{num(min(a_vs_ucs))} % y {num(max(a_vs_ucs))} % menos nodos que UCS en los escenarios, y "
            f"en las instancias aleatorias la mediana de la razón A*/UCS fue {num(ratio_a_ucs, 2)}. La "
            "codiciosa es la más rápida, con decenas de nodos frente a miles, porque avanza casi en "
            "línea recta hacia la meta. BFS fue el más costoso con lluvia (E2), cuyos planes son más largos."),
          P(f"En precisión, A* y UCS encontraron siempre el mismo costo óptimo, como predice la teoría. "
            f"BFS solo fue óptimo en {gap_bfs['optimos']} de {n_al} instancias, con una brecha media de "
            f"{num(gap_bfs['brecha_media'], 1)} %, porque prefiere planes con menos cambios de fase "
            f"aunque generen más demora. La codiciosa fue óptima en {gap_cod['optimos']} de {n_al} "
            f"(brecha media de {num(gap_cod['brecha_media'], 1)} %): elige el verde más largo para la "
            "fase cargada y luego necesita muchas acciones cortas para terminar."),
          P(f"En adecuación al problema, el plan de A* redujo la demora frente al plan fijo en "
            f"{num(ahorro(e1))} % (E1), {num(ahorro(e2))} % (E2) y {num(ahorro(e3))} % (E3). Con lluvia, "
            f"el plan fijo tardó {num(dur_fijo)} s en despejar, frente a {num(dur_a)} s del plan óptimo "
            "(Anexo D), porque sus 30 s de verde apenas alcanzan para la demanda del acceso norte "
            "cuando los vehículos arrancan más despacio. A* es el algoritmo más adecuado: garantiza el "
            "óptimo y, aun en el peor caso observado, decide en una fracción del ciclo del semáforo."),
]

    # ===================== REFLEXIÓN =====================
    h += [P("Reflexión Final", "h1"),
          P("La decisión más importante fue el modelado, más que el algoritmo. Definir el costo como "
            "demora, y no como número de acciones o tiempo hasta despejar, es lo que separa a BFS del "
            "óptimo y alinea al agente con la medida de desempeño definida en la unidad anterior. "
            "Representar las colas con enteros y usar búsqueda en grafo evitó expandir varias veces "
            "estados idénticos, y la restricción de desborde hizo finito el espacio. También se aprendió "
            "que una heurística admisible puede ser correcta y aun así poco informada: la nuestra "
            "recorta el esfuerzo de UCS, pero al ignorar el conflicto entre fases subestima bastante el "
            "costo real."),
          P("El modelo tiene límites: supone llegadas constantes y conocidas, por lo que en la práctica "
            "el agente debería replanificar en cada ciclo con nuevas percepciones (horizonte móvil). "
            "Como mejoras se proponen una heurística más fuerte que considere que las fases no pueden "
            "servirse a la vez; A* ponderado, para cambiar un poco de optimalidad por velocidad; "
            "coordinar varias intersecciones del corredor, lo que convierte el problema en multiagente; "
            "y validar el modelo con aforos reales y simulación de tránsito antes de llevarlo a la calle.")]

    # ===================== REFERENCIAS (página nueva) =====================
    h += [PageBreak(), P("Referencias", "titulo")]
    refs = [
        "Cano Niño, M. A. (s. f.). <i>Introducción a problemas de búsqueda</i> [Lectura fundamental, "
        "Módulo Inteligencia Artificial, Unidad 3]. Material institucional del curso.",
        "Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. <i>Numerische "
        "Mathematik, 1</i>, 269–271. https://doi.org/10.1007/BF01386390",
        "Hart, P. E., Nilsson, N. J. y Raphael, B. (1968). A formal basis for the heuristic determination "
        "of minimum cost paths. <i>IEEE Transactions on Systems Science and Cybernetics, 4</i>(2), "
        "100–107. https://doi.org/10.1109/TSSC.1968.300136",
        "Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. <i>Computing in Science &amp; "
        "Engineering, 9</i>(3), 90–95. https://doi.org/10.1109/MCSE.2007.55",
        "Redacción Bogotá. (2023, 11 de enero). Bogotá, la sexta ciudad con más tráfico en el mundo, "
        "¿cuántas horas se pierden? <i>El Espectador</i>. https://www.elespectador.com/bogota/"
        "bogota-la-sexta-ciudad-con-mas-trafico-en-el-mundo-cuantas-horas-se-pierden/",
        "Russell, S. J. y Norvig, P. (2021). <i>Artificial intelligence: A modern approach</i> (4.ª ed.). "
        "Pearson.",
        "Webster, F. V. (1958). <i>Traffic signal settings</i> (Road Research Technical Paper N.º 39). "
        "Her Majesty's Stationery Office.",
    ]
    h += [P(r, "ref") for r in refs]

    # ===================== ANEXOS (cada uno en página aparte) =====================
    prob2 = e2["problema"]
    t_a = [["Paso", "Acción", "Colas antes (N, S, E, O)", "Colas después", "Demora del paso (veh·s)",
            "<i>g</i> acumulado", "<i>h</i>(estado)"]]
    s, g = prob2.inicial, 0.0
    fmt = lambda est: "; ".join(f"{v:.1f}".replace(".", ",") for v in est.en_vehiculos())
    for i, a in enumerate(e2["resultados"]["A*"].acciones, 1):
        s2, c = prob2.transicion(s, a)
        g += c
        t_a.append([i, f"{a.fase} {a.verde} s", fmt(s), fmt(s2), num(c), num(g), num(prob2.h(s2))])
        s = s2
    h += [PageBreak(), P("Anexo A", "titulo"),
          P("Plan Óptimo de A* en el Escenario con Lluvia (E2)", "titulo"), Spacer(1, 6),
          tabla(t_a, [1.0 * cm, 1.8 * cm, 3.9 * cm, 3.9 * cm, 2.4 * cm, 1.9 * cm,
                      ANCHO_TEXTO - 14.9 * cm]),
          nota("Colas en vehículos; demora y <i>g</i> en vehículo-segundo.")]

    h += [PageBreak(), P("Anexo B", "titulo"),
          P("Ejecución del Agente: Ciclo Percibir, Decidir y Actuar", "titulo"), Spacer(1, 6),
          P("Salida del programa cuando el agente recibe las lecturas de sus sensores en el escenario "
            "con lluvia, planifica con A* y envía las órdenes al controlador semafórico."),
          Spacer(1, 6), Preformatted(agente_log, E["codigo"])]

    h += [PageBreak(), P("Anexo C", "titulo"),
          P("Código Fuente de las Funciones Centrales del Modelo", "titulo"), Spacer(1, 6),
          P("El código completo se entrega junto con este documento. Se reproducen la función de transición con su "
            "costo y la heurística."),
          Spacer(1, 6), Preformatted(datos["codigo_clave"], E["codigo"])]

    h += [PageBreak(), P("Anexo D", "titulo"),
          P("Evolución de las Colas con Cada Plan", "titulo"), Spacer(1, 6),
          rotulo("Figura D1", "Evolución de la cola total con cada plan en el escenario con lluvia"),
          figura(figs["evolucion"], 16.5),
          nota("Cada punto es un cambio de fase; entre paréntesis, el tiempo hasta despejar. La meta "
               f"exige que cada acceso tenga como máximo {params.meta:.0f} veh, no solo la suma. ")]

    doc = SimpleDocTemplate(ruta_pdf, pagesize=letter, leftMargin=MARGEN, rightMargin=MARGEN,
                            topMargin=MARGEN, bottomMargin=MARGEN, title=TITULO,
                            author=NOMBRE, subject=f"{CURSO} - Unidad 3")
    doc.build(h, onFirstPage=_numero_pagina, onLaterPages=_numero_pagina)
    return ruta_pdf
