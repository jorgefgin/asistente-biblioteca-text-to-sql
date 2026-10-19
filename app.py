import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(page_title="Asistente de Biblioteca IA", layout="centered")
st.title("Asistente Inteligente de Biblioteca")
st.markdown("Haz preguntas en lenguaje natural sobre el catálogo de más de **2,3 millones de libros**.")

with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Introduce tu Google API Key:", type="password")
    st.markdown("---")
    st.markdown("**Ejemplos de preguntas:**")
    st.caption("• ¿Cuáles son los 5 libros más antiguos y de qué año son?")
    st.caption("• ¿Cuáles son los 5 autores con más libros?")
    st.caption("• ¿Cuántos libros hay publicados desde el año 2000?")

if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    db = SQLDatabase.from_uri("sqlite:///biblioteca.db")
    llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0)
    cadena_texto = llm | StrOutputParser()

    pregunta = st.text_input("Escribe tu pregunta:", placeholder="Ej: ¿Cuáles son los libros más antiguos?")

    if st.button("Consultar catálogo") and pregunta:
        with st.spinner("Generando consulta SQL y buscando en la base de datos..."):
            try:
                schema = db.get_table_info()

                prompt_sql = f"""
                Basándote en el siguiente esquema de base de datos SQLite:
                {schema}

                REGLAS CRÍTICAS DE LA BASE DE DATOS:
                1. En 'fecha_de_publicacion', el valor -99999 es nulo y los números menores a 1500 (como 9, 20, 130) son errores tipográficos de catalogación. SIEMPRE que busques libros antiguos, ordenes fechas o hagas cálculos temporales, filtra únicamente años históricos reales usando: WHERE fecha_de_publicacion BETWEEN 1500 AND 2026.
                2. En columnas de texto, 'Desconocido', 'Desconocida', 'Sin serie' y 'Sin mención de autores' representan valores nulos. Exclúyelos siempre que te pidan rankings, conteos o listas (ej. WHERE autores != 'Desconocido').

                Escribe únicamente una consulta SQL válida de SQLite que responda a esta pregunta: "{pregunta}"
                No incluyas explicaciones ni bloques markdown, solo la sentencia SELECT limpia.
                """
                sql_query = cadena_texto.invoke(prompt_sql).replace("```sql", "").replace("```", "").strip()

                with st.expander("Ver consulta SQL generada"):
                    st.code(sql_query, language="sql")

                resultado_db = db.run(sql_query)

                with st.expander("Ver datos crudos de SQLite"):
                    st.write(resultado_db)

                prompt_respuesta = f"""
                Pregunta del usuario: "{pregunta}"
                Consulta SQL ejecutada: {sql_query}
                Resultado de la base de datos: {resultado_db}

                Responde a la pregunta del usuario en español de forma clara, natural y directa basándote en el resultado.
                """
                respuesta_final = cadena_texto.invoke(prompt_respuesta)

                st.success("¡Respuesta encontrada!")
                st.markdown(f"### Resultado:\n{respuesta_final}")

            except Exception as e:
                st.error(f"Ocurrió un error al procesar la consulta: {e}")
else:
    st.info("Por favor, pega tu Google API Key en el menú de la izquierda para activar el asistente.")
