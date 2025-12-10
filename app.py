import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO
import base64
import time
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from supabase import create_client, Client

# --- GİZLİ BİLGİLERİ (SECRETS) ÇEKME ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    EMAIL_USER = st.secrets["EMAIL_USER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
except:
    st.error("⚠️ Eksik Anahtarlar! Lütfen Streamlit Secrets ayarlarını kontrol et.")
    st.stop()

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Fallink",
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

# --- CSS TASARIM & LOGO STİLİ ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #121212 !important;
        color: #E0E0E0 !important;
    }

    .stApp {
        background-color: #121212;
    }
    
    div[data-testid="stContainer"], div[data-testid="stExpander"] {
        background-color: #1E1E1E;
        border-radius: 16px;
        border: 1px solid #333;
        padding: 20px;
        margin-bottom: 15px;
    }

    /* Dosya Yükleyici Stili */
    div[data-testid="stFileUploader"] {
        padding: 10px;
        border: 1px dashed #555;
        border-radius: 12px;
        text-align: center;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #2C2C2C !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        border-radius: 12px !important;
    }
    
    div[data-baseweb="popover"], div[data-baseweb="menu"] {
        background-color: #2C2C2C !important;
        color: #FFF !important;
    }
    
    /* --- ÖZEL FALLINK LOGO CSS --- */
    .fallink-logo {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: -2px;
        background: linear-gradient(to right, #E9D5FF 0%, #A855F7 50%, #7E22CE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        display: inline-block;
    }
    
    /* Butonlar */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8A2BE2, #4B0082) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 16px 24px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 18px !important;
        box-shadow: 0 4px 15px rgba(138, 43, 226, 0.4) !important;
        width: 100%;
    }
    
    .stButton > button[kind="secondary"] {
        background-color: #333333 !important;
        color: #E0E0E0 !important;
        border-radius: 12px !important;
        border: 1px solid #555 !important;
        font-weight: 600 !important;
        width: 100%;
    }

    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    .stDeployButton {display:none;}
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 600px;
    }
    
    .credit-info {
        text-align: right;
        font-weight: 700;
        color: #E0E0E0;
    }

</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---

def send_email_with_design(to_email, img_buffer, prompt):
    # (E-posta fonksiyonu aynı kalıyor)
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = "Your Fallink Tattoo Design is Ready! ✒️"
    body = f"""<html><body style='font-family: sans-serif; color: #333;'>
        <h2>Your Design is Here!</h2>
        <p>Here is the high-detail AI tattoo design you created with Fallink.</p>
        <p><strong>Idea:</strong> {prompt}</p>
        <br><p>See you at the studio!</p><p><em>Fallink Team</em></p>
      </body></html>"""
    msg.attach(MIMEText(body, 'html', 'utf-8'))
    image_data = img_buffer.getvalue()
    image = MIMEImage(image_data, name="fallink_design.png")
    msg.attach(image)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

def check_user_credits(username):
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        if response.data: return response.data[0]["credits"]
        return -1
    except: return -1

def deduct_credit(username, current_credits):
    try:
        new_credit = current_credits - 1
        supabase.table("users").update({"credits": new_credit}).eq("username", username).execute()
        return new_credit
    except: return current_credits

def get_image_download_link(img, filename, text):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"""
        <a href="data:file/png;base64,{img_str}" download="{filename}" 
           style="display: block; text-align: center; background-color: #333; color: #FFF; 
                  padding: 12px; border-radius: 12px; text-decoration: none; font-weight: 700; border: 1px solid #555;">
           📥 {text}
        </a>
    """

