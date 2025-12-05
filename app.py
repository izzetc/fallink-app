import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO
import base64
import time
import random
from supabase import create_client, Client

# --- GİZLİ BİLGİLER (SECRETS) ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    st.error("⚠️ API Anahtarları bulunamadı. Lütfen Streamlit Secrets ayarlarını kontrol et.")
    st.stop()

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Fallink Studio",
    page_icon="✒️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- VERİTABANI BAĞLANTISI ---
@st.cache_resource
def init_connection():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return None

supabase = init_connection()

# --- CSS & TASARIM BÜYÜSÜ (PREMIUM UI) ---
st.markdown("""
<style>
    /* Google Fonts - Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #FAFAFA; /* Hafif kırık beyaz */
        color: #111;
    }

    /* Başlık Stili */
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        background: -webkit-linear-gradient(45deg, #111, #555);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .sub-title {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }

    /* Kredi Rozeti */
    .credit-badge {
        background-color: #fff;
        border: 1px solid #eaeaea;
        color: #111;
        padding: 8px 16px;
        border-radius: 99px;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        display: inline-block;
    }

    /* Butonlar (Apple Style) */
    .stButton > button {
        background-color: #111 !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        border: none !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2) !important;
        background-color: #333 !important;
    }

    /* Input Alanları */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 10px;
        font-size: 1rem;
    }
    
    .stSelectbox > div > div {
        background-color: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        color: #111;
    }

    /* Kart Görünümü (Tasarım Sonucu) */
    .design-card {
        background: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        text-align: center;
        margin-top: 20px;
        border: 1px solid #f0f0f0;
    }
    
    /* Streamlit Logolarını Gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---

def check_user_credits(username):
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]["credits"]
        else:
            return -1
    except:
        return -1

def deduct_credit(username, current_credits):
    try:
        new_credit = current_credits - 1
        supabase.table("users").update({"credits": new_credit}).eq("username", username).execute()
        return new_credit
    except:
        return current_credits

def get_image_download_link(img, filename, text):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'''
    <a href="data:file/png;base64,{img_str}" download="{filename}" 
    style="text-decoration:none; display:inline-block; margin-top:10px; background-color:#F5F5F7; color:#111; padding:10px 20px; border-radius:10px; font-weight:600; border:1px solid #d1d1d1; transition:0.2s;">
    📥 {text}
    </a>
    '''
    return href

def generate_tattoo_stencil(user_prompt, style, placement):
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        # PROMPT MÜHENDİSLİĞİ (GELİŞMİŞ)
        # Amacımız: Temiz, beyaz arka planlı, deriye aktarılabilir şablonlar.
        base_prompt = f"Design a professional tattoo stencil of: {user_prompt}. Body placement context: {placement}."
        
        style_details = {
            "Fine Line": "Ultra-thin single needle lines, minimalist, delicate, high precision, no shading, distinct outlines.",
            "Micro Realism": "Highly detailed micro realism, soft grey shading, photographic quality in black and white.",
            "Dotwork/Mandala": "Stippling texture, pointillism, sacred geometry, precise dot patterns, black ink.",
            "Traditional (Old School)": "Bold thick outlines, heavy black shading, classic tattoo iconography, strong contrast.",
            "Sketch/Abstract": "Pencil sketch style, rough artistic lines, charcoal texture, unfinished artistic edges.",
            "Blackwork/Tribal": "Solid black fill, heavy bold shapes, high contrast, negative space patterns."
        }
        
        selected_style_prompt = style_details.get(style, "")
        
        # Final Prompt'u güçlendiriyoruz
        final_prompt = (
            f"{base_prompt} Style: {selected_style_prompt}. "
            f"Requirements: Pure white background, high contrast black ink, clean isolation, "
            f"no skin texture, no realistic body parts, 2D vector graphic style, professional tattoo flash sheet."
        )

        response = client.models.generate_images(
            model="imagen-4.0-generate-001", 
            prompt=final_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            img = Image.open(BytesIO(image_bytes))
            return img, None
        return None, "Yapay zeka boş yanıt döndü."
    except Exception as e:
        return None, str(e)

# --- UYGULAMA AKIŞI ---

# Session State Başlatma (Oturum Hafızası)
if "gallery" not in st.session_state:
    st.session_state["gallery"] = [] 

# 1. GİRİŞ EKRANI
if "logged_in_user" not in st.session_state:
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Fallink.</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>AI Tattoo Design Studio</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            st.markdown("**Member Access**")
            username_input = st.text_input("Access Code", placeholder="Enter your code", label_visibility="collapsed")
            if st.button("Enter Studio", use_container_width=True):
                credits = check_user_credits(username_input)
                if credits == -1:
                    st.error("Access code not found.")
                else:
                    st.session_state["logged_in_user"] = username_input
                    st.session_state["credits"] = credits
                    st.rerun()
    st.stop()

# 2. STÜDYO EKRANI
user = st.session_state["logged_in_user"]
credits = check_user_credits(user)

# Üst Bar
c1, c2 = st.columns([3,1])
with c1:
    st.markdown(f"<h3 style='margin:0; padding-top:10px;'>Fallink Studio</h3>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='credit-badge'>💎 {credits} Credits</div>", unsafe_allow_html=True)

st.markdown("---")

# Giriş Alanı
c_left, c_right = st.columns([2, 1])

with c_left:
    st.markdown("##### 💡 Describe your idea")
    user_prompt = st.text_area("Prompt", height=120, placeholder="E.g. A wolf head with geometric shapes, looking fierce...", label_visibility="collapsed")
    
    # Hızlı İlham Butonu
    if st.button("🎲 Surprise Me (Random Idea)"):
        ideas = ["A minimalist paper plane flying through clouds", "A realistic eye crying a galaxy", "A snake wrapped around a dagger, traditional style", "Geometric deer head with flowers"]
        user_prompt = random.choice(ideas)
        st.info(f"Try this: {user_prompt}")

with c_right:
    st.markdown("##### 🎨 Style & Fit")
    style = st.selectbox("Art Style", ("Fine Line", "Micro Realism", "Dotwork/Mandala", "Traditional (Old School)", "Sketch/Abstract", "Blackwork/Tribal"))
    placement = st.selectbox("Body Area", ("Inner Arm", "Back", "Chest", "Ankle", "Neck", "Thigh"))
    
    generate_btn = st.button("Generate Ink ✨", type="primary", use_container_width=True)

# Üretim İşlemi
if generate_btn:
    if credits < 1:
        st.error("Out of ink! Please top up your credits.")
    elif not user_prompt:
        st.warning("Please describe what you want first.")
    else:
        with st.spinner("Mixing ink & designing..."):
            new_credits = deduct_credit(user, credits)
            img, err = generate_tattoo_stencil(user_prompt, style, placement)
            
            if img:
                # Galeriye ekle
                st.session_state["gallery"].insert(0, {"img": img, "prompt": user_prompt, "style": style})
                st.session_state["credits"] = new_credits
                st.rerun() # Sayfayı yenile ki galeri güncellensin
            else:
                st.error(f"Error: {err}")

# 3. GALERİ (SONUÇLAR)
if len(st.session_state["gallery"]) > 0:
    st.markdown("### Recent Designs")
    
    # En son tasarımı büyük göster
    latest = st.session_state["gallery"][0]
    
    st.markdown(f"""
    <div class="design-card">
        <p style="color:#888; font-size:0.9rem;">{latest['prompt']} • {latest['style']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.image(latest['img'], use_column_width=True)
    st.markdown(get_image_download_link(latest['img'], "fallink_design.png", "Download Stencil"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Eski tasarımları küçük göster (Expander içinde)
    with st.expander("View Previous Designs in Session"):
        for item in st.session_state["gallery"][1:]:
            col_a, col_b = st.columns([1,3])
            with col_a:
                st.image(item['img'], width=100)
            with col_b:
                st.write(f"**{item['style']}**")
                st.caption(item['prompt'])
                st.markdown(get_image_download_link(item['img'], "design.png", "Download"), unsafe_allow_html=True)
