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
   |
   +--> KeyboardDriver



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


HP Potion:

F8


MP Potion:

F9


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


Pendiente implementar.


Comportamiento deseado:


1.
Si no existe objetivo:

usar tecla E


2.
Si objetivo está en lista ignorada:

cambiar objetivo


3.
Si objetivo no pierde vida durante 6 segundos:

cambiar objetivo


El juego funciona así:

E selecciona enemigo más cercano y rota entre enemigos en rango.


---

# AutoAttack


Pendiente implementar.


Debe:

- comprobar objetivo válido
- usar tecla configurada
- respetar intervalo


No atacar:

- sin objetivo
- objetivo muerto
- objetivo ignorado


---

# AutoLoot


Pendiente implementar.


No crear detector de objetos inicialmente.


Primera versión:

Si no estamos en combate:

usar tecla F cada X ms


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
- las coordenadas y el radio de acción todavía no tienen un diseño definitivo
- la eficiencia actual de coordenadas y radio de acción se considera inferior al 50 %
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