# --- ANA AI FONKSİYONU (GÜNCELLENDİ: Görsel Desteği Eklendi) ---
def generate_tattoo_stencil(user_prompt, style, placement, input_pil_image=None):
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        style_details = {
            "Fine Line": "Intricate ultra-thin single needle lines, high precision, delicate details, elegant composition, clean blackwork.",
            "Micro Realism": "Highly detailed micro realism, sophisticated soft grey shading, photographic quality, depth, complex textures.",
            "Dotwork/Mandala": "Complex stippling texture, precise pointillism, intricate sacred geometry patterns, detailed shading through dots.",
            "Old School (Traditional)": "Bold clean outlines, solid heavy black shading, highly detailed classic iconography, high contrast.",
            "Sketch/Abstract": "Detailed artistic pencil sketch style, expressive lines, cross-hatching shading, dynamic composition.",
            "Tribal/Blackwork": "Intricate solid black patterns, complex Polynesian or modern ornamental shapes, high contrast, heavy saturation.",
            "Japanese (Irezumi)": "Highly detailed traditional Japanese style, complex background elements (waves/clouds), bold flowing outlines.",
            "Geometric": "Complex mathematical shapes, intricate sacred geometry, sacred patterns, precise sharp lines, detailed architectural feel.",
            "Watercolor": "Detailed black and grey ink wash style, complex liquid textures, artistic drips, soft gradients mimicking watercolor painting.",
            "Neo-Traditional": "Highly detailed illustrated realism, varying line weights, decorative filigree, complex composition.",
            "Trash Polka": "Complex chaotic composition, detailed realism elements mixed with abstract brush strokes and typography, high energy.",
            "Cyber Sigilism": "Intricate futuristic sharp lines, complex aggressive patterns, Y2K aesthetic, detailed chrome-like texture feel.",
            "Chicano": "Highly detailed black and grey fine art, complex shading, realistic portraits or script, rich cultural details.",
            "Engraving/Woodcut": "Highly intricate vintage illustration style, dense cross-hatching shading, linocut texture, detailed antique print look.",
            "Minimalist": "Clean, precise, highly refined simple lines. Detail through perfect composition and negative space."
        }
        selected_style_description = style_details.get(style, "High detail tattoo design")

        # --- PROMPT MANTIĞI (Görsel var mı yok mu?) ---
        contents = []
        if input_pil_image:
            # Eğer görsel varsa, AI'ya görseli ve ona dayalı komutu gönderiyoruz.
            contents.append(input_pil_image)
            instruction_base = f"Based on this uploaded image, create a tattoo design modifying it as follows: {user_prompt}. "
            placement_instruction = f"Ensure the flow is suitable for '{placement}' placement."
        else:
            # Görsel yoksa, sadece metin tabanlı üretim.
            instruction_base = f"A highly detailed, finished digital tattoo design (Procreate style) showing: {user_prompt}. "
            placement_instruction = f"The design flow is intended for a '{placement}' placement, show ONLY isolated artwork."

        technical_requirements = (
            "REQUIREMENTS: The final output MUST be a professional tattoo stencil. "
            "Pure white background (Hex #FFFFFF). Deep black ink only. High contrast. "
            "ABSOLUTELY NO skin texture, NO body parts, and NO anatomy in the image. "
            "Intricate details, clean professional linework."
        )
        
        final_prompt = f"{instruction_base} {placement_instruction} Style: {selected_style_description}. {technical_requirements}"
        contents.append(final_prompt)

        # API ÇAĞRISI (Contents listesi gönderiliyor)
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            contents=contents,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            return Image.open(BytesIO(image_bytes)), None
        return None, "AI returned empty response."
    except Exception as e:
        return None, str(e)

# --- UYGULAMA AKIŞI ---

if "generated_img" not in st.session_state:
    st.session_state["generated_img"] = None
    st.session_state["last_prompt"] = ""
    st.session_state["last_style"] = "Fine Line" 
    st.session_state["last_placement"] = "Arm"
    # Yüklenen görseli de hafızada tutalım
    if "uploaded_ref_image" not in st.session_state:
        st.session_state["uploaded_ref_image"] = None

