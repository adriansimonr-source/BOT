# SB Automation Suite - Project Context


## Descripción

Proyecto de automatización para juegos basado en Python + PySide6.

Objetivo:
Crear un bot modular, genérico y no intrusivo.

No se permite:
- lectura de memoria del juego
- inyección DLL
- hooks internos
- modificaciones específicas del juego

El sistema debe funcionar mediante:
- visión
- OCR
- interacción Windows
- se pueden explorar nuevas opciones de mejora no intrusivas que lean la memoria del juego o intenten modificarla
- Compatible con W102h20. Pendiente implementar compatibilidad con  versiones de W11, MAC y Ubuntu.

---

# Arquitectura


## Capas principales


GUI
 |
 v
BotEngine
 |
 +-- Modules
 |
 +-- InputManager
 |
 +-- GameStateManager
 |
 v
Vision / Windows


---

# GUI

Framework:
PySide6

La interfaz actual está aprobada visualmente.

IMPORTANTE:

NO modificar:
- distribución de paneles
- colores
- estilos
- tamaños

salvo petición explícita.

---

# BotEngine


Responsabilidad:

- controlar ciclo del bot
- registrar módulos
- iniciar/detener módulos
- coordinar estado global


Actualmente registra:

- AutoTarget
- AutoAttack
- AutoLoot
- AutoConsumables
- AutoHeal
- RotationManager


---

# GameStateManager


Mantiene el estado actual del juego.

Tiene referencia a:

ProcessManager


Acceso:

game_state_manager.process_manager


Permite obtener:

HWND del juego:

process_manager.get_window_handle()


---

# Input System


Arquitectura:


Modules

   |
   v

InputManager

   |
   +--> WindowInputDriver



## Objetivo

Enviar teclas a ventanas en segundo plano.


Actualmente funciona:

- Kathana Steam
- DX11
- ventana completa


Método:

Windows PostMessage usando HWND.


NO usar:

- keybd_event
- soluciones dependientes del foco

Si no existe un HWND válido, `InputManager` no debe enviar ninguna tecla ni
usar como alternativa la ventana que tenga el foco.


---

# Input Usage


Los módulos nunca llaman directamente a Windows.


Correcto:


input.press("F8")


Incorrecto:

win32gui.PostMessage()


---

# AutoConsumables


Implementado:


AutoPot1 (umbral de vida):

F8 (AutoPot1)


AutoMP (umbral de maná):

F9 (AutoMP)


Auto Heal:

F10 (AutoHeal), activado mediante umbral de HP e intervalo propio.


Configuración:

- tecla
- umbral %
- intervalo ms


Ejemplo:

HP < 40%

cada 2000ms:

F8


---

# AutoTarget


Implementado mediante `InputManager`.


Comportamiento deseado:


1.
Si no existe objetivo:

usar tecla E


2.
Si objetivo está en lista ignorada:

cambiar objetivo


El juego funciona así:

E selecciona enemigo más cercano y rota entre enemigos en rango.


---

# AutoAttack


Implementado mediante `InputManager`.


Debe:

- comprobar objetivo válido
- usar tecla configurada
- respetar intervalo


No atacar:

- sin objetivo
- objetivo ignorado

No utilizar el porcentaje de HP enemigo para decidir si se ataca.


---

# AutoLoot


Implementado mediante `InputManager`.


No crear detector de objetos inicialmente.


Primera versión:

Si no estamos en combate:

usar tecla F cada X ms

El intervalo se configura en milisegundos desde la GUI.


Motivo:

El juego recoge objetos cercanos con interacción global.


---

# Vision


Sistema basado en:

OCR
captura pantalla


No modificar salvo necesidad.


---

# Código


Mantener:

- módulos independientes
- bajo acoplamiento
- evitar lógica en GUI


---

# Regla importante


Antes de modificar archivos:

revisar arquitectura existente.

No crear clases duplicadas.

No cambiar nombres públicos usados por otros módulos.

---

# Fases del proyecto


## Fase 1 - Interfaz gráfica

Objetivo:

- crear una GUI estable, amigable y genérica
- permitir incorporar distintas acciones de automatización

Estado:

- concluida
- el diseño visual actual está aprobado y debe conservarse


## Fase 2 - Visión y automatización en segundo plano

Objetivo:

- capturar cualquier ventana, incluso cuando esté en segundo plano
- detectar su estado y comportamiento mediante visión
- ejecutar acciones sin depender del foco de la ventana

Implementación de referencia:

- juego Kathana
- motor gráfico DX11
- captura mediante WinRT en Windows 10
- OCR para funcionalidades que requieren leer texto de la imagen

Estado:

- la captura y la capa de visión están operativas
- las coordenadas y el radio de acción disponen ya de una primera implementación funcional
- el retorno por radio necesita calibración dentro del juego porque no se conoce la orientación del personaje
- esta parte queda temporalmente cerrada para priorizar la validación de entradas
- se ha validado el envío de F8 en segundo plano al alcanzar el umbral configurado

Prioridad inmediata:

