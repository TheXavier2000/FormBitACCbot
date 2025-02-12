import win32com.client as win32
import pythoncom
import pandas as pd
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def generar_html_con_formato(df):
    """
    Genera una tabla HTML con formato compacto para enviar por correo.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("❌ Error: El objeto pasado a generar_html_con_formato no es un DataFrame.")

    if df.empty:
        return "<p><strong>⚠️ No hay datos disponibles para mostrar.</strong></p>"

    df = df.fillna("")  # Reemplazar valores NaN con cadenas vacías

    try:
        # 📌 Estilos CSS para la tabla
        estilos_css = """
        <style>
        table {
            border-collapse: collapse;
            border-spacing: 0;
            font-family: Calibri, sans-serif;
            font-size: 9px;
            width: auto;
        }
        th, td {
            border: 1px solid #0563C1;
            background-color: #D9E1F2;
            padding: 2px 5px; /* Reduce el espacio interno */
            white-space: nowrap;
        }
        th {
            background-color: #FFFFFF;
            font-weight: bold;
            text-align: center;
        }
        td:nth-child(1) { width: 480px; text-align: left; }   /* Actividad */
        td:nth-child(2) { width: 55px; text-align: center; }    /* Status */
        td:nth-child(3) { width: 137px; text-align: center; }   /* Observación */
        td:nth-child(4) { width: 99px; text-align: center; }    /* Revisado por */
        td:nth-child(5) { width: 86px; text-align: center; }    /* Franja horaria */
        td:nth-child(6) { width: 42px; text-align: center; }    /* Día */
        td:nth-child(7) { width: 73px; text-align: center; }    /* Mes */
        td:nth-child(8) { width: 47px; text-align: center; }    /* Año */
        td:nth-child(9) { width: 34px; text-align: center; }    /* TK */
        td:nth-child(10) { width: 105px; text-align: center; }  /* Categoría */
        td:nth-child(11) { width: 63px; text-align: center; }   /* Impacto */
        td:nth-child(9):has(span.tiny-text) { height: 14px; }   /* Si TK es de una sola línea */
        </style>
        """

        # 📌 Convertir DataFrame a HTML sin índices y con escape deshabilitado
        html_table = df.to_html(index=False, escape=False)

        # 📌 Agregar estilos CSS a la tabla
        html_final = estilos_css + html_table

        return html_final
    except Exception as e:
        logging.error(f"❌ Error al generar la tabla HTML: {e}")
        return "<p><strong>⚠️ Error al generar la tabla.</strong></p>"


def send_mail(destinatario, cc_list, df):
    """
    Envía un correo usando Microsoft Outlook con una tabla HTML.
    """
    if not isinstance(df, pd.DataFrame):
        logging.error("❌ Error: df no es un DataFrame válido.")
        return

    # 📌 Obtener la fecha actual en el formato requerido
    fecha_actual = datetime.now()
    fecha_formateada_texto = fecha_actual.strftime("%d de %B de %Y")  # Ejemplo: 09 de febrero de 2025
    fecha_formateada_asunto = fecha_actual.strftime("%d/%m/%Y")  # Ejemplo: 09/02/2025

    # 📌 Asunto del correo
    asunto = f"PRUEBA AUTOMATIZACIÓN Bitácora {fecha_formateada_asunto}"

    # 📌 Cuerpo del correo
    cuerpo_correo = f"""
    <html>
        <body>
            <p>Buen día,</p>
            <p>Se hace envío de la bitácora correspondiente al día {fecha_formateada_texto},\n</p>
            {generar_html_con_formato(df)}
            <p>\nCordialmente,</p>
            
        </body>
    </html>
    """

    try:
        pythoncom.CoInitialize()  # 🔹 Inicializa COM para evitar el error de CoInitialize

        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # Crear nuevo correo

        #Definición del correo destinatario y copia de correo
        destinatario = "emolina@azteca-comunicaciones.com"
        cc_list = ["nocti@azteca-comunicaciones.com", ""]

        mail.To = destinatario
        mail.CC = "; ".join(cc_list) if cc_list else ""  
        mail.Subject = asunto
        mail.HTMLBody = cuerpo_correo  # Cuerpo del correo en HTML

        mail.Send()
        logging.info(f"✅ Correo enviado con éxito a {destinatario}.")

    except Exception as e:
        logging.error(f"❌ Error al enviar el correo con Outlook: {e}")

    finally:
        pythoncom.CoUninitialize()  # 🔹 Libera COM al finalizar
