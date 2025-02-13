import re
import spacy
import logging
import pandas as pd
from datetime import datetime
from io import StringIO
from send_mail import send_mail

# Cargar modelo de NLP
nlp = spacy.load("es_core_news_md")

# Lista de meses en español
meses_espanol = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

def clasificar_status(oracion):
    oracion_lower = oracion.lower()

    # Palabras clave para cada categoría
    cerrado_keywords = [
    "cerrado", "finalizado", "resuelto", "completado", "terminado", "hecho", 
    "concluido", "solucionado", "ejecutado", "culminado", "listo", "archivado", 
    "entregado", "realizado", "satisfactorio"
]

    en_espera_keywords = [
        "pendiente", "validar", "revisar", "falta", "por hacer", "espera", 
        "esperar", "comunicarse", "aplazado", "pausado", "detenido", 
        "en espera", "revisión", "suspendido", "requerido", "confirmar", 
        "por confirmar", "necesario", "consulta", "aguardar", "verificar"
    ]

    en_proceso_keywords = [
        "proceso", "en curso", "trabajando", "ejecutando", "gestionando", 
        "desarrollando", "se está trabajando", "implementando", "operando", 
        "avanzando", "atendiendo", "en marcha", "realizando", "moviendo", 
        "ejecución", "tratando", "progresando", "continuando", "resolviendo"
]


    if any(word in oracion_lower for word in cerrado_keywords):
        return "Cerrado"
    elif any(word in oracion_lower for word in en_espera_keywords):
        return "En espera"
    elif any(word in oracion_lower for word in en_proceso_keywords):
        return "En proceso"
    else:
        return "En proceso"  # Se mantiene como "En proceso" si no hay coincidencias

def extraer_observaciones(texto):
    """ Extrae y resume las observaciones más relevantes de la actividad """
    doc = nlp(texto.lower())
    observaciones = []

    # 🔹 Categorías de palabras clave
    keywords_pendientes = [
        "pendiente", "falta", "por hacer", "completar", "retraso", 
        "atrasado", "quedó", "no se ha hecho", "no realizado", "sin terminar", 
        "postergado", "debe hacerse", "debe completarse"
    ]
    keywords_validacion = [
        "validar", "confirmar", "verificar", "corroborar", "analizar", 
        "ratificar", "comprobar", "autenticar", "certificar", "examinar"
    ]
    keywords_revision = [
        "revisar", "inspeccionar", "chequear", "auditar", "examinar", 
        "monitorear", "repasar", "evaluar", "controlar", "ajustar", "detallar"
    ]
    keywords_urgencia = [
        "urgente", "prioridad", "inmediato", "pronto", "rápido", "crítico", 
        "importante", "debe resolverse", "asap", "lo antes posible", "imprescindible"
    ]

    for sent in doc.sents:
        sent_text = sent.text.capitalize()

        # 🟢 Buscar si la frase contiene palabras clave de cada categoría
        if any(word in sent.text for word in keywords_urgencia):
            observaciones.append(f"🚨 **¡URGENTE!** {sent_text}")
        elif any(word in sent.text for word in keywords_pendientes):
            observaciones.append(f"🔹 **Pendiente:** {sent_text}")
        elif any(word in sent.text for word in keywords_validacion):
            observaciones.append(f"🟠 **Validación requerida:** {sent_text}")
        elif any(word in sent.text for word in keywords_revision):
            observaciones.append(f"🔍 **Revisión pendiente:** {sent_text}")

    return " | ".join(observaciones) if observaciones else "✅ Sin observaciones relevantes."


def determinar_franja_horaria(hora_envio):
    """
    Determina la franja horaria basada en la hora del mensaje.
    Se aplica un margen de 20 minutos después del cambio de turno.
    """
    hora = hora_envio if isinstance(hora_envio, int) else hora_envio.hour

    minutos = hora_envio.minute

    if (6 <= hora < 14) or (hora == 14 and minutos <= 20):
        return "Mañana"
    elif (14 <= hora < 21) or (hora == 21 and minutos <= 20):
        return "Tarde"
    else:  # De 21:00 a 6:00 (incluye margen hasta 6:20)
        if (hora == 21 and minutos > 20) or (hora < 6) or (hora == 6 and minutos <= 20):
            return "Noche"

    return "Desconocido"  # Esto no debería ocurrir, pero es una capa de seguridad.



