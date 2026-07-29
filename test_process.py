from core.process_manager import ProcessManager

pm = ProcessManager()

process_name = "KathanaGame.exe"  # Cambia esto por el .exe de tu juego

if pm.find_process(process_name):
    print("✅ Proceso encontrado")
    print(f"PID: {pm.get_pid()}")
else:
    print("❌ Proceso no encontrado")