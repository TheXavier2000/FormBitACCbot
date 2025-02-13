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
    if any(word in oracion_lower for word in ["cerrado", "finalizado", "resuelto"]):
        return "Cerrado"
    elif any(word in oracion_lower for word in ["pendiente", "validar", "revisar", "falta", "por hacer"]):
        return "En espera"
    elif any(word in oracion_lower for word in ["proceso", "en curso", "trabajando"]):
        return "En proceso"
    else:
        return "En proceso"

def extraer_observaciones(texto):
    """ Genera un resumen de puntos importantes en la columna OBSERVACIÓN """
    doc = nlp(texto.lower())
    observaciones = []

    for sent in doc.sents:
        if any(word in sent.text for word in ["pendiente", "revisar", "validar", "por hacer"]):
            observaciones.append(sent.text.capitalize())

    return " | ".join(observaciones) if observaciones else "N/A"

def analizar_message_ia(message, usuario, fecha, destinatario, cc_list, df):
    if not hasattr(message, "text") or not message.text:
        return None

    mensaje_texto = message.text
    lineas = mensaje_texto.split("\n")

    actividades = []
    actividad_actual = None
    seccion_actual = "ENTREGA DE TURNO"

    numero_mes = datetime.fromtimestamp(fecha).month
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
                "Escalado": "No",
                "Revisado por": usuario,
                "Franja Horaria": "",
                "DIA": datetime.fromtimestamp(fecha).day,
                "MES": nombre_mes,
                "AÑO": datetime.fromtimestamp(fecha).year
            }
        elif actividad_actual:
            actividad_actual["ACTIVIDAD"] += f"<br>{linea}"

        if actividad_actual:
            actividad_actual["STATUS"] = clasificar_status(actividad_actual["ACTIVIDAD"])
            actividad_actual["OBSERVACION"] = extraer_observaciones(actividad_actual["ACTIVIDAD"])

    if actividad_actual:
        actividades.append(actividad_actual)

    df = pd.DataFrame(actividades)
    return df if not df.empty else None
