import os
from dotenv import load_dotenv
import telebot
from datetime import datetime
from bot_handler import analizar_mensaje_ia  # Importar la función mejorada

# Cargar variables de entorno
load_dotenv()

# Obtener el token desde el archivo .env
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Verifica que el token se haya cargado
if not TOKEN:
    raise ValueError("❌ ERROR: No se encontró el token de Telegram. Verifica tu archivo .env.")

bot = telebot.TeleBot(TOKEN)

print(f"✅ Bot iniciado con éxito: {TOKEN[:10]}...")  # Muestra los primeros caracteres del token

@bot.message_handler(func=lambda message: True)
def recibir_mensaje(message):
    """Captura los mensajes del usuario y los procesa."""
    usuario = message.from_user.first_name + " " + message.from_user.last_name if message.from_user.last_name else message.from_user.first_name
    fecha = datetime.now()
    mensaje_texto = message.text

    # Procesar el mensaje y generar el archivo
    df = analizar_mensaje_ia(mensaje_texto, usuario, fecha)

    # Responder en Telegram confirmando el guardado del archivo
    bot.reply_to(message, "✅ Tu reporte ha sido procesado y guardado en 'reporte.xlsx'.")

# Iniciar el bot
print("🤖 Bot en ejecución...")
bot.polling()
