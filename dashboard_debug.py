import streamlit as st
import os

st.title("Debug Mode 🟢")
st.write("If you see this, Streamlit is working correctly!")
st.write(f"Listening on Port: {os.environ.get('PORT', 'Unknown')}")
st.write("Environment Variables:")
st.write(os.environ)
