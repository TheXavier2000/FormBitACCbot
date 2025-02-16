import os
import tkinter as tk
import psutil
from dotenv import load_dotenv
import telebot
from bot_handler import procesar_texto_desde_gui  # Importar la nueva función

# 📌 Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ ERROR: Credenciales de Telegram no encontradas en .env.")

bot = telebot.TeleBot(TOKEN)

# 📌 Verificar si la GUI ya está en ejecución
def gui_ya_ejecutandose():
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            if proc.info["cmdline"] and "notes.py" in proc.info["cmdline"]:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

# 📌 Evitar múltiples instancias de la GUI
if gui_ya_ejecutandose():
    print("⚠️ La interfaz gráfica ya está abierta.")
    exit()

# 📌 Función para enviar mensaje a Telegram y procesarlo
def enviar_mensaje():
    texto = text_area.get("1.0", tk.END).strip()
    if texto:
        try:
            # Enviar el mensaje al bot de Telegram
            bot.send_message(TELEGRAM_CHAT_ID, f"📝 *Nuevo mensaje:* \n\n{texto}", parse_mode="Markdown")
            
            # Enviar el mensaje al procesamiento en bot_handler.py
            procesar_texto_desde_gui(texto)

            text_area.delete("1.0", tk.END)
            estado_label.config(text="✅ Mensaje enviado y procesado", fg="green")
        except Exception as e:
            estado_label.config(text=f"❌ Error al enviar: {e}", fg="red")

# 📌 Crear la interfaz tipo Bloc de Notas
root = tk.Tk()
root.title("Bloc de Notas")
root.geometry("600x500")

# 📌 Área de texto
text_area = tk.Text(root, wrap="word")
text_area.pack(expand=True, fill="both", padx=10, pady=10)

# 📌 Botón para enviar mensaje
boton_enviar = tk.Button(root, text="Enviar a Telegram", command=enviar_mensaje, bg="blue", fg="white")
boton_enviar.pack(pady=5)

# 📌 Etiqueta de estado
estado_label = tk.Label(root, text="", fg="black")
estado_label.pack()

# 📌 Iniciar la interfaz gráfica
root.mainloop()
