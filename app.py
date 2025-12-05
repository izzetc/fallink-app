import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO
import base64
import time

# --- APPLE STYLE CONFIGURATION ---
st.set_page_config(
    page_title="JustArt Studio",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- PASTE YOUR API KEY HERE ---
API_KEY = "AIzaSyD2BN8tmMSYnOIHBYJrOJnBNXDF2OnjPVI"

# --- PASSWORD SYSTEM ---
# Basit ve etkili şifre koruması
def check_password():
    """Returns `True` if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.markdown(
        """
        <style>
        .stTextInput > div > div > input {
            text-align: center;
            font-size: 24px;
            letter-spacing: 5px;
            border-radius: 12px;
            padding: 15px;
        }
        </style>
        <h1 style='text-align: center; font-weight: 300;'>Welcome to Studio.</h1>
        <p style='text-align: center; color: grey;'>Please enter your access code.</p>
        """, unsafe_allow_html=True)

    password = st.text_input("", type="password", key="password_input")
    
    # --- ŞİFREYİ BURADAN DEĞİŞTİREBİLİRSİN (Şu an: xqr) ---
    if password == "xqr": 
        st.session_state["password_correct"] = True
        st.rerun()  # Şifre doğruysa sayfayı yenile ve içeri al
    elif password:
        st.error("Incorrect code. Please try again.")
    
    return False

if not check_password():
    st.stop() # Şifre yanlışsa burada dur, aşağıyı gösterme

# --- CSS STYLING (Apple Aesthetic) ---
st.markdown("""
<style>
    /* Font ve Genel Yapı */
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
        background-color: #ffffff; /* Saf beyaz arka plan */
        color: #1d1d1f; /* Apple koyu gri yazı rengi */
    }

    /* Başlıklar */
    h1 {
        font-weight: 600;
        font-size: 2.5rem;
        letter-spacing: -0.02em;
    }
    h2, h3 {
        font-weight: 500;
    }

    /* Butonlar (Apple Mavisi) */
    .stButton > button {
        background-color: #0071e3 !important;
        color: white !important;
        border-radius: 980px !important; /* Tam yuvarlak kenarlar */
        padding: 12px 24px !important;
        font-weight: 500 !important;
        font-size: 16px !important;
        border: none !important;
        box-shadow: none !important;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #0077ED !important;
        transform: scale(1.02);
    }
    /* İkincil Buton (İndir) */
    .download-btn {
        background-color: #f5f5f7;
        color: #1d1d1f;
        border-radius: 12px;
        padding: 10px 20px;
        text-decoration: none;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        transition: background-color 0.3s ease;
    }
    .download-btn:hover {
        background-color: #e8e8ed;
    }

    /* Giriş Alanları ve Seçim Kutuları */
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important;
        border: 1px solid #d2d2d7 !important;
        background-color: #ffffff !important;
        padding: 5px !important;
    }
    .stTextArea textarea:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #0071e3 !important;
        box-shadow: 0 0 0 4px rgba(0,113,227,0.1) !important;
    }

    /* Radio Butonları (Stil Seçimi) */
    .stRadio > div {
        background-color: #f5f5f7;
        padding: 15px;
        border-radius: 16px;
    }

    /* Görseller */
    img {
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def get_image_download_link(img, filename, text):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}" class="download-btn">Is {text}</a>'
    return href

