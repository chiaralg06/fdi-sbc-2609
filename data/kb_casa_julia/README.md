# Casa de Julia — base de conocimiento de un colegio mayor

KB individual de SBC. Modela mi colegio mayor (solo chicas, ~200 alumnas) y su "domótica": quién puede entrar, subir o quedarse, cuándo está abierto cada servicio, reservas de salas, lavandería, clima, ascensores, incendio y avisos al personal. Cuando dos objetivos chocan (música vs. examen de la vecina, aire acondicionado vs. cierre del colegio, visita vs. hora límite de chicos...) decide el motor, no yo, y puede explicar por qué.

```
uv run -m sbc data/kb_casa_julia data/kb_casa_julia/escenarios/3_visitas.sbq     # un escenario
uv run -m sbc data/kb_casa_julia data/kb_casa_julia/consultas.sbq                # consultas estáticas
uv run -m sbc data/kb_casa_julia data/kb_casa_julia/explicacion.sbq              # traza (stderr)
uv run -m sbc --jsonl data/kb_casa_julia data/kb_casa_julia/escenarios/6_incendio.sbq | diff - data/kb_casa_julia/escenarios/6_incendio_expected.jsonl
python3 data/kb_casa_julia/generar.py     # regenera 02_habitaciones, 04_tiempo, 05_tablas
```

## Cómo está organizada

| Ficheros | Contenido |
|---|---|
| `00_edificio` | Colegio, 3 pabellones (A, B, C), planta calle con zonas comunes, sótano con lavandería, 3 ascensores, cámaras, accesos |
| `01_clases` | Jerarquía de clases (zonas, aparatos, parentescos, periodos) y hechos **de clase** (p. ej. toda habitación contiene cama, armario...) |
| `02_habitaciones` | *(generado)* 12 plantas, 240 habitaciones con calefacción/aire, alarma, sala de planta con papel, basura y ropa |
| `03_personas` | Alumnas ficticias (Lucía, Irene, Paula, Carmen, Elena), visitantes, personal |
| `04_tiempo`, `05_tablas` | *(generado)* tramos de media hora, orden entre ellos, tablas de saldo y de "mayor que" |
| `06_servicios`, `07_motivos` | Horarios de comedor/gimnasio; verbos, opuestos, categorías de prioridad y ~40 motivos con nombre |
| `10`–`17` | Reglas por tema: edificio, tiempo, entrada, visitas, estudio, lavandería, recursos, clima/incendio |
| `18_reglas_decision` | El corazón del razonamiento contextual: resolución de conflictos |

## Decisiones de diseño (por criterio)

**Amplitud.** Cubre todo lo que hay en el colegio: pabellones, plantas, 240 habitaciones, zonas comunes, personal (limpiadoras, cocineras, dirección, monjas, recepción, monitoras), visitas, estudio, comida, ropa, clima, seguridad.

**Profundidad.** Habitación → planta → pabellón → colegio (`dentro_de`); habitación → muebles y aparatos; cada aparato con su coste/estado; el tiempo en tramos de media hora; periodos del año con su facturación (curso por mes, junio por día; Navidad, Semana Santa y verano = cerrado).

**Razonamiento contextual.** Cada situación (llegada tardía, visita de un chico a las 23:00, sobreaforo, incendio...) produce una *medida* con el patrón `sujeto verbo_por motivo` (`v2 denegar_por hora_chicos`) y cada motivo tiene una **categoría** con prioridad (`vida > cierre/norma > recurso > estudio > servicio > confort > ahorro`). Si hay acciones opuestas (permitir/denegar, encender/apagar...), `se_impone` elige la de categoría más alta. Ejemplos: la visita en cafetería está permitida (`zona_visitas`) pero a las 23:00 un chico no familiar la pierde (`hora_chicos`, norma > servicio); durante Navidad se apaga la calefacción aunque la alumna la pida (`cierre_colegio`); en un incendio los ascensores se bloquean.

**Generalidad.** Las reglas hablan de *clases*, no de casos: añadir una alumna, una habitación o una limpiadora nueva se hace solo con hechos (en el escenario 7 aparece una `limpiadora_extra` y recibe los avisos sin tocar reglas). La 240 habitaciones se generan con `generar.py`.