def analizar_message_ia(message, usuario, fecha, fecha_actual, destinatario, cc_list, df, fecha_timestamp):

    # Extraer la hora de la fecha actual
    hora_envio = fecha_actual.hour  

    # 📌 Determinar franja horaria
    franja_horaria = determinar_franja_horaria(fecha_actual)

    # Convertimos la fecha del mensaje a objeto datetime
    fecha_envio = datetime.fromtimestamp(fecha_timestamp)

    # 📌 Agregar franja horaria a la tabla auxiliar
    nueva_fila = {
        "Usuario": usuario,
        "Fecha": fecha_envio.strftime("%d-%m-%Y %H:%M"),
        "Franja Horaria": franja_horaria,  # Se agrega la franja horaria aquí
        "Mensaje": message.text
    }

    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)

    if not hasattr(message, "text") or not message.text:
        return None

    mensaje_texto = message.text
    lineas = mensaje_texto.split("\n")

    actividades = []
    actividad_actual = None
    seccion_actual = "ENTREGA DE TURNO"

    numero_mes = fecha.month
    nombre_mes = meses_espanol[numero_mes]

    for linea in lineas:
        linea = linea.strip()

        # 🔍 Detección de secciones
        if "ENTREGA DE TURNO" in linea.upper():
            seccion_actual = "ENTREGA DE TURNO"
            continue
        elif "PENDIENTES" in linea.upper():
            seccion_actual = "PENDIENTES"
            actividades.append({
                "TK": "",
                "CATEGORIA": "SECCIÓN",
                "IMPACTO": "",
                "ACTIVIDAD": "PENDIENTES",
                "STATUS": "",
                "OBSERVACION": "",
                "Escalado": "",
                "Revisado por": "",
                "Franja Horaria": "",
                "DIA": "",
                "MES": "",
                "AÑO": ""
            })
            continue

        # 🔍 Nueva actividad
        if linea.startswith("*"):
            if actividad_actual:
                actividades.append(actividad_actual)

            actividad_actual = {
                "TK": "N/A",
                "CATEGORIA": "Pendiente" if seccion_actual == "PENDIENTES" else "Evento/Solicitud",
                "IMPACTO": "Bajo",
                "ACTIVIDAD": linea[1:].strip(),
                "STATUS": "Pendiente" if seccion_actual == "PENDIENTES" else "En proceso",
                "OBSERVACION": "",
                "Escalado": "Escalado" if any(word in linea.lower() for word in ["escalado", "escalar", "remitido", "transferido", "derivado"]) else "Solucionado por el área",
                "Revisado por": usuario,
                "Franja Horaria": franja_horaria,  # 📌 Se asigna correctamente aquí
                "DIA": fecha.day,
                "MES": nombre_mes,
                "AÑO": fecha.year
            }
        elif actividad_actual:
            actividad_actual["ACTIVIDAD"] += f"<br>{linea}"

        if actividad_actual:
            actividad_actual["STATUS"] = clasificar_status(actividad_actual["ACTIVIDAD"])
            actividad_actual["OBSERVACION"] = extraer_observaciones(actividad_actual["ACTIVIDAD"])

         # 🔍 Validación de escalado
    keywords_escalado = [
        "escalado", "escalar", "remitido", "transferido", "derivado",
        "pasado a otro equipo", "reportado a otro área", "asignado a otro grupo"
    ]

    if any(word in actividad_actual["ACTIVIDAD"].lower() for word in keywords_escalado):
        actividad_actual["Escalado"] = "Escalado"
    elif actividad_actual["STATUS"].lower() in ["cerrado", "resuelto", "finalizado", "completado"]:
        actividad_actual["Escalado"] = "Solucionado por el área"


    if actividad_actual:
        actividades.append(actividad_actual)

    df = pd.DataFrame(actividades)
    return df if not df.empty else None