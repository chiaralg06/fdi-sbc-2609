# Base de conocimiento: la domótica de mi casa

Chiara · 23 de noviembre de 2026

## Enfoque

La base representa mi casa real (11 estancias, mis padres, yo y mi gato Miko) y la domótica que decide cómo debe comportarse en cada momento. Hay una Alexa en el salón y un Echo en dos dormitorios, luces, persianas, clima, cerradura, cámara, sensores, electrodomésticos con wifi y los aparatos de Miko.

La base no guarda el estado de la casa. Cada escenario lo cuenta con hechos como `casa modo noche`, `padre estado dormido` o `sensor_lluvia detecta lluvia`, y las reglas razonan en cuatro pasos:

1. Situaciones: qué significan los datos según el contexto. Abrir la puerta es una intrusión solo si no hay nadie en casa y se abre sin código.
2. Acciones con motivo: qué hace cada dispositivo y por qué, siempre juntos, por ejemplo `luz_pasillo encender_por paso_nocturno`.
3. Conflictos: si dos motivos piden acciones opuestas sobre el mismo dispositivo, gana el de la categoría más importante.
4. Origen: cada motivo se puede seguir hasta el sensor, la persona o el aparato que lo provocó.

Las categorías de motivos, de más a menos importante, son: riesgo de explosión, emergencia, seguridad, bienestar de la mascota, protección de la casa, descanso, peticiones a la Alexa, confort y ahorro.

## Organización de la base

La base tiene 14 ficheros en `data/kb_casa_chiara`: siete de hechos (00 a 06), que dicen qué hay y dónde, y siete de reglas (10 a 16), con 114 reglas en total. El motor los carga por orden alfabético.

| Fichero | Contenido |
| --- | --- |
| `00_casa.sbc` | Estancias, su tipo (dormitorio, zona común, cuarto húmedo, exterior) y las puertas entre ellas |
| `01_clases.sbc` | Taxonomía de estancias, objetos, habitantes y dispositivos, y qué clases pueden hacer chispa |
| `02_objetos.sbc` | Muebles, electrodomésticos y objetos, y dónde está cada uno |
| `03_personas.sbc` | La familia, Miko, dónde duerme cada uno y las tareas de casa |
| `04_domotica.sbc` | Asistentes de voz, dispositivos controlables, sensores y la tarea que tiene que ver con cada aparato |
| `05_motivos.sbc` | Acciones y cuáles son opuestas, motivos, categorías con su prioridad y qué lectura de sensor da cada motivo |
| `06_energia.sbc` | Aparatos de alto consumo y su orden de importancia |
| `10_reglas_casa.sbc` | Conexiones entre estancias, en qué estancia está cada cosa y herencia de tipos (8 reglas) |
| `11_reglas_familia.sbc` | Progenitores e hijos (3 reglas) |
| `12_reglas_domotica.sbc` | Qué controla cada asistente, modos de la casa, situaciones, origen de cada motivo y resolución de conflictos (33 reglas) |
| `13_reglas_acciones.sbc` | Qué hace cada tipo de dispositivo en cada situación, por categoría (53 reglas) |
| `14_reglas_ordenes.sbc` | Órdenes a la Alexa (8 reglas) |
| `15_reglas_energia.sbc` | Plomos: sobrecarga y qué se corta (5 reglas) |
| `16_reglas_tareas.sbc` | Avisos a quien tiene cada tarea (4 reglas) |

Las pruebas están en `consultas.sbq` (consultas generales sobre la casa) y en la carpeta `escenarios`, cada una con sus resultados esperados en texto y en JSONL.

## Decisiones de diseño

Las decisiones se agrupan según el criterio de evaluación al que responden.

### Amplitud

La casa cubre nueve aspectos que se cruzan entre sí: estancias y objetos, familia y tareas, Miko, iluminación y persianas, clima, seguridad (puerta, cámara, gas, humo), agua (fugas y riego), consumo eléctrico y órdenes a la Alexa. Ninguno funciona aislado: Miko cambia lo que hacen la calefacción y el robot, el gas bloquea las órdenes a la Alexa y la lluvia cambia cómo se avisa de que ha terminado la lavadora.

### Profundidad

Casi todo lo que la base responde no está escrito. Algunos ejemplos:

- En qué estancia está algo aunque esté dentro de un mueble: el portátil está en el escritorio, que está en mi habitación.
- Qué controla cada asistente: todo lo controlable de su estancia, y lo enchufado a un enchufe que controla (el deco de Movistar).
- A quién avisar cuando termina la lavadora: se cruza qué tarea tiene que ver con el aparato con quién tiene esa tarea, y si llueve el aviso es tender dentro.
- Qué cortar antes de que salten los plomos: se cuentan los aparatos activos, contando también los que la casa ha decidido encender (el aire por el calor), y se corta el menos importante.

