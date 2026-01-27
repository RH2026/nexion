import streamlit as st

st.write("🚀 La app arrancó correctamente")

with st.expander("Form de prueba"):
    with st.form("form_test"):
        st.text_input("Código")
        st.form_submit_button("Enviar")


































