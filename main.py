from pathlib import Path
from parser import cargar_KB, cargar_script
from collections import defaultdict

hash_map = defaultdict(list)
carpeta = Path(__file__).parent
for tipo, hechos in cargar_KB(carpeta):
    for hecho in hechos:
        hash_map[hecho[0]].append((hecho[1], hecho[2])) #sujeto : (predicado, objeto)

    
for tipo, hechos in cargar_script(carpeta / "script.sbq"):
    if tipo != "afirmacion":
        statements = []
        for hecho in hechos:
            ans = True
            if hecho[0] in hash_map:
                ans = ans and (hecho[1], hecho[2]) in hash_map[hecho[0]]
                statements.append(" ".join(hecho))
                    
        if ans:
            print(f"{", ".join(statements)}? -> SI")
        else:
            print(f"{", ".join(statements)}? -> NO")

    # else: ignoramos
