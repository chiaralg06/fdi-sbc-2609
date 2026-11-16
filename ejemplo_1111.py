def procesar(kb: KB, frase: tuple, jsonl: bool):
    match frase:
        case ("afirmacion", contenido):
            for hecho in a_hechos(contenido):
                kb.afirmar(hecho)
        case ("regla", (consecuente, antecedente)):
            kb.afirmar(Regla(a_hechos(consecuente), a_hechos(antecedente)))
        case ("pregunta", contenido):
            hechos = a_hechos(contenido)
            soluciones = None  # TODO
            if jsonl:
                imprimir_jsonl(contenido, soluciones)
            else:
                raise NotImplementedError
        case ("comando", ["descubre"]):
            nuevos = kb.descubrir()
            logger.info(f"Descubiertos {len(nuevos)} hechos nuevos")
        case ("comando", ["imprimir"]):
            print(kb, file=sys.stderr)
        case ("comando", ["cargar", fichero]):
            for f in cargar_script(Path(fichero)):
                procesar(kb, f, jsonl)
        case ("comando", ["log", nivel]) if nivel.upper() in NIVELES_LOG:
            configurar_log(nivel)
        case ("comando", palabras):
            logger.error(f"Comando desconocido: {' '.join(palabras)}!")
