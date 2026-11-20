# Base de conocimiento de Juan: un colegio mayor

La vivienda es el colegio mayor donde vivo: planta baja con todos los
servicios (recepción, comedor, cafetería, gimnasio, pistas, lavandería y sala
de estudio), una entreplanta de ocio (sala de juegos y sala de televisión) y
siete plantas de habitaciones. Comparto la habitación doble 514 con mi primo
Nico, y en el colegio vive y trabaja mucha más gente.

A diferencia de una casa familiar, aquí la domótica tiene que conciliar a
muchas personas que no se conocen tanto: compañeros de habitación con
horarios distintos, servicios con horario, normas del colegio (silencio
nocturno, corte del aire, visitas) y personal con turnos.

## Cómo se usa

```
uv run -m sbc data/kb_casa_juan data/kb_casa_juan/consultas.sbq
uv run -m sbc data/kb_casa_juan data/kb_casa_juan/escenarios/1_examen_madrugon.sbq
```

Los escenarios activan `razona si!`. También funcionan con `descubre!`
(hacia delante) en lugar de `razona si!`.

## Organización

| Fichero | Contenido |
|---|---|
| `00_colegio.sbc` | Plantas y espacios, con su clase y su planta |
| `01_clases.sbc` | Taxonomía: espacios, personas, objetos y dispositivos |
| `02_personas.sbc` | Colegiales, personal con turnos, familias y amigos, rutinas |
| `03_horario.sbc` | Franjas del día, horario diurno/nocturno, horarios, silencio, corte del aire, visitas, turnos |
| `04_domotica.sbc` | Dispositivos: qué son, dónde están y de quién son |
| `05_motivos.sbc` | Acciones, motivos, prioridades fijas y las que cambian de día a noche |
| `10_reglas_generales.sbc` | Herencia de clases, ubicación, parentesco, prioridades |
| `11_reglas_horario.sbc` | De la hora a la franja y todo lo que depende de ella |
| `12_reglas_situaciones.sbc` | Situaciones, permisos de la app y resolución de conflictos |
| `13_reglas_habitacion.sbc` | Descanso, despertar, estudio y clima en las habitaciones |
| `14_reglas_zonas_comunes.sbc` | Pasillos, salas, exámenes, silencio, lavandería, entrada |
| `15_reglas_servicios.sbc` | Comedor y cafetería, visitas, recepción y limpieza |

## Decisiones de diseño

**Hechos separados de reglas, y reglas sobre clases.** Los ficheros `0X_`
solo dicen qué hay; los `1X_` deciden qué hacer. Las reglas nunca nombran un
dispositivo o una habitación concretos: trabajan con clases (`luz_techo`,
`zona_ocio`, `habitacion`...). Por eso la habitación 515 funciona igual que
la 514 sin escribir ninguna regla para ella, y añadir una habitación, una
sala o un dispositivo solo pide escribir sus hechos.

**Lo personal y lo compartido.** En una habitación doble, cada dispositivo es
`pertenece_a` una persona (la luz de su cama) o de `uso compartido` (la luz
del techo, la persiana, el aire). Lo compartido respeta al que duerme; lo
personal es de cada uno. Así Juan puede estudiar o levantarse con su luz sin
despertar a Nico, y Nico no puede encender la luz de Juan desde la app.

**El tiempo, por franjas.** El motor no compara horas, así que cada media
hora dice en qué franja cae (madrugada, desayuno, media mañana, comida,
tarde, cena, noche). El escenario solo da la hora (`colegio hora h0030`) y se
deduce la franja, y de ella qué está abierto, si hay silencio, si se corta
el aire, si las visitas pueden subir y quién está de turno.

**Sin negación.** El motor no puede deducir "cerrado" de "no abierto". Por eso
cada franja dice explícitamente `si` o `no` para cada propiedad, y el comedor
dice en qué franjas abre y en cuáles cierra. Así se puede proponer la
cafetería solo cuando el comedor está cerrado, o encender el aire por calor
solo fuera del corte nocturno.

**Cada conclusión lleva su motivo.** Las acciones se guardan como
`D <verbo>_por M` (`luz_techo_514 apagar_por alguien_durmiendo`), y cada
motivo tiene un `nombre` en castellano. Cualquier conclusión se explica
preguntando por su motivo (`D encender_por M, M nombre N?`).

**Conflictos por prioridad, y la prioridad depende de la hora.** Cada motivo
es de una categoría. Si dos motivos piden acciones opuestas sobre lo mismo
(`conflicto`), gana el de categoría más alta (`gana`, `pierde`, `resultado`).
Pero en un colegio mayor no tiene sentido un orden fijo: lo que importa a
las 00:30 no es lo que importa a las 16:00. Por eso el descanso cambia de
sitio según el horario:

