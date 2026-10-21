from pathlib import Path
from profesor import cargar_KB, cargar_script
from collections import defaultdict

hash_map = defaultdict(list)
carpeta = Path(__file__).parent
for tipo, hechos in cargar_KB(carpeta):
    for hecho in hechos:
        hash_map[hecho[0]].append((hecho[1], hecho[2]))  # sujeto : (predicado, objeto)


def esVar(hecho):
    return isinstance(hecho, str) and hecho[0].isupper()


# Funciones que para que variables de distintos predicados coincidan
def unificar(termino, valor, sustitucion):
    """Intenta casar un término de la pregunta con un valor de la KB.
    Devuelve la sustitución ampliada, o None si no casa."""
    if esVar(termino):
        if termino in sustitucion:
            return sustitucion if sustitucion[termino] == valor else None
        nueva = dict(sustitucion)
        nueva[termino] = valor
        return nueva
    return sustitucion if termino == valor else None


def resolver(hechos, sustitucion=None):
    """Busca una asignación de variables que satisfaga TODOS los hechos a la vez
    (backtracking): la X del primer hecho tiene que ser la misma X en el resto."""
    if sustitucion is None:
        sustitucion = {}
    if not hechos:
        return True
    s, p, o = hechos[0]
    for sujeto, parejas in hash_map.items():
        sub1 = unificar(s, sujeto, sustitucion)
        if sub1 is not None:
            for predicado, objeto in parejas:
                sub2 = unificar(p, predicado, sub1)
                if sub2 is not None:
                    sub3 = unificar(o, objeto, sub2)
                    if sub3 is not None and resolver(hechos[1:], sub3):
                        return True
    return False


for tipo, hechos in cargar_script(carpeta / "script.sbq"):
    if tipo != "afirmacion":
        statements = []
        for hecho in hechos:
            ans = True
            variables = 0
            encontrado = False
            variables += sum(1 for palabra in hecho if esVar(palabra))

            if variables == 2:
                v0, v1, v2 = hecho[0], hecho[1], hecho[2]

                if esVar(v0) and esVar(v2):
                    if v0 == v2:
                        # Ej. X admira X
                        encontrado = any(
                            k == pareja[1]
                            for k, lista_parejas in hash_map.items()
                            for pareja in lista_parejas
                            if pareja[0] == v1
                        )
                    else:
                        # Ej. X admira Y
                        encontrado = any(
                            k != pareja[1]
                            for k, lista_parejas in hash_map.items()
                            for pareja in lista_parejas
                            if pareja[0] == v1
                        )

                elif esVar(v0) and esVar(v1):
                    encontrado = any(
                        pareja[1] == v2
                        for lista_parejas in hash_map.values()
                        for pareja in lista_parejas
                    )

                else:
                    encontrado = v0 in hash_map and len(hash_map[v0]) > 0

            else:
                if hecho[0] in hash_map:
                    if esVar(hecho[1]) and not esVar(hecho[2]):
                        encontrado = any(
                            hecho[2] in pareja for pareja in hash_map[hecho[0]]
                        )
                    elif not esVar(hecho[1]) and esVar(hecho[2]):
                        encontrado = any(
                            hecho[1] in pareja for pareja in hash_map[hecho[0]]
                        )
                    else:
                        encontrado = (hecho[1], hecho[2]) in hash_map[hecho[0]]

                elif esVar(hecho[0]):
                    pareja = (hecho[1], hecho[2])
                    encontrado = any(pareja in valores for valores in hash_map.values())

            ans = ans and encontrado
            statements.append(" ".join(hecho))

        if len(hechos) > 1:
            ans = resolver(hechos)

        if ans:
            print(f"{', '.join(statements)}? -> SI")
        else:
            print(f"{', '.join(statements)}? -> NO")

    # else: ignoramos