### Razonamiento contextual

Un mismo dato significa cosas distintas según el contexto. Abrir la puerta es normal con gente en casa, es una visita si se abre con código sin nadie (la cuidadora de Miko) y una intrusión si se abre sin código. El movimiento en el pasillo solo importa de noche.

El contexto lo dan el modo de la casa (noche, fuera, vacaciones), que también se deduce de órdenes como "buenas noches" o "me voy"; la estación y la hora; dónde está cada uno y quién está dormido. "Fuera" y "vacaciones" comparten la idea de casa ausente, así que el ahorro, el cierre y el cuidado de Miko valen para los dos.

Los objetivos enfrentados se resuelven con las categorías de prioridad. Por ejemplo, si salimos con Miko en casa, el ahorro pide apagar la calefacción y el bienestar de Miko pide mantenerla, y gana Miko.

### Generalidad

Ninguna regla nombra un dispositivo, una estancia o una persona concretos: todas trabajan con tipos (`L tipo luz_inteligente`, `E tipo zona_comun`). Añadir una luz, una habitación o un invitado solo pide escribir sus hechos, y las reglas se aplican solas. En el escenario de noche llega una invitada a la habitación de invitados y su persiana pasa a bajarse sin tocar ninguna regla.

Lo mismo vale para las propiedades de una clase: qué clases pueden hacer chispa o qué acciones son opuestas se escribe una vez y vale para todo lo que entre en ellas. Cada estancia tiene su tipo, cada puerta se escribe una sola vez y la jerarquía de prioridades se escribe por escalones (la regla `prevalece_sobre` deduce el orden completo).

### Explicabilidad

Cada acción lleva su motivo pegado en el propio predicado (`persiana_salon bajar_por modo_pelicula`), cada motivo tiene un nombre legible y la relación `origen` lo une con el sensor, la persona o el aparato que lo provocó. Así una sola consulta da la explicación completa:

```
cerradura se_impone M, M nombre NM, M origen S, S nombre NS?
```

En el escenario de noche responde que la puerta se abre de madrugada porque hay humo, y que el humo lo ha detectado el detector de la cocina. Con `conflicto` y `se_impone` se ve también qué motivo ha perdido y frente a cuál.

### Corrección

Los nueve escenarios se han revisado a mano consulta por consulta, y sus resultados están guardados como esperados. Cada escenario da exactamente las mismas respuestas razonando hacia atrás y hacia delante. Las reglas recursivas (ubicación, tipos, prioridades) recorren relaciones sin ciclos, así que terminan con los dos modos.

### Extensiones

La base usa el encadenamiento hacia atrás (`razona si!`) y hacia delante (`descubre!`). También aprovecha que el motor admite variables en el predicado: las reglas generales de acciones y conflictos (`D accion A <- V verbo A, D V M`) funcionan para cualquier acción, presente o futura, sin una regla por cada verbo.

## Limitaciones del motor y cómo se han resuelto

Varias decisiones de la base vienen de lo que el motor no permite. Estas son las limitaciones, cómo se han resuelto y lo que queda pendiente.

| Limitación | Solución en la base |
| --- | --- |
| No hay negación: no se puede escribir "si no hay nadie" ni "salvo que llueva" | El contexto se afirma en positivo (`casa modo fuera`, `cerradura detecta sin_codigo`) y los objetivos enfrentados se resuelven con prioridades, no con excepciones |
| No se puede decir "X distinto de Y" | Una regla "hermanos si comparten padres" diría que cada uno es hermano de sí mismo, así que esas relaciones se escriben como hechos. Para contar tres aparatos encendidos se usa su orden de importancia: si X está por encima de Y e Y por encima de Z, los tres son distintos a la fuerza |
| Con `razona si!`, una regla que se llama a sí misma en círculo no termina | Las relaciones simétricas usan dos predicados: cada puerta se escribe una vez con `acceso_a` y se deduce `conecta_con` en los dos sentidos. Las reglas recursivas solo recorren relaciones sin ciclos |
| Los hechos no se pueden retirar | Cada escenario es una situación que avanza añadiendo información. No se afirma `casa modo normal`, porque al pasar a modo noche la casa estaría en los dos |
| Razonar hacia atrás repite mucho trabajo | La regla de `tipo` baja por la jerarquía desde la clase, `en_estancia` reconoce las estancias por `parte_de casa` y las reglas comprueban primero las condiciones baratas. Los escenarios pasaron de más de cuatro minutos a menos de 20 segundos |