```
noche (22:30-07:30): seguridad > descanso > estudio > peticion > norma_colegio > rutina > confort > ahorro > aviso
día   (07:30-22:30): seguridad > estudio > peticion > descanso > norma_colegio > rutina > confort > ahorro > aviso
```

La parte fija se escribe con `por_encima_de`. Los escalones que solo valen
en un horario son hechos con nombre (`noche_descanso_estudio arriba
descanso`, `abajo estudio`, `nombre "De noche, dormir va antes que
estudiar"`), y una regla los activa según la hora del escenario:

```
C1 por_encima_de C2 <- colegio periodo P, P escalon E, E arriba C1, E abajo C2.
```

Así se puede preguntar por qué manda una cosa u otra en cada momento
(`colegio periodo P, P escalon E, E nombre N?`), y añadir otro contexto
(por ejemplo, fines de semana) solo pide escribir sus escalones. Sin hora, el
descanso no tiene sitio en el orden. Algunas decisiones:

- De noche el descanso va por delante del estudio: el que estudia tiene su
  luz personal y la sala de estudio, abierta las 24 horas, y la app se la
  propone. De día es al revés: una siesta no deja a oscuras al compañero que
  estudia, ni le impide subir la persiana desde la app (escenarios 2 y 8:
  misma situación, resultado contrario).
- Aun de día, el descanso va por delante de normas y rutinas: la limpieza
  espera.
- Lo que se pide desde la app se cumple salvo que moleste al estudio o, de
  noche, al descanso.
- El corte nocturno del aire es una norma de ahorro del colegio, y el propio
  colegio deja encenderlo desde el móvil: una petición la anula. El calor,
  en cambio, no lo vuelve a encender de madrugada.
- La limpieza programada espera si en la habitación alguien duerme o estudia.

**Limitación conocida.** Cada pareja de motivos se resuelve por separado. Si
sobre lo mismo un motivo alto y uno bajo pidieran una acción y uno intermedio
la contraria, saldrían dos resultados opuestos. Resolverlo exigiría negación.
Las reglas están escritas para que no ocurra, y `D resultado_dudoso si?` lo
detectaría: todos los escenarios lo comprueban y sale vacío.

**Relaciones simétricas escritas en los dos sentidos** (`primo_de`): una regla
simétrica se llamaría a sí misma en bucle con `razona si!`. Todas las reglas
recursivas (clases, prioridades, plantas) bajan por estructuras sin ciclos.

## Escenarios de prueba

Como el motor no permite retirar hechos, cada escenario es un momento fijo
del día; dentro de él se van añadiendo hechos (una petición, un sensor) y se
comprueba cómo cambia la respuesta. Cada uno tiene su `_expected.jsonl` y su
`_expected.txt`.

| Escenario | Hora | Qué se prueba |
|---|---|---|
| `consultas.sbq` | sin hora | Estructura, herencia, ubicaciones, parentesco, permisos, prioridades fijas (el descanso sin sitio); sin razonar, nada deducido |
| `1_examen_madrugon` | 07:00, invierno | Juan madruga para un examen y Nico duerme: su luz sí, la persiana no (ni pidiéndolo); calientatoallas, calefacción, pasillo tenue, comedor aún cerrado → cafetería |
| `2_estudio_nocturno` | 00:30 | Juan estudia y Nico duerme: la luz del techo se queda apagada aunque la pida; aviso y propuesta de sala de estudio; Nico no controla la luz de Juan |
| `3_examenes_ocio` | 17:00, exámenes | Música apagada aunque se pida, tele con volumen bajo, sala de estudio iluminada aunque esté vacía, gimnasio vacío apagado |
| `4_noche_verano` | 01:00, verano | Hora de acostarse, corte del aire (el calor no lo enciende, la app sí), tele en silencio nocturno, pistas cerradas, gimnasio 24 h |
| `5_gimnasio_cena` | 23:00 | Gimnasio con luz y aire, cena terminada → cafetería, lavadora pagada con el móvil y aviso al terminar, entrada con la app, recepción de turno |
| `6_visitas` | 12:00 | La madre de Juan sube, el amigo de Nico espera abajo, avisos a recepción, limpieza que espera donde alguien estudia o duerme |
| `7_cena_invierno` | 21:00, invierno | Comedor abierto (no se propone la cafetería), un familiar que ya no puede subir, persiana desde la app, calefacción automática |
| `8_siesta` | 16:00 | Lo mismo que el escenario 2 pero de día: Nico duerme la siesta y Juan estudia. Orden de día, la luz del techo se enciende, la persiana sube desde la app, sin aviso ni sala de estudio |