# 1. LOGIN EKRANI
if "logged_in_user" not in st.session_state:
    st.markdown("<div style='margin-top: 80px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center;'>
            <h1 class='fallink-logo' style='font-size: 4rem; margin: 0;'>Fallink</h1>
            <p style='color:#aaa; margin-top: 10px;'>AI Powered Tattoo Stencil Studio</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        username_input = st.text_input("Enter Access Code", placeholder="Code here...")
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Enter Studio 🚀", type="primary", use_container_width=True):
            credits = check_user_credits(username_input)
            if credits == -1: st.error("Invalid code.")
            else:
                st.session_state["logged_in_user"] = username_input
                st.session_state["credits"] = credits
                st.rerun()
    st.stop()

# 2. STÜDYO ARAYÜZÜ
user = st.session_state["logged_in_user"]
credits = check_user_credits(user)

# Üst Bilgi Çubuğu
st.markdown(f"""
<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
    <div class='fallink-logo' style='font-size: 2rem;'>Fallink</div>
    <div class='credit-info'>{credits} 💎 Credits</div>
</div>
""", unsafe_allow_html=True)

# GİRİŞ ALANI
if st.session_state["generated_img"] is None:
    
    # KART 1: Fikir Alanı (Görsel Yükleme Eklendi)
    with st.container():
        st.markdown("### 1. Describe Your Idea")
        
        # --- YENİ: GÖRSEL YÜKLEME ALANI (Expander içinde gizli) ---
        with st.expander("📸 Upload Reference Image (Optional)", expanded=False):
            uploaded_file = st.file_uploader("Choose an image to modify...", type=["jpg", "png", "jpeg"])
            if uploaded_file is not None:
                # Görseli oturuma kaydet ve küçük bir önizleme göster
                st.session_state["uploaded_ref_image"] = Image.open(uploaded_file)
                st.image(st.session_state["uploaded_ref_image"], caption="Reference Image", width=150)
                st.caption("💡 Now describe how you want to change this image below.")
            else:
                # Eğer kullanıcı görseli silerse, oturumdan da sil
                 st.session_state["uploaded_ref_image"] = None
        # ---------------------------------------------------------

        user_prompt = st.text_area("What do you want to create or change?", height=120, placeholder="E.g. 'A geometric wolf' OR if image uploaded: 'Remove background, make clouds Japanese style'...")
        
        if st.session_state["uploaded_ref_image"] is None:
            if st.button("🎲 Need Inspiration? (Random Idea)", type="secondary", use_container_width=True):
                ideas = ["A geometric wolf howling at a crescent moon", "Minimalist paper plane flying through clouds", "Realistic eye crying a galaxy", "Snake wrapped around a vintage dagger", "Koi fish swimming in a yin yang pattern", "Clock melting over a tree branch (Dali style)", "Astronaut sitting on a swing in space", "Skeleton hand holding a red rose", "Phoenix rising from ashes, watercolor style", "Compass with mountains inside", "Lion head with a crown of thorns", "Hourglass with sand turning into birds", "Samurai mask with cherry blossoms", "Cyberpunk geisha portrait", "Detailed map of Middle Earth", "Hummingbird drinking from a hibiscus flower", "Viking ship in a storm", "Medusa head with stone eyes", "Anchor entangled with octopus tentacles", "Tarot card 'The Moon' design", "Geometric deer head with antlers transforming into trees", "Single line drawing of a cat", "Moth with skull pattern on wings", "Phonograph playing musical notes", "Pocket watch with exposed gears", "Tree of life with deep roots", "Raven perched on a skull", "Abstract soundwave of a heartbeat", "Barcode melting into liquid", "Chess piece (King) falling over", "Spartan helmet with spears", "Feather turning into a flock of birds", "Lotus flower unalome", "Dragon wrapping around the arm", "Butterfly with one wing as flowers", "Vintage camera illustration", "Micro realistic bee", "Portrait of a Greek statue broken", "Cyber sigilism pattern on spine", "Trash polka style heart and arrows", "Egyptian Anubis god profile", "Nordic runes circle", "Sword piercing a heart", "Alien spaceship beaming up a cow", "Jellyfish floating in space", "Owl with piercing eyes", "Grim reaper playing chess", "Angel wings on back", "Dna helix made of tree branches", "Retro cassette tape"]
                user_prompt = random.choice(ideas)
                st.info(f"💡 Idea selected. Feel free to edit it above.")

    # KART 2: Seçenekler
    with st.container():
        st.markdown("### 2. Customize It")
        
        style_options = ("Fine Line", "Micro Realism", "Dotwork/Mandala", "Old School (Traditional)", "Sketch/Abstract", "Tribal/Blackwork", "Japanese (Irezumi)", "Geometric", "Watercolor", "Neo-Traditional", "Trash Polka", "Cyber Sigilism", "Chicano", "Engraving/Woodcut", "Minimalist")
        style = st.selectbox("Choose Style", style_options)
        
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) 

        placement_options = ("Forearm (Inner)", "Forearm (Outer)", "Upper Arm / Bicep", "Shoulder", "Chest", "Back (Upper)", "Back (Full)", "Spine", "Ribs / Side", "Thigh", "Calf", "Ankle", "Wrist", "Hand", "Finger", "Neck", "Behind Ear", "Other (Custom)")
        placement_select = st.selectbox("Body Placement (Defines Flow)", placement_options)
        if placement_select == "Other (Custom)":
            placement = st.text_input("Specify placement flow", placeholder="e.g. Knuckles flow")
        else:
            placement = placement_select
            
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ANA BUTON
    btn_text = "✨ GENERATE INK (1 Credit)"
    if st.session_state["uploaded_ref_image"] is not None:
        btn_text = "✨ MODIFY IMAGE (1 Credit)"

    if st.button(btn_text, type="primary", use_container_width=True):
        if credits < 1: st.error("You're out of credits! Please top up.")
        elif not user_prompt and st.session_state["uploaded_ref_image"] is None: st.warning("Please describe your idea or upload an image.")
        else:
            spinner_text = "Creating detailed stencil..."
            if st.session_state["uploaded_ref_image"] is not None:
                spinner_text = "Processing image and applying changes..."
                
            with st.spinner(spinner_text):
                new_credits = deduct_credit(user, credits)
                # Görseli de fonksiyona gönderiyoruz
                img, err = generate_tattoo_stencil(user_prompt, style, placement, st.session_state["uploaded_ref_image"])
                if img:
                    st.session_state["generated_img"] = img
                    st.session_state["last_prompt"] = user_prompt
                    st.session_state["last_style"] = style
                    st.session_state["last_placement"] = placement
                    st.session_state["credits"] = new_credits
                    # İşlem bitince yüklenen görseli temizleyelim ki kafa karıştırmasın
                    st.session_state["uploaded_ref_image"] = None 
                    st.rerun()
                else: st.error(err)

