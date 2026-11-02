# SemaforIA-BOG · Búsqueda de soluciones a partir de algoritmos (Unidad 3)

Agente inteligente que planifica los tiempos de verde de una intersección
semaforizada de Bogotá para despejar las colas con la menor demora total.
Compara búsqueda en anchura (BFS), costo uniforme (UCS), búsqueda codiciosa
del mejor primero y A*.

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
python main.py            # estudio completo (100 instancias, ~1-3 min)

```

Todo se guarda en `resultados/`:

| Archivo | Contenido |
|---|---|
| `Informe_U3_Busqueda_SemaforIA.pdf` | Informe generado automáticamente |
| `escenarios.csv` | Métricas y plan de cada algoritmo en E1, E2, E3 |
| `aleatorios.csv` | Métricas de las 100 instancias aleatorias |
| `resumen.json` | Resumen estadístico y verificación de la heurística |
| `fig*.png` | Figuras del informe |

## Estructura

| Módulo | Qué hace |
|---|---|
| `modelo.py` | Estado, acciones, transición, objetivo, costo, heurística y la clase `AgenteSemaforIA` |
| `busqueda.py` | BFS, UCS, codiciosa y A* (búsqueda en grafo) con métricas |
| `experimentos.py` | Escenarios, plan fijo, instancias aleatorias y verificación de la heurística |
| `graficos.py` | Figuras (matplotlib) |
| `informe.py` | Generación del PDF (ReportLab) |
| `main.py` | Ejecuta todo |

El informe sigue las normas APA 7 (portada de estudiante, Arial 11, interlineado 1,5,
tablas y figuras APA, referencias con sangría francesa y anexos).


