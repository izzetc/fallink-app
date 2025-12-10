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

# --- CSS TASARIM ---
st.markdown("""
# --- CSS TASARIM (iOS 17+ GLASSPHORISM STYLE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* --- GENEL SAYFA YAPISI --- */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        background-color: #F2F2F7; /* Apple Sistem Grisi */
        color: #1C1C1E;
    }
    
    /* --- INPUT ALANLARI (Buzlu Cam Etkisi) --- */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.8) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 16px !important;
        color: #1C1C1E !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.2s ease;
        padding: 12px !important;
    }
    
    /* Inputa Tıklayınca (Focus) */
    .stTextInput input:focus, .stTextArea textarea:focus {
        border: 1px solid #007AFF !important; /* Apple Mavisi */
        box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1) !important;
    }
    
    /* --- BAŞLIKLAR --- */
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        background: -webkit-linear-gradient(45deg, #1C1C1E, #3A3A3C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1.5px;
    }
    
    /* --- BUTONLAR (Apple Style) --- */
    /* Birincil Buton (Siyah) */
    .stButton > button[kind="primary"] {
        background-color: #000000 !important;
        color: white !important;
        border-radius: 99px !important; /* Tam Yuvarlak */
        padding: 14px 28px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        transition: transform 0.1s ease, box-shadow 0.2s ease;
    }
    
    /* İkincil Buton (Gri) */
    .stButton > button[kind="secondary"] {
        background-color: #E5E5EA !important;
        color: #000000 !important;
        border-radius: 99px !important;
        border: none !important;
        font-weight: 500 !important;
    }

    /* Buton Tıklama Efekti */
    .stButton > button:active {
        transform: scale(0.96);
    }
    .stButton > button:hover {
        box-shadow: 0 6px 16px rgba(0,0,0,0.2) !important;
    }

    /* --- KARTLAR & KUTULAR --- */
    div[data-testid="stExpander"], div[data-testid="stContainer"] {
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 20px;
        padding: 10px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
    }

    /* --- YÜKLEME ANİMASYONU (Spinner) --- */
    .stSpinner > div {
        border-top-color: #007AFF !important;
    }
    
    /* --- BİLGİ KUTULARI (Toast/Success) --- */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 16px !important;
        font-weight: 500;
    }

</style>
""", unsafe_allow_html=True)

# --- FONKSİYONLAR ---

