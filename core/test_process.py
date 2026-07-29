from core.process_manager import ProcessManager

pm = ProcessManager()

process_name = "Game.exe"  # Cambia esto por el .exe de tu juego

if pm.find_process(process_name):
    print("✅ Proceso encontrado")
    print(f"Nombre: {pm.get_name()}")
    print(f"PID: {pm.get_pid()}")
else:
    print("❌ Proceso no encontrado")