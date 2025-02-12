import os
import pandas as pd
from dotenv import load_dotenv
import telebot
from datetime import datetime
from generar_csv import analizar_message_ia
from send_mail import send_mail  # Se importa la función correcta

# 📌 Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ ERROR: No se encontró el token de Telegram. Verifica tu archivo .env.")

bot = telebot.TeleBot(TOKEN)

print(f"✅ Bot iniciado con éxito: {TOKEN[:10]}...")

@bot.message_handler(func=lambda message: True)
def recibir_message(message):
    usuario = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
    fecha_actual = datetime.now()

    df = analizar_message_ia(message, usuario, fecha_actual.timestamp())

    if df is None or df.empty:
        bot.reply_to(message, "⚠️ No se pudo generar la tabla correctamente. Verifica tu mensaje.")
        return

    destinatario = "vilopez@azteca-comunicaciones.com"
    cc_list = [""]  # Puedes agregar más correos aquí

    # 📌 Formatear la fecha para el asunto y cuerpo del correo
    fecha_texto = fecha_actual.strftime("%d de %B de %Y")  # Ejemplo: 09 de febrero de 2025
    fecha_asunto = fecha_actual.strftime("%d/%m/%Y")  # Ejemplo: 09/02/2025

    asunto = f"Bitácora {fecha_asunto}"  # 📌 Asunto con la fecha actual

    send_mail(destinatario, cc_list, df)  # Se usa la función con Outlook

    bot.reply_to(message, f"✅ Bitácora del {fecha_texto} procesada y enviada por correo.")

# 🚀 Iniciar el bot
bot.polling()
