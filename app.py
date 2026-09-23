"""
app.py
------
Interfaz web con Streamlit. Solo se encarga de mostrar cosas y recoger
la interacción del usuario; toda la lógica pesada vive en analyzer.py.
"""

import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd

from analyzer import analizar_log

# Carga las variables del archivo .env (como GROQ_API_KEY) al entorno.
# Así nunca escribes la clave directamente en el código.
load_dotenv()

st.set_page_config(page_title="Analizador de Logs con IA", page_icon="🛠️")

st.title("🛠️ Analizador de Logs con IA")
st.write(
    "Sube un archivo de log y la IA identificará los errores, su severidad "
    "y una sugerencia de solución, como apoyo a la resolución de incidencias."
)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.warning("No se ha encontrado GROQ_API_KEY. Configúrala en tu archivo .env")

archivo = st.file_uploader("Archivo de log (.log o .txt)", type=["log", "txt"])

if archivo is not None:
    contenido = archivo.read().decode("utf-8", errors="ignore")

    with st.expander("Ver contenido del log original"):
        st.text(contenido)

    if st.button("Analizar log con IA", type="primary", disabled=not api_key):
        with st.spinner("Analizando líneas relevantes con el modelo..."):
            resultados = analizar_log(contenido, api_key)

        if not resultados:
            st.success("No se han detectado líneas de error o aviso en este log.")
        else:
            st.subheader(f"Se han encontrado {len(resultados)} líneas a revisar")

            # Mostramos cada resultado como una tarjeta, coloreada según severidad
            colores = {
                "critica": "🔴", "alta": "🟠", "media": "🟡",
                "baja": "🟢", "desconocida": "⚪",
            }

            for r in resultados:
                icono = colores.get(r["severidad"].lower(), "⚪")
                with st.container(border=True):
                    st.code(r["linea_original"], language="text")
                    st.markdown(f"**{icono} Severidad:** {r['severidad']}")
                    st.markdown(f"**Causa probable:** {r['causa_probable']}")
                    st.markdown(f"**Sugerencia:** {r['sugerencia']}")

            # Botón para descargar el informe completo en CSV,
            # útil para adjuntarlo a un ticket o compartirlo con el equipo.
            df = pd.DataFrame(resultados)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar informe en CSV",
                data=csv,
                file_name="informe_incidencias.csv",
                mime="text/csv",
            )
