from core.process_manager import ProcessManager
from core.memory_reader import MemoryReader

pm = ProcessManager()

if pm.find_process("KathanaGame.exe"):

    print("Proceso encontrado")

    reader = MemoryReader()

    if reader.open_process(pm.get_pid()):
        print("Handle abierto correctamente")
    else:
        print("No se pudo abrir el proceso")

else:

    print("Proceso no encontrado")