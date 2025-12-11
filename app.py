import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO
import base64
import time
import random
import uuid 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from supabase import create_client, Client
import streamlit.components.v1 as components

# --- GİZLİ BİLGİLERİ (SECRETS) ÇEKME ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    EMAIL_USER = st.secrets["EMAIL_USER"]
    EMAIL_PASSWORD = st.secrets["EMAIL_PASSWORD"]
except:
    st.error("Eksik Anahtarlar! Lütfen Streamlit Secrets ayarlarını kontrol et.")
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #121212 !important;
        color: #E0E0E0 !important;
    }
    .stApp {
        background-color: #121212;
    }

    /* --- NÜKLEER TEMİZLİK --- */
    footer {visibility: hidden !important; display: none !important; height: 0px !important;}
    #MainMenu {visibility: hidden !important; display: none !important;}
    .stDeployButton {display:none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    
    div[data-testid="stContainer"], div[data-testid="stExpander"] {
        background-color: #1E1E1E;
        border-radius: 16px;
        border: 1px solid #333;
        padding: 20px;
        margin-bottom: 15px;
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
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8A2BE2, #4B0082) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 16px 24px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(138, 43, 226, 0.4) !important;
        width: 100%;
        text-transform: uppercase;
    }
    
    .stButton > button[kind="secondary"] {
        background-color: #333333 !important;
        color: #E0E0E0 !important;
        border-radius: 12px !important;
        border: 1px solid #555 !important;
        font-weight: 600 !important;
        width: 100%;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
        max-width: 600px;
    }
    
    .credit-info {
        text-align: right;
        font-weight: 700;
        color: #E0E0E0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---

def render_hover_image_from_url(image_url, filename, unique_id):
    download_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>"""
    
    html_code = f"""
    <style>
        .img-container-{unique_id} {{
            position: relative;
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            margin-bottom: 10px;
        }}
        .img-container-{unique_id} img {{
            width: 100%;
            display: block;
            transition: transform 0.3s ease;
        }}
        .img-link {{ display: block; cursor: zoom-in; }}
        .download-btn-{unique_id} {{
            position: absolute; top: 10px; right: 10px;
            background-color: rgba(0, 0, 0, 0.6); color: white;
            padding: 8px; border-radius: 50%;
            opacity: 0; transition: all 0.3s ease;
            cursor: pointer; display: flex;
            align-items: center; justify-content: center;
            text-decoration: none; backdrop-filter: blur(4px);
        }}
        .img-container-{unique_id}:hover .download-btn-{unique_id} {{ opacity: 1; }}
        .download-btn-{unique_id}:hover {{ background-color: #A855F7; }}
    </style>
    <div class="img-container-{unique_id}">
        <a href="{image_url}" target="_blank" class="img-link">
            <img src="{image_url}" alt="Tattoo Design">
        </a>
        <a href="{image_url}" download="{filename}" class="download-btn-{unique_id}" title="Download Image">
            {download_icon}
        </a>
    </div>
    """
    components.html(html_code, height=320)

def save_design_to_history(username, img_pil, prompt, style):
    try:
        bucket_name = "generated-tattoos" 
        file_name = f"{username}_{uuid.uuid4()}.png"
        buff = BytesIO()
        img_pil.save(buff, format="PNG")
        image_bytes = buff.getvalue()
        supabase.storage.from_(bucket_name).upload(file_name, image_bytes, {"content-type": "image/png"})
        image_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        data = {
            "username": username,
            "image_url": image_url,
            "prompt": prompt,
            "style": style
        }
        supabase.table("user_designs").insert(data).execute()
        return image_url
    except Exception as e:
        st.error(f"Kayıt Hatası: {str(e)}")
        return None

def get_user_gallery(username):
    try:
        response = supabase.table("user_designs").select("*").eq("username", username).order("created_at", desc=True).execute()
        return response.data
    except:
        return []

def send_email_with_design(to_email, img_buffer, prompt):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = "Fallink Tattoo Design Ready"
    body = f"""<html><body style='font-family: sans-serif; color: #333;'>
        <h2>Your Design is Here</h2>
        <p>Here is the high-detail AI tattoo design generated by Fallink Studio.</p>
        <p><strong>Concept:</strong> {prompt}</p>
        <br><p>See you at the studio.</p><p><em>Fallink Team</em></p>
      </body></html>"""
    msg.attach(MIMEText(body, 'html', 'utf-8'))
    img_buffer.seek(0)
    image_data = img_buffer.getvalue()
    image = MIMEImage(image_data, name="fallink_design.png")
    msg.attach(image)
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully."
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

# --- NÖTRLEŞTİRİLMİŞ RANDOM PROMPTLAR ---
def get_random_prompt():
    prompts = [
        "A lion portrait roaring, wearing a royal crown encrusted with jewels.",
        "A delicate floral bouquet featuring peonies, roses, and lavender stems tied together.",
        "A majestic stag standing in a forest, with antlers branching out into tree roots.",
        "An intricate pocket watch with exposed mechanical gears and springs.",
        "A dragon winding around a samurai sword (Katana).",
        "A minimalist drawing of two faces kissing, forming a heart shape.",
        "A skeleton cat sitting on a crescent moon.",
        "A Viking warrior skull with a long braided beard and a cracked helmet.",
        "A jellyfish floating in space, with tentacles turning into constellations.",
        "A compass rose with a world map in the background.",
        "A wolf head split down the middle. Left side fur, right side geometric wireframe.",
        "A Phoenix rising from ashes, wings spread wide.",
        "A lady face with a gypsy headscarf and large hoop earrings.",
        "A haunted house on a hill with bats flying out of the chimney.",
        "An anatomical heart with flowers blooming out of the arteries and veins.",
        "A geisha with half of her face robotic.",
        "An hourglass where the sand is flowing upwards.",
        "An eye crying a galaxy.",
        "A tiger prowling through bamboo stalks.",
        "A snake wrapped around a dagger, mouth open showing fangs.",
        "Cheshire Cat grinning in a tree, with a melting clock and playing cards.",
        "An owl perched on a stack of vintage books.",
        "A Medusa head with snakes for hair.",
        "An eagle swooping down with talons out.",
        "A moth with a skull pattern on its wings.",
        "A bear standing on hind legs, with a mountain landscape inside its silhouette.",
        "A pattern running down the spine with sharp spikes and curves.",
        "A portrait of a Greek statue (David) that is cracked.",
        "An astronaut sitting on a swing that hangs from a planet.",
        "A ship in a bottle, tossing in waves.",
        "A mandala with a lotus flower in the center.",
        "A grim reaper playing chess with a human.",
        "A koi fish swimming upstream, transforming into a dragon.",
        "A mountain range with a pine forest reflection in a lake.",
        "A vintage microphone with musical notes and roses.",
        "A raven perched on top of a skull.",
        "A spider web with a dew drop in the center reflecting a skull.",
        "An Egyptian Anubis god holding a staff.",
        "A hot air balloon where the balloon is a giant human brain.",
        "A hand holding a tarot card.",
        "A cherry blossom branch blowing in the wind.",
        "A gladiator helmet with two crossed swords.",
        "A tree of life with roots deep in the ground.",
        "A broken chain with a bird flying free.",
        "A portrait of a French Bulldog wearing a tuxedo.",
        "A DNA helix made of tree branches and leaves.",
        "A retro cassette tape.",
        "A feather turning into a flock of birds.",
        "A lighthouse standing against crashing waves.",
        "A weeping angel statue covering its face.",
        "A barcode melting into liquid drips.",
        "An elephant head with mandala patterns.",
        "A pin-up girl sitting on a bomb.",
        "A scorpion ready to strike.",
        "Phases of the moon cycle arranged vertically.",
        "A bat hanging upside down from a branch.",
        "A heart padlock with a skeleton key.",
        "A paper crane origami figure.",
        "A dreamcatcher with feathers and beads.",
        "A panther crawling down, claws out.",
        "A map of Middle Earth.",
        "A hummingbird drinking from a hibiscus flower.",
        "Knuckles with 'STAY TRUE' written on them.",
        "A scary clown face peeking from a sewer.",
        "A horse galloping, mane flowing.",
        "A rosary bead necklace with a cross.",
        "A butterfly with one wing made of flowers.",
        "A yin yang symbol made of two koi fishes.",
        "A chess piece (King) falling over.",
        "A sunflower field with a sunset.",
        "A crystal ball with a fortune teller's hands.",
        "A grand piano with sheet music flying.",
        "A cute ghost holding a flower.",
        "A shark breaking through water surface.",
        "A dragonfly with lace pattern wings.",
        "A skyline of New York City.",
        "A pair of angel wings.",
        "A retro robot toy.",
        "An anatomical skull with a crown of roses."
    ]
    return random.choice(prompts)

# --- ANA AI FONKSİYONU (MEMORY WIPE & STRICT FOCUS) ---
def generate_tattoo_design(user_prompt, style, placement):
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        style_details = {
            "Fine Line": "Extremely thin single needle lines, minimalist, NO shading, NO heavy blacks, delicate, elegant, airy, outline only.",
            "Micro Realism": "Photorealistic detail in small scale, sophisticated soft grey shading, depth, 3D effect, complex textures.",
            "Dotwork/Mandala": "Stippling texture, pointillism, intricate sacred geometry patterns, shading created strictly by dots, no solid grey fill.",
            "Old School (Traditional)": "Bold thick outlines, heavy black shading, limited palette, flat 2D look, iconic vintage flash.",
            "Sketch/Abstract": "Pencil sketch texture, rough artistic lines, cross-hatching shading, dynamic composition, unfinished artistic edges.",
            "Tribal/Blackwork": "Solid black fill, heavy bold shapes, maori or polynesian influence, high contrast, negative space patterns.",
            "Japanese (Irezumi)": "Traditional japanese fluid style, waves, wind bars, bold flowing outlines, atmospheric background.",
            "Geometric": "Mathematical shapes, polygons, sharp straight lines, architectural precision, symmetry, sacred geometry.",
            "Watercolor": "Black and grey ink wash style, liquid textures, artistic drips, soft gradients mimicking watercolor painting.",
            "Neo-Traditional": "Illustrative realism, varying line weights, art nouveau influence, decorative filigree, detailed but with outlines.",
            "Trash Polka": "Chaotic composition, realism mixed with abstract brush strokes and bold typography, high energy, collage style.",
            "Cyber Sigilism": "Futuristic sharp spikes, aggressive flowing lines, Y2K aesthetic, chrome-like texture feel, bio-mechanical.",
            "Chicano": "Smooth black and grey shading, fine script lettering, realistic portraits, soft shadows, street culture aesthetic.",
            "Engraving/Woodcut": "Vintage illustration, dense cross-hatching, linocut texture, antique book print look.",
            "Minimalist": "Extremely simple, very few lines, symbolic, clean, lots of white negative space, outline only."
        }
        
        selected_style_desc = style_details.get(style, "clean professional tattoo design")

        placement_shape_map = {
            "Forearm (Inner)": "vertical and narrow composition",
            "Forearm (Outer)": "vertical and elongated composition",
            "Upper Arm / Bicep": "vertical oval composition",
            "Shoulder": "rounded or cap-like composition",
            "Chest": "wide horizontal composition",
            "Back (Upper)": "broad expansive composition",
            "Back (Full)": "large vertical detailed composition",
            "Spine": "long thin vertical composition",
            "Ribs / Side": "curved vertical composition",
            "Thigh": "large vertical oval composition",
            "Calf": "vertical tapered composition",
            "Ankle": "small horizontal band or spot composition",
            "Wrist": "small delicate horizontal composition",
            "Hand": "compact diamond or circular composition",
            "Finger": "tiny vertical minimal composition",
            "Neck": "vertical narrow composition",
            "Behind Ear": "small curved composition",
            "Other (Custom)": "balanced centered composition"
        }
        
        shape_instruction = placement_shape_map.get(placement, "balanced centered composition")

        # --- KRİTİK PROMPT MÜDAHALESİ (KONU ODAKLI) ---
        final_prompt = (
            f"**SUBJECT:** A professional tattoo design of {user_prompt}. "
            f"**STYLE:** {style} ({selected_style_desc}). "
            f"**COMPOSITION:** {shape_instruction}. "
            "**STRICT RULES:** "
            "1. ISOLATE THE SUBJECT: Draw ONLY the specific subject requested in the prompt. "
            "2. NO FILLERS: Do NOT add background elements, flowers, frames, ribbons, books, or generic decorations unless explicitly asked for in the subject description. "
            "3. NO BODY PARTS: Draw on a plain white background. No skin, arms, or models. "
            "4. NO TEXT: Do not write any text or labels. "
            "5. NO COLORS: Use only black ink. "
        )

        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=final_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            return Image.open(BytesIO(image_bytes)), None
        
        return None, "Güvenlik Politikası: Bu içerik oluşturulamadı. Lütfen farklı bir tarif deneyin."
        
    except Exception as e:
        return None, str(e)

# --- UYGULAMA AKIŞI ---

# State'leri başlat
if "generated_img_list" not in st.session_state:
    st.session_state["generated_img_list"] = [] 

if "last_prompt" not in st.session_state:
    st.session_state["last_prompt"] = ""
if "last_style" not in st.session_state:
    st.session_state["last_style"] = "Fine Line"
if "last_placement" not in st.session_state:
    st.session_state["last_placement"] = "Forearm (Inner)"

# 2. LOGIN EKRANI
if "logged_in_user" not in st.session_state:
    st.markdown("<div style='margin-top: 80px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center;'>
            <h1 class='fallink-logo' style='font-size: 4rem; margin: 0;'>Fallink</h1>
            <p style='color:#aaa; margin-top: 10px; font-weight: 600;'>AI Tattoo Design Studio</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        username_input = st.text_input("Enter Access Code", placeholder="Code here...")
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Enter Studio", type="primary", use_container_width=True):
            credits = check_user_credits(username_input)
            if credits == -1: st.error("Invalid code.")
            else:
                st.session_state["logged_in_user"] = username_input
                st.session_state["credits"] = credits
                st.rerun()
    st.stop()

# 3. STÜDYO ARAYÜZÜ (TAB YAPISI)
user = st.session_state["logged_in_user"]
credits = check_user_credits(user)

st.markdown(f"""
<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
    <div class='fallink-logo' style='font-size: 2rem;'>Fallink</div>
    <div class='credit-info'>{credits} Credits</div>
</div>
""", unsafe_allow_html=True)

# SEKME YAPISI (TABS)
tab1, tab2 = st.tabs(["Create Design", "My Gallery"])

# --- TAB 1: TASARIM OLUŞTURMA ---
with tab1:
    # GİRİŞ ALANI (Liste boşsa göster)
    if not st.session_state["generated_img_list"]:
        
        with st.container():
            st.markdown("### 1. Describe Concept")
            if st.button("Random Idea Inspiration", type="secondary", use_container_width=True):
                st.session_state["last_prompt"] = get_random_prompt()
                st.rerun() 
            user_prompt = st.text_area("What do you want to create?", height=120, value=st.session_state["last_prompt"], placeholder="E.g. 'A geometric wolf'...")
            
        with st.container():
            st.markdown("### 2. Customize Details")
            style_options = ("Fine Line", "Micro Realism", "Dotwork/Mandala", "Old School (Traditional)", "Sketch/Abstract", "Tribal/Blackwork", "Japanese (Irezumi)", "Geometric", "Watercolor", "Neo-Traditional", "Trash Polka", "Cyber Sigilism", "Chicano", "Engraving/Woodcut", "Minimalist")
            style = st.selectbox("Choose Style", style_options)
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) 
            placement_options = ("Forearm (Inner)", "Forearm (Outer)", "Upper Arm / Bicep", "Shoulder", "Chest", "Back (Upper)", "Back (Full)", "Spine", "Ribs / Side", "Thigh", "Calf", "Ankle", "Wrist", "Hand", "Finger", "Neck", "Behind Ear", "Other (Custom)")
            placement_select = st.selectbox("Body Placement (Defines Flow/Shape Only)", placement_options)
            if placement_select == "Other (Custom)":
                placement = st.text_input("Specify placement flow", placeholder="e.g. Knuckles flow")
            else:
                placement = placement_select

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        if st.button("GENERATE DESIGN (1 Credit)", type="primary", use_container_width=True):
            if credits < 1: st.error("You're out of credits. Please top up.")
            elif not user_prompt: st.warning("Please describe your idea.")
            else:
                with st.spinner("Creating tattoo design..."):
                    # MEMORY WIPE & CLEAN STATE
                    st.session_state["generated_img_list"] = [] 
                    
                    new_credits = deduct_credit(user, credits)
                    img, err = generate_tattoo_design(user_prompt, style, placement)
                    if img:
                        img_url = save_design_to_history(user, img, user_prompt, style)
                        if img_url:
                            st.session_state["generated_img_list"].append({
                                "img_pil": img,
                                "img_url": img_url
                            })
                        
                        st.session_state["last_prompt"] = user_prompt
                        st.session_state["last_style"] = style
                        st.session_state["last_placement"] = placement
                        st.session_state["credits"] = new_credits
                        st.rerun()
                    else: st.error(err)

    # SONUÇ EKRANI
    else:
        st.markdown("<h2 style='text-align:center;'>Generated Designs</h2>", unsafe_allow_html=True)
        images = st.session_state["generated_img_list"]
        num_images = len(images)
        for i in range(0, num_images, 2):
            cols = st.columns(2)
            with cols[0]:
                item = images[i]
                render_hover_image_from_url(item['img_url'], f"fallink_design_{i+1}.png", i)
            
            if i + 1 < num_images:
                with cols[1]:
                    item = images[i+1]
                    render_hover_image_from_url(item['img_url'], f"fallink_design_{i+2}.png", i+1)
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        st.markdown("---")
        
        with st.expander("Email latest design to client"):
            customer_email = st.text_input("Customer Email", placeholder="client@example.com")
            if st.button("Send Email Now", type="primary", use_container_width=True):
                if customer_email and images:
                    with st.spinner("Sending email..."):
                        latest_item = images[-1]
                        buff = BytesIO()
                        latest_item['img_pil'].save(buff, format="PNG")
                        success, msg = send_email_with_design(customer_email, buff, st.session_state["last_prompt"])
                        if success: st.success(f"Sent to {customer_email}.")
                        else: st.error(f"Error: {msg}")

        st.markdown("---")
        st.markdown("#### Modify & Generate New Variation")
        st.caption("Creates a new version using current settings. (Old images stay in gallery).")
        with st.container():
            new_prompt_input = st.text_area("Edit concept details:", value=st.session_state["last_prompt"], height=100)
            style_options_refine = ("Fine Line", "Micro Realism", "Dotwork/Mandala", "Old School (Traditional)", "Sketch/Abstract", "Tribal/Blackwork", "Japanese (Irezumi)", "Geometric", "Watercolor", "Neo-Traditional", "Trash Polka", "Cyber Sigilism", "Chicano", "Engraving/Woodcut", "Minimalist")
            try: current_style_idx = style_options_refine.index(st.session_state["last_style"])
            except: current_style_idx = 0
            new_style = st.selectbox("Change Style", style_options_refine, index=current_style_idx)
            placement_options = ("Forearm (Inner)", "Forearm (Outer)", "Upper Arm / Bicep", "Shoulder", "Chest", "Back (Upper)", "Back (Full)", "Spine", "Ribs / Side", "Thigh", "Calf", "Ankle", "Wrist", "Hand", "Finger", "Neck", "Behind Ear", "Other (Custom)")
            try: current_place_idx = placement_options.index(st.session_state["last_placement"]) if st.session_state["last_placement"] in placement_options else 0
            except: current_place_idx = 0
            new_placement_select = st.selectbox("Change Body Placement", placement_options, index=current_place_idx)
            new_placement = st.text_input("Specify placement flow", placeholder="e.g. Knuckles flow") if new_placement_select == "Other (Custom)" else new_placement_select
                
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
            
            if st.button("GENERATE NEW VARIATION (1 Credit)", type="primary", use_container_width=True):
                if credits < 1: st.error("Not enough credits.")
                else:
                    with st.spinner("Generating new version..."):
                        new_credits = deduct_credit(user, credits)
                        img, err = generate_tattoo_design(new_prompt_input, new_style, new_placement)
                        if img:
                            img_url = save_design_to_history(user, img, new_prompt_input, new_style)
                            if img_url:
                                st.session_state["generated_img_list"].append({
                                    "img_pil": img,
                                    "img_url": img_url
                                })
                            st.session_state["last_prompt"] = new_prompt_input
                            st.session_state["last_style"] = new_style
                            st.session_state["last_placement"] = new_placement
                            st.session_state["credits"] = new_credits
                            st.rerun()
                        else: st.error(err)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        if st.button("Start Fresh (New Concept)", type="secondary", use_container_width=True):
            st.session_state["generated_img_list"] = [] 
            st.session_state["last_prompt"] = ""
            st.rerun()

# --- TAB 2: GALERİ ---
with tab2:
    st.markdown("### Your Gallery")
    user_designs = get_user_gallery(user)
    
    if not user_designs:
        st.info("You haven't created any designs yet.")
    else:
        num_cols = 2
        cols = st.columns(num_cols)
        for idx, design in enumerate(user_designs):
            with cols[idx % num_cols]:
                render_hover_image_from_url(design['image_url'], f"gallery_design_{idx}.png", f"gal_{idx}")
