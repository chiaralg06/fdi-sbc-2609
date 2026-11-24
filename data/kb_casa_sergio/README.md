# Base de conocimiento de Sergio: un chalet familiar

La vivienda es un chalet de tres plantas con parcela. En el sótano hay una
sala de cine y juegos, un gimnasio y el cuarto de máquinas. En la planta baja
están el salón, la cocina, el despacho donde teletrabaja Elena y el garaje.
Arriba están los dormitorios. Fuera hay jardín, piscina y porche. Viven Luis
y Elena (los padres), Sergio (20 años), su hermano pequeño Pablo (12) y
Thor, el perro. Luis tiene un coche eléctrico y Elena uno de gasolina.

La domótica se centra en el garaje y los coches, el jardín y la piscina, y
el clima por plantas. Los conflictos giran en torno a Thor, al ocio frente
al ahorro y a los padres frente a los hijos.

## Cómo se usa

```
uv run -m sbc data/kb_casa_sergio data/kb_casa_sergio/consultas.sbq
uv run -m sbc data/kb_casa_sergio data/kb_casa_sergio/escenarios/1_tarde_verano.sbq
```

Los escenarios activan `razona si!`. También funcionan con `descubre!`
(hacia delante) en lugar de `razona si!`.

## Organización

| Fichero | Contenido |
|---|---|
| `00_chalet.sbc` | Plantas, espacios, de quién es cada dormitorio y qué zonas son comunes |
| `01_clases.sbc` | Taxonomía: espacios, seres vivos, vehículos y dispositivos |
| `02_familia.sbc` | La familia con su categoría, Thor (y quién lo cuida), los coches, rutinas |
| `03_momentos.sbc` | Momentos del día: luz, tarifa, cierre nocturno, pantallas, silencio, riego... |
| `04_domotica.sbc` | Dispositivos: qué son, dónde están, qué estancias climatizan, cuáles gastan mucho |
| `05_modos_y_autoridad.sbc` | Acciones, orden de importancia de las categorías y modos de la casa |
| `06_motivos.sbc` | Motivos con su categoría: lo que pasa en la casa, normas de los padres, avisos |
| `10_reglas_generales.sbc` | Herencia de clases, ubicación, familia |
| `11_reglas_decision.sbc` | Permisos de la app, peticiones, modo y conflictos |
| `12_reglas_piscina_jardin.sbc` | Cubierta, depuradora, climatización, riego, cortacésped, luces, Thor con calor |
| `13_reglas_garaje_accesos.sbc` | Llegada del coche, Thor junto a la puerta, cierre nocturno, salidas, cargador |
| `14_reglas_clima.sbc` | Clima por plantas, humedad del sótano, ola de calor, vacaciones |
| `15_reglas_ocio.sbc` | Norma de pantallas y música fuera de madrugada |

## Decisiones de diseño

**Cada acción lleva su motivo.** Las acciones se guardan como
`D <verbo>_por M`: el aparato D hace esa acción por el motivo M. El motivo
puede ser algo que pasa en la casa (`cubierta cerrar_por menor_sin_adulto`),
una norma de los padres (`tele_pablo apagar_por norma_pantallas`) o una
persona que lo pide desde la app (`bomba_piscina encender_por pablo`).

**Todo motivo tiene una categoría, también las personas.** Las categorías
tienen un orden de importancia:

```
seguridad > perro > salud > vecinos > padres > hijo_mayor > hijo_menor > ahorro > confort > mantenimiento
```

Primero, que nadie se haga daño (ni las personas ni Thor) y la salud;
después, no molestar a los vecinos; después, lo que quiere la familia (los
padres por delante de los hijos, y el mayor por delante del pequeño); y por
último lo que la casa hace sola para ahorrar, estar a gusto o mantenerse.
Las normas de los padres son de categoría `padres`: cuentan como algo que
piden ellos.

**Conflictos.** Si dos motivos piden cosas contrarias sobre el mismo aparato
(`conflicto`), gana el de la categoría más importante (`gana`, `pierde`) y se
hace lo que pide (`hace`). Si son de la misma categoría, como Luis y Elena,
no gana ninguno (`empate`) y se avisa a los padres.

**Permisos de la app.** Cada uno puede manejar lo de las zonas comunes y lo
de su cuarto; los padres, también lo del cuarto de Pablo, que es menor. Así
Pablo no puede apagar el aire de su hermano.

