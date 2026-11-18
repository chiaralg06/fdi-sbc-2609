"""CLI del motor de preguntas sobre bases de conocimiento (sbc).

Uso: uv run -m sbc [OPCIONES] DIRECTORIO [SCRIPT]

en este ejemplo:
cd fdi-sbc-2609
uv run -m sbc --jsonl . script.sbq (para obtener los expected.jsonl)
uv run -m sbc . script.sbq (para obtener expected.txt)
"""

import sys
from collections import defaultdict
from itertools import count
from pathlib import Path

import click
from loguru import logger
from pyparsing import ParseException

from profesor import _script, cargar_KB, cargar_script, imprimir_jsonl


def es_variable(termino):
    return termino[0].isupper() or termino[0] == "_"


def valor_de(termino, sustitucion):
    """Sigue las ligaduras de la sustitución hasta el final: si X -> Y e
    Y -> ana, el valor de X es ana. Si la variable no tiene valor, la
    devuelve tal cual."""
    while es_variable(termino) and termino in sustitucion:
        termino = sustitucion[termino]
    return termino


def unifica(a, b, sustitucion):
    """
    Se pueden "emparejar" los términos a y b?
    Primero se sustituye cada uno por su valor (si son variables con valor).
    - Si quedan iguales, ya están emparejados.
    - Si uno es una variable sin valor, se le asigna el otro (que puede ser
      una constante u otra variable, al usar reglas).
    - Si son dos constantes distintas -> NO
    """
    a, b = valor_de(a, sustitucion), valor_de(b, sustitucion)
    if a == b:
        return sustitucion

    if es_variable(a) or es_variable(b):
        variable, otro = (a, b) if es_variable(a) else (b, a)
        nueva_sustitucion = dict(sustitucion)  # copia nueva del diccionario
        nueva_sustitucion[variable] = otro
        return nueva_sustitucion

    return None  # Son constantes, pero diferentes -> NO


def unifica_tripleta(tripleta_a, tripleta_b, sustitucion):
    for a, b in zip(tripleta_a, tripleta_b):
        sustitucion = unifica(a, b, sustitucion)
        if sustitucion is None:
            return None
    return sustitucion


def a_texto(hechos):
    """[("ana", "madre_de", "luis"), ...] -> 'ana madre_de luis, ...'"""
    return ", ".join(" ".join(hecho) for hecho in hechos)


class KB:
    """Base de conocimiento: hechos, reglas y el estado de razona/explica."""

    def __init__(self):
        self.hash_map = defaultdict(list)  # sujeto -> [(predicado, objeto)]
        self.reglas = []  # [(consecuente, antecedente)]
        self.razonar = False  # razona si! / razona no!: encadenamiento hacia atrás
        self.explicar = False  # explica si! / explica no!: razonamiento por stderr
        self.usos_de_reglas = count()  # para renombrar variables en cada uso

    def __str__(self):
        """La base de conocimiento (hechos y reglas) con la misma sintaxis de
        los .sbc, para imprimir!."""
        lineas = [
            f"{sujeto} {predicado} {objeto}."
            for sujeto, parejas in self.hash_map.items()
            for predicado, objeto in parejas
        ]
        lineas += [
            f"{a_texto(consecuente)} <- {a_texto(antecedente)}."
            for consecuente, antecedente in self.reglas
        ]
        return "\n".join(lineas)

    def afirmar(self, hechos):
        """Añade los hechos que no estén ya. Devuelve si se ha añadido alguno."""
        nuevo = False
        for sujeto, predicado, objeto in hechos:
            if es_variable(sujeto) or es_variable(predicado) or es_variable(objeto):
                continue

            pareja = (predicado, objeto)
            if pareja not in self.hash_map[sujeto]:
                self.hash_map[sujeto].append(pareja)
                nuevo = True

        return nuevo

    def afirmar_regla(self, regla):
        if regla not in self.reglas:
            self.reglas.append(regla)

    def renombra(self, regla):
        """Copia de la regla con variables nuevas (X -> X#3), para que no se
        mezclen con las de la consulta ni con las de otro uso de la misma regla.
        El parser no admite # en los términos, así que no pueden chocar."""
        n = next(self.usos_de_reglas)
        consecuente, antecedente = regla

        def cambia(hechos):
            return [
                tuple(f"{t}#{n}" if es_variable(t) else t for t in hecho)
                for hecho in hechos
            ]

        return cambia(consecuente), cambia(antecedente)

    def resolver(self, preguntas, sustitucion=None):
        """Genera cada sustitución de variables que satisface TODAS las tripletas
        de `preguntas` a la vez (una por cada solución distinta). Con
        `razona si!` usa también las reglas (encadenamiento hacia atrás)."""
        if sustitucion is None:
            sustitucion = {}

        if not preguntas:  # caso base de la recursión
            yield sustitucion
            return

        sujeto, predicado, objeto = preguntas[0]
        resto = preguntas[1:]

        # 1) Con los hechos. Si el sujeto ya tiene valor, solo hace falta mirar
        # ese sujeto (el diccionario está indexado por sujeto)
        sujeto_valor = valor_de(sujeto, sustitucion)
        if es_variable(sujeto_valor):
            candidatos = self.hash_map.items()  # sujeto libre: hay que mirar todos
        elif sujeto_valor in self.hash_map:
            candidatos = [(sujeto_valor, self.hash_map[sujeto_valor])]
        else:
            candidatos = []  # ese sujeto no tiene ningún hecho

        for sujeto_kb, parejas in candidatos:
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

                yield from self.resolver(resto, nueva_sustitucion)

        # 2) Con las reglas (razona si!): si un consecuente encaja con la
        # pregunta, se cambia la pregunta por el antecedente de la regla
        if self.razonar:
            for regla in self.reglas:
                consecuente, antecedente = self.renombra(regla)
                for hecho in consecuente:
                    nueva_sustitucion = unifica_tripleta(
                        preguntas[0], hecho, sustitucion
                    )
                    if nueva_sustitucion is not None:
                        yield from self.resolver(antecedente + resto, nueva_sustitucion)

    def descubrir(self):
        """Aplica las reglas hasta que no salen hechos nuevos, y devuelve
        cuántos hechos nuevos se han añadido."""
        total = 0
        while True:
            cambios = False

            for consecuente, antecedente in self.reglas:
                soluciones = list(self.resolver(antecedente))

                for sust in soluciones:
                    for s, p, o in consecuente:
                        hecho_nuevo = tuple(valor_de(t, sust) for t in (s, p, o))
                        if self.afirmar([hecho_nuevo]):
                            cambios = True
                            total += 1

            if not cambios:
                return total