def send_email_with_design(to_email, img_buffer, prompt):
    """Müşteriye tasarımı gönderir."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = "Your Fallink Tattoo Design is Ready! ✒️"

    body = f"""
    <html>
      <body>
        <h2>Your Design is Here!</h2>
        <p>Here is the high-detail AI tattoo design you created with Fallink.</p>
        <p><strong>Idea:</strong> {prompt}</p>
        <br>
        <p>See you at the studio!</p>
        <p><em>Fallink Team</em></p>
      </body>
    </html>
    """
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
        if response.data:
            return response.data[0]["credits"]
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
    return f'<a href="data:file/png;base64,{img_str}" download="{filename}" style="text-decoration:none; color:#007AFF; font-weight:600;">📥 {text}</a>'

def generate_tattoo_stencil(user_prompt, style, placement):
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        # --- GÜNCELLENMİŞ VE DETAYLANDIRILMIŞ STİL TANIMLARI ---
        style_details = {
            "Fine Line": "Intricate ultra-thin single needle lines, high precision, delicate details, elegant composition, clean blackwork.",
            "Micro Realism": "Highly detailed micro realism, sophisticated soft grey shading, photographic quality, depth, complex textures rendered in small scale.",
            "Dotwork/Mandala": "Complex stippling texture, precise pointillism, intricate sacred geometry patterns, detailed shading through dots.",
            "Old School (Traditional)": "Bold clean outlines, solid heavy black shading, highly detailed classic iconography, high contrast, finished flash sheet look.",
            "Sketch/Abstract": "Detailed artistic pencil sketch style, expressive lines, cross-hatching shading, dynamic composition, unfinished yet complex look.",
            "Tribal/Blackwork": "Intricate solid black patterns, complex Polynesian or modern ornamental shapes, high contrast, heavy saturation.",
            "Japanese (Irezumi)": "Highly detailed traditional Japanese style, complex background elements (waves/clouds), bold flowing outlines, rich detail.",
            "Geometric": "Complex mathematical shapes, intricate sacred geometry, sacred patterns, precise sharp lines, detailed architectural feel.",
            "Watercolor": "Detailed black and grey ink wash style, complex liquid textures, artistic drips, soft gradients mimicking watercolor painting.",
            "Neo-Traditional": "Highly detailed illustrated realism, varying line weights, decorative filigree, complex composition with Art Nouveau influence.",
            "Trash Polka": "Complex chaotic composition, detailed realism elements mixed with abstract brush strokes and typography, high energy.",
            "Cyber Sigilism": "Intricate futuristic sharp lines, complex aggressive patterns, Y2K aesthetic, detailed chrome-like texture feel.",
            "Chicano": "Highly detailed black and grey fine art, complex shading, realistic portraits or script, rich cultural details.",
            "Engraving/Woodcut": "Highly intricate vintage illustration style, dense cross-hatching shading, linocut texture, detailed antique print look.",
            "Minimalist": "Clean, precise, highly refined simple lines. Detail through perfect composition and negative space."
        }
        
        selected_style_description = style_details.get(style, "High detail tattoo design")

        # --- YENİ GÜÇLÜ PROMPT YAPISI (Procreate & Detay Odaklı) ---
        # Placement'ı sadece "akış" için kullanıyoruz, çizdirmemek için uyarıyoruz.
        base_prompt = (
            f"A highly detailed, finished digital tattoo design (created in Procreate style) showing: {user_prompt}. "
            f"The design flow is intended for a '{placement}' placement, but the image must show ONLY the isolated artwork on flat paper."
        )
        
        technical_requirements = (
            "REQUIREMENTS: Pure white background (Hex #FFFFFF). Deep black ink only. "
            "High contrast. ABSOLUTELY NO skin texture, NO body parts, and NO anatomy in the image. "
            "Intricate details, clean professional linework, high resolution digital illustration look. "
            "Not a simple vector, but a complex digital drawing ready for stenciling."
        )
        
        final_prompt = f"{base_prompt} Style: {selected_style_description}. {technical_requirements}"

        # API ÇAĞRISI
        response = client.models.generate_images(
            model="imagen-4.0-generate-001", 
            prompt=final_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            img = Image.open(BytesIO(image_bytes))
            return img, None
            
        return None, "AI returned empty response."
    except Exception as e:
        return None, str(e)

# --- UYGULAMA AKIŞI ---

if "generated_img" not in st.session_state:
    st.session_state["generated_img"] = None
    st.session_state["last_prompt"] = ""
    st.session_state["last_style"] = "Fine Line" 
    st.session_state["last_placement"] = "Arm"

# 1. LOGIN
if "logged_in_user" not in st.session_state:
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>Fallink.</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.container(border=True):
            username_input = st.text_input("Access Code", placeholder="Enter code...")
            if st.button("Enter Studio", use_container_width=True):
                credits = check_user_credits(username_input)
                if credits == -1:
                    st.error("Invalid code.")
                else:
                    st.session_state["logged_in_user"] = username_input
                    st.session_state["credits"] = credits
                    st.rerun()
    st.stop()

# 2. STÜDYO ARAYÜZÜ
user = st.session_state["logged_in_user"]
credits = check_user_credits(user)

c1, c2 = st.columns([3,1])
with c1:
    st.markdown(f"**Member:** {user}")
with c2:
    st.markdown(f"**Credits:** {credits} 💎")

st.markdown("---")

# Eğer görsel yoksa GİRİŞ ALANI
if st.session_state["generated_img"] is None:
    c_left, c_right = st.columns([1.5, 1])

    with c_left:
        user_prompt = st.text_area("Describe your tattoo idea", height=150, placeholder="E.g. A geometric wolf head, highly detailed...")
        
        # --- RANDOM IDEAS (50 ADET) ---
        if st.button("🎲 Random Idea"):
            ideas = [
                "A geometric wolf howling at a crescent moon", "Minimalist paper plane flying through clouds", 
                "Realistic eye crying a galaxy", "Snake wrapped around a vintage dagger", 
                "Koi fish swimming in a yin yang pattern", "Clock melting over a tree branch (Dali style)",
                "Astronaut sitting on a swing in space", "Skeleton hand holding a red rose",
                "Phoenix rising from ashes, watercolor style", "Compass with mountains inside",
                "Lion head with a crown of thorns", "Hourglass with sand turning into birds",
                "Samurai mask with cherry blossoms", "Cyberpunk geisha portrait",
                "Detailed map of Middle Earth", "Hummingbird drinking from a hibiscus flower",
                "Viking ship in a storm", "Medusa head with stone eyes",
                "Anchor entangled with octopus tentacles", "Tarot card 'The Moon' design",
                "Geometric deer head with antlers transforming into trees", "Single line drawing of a cat",
                "Moth with skull pattern on wings", "Phonograph playing musical notes",
                "Pocket watch with exposed gears", "Tree of life with deep roots",
                "Raven perched on a skull", "Abstract soundwave of a heartbeat",
                "Barcode melting into liquid", "Chess piece (King) falling over",
                "Spartan helmet with spears", "Feather turning into a flock of birds",
                "Lotus flower unalome", "Dragon wrapping around the arm",
                "Butterfly with one wing as flowers", "Vintage camera illustration",
                "Micro realistic bee", "Portrait of a Greek statue broken",
                "Cyber sigilism pattern on spine", "Trash polka style heart and arrows",
                "Egyptian Anubis god profile", "Nordic runes circle",
                "Sword piercing a heart", "Alien spaceship beaming up a cow",
                "Jellyfish floating in space", "Owl with piercing eyes",
                "Grim reaper playing chess", "Angel wings on back",
                "Dna helix made of tree branches", "Retro cassette tape"
            ]
            user_prompt = random.choice(ideas)
            st.info(f"Try this: {user_prompt}")

    with c_right:
        # --- STİL LİSTESİ (15 ADET) ---
        style_options = (
            "Fine Line", "Micro Realism", "Dotwork/Mandala", "Old School (Traditional)", 
            "Sketch/Abstract", "Tribal/Blackwork", "Japanese (Irezumi)", "Geometric",
            "Watercolor", "Neo-Traditional", "Trash Polka", "Cyber Sigilism", 
            "Chicano", "Engraving/Woodcut", "Minimalist"
        )
        style = st.selectbox("Style", style_options)
        
        # --- PLACEMENT + OTHER SEÇENEĞİ ---
        placement_options = (
            "Forearm (Inner)", "Forearm (Outer)", "Upper Arm / Bicep", "Shoulder", 
            "Chest", "Back (Upper)", "Back (Full)", "Spine", "Ribs / Side", 
            "Thigh", "Calf", "Ankle", "Wrist", "Hand", "Finger", "Neck", "Behind Ear", "Other (Custom)"
        )
        placement_select = st.selectbox("Placement (Defines Flow, Not Drawn)", placement_options)
        
        # Eğer 'Other' seçilirse yazı kutusu aç
        if placement_select == "Other (Custom)":
            placement = st.text_input("Specify placement flow", placeholder="e.g. Knuckles flow")
        else:
            placement = placement_select
        
        if st.button("Generate Ink ✨ (1 Credit)", type="primary", use_container_width=True):
            if credits < 1:
                st.error("No credits left!")
            elif not user_prompt:
                st.warning("Please describe an idea.")
            else:
                with st.spinner("Designing detailed artwork..."):
                    new_credits = deduct_credit(user, credits)
                    img, err = generate_tattoo_stencil(user_prompt, style, placement)
                    
                    if img:
                        st.session_state["generated_img"] = img
                        st.session_state["last_prompt"] = user_prompt
                        st.session_state["last_style"] = style
                        st.session_state["last_placement"] = placement
                        st.session_state["credits"] = new_credits
                        st.rerun()
                    else:
                        st.error(err)

# 3. SONUÇ EKRANI
else:
    st.markdown("### Your Design")
    
    img = st.session_state["generated_img"]
    st.image(img, caption="Fallink High-Detail Design", width=400)
    
    # İndirme ve Email
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown(get_image_download_link(img, "design.png", "Download Image"), unsafe_allow_html=True)
    with col_d2:
        with st.expander("📧 Email this design"):
            customer_email = st.text_input("Customer Email", placeholder="client@example.com")
            if st.button("Send Email"):
                if customer_email:
                    with st.spinner("Sending email..."):
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        buf.seek(0)
                        success, msg = send_email_with_design(customer_email, buf, st.session_state["last_prompt"])
                        if success:
                            st.success(f"Sent to {customer_email}!")
                        else:
                            st.error(f"Error: {msg}")

    st.markdown("---")
    
    # 4. YENİDEN DÜZENLEME (UPDATE)
    st.markdown("#### ✏️ Want changes?")
    st.caption("Refine your idea and generate a new detailed version.")
    
    with st.container(border=True):
        new_prompt_input = st.text_area("Refine your idea:", value=st.session_state["last_prompt"], height=100)
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
             # Stili tekrar seçebilsin
             style_options_refine = (
                "Fine Line", "Micro Realism", "Dotwork/Mandala", "Old School (Traditional)", 
                "Sketch/Abstract", "Tribal/Blackwork", "Japanese (Irezumi)", "Geometric",
                "Watercolor", "Neo-Traditional", "Trash Polka", "Cyber Sigilism", 
                "Chicano", "Engraving/Woodcut", "Minimalist"
            )
             current_style = st.session_state["last_style"]
             idx = 0
             if current_style in style_options_refine:
                 idx = style_options_refine.index(current_style)
                 
             new_style = st.selectbox("Style", style_options_refine, index=idx)
             
        with col_u2:
             if st.button("Update Design (1 Credit)", type="secondary", use_container_width=True):
                 if credits < 1:
                     st.error("Not enough credits!")
                 else:
                     with st.spinner("Updating design..."):
                        new_credits = deduct_credit(user, credits)
                        # Placement değişmiyor, sessiondan alıyoruz
                        img, err = generate_tattoo_stencil(new_prompt_input, new_style, st.session_state["last_placement"])
                        if img:
                            st.session_state["generated_img"] = img
                            st.session_state["last_prompt"] = new_prompt_input
                            st.session_state["last_style"] = new_style
                            st.session_state["credits"] = new_credits
                            st.rerun()
                        else:
                            st.error(err)

    if st.button("Start Fresh (Clear All)"):
        st.session_state["generated_img"] = None
        st.rerun()
