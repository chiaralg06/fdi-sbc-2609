"""CLI del motor de preguntas sobre bases de conocimiento (sbc).

Uso: uv run -m sbc [OPCIONES] DIRECTORIO [SCRIPT]

en este ejemplo:
cd fdi-sbc-2609
uv run -m sbc --jsonl . script.sbq (para obtener los expected.jsonl)
uv run -m sbc . script.sbq (para obtener expected.txt)
"""

from collections import defaultdict
from pathlib import Path

import click
from loguru import logger
from pyparsing import ParseException

from profesor import _script, cargar_KB, cargar_script, imprimir_jsonl

hash_map = defaultdict(list)


def es_variable(termino):
    return termino[0].isupper()


def unifica(termino, valor, sustitucion):
    """
    Se puede "emparejar" el término con el valor?
    Si ambos son constantes, sólo se pueden emparejar si son iguales.
    Si hay variables:
    - si hay sustitución (valor(es) asignado(s) a la variable), valor debe
    estar entre ellos
    - si no la hay, se añade
    """
    if not es_variable(termino):
        if termino == valor:
            return sustitucion
        return None  # Son constantes, pero diferentes -> NO

    if termino in sustitucion:
        if sustitucion[termino] == valor:
            return sustitucion
        return None  # ya hay valor asignado, y no es ese -> NO

    # no hay valor asignado -> se asigna
    nueva_sustitucion = dict(sustitucion)  # copia nueva del diccionario de entrada
    nueva_sustitucion[termino] = valor
    return nueva_sustitucion


def resolver(preguntas, sustitucion=None):
    """Genera cada sustitución de variables que satisface TODAS las tripletas
    de `preguntas` a la vez (una por cada solución distinta)."""
    if sustitucion is None:
        sustitucion = {}

    if not preguntas:  # caso base de la recursión
        yield sustitucion
        return

    sujeto, predicado, objeto = preguntas[0]
    resto = preguntas[1:]

    for sujeto_kb, parejas in hash_map.items():
        sustitucion_sujeto = unifica(sujeto, sujeto_kb, sustitucion)
        if sustitucion_sujeto is None:
            continue

        for predicado_kb, objeto_kb in parejas:
            nueva_sustitucion = unifica(predicado, predicado_kb, sustitucion_sujeto)
            if nueva_sustitucion is None:
                continue

            nueva_sustitucion = unifica(objeto, objeto_kb, nueva_sustitucion)
            if nueva_sustitucion is None:
                continue

            yield from resolver(resto, nueva_sustitucion)


def afirma(hechos):
    for hecho in hechos:
        hash_map[hecho[0]].append((hecho[1], hecho[2]))


def responde(hechos, jsonl):
    soluciones = list(resolver(hechos))
    if jsonl:
        imprimir_jsonl(hechos, soluciones)
    else:
        texto = ", ".join(" ".join(hecho) for hecho in hechos)
        print(f"{texto}? -> {'SI' if soluciones else 'NO'}")


def procesa(tipo, hechos, jsonl):
    if tipo == "afirmacion":
        afirma(hechos)
    else:
        responde(hechos, jsonl)


def ejecuta_script(fichero, jsonl):
    for tipo, hechos in cargar_script(fichero):
        procesa(tipo, hechos, jsonl)


def cargar_linea(texto):
    """Parsea una línea escrita por el usuario (afirmación o pregunta),
    igual que una línea de un script, usando la misma gramática de `profesor`."""
    try:
        yield from _script.parse_string(texto, parse_all=True)
    except ParseException as e:
        logger.error(f"Error de sintaxis: {e}")


def modo_interactivo(jsonl):
    try:
        import readline  # noqa: F401  habilita edición de línea e historial en input()
    except ImportError:
        logger.warning("readline no disponible: sin historial ni edición de línea")

    logger.info("Modo interactivo: afirmaciones (.) o consultas (?). Ctrl+D para salir.")
    while True:
        try:
            linea = input("sbc> ")
        except EOFError:
            print()
            break

        if not linea.strip():
            continue

        for tipo, hechos in cargar_linea(linea):
            procesa(tipo, hechos, jsonl)


@click.command()
@click.argument("directorio", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("script", required=False, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-i",
    "--interactive",
    "interactivo",
    is_flag=True,
    help="Entra en modo interactivo después de ejecutar SCRIPT.",
)
@click.option(
    "--jsonl",
    is_flag=True,
    help="Imprime las respuestas en formato JSON Lines en vez de texto libre.",
)
def cli(directorio, script, interactivo, jsonl):
    """Carga la base de conocimiento de los ficheros .sbc de DIRECTORIO.

    Si se da SCRIPT, ejecuta sus afirmaciones y consultas. Si no se da,
    entra en modo interactivo, leyendo afirmaciones y consultas del usuario.
    """
    for _, hechos in cargar_KB(directorio):
        afirma(hechos)

    if script is not None:
        ejecuta_script(script, jsonl)

    if script is None or interactivo:
        modo_interactivo(jsonl)


if __name__ == "__main__":
    cli(prog_name="sbc")
