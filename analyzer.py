"""
analyzer.py
-----------
Lógica central del proyecto: separada de la interfaz (app.py) a propósito.
Esto se llama "separación de responsabilidades": el archivo de interfaz
solo debe encargarse de mostrar cosas, y este archivo de la lógica.
Así puedes testear o reutilizar analyzer.py sin necesidad de Streamlit.
"""

import os
import re
import json
import requests

# Groq expone una API compatible con el formato de OpenAI,
# por eso la URL y el formato del "payload" (los datos que enviamos)
# se parecen tanto a los que usarías con OpenAI.
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"  # mismo modelo que usasteis en sanse-llm-assistant

# Palabras clave típicas para detectar líneas "interesantes" en un log.
# Esto es una técnica simple (no IA todavía): filtrar con reglas antes
# de gastar llamadas a la IA solo en lo que de verdad importa.
KEYWORDS = ["ERROR", "CRITICAL", "FATAL", "WARN", "WARNING", "Exception", "Traceback"]


def extraer_lineas_relevantes(contenido_log: str) -> list[str]:
    """
    Recorre el log línea a línea y se queda solo con las que
    contienen alguna palabra clave de error/aviso.

    Por qué filtrar antes de llamar a la IA: cada llamada a un LLM
    cuesta tiempo y (en producción) dinero. No tiene sentido analizar
    con IA una línea de log normal tipo "INFO: usuario conectado".
    """
    lineas = contenido_log.splitlines()
    relevantes = [
        linea for linea in lineas
        if any(kw in linea for kw in KEYWORDS) and linea.strip()
    ]
    return relevantes


def construir_prompt(linea_log: str) -> str:
    """
    El "prompt" es simplemente el texto que le mandamos al modelo.
    Aquí le pedimos explícitamente que responda en un formato JSON
    concreto, para poder procesar la respuesta como datos estructurados
    en vez de como texto libre (esto es clave en cualquier pipeline real).
    """
    return f"""Eres un asistente experto en sistemas y DevOps.
Analiza la siguiente línea de log y responde ÚNICAMENTE con un JSON
con esta forma exacta, sin texto adicional ni bloques de código:

{{"causa_probable": "...", "severidad": "baja|media|alta|critica", "sugerencia": "..."}}

Línea de log:
{linea_log}
"""


def llamar_llm(prompt: str, api_key: str) -> dict:
    """
    Llamada HTTP directa a la API de Groq (mismo tipo de llamada que
    harías a OpenAI o Anthropic; el "shape" del JSON es casi idéntico
    en toda la industria, por eso aprenderlo aquí se traslada a otros
    proveedores sin apenas cambios).
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,  # baja temperatura = respuestas más consistentes/predecibles
    }

    respuesta = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    respuesta.raise_for_status()  # lanza un error claro si la API falla (401, 429, etc.)

    texto = respuesta.json()["choices"][0]["message"]["content"]

    # El modelo a veces envuelve el JSON en ```json ... ``` aunque se lo
    # hayamos pedido en texto plano. Lo limpiamos por seguridad.
    texto = texto.strip().removeprefix("```json").removesuffix("```").strip()

    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        # Si el modelo no devuelve JSON válido, no rompemos el programa:
        # devolvemos algo interpretable igualmente.
        return {"causa_probable": "No se pudo interpretar la respuesta", "severidad": "desconocida", "sugerencia": texto}


def analizar_log(contenido_log: str, api_key: str) -> list[dict]:
    """
    Función principal que orquesta todo el flujo:
    1. Filtra líneas relevantes
    2. Para cada una, llama al LLM
    3. Devuelve una lista de resultados listos para mostrar
    """
    lineas = extraer_lineas_relevantes(contenido_log)
    resultados = []

    for linea in lineas:
        prompt = construir_prompt(linea)
        analisis = llamar_llm(prompt, api_key)
        resultados.append({
            "linea_original": linea,
            "causa_probable": analisis.get("causa_probable", ""),
            "severidad": analisis.get("severidad", ""),
            "sugerencia": analisis.get("sugerencia", ""),
        })

    return resultados
