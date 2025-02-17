import psutil
import os
import signal

# Obtener el PID del script actual
current_pid = os.getpid()

# Buscar todos los procesos en ejecución
for proc in psutil.process_iter(attrs=["pid", "name"]):
    try:
        # Verificar si el proceso es "python" o "python.exe"
        if "python" in proc.info["name"].lower() and proc.info["pid"] != current_pid:
            print(f"🔴 Matando proceso: {proc.info['name']} (PID: {proc.info['pid']})")
            os.kill(proc.info["pid"], signal.SIGTERM)  # SIGKILL si SIGTERM no funciona
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        continue

print("✅ Todos los procesos de Python han sido detenidos.")
