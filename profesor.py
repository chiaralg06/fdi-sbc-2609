# Código de ayuda para gestionar bases de conocimiento

import json
from pathlib import Path

from loguru import logger
from pyparsing import (
    DelimitedList,
    Group,
    ParseException,
    Suppress,
    Word,
    alphas,
    python_style_comment,
)

# Un término es una palabra con caracteres alfanuméricos
_termino = Word(alphas + "_:ñ0123456789")

# Un hecho es una tripleta sujeto predicado objeto (3 términos)
_hecho = _termino * 3
_hecho.set_parse_action(lambda t: [tuple(t)])

_lista_hechos = Group(DelimitedList(_hecho, ","), aslist=True)

# Una afirmación es una lista de hechos acabada en un punto
_afirmacion = _lista_hechos + Suppress(".")
_afirmacion.set_parse_action(lambda t: [("afirmacion", t[0])])

# Una pregunta es una lista de hechos acabada en una interrogación
_pregunta = _lista_hechos + Suppress("?")
_pregunta.set_parse_action(lambda t: [("pregunta", t[0])])

# Una base de conocimiento contiene afirmaciones
_kb = _afirmacion * ...

# Un script puede contener además preguntas
_linea = _pregunta | _afirmacion
_script = _linea * ...

# Comentarios estilo python, que van desde # hasta el final de la línea
_kb.ignore(python_style_comment)
_script.ignore(python_style_comment)


def _cargar(gramatica, fichero: Path):
    logger.info(f"Cargando {fichero}")
    try:
        yield from gramatica.parse_file(fichero, parse_all=True)
    except ParseException as e:
        logger.error(f"Error de sintaxis en {fichero}: {e}")


def cargar_KB(directorio: Path):
    for p in sorted(directorio.glob("*.sbc")):
        yield from _cargar(_kb, p)


def cargar_script(fichero: Path):
    yield from _cargar(_script, fichero)


def imprimir_jsonl(consulta, soluciones):
    """Imprime por stdout la respuesta a una consulta en formato JSON Lines.
    `consulta` es la lista de hechos tal como la entrega `cargar_script`, y cada
    solución algo que `dict()` pueda convertir en `{variable: valor}`."""
    terminos = dict.fromkeys(t for hecho in consulta for t in hecho)
    unicas = {
        tuple((t, s[t]) for t in terminos if t in s) for s in map(dict, soluciones)
    }
    respuesta = {
        "consulta": ", ".join(" ".join(hecho) for hecho in consulta),
        "soluciones": [
            dict(s) for s in sorted(unicas, key=lambda s: [v for _, v in s])
        ],
    }
    print(json.dumps(respuesta, ensure_ascii=False))