**Modos de la casa.** El modo (normal, vacaciones, fiesta, ola de calor)
dice qué reglas se aplican. Solo los padres lo pueden cambiar; si lo pide un
hijo, se les avisa.

- **normal:** el día a día. Rigen las normas de los padres y el clima se
  enciende solo donde hay alguien.
- **vacaciones:** todo lo que gasta mucho se apaga (`casa_vacia`, de
  categoría `padres`: lo decidieron ellos al irse), aunque Pablo lo encienda
  desde la playa.
- **fiesta:** no rigen las normas del día a día.
- **ola de calor:** el aire se enciende por salud donde haya alguien, y no
  se puede apagar.

**El tiempo, por momentos.** El escenario dice el momento del día
(`chalet momento noche`), si es laborable o festivo y la estación. Cada
momento dice qué implica: si es de noche, la tarifa de la luz, si se cierran
los accesos, si Pablo puede usar pantallas, si hay que guardar silencio por
los vecinos...

**Sin negación.** El motor no deduce "no" de que algo no esté escrito. Por
eso los momentos dicen `si` o `no` para cada cosa. La cámara de la piscina
informa directamente de que hay un menor o el perro sin adulto (`detecta
menor_solo`). El cierre nocturno solo actúa sobre lo que un sensor dice que
está abierto (`estado abierta`).

**Clima por plantas.** Cada planta tiene su termostato y solo se climatizan
las estancias donde hay alguien, con el aparato que llega a ellas y sabe
hacerlo: abajo el suelo radiante calienta y los aires enfrían; arriba la
bomba de calor de cada cuarto hace las dos cosas. El sótano no tiene clima;
es fresco, y en una ola de calor se propone bajar allí.

**Limitación conocida.** Cada pareja de motivos se resuelve por separado. Si
sobre un mismo aparato un motivo alto y uno bajo pidieran una cosa y uno
intermedio la contraria, saldrían dos resultados opuestos. Resolverlo
exigiría negación. Las reglas están pensadas para que no ocurra (por
ejemplo, el clima de confort solo funciona en un día normal), y
`D contradiccion si?` lo detectaría: todos los escenarios lo comprueban y
sale vacío.

**Relaciones simétricas escritas en los dos sentidos** (`pareja_de`,
`hermano_de`): una regla simétrica se llamaría a sí misma en bucle con
`razona si!`.

## Escenarios de prueba

Como el motor no permite retirar hechos, cada escenario es un momento fijo;
dentro de él se van añadiendo hechos (una petición, un sensor) y se comprueba
cómo cambia la respuesta. Cada uno tiene su `_expected.jsonl` y su
`_expected.txt`.

| Escenario | Momento y modo | Qué se prueba |
|---|---|---|
| `consultas.sbq` | sin modo | Estructura, clases, familia, zonas comunes, permisos, orden de importancia, categoría de cada motivo |
| `1_tarde_verano` | tarde, normal | Pablo solo en la piscina (la cubierta no se abre y se avisa), cortacésped con Thor en el jardín, aire solo donde hay alguien, ventana abierta, Pablo no puede tocar el cuarto de Sergio |
| `2_noche_invierno` | noche, normal | La norma de pantallas apaga la tele de Sergio porque Pablo está con él, Pablo no puede salir, empate de los padres por la piscina, calefacción por plantas, cierre nocturno |
| `3_llegada_garaje` | anochecer, normal | Thor en el garaje: el portón no se abre ni aunque Luis insista; el cargador en tarifa punta (Luis gana al ahorro) |
| `4_vacaciones` | madrugada, vacaciones | Luis activa el modo; todo lo que gasta se apaga y Pablo no puede encender el aire desde la playa; la depuradora sigue; el riego para con lluvia; Sergio no puede cambiar el modo |
| `5_fiesta` | madrugada, fiesta | Sergio pide la fiesta y Elena la activa; luces fuera, el riego no moja a nadie, sin música de madrugada, sin normas para Pablo |
| `6_ola_de_calor` | tarde, ola de calor | El aire por salud aunque Pablo lo apague, propuesta de bajar al sótano, trampilla abierta para Thor, Elena apaga la tele de Pablo |
| `7_vuelta_de_noche` | madrugada, normal | Sergio entra de madrugada (puede, pero sus padres se enteran), Pablo no puede salir, carga del coche en valle, música fuera prohibida |