# SONUÇ EKRANI
else:
    st.markdown("<h2 style='text-align:center;'>Your Design is Ready! 🔥</h2>", unsafe_allow_html=True)
    
    with st.container():
        img = st.session_state["generated_img"]
        col1, col2, col3 = st.columns([1,6,1])
        with col2:
             st.image(img, caption="High-Detail Procreate Style Stencil", use_column_width=True)

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    st.markdown(get_image_download_link(img, "fallink_design.png", "Save Image to Photos"), unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    
    with st.expander("📧 Email this design to client"):
        customer_email = st.text_input("Customer Email", placeholder="client@example.com")
        if st.button("Send Email Now", type="primary", use_container_width=True):
            if customer_email:
                with st.spinner("Sending email..."):
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    success, msg = send_email_with_design(customer_email, buf, st.session_state["last_prompt"])
                    if success: st.success(f"✅ Sent to {customer_email}!")
                    else: st.error(f"Error: {msg}")

    st.markdown("---")
    
    st.markdown("#### ✏️ Refine & Regenerate")
    st.caption("Not quite right? Tweak the idea and try again.")
    
    with st.container():
        # Not: Refine kısmında görsel yükleme şimdilik yok, sadece prompt ile düzeltme var.
        # Karmaşıklığı önlemek için böyle bıraktım.
        new_prompt_input = st.text_area("Edit your idea:", value=st.session_state["last_prompt"], height=100)
        
        style_options_refine = ("Fine Line", "Micro Realism", "Dotwork/Mandala", "Old School (Traditional)", "Sketch/Abstract", "Tribal/Blackwork", "Japanese (Irezumi)", "Geometric", "Watercolor", "Neo-Traditional", "Trash Polka", "Cyber Sigilism", "Chicano", "Engraving/Woodcut", "Minimalist")
        current_style = st.session_state["last_style"]
        idx = style_options_refine.index(current_style) if current_style in style_options_refine else 0
        new_style = st.selectbox("Change Style", style_options_refine, index=idx)
             
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        if st.button("🔄 Update Design (1 Credit)", type="primary", use_container_width=True):
             if credits < 1: st.error("Not enough credits!")
             else:
                 with st.spinner("Updating design..."):
                    new_credits = deduct_credit(user, credits)
                    # Refine ederken görsel göndermiyoruz, sadece text bazlı düzeltme yapıyoruz.
                    img, err = generate_tattoo_stencil(new_prompt_input, new_style, st.session_state["last_placement"])
                    if img:
                        st.session_state["generated_img"] = img
                        st.session_state["last_prompt"] = new_prompt_input
                        st.session_state["last_style"] = new_style
                        st.session_state["credits"] = new_credits
                        st.rerun()
                    else: st.error(err)

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    if st.button("Start Fresh (New Design)", type="secondary", use_container_width=True):
        st.session_state["generated_img"] = None
        st.session_state["uploaded_ref_image"] = None # Görseli de temizle
        st.rerun()
