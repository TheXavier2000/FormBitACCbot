import os
import re
import logging
import locale
import pandas as pd
import subprocess
from dotenv import load_dotenv
import telebot
from datetime import datetime
from generar_csv import analizar_message_ia
from send_mail import send_mail  # Se importa la función correcta

# 📌 Ruta del script de la interfaz gráfica
script_path = os.path.join(os.path.dirname(__file__), "notes.py")

# 📌 Verificar si la GUI ya está en ejecución
def gui_ya_ejecutandose():
    import psutil
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            if proc.info["cmdline"] and "notes.py" in proc.info["cmdline"]:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

# 📌 Iniciar la GUI si no está abierta
if not gui_ya_ejecutandose():
    try:
        subprocess.Popen(["python", script_path], creationflags=subprocess.DETACHED_PROCESS)
    except Exception as e:
        print(f"❌ Error al iniciar la interfaz gráfica: {e}")

# 📌 Configurar el idioma para que los meses aparezcan en español
locale.setlocale(locale.LC_TIME, "es_ES.utf8")  # Puede variar según el sistema operativo

# 📌 Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = os.getenv("TELEGRAM_GRUPO_NOC_TI_ID")  # 📌 ID del grupo al que se reenviarán los mensajes

if not TOKEN:
    raise ValueError("❌ ERROR: No se encontró el token de Telegram. Verifica tu archivo .env.")

if not GROUP_ID:
    raise ValueError("❌ ERROR: No se encontró el ID del grupo en .env. Asegúrate de definir TELEGRAM_GRUPO_NOC_TI_ID.")

bot = telebot.TeleBot(TOKEN)

print(f"✅ Bot iniciado con éxito: {TOKEN[:10]}...")

# 📌 Importar destinatarios desde las variables de entorno
DESTINATARIO_DEFAULT = os.getenv("EMAIL_DESTINATARIO")
CC_LIST_DEFAULT = os.getenv("EMAIL_CC_LIST").split(",") if os.getenv("EMAIL_CC_LIST") else []

def escape_markdown_v2(text):
    """ Escapa caracteres especiales para evitar errores en MarkdownV2 """
    special_chars = r"*_[]()~`>#+-=|{}.!<>"
    return re.sub(r"([%s])" % re.escape(special_chars), r"\\\1", text)

@bot.message_handler(func=lambda message: True)
def recibir_message(message):
    usuario = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
    fecha_actual = datetime.now()
    fecha_timestamp = fecha_actual.timestamp()  # Convertimos la fecha a timestamp


    print("Mensaje:", message.text)
    print("Usuario:", usuario)
    print("Fecha Timestamp:", fecha_timestamp)
    print("Destinatario:", DESTINATARIO_DEFAULT)
    print("CC List:", CC_LIST_DEFAULT)
    print("DataFrame inicial:", df)


    if df is None:
        df = pd.DataFrame()


    # ✅ Corrección en la llamada a analizar_message_ia
    df = analizar_message_ia(message.text, usuario, fecha_timestamp, fecha_actual, DESTINATARIO_DEFAULT, CC_LIST_DEFAULT, df)

    if df is None or df.empty:
        bot.reply_to(message, "⚠️ No se pudo generar la tabla correctamente. Verifica tu mensaje.")
        logging.warning("⚠️ No se pudo generar la tabla correctamente. El DataFrame está vacío.")
        return

    try:
        # ✅ Corrección en la llamada a send_mail()
        send_mail(df, DESTINATARIO_DEFAULT, CC_LIST_DEFAULT, usuario)

        fecha_formateada = fecha_actual.strftime("%d de %B de %Y")
        bot.reply_to(message, f"✅ Bitácora del {fecha_formateada} procesada y enviada por correo.")

        # 📌 Escapar caracteres especiales en MarkdownV2
        usuario_escapado = escape_markdown_v2(usuario)
        mensaje_escapado = escape_markdown_v2(message.text)

        # 📌 Reenviar el mensaje al grupo con formato seguro
        mensaje_reenviado = f"📢 *{usuario_escapado} envió un mensaje:*\n\n{mensaje_escapado}"
        bot.send_message(chat_id=GROUP_ID, text=mensaje_reenviado, parse_mode="MarkdownV2")

        logging.info(f"✅ Mensaje reenviado al grupo {GROUP_ID}")

    except Exception as e:
        bot.reply_to(message, "❌ Error al enviar el correo.")
        logging.error(f"❌ Error al enviar el correo: {e}")

# 🚀 Iniciar el bot
bot.polling()
