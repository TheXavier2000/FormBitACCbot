import re 
import spacy
import calendar
import pandas as pd
from datetime import datetime
from transformers import pipeline
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
from generar_csv import generar_csv_con_formato
 

# Cargar modelo de NLP en español
nlp = spacy.load("es_core_news_md")

# Clasificador de texto con IA
clasificador = pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")

def obtener_franja_horaria(hora):
    if 5 <= hora < 13:
        return "Mañana"
    elif 13 <= hora < 19:
        return "Tarde"
    else:
        return "Noche"

def clasificar_categoria(oracion):
    oracion_lower = oracion.lower()
    if any(word in oracion_lower for word in ["error", "fallo", "no funciona", "problema", "incidente", "bug"]):
        return "Incidente"
    elif any(word in oracion_lower for word in ["mejorar", "actualizar", "solicitud", "nuevo", "implementación", "actualización"]):
        return "Evento/Solicitud"
    elif any(word in oracion_lower for word in ["afectación general", "degradación", "crítico", "fallo masivo"]):
        return "Problema"
    else:
        return "Evento/Solicitud"

def clasificar_impacto(oracion):
    oracion_lower = oracion.lower()
    if any(word in oracion_lower for word in ["crítico", "urgente", "afectación total", "prioridad alta"]):
        return "Alto"
    elif any(word in oracion_lower for word in ["degradado", "lento", "afectación parcial", "intermitente"]):
        return "Medio"
    else:
        return "Bajo"

def clasificar_status(oracion):
    oracion_lower = oracion.lower()
    if any(word in oracion_lower for word in ["cerrado", "finalizado", "completado"]):
        return "Cerrado"
    elif any(word in oracion_lower for word in ["espera", "pendiente", "pausado", "tener en cuenta", "validar", "terminar"]):
        return "En espera"
    elif any(word in oracion_lower for word in ["proceso", "trabajando en", "en curso"]):
        return "En proceso"
    elif any(word in oracion_lower for word in ["resuelto", "corregido", "solucionado"]):
        return "Resuelto"
    elif any(word in oracion_lower for word in ["escalado", "derivado"]):
        return "Escalado"
    else:
        return "En proceso"

def analizar_mensaje_ia(mensaje, usuario, fecha):
    doc = nlp(mensaje)
    actividades = []
    hora = fecha.hour
    franja_horaria = obtener_franja_horaria(hora)
    nombre_mes = calendar.month_name[fecha.month].capitalize()

    lineas = mensaje.split("\n")
    actividad_actual = None  

    for linea in lineas:
        linea = linea.strip()

        if linea.startswith("*"):
            if actividad_actual:
                actividades.append(actividad_actual)
            
            actividad_actual = {
                "TK": "N/A",
                "CATEGORIA": "Evento/Solicitud",
                "IMPACTO": "Bajo",
                "ACTIVIDAD": linea[1:].strip(),  
                "STATUS": "En proceso",
                "OBSERVACION": "N/A",
                "Escalado": "No",
                "Revisado por": usuario,
                "Franja Horaria": franja_horaria,
                "DIA": fecha.day,
                "MES": nombre_mes,
                "AÑO": fecha.year
            }
        elif linea.startswith("-") and actividad_actual:
            sub_actividad = linea[1:].strip()
            actividad_actual["ACTIVIDAD"] += f"\n{sub_actividad}"

        if actividad_actual:
            categoria = clasificar_categoria(actividad_actual["ACTIVIDAD"])
            impacto = clasificar_impacto(actividad_actual["ACTIVIDAD"])
            status = clasificar_status(actividad_actual["ACTIVIDAD"])

            actividad_actual["CATEGORIA"] = categoria
            actividad_actual["IMPACTO"] = impacto
            actividad_actual["STATUS"] = status

            match = re.search(r'\b(tk|ticket|caso|#|id)\s*(\d+)', actividad_actual["ACTIVIDAD"], re.IGNORECASE)
            if match:
                actividad_actual["TK"] = match.group(2)

            if "escalado a" in actividad_actual["ACTIVIDAD"].lower() or "derivado a" in actividad_actual["ACTIVIDAD"].lower():
                actividad_actual["Escalado"] = "Sí"

    if actividad_actual:
        actividades.append(actividad_actual)

    df = pd.DataFrame(actividades)
    generar_csv_con_formato(df)
    return df
