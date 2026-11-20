# Base de conocimiento de Sergio: un chalet familiar

La vivienda es un chalet de tres plantas con parcela. En el sótano hay una
sala de cine y juegos, un gimnasio y el cuarto de máquinas. En la planta baja
están el salón, la cocina, el despacho donde teletrabaja Elena y el garaje.
Arriba están los dormitorios. Fuera hay jardín, piscina y porche. Viven Luis
y Elena (los padres), Sergio (20 años), su hermano pequeño Pablo (12) y
Thor, el perro. Luis tiene un coche eléctrico y Elena uno de gasolina.

Lo que hace distinta a esta casa es que **no hay un orden fijo de
prioridades**. Lo que pesa cada cosa depende del **modo** en que está la casa
(un día normal, vacaciones, una fiesta, una ola de calor), y cuando chocan
dos personas decide la **autoridad**: quién manda en el sitio donde está el
aparato.

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
| `00_chalet.sbc` | Plantas, espacios, de quién es cada dormitorio y el régimen de autoridad de cada sitio |
| `01_clases.sbc` | Taxonomía: espacios, seres vivos, vehículos y dispositivos |
| `02_familia.sbc` | La familia con su rol, Thor (y quién lo cuida), los coches, rutinas |
| `03_momentos.sbc` | Momentos del día: luz, tarifa, cierre nocturno, pantallas, silencio, riego... |
| `04_domotica.sbc` | Dispositivos: qué son, dónde están, qué estancias climatizan, cuáles gastan mucho |
| `05_modos_y_autoridad.sbc` | Acciones, niveles, los cuatro modos y el orden entre roles |
| `06_motivos.sbc` | Objetivos automáticos (con su dominio), normas de los padres (con su autor), avisos |
| `10_reglas_generales.sbc` | Herencia de clases, ubicación, familia |
| `11_reglas_decision.sbc` | Peticiones y permisos, modo, nivel de cada motivo, autoridad, resultado |
| `12_reglas_piscina_jardin.sbc` | Cubierta, depuradora, climatización, riego, cortacésped, luces, Thor con calor |
| `13_reglas_garaje_accesos.sbc` | Llegada del coche, Thor junto a la puerta, cierre nocturno, salidas, cargador |
| `14_reglas_clima.sbc` | Clima por plantas, humedad del sótano, ola de calor, vacaciones |
| `15_reglas_ocio.sbc` | Norma de pantallas y música fuera de madrugada |

## Decisiones de diseño

**Tres tipos de motivo.** Cada acción se guarda como `D <verbo>_por M`
(`cubierta cerrar_por menor_sin_adulto`), y el motivo puede ser:

- una **persona** que lo pide desde la app (`bomba_piscina encender_por pablo`);
- una **norma** que ha puesto uno de los padres (`norma_pantallas autor elena`);
- un **objetivo automático** de la casa, que pertenece a un dominio
  (seguridad, bienestar de Thor, salud, vecinos, ahorro, confort,
  mantenimiento).

**Los modos deciden qué es negociable.** En cada modo, cada dominio es
innegociable (pasa por encima de lo que pida cualquiera), preferente o
secundario (ceden ante la familia), o directamente no cuenta. Las personas y
las normas quedan en medio:

```
innegociable > voluntad (personas y normas) > preferente > secundario
```

| Modo | Innegociable | Preferente | Secundario | Normas |
|---|---|---|---|---|
| normal | seguridad, Thor, vecinos | ahorro, confort | mantenimiento | rigen |
| vacaciones | seguridad, Thor, vecinos, **ahorro** | mantenimiento | — | no |
| fiesta | seguridad, Thor, vecinos | confort | mantenimiento | no |
| ola de calor | seguridad, Thor, vecinos, **salud** | — | ahorro, mantenimiento | rigen |

