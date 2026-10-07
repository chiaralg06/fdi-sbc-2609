# Código de ayuda para gestionar bases de conocimiento

from pathlib import Path

from pyparsing import DelimitedList, Group, Suppress, Word, alphas

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


def cargar_KB(directorio: Path):
    for p in sorted(directorio.glob("*.sbc")):
        yield from _kb.parse_file(p, parse_all=True)


def cargar_script(fichero: Path):
    yield from _script.parse_file(fichero, parse_all=True)



