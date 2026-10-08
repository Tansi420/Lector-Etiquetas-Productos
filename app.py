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
    page_title="Reconocimiento Óptico de Caracteres",
    page_icon="🔎",
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
        help="Útil si el texto es claro sobre fondo oscuro.",
    )

    st.divider()
    st.subheader("Traducción")
    in_lang = st.selectbox("Idioma del texto", list(IDIOMAS), index=0)
    out_lang = st.selectbox("Traducir a", list(IDIOMAS), index=1)
    english_accent = st.selectbox(
        "Acento de la voz",
        list(ACENTOS),
        help="Solo afecta cuando el idioma de salida es inglés.",
    )
    display_output_text = st.checkbox("Mostrar el texto traducido", value=True)

input_language = IDIOMAS[in_lang]
output_language = IDIOMAS[out_lang]
tld = ACENTOS[english_accent]

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.title("Reconocimiento Óptico de Caracteres")
st.write(
    "Toma una foto o sube una imagen, extrae el texto y escúchalo traducido."
)

# ---------------------------------------------------------------------------
# 1. Fuente de la imagen
# ---------------------------------------------------------------------------
st.subheader("1. Elige la imagen")

tab_upload, tab_cam = st.tabs(["Cargar archivo", "Usar cámara"])

image_rgb = None  # imagen final (RGB) que se enviará al OCR

with tab_upload:
    bg_image = st.file_uploader("Cargar imagen", type=["png", "jpg", "jpeg"])
    if bg_image is not None:
        pil_img = Image.open(bg_image).convert("RGB")
        image_rgb = np.array(pil_img)

with tab_cam:
    img_file_buffer = st.camera_input("Toma una foto")
    if img_file_buffer is not None:
        bytes_data = img_file_buffer.getvalue()
        cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        if filtro == "Sí":
            cv2_img = cv2.bitwise_not(cv2_img)
        image_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

# ---------------------------------------------------------------------------
# 2. Texto reconocido
# ---------------------------------------------------------------------------
st.subheader("2. Texto reconocido")

text = ""
if image_rgb is not None:
    with st.spinner("Leyendo el texto de la imagen..."):
        text = run_ocr(image_rgb)

    col_img, col_text = st.columns(2, gap="large")
    with col_img:
        st.image(image_rgb, caption="Imagen que se procesó", use_container_width=True)
    with col_text:
        if text:
            safe_text = text.replace("<", "&lt;").replace(">", "&gt;")
            st.markdown(f'<div class="ocr-box">{safe_text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="ocr-box ocr-empty">No se encontró texto. '
                "Prueba con una imagen más nítida o cambia el filtro de la cámara.</div>",
                unsafe_allow_html=True,
            )
else:
    st.info("Carga una imagen o toma una foto para empezar.")

# ---------------------------------------------------------------------------
# 3. Traducción y audio
# ---------------------------------------------------------------------------
st.subheader("3. Traducir y escuchar")

if st.button("Traducir y generar audio", type="primary", disabled=not text):
    try:
        with st.spinner("Traduciendo y generando el audio..."):
            result, output_text = text_to_speech(
                input_language, output_language, text, tld
            )
            with open(f"temp/{result}.mp3", "rb") as audio_file:
                audio_bytes = audio_file.read()

        st.markdown("### Tu audio")
        st.audio(audio_bytes, format="audio/mp3", start_time=0)
        st.download_button(
            "Descargar audio (.mp3)",
            data=audio_bytes,
            file_name=f"{result}.mp3",
            mime="audio/mp3",
        )

        if display_output_text:
            st.markdown("### Texto traducido")
            st.write(output_text)
    except Exception as e:
        st.error(f"No se pudo generar el audio: {e}")
elif not text:
    st.caption("El botón se activa cuando haya texto reconocido.")