Así, el mismo aire acondicionado se enciende si Pablo lo pide en un día
normal, no se enciende aunque lo pida de vacaciones (el ahorro es
innegociable) y no se apaga aunque lo pida en una ola de calor (la salud es
innegociable). El modo solo lo pueden cambiar los padres; si lo pide un hijo,
se les avisa.

**La autoridad depende del sitio.** Cuando chocan dos voluntades, decide el
régimen del sitio donde está el aparato:

- **Zona común** (salón, garaje, jardín, piscina, sótano...): padres > hijo
  mayor > hijo pequeño.
- **Cuarto de un mayor de edad** (Sergio): manda él, también frente a las
  normas de sus padres. Nadie más puede tocar nada de ahí desde la app.
- **Cuarto de un menor** (Pablo): mandan los padres.

Una norma vale lo que vale su autor: la norma de Luis gana a Pablo en el
recibidor, pero pierde frente a Sergio en el cuarto de Sergio. Quien pone una
norma puede saltársela. Si Luis y Elena piden cosas contrarias, no gana
ninguno: hay `desacuerdo` y se avisa a los dos.

**Explicabilidad.** Cada decisión se puede preguntar: qué motivos chocan
(`D disputa M`), cuál gana y cuál no (`D se_queda_con M`, `D descarta M`),
con qué peso (`M nivel N`, y cada nivel tiene un `nombre`) y, si fue por
autoridad, quién mandaba (`D manda P`). Todos los motivos, modos, niveles y
regímenes tienen su `nombre` en castellano.

**Permisos de la app.** Cada uno solo puede pedir cosas de las zonas comunes
y de su cuarto (los padres, también del de Pablo). Así Pablo no puede apagar
el aire de su hermano.

**El tiempo, por momentos.** El escenario dice el momento del día
(`chalet momento noche`), si es laborable o festivo y la estación. Cada
momento dice explícitamente qué implica: si es de noche, la tarifa de la luz,
si se cierran los accesos, si Pablo puede usar pantallas, si hay que guardar
silencio por los vecinos...

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
exigiría negación. Las reglas y los modos están pensados para que no ocurra
(por ejemplo, en una ola de calor el clima lo lleva la salud y el confort no
cuenta), y `D contradiccion si?` lo detectaría: todos los escenarios lo
comprueban y sale vacío.

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
| `consultas.sbq` | sin modo | Estructura, clases, familia, regímenes, permisos, qué impone cada modo; sin modo solo las personas tienen nivel |
| `1_tarde_verano` | tarde, normal | Pablo solo en la piscina (la cubierta no se abre y se avisa), cortacésped con Thor en el jardín, aire solo donde hay alguien, ventana abierta, Pablo no puede tocar el cuarto de Sergio |
| `2_noche_invierno` | noche, normal | Norma de pantallas frente a Sergio en su cuarto (gana él), norma de salidas en el recibidor (gana Luis), desacuerdo de los padres por la piscina, calefacción por plantas, cierre nocturno |
| `3_llegada_garaje` | anochecer, normal | Thor en el garaje: el portón no se abre ni aunque Luis insista; el cargador en tarifa punta (gana Luis frente al ahorro); Luis se salta su propia norma |
| `4_vacaciones` | madrugada, vacaciones | Luis activa el modo; todo lo que gasta se apaga y Pablo no puede encender el aire desde la playa; la depuradora sigue; el riego para con lluvia; Sergio no puede cambiar el modo |
| `5_fiesta` | madrugada, fiesta | Sergio pide la fiesta y Elena la activa; luces fuera, el riego no moja a nadie, sin música de madrugada, sin normas para Pablo |
| `6_ola_de_calor` | tarde, ola de calor | El aire por salud aunque Pablo lo apague, propuesta de bajar al sótano, trampilla abierta para Thor, Elena manda en el cuarto de Pablo |
| `7_vuelta_de_noche` | madrugada, normal | Sergio entra de madrugada (puede, pero sus padres se enteran), Pablo no puede salir, carga del coche en valle, música fuera prohibida |
