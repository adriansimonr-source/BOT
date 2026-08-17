# SB Automation Suite - documento canónico

Estado operativo consolidado del 17 de agosto de 2026. Este archivo reúne el contexto del proyecto, el contrato funcional, la arquitectura, las dependencias, la ejecución, la compatibilidad y los criterios de continuidad. Es la única documentación técnica normativa; `README.md` es solo la portada del repositorio y `requirements.txt` es el manifiesto instalable.

## Propósito y fases

Suite modular para automatizar acciones de juegos mediante captura visual, OCR e input dirigido a una ventana en segundo plano. Kathana, basado en DX11, es la referencia actual, pero las capas deben permitir nuevos perfiles.

El proyecto es deliberadamente no intrusivo:

- No lee memoria del juego ni inyecta DLL, hooks o modificaciones en el cliente.
- No depende del foco del teclado.
- Todo el estado procede de visión o configuración.
- Toda tecla pasa por `InputManager` y se entrega al `HWND` seleccionado.

| Fase | Estado |
| --- | --- |
| GUI genérica | Estable y funcional. Mantener diseño y distribución salvo petición expresa. |
| Captura, visión e input de fondo | Flujo general validado en una prueba real de Kathana sobre Windows 10; el regreso al origen sigue siendo la función menos fiable. |
| Persistencia | Operativa para juegos, configuración, enemigos, ignorados, items y aprendizaje de navegación. |
| Build y multiplataforma | Build portable Windows 10 x64 v1.1.1 generada y validada; Windows 11, instalador firmado y Ubuntu siguen pendientes. |

## Arquitectura

```text
MainWindow (Qt, siempre visible salvo minimización)
  |-- ProcessManager / GameProfileManager
  |-- EntityDatabaseManager
  |-- BotWorker (QThread, reloj de automatización de 25 ms)
  |     `-- BotEngine -> GameStateManager(snapshot) -> módulos -> InputManager
  `-- bot-vision (hilo Python exclusivo)
        `-- VisionManager -> WGC/D3D11/OCR -> VisionSnapshot inmutable