def generate_tattoo_stencil(user_prompt, style, placement):
    client = genai.Client(api_key=API_KEY)
    
    base_prompt = f"Tattoo design concept: {user_prompt}. Placement body area: {placement}."
    
    # --- YENİ VE GENİŞLETİLMİŞ STİL MENÜSÜ ---
    styles = {
        "Fine Line Minimalist": "Style: Ultra-thin fine line tattoo, single needle, minimalist, clean, delicate, black ink, no shading, negative space.",
        "Micro Realism (Small & Detailed)": "Style: Micro realism tattoo, incredible detail in small scale, fine black and grey shading, photographic quality.",
        "Dotwork & Geometry": "Style: Dotwork shading, sacred geometry patterns, mandalas, stippling, precise dots, blackwork.",
        "Engraving / Woodcut": "Style: Vintage engraving illustration, cross-hatching, linocut print texture, old book illustration feel.",
        "Sketch / Hand-Drawn": "Style: Pencil sketch, rough guidelines, artistic, unfinished look, charcoal texture on paper.",
        "Blackwork / Tribal": "Style: Bold blackwork, solid blackfill areas, heavy lines, high contrast, tribal or ornamental patterns.",
        "Cyber Sigilism / Neo-Tribal": "Style: Cyber sigilism, futuristic chrome tribal, sharp aggressive lines, Y2K aesthetic, bio-mechanical.",
        "Japanese (Irezumi - Black & Grey)": "Style: Traditional Japanese tattoo, irezumi, waves, clouds, dragon scales, bold outlines, heavy black shading.",
        "Trash Polka (Black & Red)": "Style: Trash Polka, chaotic composition, realism mixed with abstract brush strokes, typography, black and red ink only."
    }
    
    style_prompt = styles.get(style, styles["Blackwork / Tribal"]) # Varsayılan: Blackwork

    # Final Prompt Engineering
    final_prompt = f"{base_prompt} {style_prompt} Output must be a clean, high-contrast tattoo design on a plain white background. Professional tattoo flash art."

    try:
        response = client.models.generate_images(
            model="imagen-4.0-generate-001", 
            prompt=final_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            img = Image.open(BytesIO(image_bytes))
            return img, None
        else:
            return None, "AI returned an empty response."
            
    except Exception as e:
        return None, str(e)

# --- MAIN APP INTERFACE ---

st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>Design Your Ink.</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: grey; margin-top: -15px; margin-bottom: 40px;'>Powered by JustArt AI</p>", unsafe_allow_html=True)

with st.container():
    st.subheader("1. The Idea")
    user_input = st.text_area(
        "Describe your vision", 
        height=120,
        help="Be descriptive. Example: 'A astronaut sitting on a crescent moon, holding a balloon'",
        placeholder="e.g., A stoic lion portrait with a geometric mane..."
    )

col1, col2 = st.columns(2)
with col1:
    st.subheader("2. The Style")
    selected_style = st.selectbox(
        "Choose an aesthetic",
        ("Fine Line Minimalist", "Micro Realism (Small & Detailed)", "Dotwork & Geometry", "Engraving / Woodcut", "Sketch / Hand-Drawn", "Blackwork / Tribal", "Cyber Sigilism / Neo-Tribal", "Japanese (Irezumi - Black & Grey)", "Trash Polka (Black & Red)")
    )
with col2:
    st.subheader("3. Placement")
    placement = st.selectbox(
        "Where will it go?",
        ("Arm / Forearm", "Shoulder", "Back", "Chest / Sternum", "Leg / Calf", "Ankle / Wrist", "Neck (Small)")
    )

st.markdown("---")

# Generate Button with Animation Effect
if st.button("Create Design", type="primary", use_container_width=True):
    if not user_input:
        st.toast("Please describe your idea first.", icon="⚠️")
    else:
        progress_text = "Crafting your design... This feels like magic."
        my_bar = st.progress(0, text=progress_text)

        for percent_complete in range(100):
            time.sleep(0.05) # Fake loading animation for better UX
            my_bar.progress(percent_complete + 1, text=progress_text)
            
        # Real Generation
        generated_image, error_message = generate_tattoo_stencil(user_input, selected_style, placement)
        my_bar.empty() # Remove progress bar

        if generated_image:
            st.balloons() # Success animation
            st.success("Your design is ready.")
            
            # Result Display
            st.image(generated_image, caption=f"{selected_style} on {placement}", use_column_width=True)
            
            # Download Section
            st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
            st.markdown(get_image_download_link(generated_image, "justart_design.png", "Download High-Res Image"), unsafe_allow_html=True)
            st.caption("Show this to your tattoo artist.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            st.error(f"Something went wrong: {error_message}")

# Minimal Footer
st.markdown("<div style='text-align: center; color: #86868b; font-size: 12px; margin-top: 50px; padding-bottom: 20px;'>JustArt Studio © 2025</div>", unsafe_allow_html=True)