- conectar y validar el resto de teclas y acciones disponibles en la GUI
- comprobar que cada acción se comporte como se espera en segundo plano
- mantener el uso centralizado de `InputManager`


## Fase 3 - Persistencia de datos

Objetivo:

- almacenar datos obtenidos mediante capturas y detecciones
- almacenar datos introducidos manualmente
- utilizar el apartado de base de datos existente como capa de persistencia

Estado:

- fase prevista y parcialmente estructurada en el proyecto

---

# Continuidad y documentación

- El proyecto dispone de un repositorio GitHub donde se publica el código junto con su documentación.
- Actualizar este archivo con resúmenes relevantes de los descubrimientos, decisiones, avances, limitaciones y tareas pendientes.
- Mantener la información concisa para que `PROJECT_CONTEXT.md` permita recuperar rápidamente el contexto en futuras sesiones.

---

# Estado de la automatización - agosto de 2026

- `AutoTarget` envía la tecla configurada cuando no existe objetivo o el objetivo está ignorado.
- `AutoAttack` actúa sobre un objetivo existente y no ignorado, sin depender de la lectura de HP enemigo.
- `AutoLoot` utiliza su tecla configurada cuando no existe objetivo y ha vencido el tiempo de seguridad.
- `RotationManager` envía las habilidades habilitadas mediante `InputManager` respetando exclusivamente el intervalo configurado; no depende de combate, objetivo, filtros nominales ni navegación.
- La rotación solo registra habilidades con el check activo y espera su intervalo antes de la primera ejecución.
- Cuando varias habilidades están disponibles, se ejecuta primero la que lleva más tiempo vencida.
- Si dos habilidades vencen al mismo tiempo, se elige una mediante desempate circular y la otra queda pendiente para el ciclo siguiente.
- F8 (AutoPot1) y F10 (AutoHeal) usan el porcentaje de HP; F9 (AutoMP) usa el porcentaje de MP. Un valor igual a cero se considera una lectura no disponible.
- El estado `in_combat` se deriva de la presencia del HUD de un objetivo, sin validar su HP.
- El refresco visual de la GUI se limita a 250 ms para evitar actualizaciones innecesarias.
- El minimapa y el OCR de coordenadas se procesan como máximo una vez por segundo; HP, MP y objetivo mantienen el ciclo normal.
- Las imágenes y trazas de depuración de coordenadas quedan desactivadas salvo que `features.debug_mode` esté habilitado.
- El ciclo ligero de acciones se ejecuta cada 50 ms. La presencia de objetivo se revisa cada 100 ms y el HUD del jugador cada 250 ms para equilibrar respuesta y consumo.
- Auto Target busca objetivos cada 250 ms. Auto Attack se evalúa cada 50 ms y tiene un intervalo editable de 100 a 600000 ms, con 250 ms por defecto.
- Auto Loot permite configurar en la GUI un intervalo de 100 a 600000 ms, con 500 ms por defecto.
- Auto Loot muestra nombre, tecla F e intervalo juntos en una misma línea.
- Auto Attack solo actúa con un objetivo seleccionado y permitido. Ataca inmediatamente al detectar cada objetivo nuevo y después respeta los milisegundos configurados.
- Auto Loot nunca envía F mientras exista un objetivo seleccionado. Cuando el objetivo desaparece espera al menos 5 segundos antes del primer intento y después respeta su intervalo configurado.
- Auto Loot y Auto Target no envían F y E dentro del mismo ciclo: cuando corresponde recoger, ese intento tiene prioridad y la búsqueda continúa en el siguiente ciclo.
- La detección crítica de jugador/objetivo ocurre antes del OCR auxiliar de minimapa para priorizar las acciones.
- La parada del bot se solicita al hilo de trabajo de forma asíncrona; la GUI no espera bloqueada a que termine visión.
- Los consumibles visibles son F8 (AutoPot1), F9 (AutoMP) y F10 (AutoHeal). Cada uno usa su umbral de recurso y un intervalo independientes; el primer intento al cumplirse el umbral es inmediato y un envío fallido no consume el intervalo.
- Los checks F8/F9 de la rotación y las tarjetas AutoPot/AutoMP son automatizaciones independientes sobre la misma tecla; si se activan ambas, existirán tanto intentos periódicos como intentos condicionados por HP o MP.
- La opción `Atacar objetivos únicos` habilita una lista blanca editable. El diálogo propone los enemigos disponibles de la BBDD y también acepta texto manual.
- Con la lista blanca activa, Auto Target rota con E hasta encontrar un nombre permitido y Auto Attack rechaza cualquier otro objetivo. La rotación de teclas es independiente de esos filtros.
- Los nombres ignorados y únicos se comparan sin distinguir mayúsculas y minúsculas.
- Con filtros de ignorados o únicos, un objetivo sin nombre queda pendiente de OCR hasta 2 segundos; Auto Attack no reutiliza la identidad anterior.
- Las listas `Disponibles` e `Ignorados` se sincronizan cada segundo con `data/entities/enemies.json` cuando cambia el fichero.
- Los enemigos detectados se incorporan a la BBDD; la GUI evita duplicados por mayúsculas/minúsculas y agrupa variantes OCR claras sin fusionar nombres legítimos parecidos.
- El estado ignorado se guarda en `enemies.json`. Mover un enemigo entre listas actualiza todas sus variantes OCR y sobrevive al reinicio de la GUI.
- Las escrituras de enemigos son atómicas y están protegidas entre los hilos de visión y GUI para no perder encuentros ni cambios de ignorados.
- Lecturas OCR con formato de temporizador, por ejemplo `4m 59s`, no se añaden ni se muestran como enemigos. Los registros antiguos de ese tipo se conservan en el JSON, pero quedan ocultos de la lista.
- Un nombre no puede estar simultáneamente en `Ignorados` y `Únicos`; al ignorarlo se elimina de la lista blanca.
- La lista de objetivos únicos se mantiene durante la sesión actual; todavía no tiene persistencia propia.

