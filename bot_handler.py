import os
import logging
import smtplib
import telegram
from send_mail import enviar_correo_outlook
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from generar_csv import analizar_message_ia

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = os.getenv("TELEGRAM_GRUPO_NOC_TI_ID")  # Asegúrate de que el ID del grupo está bien escrito en el .env


if not TOKEN:
    raise ValueError("\n❌ ERROR: No se encontró el token de Telegram. Verifica tu archivo .env.\n")
if not GROUP_ID:
    raise ValueError("\n❌ ERROR: No se encontró el ID del grupo. Verifica tu archivo .env.\n")

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="\n%(asctime)s - %(levelname)s - %(message)s\n",
    handlers=[logging.StreamHandler()]
)

# Inicializar bot de Telegram
bot = telegram.Bot(token=TOKEN)

# Estados de la conversación en Telegram
CORREO, PASSWORD = range(2)

# Diccionario temporal para credenciales de usuarios
credenciales_pendientes = {}

def solicitar_correo(update, context):
    update.message.reply_text("✉️ Ingresa tu correo de Outlook:")
    return CORREO

def recibir_correo(update, context):
    user = update.message.from_user.username or update.message.from_user.first_name
    correo = update.message.text

    # Almacenar temporalmente el correo
    credenciales_pendientes[user] = {"correo": correo}
    
    update.message.reply_text("🔑 Ingresa tu contraseña de Outlook:")
    return PASSWORD

def recibir_password(update, context):
    user = update.message.from_user.username or update.message.from_user.first_name
    password = update.message.text

    # Almacenar la contraseña (solo en memoria temporalmente)
    credenciales_pendientes[user]["password"] = password

    # Intentar autenticación con Outlook
    if validar_credenciales(credenciales_pendientes[user]["correo"], password):
        update.message.reply_text("✅ Autenticación exitosa. Procesando tu solicitud...")
        
        # Procesar tabla y enviar correo
        procesar_mensaje(update, context)
        return ConversationHandler.END
    else:
        update.message.reply_text("❌ Error en la autenticación. Verifica tu correo o contraseña.")
        return ConversationHandler.END

def validar_credenciales(correo, password):
    """ Intenta autenticarse con Outlook. Si hay 2FA, se pedirá autorización en el móvil. """
    try:
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls()
        server.login(correo, password)  # Aquí Microsoft puede enviar la notificación al móvil
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError:
        return False

def procesar_mensaje(update, context):
    user = update.message.from_user.username or update.message.from_user.first_name
    correo_usuario = credenciales_pendientes[user]["correo"]
    
    df = analizar_message_ia(update.message, user, update.message.date.timestamp(), destinatario, cc_list, df)

    if df is not None and not df.empty:
        logging.info(f"✅ DataFrame generado correctamente:\n{df}")

        destinatario = os.getenv("EMAIL_DESTINATARIO")
        cc_list = [correo_usuario]

        if enviar_correo_outlook(df, destinatario, cc_list, correo_usuario):
            update.message.reply_text("📧 Correo enviado con éxito.")
        else:
            update.message.reply_text("❌ Error enviando el correo.")
    else:
        update.message.reply_text("⚠️ No se generó información válida.")


def reenviar_mensaje(update, context):
    """ Reenvía el mensaje recibido al grupo especificado. """
    user = update.message.from_user.username or update.message.from_user.first_name
    mensaje = update.message.text

    if mensaje:
        mensaje_reenviado = f"📢 *{user} envió un mensaje:*\n\n{mensaje}"
        bot.send_message(chat_id=GROUP_ID, text=mensaje_reenviado, parse_mode="Markdown")
        logging.info(f"✅ Mensaje reenviado al grupo {GROUP_ID}")


def start_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Agregar manejador para reenviar mensajes
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, reenviar_mensaje))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text & ~Filters.command, solicitar_correo)],
        states={
            CORREO: [MessageHandler(Filters.text & ~Filters.command, recibir_correo)],
            PASSWORD: [MessageHandler(Filters.text & ~Filters.command, recibir_password)]
        },
        fallbacks=[]
    )

    dp.add_handler(conv_handler)

    logging.info("🤖 Bot en ejecución...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    start_bot()
