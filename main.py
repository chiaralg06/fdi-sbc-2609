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
            if hecho[0] in hash_map:
                if esVar(hecho[1]) and not esVar(hecho[2]):
                    encontrado = any(hecho[2] in pareja for pareja in hash_map[hecho[0]])
                    ans = ans and encontrado
                    statements.append(" ".join(hecho))
                elif not esVar(hecho[1]) and esVar(hecho[2]):
                    encontrado = any(hecho[1] in pareja for pareja in hash_map[hecho[0]])
                    ans = ans and encontrado
                    statements.append(" ".join(hecho))
                else:
                    ans = ans and (hecho[1], hecho[2]) in hash_map[hecho[0]]
                    statements.append(" ".join(hecho))

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