def configurar_log(nivel):
    try:
        logger.level(nivel)  # ValueError si loguru no conoce el nivel
    except ValueError:
        logger.error(f"Nivel de log desconocido: {nivel}")
        return

    logger.remove()
    logger.add(sys.stderr, level=nivel)


def sin_comillas(valor):
    """'"Fëanor"' -> 'Fëanor' (los literales guardan sus comillas)."""
    return valor[1:-1] if valor.startswith('"') else valor


def imprime_soluciones(hechos, soluciones):
    # variables de la consulta, en orden de aparición y sin repetir,
    # quitando las auxiliares (las que empiezan por _)
    terminos = dict.fromkeys(t for hecho in hechos for t in hecho)
    variables = [t for t in terminos if es_variable(t) and not t.startswith("_")]
    if not variables:
        return  # consulta sin variables visibles: basta con el SI/NO

    # quitar duplicados y ordenar
    filas = sorted({tuple(s[v] for v in variables) for s in soluciones})
    for fila in filas:
        print(
            "   ",
            ", ".join(f"{v} = {sin_comillas(x)}" for v, x in zip(variables, fila)),
        )


def responde(kb, hechos, jsonl, detalle=False):
    # de cada solución, solo el valor final de las variables de la consulta
    # (las de las reglas, como X#3, son internas)
    terminos = dict.fromkeys(t for hecho in hechos for t in hecho)
    variables = [t for t in terminos if es_variable(t)]
    soluciones = [{v: valor_de(v, s) for v in variables} for s in kb.resolver(hechos)]
    if jsonl:
        imprimir_jsonl(hechos, soluciones)
    else:
        print(f"{a_texto(hechos)}? -> {'SI' if soluciones else 'NO'}")
        if detalle:
            imprime_soluciones(hechos, soluciones)


def procesa(kb, tipo, hechos, jsonl=False, detalle=False):
    match (tipo, hechos):
        case ("afirmacion", _):
            kb.afirmar(hechos)
        case ("pregunta", _):
            responde(kb, hechos, jsonl, detalle)
        case ("regla", _):
            kb.afirmar_regla(hechos)
        case ("comando", ["descubre"]):
            nuevos = kb.descubrir()
            logger.info(f"Descubiertos {nuevos} hechos nuevos")
        case ("comando", ["cargar", fichero]):
            for tipo_frase, frase in cargar_script(Path(fichero)):
                procesa(kb, tipo_frase, frase, jsonl, detalle)
        case ("comando", ["log", nivel]):
            configurar_log(nivel.upper())
        case ("comando", ["imprimir"]):
            print(kb, file=sys.stderr)
        case ("comando", ["razona", "si" | "no" as valor]):
            kb.razonar = valor == "si"
        case ("comando", ["explica", "si" | "no" as valor]):
            kb.explicar = valor == "si"
        case ("comando", palabras):
            logger.error(f"Comando desconocido: {' '.join(palabras)}!")


def ejecuta_script(kb, fichero, jsonl):
    for tipo, hechos in cargar_script(fichero):
        procesa(kb, tipo, hechos, jsonl)


def cargar_linea(texto):
    """Parsea una línea escrita por el usuario (afirmación o pregunta),
    igual que una línea de un script, usando la misma gramática de `profesor`."""
    try:
        yield from _script.parse_string(texto, parse_all=True)
    except ParseException as e:
        logger.error(f"Error de sintaxis: {e}")


def modo_interactivo(kb, jsonl):
    try:
        import readline  # noqa: F401  habilita edición de línea e historial en input()
    except ImportError:
        logger.warning("readline no disponible: sin historial ni edición de línea")

    logger.info(
        "Modo interactivo: afirmaciones (.) o consultas (?). Ctrl+D para salir."
    )
    while True:
        try:
            linea = input("sbc> ")
        except EOFError:
            print()
            break

        if not linea.strip():
            continue

        for tipo, hechos in cargar_linea(linea):
            procesa(kb, tipo, hechos, jsonl, detalle=True)


@click.command()
@click.argument(
    "directorio", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.argument(
    "script",
    required=False,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
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
    kb = KB()
    for tipo, hechos in cargar_KB(directorio):
        procesa(kb, tipo, hechos)

    if script is not None:
        ejecuta_script(kb, script, jsonl)

    if script is None or interactivo:
        modo_interactivo(kb, jsonl)


if __name__ == "__main__":
    cli(prog_name="sbc")
