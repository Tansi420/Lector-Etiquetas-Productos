```python
import streamlit as st
import os
import time
import glob
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

# --------------------------------------------------
# ESTILOS
# --------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --background: #F7F8F4;
    --surface: #FFFFFF;
    --text: #202D28;
    --muted: #758079;
    --primary: #246B53;
    --accent: #D9F0A5;
}

.stApp {
    background: var(--background);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1150px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

h1, h2, h3 {
    font-family: 'Manrope', sans-serif !important;
    color: var(--text) !important;
    letter-spacing: -1px;
}

.hero {
    background: #E6EEDC;
    border-radius: 28px;
    padding: 38px 42px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}

.hero-label {
    color: #246B53;
    text-transform: uppercase;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 15px;
}

.hero h1 {
    font-size: clamp(32px, 4vw, 52px);
    line-height: 1.12;
    margin: 0;
    max-width: 650px;
}

.hero p {
    color: #56645A;
    font-size: 16px;
    line-height: 1.7;
    max-width: 560px;
    margin-top: 16px;
    margin-bottom: 0;
}

.hero-decoration {
    position: absolute;
    right: 38px;
    top: 32px;
    font-size: 100px;
    opacity: 0.15;
}

.section-heading {
    font-family: 'Manrope', sans-serif;
    font-size: 23px;
    font-weight: 800;
    letter-spacing: -0.6px;
    margin-top: 22px;
    margin-bottom: 5px;
}

.section-description {
    color: #758079;
    font-size: 14px;
    margin-bottom: 22px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: white;
    border: 1px solid #E6EAE3;
    border-radius: 20px;
    padding: 18px;
}

div[data-testid="stFileUploader"] section {
    background: #FAFBF8;
    border: 1.5px dashed #C6D4C8;
    border-radius: 16px;
}

div[data-testid="stCameraInput"] {
    border-radius: 16px;
    overflow: hidden;
}

.stButton > button {
    background: #246B53;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.65rem 1.2rem;
    font-weight: 700;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: #194E3C;
    color: white;
    border: none;
    transform: translateY(-1px);
}

.stSelectbox > div > div,
.stRadio > div {
    border-radius: 10px;
}

div[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E6EAE3;
}

div[data-testid="stSidebar"] h2,
div[data-testid="stSidebar"] h3 {
    letter-spacing: -0.5px;
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

.tip {
    background: #F0F3E9;
    border-radius: 14px;
    padding: 16px 18px;
    color: #56645A;
    font-size: 13px;
    line-height: 1.7;
    margin-top: 16px;
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

text = " "

def text_to_speech(input_language, output_language, text, tld):
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

    try:
        my_file_name = text[0:20]
        my_file_name = "".join(
            c for c in my_file_name
            if c.isalnum() or c in (" ", "_", "-")
        ).strip()
        if not my_file_name:
            my_file_name = "audio"
    except Exception:
        my_file_name = "audio"

    os.makedirs("temp", exist_ok=True)
    tts.save(f"temp/{my_file_name}.mp3")

    return my_file_name, trans_text


def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")

    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400

        for f in mp3_files:
            if os.stat(f).st_mtime < now - n_days:
                os.remove(f)


remove_files(7)
os.makedirs("temp", exist_ok=True)

translator = Translator()

# --------------------------------------------------
# ENCABEZADO
# --------------------------------------------------

st.markdown("""
<div class="hero">
    <div class="hero-label">LEE LABEL · LECTURA INTELIGENTE</div>
    <h1>Las etiquetas pequeñas.<br>Las letras, más claras.</h1>
    <p>
        Fotografía la etiqueta de un producto y convierte sus textos
        diminutos en palabras fáciles de leer o escuchar.
        Ingredientes, instrucciones y advertencias, a tu alcance.
    </p>
    <div class="hero-decoration">⌕</div>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# CAPTURA DE IMAGEN
# --------------------------------------------------

st.markdown(
    '<div class="section-heading">01 — Captura tu etiqueta</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="section-description">'
    'Usa tu cámara o sube una fotografía del empaque.'
    '</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    with st.container(border=True):
        st.markdown("### 📷 Fotografía")
        st.caption("Encuadra el texto que quieres leer.")

        cam_ = st.checkbox("Usar cámara")

        if cam_:
            img_file_buffer = st.camera_input(
                "Fotografía la etiqueta",
                help="Procura que el texto esté enfocado y bien iluminado."
            )
        else:
            img_file_buffer = None

        st.markdown("""
        <div class="tip">
        <b>Consejo:</b> acerca la cámara a las letras, evita los reflejos
        y mantén la etiqueta lo más recta posible.
        </div>
        """, unsafe_allow_html=True)

with col2:
    with st.container(border=True):
        st.markdown("### 🏷️ Cargar imagen")
        st.caption("Selecciona una fotografía guardada.")

        bg_image = st.file_uploader(
            "Sube la etiqueta del producto",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )

        if bg_image is not None:
            uploaded_file = bg_image
            image = Image.open(uploaded_file).convert("RGB")
            st.image(
                image,
                caption="Etiqueta seleccionada",
                use_container_width=True
            )

            # Mantiene el guardado local de la imagen.
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getvalue())

            st.success(f"Imagen guardada como {uploaded_file.name}")

            img_cv = cv2.cvtColor(
                np.array(image),
                cv2.COLOR_RGB2BGR
            )
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            text = pytesseract.image_to_string(img_rgb)

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
        help="El filtro invierte los colores de la imagen."
    )

if img_file_buffer is not None:
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(
        np.frombuffer(bytes_data, np.uint8),
        cv2.IMREAD_COLOR
    )

    if filtro == "Sí":
        cv2_img = cv2.bitwise_not(cv2_img)

    img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    text = pytesseract.image_to_string(img_rgb)

# --------------------------------------------------
# RESULTADO OCR
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-heading">02 — Lee el texto</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="section-description">'
    'El texto detectado aparecerá aquí para que puedas consultarlo.'
    '</div>',
    unsafe_allow_html=True
)

if text.strip():
    st.markdown(
        '<div class="result-label">Texto reconocido</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="result-box">{text}</div>',
        unsafe_allow_html=True
    )
else:
    st.info(
        "Tu texto aparecerá aquí cuando captures una fotografía "
        "o cargues una imagen."
    )

# --------------------------------------------------
# TRADUCCIÓN Y AUDIO
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
                "Primero captura una etiqueta o carga una imagen."
            )
        else:
            try:
                result, output_text = text_to_speech(
                    input_language,
                    output_language,
                    text,
                    tld
                )

                with open(f"temp/{result}.mp3", "rb") as audio_file:
                    audio_bytes = audio_file.read()

                st.markdown("### Tu audio")
                st.audio(audio_bytes, format="audio/mp3")

                if display_output_text:
                    st.markdown("### Texto traducido")
                    st.write(output_text)

            except Exception as e:
                st.error(
                    f"No fue posible generar el audio: {e}"
                )

# --------------------------------------------------
# PIE DE PÁGINA
# --------------------------------------------------

st.markdown("""
<div class="footer">
    LEE LABEL · Lee mejor lo que los empaques tienen para decir.
</div>
""", unsafe_allow_html=True)
```