Queda un caso sin resolver. Si en un mismo dispositivo chocan tres motivos de tres categorías, cada pareja se resuelve por separado y pueden salir dos decisiones opuestas. Pasa, por ejemplo, con Miko solo en casa y humo: Miko gana al ahorro y pide encender la calefacción, y el humo gana a Miko y pide apagarla. Quedarse solo con la más fuerte exige negación. La regla `decision_dudosa` detecta el caso, y en él vale la decisión de categoría más alta. Ninguno de los nueve escenarios lo produce.

## Escenarios de prueba

Hay nueve escenarios en la carpeta `escenarios`. Cada uno empieza con `razona si!`, describe una situación y le va añadiendo información nueva, con consultas después de cada cambio para ver cómo reacciona la casa.

| Escenario | Qué pasa | Conflictos y quién gana |
| --- | --- | --- |
| `1_fuera_invierno` | Salimos con "Alexa, me voy" y Miko se queda. Luego alguien abre la puerta sin código | Calefacción: Miko gana al ahorro. Robot: Miko gana a limpiar. Luces: la intrusión gana al ahorro |
| `2_noche` | Todos duermen. Miko usa el arenero, alguien se levanta, llega una invitada y salta el detector de humo de la cocina | Arenero: el descanso gana a la limpieza. Luz del pasillo: el paso nocturno gana al descanso. Con el humo, la emergencia gana al descanso en luces, persianas, avisos y cerradura |
| `3_tormenta_verano` | Calor con ropa tendida, llega una tormenta, alguien se ducha y se ponen la lavadora y el lavavajillas | Toldo y riego: la lluvia gana al calor. Con el aire, la lavadora y el lavavajillas se corta el lavavajillas |
| `4_cena_plomos` | Se van encendiendo vitro, horno, lavavajillas, lavadora y airfryer | Se cortan los dos menos importantes. La airfryer no tiene wifi y solo se avisa |
| `5_amanecer` | Mi padre sigue dormido. Mi madre y yo decimos "buenos días" desde nuestras habitaciones, y Miko desayuna y usa el arenero | Persiana de mis padres: el descanso gana a la orden. La mía sube sin conflicto |
| `6_tarde_salon` | Modo película, "aspira", dar de comer a Miko desde la cocina (sin asistente) y desde el salón, y "buenas noches" | Robot: Miko gana a la orden. Tele y deco: el descanso gana a la película |
| `7_fuga_gas` | Fuga de gas junto al calentador con todos en casa. Luego llueve y pido una película | Ventanal: la fuga gana a la lluvia. Tele y luz: la fuga bloquea la orden |
| `8_dia_de_colada` | Terminan la lavadora y el lavavajillas, se llenan el cubo y el arenero, se vacía el comedero, llueve y hay agua en la cocina | Cada aviso le llega a quien tiene la tarea. Riego: la fuga y la lluvia piden lo mismo |
| `9_vacaciones` | Vacaciones en verano con Miko en casa. Entra la cuidadora con código, anochece y luego alguien abre sin código y llueve | Luces: la visita y la simulación de presencia ganan al ahorro. Riego: la lluvia gana al calor |

Además, `consultas.sbq` prueba la parte estática de la casa: ubicaciones, conexiones, tipos, familia, qué controla cada asistente y el orden de prioridades. Lo hace primero sin razonar, después con `razona si!` y al final otra vez sin razonar, para que se vea qué aporta cada modo.

Cada escenario termina comprobando con `D decision_dudosa si?` que ningún dispositivo ha quedado con decisiones contradictorias.

## Cómo ejecutar y comprobar

Desde la carpeta raíz del proyecto, un escenario se ejecuta así (con `--jsonl` se ven también las soluciones de cada consulta):

```
uv run -m sbc data/kb_casa_chiara data/kb_casa_chiara/escenarios/2_noche.sbq
uv run -m sbc --jsonl data/kb_casa_chiara data/kb_casa_chiara/escenarios/2_noche.sbq
```

Los resultados esperados de cada escenario están junto a él, en `<escenario>_expected.txt` y `<escenario>_expected.jsonl`; los de las consultas generales, en `expected.txt` y `expected.jsonl`. En Linux se comparan con:

```
diff --strip-trailing-cr <(uv run -m sbc data/kb_casa_chiara data/kb_casa_chiara/escenarios/2_noche.sbq 2>/dev/null) data/kb_casa_chiara/escenarios/2_noche_expected.txt
```

Si no imprime nada, coinciden.

Con `razona si!` cada escenario tarda entre 3 y 20 segundos. Cambiando `razona si!` por un `descubre!` después de cada bloque de hechos, tardan entre 2 y 6 segundos y dan exactamente las mismas respuestas.
