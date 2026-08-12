# Sistema de combate

Contrato vigente del runtime de combate. Este documento describe lo implementado, no una lista de ideas futuras.

## Principios

- Automatización externa y no intrusiva: visión, OCR e input al `HWND`; sin lectura de memoria, inyección ni hooks internos.
- `AutoTarget` selecciona; `AutoAttack` ataca. Ninguno debe usar al otro como condición.
- Una lectura incompleta nunca se convierte por defecto en HP 0.
- El nombre solo participa cuando el filtro `Ignorar objetivos` está activo.
- Todas las teclas pasan por `InputManager`.

Flujo principal:

```text
WGC/D3D11 -> VisionManager -> GameState/TargetState
                                  |
                                  +-> AutoTarget
                                  +-> AutoAttack
                                  +-> resto de módulos
                                           |
                                           v
                                      InputManager -> HWND
```

El worker ejecuta un tick preciso cada 25 ms. La visión de objetivo se limita a 100 ms y la del HUD del jugador a 250 ms. Estos intervalos son cadencias solicitadas: captura, OCR u otra acción ya en vuelo pueden añadir latencia.

## Estado del objetivo y HP triestado

`TargetState` expone:

- `selection_id`: identidad monotónica de la selección visual.
- `exists`, `visible`, `targetable`.
- `name`, `level`, `identity_pending`.
- `hp_percent`, `hp_valid`, `hp_observed_at`.

La vida se interpreta como tres estados:

| Estado | Condición | Consecuencia |
| --- | --- | --- |
| Desconocida | `hp_valid == False` o lectura demasiado antigua | No significa muerte; no provoca `E` ni avanza el temporizador de bloqueo. |
| Viva | HP válido y fresco, `hp_percent > 0` | Participa en la ventana de progreso. |
| Muerta | HP válido y fresco, `hp_percent <= 0` | AutoTarget puede solicitar otra selección cuando vence la retención mínima. |

Para AutoTarget una lectura válida deja de ser fresca después de 0,5 s. Una selección nueva dispone de 1 s para adquirir barra. Durante esa gracia existe provisionalmente: `AutoAttack` puede enviar `R` y la rotación continúa.

La clasificación visual sigue estas reglas:

- Barra física detectada y porcentaje medible mayor que cero: enemigo.
- Enemigo que ya tuvo HP válido y pierde la barra: hacen falta tres capturas vacías consecutivas para confirmar muerte; una lectura válida intermedia cancela la confirmación.
- HUD válido que nunca presenta barra durante toda la gracia: se clasifica como item y deja de ser objetivo atacable; su nombre validado puede almacenarse en la BBDD de items.
- Recorte inválido o lectura numérica inválida: HP desconocido. No confirma muerte ni item.

El OCR de identidad se ejecuta en segundo plano. Un resultado solo se aplica si conserva el `selection_id` y la firma visual vigentes. Una identidad ilegible se intenta como máximo tres veces por selección, separando los intentos 1 s para evitar Tesseract en cada frame.

## Reglas de objetivos

Solo existe el filtro `Ignorar objetivos`:

- La lista se normaliza sin distinguir mayúsculas/minúsculas.
- Sin filtro activo, cualquier `target.exists` está permitido.
- Con filtro activo, un nombre incluido se rechaza.
- Un nombre todavía desconocido se permite. Si luego se resuelve como ignorado, AutoTarget lo cambia y AutoAttack deja de atacarlo.

No existen `PENDING`, objetivos únicos, filtro por tipo ni filtro de nivel en la GUI. `TargetDecision` solo puede ser `ALLOW` o `REJECT`.

## AutoTarget (`E`)

AutoTarget solicita una nueva selección cuando:

1. No existe objetivo.
2. El nombre resuelto está en `Ignorados` y el filtro está activo.
3. El objetivo tiene HP muerto confirmado.
4. Un objetivo vivo no muestra progreso suficiente durante 10 s.

Protecciones temporales:

- La primera búsqueda sin objetivo puede ser inmediata.
- Cada selección nueva se conserva al menos 4 s.
- Dos pulsaciones de `E` quedan separadas al menos por el máximo entre el intervalo configurado y 4 s.
- Después de `E` se conceden 1 s a visión para estabilizar la selección, incluso si dos enemigos producen la misma identidad visual.

Progreso de daño:

- Al comenzar una ventana se guarda el HP de referencia.
- Hay progreso significativo solo cuando `HP actual < HP de referencia * 0,90`.
- El progreso reinicia otra ventana de 10 s desde el nuevo HP.
- Si no se alcanza ese descenso al vencer la ventana, se solicita otro objetivo.
- Una lectura desconocida o antigua limpia la ventana; nunca consume sus 10 s como si fuese HP 0.

