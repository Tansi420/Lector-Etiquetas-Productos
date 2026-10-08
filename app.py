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

st.set_page_config(
    page_title="Lector de Etiquetas de Productos",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""

translator = Translator()

def text_to_speech(input_lang, output_lang, text_to_translate, tld_val):
    try:
        translation = translator.translate(text_to_translate, src=input_lang, dest=output_lang)
        trans_text = translation.text
    except Exception:
        trans_text = text_to_translate
        
    tts = gTTS(trans_text, lang=output_lang, tld=tld_val, slow=False)
    try:
        my_file_name = text_to_translate[0:20].strip().replace(" ", "_")
        if not my_file_name:
            my_file_name = "audio"
    except Exception:
        my_file_name = "audio"
        
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
                st.error("Hubo un error al generar el archivo de audio.")    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin-bottom: 20px;
    border-left: 5px solid #ff4b4b;
}
.info-card {
    background-color: #e8f4fd;
    padding: 15px;
    border-radius: 10px;
    border-left: 5px solid #2b6cb0;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""

translator = Translator()

def text_to_speech(input_lang, output_lang, text_to_translate, tld_val):
    try:
        translation = translator.translate(text_to_translate, src=input_lang, dest=output_lang)
        trans_text = translation.text
    except Exception:
        trans_text = text_to_translate
        
    tts = gTTS(trans_text, lang=output_lang, tld=tld_val, slow=False)
    try:
        my_file_name = text_to_translate[0:20].strip().replace(" ", "_")
        if not my_file_name:
            my_file_name = "audio"
    except Exception:
        my_file_name = "audio"
        
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
st.markdown(
    "<p style='font-size: 18px; color: #555;'>Escanea o fotografía las etiquetas de tus productos de supermercado para leer sus componentes, ingredientes y advertencias al instante con voz alta y clara.</p>", 
    unsafe_allow_html=True
)
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

st.markdown("### 📝 Ingredientes / Componentes Detectados:")
if st.session_state.extracted_text:
    st.markdown(
        f"""
        <div class="custom-card">
            <p style="font-size: 16px; color: #333; white-space: pre-wrap;">{st.session_state.extracted_text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <div class="info-card">
            <b>💡 Instrucción:</b> Utiliza la cámara de tu celular o sube una fotografía clara de la etiqueta del producto para extraer su texto automáticamente.
        </div>
        """,
        unsafe_allow_html=True
    )

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
                st.markdown("### 🎧 Reproductor de Audio:")
                
                with open(audio_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3", start_time=0)
                
                if display_output_text:
                    st.markdown(
                        f"""
                        <div class="custom-card" style="border-left-color: #28a745;">
                            <h4>🌐 Traducción del Componente:</h4>
                            <p style="font-size: 16px; color: #333; white-space: pre-wrap;">{output_text}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.error("Hubo un error al generar el archivo de audio.")        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        border-left: 5px solid #ff4b4b;
    }
    .info-card {
        background-color: #e8f4fd;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2b6cb0;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar texto extraído en el estado de sesión
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""

# ---------------------------------------------------------
# FUNCIONES DE TRADUCCIÓN Y AUDIO
# ---------------------------------------------------------
translator = Translator()

def text_to_speech(input_lang, output_lang, text_to_translate, tld_val):
    try:
        translation = translator.translate(text_to_translate, src=input_lang, dest=output_lang)
        trans_text = translation.text
    except Exception:
        trans_text = text_to_translate
        
    tts = gTTS(trans_text, lang=output_lang, tld=tld_val, slow=False)
    try:
        my_file_name = text_to_translate[0:20].strip().replace(" ", "_")
        if not my_file_name:
            my_file_name = "audio"
    except Exception:
        my_file_name = "audio"
        
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

# ---------------------------------------------------------
# CABECERA PRINCIPAL
# ---------------------------------------------------------
st.title("🏷️ Lector de Etiquetas de Productos")
st.markdown(
    "<p style='font-size: 18px; color: #555;'>Escanea o fotografía las etiquetas de tus productos de supermercado para leer sus componentes, ingredientes y advertencias al instante con voz alta y clara.</p>", 
    unsafe_allow_html=True
)
st.markdown("---")

# ---------------------------------------------------------
# SECCIÓN DE ENTRADA (Cámara o Archivo)
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# BARRA LATERAL (Configuración, Filtros y Traducción)
# ---------------------------------------------------------
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

# Mapeos de idiomas y acentos
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

# ---------------------------------------------------------
# PROCESAMIENTO OCR
# ---------------------------------------------------------
if current_img is not None:
    if filtro == 'Con Filtro (Invertido)':
        current_img = cv2.bitwise_not(current_img)
        
    img_rgb = cv2.cvtColor(current_img, cv2.COLOR_BGR2RGB)
    extracted_text = pytesseract.image_to_string(img_rgb)
    st.session_state.extracted_text = extracted_text.strip()

# Mostrar resultados de OCR
st.markdown("### 📝 Ingredientes / Componentes Detectados:")
if st.session_state.extracted_text:
    st.markdown(
        f"""
        <div class="custom-card">
            <p style="font-size: 16px; color: #333; white-space: pre-wrap;">{st.session_state.extracted_text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <div class="info-card">
            <b>💡 Instrucción:</b> Utiliza la cámara de tu celular o sube una fotografía clara de la etiqueta del producto para extraer su texto automáticamente.
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# ACCIÓN DE TRADUCCIÓN Y AUDIO
# ---------------------------------------------------------
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
                st.markdown("### 🎧 Reproductor de Audio:")
                
                with open(audio_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3", start_time=0)
                
                if display_output_text:
                    st.markdown(
                        f"""
                        <div class="custom-card" style="border-left-color: #28a745;">
                            <h4>🌐 Traducción del Componente:</h4>
                            <p style="font-size: 16px; color: #333; white-space: pre-wrap;">{output_text}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.error("Hubo un error al generar el archivo de audio.")        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        border-left: 5px solid #ff4b4b;
    }
    .info-card {
        background-color: #e8f4fd;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2b6cb0;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar texto extraído en el estado de sesión
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""

# ---------------------------------------------------------
# FUNCIONES DE TRADUCCIÓN Y AUDIO
# ---------------------------------------------------------
translator = Translator()

def text_to_speech(input_lang, output_lang, text_to_translate, tld_val):
    try:
        translation = translator.translate(text_to_translate, src=input_lang, dest=output_lang)
        trans_text = translation.text
    except Exception:
        trans_text = text_to_translate
        
    tts = gTTS(trans_text, lang=output_lang, tld=tld_val, slow=False)
    try:
        my_file_name = text_to_translate[0:20].strip().replace(" ", "_")
        if not my_file_name:
            my_file_name = "audio"
    except Exception:
        my_file_name = "audio"
        
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

# ---------------------------------------------------------
# CABECERA PRINCIPAL
# ---------------------------------------------------------
st.title("🏷️ Lector de Etiquetas de Productos")
st.markdown(
    "<p style='font-size: 18px; color: #555;'>Escanea o fotografía las etiquetas de tus productos de supermercado para leer sus componentes, ingredientes y advertencias al instante con voz alta y clara.</p>", 
    unsafe_allow_html=True
)
st.markdown("---")

# ---------------------------------------------------------
# SECCIÓN DE ENTRADA (Cámara o Archivo)
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# BARRA LATERAL (Configuración, Filtros y Traducción)
# ---------------------------------------------------------
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

# Mapeos de idiomas y acentos
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

# ---------------------------------------------------------
# PROCESAMIENTO OCR
# ---------------------------------------------------------
if current_img is not None:
    if filtro == 'Con Filtro (Invertido)':
        current_img = cv2.bitwise_not(current_img)
        
    img_rgb = cv2.cvtColor(current_img, cv2.COLOR_BGR2RGB)
    extracted_text = pytesseract.image_to_string(img_rgb)
    st.session_state.extracted_text = extracted_text.strip()

# Mostrar resultados de OCR
st.markdown("### 📝 Ingredientes / Componentes Detectados:")
if st.session_state.extracted_text:
    st.markdown(
        f"""
        <div class="custom-card">
            <p style="font-size: 16px; color: #333; white-space: pre-wrap;">{st.session_state.extracted_text}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <div class="info-card">
            <b>💡 Instrucción:</b> Utiliza la cámara de tu celular o sube una fotografía clara de la etiqueta del producto para extraer su texto automáticamente.
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# ACCIÓN DE TRADUCCIÓN Y AUDIO
# ---------------------------------------------------------
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
                st.markdown("### 🎧 Reproductor de Audio:")
                
                with open(audio_path, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3", start_time=0)
                
                if display_output_text:
                    st.markdown(
                        f"""
                        <div class="custom-card" style="border-left-color: #28a745;">
                            <h4>🌐 Traducción del Componente:</h4>
                            <p style="font-size: 16px; color: #333; white-space: pre-wrap;">{output_text}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.error("Hubo un error al generar el archivo de audio.")                os.remove(f)
                print("Deleted ", f)


remove_files(7)
  



st.title("Reconocimiento Óptico de Caracteres")
st.subheader("Elige la fuente de la imágen, esta puede venir de la cámara o cargando un archivo")

cam_ = st.checkbox("Usar Cámara")

if cam_ :
   img_file_buffer = st.camera_input("Toma una Foto")
else :
   img_file_buffer = None
   
with st.sidebar:
      st.subheader("Procesamiento para Cámara")
      filtro = st.radio("Filtro para imagen con cámara",('Sí', 'No'))

bg_image = st.file_uploader("Cargar Imagen:", type=["png", "jpg"])
if bg_image is not None:
    uploaded_file=bg_image
    st.image(uploaded_file, caption='Imagen cargada.', use_container_width=True)
    
    # Guardar la imagen en el sistema de archivos
    with open(uploaded_file.name, 'wb') as f:
        f.write(uploaded_file.read())
    
    st.success(f"Imagen guardada como {uploaded_file.name}")
    img_cv = cv2.imread(f'{uploaded_file.name}')
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    text= pytesseract.image_to_string(img_rgb)
st.write(text)  
    
      
if img_file_buffer is not None:
    # To read image file buffer with OpenCV:
    bytes_data = img_file_buffer.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    
    if filtro == 'Con Filtro':
         cv2_img=cv2.bitwise_not(cv2_img)
    else:
        cv2_img= cv2_img
          
        
    img_rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    text=pytesseract.image_to_string(img_rgb) 
    st.write(text) 

with st.sidebar:
      st.subheader("Parámetros de traducción")
      
      try:
          os.mkdir("temp")
      except:
          pass
      #st.title("Text to speech")
      translator = Translator()
      
      #text = st.text_input("Enter text")
      in_lang = st.selectbox(
          "Seleccione el lenguaje de entrada",
          ("Ingles", "Español", "Bengali", "koreano", "Mandarin", "Japones"),
      )
      if in_lang == "Ingles":
          input_language = "en"
      elif in_lang == "Español":
          input_language = "es"
      elif in_lang == "Bengali":
          input_language = "bn"
      elif in_lang == "koreano":
          input_language = "ko"
      elif in_lang == "Mandarin":
          input_language = "zh-cn"
      elif in_lang == "Japones":
          input_language = "ja"
      
      out_lang = st.selectbox(
          "Select your output language",
          ("Ingles", "Español", "Bengali", "koreano", "Mandarin", "Japones"),
      )
      if out_lang == "Ingles":
          output_language = "en"
      elif out_lang == "Español":
          output_language = "es"
      elif out_lang == "Bengali":
          output_language = "bn"
      elif out_lang == "koreano":
          output_language = "ko"
      elif out_lang == "Chinese":
          output_language = "zh-cn"
      elif out_lang == "Japones":
          output_language = "ja"
      
      english_accent = st.selectbox(
          "Seleccione el acento",
          (
              "Default",
              "India",
              "United Kingdom",
              "United States",
              "Canada",
              "Australia",
              "Ireland",
              "South Africa",
          ),
      )
      
      if english_accent == "Default":
          tld = "com"
      elif english_accent == "India":
          tld = "co.in"
      
      elif english_accent == "United Kingdom":
          tld = "co.uk"
      elif english_accent == "United States":
          tld = "com"
      elif english_accent == "Canada":
          tld = "ca"
      elif english_accent == "Australia":
          tld = "com.au"
      elif english_accent == "Ireland":
          tld = "ie"
      elif english_accent == "South Africa":
          tld = "co.za"

      display_output_text = st.checkbox("Mostrar texto")

      if st.button("convert"):
          result, output_text = text_to_speech(input_language, output_language, text, tld)
          audio_file = open(f"temp/{result}.mp3", "rb")
          audio_bytes = audio_file.read()
          st.markdown(f"## Tu audio:")
          st.audio(audio_bytes, format="audio/mp3", start_time=0)
      
          if display_output_text:
              st.markdown(f"## Texto de salida:")
              st.write(f" {output_text}")




 
    
    
