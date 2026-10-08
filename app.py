
import os
import io
import uuid
import tempfile

import streamlit as st
import cv2
import numpy as np
import pytesseract

from PIL import Image
from gtts import gTTS
from googletrans import Translator


# ---------------- CONFIGURACIÓN ----------------

st.set_page_config(
    page_title="Lector de Etiquetas",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

TEMP_DIR = os.path.join(tempfile.gettempdir(), "lector_etiquetas")
os.makedirs(TEMP_DIR, exist_ok=True)

LANGUAGES = {
    "Español": "spa",
    "Inglés": "eng",
    "Portugués": "por",
    "Francés": "fra",
    "Italiano": "ita",
    "Alemán": "deu",
}

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
