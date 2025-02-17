import sys
import tkinter as tk
import psutil
import telebot
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


# 📌 Obtener el token del bot desde los argumentos de la línea de comandos
if len(sys.argv) > 1:
    TOKEN = sys.argv[1]
else:
    raise ValueError("❌ ERROR: No se proporcionó el token del bot.")

# 📌 Crear la instancia del bot usando el token proporcionado
bot = telebot.TeleBot(TOKEN)

# 📌 Función para enviar mensaje a Telegram
def enviar_mensaje():
    texto = text_area.get("1.0", tk.END).strip()
    if texto:
        try:
            bot.send_message(TELEGRAM_CHAT_ID, f"📝 *Nuevo mensaje:* \n\n{texto}", parse_mode="Markdown")
            text_area.delete("1.0", tk.END)
            estado_label.config(text="✅ Mensaje enviado y procesado", fg="green")
        except Exception as e:
            estado_label.config(text=f"❌ Error al enviar: {e}", fg="red")

# 📌 Crear la interfaz gráfica
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