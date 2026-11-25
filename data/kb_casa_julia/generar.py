"""Genera los ficheros .sbc con hechos repetitivos de la base de conocimiento.

Uso (desde cualquier sitio):  python3 generar.py

Escribe, junto a este script:
  02_habitaciones.sbc  plantas, 240 habitaciones, sus aparatos de clima y las
                       salas de planta con sus cubos y rollos de papel
  04_tiempo.sbc        franjas de media hora, su orden nocturno y las franjas
                       con nombre (visitas, comedor, gimnasio)
  05_tablas.sbc        tablas aritmeticas (restar circulos, comparar aforos)

El motor no sabe contar ni comparar, asi que esas tablas son los datos con los
que las reglas "cuentan". No hay nada que editar a mano en esos tres ficheros:
se cambia este script y se vuelve a ejecutar.
"""

from pathlib import Path

AQUI = Path(__file__).resolve().parent
PABELLONES = "abc"
PLANTAS = [1, 2, 3, 4]
HABITACIONES_POR_PLANTA = 20
CABECERA = "# FICHERO GENERADO por generar.py. No editar a mano.\n"


def escribe(nombre, lineas):
    (AQUI / nombre).write_text(CABECERA + "\n".join(lineas) + "\n", encoding="utf-8")
    print(f"{nombre}: {len(lineas)} lineas")


def habitaciones():
    out = [
        "# Plantas de cada pabellon, sus habitaciones y sus salas de planta.",
        "# Una habitacion es a<planta><numero>: a203 = pabellon A, planta 2, numero 03.",
        "",
    ]
    for p in PABELLONES:
        P = p.upper()
        for n in PLANTAS:
            planta = f"{p}_{n}"
            out.append(
                f"{planta} es_un planta_pabellon, {planta} esta_en pabellon_{p}, "
                f'{planta} nombre "Pabellón {P}, planta {n}".'
            )
            out.append(
                f"alarma_{planta} es_un alarma_incendio, alarma_{planta} esta_en {planta}."
            )
            # sala de planta con sus cosas (los rollos y los cubos se vigilan)
            sala = f"sala_{planta}"
            out.append(
                f"{sala} es_un sala_de_planta, {sala} esta_en {planta}, "
                f'{sala} nombre "Sala de la planta {n} del pabellón {P}".'
            )
            out.append(
                f"papel_{planta} es_un rollo_papel, papel_{planta} esta_en {sala}."
            )
            out.append(
                f"basura_{planta} es_un cubo_basura, basura_{planta} esta_en {sala}."
            )
            out.append(f"ropa_{planta} es_un cubo_ropa, ropa_{planta} esta_en {sala}.")
            for k in range(1, HABITACIONES_POR_PLANTA + 1):
                h = f"{p}{n}{k:02d}"
                out.append(f"{h} es_un habitacion, {h} esta_en {planta}.")
                out.append(f"{h}_calef es_un calefaccion, {h}_calef esta_en {h}.")
                out.append(f"{h}_aire es_un aire_acondicionado, {h}_aire esta_en {h}.")
    return out


def franjas():
    hh = [f"t{h:02d}{m:02d}" for h in range(24) for m in (0, 30)]
    out = ["# Franjas de media hora: t0730 = de 07:30 a 08:00.", ""]
    out += [f"{t} es_un franja_horaria." for t in hh]

    # Orden nocturno: de las 20:00 a las 06:30. Solo hace falta comparar horas
    # de llegada con un limite, y las llegadas viven en la noche.
    noche = [t for t in hh if t >= "t2000"] + [t for t in hh if t <= "t0630"]
    out += ["", "# T posterior_a U: T viene despues que U contando desde las 20:00."]
    for i, a in enumerate(noche):
        for b in noche[i + 1 :]:
            out.append(f"{b} posterior_a {a}.")

    def rango(desde, hasta):  # ambos incluidos
        return [t for t in hh if desde <= t <= hasta]

    def pon(franja, ts):
        return [f"{t} en_franja {franja}." for t in ts]

    out += ["", "# Chicos que no son de la familia: fuera a las 23:00"]
    out += pon("noche_visitas", rango("t2300", "t2330") + rango("t0000", "t0630"))
    out += [
        "",
        "# Comedor y gimnasio (la franja es la hora de inicio de cada media hora)",
    ]
    out += [f"desayuno_lab abre_en {t}." for t in rango("t0700", "t0830")]
    out += [f"desayuno_finde abre_en {t}." for t in rango("t0800", "t0930")]
    out += [f"comida abre_en {t}." for t in rango("t1300", "t1500")]
    out += [f"cena abre_en {t}." for t in rango("t2030", "t2130")]
    out += [f"horario_gimnasio abre_en {t}." for t in rango("t0700", "t2230")]
    return out


def tablas():
    out = ["# Tablas para contar. n7 = siete circulos de la tarjeta.", ""]
    for n in range(0, 21):
        out.append(f"n{n} es_un saldo_valido.")
    out.append("")
    out.append("# N menos_1 R: al tachar un circulo quedan R. sin_saldo = no habia.")
    for n in range(0, 21):
        out.append(f"n{n} menos_1 {'n' + str(n - 1) if n >= 1 else 'sin_saldo'}.")
    out.append("# N menos_2 R: dos circulos.")
    for n in range(0, 21):
        out.append(f"n{n} menos_2 {'n' + str(n - 2) if n >= 2 else 'sin_saldo'}.")
    out += ["", "# Aforo: k5 mayor_que k4 = un grupo de 5 no cabe en una sala de 4."]
    for a in range(1, 12):
        for b in range(1, a):
            out.append(f"k{a} mayor_que k{b}.")
    return out


if __name__ == "__main__":
    escribe("02_habitaciones.sbc", habitaciones())
    escribe("04_tiempo.sbc", franjas())
    escribe("05_tablas.sbc", tablas())
