from core.process_manager import ProcessManager
from core.memory_reader import MemoryReader

pm = ProcessManager()

if not pm.find_process("KathanaGame.exe"):
    print("Juego no encontrado")
    exit()

print("Juego encontrado")
print("PID:", pm.get_pid())

memory = MemoryReader()

if memory.connect(pm.get_pid()):
    print("Handle abierto correctamente")
else:
    print("No se pudo abrir el proceso")