from pathlib import Path
from parser import cargar_KB, cargar_script
from collections import defaultdict

hash_map = defaultdict(list)
carpeta = Path(__file__).parent
for tipo, hechos in cargar_KB(carpeta):
    for hecho in hechos:
        hash_map[hecho[0]].append((hecho[1], hecho[2])) #sujeto : (predicado, objeto)


def esVar(hecho):
    return len(hecho) == 1 and isinstance(hecho, str) and hecho.isalpha()

    
for tipo, hechos in cargar_script(carpeta / "script.sbq"):
    if tipo != "afirmacion":
        statements = []
        for hecho in hechos:
            ans = True
            variables = 0
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
                            pareja[0] == v1
                            for lista_parejas in hash_map.values()
                            for pareja in lista_parejas
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
                        encontrado = any(hecho[2] in pareja for pareja in hash_map[hecho[0]])
                    elif not esVar(hecho[1]) and esVar(hecho[2]):
                        encontrado = any(hecho[1] in pareja for pareja in hash_map[hecho[0]])
                    else:
                        encontrado = (hecho[1], hecho[2]) in hash_map[hecho[0]]

                elif esVar(hecho[0]):
                    pareja = (hecho[1], hecho[2])
                    encontrado = any(pareja in valores for valores in hash_map.values())

            ans = ans and encontrado
            statements.append(" ".join(hecho))
                    
        if ans:
            print(f"{", ".join(statements)}? -> SI")
        else:
            print(f"{", ".join(statements)}? -> NO")

    # else: ignoramos
