import streamlit as st

st.set_page_config(page_title="Sistema Centurion", layout="centered")

st.title("🏭 Control de Producción - Centurion")
st.write("Seleccioná una opción para navegar:")

col1, col2 = st.columns(2)

with col1:
    # IMPORTANTE: La ruta ahora debe incluir 'pages/' y el nuevo nombre
    if st.button("🚀 Ver Monitor", use_container_width=True):
        st.switch_page("pages/01_Monitor.py")

with col2:
    # IMPORTANTE: La ruta ahora debe incluir 'pages/' y el nuevo nombre
    if st.button("📋 Cargar Orden", use_container_width=True):
        st.switch_page("pages/02_Formulario.py")