Ejemplos: `100 -> 50` mantiene el objetivo y reinicia la ventana; `90 -> 85` no supone un 10 % relativo y cambiará al vencer; `100 -> 90` exacto tampoco supera el umbral estricto.

## AutoAttack (`R`)

AutoAttack es independiente de AutoTarget. Envía la tecla cuando:

- `target.exists` es verdadero; y
- las reglas permiten el objetivo.

No exige nombre, HP válido, porcentaje positivo ni un tick previo de AutoTarget. El primer ataque de cada `selection_id` es inmediato y los siguientes respetan los milisegundos configurados. Resolver el nombre del mismo objetivo no reinicia el intervalo.

Un envío fallido no consume el intervalo: se reintenta en un tick posterior.

## Rotación, recursos y loot

Rotación `1..9` y `F1..F9`:

- Solo registra tarjetas con check activo.
- Cada skill depende únicamente de su intervalo.
- La primera ejecución espera ese intervalo desde el arranque.
- Se ejecuta una skill por tick. Entre las vencidas tiene prioridad el menor intervalo configurado; después, el deadline más antiguo, y un empate exacto usa turno circular.
- No depende de combate, HP del objetivo, filtros ni navegación.
- Las skills usan pulsos de 25 ms y reintentan 25 ms después si otra acción ocupa el input; el intervalo solo empieza tras un envío correcto.
- F8/F9 también pueden pertenecer a AutoPot1/AutoMP. Si ambos productores están activos, la emergencia de recurso conserva prioridad y el timer de la tarjeta de rotación deja de ser exclusivo.

La capacidad máxima teórica de la rotación es 40 pulsaciones por segundo, antes de descontar otras acciones. Activar 18 skills a 500 ms exigiría 36 pulsaciones por segundo y deja prácticamente sin margen a E/R/F y consumibles; esos ajustes no pueden garantizar todos los intervalos simultáneamente.

Recursos:

- F8 `AutoPot1`: HP del jugador.
- F9 `AutoMP`: MP del jugador.
- F10 `AutoHeal`: HP del jugador.
- Se disparan cuando `0 < recurso <= umbral`.
- El primer intento al cumplirse el umbral es inmediato; después respetan su intervalo. Un fallo de input no inicia el intervalo.

AutoLoot (`F`):

- Nunca recoge mientras exista objetivo.
- Tras desaparecer el objetivo espera al menos 5 s.
- Después respeta su intervalo configurable.
- Si F se envía en un tick, E no se envía en ese mismo tick.

## Orden real e input

Orden de evaluación actual:

1. AutoConsumables.
2. AutoHeal.
3. MovementManager.
4. AutoLoot.
5. AutoTarget.
6. AutoAttack.
7. RotationManager.

No existe todavía un gestor global de prioridades. `InputManager` admite como máximo una acción no relacionada con movimiento y una tecla de movimiento simultáneas. Una acción ocupada se reintenta; por ello el orden anterior no garantiza tiempo real duro.

`WindowInputDriver` usa `WM_KEYDOWN/WM_KEYUP`, scan code y `SendMessageTimeout` de 20 ms. El `KEYUP` se agenda en un hilo propio para no alargar la pulsación durante OCR o captura. No hay fallback a `PostMessage`, al foco ni a otra ventana.

Kathana procesa el chat y el gameplay en el mismo `HWND`: el método evita escribir letras automáticas en el chat, pero el propio juego puede bloquear acciones de gameplay mientras el chat esté abierto. Saltarse ese estado exigiría una integración intrusiva y queda fuera de alcance.

## Interacción con navegación

- Un objetivo o combate pausa el retorno y libera `A/D/W`.
- Con navegación activa se suspenden AutoLoot y AutoTarget.
- AutoAttack, rotación y recursos pueden seguir evaluándose.
- Al salir del retorno o entrar en cooldown se reanudan los módulos suspendidos.

## Invariantes para futuras modificaciones

- Nunca equiparar `hp_percent == 0` con muerte sin `hp_valid` y frescura.
- Nunca bloquear `R` o skills esperando OCR de nombre o HP.
- No pulsar `E` repetidamente durante estabilización o retención.
- No introducir acceso directo a Win32 desde módulos.
- Cualquier gestor de prioridades futuro debe conservar los intervalos y registrar tiempo solo tras un envío exitoso.