```

Responsabilidades:

- `MainWindow`: GUI, alta/detección de juegos, estado visible y ciclo de vida del worker. No decide combate.
- `BotEngine`: aplica snapshots planos de configuración, inicia y evalúa los módulos.
- `GameStateManager`: consume el último snapshot visual sin bloquear el reloj de acciones y publica una copia coherente para la GUI.
- `VisionManager`: posee captura, COM, HUD, HP/MP, objetivo, OCR, coordenadas y orientación dentro de `bot-vision`.
- `InputManager`: entrega `KEYDOWN`, agenda `KEYUP`, separa movimiento, acción general y F8/F9/F10, y libera teclas al pausar o parar.
- `MovementManager`: único productor de `A/D/W`; conserva la máquina de estados, radio, watchdog y seguridad.
- `AdaptiveReturnPolicy`: política matemática O(1) sobre las tres teclas fijas que aprende el efecto de `A/D/W`; no captura, no usa OCR directamente, no crea hilos y no llama a Win32.
- Gestores de entidades: lectura y escritura JSON atómica, compartida por GUI y visión.

## GUI y perfiles

- `MainWindow` usa `WindowStaysOnTopHint`: permanece en primer plano y solo desaparece si el usuario la minimiza.
- La ventana v1.1.1 mide 480×320, con un mínimo intrínseco medido de 465×295. Muestra directamente el panel operativo sin pestañas `BOT/LOG`; inicio/parada comparte la cabecera compacta con GAME. `TARGET`, `LVL` y la barra HP enemiga están en ese orden y separados por 4 px, dejando el espacio flexible detrás de la barra.
- GAME permite seleccionar, añadir y borrar perfiles. El alta manual detecta ventana, PID y ejecutable; refresh vuelve a localizar el proceso del juego seleccionado. La pestaña PROCESO fue eliminada.
- La tarjeta `PERSONAJE` solo muestra HP, MP, coordenadas, origen y radio. HP y MP comparten una fila de barras de 120 px; coordenadas, botones y radio comparten otra. Nombre, nivel, online, tiempo quieto y OCR de identidad del jugador no existen.
- El objetivo ocupa una única fila y el panel de filtros contiene dos listas de 92×46, `Disponibles`, dos flechas e `Ignorados`; admite selección múltiple y guarda los cambios. Solo existe `Ignorar objetivos`; objetivos únicos fue eliminado.
- AutoTarget, AutoAttack y AutoLoot exponen milisegundos. AutoPot1, AutoMP y AutoHeal exponen recurso, umbral e intervalo independientes.
- La rotación expone `1..9` y `F1..F7`; solo participan las tarjetas marcadas. La columna numérica no tiene cabecera y la columna F1–F7 muestra únicamente `PRIORIDAD`, con un tooltip que explica que gana las colisiones sin adelantar sus tiempos. F8 y F9 están reservadas para AutoPot1 y AutoMP.
- Todos los botones tienen ayuda contextual al pasar el ratón. También se explican los tiempos, umbrales, coordenadas, listas y selectores; la ayuda del botón principal sigue el estado de arranque/parada y GAME siempre describe su conexión.
- Checks, umbrales y milisegundos de automatismos, radio e ignorados se aplican en vivo con debounce de 75 ms. La configuración de skills se captura al arrancar y sus checks y milisegundos quedan bloqueados hasta detener el bot. La GUI crea un snapshot inmutable de valores; ningún `QWidget` cruza al hilo del bot.
- El arranque muestra un estado intermedio cancelable. Al detener, la GUI conserva worker e hilo y muestra `DETENIENDO...` hasta confirmar que visión, OCR y COM han terminado; nunca permite reiniciar sobre una captura anterior aún viva.
- Durante una sesión quedan bloqueados GAME/proceso y las tarjetas `1..9`/`F1..F7`; los automatismos y ajustes auxiliares continúan editables. No se añadieron controles manuales de recalibración, panel de diagnóstico ni persistencia adicional de la configuración por juego.
- El refresco visual está limitado a 250 ms y la BBDD de enemigos se consulta cada segundo solo para detectar cambios.

## Cadencias y contrato de input

| Operación | Cadencia |
| --- | ---: |
| Worker y rotación | 25 ms, `PreciseTimer` |
| Movimiento | 100 ms |
| Objetivo y captura de visión | 100 ms |
| HP/MP del jugador | 250 ms |
| Coordenadas normales | 1 s |
| Coordenadas durante retorno | 500 ms |
| Orientación del minimapa normal / retorno | 500 / 100 ms |
| Espera máxima de frame | 10 ms |

Orden real de evaluación:

1. AutoConsumables.
2. AutoHeal.
3. MovementManager.
4. AutoLoot.
5. AutoTarget.
6. RotationManager.
7. AutoAttack.

La rotación se evalúa antes de AutoAttack para impedir que dos intervalos alineados hagan que `R` ocupe todos los vencimientos de una skill; `R` conserva el vencimiento fallido y lo reintenta en un tick posterior. AutoLoot y AutoTarget siguen delante. `InputManager` mantiene una vía de movimiento, una de acción general y vías propias para F8, F9 y F10. Mantener `W`, `A` o `D` no ocupa una acción; F8/F9/F10 pueden coincidir entre sí y con `R` o una skill porque no comparten cooldown. La misma tecla nunca se solapa. Movimiento libera exclusivamente su propia tecla; nunca ejecuta `release_all`.

Los intervalos usan reloj monotónico. La rotación no conserva intenciones, cola, TTL ni aplazamientos: cada tick calcula las skills vencidas y realiza un solo intento. Una F vencida gana cualquier colisión con `1..9`. Todas las ocurrencias de esa colisión se consideran consumidas aunque no se elijan o el envío falle; cada skill espera su siguiente periodo configurado y nunca reaparece 25 ms después como trabajo atrasado. Un tick tardío permite un único intento y salta los periodos ya perdidos. Solo un `KEYDOWN` correcto reinicia la cadencia desde la entrega real. F8, F9 y F10 pertenecen exclusivamente a los módulos de recursos y usan vías independientes.

No existe un planificador global con garantías de tiempo real. Sin embargo, captura, detección y OCR ya no se ejecutan delante de los módulos: el bot toma el snapshot visual más reciente y mantiene su reloj de 25 ms. Un heartbeat o frame con más de 750 ms se considera obsoleto, se detienen las acciones dependientes de visión y se libera cualquier movimiento activo. La rotación `1..9/F1..F7` sigue sus temporizadores si el proceso y su ventana continúan vivos; si el proceso se desconecta también se bloquea.

El arranque espera visión en pasos cancelables de 50 ms, no mediante una espera opaca. La petición de parada deshabilita input de inmediato y el worker comprueba cada 50 ms si `bot-vision` ya terminó; solo entonces emite `finished`. Las llamadas OCR tienen timeout de 750 ms y el pool se cierra de forma verificable, por lo que no quedan tareas de Tesseract deliberadamente abandonadas.

`WindowInputDriver` utiliza `WM_KEYDOWN/WM_KEYUP`, scan code y `SendMessageTimeout` de hasta 20 ms. `KEYUP` se agenda en un hilo propio. No hay fallback a `PostMessage`, al foco ni a otra ventana. La vía general, con hold de 25 ms, tiene una capacidad ideal de 40 skills/s; `R/E/F` usan normalmente 50 ms y comparten esa vía. F8/F9/F10 tienen capacidad independiente. Qt, Python y Win32 impiden prometer tiempo real duro. Activar las 16 skills de la vía general a 500 ms exige 32 acciones/s antes de contar ataque, target o loot y deja poco margen; no se almacenan atrasos ni se descargan después como una ráfaga.

Como `MovementManager` conserva su posición histórica antes de `R` y rotación, un `SendMessageTimeout` lento de `A/D/W` puede retrasar la entrega de una skill hasta 20 ms en ese tick. No cambia su deadline: `last_cast` se fija al `KEYDOWN` real y el siguiente intervalo se mide desde ahí. La suite incluye una prueba determinista de ese peor caso.

Kathana procesa chat y gameplay en el mismo `HWND`. El método evita escribir teclas automáticas dentro del chat, pero el propio juego puede bloquear acciones de gameplay mientras el chat está abierto. Evitar ese bloqueo exigiría una integración intrusiva y queda fuera de alcance.

## Contrato de combate

### Estado del objetivo y HP triestado

`TargetState` expone `selection_id`, `exists`, `visible`, `targetable`, identidad y los campos `hp_percent`, `hp_valid` y `hp_observed_at`.

| Estado | Condición | Consecuencia |
| --- | --- | --- |
| Desconocida | El HUD existe, pero la barra no se puede medir | `exists` sigue verdadero; `R` y las skills no esperan HP, y `E`, loot y movimiento responden a la selección real, no a una falsa lectura cero. |
| Medida | Barra roja continua y porcentaje mayor que cero | Clasifica la selección como enemigo y habilita OCR, BBDD y reglas de ignorados. |
| Vacía confirmada | Enemigo ya medido con cinco capturas vacías durante al menos 0,5 s | Marca el HP visual como cero, sin convertir una lectura aislada en muerte. |

La presencia procede exclusivamente del HUD seleccionado, no del porcentaje. Se toleran dos fallos consecutivos del anchor/crop y solo el tercero elimina el objetivo. La última lectura válida se conserva como fresca durante 750 ms; después se muestra como desconocida, pero el objetivo permanece presente mientras siga su HUD.

- Una barra detectada y medible por encima de cero clasifica un enemigo.
- Una lectura inválida es `None`, nunca un HP cero. No sobrescribe la última muestra ni confirma muerte o item.
- Una lectura válida intermedia cancela inmediatamente la confirmación de barra vacía.
- Un HUD que nunca presenta barra durante 1 s se clasifica como item y puede persistir su nombre validado en la BBDD correspondiente.
- El HP enemigo interviene en esta clasificación enemigo/item, necesaria para resolver nombres y aplicar `Ignorar objetivos`. Además, cada nuevo mínimo válido de al menos un punto reinicia exclusivamente el temporizador anti-bloqueo de AutoTarget; nunca condiciona AutoAttack ni la rotación.

El OCR de identidad trabaja en segundo plano. Solo se aplica un resultado con el mismo `selection_id` y firma visual. Una identidad ilegible se intenta como máximo tres veces, separando intentos 1 s.

### Ignorar objetivos

- La lista se normaliza sin distinguir mayúsculas y minúsculas.
- Sin filtro activo, cualquier objetivo existente está permitido.
- Con filtro activo, un nombre de `Ignorados` se rechaza.
- Un nombre desconocido se permite. Si después se resuelve como ignorado, AutoTarget cambia y AutoAttack deja de atacarlo.
- No existen objetivos únicos, filtros por tipo o nivel ni estados intermedios de decisión.

### AutoTarget (`E`)

Solicita otra selección si no hay un HUD de objetivo, el nombre resuelto pertenece a `Ignorados` o la misma selección agota el tiempo configurado sin progreso de HP.

- La primera búsqueda sin objetivo puede ser inmediata.
- Cada selección nueva observada durante la sesión se conserva al menos 4 s. Un objetivo ya presente al arrancar se considera anterior al bot y puede cambiar inmediatamente si está ignorado.
- La casilla de AutoTarget configura el tiempo anti-bloqueo entre 4.000 y 600.000 ms; su valor inicial es 10.000 ms. Cuenta desde que aparece la selección, se reinicia con cada nuevo mínimo válido de al menos un punto y, si `E` no cambia el objetivo, vuelve a contar desde la entrega correcta de esa tecla. La primera lectura válida solo fija la referencia y no desplaza el plazo; las subidas y oscilaciones no simulan progreso.
- Dos `E` quedan separadas por al menos 4 s. La búsqueda sin objetivo y el descarte de ignorados conservan esa cadencia y no quedan ralentizados por el tiempo anti-bloqueo.
- Después de `E` concede 1 s para estabilizar visión.
- Un cambio de `selection_id` reinicia el estado. Una lectura incompleta nunca se convierte en HP cero ni reinicia el plazo: si durante todo el intervalo no existe evidencia de daño, AutoTarget avanza para que un objetivo propio, parcialmente herido o ilegible no bloquee el bot.

### AutoAttack (`R`)

Es independiente de AutoTarget. Ataca si `target.exists` y las reglas permiten el objetivo. No exige nombre, HP válido, porcentaje positivo ni un tick previo de `E`. El primer ataque de cada `selection_id` es inmediato; los siguientes respetan los milisegundos configurados. Resolver el nombre del mismo objetivo no reinicia el intervalo. Un envío fallido no consume tiempo.

### Rotación, recursos y loot

Skills `1..9` y `F1..F7`:

- Solo se registran checks activos y cada skill depende exclusivamente de sus milisegundos.
- La primera ejecución espera el intervalo configurado desde el arranque.
- Se intenta como máximo una skill por tick. Si hay teclas F1–F7 y numéricas vencidas a la vez, una F gana la colisión incluso cuando su entrega falla.
- Dentro de cada grupo gana el vencimiento más antiguo y después un cursor circular independiente. La prioridad nunca adelanta una acción antes de sus milisegundos.
- No dependen de combate, HP del objetivo, nombre, filtros o navegación.
- Usan pulsos de 25 ms y no tienen buffer. Una ocurrencia no elegida o fallida se pierde y solo vuelve a ser candidata en su siguiente periodo configurado. No hay reintento inmediato, catch-up ni ráfaga.
- F8 y F9 no forman parte de la rotación y quedan reservadas para AutoPot1 y AutoMP.

Recursos:

- F8 `AutoPot1` lee HP.
- F9 `AutoMP` lee MP.
- F10 `AutoHeal` lee HP.
- Se disparan con `0 < recurso <= umbral`, inmediatamente al cumplirlo y luego según su intervalo. Un fallo no inicia el intervalo. F8, F9 y F10 pueden entregarse en el mismo ciclo.
- HP y MP llevan validez y tiempo de observación independientes. Una lectura de más de 750 ms, inválida o fechada en el futuro no dispara consumibles; esta protección no bloquea `R` ni las skills.

AutoLoot (`F`) nunca recoge con un objetivo vivo seleccionado. Solo arma su ventana si antes observó un objetivo y este desaparece; no retrasa AutoTarget al arrancar sin objetivo. Durante los primeros 5 s post-combate bloquea temporalmente `E` y suspende el retorno para no abandonar el drop. Después envía `F`, conserva su intervalo mientras siga sin objetivo y permite AutoTarget en el tick siguiente. Si `F` falla, mantiene pendiente esa primera recogida.

## Navegación adaptativa

### Radio, llegada y seguridad

RADIO BOT usa distancia euclídea al origen: `FIJO`, `SIN LÍMITE`, `10`, `20`, `30` o `40`. El valor inicial es `40`. El origen solo se fija con coordenadas frescas. Coordenadas de uno solo dígito por eje se rechazan.

- Dos revisiones frescas consecutivas fuera del radio activan un regreso forzado.
- La histéresis no declara éxito junto al límite: exige volver cerca del origen. Con radio 10 termina a un máximo de 7 coordenadas; con 20, 30 o 40, a un máximo de 10. Esto evita oscilar sin exigir una precisión que el OCR y el movimiento actual aún no garantizan.
- El modo fijo `0` termina a un máximo de 2 coordenadas del origen. Permanecer quieto dentro del radio no inicia ningún movimiento.
- Un objetivo o combate pausa y libera movimiento. AutoAttack, skills y recursos continúan; navegación activa suspende normalmente AutoLoot y AutoTarget. La excepción es la primera recogida post-combate: durante sus 5 s se suspende el movimiento y `F` tiene precedencia antes de reanudar retorno o selección.
- Solo existe un comando de movimiento en vuelo. Los pulsos de calibración duran 250-500 ms y cualquier avance queda limitado a 650 ms.
- Cada resultado espera 200 ms tras soltar la tecla. Las muestras cuyo frame fue capturado durante el hold o el asentamiento se descartan para no atribuir movimiento residual a la siguiente tecla; se usa la primera posterior. Sin una muestra posterior en 2 s se entra en cooldown.
- Watchdog sin progreso: 6,5 s. Deadline por intento: 12-25 s. Hay límite de acciones, cooldown de 5 s y un reintento; después queda `FAILED` hasta volver al radio o cambiar el origen.
- La secuencia de desbloqueo es determinista; no genera movimientos aleatorios.

### Aprendizaje online

No se usa una red neuronal. El problema tiene tres acciones y poco estado, por lo que un controlador adaptativo es más barato y explicable:

1. Después de cada `A`, `D` o `W`, registra posición anterior, posterior y duración.
2. Calcula el vector X/Y por segundo y la recompensa: reducción de distancia al origen.
3. Mantiene por tecla una media móvil, confianza, muestras y contradicciones.
4. Ordena las próximas pruebas mediante el producto del vector aprendido con la dirección al origen, pero un vector por debajo de la confianza mínima no puede dominar el ranking.
5. Si la confianza es suficiente, calcula un hold conservador para recorrer aproximadamente el 70 % de la distancia pendiente y vuelve a observar.

El minimapa aporta además un heading automático del marcador central. Se segmenta el cuerpo rojo y su punta clara en un ROI de 50x50, se exigen dos frames distintos y concordantes y se filtran outliers mediante media circular con dispersión máxima entre pares. La punta debe ser pequeña, compacta y estar pegada al cuerpo para rechazar iconos blancos grandes, lejanos o alargados. La lectura representa orientación visual/cámara, no una pose garantizada. El aprendizaje conserva modelos independientes en sectores de 30 grados; un sector solo gobierna tras al menos tres observaciones coherentes y confianza suficiente. Mientras se calienta o si el heading no es fresco usa un modelo general aprendido lentamente como fallback.

Un desplazamiento menor de 1,25 coordenadas se interpreta como jitter o posible bloqueo y no crea un vector. Una lectura superior a 20 coordenadas/s se descarta como outlier; la velocidad de referencia observada es aproximadamente 6 coordenadas/s. Si el vector nuevo contradice el aprendido, la confianza cae y la media se adapta con más peso al dato reciente. Confianza repetidamente baja olvida el vector. Tras combate, pausa o desconexión se descarta el comando incompleto, se reduce la confianza a la mitad y se obliga a recalibrar `W/A/D` antes de volver a fijar una dirección.

El modelo, incluidos los sectores de orientación, se conserva entre regresos y se guarda por ID de juego en `data/navigation_learning.json` solo al detener el bot o cambiar de perfil. Este archivo de runtime está ignorado por Git. Al cargarlo, la confianza anterior se reduce a la mitad y nunca supera 0,5 hasta recibir evidencia nueva; los datos históricos orientan la primera prueba, pero no se obedecen ciegamente.

Métricas persistidas: episodios, regresos completados/fallidos, observaciones aceptadas/rechazadas/bloqueadas, contradicciones y mejora neta. `GameState.navigation_confidence` publica la confianza actual para diagnóstico, sin añadir refresco a la GUI.

Coste: tres productos escalares y unas pocas operaciones por observación, a 100 ms como máximo. El detector de heading mide aproximadamente 338 microsegundos por lectura sintética local, equivalente a cerca del 0,34 % de un núcleo a 10 Hz; no usa GPU, OCR ni dependencias nuevas. Obstáculos, UI escalada, o una dirección inaccesible impiden garantizar el 100 % de retornos. El aprendizaje confirma entrega de teclas y cambio de coordenadas, no que el juego haya ejecutado una acción interna.

Microbenchmark local orientativo: 100.000 rankings de las tres teclas promediaron 5,35 microsegundos por decisión. No sustituye una medición de CPU durante una sesión real, pero confirma que la política no es un nuevo cuello de botella.

## Visión y persistencia

- WGC captura el `HWND`; D3D11 copia y mapea el frame a CPU. Frames e interfaces se liberan también ante errores.
- WGC/D3D, sus objetos COM y `VisionManager` nacen, se usan y se destruyen en el hilo `bot-vision`. La automatización solo recibe `VisionSnapshot` congelados; no comparte arrays de imagen ni espera captura/OCR.
- El watchdog exige heartbeat y frame de menos de 750 ms. Un snapshot antiguo, una visión detenida o una ventana sin frames no mantienen acciones basadas en estado viejo.
- HP y MP cruzan el snapshot con validez y timestamp propios; un frame fresco no convierte en fresca una barra antigua.
- Los anchors de jugador y enemigo usan comparación en color dentro de zonas fijas del HUD a 1920x1080: jugador `(600,740,540x300)` y enemigo `(900,740,540x300)`. No vuelven a buscar a pantalla completa cuando una zona configurada no contiene el anchor. Esto evita los falsos positivos observados con la detección enmascarada y mantiene el ciclo por debajo del watchdog incluso si faltan ambas barras.
- Tras la primera detección se reutiliza el HUD del jugador y la posición del anchor enemigo. Las comprobaciones posteriores buscan en un ROI local de 24 px. Si tres capturas enemigas fallan, se fuerza una nueva búsqueda en su zona configurada; un fallo descarta esa caché y vuelve a intentar a 500 ms.
- HP y MP se recuperan de forma independiente. Un fallo de ambos solicita relectura a 100 ms; un solo recurso ilegible no invalida el otro. Las búsquedas del jugador tienen backoff de 500 ms medido desde el final del intento, por lo que un HUD ausente no encadena `matchTemplate` continuamente.
- Solo se cargan anchors de jugador, enemigo y minimapa. La orientación reutiliza el crop central del minimapa y no añade otro `matchTemplate`.
- El pool OCR tiene dos workers: identidad enemiga y coordenadas. Cada llamada Tesseract tiene timeout de 750 ms y el cierre espera esas tareas acotadas antes de dar por terminado `bot-vision`.
- Coordenadas válidas tienen dos o tres dígitos por eje. Saltos grandes requieren dos lecturas coherentes. `VisionManager` fecha la observación con el instante del frame, no con el final del OCR, y `PlayerState` conserva un historial corto de revisiones para atribuir cada pulso correctamente.
- Refrescar el origen invalida el epoch y sustituye el lector de coordenadas: un OCR iniciado antes del refresh se cancela o se ignora y no puede revalidar una posición anterior.
- Las imágenes de diagnóstico solo se escriben con `features.debug_mode`.

Datos activos:

- `data/config.json`: juego activo, features y filtro por juego.
- `data/games.json`: perfiles de proceso, ventana y resolución.
- `data/entities/enemies.json`: nombres, encuentros e ignorados.
- `data/entities/items.json`: entidades sin barra para uso futuro.
- `data/templates.json` y tres anchors PNG: geometría y referencias visuales.
- `data/navigation_learning.json`: aprendizaje generado en runtime; no forma parte del repositorio.

Los nombres OCR se normalizan antes de persistir. Se rechazan temporizadores, coordenadas, niveles, símbolos impropios y candidatos sin letras suficientes. Un enemigo nuevo necesita dos observaciones coincidentes; aliases e ignorados se deduplican. Las BBDD de entidades son datos de usuario y deben preservarse en futuras limpiezas.

## Requirements, instalación y ejecución

Entorno de referencia: Windows 10 20H2 x64 y Python 3.14.6. `requirements.txt` fija las nueve dependencias directas:

| Dependencia | Uso |
| --- | --- |
| `PySide6_Essentials` | GUI Qt sin Addons no usados |
| `numpy` | Frames y máscaras |
| `opencv-python-headless` | Visión sin segunda GUI |
| `psutil` | Procesos |
| `pytesseract` | Puente hacia Tesseract |
| `comtypes`, `pywin32` | COM, ventanas e input de Windows |
| `winrt-runtime`, `winrt-Windows.Graphics.Capture` | WGC |

Las dependencias Windows tienen marcador de plataforma. El controlador adaptativo usa solo la biblioteca estándar; no se ha añadido TensorFlow, PyTorch, scikit-learn ni otra dependencia.

Una instalación limpia debe contener solo `opencv-python-headless`; no debe coexistir con `opencv-python`, porque ambos distribuyen el mismo namespace `cv2`.

Desde la raíz del repositorio:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

`pytesseract` no incluye el programa Tesseract. Para ejecutar desde código debe instalarse por separado y estar en `PATH`:

```powershell
tesseract --version
```

Arranque y pruebas:

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Desde código, los recursos se resuelven respecto a la raíz del repositorio y los datos mutables permanecen en `data/`, con independencia del directorio desde el que se lance `main.py`. En una build congelada los recursos se leen desde `_internal` y los datos de usuario se guardan en `%LOCALAPPDATA%\SB Automation Suite\data`. En el primer arranque se copian solo los ficheros iniciales que falten; una actualización nunca sobrescribe la configuración, perfiles o BBDD existentes. `SB_AUTOMATION_DATA_DIR` permite usar un directorio alternativo para pruebas o modo portable explícito.

## Compatibilidad y build

| Plataforma | Estado real |
| --- | --- |
| Windows 10 20H2 x64 | Referencia desde código y build portable validadas por tests y smoke. WGC conserva el marco amarillo si el sistema no concede captura sin borde. |
| Windows 10 1903+ | Diseño compatible con WGC; falta validar cada build. |
| Windows 11 x64 | Ruta prevista; falta validar permisos, captura sin borde y artefacto final. |
| Ubuntu 24.04 X11/Wayland | No compatible: faltan backends de captura, ventana e input y hay imports Win32. |
| macOS | Fuera del plan. |

El marco WGC no aparece en el frame entregado a visión. La aplicación intenta desactivarlo si la API y permisos lo permiten; un fallo conserva el borde sin detener captura. Cada sistema necesita una build nativa.

La build se genera con PyInstaller 6.22.1 en formato `onedir`, ventana sin consola, sin UPX y para Windows x64. `SB_Automation_Suite.spec` incorpora Qt, OpenCV, NumPy, pywin32, WinRT, logo, templates, anchors y los datos iniciales. También incluye Tesseract 5.5.3, sus DLL, `tessdata` y su licencia; el equipo de destino no necesita instalar Python ni Tesseract. En Windows, las rutas del motor OCR se convierten mediante `GetShortPathNameW` para que Tesseract pueda cargar idiomas aunque la ruta de extracción contenga acentos.

Las dependencias de empaquetado están fijadas en `requirements-build.txt`. El proceso reproducible es:

```powershell
.\scripts\build_windows.ps1 -Version 1.1.1
```

El script crea un entorno limpio `.build-venv`, valida dependencias, ejecuta toda la suite, genera el ejecutable, comprueba los recursos críticos —incluida `python314.dll`—, arranca y espera la aplicación empaquetada con un directorio de datos nuevo, ejecuta el Tesseract incluido y crea `release/SB_Automation_Suite_v<versión>_Windows_x64.zip`. Después extrae ese ZIP en una carpeta nueva, vuelve a comprobar el ejecutable y la DLL y repite el smoke desde la copia extraída. Esperar cada proceso gráfico evita bloquear `base_library.zip` y convierte ambos smoke en validaciones reales del código de salida. El paquete incluye `LEEME_PRIMERO.txt` para advertir que no se debe abrir el EXE dentro del ZIP ni separarlo de `_internal`.

Build v1.1.1 del 17 de agosto de 2026: `SB_Automation_Suite_v1.1.1_Windows_x64.zip`, 173,31 MiB, SHA-256 `31A838B0085DA557363F3810E37C62FB1D108F9143B49CFA07D7741EC09915AB`. Contiene 429 archivos; `_internal/python314.dll` mide 6.778.592 bytes y el ejecutable extraído termina el smoke con código 0. Es una candidata portable, no un instalador ni un binario firmado. Falta validar en equipos Windows 10 y 11 limpios la captura WGC real, OCR, entrega de input, permisos de captura sin borde, persistencia y sesiones prolongadas sin fuga D3D.

Checklist de entrega final: prueba en Windows limpio, selección del `HWND`, captura y resize/restart, OCR con Tesseract incluido, input de fondo, diferencia de privilegios frente al juego, ciclos repetidos sin fuga D3D, datos persistentes y smoke por versión de Windows.

## Health check

Baseline de ingeniería del 11 de agosto de 2026; no equivale a un benchmark de FPS:

| Factor | Peso | Nota | Evidencia o penalización |
| --- | ---: | ---: | --- |
| Rendimiento | 30 % | 92 % | Automatización desacoplada de captura/CV; timer de 25 ms, rotación sin cola y detección de heading submilisegundo. |
| Consumo | 25 % | 90 % | Tres anchors, un hilo visual y dos workers OCR; penalizan copia GPU-CPU y Tesseract. |
| Fiabilidad | 25 % | 93 % | Snapshots inmutables, watchdog, cierre verificado, timeout OCR, JSON atómico y HP/MP con frescura; falta sesión real prolongada. |
| Utilidad y mantenibilidad | 20 % | 95 % | Configuración live sin QWidget cruzados y caminos legacy reducidos; heading/HUD requieren calibración real. |

Resultado ponderado: **92 %**. No se puntúa como tiempo real ni se da por validado el retorno hasta medirlo dentro de Kathana.

Resultados de la limpieza previa:

- Requirements directos: 14 a 9.
- Plantillas: 17 archivos/1.101.278 bytes a 3/16.766 bytes.
- `TemplateDetector` pasó de recolectar y deduplicar todos los matches a buscar el máximo.
- Se retiraron capturadores alternativos, modelos legacy, pestaña PROCESO, identidad del jugador, herramientas manuales, datos duplicados y debug generado.
- Construcción local orientativa de `VisionManager`: 86,23 ms y +5,29 MiB antes; primera muestra de 23,84 ms y mediana warm aproximada de 6 ms y +0,81 MiB después.

La suite y las cifras exactas de archivos se actualizan al final de cada health check; los tests verifican contratos Python y entrega Win32 simulada, no el resultado visual dentro de Kathana.

Snapshot v1.1.1 del 17 de agosto de 2026 tras ajustar la GUI y endurecer la distribución portable:

- 292/292 tests automatizados en verde, incluidos snapshots/hilo visual, inicio cancelable, cierre pendiente/verificado, watchdog con rotación independiente, frescura independiente de HP/MP, AutoTarget anti-bloqueo configurable, zonas de HUD sin fallback global, rechazo cruzado jugador/enemigo, recuperación local, ausencia del retorno por quietud, bloqueo de skills durante la sesión, rotación F1–F7 sin cola, arbitraje frente a `R`, loot antes de target/retorno, layout 480×320 sin solapes y fila TARGET/LVL/HP adyacente, radio live 10/20/30/40, timeout OCR, configuración live auxiliar, tooltips, lanes de input, heading circular, aprendizaje sectorizado, persistencia opcional, atribución temporal, outliers, histéresis, convivencia de teclas y rutas Unicode frozen/source para templates y OCR.
- 106 archivos Python, 18.534 líneas físicas, 3.424 en blanco, 1 comentario de línea completa y 15.109 líneas efectivas.
- `compileall`, `pip check`, smoke offscreen desde código, desde `dist` y desde una extracción limpia del ZIP, imports nativos, idiomas de Tesseract empaquetado, validación JSON, presencia de `python314.dll` e integridad del ZIP correctos.
- No se añadieron dependencias, polling ni consumo de GPU/CPU durante la ejecución. El cambio de GUI solo modifica geometría y pintura; el endurecimiento se ejecuta únicamente al construir la distribución. Una prueba real de Kathana en el equipo Windows 10 de referencia confirmó el funcionamiento general de visión, combate e input en v1.1; el regreso al origen siguió siendo irregular. Los radios reducidos hacen que se active antes, pero no se considera corregida la navegación hasta repetir pruebas reales.

## Riesgos y siguientes pasos

1. Validar en una zona abierta de Kathana el heading en varias orientaciones, mapas y escalas de UI; medir falso-válido y error angular antes de confiar en él como señal principal.
2. Probar los radios 10/20/30/40 y medir porcentaje de regresos, tiempo medio, distancia extra, contradicciones, cambios de sector y pausas de combate. Si la dirección mejora pero se detiene demasiado lejos, evaluar por separado bajar la tolerancia máxima de llegada de 10 a 5.
3. Inspeccionar `data/navigation_learning.json` tras varias sesiones para ajustar umbrales solo con evidencia.
4. Instrumentar percentiles de captura, OCR, antigüedad del snapshot y retraso entre deadline y `KEYDOWN` sin convertirlos de momento en un panel GUI.
5. Validar barras, watchdog, resize/restart de captura y sesiones prolongadas a 1920x1080. Los templates actuales asumen esa resolución y escala fija de UI; un cambio de escala exige anchors y geometría calibrados para ese perfil.
6. Validar la build portable en Windows 10 y 11 limpios, incluyendo WGC, OCR, input de fondo y varias horas de ejecución; después decidir si se crea instalador firmado y el alcance real de Ubuntu.
7. Python no puede interrumpir con seguridad una llamada nativa que se bloquee dentro de WinRT o del proceso de Tesseract. Los timeouts cubren el funcionamiento normal; si una prueba real reproduce un bloqueo nativo, el siguiente aislamiento debe ser un proceso auxiliar reiniciable, no finalizar hilos a la fuerza.

## Invariantes de continuidad

- No equiparar HP numérico cero con muerte sin `hp_valid` y frescura.
- No bloquear `R` o skills esperando nombre, OCR o HP.
- No pulsar `E` durante estabilización o retención.
- No cambiar los temporizadores de skills desde navegación.
- No ejecutar F1–F7 antes de su deadline, no almacenar skills vencidas y dar siempre a una F vencida el primer intento frente a `1..9`.
- Aplicar cambios live mediante valores planos encolados; no leer ni transportar widgets desde el hilo del bot.
- No ejecutar automatismos dependientes de visión con heartbeat o frame obsoleto; la rotación temporizada continúa solo mientras el proceso siga conectado.
- No disparar F8/F9/F10 con HP o MP inválido, antiguo o fechado en el futuro; esto nunca debe condicionar `R` ni la rotación.
- No emitir `finished`, cerrar la GUI ni permitir otro arranque mientras `bot-vision` siga vivo.
- Un movimiento nunca debe liberar una tecla de acción.
- Aprender solo de coordenadas nuevas y frescas; degradar datos contradictorios y limitar cada intento.
- No introducir acceso Win32 directo en módulos.
- No reintroducir funciones eliminadas sin un caso aprobado.
- Preservar GUI y BBDD activas durante limpiezas.
- Actualizar este snapshot tras cambios de arquitectura, comportamiento, compatibilidad o riesgos, sin acumular un diario cronológico.
- Ejecutar suite, `pip check`, smoke de imports y revisión de recursos antes de cerrar una auditoría.
