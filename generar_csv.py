import spacy
import logging
import pandas as pd
from datetime import datetime

# Cargar modelo de NLP
nlp = spacy.load("es_core_news_md")

# Lista manual de meses en español
meses_espanol = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

def obtener_franja_horaria(hora):
    if 5 <= hora < 13:
        return "Mañana"
    elif 13 <= hora < 19:
        return "Tarde"
    else:
        return "Noche"

def clasificar_status(oracion):
    oracion_lower = oracion.lower()
    if any(word in oracion_lower for word in ["cerrado", "finalizado"]):
        return "Cerrado"
    elif any(word in oracion_lower for word in ["pendiente", "validar", "terminar", "tener en cuenta"]):
        return "En espera"
    elif any(word in oracion_lower for word in ["proceso", "trabajando"]):
        return "En proceso"
    else:
        return "En proceso"

def analizar_message_ia(message, usuario, fecha):
    if not hasattr(message, "text") or not message.text:
        return pd.DataFrame()

    mensaje_texto = message.text
    doc = nlp(mensaje_texto)
    actividades = []
    hora = datetime.fromtimestamp(fecha).hour
    franja_horaria = obtener_franja_horaria(hora)

    # Obtener el mes en español
    numero_mes = datetime.fromtimestamp(fecha).month
    nombre_mes = meses_espanol[numero_mes]

    lineas = mensaje_texto.split("\n")
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
                "DIA": datetime.fromtimestamp(fecha).day,
                "MES": nombre_mes,  # ✅ Ahora el mes aparece en español
                "AÑO": datetime.fromtimestamp(fecha).year
            }

        if actividad_actual:
            actividad_actual["STATUS"] = clasificar_status(actividad_actual["ACTIVIDAD"])

    if actividad_actual:
        actividades.append(actividad_actual)

    df = pd.DataFrame(actividades)
    
    return df
