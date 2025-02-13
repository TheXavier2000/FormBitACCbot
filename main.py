import os
import logging
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



# 📌 Importar destinatarios desde las variables de entorno
DESTINATARIO_DEFAULT = os.getenv("EMAIL_DESTINATARIO")
CC_LIST_DEFAULT = os.getenv("EMAIL_CC_LIST").split(",") if os.getenv("EMAIL_CC_LIST") else []

@bot.message_handler(func=lambda message: True)
def recibir_message(message):
    usuario = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
    fecha_actual = datetime.now()

    # 📌 Pasar las variables correctas a analizar_message_ia
    df = pd.DataFrame()  # Inicializar df antes de llamarlo
    df = analizar_message_ia(message, usuario, fecha_actual.timestamp(), DESTINATARIO_DEFAULT, CC_LIST_DEFAULT, df)


    if df is None or df.empty:
        bot.reply_to(message, "⚠️ No se pudo generar la tabla correctamente. Verifica tu mensaje.")
        logging.warning("⚠️ No se pudo generar la tabla correctamente. El DataFrame está vacío.")
        return

    try:
        send_mail(df)  # 📌 Ya no pasamos destinatarios ni cc_list, ya se toman dentro de send_mail()
        bot.reply_to(message, f"✅ Bitácora del {fecha_actual.strftime('%d de %B de %Y')} procesada y enviada por correo.")
    except Exception as e:
        bot.reply_to(message, "❌ Error al enviar el correo.")
        logging.error(f"❌ Error al enviar el correo: {e}")




# 🚀 Iniciar el bot
bot.polling()
