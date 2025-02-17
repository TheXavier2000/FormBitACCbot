import os
import logging
import smtplib
from datetime import datetime
import telegram
from send_mail import send_mail
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from generar_csv import analizar_message_ia

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = os.getenv("TELEGRAM_GRUPO_NOC_TI_ID")

DESTINATARIO_DEFAULT = os.getenv("EMAIL_DESTINATARIO")
CC_LIST_DEFAULT = os.getenv("EMAIL_CC_LIST").split(",") if os.getenv("EMAIL_CC_LIST") else []

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

def procesar_texto_desde_gui(mensaje):
    """ Procesa el texto ingresado en la interfaz gráfica como si fuera un mensaje de usuario en Telegram. """
    user = "Usuario_GUI"
    destinatario = DESTINATARIO_DEFAULT
    cc_list = CC_LIST_DEFAULT

    df = None  # Inicializar df
    fecha_timestamp = datetime.now().timestamp()  # Definir la fecha

    # Llamada corregida a analizar_message_ia
    df = analizar_message_ia(mensaje, user, fecha_timestamp, DESTINATARIO_DEFAULT, CC_LIST_DEFAULT, df, fecha_timestamp)

    if df is not None and not df.empty:
        logging.info(f"✅ DataFrame generado correctamente desde la GUI:\n{df}")

        if send_mail(df, destinatario, cc_list, user):
            print("📧 Correo enviado con éxito desde GUI.")
        else:
            print("❌ Error enviando el correo desde GUI.")
    else:
        print("⚠️ No se generó información válida desde GUI.")

def solicitar_correo(update, context):
    update.message.reply_text("✉️ Ingresa tu correo de Outlook:")
    return CORREO

def recibir_correo(update, context):
    user = update.message.from_user.username or update.message.from_user.first_name
    correo = update.message.text
    credenciales_pendientes[user] = {"correo": correo}
    
    update.message.reply_text("🔑 Ingresa tu contraseña de Outlook:")
    return PASSWORD

def recibir_password(update, context):
    user = update.message.from_user.username or update.message.from_user.first_name
    password = update.message.text
    credenciales_pendientes[user]["password"] = password

    if validar_credenciales(credenciales_pendientes[user]["correo"], password):
        update.message.reply_text("✅ Autenticación exitosa. Procesando tu solicitud...")
        procesar_mensaje(update, context)
    else:
        update.message.reply_text("❌ Error en la autenticación. Verifica tu correo o contraseña.")
    
    return ConversationHandler.END

def validar_credenciales(correo, password):
    try:
        server = smtplib.SMTP("smtp.office365.com", 587)
        server.starttls()
        server.login(correo, password)
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError:
        return False

def procesar_mensaje(update, context):
    user = update.message.from_user.username or update.message.from_user.first_name
    correo_usuario = credenciales_pendientes.get(user, {}).get("correo", "")

    destinatario = DESTINATARIO_DEFAULT
    cc_list = [correo_usuario]

    df = None  # Inicializar df
    fecha_timestamp = update.message.date.timestamp()  # Obtener timestamp del mensaje
    fecha_actual = datetime.now()  # Definir fecha actual

    # ✅ Corrección: Usar `update.message.text` y `user` en vez de `usuario`
    df = analizar_message_ia(update.message.text, user, fecha_timestamp, fecha_actual, DESTINATARIO_DEFAULT, CC_LIST_DEFAULT, df)

    if df is not None and not df.empty:
        logging.info(f"✅ DataFrame generado correctamente:\n{df}")

        if send_mail(df, destinatario, cc_list, correo_usuario):
            update.message.reply_text("📧 Correo enviado con éxito.")
        else:
            update.message.reply_text("❌ Error enviando el correo.")
    else:
        update.message.reply_text("⚠️ No se generó información válida.")


def reenviar_mensaje(update, context):
    user = update.message.from_user.username or update.message.from_user.first_name
    mensaje = update.message.text

    if mensaje:
        mensaje_reenviado = f"📢 *{user} envió un mensaje:*\n\n{mensaje}"
        bot.send_message(chat_id=GROUP_ID, text=mensaje_reenviado, parse_mode="Markdown")
        logging.info(f"✅ Mensaje reenviado al grupo {GROUP_ID}")

def start_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reenviar_mensaje))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, solicitar_correo)],
        states={
            CORREO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_correo)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_password)]
        },
        fallbacks=[]
    )

    dp.add_handler(conv_handler)

    logging.info("🤖 Bot en ejecución...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    start_bot()
