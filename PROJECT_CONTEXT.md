# SB Automation Suite — contexto vigente

Snapshot operativo del 11 de agosto de 2026. Para reglas detalladas de combate y distribución, consultar `COMBAT_SYSTEM_DESIGN.md` y `BUILDING.md`.

## Propósito y límites

Suite modular para automatizar acciones de juegos mediante captura visual, OCR e input dirigido a una ventana en segundo plano. Kathana (DX11) es la implementación de referencia, pero la separación por capas debe permitir añadir otros perfiles.

El proyecto es deliberadamente no intrusivo:

- Sin lectura de memoria del juego.
- Sin inyección de DLL, hooks internos ni modificación del cliente.
- Sin depender del foco de teclado.
- Toda acción pasa por `InputManager` y todo estado del juego procede de visión/configuración.

## Estado por fases

| Fase | Estado |
| --- | --- |
| GUI genérica | Estable y funcional. Mantener distribución y estilo salvo petición expresa. |
| Captura, visión e input de fondo | Operativa en el entorno Windows 10 de referencia; combate y navegación siguen en calibración real. |
| Persistencia | Operativa para perfiles de juego, configuración, enemigos, ignorados e items. |
| Build y multiplataforma | Pendiente. No existe instalador validado; Windows 11 y Ubuntu requieren trabajo descrito en `BUILDING.md`. |

## Arquitectura actual

```text
MainWindow (GUI Qt)
  |-- ProcessManager / GameProfileManager
  |-- EntityDatabaseManager
  `-- BotWorker (QThread, 25 ms preciso)
        `-- BotEngine
              |-- GameStateManager -> VisionManager -> WGC/D3D11/OCR
              |-- InputManager -> WindowInputDriver -> HWND
              `-- módulos de automatización
