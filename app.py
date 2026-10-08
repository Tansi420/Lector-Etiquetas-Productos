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
    st.caption("El botón se activa cuando haya texto reconocido.")    /* Botón principal */
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
    st.caption("El botón se activa cuando haya texto reconocido.")        --amber: #F2A541;
        --muted: #5B6B82;
        --line: #D5DEE8;
    

    html, body, [class*="css"], .stApp {
        font-family: 'Source Sans 3', sans-serif;
        color: var(--ink);
    }
    .stApp { background: var(--paper); }

    h1, h2, h3, h4 { font-family: 'Sora', sans-serif; color: var(--ink); letter-spacing: -0.01em; }

    /* Encabezado */
    .hero {
        background: var(--ink);
        color: #fff;
        border-radius: 20px;
        padding: 2.2rem 2rem 2rem 2rem;
        margin-bottom: 1.6rem;
        border-bottom: 6px solid var(--amber);
    }
    .hero h1 { color: #fff; font-size: 2.1rem; margin: 0 0 .5rem 0; line-height: 1.15; }
    .hero p  { color: #C9D4E5; font-size: 1.08rem; margin: 0; max-width: 34rem; }

    /* Encabezado de cada paso */
    .step { display: flex; align-items: center; gap: .8rem; margin: .2rem 0 .6rem 0; }
    .step .num {
        background: var(--teal); color: #fff; font-family: 'Sora', sans-serif; font-weight: 700;
        width: 2.1rem; height: 2.1rem; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .step .title { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 1.25rem; }
    .step .hint { color: var(--muted); font-size: .98rem; margin: 0 0 .6rem 2.9rem; }

    /* Tarjetas (contenedores con borde) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card);
        border: 1px solid var(--line) !important;
        border-radius: 16px;
        padding: .6rem .5rem;
    }

    /* Botones */
    .stButton > button {
        background: var(--teal); color: #fff; border: none; border-radius: 12px;
        font-family: 'Sora', sans-serif; font-weight: 500;
        padding: .65rem 1.4rem; width: 100%;
        transition: background .15s ease;
    }
    .stButton > button:hover { background: var(--teal-dark); color: #fff; }
    .stButton > button:focus-visible { outline: 3px solid var(--amber); outline-offset: 2px; }

    /* Subida de archivos */
    section[data-testid="stFileUploaderDropzone"] {
        border: 2px dashed var(--teal); border-radius: 14px; background: #F6FBFA;
    }

    /* Área de texto */
    textarea { border-radius: 12px !important; font-size: 1.02rem !important; }

    /* Barra lateral */
    section[data-testid="stSidebar"] { background: #E2E9F1; border-right: 1px solid var(--line); }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { font-size: 1.1rem; }

    /* Resultado traducido */
    .result {
        background: #FFF7E8; border-left: 5px solid var(--amber);
        border-radius: 10px; padding: 1rem 1.2rem; font-size: 1.1rem; line-height: 1.55;
    }

    #MainMenu, footer { visibility: hidden; }

    @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def step(num, title, hint=""):
    st.markdown(
        f'<div class="step"><div class="num">{num}</div><div class="title">{title}</div></div>'
        + (f'<p class="hint">{hint}</p>' if hint else ""),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Lógica
# ---------------------------------------------------------------------------
os.makedirs("temp", exist_ok=True)
translator = Translator()


def text_to_speech(input_language, output_language, text, tld):
    translation = translator.translate(text, src=input_language, dest=output_language)
    trans_text = translation.text
    tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
    my_file_name = "".join(c for c in text[:20] if c.isalnum()) or "audio"
    tts.save(f"temp/{my_file_name}.mp3")
    return my_file_name, trans_text


def remove_files(n):
    now = time.time()
    for f in glob.glob("temp/*mp3"):
        if os.stat(f).st_mtime < now - n * 86400:
            os.remove(f)


remove_files(7)

LANGS = {
    "Inglés": "en",
    "Español": "es",
    "Bengalí": "bn",
    "Coreano": "ko",
    "Mandarín": "zh-cn",
    "Japonés": "ja",
}
ACCENTS = {
    "Predeterminado": "com",
    "India": "co.in",
    "Reino Unido": "co.uk",
    "Estados Unidos": "com",
    "Canadá": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za",
}

# ---------------------------------------------------------------------------
# Barra lateral: ajustes
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Idiomas")
    in_lang = st.selectbox("Idioma del texto en la imagen", list(LANGS), index=0)
    out_lang = st.selectbox("Traducir a", list(LANGS), index=1)

    st.subheader("Voz")
    accent = st.selectbox("Acento (útil para inglés)", list(ACCENTS))
    show_text = st.checkbox("Mostrar el texto traducido", value=True)

    st.subheader("Cámara")
    invert = st.toggle("Invertir colores de la foto", value=False,
                       help="Ayuda cuando el texto es claro sobre fondo oscuro.")

input_language = LANGS[in_lang]
output_language = LANGS[out_lang]
tld = ACCENTS[accent]

# ---------------------------------------------------------------------------
# Encabezado
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>Del papel a tu idioma, con voz</h1>
        <p>Sube una foto o usa la cámara. Extraemos el texto, lo traducimos y lo leemos en voz alta.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Paso 1: imagen
# ---------------------------------------------------------------------------
text = ""
img_rgb = None

with st.container(border=True):
    step(1, "Elige tu imagen", "Sube un archivo o toma una foto con la cámara.")

    cam_ = st.checkbox("Usar cámara")
    img_file_buffer = st.camera_input("Toma una foto") if cam_ else None
    bg_image = st.file_uploader("Cargar imagen", type=["png", "jpg", "jpeg"])

    if bg_image is not None:
        st.image(bg_image, caption="Imagen cargada", use_container_width=True)
        img_rgb = np.array(Image.open(bg_image).convert("RGB"))
    elif img_file_buffer is not None:
        data = np.frombuffer(img_file_buffer.getvalue(), np.uint8)
        cv2_img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if invert:
            cv2_img = cv2.bitwise_not(cv2_img)
        img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

    if img_rgb is not None:
        with st.spinner("Leyendo el texto…"):
            text = pytesseract.image_to_string(img_rgb)

# ---------------------------------------------------------------------------
# Paso 2: texto detectado
# ---------------------------------------------------------------------------
with st.container(border=True):
    step(2, "Revisa el texto", "Puedes corregir cualquier error antes de traducir.")
    if img_rgb is None:
        st.info("Aún no hay imagen. Sube un archivo o activa la cámara en el paso 1.")
    text = st.text_area("Texto detectado", value=text, height=180, label_visibility="collapsed",
                        placeholder="El texto de tu imagen aparecerá aquí.")

# ---------------------------------------------------------------------------
# Paso 3: traducir y escuchar
# ---------------------------------------------------------------------------
with st.container(border=True):
    step(3, "Traduce y escucha", f"{in_lang} → {out_lang}")

    if st.button("Traducir y generar audio"):
        if not text.strip():
            st.warning("No hay texto para traducir. Sube una imagen o escribe el texto en el paso 2.")
        else:
            try:
                with st.spinner("Traduciendo y creando el audio…"):
                    result, output_text = text_to_speech(input_language, output_language, text, tld)
                    with open(f"temp/{result}.mp3", "rb") as f:
                        audio_bytes = f.read()

                st.markdown("#### Tu audio")
                st.audio(audio_bytes, format="audio/mp3", start_time=0)

                if show_text:
                    st.markdown("#### Texto traducido")
                    st.markdown(f'<div class="result">{output_text}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"No se pudo completar la traducción. Revisa tu conexión e inténtalo de nuevo. ({e})")