TRANSLATION_LANGUAGES = {
    "Español": "es",
    "Inglés": "en",
    "Portugués": "pt",
    "Francés": "fr",
    "Italiano": "it",
    "Alemán": "de",
    "Coreano": "ko",
    "Chino": "zh-cn",
    "Japonés": "ja",
    "Bengalí": "bn",
}

ACCENTS = {
    "Predeterminado": "com",
    "Estados Unidos": "com",
    "Reino Unido": "co.uk",
    "India": "co.in",
    "Canadá": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za",
}


# ---------------- ESTILOS ----------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #F6F7F4;
    color: #202B27;
}

.block-container {
    padding-top: 2.5rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

.hero {
    background: linear-gradient(120deg, #173F35, #276A56);
    padding: 2.4rem;
    border-radius: 26px;
    color: white;
    margin-bottom: 1.8rem;
}

.hero h1 {
    color: white;
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -1.5px;
    margin-bottom: 0.5rem;
}

.hero p {
    color: #D9EAE1;
    font-size: 1.05rem;
    margin-bottom: 0;
}

.eyebrow {
    color: #A8D7BC;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-size: 0.75rem;
    font-weight: 700;
}

.section-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: #20372D;
    margin-top: 1rem;
    margin-bottom: 0.3rem;
}

.section-subtitle {
    color: #75827A;
    font-size: 0.95rem;
    margin-bottom: 1.2rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #E5EAE5;
    border-radius: 20px;
}

.stButton > button {
    background: #24664F;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.65rem 1rem;
    font-weight: 700;
    min-height: 45px;
}

.stButton > button:hover {
    background: #194D3B;
    color: white;
    border: none;
}

.stDownloadButton > button {
    border-radius: 12px;
}

div[data-testid="stFileUploader"] {
    border-radius: 14px;
}

div[data-testid="stSidebar"] {
    background: #FFFFFF;
}

div[data-testid="stSidebar"] h2 {
    color: #20372D;
}

.tip {
    background: #E7F1E8;
    color: #315D45;
    padding: 1rem;
    border-radius: 14px;
    font-size: 0.9rem;
    margin-top: 0.8rem;
}

.footer {
    text-align: center;
    color: #859087;
    padding-top: 2rem;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)


# ---------------- FUNCIONES ----------------

def preprocess_image(image, mode):
    """Mejora la imagen para facilitar el reconocimiento OCR."""
    if mode == "Original":
        return image

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Ampliar la imagen ayuda a reconocer letras pequeñas.
    height, width = gray.shape
    scale = max(2, min(4, 1800 // max(height, width)))

    gray = cv2.resize(
        gray,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    if mode == "Alto contraste":
        gray = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        ).apply(gray)

        gray = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11
        )

    elif mode == "Texto nítido":
        gray = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        ).apply(gray)

        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        gray = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

    return gray


def extract_text(image, language, mode):
    processed = preprocess_image(image, mode)

    try:
        return pytesseract.image_to_string(
            processed,
            lang=language,
            config="--oem 3 --psm 6"
        ).strip()
    except pytesseract.TesseractError:
        raise RuntimeError(
            f"No está instalado el paquete OCR '{language}'. "
            "Instala el idioma correspondiente de Tesseract."
        )


def translate_text(text, source, target):
    translator = Translator()
    result = translator.translate(
        text,
        src=source,
        dest=target
    )
    return result.text


def create_audio(text, language, accent):
    filename = os.path.join(
        TEMP_DIR,
        f"{uuid.uuid4().hex}.mp3"
    )

    tts = gTTS(
        text=text,
        lang=language,
        tld=accent,
        slow=False
    )

    tts.save(filename)

    with open(filename, "rb") as audio_file:
        audio_bytes = audio_file.read()

    try:
        os.remove(filename)
    except OSError:
        pass

    return audio_bytes


# ---------------- ENCABEZADO ----------------

st.markdown("""
<div class="hero">
    <div class="eyebrow">LECTURA INTELIGENTE</div>
    <h1>Lee lo que no alcanzas a ver.</h1>
    <p>
        Fotografía una etiqueta y convierte sus letras pequeñas
        en texto claro, traducible y listo para escuchar.
    </p>
</div>
""", unsafe_allow_html=True)


# ---------------- CONFIGURACIÓN LATERAL ----------------

with st.sidebar:
    st.markdown("## ⚙️ Preferencias")

    st.caption("Personaliza cómo se reconoce el texto.")

    ocr_language_name = st.selectbox(
        "Idioma de la etiqueta",
        list(LANGUAGES.keys()),
        index=0
    )

    image_mode = st.selectbox(
        "Mejora de imagen",
        [
            "Texto nítido",
            "Alto contraste",
            "Original"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("### 🌐 Traducción")

    source_language_name = st.selectbox(
        "Idioma original",
        list(TRANSLATION_LANGUAGES.keys()),
        index=0
    )

    target_language_name = st.selectbox(
        "Traducir a",
        list(TRANSLATION_LANGUAGES.keys()),
        index=1
    )

    st.markdown("---")
    st.markdown("### 🔊 Lectura en voz alta")

    speech_language_name = st.selectbox(
        "Idioma de la voz",
        list(TRANSLATION_LANGUAGES.keys()),
        index=0
    )

    accent_name = st.selectbox(
        "Variante de voz",
        list(ACCENTS.keys())
    )

    st.markdown("""
    <div class="tip">
        💡 <b>Consejo:</b> coloca la etiqueta bajo buena luz,
        evita reflejos y mantén el teléfono lo más quieto posible.
    </div>
    """, unsafe_allow_html=True)


# ---------------- CAPTURA DE IMAGEN ----------------

st.markdown(
    '<div class="section-title">01 · Captura tu etiqueta</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Usa la cámara o selecciona una fotografía existente.'
    '</div>',
    unsafe_allow_html=True
)

source = st.radio(
    "Fuente de imagen",
    ["📷 Tomar fotografía", "🖼️ Subir imagen"],
    horizontal=True,
    label_visibility="collapsed"
)

uploaded_image = None

if source == "📷 Tomar fotografía":
    uploaded_image = st.camera_input(
        "Encuadra la etiqueta y toma la fotografía",
        help="Procura que las letras se vean enfocadas."
    )
else:
    uploaded_image = st.file_uploader(
        "Selecciona una fotografía de la etiqueta",
        type=["png", "jpg", "jpeg", "webp"]
    )


# ---------------- PROCESAMIENTO ----------------

if uploaded_image is not None:

    try:
        pil_image = Image.open(uploaded_image).convert("RGB")
        image_rgb = np.array(pil_image)

        st.markdown("---")
        st.markdown(
            '<div class="section-title">02 · Revisa tu fotografía</div>',
            unsafe_allow_html=True
        )

        left, right = st.columns([1, 1], gap="large")

        with left:
            with st.container(border=True):
                st.markdown("**Tu fotografía**")
                st.image(
                    pil_image,
                    use_container_width=True
                )

                st.caption(
                    f"{pil_image.width} × {pil_image.height} píxeles"
                )

        with right:
            with st.container(border=True):
                st.markdown("**Preparación de imagen**")

                preview = preprocess_image(
                    image_rgb,
                    image_mode
                )

                st.image(
                    preview,
                    clamp=True,
                    use_container_width=True
                )

                st.caption(
                    "Vista previa del tratamiento aplicado "
                    "para mejorar la lectura."
                )

        if st.button(
            "✨ Leer etiqueta",
            use_container_width=True
        ):
            with st.spinner("Analizando letras y palabras..."):
                try:
                    recognized_text = extract_text(
                        image_rgb,
                        LANGUAGES[ocr_language_name],
                        image_mode
                    )

                    st.session_state["recognized_text"] = (
                        recognized_text
                    )

                except Exception as error:
                    st.error(f"No se pudo leer la imagen: {error}")

        # Mostrar resultado guardado
        recognized_text = st.session_state.get(
            "recognized_text",
            ""
        )

        if recognized_text:
            st.markdown("---")
            st.markdown(
                '<div class="section-title">'
                '03 · Tu etiqueta, en texto</div>',
                unsafe_allow_html=True
            )

            with st.container(border=True):
                st.markdown("**Texto reconocido**")

                edited_text = st.text_area(
                    "Puedes corregir cualquier palabra antes de "
                    "traducir o escuchar.",
                    value=recognized_text,
                    height=250,
                    key="edited_text"
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        "⬇️ Descargar texto",
                        data=edited_text,
                        file_name="texto_etiqueta.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

                with col2:
                    if st.button(
                        "🌐 Traducir texto",
                        use_container_width=True
                    ):
                        if not edited_text.strip():
                            st.warning("No hay texto para traducir.")
                        else:
                            try:
                                translated = translate_text(
                                    edited_text,
                                    TRANSLATION_LANGUAGES[
                                        source_language_name
                                    ],
                                    TRANSLATION_LANGUAGES[
                                        target_language_name
                                    ]
                                )

                                st.session_state["translated_text"] = (
                                    translated
                                )

                            except Exception as error:
                                st.error(
                                    "No se pudo traducir. "
                                    f"Comprueba tu conexión: {error}"
                                )

                translated_text = st.session_state.get(
                    "translated_text",
                    ""
                )

                if translated_text:
                    st.markdown("---")
                    st.markdown("**Traducción**")
                    st.text_area(
                        "Texto traducido",
                        value=translated_text,
                        height=180,
                        disabled=True
                    )

                    st.download_button(
                        "⬇️ Descargar traducción",
                        data=translated_text,
                        file_name="etiqueta_traducida.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

                st.markdown("---")
                st.markdown("**Escuchar texto**")

                speech_source = st.radio(
                    "Texto que quieres escuchar",
                    ["Texto original", "Texto traducido"],
                    horizontal=True,
                    key="speech_source"
                )

                if st.button(
                    "🔊 Generar audio",
                    use_container_width=True
                ):
                    if speech_source == "Texto traducido":
                        speech_text = translated_text
                        speech_language = TRANSLATION_LANGUAGES[
                            target_language_name
                        ]
                    else:
                        speech_text = edited_text
                        speech_language = TRANSLATION_LANGUAGES[
                            speech_language_name
                        ]

                    if not speech_text.strip():
                        st.warning("No hay texto para escuchar.")
                    else:
                        try:
                            with st.spinner("Generando voz..."):
                                audio_bytes = create_audio(
                                    speech_text,
                                    speech_language,
                                    ACCENTS[accent_name]
                                )

                            st.audio(
                                audio_bytes,
                                format="audio/mp3"
                            )

                        except Exception as error:
                            st.error(
                                "No se pudo generar el audio. "
                                f"Comprueba tu conexión: {error}"
                            )

                st.caption(
                    "Revisa siempre los números, ingredientes y "
                    "advertencias contra la etiqueta original."
                )

    except Exception as error:
        st.error(f"No se pudo abrir la imagen: {error}")

else:
    st.markdown("""
    <div class="tip">
        <b>¿Cómo funciona?</b><br><br>
        1. Fotografía o sube una imagen de la etiqueta.<br>
        2. Mejora la imagen para distinguir las letras pequeñas.<br>
        3. Reconoce el texto, edítalo, tradúcelo o escúchalo.
    </div>
    """, unsafe_allow_html=True)


st.markdown("""
<div class="footer">
    LECTOR DE ETIQUETAS · Lee mejor, comprende más.
</div>
""", unsafe_allow_html=True)        my_file_name = "audio"
        
    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/{my_file_name}.mp3"
    tts.save(file_path)
    return my_file_name, trans_text

def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    if len(mp3_files) != 0:
        now = time.time()
        n_days = n * 86400
        for f in mp3_files:
            try:
                if os.stat(f).st_mtime < now - n_days:
                    os.remove(f)
            except Exception:
                pass

remove_files(7)

st.title("🏷️ Lector de Etiquetas de Productos")
st.write("Escanea o fotografía las etiquetas de tus productos de supermercado para leer sus componentes, ingredientes y advertencias al instante con voz alta y clara.")
st.markdown("---")

col_cam, col_file = st.columns(2)

with col_cam:
    st.subheader("📸 Usar Cámara en Vivo")
    cam_active = st.checkbox("Activar cámara para escanear etiqueta")
    img_file_buffer = st.camera_input("Toma una foto de la etiqueta") if cam_active else None

with col_file:
    st.subheader("📁 Subir Imagen Existente")
    bg_image = st.file_uploader("Cargar foto de la etiqueta:", type=["png", "jpg", "jpeg"])

current_img = None
if img_file_buffer is not None:
    bytes_data = img_file_buffer.getvalue()
    current_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
elif bg_image is not None:
    file_bytes = np.asarray(bytearray(bg_image.read()), dtype=np.uint8)
    current_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

with st.sidebar:
    st.subheader("⚙️ Procesamiento de Imagen")
    filtro = st.radio("Filtro para mejorar lectura", ('Normal', 'Con Filtro (Invertido)'))
    
    st.markdown("---")
    st.subheader("🌐 Configuración de Traducción")
    
    in_lang = st.selectbox(
        "Lenguaje de la etiqueta (Entrada)",
        ("Ingles", "Español", "Bengali", "koreano", "Mandarin", "Japones")
    )
    
    out_lang = st.selectbox(
        "Lenguaje de lectura (Salida)",
        ("Español", "Ingles", "Bengali", "koreano", "Mandarin", "Japones")
    )
    
    english_accent = st.selectbox(
        "Acento de voz",
        ("Default", "India", "United Kingdom", "United States", "Canada", "Australia", "Ireland", "South Africa")
    )
    
    display_output_text = st.checkbox("Mostrar texto traducido", value=True)
    convert_btn = st.button("🔊 Leer y Traducir Etiqueta", use_container_width=True)

lang_map = {
    "Ingles": "en",
    "Español": "es",
    "Bengali": "bn",
    "koreano": "ko",
    "Mandarin": "zh-cn",
    "Japones": "ja"
}
input_language = lang_map.get(in_lang, "en")
output_language = lang_map.get(out_lang, "es")

tld_map = {
    "Default": "com",
    "India": "co.in",
    "United Kingdom": "co.uk",
    "United States": "com",
    "Canada": "ca",
    "Australia": "com.au",
    "Ireland": "ie",
    "South Africa": "co.za"
}
tld = tld_map.get(english_accent, "com")

if current_img is not None:
    if filtro == 'Con Filtro (Invertido)':
        current_img = cv2.bitwise_not(current_img)
        
    img_rgb = cv2.cvtColor(current_img, cv2.COLOR_BGR2RGB)
    extracted_text = pytesseract.image_to_string(img_rgb)
    st.session_state.extracted_text = extracted_text.strip()

st.subheader("📝 Ingredientes / Componentes Detectados:")
if st.session_state.extracted_text:
    st.info(st.session_state.extracted_text)
else:
    st.write("💡 Utiliza la cámara de tu celular o sube una fotografía clara de la etiqueta del producto para extraer su texto automáticamente.")

if convert_btn:
    if not st.session_state.extracted_text:
        st.warning("⚠️ Primero debes capturar o subir la imagen de una etiqueta con texto legible.")
    else:
        with st.spinner("🎙️ Procesando y generando audio de la etiqueta..."):
            result_file, output_text = text_to_speech(
                input_language, output_language, st.session_state.extracted_text, tld
            )
            audio_path = f"temp/{result_file}.mp3"
            
            if os.path.exists(audio_path):
                st.success("¡Lectura de etiqueta completada con éxito!")
                st.markdown("---")
                st.subheader("🎧 Reproductor de Audio:")
                
                with open(audio_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3", start_time=0)
                
                if display_output_text:
                    st.subheader("🌐 Traducción del Componente:")
                    st.success(output_text)
            else:
                st.error("Hubo un error al generar el archivo de audio.")