**Explicabilidad.** Toda notificación lleva `provocado_por` (qué la causó) y todo motivo tiene `nombre` y `origen`. Además `explica si!` da la traza de prueba completa (`explicacion_traza.txt`: por qué se deniega la visita de Marcos a las 23:00, con cada regla y hecho).

**Corrección.** 10 escenarios + consultas con resultados esperados (`*_expected.txt` y `.jsonl`), revisados a mano. Razonar hacia delante (`descubre!`) y hacia atrás (`razona si!`) dan **las mismas respuestas** (comprobado en los escenarios 1, 7 y 9; `descubre!` tarda ~30 s con las 240 habitaciones). Cada escenario termina comprobando que no hay `empate` ni `decision_dudosa`.

**Extensiones.** Vales de salida, límite distinto por alumna (`limite_finde` fijado por los padres), reglas distintas por parentesco (madre/padre/hermana sí; hermano solo con progenitores; amigos/amigas solo en zonas de visita), cola de lavadoras con derivación a una libre, tarjeta de 20 círculos con saldo, aviso a dirección o a los padres, derivación de comida a cafetería y de música a la sala de música.

## Límites del motor y cómo se resolvieron

| Límite | Solución |
|---|---|
| No hay negación | Marcadores positivos: `acompanado_por nadie`, `con_reserva ninguna`, `M estado libre` |
| No hay aritmética ni comparación | Tablas generadas: `n13 menos_2 n11`, `k5 mayor_que k4`, `T posterior_a U` |
| No se pueden retirar hechos | Escenarios con un solo periodo; un periodo nuevo se prueba en otro escenario |
| Sin acentos fuera de comillas | Nombres ASCII; los textos con acento van entre comillas (`nombre "Recepcionista de día"`) |
| Variable en la cabeza de una regla = recursión infinita | Predicado variable solo en el cuerpo (costes de lavadora) |
| La clase de un sitio único no puede llamarse como el sitio | `cafeteria es_un sala_cafeteria` (evita bucle de `contiene`) |

## Supuestos (no sabía el dato real)

- Planta calle = común; 4 plantas residenciales por pabellón; cada una con su sala (papel, basura, ropa).
- Un festivo se trata como domingo (sin cena). Reglas de "día" de una llegada: el día en que empieza la noche.
- Protocolo de incendio: se bloquean ascensores y se avisa a dirección y recepción; la alarma real nunca la he visto sonar.
- Si una alumna de primero llega tarde sin vale: aviso a dirección y a los padres; el vale se puede firmar al llegar.
- Nombres de alumnas y visitantes ficticios (no uso datos de personas reales).

## Limitación conocida

`decision` solo resuelve conflictos por pares de acciones opuestas. Con tres acciones enfrentadas a la vez, `empate`/`decision_dudosa` lo marcan en vez de adivinar.

## Escenarios

| # | Fichero | Qué prueba |
|---|---|---|
| 1 | `1_entrada_martes` | Martes de noche: cuatro alumnas de distinto curso y vale, y una quinta sin vale |
| 2 | `2_finde_hora_padres` | Vie–dom: hora fijada por los padres (Lucía 1:00, Irene 23:30), domingo a medianoche, vales de salida |
| 3 | `3_visitas` | Visitas de familia, hermano, amigas y amigos de Lucía |
| 4 | `4_estudio_y_musica` | Reservas (aforo, doble reserva), comida en biblioteca, ruido, música vs. examen |
| 5 | `5_lavanderia` | Tarjeta de 20 círculos, coste por máquina, saldo con tablas, máquina ocupada |
| 6 | `6_incendio` | Alarma en planta 1 del pabellón A con peticiones de clima, y otra en planta calle |
| 7 | `7_recursos_plantas` | Papel/basura/ropa → limpiadora del pabellón |
| 8 | `8_cierre_navidad` | Colegio cerrado: clima, visitas, servicios |
| 9 | `9_junio_domingo` | Domingo de junio: cobro por día, sin cena, hora límite de primero |
| 10 | `10_sabado_noche` | Cena de sábado y hora límite de chicos |
