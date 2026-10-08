import glob
import hashlib
import os
import time

import cv2
import numpy as np
import pytesseract
import streamlit as st
from googletrans import Translator
from gtts import gTTS
from PIL import Image

# ---------------------------------------------------------------------------
# Configuración de la página y estilos
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Lector de etiquetas de productos",
    page_icon="🛒",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap');

    html, body, [class*="css"], .stMarkdown, .stButton button {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Fraunces', serif !important;
        letter-spacing: -0.01em;
    }
    .block-container { padding-top: 2.5rem; max-width: 1150px; }

    /* Botón principal */
    .stButton button[kind="primary"], .stButton button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.4rem;
    }

    /* Caja del texto reconocido */
    .ocr-box {
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-left: 4px solid #1f7a6d;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        white-space: pre-wrap;
        line-height: 1.6;
        min-height: 140px;
    }
    .ocr-empty { opacity: 0.6; font-style: italic; }

    section[data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,0.2); }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Datos de apoyo
# ---------------------------------------------------------------------------
IDIOMAS = {
    "Inglés": "en",
    "Español": "es",
    "Bengalí": "bn",
    "Coreano": "ko",
    "Mandarín": "zh-cn",
    "Japonés": "ja",
}

ACENTOS = {
    "Por defecto": "com",
    "India": "co.in",
    "Reino Unido": "co.uk",
    "Estados Unidos": "com",
    "Canadá": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za",
}

os.makedirs("temp", exist_ok=True)
translator = Translator()


# ---------------------------------------------------------------------------
# Funciones
# ---------------------------------------------------------------------------
def text_to_speech(input_language, output_language, text, tld):
    translation = translator.translate(text, src=input_language, dest=output_language)
    trans_text = translation.text
    tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
    # Nombre de archivo seguro (el texto puede traer saltos de línea o símbolos)
    my_file_name = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
    tts.save(f"temp/{my_file_name}.mp3")
    return my_file_name, trans_text


def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    now = time.time()
    for f in mp3_files:
        if os.stat(f).st_mtime < now - n * 86400:
            os.remove(f)


def run_ocr(pil_or_array):
    return pytesseract.image_to_string(pil_or_array).strip()


remove_files(7)

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Ajustes")

    st.subheader("Cámara")
    filtro = st.radio(
        "Invertir colores de la foto",
        ("Sí", "No"),
        index=1,
        horizontal=True,
        help="Útil si la etiqueta tiene letras claras sobre fondo oscuro.",
    )

    st.divider()
    st.subheader("Traducción")
    in_lang = st.selectbox("Idioma de la etiqueta", list(IDIOMAS), index=0)
    out_lang = st.selectbox("Traducir a", list(IDIOMAS), index=1)
    english_accent = st.selectbox(
        "Acento de la voz",
        list(ACENTOS),
        help="Solo afecta cuando el idioma de salida es inglés.",
    )
    display_output_text = st.checkbox("Mostrar la traducción escrita", value=True)

input_language = IDIOMAS[in_lang]
output_language = IDIOMAS[out_lang]
tld = ACENTOS[english_accent]

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.title("Lector de etiquetas de productos")
st.write(
    "Fotografía la etiqueta de un producto del supermercado, lee su letra pequeña "
    "(ingredientes, fecha de vencimiento, información nutricional) y escúchala traducida."
)

# ---------------------------------------------------------------------------
# 1. Fuente de la imagen
# ---------------------------------------------------------------------------
st.subheader("1. Fotografía la etiqueta")

tab_upload, tab_cam = st.tabs(["Subir foto", "Usar cámara"])

image_rgb = None  # imagen final (RGB) que se enviará al OCR

with tab_upload:
    bg_image = st.file_uploader("Sube una foto de la etiqueta", type=["png", "jpg", "jpeg"])
    if bg_image is not None:
        pil_img = Image.open(bg_image).convert("RGB")
        image_rgb = np.array(pil_img)

with tab_cam:
    img_file_buffer = st.camera_input("Toma una foto de la etiqueta")
    if img_file_buffer is not None:
        bytes_data = img_file_buffer.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        if filtro == "Sí":
            cv2_img = cv2.bitwise_not(cv2_img)
        image_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

# ---------------------------------------------------------------------------
# 2. Texto reconocido
# ---------------------------------------------------------------------------
st.subheader("2. Letra pequeña de la etiqueta")

text = ""
if image_rgb is not None:
    with st.spinner("Leyendo la etiqueta..."):
        text = run_ocr(image_rgb)

    col_img, col_text = st.columns(2, gap="large")
    with col_img:
        st.image(image_rgb, caption="Foto de la etiqueta", use_container_width=True)
    with col_text:
        if text:
            safe_text = text.replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(f'<div class="ocr-box">{safe_text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="ocr-box ocr-empty">No se pudo leer la etiqueta. '
                "Acércate más, evita los reflejos del empaque, enfoca bien o prueba invertir los colores.</div>",
                unsafe_allow_html=True,
            )
else:
    st.info("Sube o toma una foto de la etiqueta para empezar.")

# ---------------------------------------------------------------------------
# 3. Traducción y audio
# ---------------------------------------------------------------------------
st.subheader("3. Traduce y escucha la etiqueta")

if st.button("Traducir y escuchar etiqueta", type="primary", disabled=not text):
    try:
        with st.spinner("Traduciendo la etiqueta y generando el audio..."):
            result, output_text = text_to_speech(
                input_language, output_language, text, tld
            )
            with open(f"temp/{result}.mp3", "rb") as audio_file:
                audio_bytes = audio_file.read()

        st.markdown("### Audio de la etiqueta")
        st.audio(audio_bytes, format="audio/mp3", start_time=0)
        st.download_button(
            "Descargar audio (.mp3)",
            data=audio_bytes,
            file_name=f"{result}.mp3",
            mime="audio/mp3",
        )

        if display_output_text:
            st.markdown("### Traducción de la etiqueta")
            st.write(output_text)
    except Exception as e:
        st.error(f"No se pudo generar el audio: {e}")
elif not text:
    st.caption("El botón se activa cuando se lea texto de la etiqueta.")
