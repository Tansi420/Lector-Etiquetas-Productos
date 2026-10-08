```python
import streamlit as st
import os
import time
import glob
import html
import cv2
import numpy as np
import pytesseract
from PIL import Image
from gtts import gTTS
from googletrans import Translator

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

st.set_page_config(
    page_title="LeeLabel | Lee tus etiquetas",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

os.makedirs("temp", exist_ok=True)

# --------------------------------------------------
# ESTILOS
# --------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

.stApp {
    background: #F7F8F4;
    color: #202D28;
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1150px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

h1, h2, h3 {
    font-family: 'Manrope', sans-serif !important;
    color: #202D28 !important;
    letter-spacing: -0.7px;
}

.hero {
    background: #E6EEDC;
    border-radius: 28px;
    padding: 40px;
    margin-bottom: 30px;
    position: relative;
    overflow: hidden;
}

.hero-label {
    color: #246B53;
    text-transform: uppercase;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 16px;
}

.hero h1 {
    font-size: clamp(32px, 4vw, 52px);
    line-height: 1.12;
    margin: 0;
    max-width: 700px;
}

.hero p {
    color: #56645A;
    font-size: 16px;
    line-height: 1.8;
    max-width: 600px;
    margin-top: 18px;
    margin-bottom: 0;
}

.hero-decoration {
    position: absolute;
    right: 40px;
    top: 25px;
    font-size: 100px;
    opacity: 0.15;
}

.section-heading {
    font-family: 'Manrope', sans-serif;
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.6px;
    margin-top: 15px;
    margin-bottom: 5px;
}

.section-description {
    color: #758079;
    font-size: 14px;
    margin-bottom: 22px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #E6EAE3;
    border-radius: 20px;
    padding: 18px;
}

div[data-testid="stFileUploader"] section {
    background: #FAFBF8;
    border: 1.5px dashed #C6D4C8;
    border-radius: 16px;
}

div[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E6EAE3;
}

.stButton > button {
    background: #246B53;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 1rem;
    font-weight: 700;
    transition: 0.2s ease;
}

.stButton > button:hover {
    background: #194E3C;
    color: white;
    border: none;
    transform: translateY(-1px);
}

.tip {
    background: #F0F3E9;
    border-radius: 14px;
    padding: 16px 18px;
    color: #56645A;
    font-size: 13px;
    line-height: 1.7;
    margin-top: 16px;
}

.result-label {
    color: #246B53;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
}

.result-box {
    background: white;
    border: 1px solid #E6EAE3;
    border-radius: 18px;
    padding: 24px;
    line-height: 1.8;
    color: #26352D;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    font-size: 16px;
}

.footer {
    color: #8A948C;
    text-align: center;
    font-size: 12px;
    margin-top: 50px;
}

hr {
    border-color: #E6EAE3;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# FUNCIONES
# --------------------------------------------------

def text_to_speech(input_language, output_language, text, tld):
    translator = Translator()

    translation = translator.translate(
        text,
        src=input_language,
        dest=output_language
    )

    trans_text = translation.text

    tts = gTTS(
        trans_text,
        lang=output_language,
        tld=tld,
        slow=False
    )

    my_file_name = "".join(
        c for c in text[:20]
        if c.isalnum() or c in (" ", "_", "-")
    ).strip()

    if not my_file_name:
        my_file_name = "audio"

    # Evitar nombres de archivo problemáticos.
    my_file_name = my_file_name.replace(" ", "_")
    file_path = os.path.join("temp", f"{my_file_name}.mp3")

    tts.save(file_path)

    return my_file_name, trans_text


def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    now = time.time()
    n_days = n * 86400

    for file_path in mp3_files:
        if os.stat(file_path).st_mtime < now - n_days:
            os.remove(file_path)


def recognize_text(image_array):
    return pytesseract.image_to_string(image_array)


remove_files(7)


# --------------------------------------------------
# ENCABEZADO
# --------------------------------------------------

st.markdown("""
<div class="hero">
    <div class="hero-label">LEELABEL · LECTURA INTELIGENTE</div>
    <h1>Las etiquetas pequeñas.<br>Las letras, más claras.</h1>
    <p>
        Fotografía la etiqueta de un producto y descubre lo que dice.
        Lee ingredientes, instrucciones y advertencias con ayuda
        del reconocimiento de texto y escucha el contenido en otro idioma.
    </p>
    <div class="hero-decoration">⌕</div>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# ESTADO DE LA APLICACIÓN
# --------------------------------------------------

if "recognized_text" not in st.session_state:
    st.session_state.recognized_text = ""

if "image_source" not in st.session_state:
    st.session_state.image_source = ""


# --------------------------------------------------
# CAPTURA Y CARGA DE IMAGEN
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">01 — Captura tu etiqueta</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Fotografía el empaque o carga una imagen que ya tengas.'
    '</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.markdown("### 📷 Fotografía")
        st.caption("Usa la cámara para capturar las letras de la etiqueta.")

        cam_ = st.checkbox(
            "Usar cámara",
            key="use_camera"
        )

        img_file_buffer = None

        if cam_:
            img_file_buffer = st.camera_input(
                "Fotografía la etiqueta",
                help="Procura que el texto esté enfocado y bien iluminado."
            )

        st.markdown("""
        <div class="tip">
            <b>Consejo:</b> acerca la cámara a las letras,
            evita los reflejos y mantén la etiqueta recta
            para facilitar la lectura.
        </div>
        """, unsafe_allow_html=True)

with col2:
    with st.container(border=True):
        st.markdown("### 🏷️ Cargar imagen")
        st.caption("Selecciona una fotografía guardada en tu dispositivo.")

        bg_image = st.file_uploader(
            "Sube la etiqueta del producto",
            type=["png", "jpg", "jpeg"]
        )

        if bg_image is not None:
            try:
                image = Image.open(bg_image).convert("RGB")

                st.image(
                    image,
                    caption="Etiqueta seleccionada",
                    use_container_width=True
                )

                # Se conserva el guardado local de la imagen.
                with open(bg_image.name, "wb") as file:
                    file.write(bg_image.getvalue())

                st.success(f"Imagen guardada como {bg_image.name}")

                img_array = np.array(image)
                st.session_state.recognized_text = recognize_text(
                    img_array
                )
                st.session_state.image_source = "upload"

            except Exception as error:
                st.error(f"No fue posible procesar la imagen: {error}")


# --------------------------------------------------
# PROCESAMIENTO DE CÁMARA
# --------------------------------------------------

with st.sidebar:
    st.markdown("## ⚙️ Preferencias")
    st.caption("Personaliza cómo quieres leer tu etiqueta.")
    st.divider()

    st.markdown("### Procesamiento de imagen")

    filtro = st.radio(
        "Aplicar filtro a la fotografía",
        ("No", "Sí"),
        help="Invierte los colores de la imagen antes de reconocer el texto."
    )


if img_file_buffer is not None:
    try:
        bytes_data = img_file_buffer.getvalue()

        cv2_img = cv2.imdecode(
            np.frombuffer(bytes_data, np.uint8),
            cv2.IMREAD_COLOR
        )

        if cv2_img is not None:
            if filtro == "Sí":
                cv2_img = cv2.bitwise_not(cv2_img)

            img_rgb = cv2.cvtColor(
                cv2_img,
                cv2.COLOR_BGR2RGB
            )

            st.session_state.recognized_text = recognize_text(img_rgb)
            st.session_state.image_source = "camera"

    except Exception as error:
        st.error(f"No fue posible procesar la fotografía: {error}")


# --------------------------------------------------
# RESULTADO DEL RECONOCIMIENTO
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-heading">02 — Lee el texto</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-description">'
    'Aquí encontrarás el texto que se pudo reconocer en la etiqueta.'
    '</div>',
    unsafe_allow_html=True
)

text = st.session_state.recognized_text

if text.strip():
    st.markdown(
        '<div class="result-label">Texto reconocido</div>',
        unsafe_allow_html=True
    )

    # Escapar el texto para evitar que caracteres de la etiqueta
    # se interpreten como HTML.
    safe_text = html.escape(text)

    st.markdown(
        f'<div class="result-box">{safe_text}</div>',
        unsafe_allow_html=True
    )
else:
    st.info(
        "Tu texto aparecerá aquí cuando captures una fotografía "
        "o cargues una imagen."
    )


# --------------------------------------------------
# IDIOMA, TRADUCCIÓN Y AUDIO
# --------------------------------------------------

with st.sidebar:
    st.divider()
    st.markdown("### 🌐 Idioma y audio")

    language_options = {
        "Inglés": "en",
        "Español": "es",
        "Bengalí": "bn",
        "Coreano": "ko",
        "Mandarín": "zh-cn",
        "Japonés": "ja"
    }

    in_lang = st.selectbox(
        "Idioma original de la etiqueta",
        tuple(language_options.keys())
    )

    input_language = language_options[in_lang]

    out_lang = st.selectbox(
        "Idioma del audio",
        tuple(language_options.keys()),
        index=1
    )

    output_language = language_options[out_lang]

    english_accent = st.selectbox(
        "Acento de la voz",
        (
            "Default",
            "India",
            "United Kingdom",
            "United States",
            "Canada",
            "Australia",
            "Ireland",
            "South Africa"
        )
    )

    tld_options = {
        "Default": "com",
        "India": "co.in",
        "United Kingdom": "co.uk",
        "United States": "com",
        "Canada": "ca",
        "Australia": "com.au",
        "Ireland": "ie",
        "South Africa": "co.za"
    }

    tld = tld_options[english_accent]

    display_output_text = st.checkbox(
        "Mostrar texto traducido"
    )

    convert_button = st.button(
        "🔊 Escuchar etiqueta",
        use_container_width=True
    )

    if convert_button:
        if not text.strip():
            st.warning(
                "Primero fotografía una etiqueta o carga una imagen."
            )
        else:
            try:
                with st.spinner("Preparando la traducción y el audio..."):
                    result, output_text = text_to_speech(
                        input_language,
                        output_language,
                        text,
                        tld
                    )

                    audio_path = os.path.join(
                        "temp",
                        f"{result}.mp3"
                    )

                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()

                st.markdown("### 🔊 Tu audio")
                st.audio(audio_bytes, format="audio/mp3")

                if display_output_text:
                    st.markdown("### Texto traducido")
                    st.write(output_text)

            except Exception as error:
                st.error(
                    f"No fue posible generar el audio: {error}"
                )


# --------------------------------------------------
# PIE DE PÁGINA
# --------------------------------------------------

st.markdown("""
<div class="footer">
    LEELABEL · Lee mejor lo que los empaques tienen para decir.
</div>
""", unsafe_allow_html=True)
```