```

Responsabilidades:

- `MainWindow`: interacción, estado visible, alta/detección de juegos y lifecycle del worker; no contiene decisiones de combate.
- `BotEngine`: configura, inicia y ordena módulos.
- `GameStateManager`: mantiene un único `GameState` y regula visión.
- `VisionManager`: captura, HUD, HP/MP, objetivo, OCR enemigo y coordenadas.
- `InputManager`: entrega inmediata de `KEYDOWN`, agenda `KEYUP`, impide solapamientos incompatibles y libera teclas al pausar/parar.
- BBDD: escrituras JSON atómicas protegidas entre GUI y visión.

## GUI

- La ventana principal usa `WindowStaysOnTopHint`: permanece visible sobre el juego y solo se oculta al minimizarla.
- GAME permite seleccionar, añadir y borrar perfiles; el alta manual detecta ventana, PID y ejecutable. Refresh vuelve a localizar el proceso del juego seleccionado. La antigua pestaña PROCESO no existe.
- La tarjeta `PERSONAJE` muestra únicamente HP, MP, coordenadas, origen, radio y tiempo quieto. Nombre, nivel, online y OCR de identidad del jugador fueron retirados.
- El panel de objetivos contiene `Disponibles`, dos flechas e `Ignorados`. Admite selección múltiple y autosave. Solo existe el check `Ignorar objetivos`; objetivos únicos fue eliminado por completo.
- AutoAttack y AutoLoot tienen intervalo editable. AutoPot1, AutoMP y AutoHeal tienen recurso, umbral e intervalo independientes.
- La rotación expone `1..9` y `F1..F9`; solo participan los checks activos.
- El refresco visual se limita a 250 ms y la BBDD de enemigos se consulta cada segundo solo para detectar cambios.

## Automatización y cadencias

Orden del engine: consumibles, heal, movimiento, loot, target, attack y rotación.

- Tick del worker y rotación: 25 ms con `PreciseTimer`.
- Objetivo/captura de visión: 100 ms.
- HUD HP/MP del jugador: 250 ms.
- Minimap y coordenadas normales: 1 s.
- Coordenadas durante retorno: 500 ms, reutilizando el último HUD del minimapa.
- Espera máxima de un frame: 10 ms.

Resumen funcional:

- AutoTarget (`E`) mantiene cada selección al menos 4 s, separa pulsaciones al menos 4 s, concede 1 s de estabilización y cambia por objetivo ausente, ignorado, muerte confirmada o 10 s sin un descenso relativo superior al 10 %.
- AutoAttack (`R`) actúa inmediatamente sobre cada nueva selección permitida y después respeta su intervalo. No espera nombre ni HP.
- Skills respetan solo check e intervalo; una por tick, priorizando el menor valor de ms entre las vencidas, después el deadline y finalmente un desempate circular. Usan pulsos de 25 ms.
- F8/F9 tienen doble productor si se habilitan también como AutoPot1/AutoMP: la emergencia de recurso gana el slot y la tarjeta de rotación se reintenta en el siguiente tick.
- F8 usa HP, F9 usa MP y F10 usa HP; se activan con `0 < valor <= umbral` y reintentan tras el intervalo solo si el envío anterior tuvo éxito.
- AutoLoot (`F`) requiere ausencia de objetivo durante al menos 5 s.

La semántica completa, incluida la validez de HP, está centralizada en `COMBAT_SYSTEM_DESIGN.md`.

## Visión y estado de HP

- WGC captura el `HWND` validado; D3D11 copia y mapea el frame a CPU. Cada frame y todos los interfaces se liberan incluso ante error.
- El detector de anchors devuelve únicamente el mejor `matchTemplate` mediante `minMaxLoc`; ya no materializa todos los píxeles coincidentes ni hace deduplicación cuadrática.
- Solo se cargan los anchors realmente usados: jugador, enemigo y minimapa.
- El pool OCR tiene dos workers: identidad enemiga y coordenadas. Los resultados se descartan si pertenecen a una selección/generación antigua; un nombre fallido se reintenta como máximo tres veces, con 1 s entre intentos.
- `TargetState.hp_valid` y `hp_observed_at` separan HP desconocido, vivo y muerto. Lectura inválida o tardía nunca equivale a cero.
- Una selección dispone de 1 s para adquirir HP. Un enemigo conocido necesita tres frames consecutivos sin barra para confirmar muerte; un HUD que nunca presenta barra se clasifica como item solo después de la gracia.
- Coordenadas válidas tienen dos o tres dígitos por eje. Saltos grandes exigen dos lecturas coherentes y cada posición conserva revisión y antigüedad.
- Las imágenes de diagnóstico solo se escriben con `features.debug_mode`; los artefactos generados se ignoran en Git.

## Datos

Archivos activos:

- `data/config.json`: juego activo, features y estado del filtro por juego.
- `data/games.json`: perfiles de nombre, proceso, ventana y resolución.
- `data/entities/enemies.json`: nombres canónicos, encuentros y estado ignorado.
- `data/entities/items.json`: nombres detectados sin barra para uso futuro.
- `data/templates.json` y tres PNG de anchors: geometría y referencias visuales.

Los nombres OCR se normalizan y se filtran antes de persistir. Se rechazan temporizadores, coordenadas, niveles, símbolos impropios y candidatos sin suficientes letras. Un enemigo nuevo requiere dos observaciones coincidentes; los aliases se deduplican y los cambios de ignorados se escriben por lote. La GUI oculta registros legacy de baja confianza sin borrar datos activos.

Se eliminaron las BBDD duplicadas y el histórico de jugadores porque la identidad del personaje ya no tiene consumidores. `data/entities/enemies.json` y `items.json` son datos de runtime y deben preservarse durante futuras limpiezas.

## Navegación

- RADIO BOT usa distancia euclídea desde el origen: fijo `0`, `25`, `50`, `75`, `100` o sin límite.
- El origen solo se fija con coordenadas frescas. Dos muestras fuera del radio inician retorno; permanecer quieto el tiempo configurado es un segundo disparador.
- `MovementManager` prueba `W/A/D`, mide si cada pulso acerca al origen y exige dos mejoras fiables antes de confiar en una dirección.
- Pulsos de 250–500 ms en calibración y máximo de 650 ms al avanzar; búsqueda de desbloqueo determinista, sin movimiento aleatorio.
- Watchdog sin progreso de 6,5 s, deadline de 12–25 s, límite de acciones, cooldown de 5 s y un único reintento. Después queda en `FAILED` hasta recuperar el radio o cambiar el origen.
- Objetivo/combate pausa y libera movimiento. El retorno es heurístico porque X/Y no informa de la orientación; necesita validación dentro de Kathana.

## Health check 2026-08-11

La puntuación es una evaluación de ingeniería, no un benchmark de FPS:

| Factor | Peso | Nota | Evidencia/penalización |
| --- | ---: | ---: | --- |
| Rendimiento | 30 % | 88 % | Detector de anchors linealizado y cadencias acotadas; penaliza captura/visión síncrona antes de acciones. |
| Consumo | 25 % | 91 % | Solo 3 anchors y 2 workers OCR; penalizan copia completa GPU→CPU y Tesseract. |
| Fiabilidad | 25 % | 92 % | Suite automatizada, cleanup D3D, JSON atómico y HP triestado; falta perfil prolongado real W10/W11. |
| Utilidad y mantenibilidad | 20 % | 94 % | Funciones actuales cubiertas y gran reducción de caminos legacy; quedan calibraciones específicas de HUD/navegación. |

Resultado ponderado: **91 %**.

Cambios de la auditoría:

- `requirements.txt`: 14 → 9 entradas directas; sin addons Qt, namespaces WinRT ni OpenCV GUI no usados.
- Plantillas raster: 17 archivos / 1.101.278 bytes → 3 archivos / 16.766 bytes (aprox. 98,5 % menos).
- Código Python: 125 → 92 archivos y 20.100 → 12.118 líneas; el código efectivo baja de 12.050 a 9.441 líneas, los comentarios completos de 522 a 2 y las líneas en blanco de 7.528 a 2.675. El archivo adicional es cobertura útil de barras, no runtime.
- En muestras locales, construir `VisionManager` pasó de 86,23 ms / +5,29 MiB RSS / 18 entradas de plantilla a 23,84 ms en la primera muestra y una mediana warm de ~6,0 ms / +0,81 MiB / 13 entradas. Es una medición orientativa de arranque, no un benchmark sostenido.
- Eliminados capturadores alternativos sin consumidores, modelos y gestores legacy, antigua GUI PROCESO/widgets huérfanos, pipeline de identidad del jugador, tools manuales, datos duplicados y debug generado.
- `TemplateDetector` pasa de recolectar/deduplicar todos los matches a buscar solo el máximo.
- Comentarios de separador, bloques vacíos y prints de hot path se reducen sin cambiar contratos.
- La suite final contiene 155/155 tests automatizados en verde; el script manual de plantillas no se contabiliza como test y fue retirado.

La auditoría estática y los tests no garantizan consumo máximo en una sesión real. La cifra debe recalibrarse cuando exista telemetría de CPU, GPU, latencia de acción y RSS en una prueba prolongada dentro del juego.

## Riesgos y siguientes pasos

1. Instrumentar percentiles de captura, visión, OCR y retraso real entre acción vencida y `KEYDOWN`.
2. Desacoplar el snapshot de captura del tick de módulos si la visión síncrona demuestra retrasar teclas.
3. Extender el uso de ROI a los anchors de jugador/enemigo y medir si el OCR de coordenadas necesita menos variantes; identidad ya aplica backoff y el minimapa ya usa su área de búsqueda.
4. Añadir integración completa EnemyMonitor+barra, restart/resize de captura, lifecycle completo GUI/worker y persistencia concurrente; `BarReader`, timeout sin frame y error del worker ya tienen cobertura directa.
5. Validar retorno, umbrales de barra y sesiones prolongadas en Kathana 1920×1080.
6. Crear y probar la build Windows descrita en `BUILDING.md`; después decidir el alcance real de Ubuntu.

## Reglas de continuidad

- Revisar esta arquitectura antes de crear clases o pipelines nuevos.
- No reintroducir funcionalidades eliminadas sin un caso de uso aprobado.
- Preservar el diseño visual salvo petición expresa.
- Actualizar este snapshot tras cambios de arquitectura, comportamiento, compatibilidad o riesgos; evitar acumular un historial cronológico.
- Ejecutar suite, `pip check`, smoke de imports y revisión de recursos antes de cerrar una auditoría.
