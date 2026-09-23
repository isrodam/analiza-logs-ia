# Analizador de Logs con IA

Herramienta que analiza archivos de log, detecta líneas de error/aviso
mediante reglas, y usa un modelo de lenguaje (LLM) para explicar la causa
probable, asignar una severidad y sugerir una solución — pensado como
apoyo directo a tareas de sistemas: monitorización, análisis de logs y
resolución de incidencias.

## Arquitectura (por qué está hecho así)

```
sample_logs/sample.log  →  analyzer.py  →  app.py (Streamlit)
                           (filtra +            (interfaz,
                            llama al LLM)         descarga CSV)
```

- **analyzer.py**: toda la lógica, sin nada de interfaz. Primero filtra
  con reglas simples (palabras clave como ERROR, WARNING, CRITICAL) para
  no gastar llamadas a la IA en líneas normales. Solo las líneas
  relevantes se mandan al LLM, pidiéndole una respuesta en JSON
  estructurado (no texto libre) para poder procesarla como datos.
- **app.py**: solo interfaz. Sube el archivo, muestra los resultados
  como tarjetas con color según severidad, y permite descargar un CSV
  (pensado para adjuntar a un ticket o pasarlo al equipo).

## Cómo ejecutarlo

1. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```
2. Copia `.env.example` como `.env` y añade tu clave gratuita de
   [Groq](https://console.groq.com).
3. Lanza la app:
   ```
   streamlit run app.py
   ```
4. Sube `sample_logs/sample.log` para probarlo con datos de ejemplo.

## Posibles mejoras (para mencionar en entrevista como "siguientes pasos")

- Dockerizar la aplicación (`Dockerfile` + `docker-compose`) para
  desplegarla igual en cualquier entorno.
- Añadir un GitHub Action que ejecute tests básicos en cada push.
- Sustituir el filtrado por palabras clave por expresiones regulares
  más específicas por tipo de servidor (Nginx, Apache, aplicación).
- Guardar el histórico de incidencias en una base de datos en vez de
  solo exportarlo a CSV.
