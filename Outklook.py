import os
import smtplib
from email.mime.text import MIMEText

# Leer credenciales desde las variables de entorno
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Servidor SMTP de Outlook
OUTLOOK_SMTP_SERVER = "smtp.office365.com"
OUTLOOK_SMTP_PORT = 587

def enviar_correo(destinatario, asunto, mensaje):
    # Crear el contenido del correo
    msg = MIMEText(mensaje)
    msg["Subject"] = asunto
    msg["From"] = EMAIL_USER
    msg["To"] = destinatario

    try:
        # Conectar al servidor SMTP de Outlook
        server = smtplib.SMTP(OUTLOOK_SMTP_SERVER, OUTLOOK_SMTP_PORT)
        server.starttls()  # Seguridad TLS
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        server.quit()
        print("✅ Correo enviado con éxito")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

# Ejemplo de uso
enviar_correo("destinatario@ejemplo.com", "Prueba desde Python", "Este es un correo de prueba enviado con variables de entorno.")