## Cambios de respuesta, GAME y navegación - agosto de 2026

- OCR de jugador, enemigo y coordenadas se ejecuta fuera del hilo del bot. Los resultados se aplican solo si siguen perteneciendo a la selección o sesión vigente.
- La presencia de un objetivo queda disponible antes de conocer su nombre. Sin filtros nominales, Auto Attack puede enviar la primera `R` inmediatamente; con filtros espera una identidad segura.
- Cada objetivo recibe un `selection_id`; resolver `<desconocido>` a un nombre no reinicia el intervalo de Auto Attack ni duplica `R`.
- Las pulsaciones de fondo usan `WM_KEYDOWN/WM_KEYUP` con scan code y flags correctos para `1..9`, `F1..F10`, `E`, `R`, `F`, `A`, `D` y `W`.
- `KEYUP` se programa fuera del ciclo del bot, por lo que el OCR no alarga la pulsación. Se mantiene una sola acción a la vez, pero puede coexistir con una tecla de movimiento; así `W/A/D` no retrasa habilidades ni curación. Una acción ocupada reintenta en el siguiente tick y sus milisegundos se registran solo al enviarse realmente.
- La espera de un frame tiene un límite de 50 ms para que una captura detenida no bloquee el ciclo de acciones, la parada ni la GUI.
- El lector de coordenadas procesa el texto `X/Y` completo, prioriza una máscara de blanco que elimina colores saturados y usa umbrales grises como respaldo.
- Se rechazan ejes de un solo dígito. Los saltos grandes requieren dos lecturas coherentes y las posiciones tienen validez, antigüedad y revisión.
- El bot captura el HWND exacto validado por ProcessManager y usa el tamaño actual de esa ventana, evitando asociar el proceso de una ventana con otra de título parecido.
- GAME integra el alta manual, detección ventana→PID→ejecutable, refresh del juego seleccionado, estado de conexión y borrado. La pestaña PROCESO se retiró; quedan BOT y LOG.
- El botón junto a NAME invalida el nombre almacenado y fuerza una nueva lectura OCR.
- MODE pasa a llamarse RADIO BOT, con radios `FIJO (0)`, `50`, `100`, `150` y `SIN LÍMITE`, más un tiempo `QUIETO` configurable entre 3 y 120 segundos. El radio se mide en unidades de las coordenadas `X/Y` del juego mediante distancia euclídea desde la posición inicial; no representa píxeles.
- Al exceder el radio en dos lecturas frescas o permanecer quieto el tiempo configurado lejos del inicio, MovementManager intenta volver probando `W`, `A` y `D`; conserva la dirección que reduce distancia y usa recuperación `A → D → W` si se bloquea.
- La navegación se pausa ante objetivo o combate. Durante el retorno se suspenden loot, target y ataque; las teclas `1..9`, `F1..F9`, AutoPot, AutoMP y AutoHeal siguen respetando sus temporizadores.
- El retorno es heurístico porque las coordenadas no aportan orientación. Debe validarse en Kathana si `A/D` desplazan lateralmente como se espera y ajustar pulso, tolerancia o secuencia con resultados reales.
- La ruta WinRT/D3D ya no vuelca vtables ni genera 99 mensajes por frame. Las funciones ABI se enlazan una vez, la conversión evita una copia completa intermedia y `Unmap` queda protegido incluso ante errores.
- Cada frame libera superficie, acceso DXGI y textura; al parar se cierran session/framepool/dispositivo WinRT y se liberan staging, contexto y dispositivo D3D. La prueba real mantuvo estable la memoria durante 120 frames y eliminó el crecimiento previo de unos 13 MB por reinicio.
- El arranque de captura es transaccional: si WinRT/D3D falla, se liberan los recursos parciales, el bot vuelve a `STOPPED`, la GUI se desbloquea y GAME muestra `Error al iniciar` con el detalle en el tooltip.
- La validación automatizada cubre acciones, filtros, OCR asíncrono, coordenadas, input, cleanup de captura, perfiles GAME, BBDD, GUI y navegación; la suite actual contiene 63 pruebas.
