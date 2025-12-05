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
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #FAFAFA;
        color: #111;
    }
    
    /* Input alanları */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF !important; 
        color: #000000 !important;
        border: 1px solid #d1d1d1 !important;
        border-radius: 8px !important;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        color: #111;
    }
    
    /* Standart Butonlar */
    .stButton > button {
        background-color: #111 !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        border: none !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    .stButton > button:hover {
        background-color: #333 !important;
        transform: translateY(-2px);
    }

    /* Refine (Düzenleme) Kutusu Stili */
    .refine-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        margin-top: 20px;
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
        <p>Here is the AI-generated tattoo stencil you created with Fallink.</p>
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
        
        base_prompt = f"Professional tattoo stencil design of: {user_prompt}. Placement: {placement}."
        style_prompt = f"Style: {style}. Requirements: Clean white background, high contrast black ink, isolated subject, vector style, no skin texture."
        final_prompt = f"{base_prompt} {style_prompt}"

        # Tek Resim Modu
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
    st.session_state["last_style"] = "Fine Line" # Varsayılan
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

# Eğer henüz görsel üretilmediyse ANA GİRİŞ ALANINI göster
if st.session_state["generated_img"] is None:
    c_left, c_right = st.columns([1.5, 1])

    with c_left:
        user_prompt = st.text_area("Describe your tattoo idea", height=150, placeholder="E.g. A geometric wolf head...")
        if st.button("🎲 Random Idea"):
            ideas = ["Minimalist paper plane", "Snake wrapped around dagger", "Realistic eye crying galaxy", "Geometric deer head"]
            user_prompt = random.choice(ideas)
            st.info(f"Try: {user_prompt}")

    with c_right:
        style = st.selectbox("Style", ("Fine Line", "Micro Realism", "Dotwork", "Old School", "Sketch", "Tribal"))
        placement = st.selectbox("Placement", ("Arm", "Leg", "Chest", "Back", "Wrist"))
        
        if st.button("Generate Ink ✨ (1 Credit)", type="primary", use_container_width=True):
            if credits < 1:
                st.error("No credits left!")
            elif not user_prompt:
                st.warning("Please describe an idea.")
            else:
                with st.spinner("Designing..."):
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

# 3. SONUÇ EKRANI (Resim Varsa Burası Çalışır)
else:
    st.markdown("### Your Design")
    
    img = st.session_state["generated_img"]
    st.image(img, caption="Fallink AI Design", width=400)
    
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
    
    # 4. YENİDEN DÜZENLEME ALANI (UPDATE & RETRY)
    st.markdown("#### ✏️ Want changes?")
    st.caption("Not exactly what you wanted? Describe changes below to generate a new version.")
    
    with st.container(border=True):
        # Eski promptu varsayılan olarak getiriyoruz ki üzerinde oynayabilsin
        new_prompt_input = st.text_area("Refine your idea:", value=st.session_state["last_prompt"], height=100)
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
             # Stili de değiştirmek isteyebilir
             new_style = st.selectbox("Style", ("Fine Line", "Micro Realism", "Dotwork", "Old School", "Sketch", "Tribal"), index=["Fine Line", "Micro Realism", "Dotwork", "Old School", "Sketch", "Tribal"].index(st.session_state["last_style"]))
        with col_u2:
             if st.button("Update Design (1 Credit)", type="secondary", use_container_width=True):
                 if credits < 1:
                     st.error("Not enough credits!")
                 else:
                     with st.spinner("Updating design..."):
                        new_credits = deduct_credit(user, credits)
                        img, err = generate_tattoo_stencil(new_prompt_input, new_style, st.session_state["last_placement"])
                        if img:
                            st.session_state["generated_img"] = img
                            st.session_state["last_prompt"] = new_prompt_input
                            st.session_state["last_style"] = new_style
                            st.session_state["credits"] = new_credits
                            st.rerun()
                        else:
                            st.error(err)

    # En başa dönmek için buton
    if st.button("Start Fresh (Clear All)"):
        st.session_state["generated_img"] = None
        st.rerun()
