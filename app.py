import glob
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
# Configuración de la página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Lector de imágenes",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap');

    :root {
        --ink: #14213D;
        --paper: #EEF2F6;
        --card: #FFFFFF;
        --teal: #0F9D8A;
        --teal-dark: #0B7A6B;
        --amber: #F2A541;
        --muted: #5B6B82;
        --line: #D5DEE8;
    }

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
                st.error(f"No se pudo completar la traducción. Revisa tu conexión e inténtalo de nuevo. ({e})")}

.stApp {
    background: linear-gradient(145deg, #f5f7ff 0%, #f8f9fc 55%, #f0f4ff 100%);
    color: #202642;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

.hero {
    background: linear-gradient(120deg, #222a66 0%, #5148bd 65%, #8176ed 100%);
    padding: 38px 38px 34px 38px;
    border-radius: 26px;
    color: white;
    margin-bottom: 30px;
    box-shadow: 0 14px 35px rgba(64, 64, 155, 0.18);
}

.hero-tag {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.23);
    border-radius: 30px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 15px;
}

.hero h1 {
    color: white;
    font-size: clamp(30px, 4vw, 43px);
    font-weight: 800;
    letter-spacing: -1.5px;
    line-height: 1.15;
    margin: 0 0 12px 0;
}

.hero p {
    color: #e3e5ff;
    font-size: 16px;
    line-height: 1.7;
    max-width: 650px;
    margin: 0;
}

.section-title {
    color: #242b50;
    font-size: 23px;
    font-weight: 800;
    letter-spacing: -0.6px;
    margin: 12px 0 5px 0;
}

.section-subtitle {
    color: #777f9a;
    font-size: 14px;
    margin-bottom: 22px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.9);
    border: 1px solid #e7eafb;
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 6px 22px rgba(43, 53, 108, 0.045);
}

.stButton > button {
    border: none;
    border-radius: 12px;
    min-height: 45px;
    font-weight: 700;
    background: linear-gradient(110deg, #5148bd, #7468e8);
    color: white;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: linear-gradient(110deg, #40379f, #6256d1);
    color: white;
    box-shadow: 0 5px 15px rgba(81, 72, 189, 0.2);
    transform: translateY(-1px);
}

div[data-testid="stFileUploader"] {
    background: #f8f9ff;
    border: 1.5px dashed #c8cef3;
    border-radius: 16px;
    padding: 12px;
}

div[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #eaecf7;
}

div[data-testid="stSidebar"] h2,
div[data-testid="stSidebar"] h3 {
    color: #292f59;
    font-weight: 800;
}

div[data-testid="stSidebar"] label {
    color: #535b78;
    font-weight: 500;
}

div[data-testid="stAudio"] {
    border-radius: 12px;
}

.result-label {
    color: #5148bd;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 800;
    margin-bottom: 8px;
}

.helper {
    background: #f0f2ff;
    color: #555c8c;
    border-radius: 12px;
    padding: 13px 16px;
    font-size: 13px;
    line-height: 1.6;
    margin: 10px 0 20px 0;
}

.footer {
    color: #9299b0;
    font-size: 12px;
    text-align: center;
    padding-top: 35px;
}

@media (max-width: 640px) {
    .hero {
        padding: 25px 22px;
        border-radius: 20px;
    }
    .block-container {
        padding-top: 1.2rem;
    }
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# FUNCIONES
# --------------------------------------------------

LANGUAGES = {
    "Español": "es",
    "Inglés": "en",
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


def remove_files(days=7):
    """Elimina archivos de audio antiguos."""
    now = time.time()
    for file in glob.glob("temp/*.mp3"):
        try:
            if os.stat(file).st_mtime < now - days * 86400:
                os.remove(file)
        except OSError:
            pass


def extract_text(image_bytes, invert=False):
    """Procesa una imagen y extrae su texto mediante OCR."""
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("No se pudo leer la imagen. Intenta con otro archivo.")

    if invert:
        image = cv2.bitwise_not(image)

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return pytesseract.image_to_string(image_rgb)


def text_to_speech(input_language, output_language, text, tld):
    """Traduce el texto y genera un archivo de audio."""
    translation = translator.translate(
        text,
        src=input_language,
        dest=output_language
    )
    translated_text = translation.text

    audio = gTTS(
        text=translated_text,
        lang=output_language,
        tld=tld,
        slow=False
    )

    filename = hashlib.md5(
        f"{translated_text}{time.time()}".encode("utf-8")
    ).hexdigest() + ".mp3"

    filepath = os.path.join("temp", filename)
    audio.save(filepath)

    return filepath, translated_text


remove_files(7)


# --------------------------------------------------
# ENCABEZADO
# --------------------------------------------------

st.markdown("""
<div class="hero">
    <div class="hero-tag">✦ LECTURA INTELIGENTE</div>
    <h1>Lee lo que antes<br>no podías ver.</h1>
    <p>
        Convierte imágenes en texto, traduce su contenido
        y escúchalo en el idioma que prefieras.
        Todo desde un solo lugar.
    </p>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# BARRA LATERAL: CONFIGURACIÓN
# --------------------------------------------------

with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    st.caption("Personaliza tu experiencia de lectura.")

    st.markdown("---")
    st.markdown("### 📷 Captura de imagen")

    camera_enabled = st.checkbox("Usar cámara")

    camera_filter = st.radio(
        "Filtro para la imagen",
        options=["Original", "Invertir colores"],
        index=0,
        help="Invertir colores puede ayudar con algunos tipos de imágenes."
    )

    st.markdown("---")
    st.markdown("### 🌐 Traducción")

    input_language_name = st.selectbox(
        "Idioma del texto original",
        list(LANGUAGES.keys()),
        index=0
    )

    output_language_name = st.selectbox(
        "Idioma de salida",
        list(LANGUAGES.keys()),
        index=1
    )

    st.markdown("---")
    st.markdown("### 🔊 Voz y audio")

    accent_name = st.selectbox(
        "Acento de la voz",
        list(ACCENTS.keys()),
        index=0
    )

    display_output_text = st.checkbox(
        "Mostrar texto traducido",
        value=True
    )

    st.markdown("---")
    st.caption("Lector inteligente · OCR + traducción + voz")


input_language = LANGUAGES[input_language_name]
output_language = LANGUAGES[output_language_name]
tld = ACCENTS[accent_name]


# --------------------------------------------------
# CONTENIDO PRINCIPAL
# --------------------------------------------------

left_column, right_column = st.columns([1, 1], gap="large")

text = ""
image_bytes = None

with left_column:
    st.markdown(
        '<div class="section-title">01 · Añade una imagen</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-subtitle">Fotografía o carga una imagen '
        'para reconocer su contenido.</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Selecciona una imagen",
            type=["png", "jpg", "jpeg"],
            help="Puedes cargar fotografías, documentos o etiquetas."
        )

        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()

            # Conserva la funcionalidad de guardar el archivo cargado.
            with open(uploaded_file.name, "wb") as file:
                file.write(image_bytes)

            st.image(
                image_bytes,
                caption="Imagen seleccionada",
                use_container_width=True
            )

        elif camera_enabled:
            camera_image = st.camera_input("Toma una fotografía")

            if camera_image is not None:
                image_bytes = camera_image.getvalue()

        else:
            st.markdown("""
            <div class="helper">
                💡 <b>Consejo:</b> busca una buena iluminación,
                mantén la imagen enfocada y procura que el texto
                esté lo más recto posible.
            </div>
            """, unsafe_allow_html=True)

with right_column:
    st.markdown(
        '<div class="section-title">02 · Texto reconocido</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="section-subtitle">El contenido extraído aparecerá aquí.</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        if image_bytes is not None:
            try:
                with st.spinner("Analizando imagen..."):
                    text = extract_text(
                        image_bytes,
                        invert=(camera_filter == "Invertir colores")
                    )

                if text.strip():
                    st.markdown(
                        '<div class="result-label">✓ Texto detectado</div>',
                        unsafe_allow_html=True
                    )
                    text = st.text_area(
                        "Puedes editar el texto antes de traducirlo",
                        value=text,
                        height=240,
                        key="recognized_text"
                    )
                else:
                    st.warning(
                        "No se detectó texto. Intenta con otra imagen "
                        "o mejora la iluminación."
                    )
                    text = ""

            except Exception as error:
                st.error(f"No se pudo procesar la imagen: {error}")
                text = ""
        else:
            st.markdown("""
            <div class="helper">
                <b>Tu texto aparecerá aquí.</b><br><br>
                1. Carga una imagen o toma una fotografía.<br>
                2. Espera a que termine el reconocimiento.<br>
                3. Revisa el texto y edítalo si es necesario.
            </div>
            """, unsafe_allow_html=True)

            text = st.text_area(
                "O escribe o pega un texto manualmente",
                value="",
                height=150,
                key="manual_text"
            )


# --------------------------------------------------
# TRADUCCIÓN Y GENERACIÓN DE AUDIO
# --------------------------------------------------

st.markdown("---")
st.markdown(
    '<div class="section-title">03 · Escucha tu texto</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="section-subtitle">Genera una versión hablada '
    'del texto en el idioma seleccionado.</div>',
    unsafe_allow_html=True
)

audio_column, info_column = st.columns([1, 1], gap="large")

with audio_column:
    with st.container(border=True):
        st.markdown("### 🎧 Tu audio")

        if st.button(
            "✦ Traducir y generar audio",
            use_container_width=True,
            type="primary"
        ):
            if not text.strip():
                st.warning("Primero añade una imagen o escribe un texto.")
            else:
                try:
                    with st.spinner("Traduciendo y generando tu audio..."):
                        audio_path, output_text = text_to_speech(
                            input_language,
                            output_language,
                            text,
                            tld
                        )

                    st.success("¡Tu audio está listo!")

                    with open(audio_path, "rb") as audio_file:
                        st.audio(
                            audio_file.read(),
                            format="audio/mp3"
                        )

                    if display_output_text:
                        st.markdown("#### Texto traducido")
                        st.text_area(
                            "Resultado de la traducción",
                            value=output_text,
                            height=150,
                            key="translated_text"
                        )

                except Exception as error:
                    st.error(
                        "No se pudo generar el audio. "
                        "Verifica tu conexión a internet y los idiomas "
                        f"seleccionados. Detalle: {error}"
                    )

with info_column:
    with st.container(border=True):
        st.markdown("### ✨ ¿Cómo funciona?")
        st.markdown("""
        **01. Captura**  
        Fotografía o carga una imagen con texto.

        **02. Reconoce**  
        El sistema identifica las palabras de la imagen mediante OCR.

        **03. Traduce**  
        Convierte el contenido al idioma de tu elección.

        **04. Escucha**  
        Genera un audio para que puedas escuchar el resultado.
        """)

st.markdown("""
<div class="footer">
    LECTOR INTELIGENTE · Reconocimiento óptico de caracteres
</div>
""", unsafe_allow_html=True)
```
