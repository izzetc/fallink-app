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
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---

def image_to_base64(img_pil):
    buff = BytesIO()
    img_pil.save(buff, format="PNG")
    img_str = base64.b64encode(buff.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def render_hover_image(img_pil, filename, unique_id):
    img_b64 = image_to_base64(img_pil)
    download_icon = """<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>"""
    
    html_code = f"""
    <style>
        .img-container-{unique_id} {{
            position: relative;
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
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
        <a href="{img_b64}" target="_blank" class="img-link">
            <img src="{img_b64}" alt="Tattoo Design">
        </a>
        <a href="{img_b64}" download="{filename}" class="download-btn-{unique_id}" title="Download Image">
            {download_icon}
        </a>
    </div>
    """
    components.html(html_code, height=320)

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

# --- 80 ADET DETAYLI PINTEREST POPÜLER DÖVME FİKİRLERİ ---
def get_random_prompt():
    prompts = [
        "A hyper-realistic lion portrait roaring, wearing a royal crown encrusted with jewels. The mane should fade into geometric shapes and mandalas at the bottom. High contrast black and grey shading with intense eye detail.",
        "A delicate floral bouquet featuring peonies, roses, and lavender stems tied together with a thin ribbon. Fine line style with minimal shading, focusing on the intricate details of the petals and leaves.",
        "A majestic stag standing in a misty forest, with antlers branching out into tree roots that connect to the earth. Double exposure style mixing nature scenery within the silhouette of the animal.",
        "An intricate pocket watch with exposed mechanical gears and springs, surrounded by smoke and rose petals. The time is set to 5:00. Realism style with deep shadows and metallic textures.",
        "A Japanese dragon winding around a samurai sword (Katana). The scales should be highly detailed with traditional waves and clouds in the background. Irezumi style with bold outlines and heavy black shading.",
        "A minimalist single-line drawing of two faces kissing, forming a heart shape in the negative space. The line should be continuous and fluid, creating an abstract and artistic look.",
        "A creepy-cute tarot card design of 'The Moon', featuring a skeleton cat sitting on a crescent moon. Surrounded by twinkling stars and occult symbols. Woodcut engraving style with cross-hatching.",
        "A fierce Viking warrior skull with a long braided beard and a cracked helmet. Two crossed battle axes behind the skull. Nordic runes engraved on the forehead. Blackwork style with gritty texture.",
        "A serene jellyfish floating in space, with tentacles turning into constellations and galaxy dust. Dotwork shading style (stippling) to create a soft, ethereal glow effect.",
        "A detailed compass rose with a world map in the background. An arrow piercing through the center pointing North. Travel theme with coordinates written in a typewriter font.",
        "A geometric wolf head split down the middle. The left side is realistic fur texture, the right side is low-poly geometric wireframe. Connecting the two sides with glitch effects.",
        "A mythical Phoenix rising from ashes, wings spread wide. The feathers should turn into flames at the tips. Dynamic composition with a sense of movement. Illustrative black and grey style.",
        "A neo-traditional lady face with a gypsy headscarf and large hoop earrings. She is crying tears that turn into diamonds. Surrounded by old-school roses and a dagger.",
        "A spooky haunted house on a hill with bats flying out of the chimney. A full moon in the background with a silhouette of a witch. Dark art style with heavy black fill.",
        "An anatomical heart with flowers blooming out of the arteries and veins. The heart should look realistic, while the flowers are delicate and illustrative. Exploring the balance of life and death.",
        "A cyberpunk geisha with half of her face robotic, showing wires and circuits underneath the skin. Wearing traditional kimono but with futuristic neon-style patterns (in black ink).",
        "A detailed hourglass where the sand is flowing upwards, defying gravity. Inside the bottom glass is a skull, top glass has a tree of life. Symbolizing time and rebirth.",
        "A realistic eye crying a galaxy. The iris should look like a black hole sucking in light. The tears are stars and planets dripping down. Surrealism style.",
        "A fierce tiger prowling through bamboo stalks. Japanese traditional style with bold wind bars and cherry blossoms falling around. Dynamic pose showing muscle definition.",
        "A snake wrapped tightly around a dagger, with its mouth open showing fangs. The dagger handle is ornate and jeweled. Traditional Old School style with bold lines.",
        "A whimsical Alice in Wonderland theme features the Cheshire Cat grinning in a tree, with a melting clock and playing cards falling around. Sketchy, illustrative style.",
        "A wise owl perched on a stack of vintage books, wearing reading glasses. A quill pen and ink pot nearby. Symbolizing wisdom and knowledge. Engraving style.",
        "A Medusa head with snakes for hair, eyes turning to stone. The expression should be terrifying yet beautiful. High contrast realism with focus on the texture of the snakes.",
        "A majestic eagle swooping down with talons out, ready to strike. American Traditional style with bold lines and heavy shading on the wings.",
        "A delicate moth with a skull pattern on its wings. Beneath it, phases of the moon. Witchy, mystical vibe with fine dotwork shading.",
        "A roaring bear standing on its hind legs, with a mountain landscape inside its silhouette. Double exposure style, blending animal and nature.",
        "A cyber-sigilism tribal pattern running down the spine. Sharp, aggressive spikes and flowing chrome-like curves. Y2K futuristic aesthetic.",
        "A realistic portrait of a Greek statue (David or Zeus) that is cracked and broken, revealing a golden skeleton underneath (in black/grey). Vaporwave aesthetic.",
        "A cute astronaut sitting on a swing that hangs from a planet. Stars and comets in the background. Minimalist line art style.",
        "A detailed ship in a bottle, tossing in stormy waves. The bottle is cracked and leaking water. Traditional style with cross-hatching.",
        "A sacred geometry mandala with a lotus flower in the center. Intricate symmetry and precise lines. Dotwork shading for depth.",
        "A grim reaper playing chess with a human. The board is set on a tombstone. Dark, gothic style with heavy shadows.",
        "A koi fish swimming upstream, transforming into a dragon. Symbolizing perseverance. Japanese Irezumi style with wave backgrounds.",
        "A minimalist mountain range with a pine forest reflection in a lake below. Enclosed in a diamond geometric shape. Clean fine lines.",
        "A vintage microphone with musical notes and roses wrapping around the stand. Realistic style, perfect for a musician.",
        "A raven perched on top of a human skull. The skull has a candle melting on top of it. Poe-inspired gothic literature theme.",
        "A detailed spider web with a dew drop in the center reflecting a skull. Spooky and intricate. Fine line style.",
        "An Egyptian Anubis god in profile, holding a staff. Hieroglyphs in the background. Stone texture effect.",
        "A whimsical hot air balloon where the balloon is actually a giant human brain. Steampunk style with gears and pipes.",
        "A realistic hand holding a tarot card. The card is 'Death' but depicts a new beginning. Mystical style.",
        "A cherry blossom branch blowing in the wind. Petals falling dynamically. Soft shading, very delicate and feminine.",
        "A fierce gladiator helmet with two crossed swords behind it. Roman numerals for a date underneath. Realistic metallic texture.",
        "A tree of life with roots extending deep into the ground and branches reaching high. Celtic knots integrated into the bark.",
        "A broken chain with a bird flying free from it. Symbolizing freedom. Sketch style with loose lines.",
        "A realistic portrait of a pet dog (French Bulldog) wearing a tuxedo and monocle. Funny and detailed.",
        "A DNA helix where the strands are made of tree branches and leaves. Combining science and nature.",
        "A retro cassette tape with the tape ribbon pulled out, forming the word 'Music'. 80s nostalgia style.",
        "A detailed feather turning into a flock of birds flying away at the tip. Silhouette style.",
        "A lighthouse standing strong against giant crashing waves. Traditional style with bold outlines.",
        "A weeping angel statue covering its face. Stone texture and moss details. Gothic atmosphere.",
        "A barcode melting into liquid drips. Cyberpunk / Glitch art style.",
        "A majestic elephant head with Indian mandala patterns decorating its trunk and ears. Ornamental style.",
        "A classic pin-up girl sitting on a bomb. WWII bomber nose art style. Old school traditional.",
        "A detailed scorpion ready to strike. Realistic texture on the shell. 3D shadow effect.",
        "A phases of the moon cycle (full to new) arranged vertically. Minimalist dotwork.",
        "A spooky bat with wings spread, hanging upside down from a branch. Gothic engraving style.",
        "A realistic heart padlock with a skeleton key. The keyhole glows. Symbolizing a locked heart.",
        "A paper crane origami figure. Geometric lines and shading to show paper folds.",
        "A intricate dreamcatcher with feathers and beads. Realistic texture.",
        "A fierce panther crawling down, claws out. Traditional Panther tattoo style.",
        "A detailed map of Middle Earth (Lord of the Rings style). Aged paper texture look.",
        "A hummingbird drinking nectar from a hibiscus flower. frozen in flight. High detail.",
        "A set of knuckles with 'STAY TRUE' written in Old English font. Chicano lettering style.",
        "A scary clown face (It style) peeking out from a sewer grate. Horror realism.",
        "A majestic horse galloping, mane flowing in the wind. Sketchy artistic style.",
        "A detailed rosary bead necklace with a cross. Realistic shadows to look like it's resting on skin.",
        "A butterfly where one wing is normal and the other is made of flowers. Surreal nature.",
        "A yin yang symbol made of two koi fishes. Balance and harmony.",
        "A detailed chess piece (King) that is falling over. Checkmate concept.",
        "A sunflower field with a sunset in the background. Framed in a circle.",
        "A mystical crystal ball with a fortune teller's hands around it. Smoke inside the ball.",
        "A detailed grand piano with sheet music flying around. Artistic music theme.",
        "A cute ghost holding a flower. Cartoon new school style.",
        "A fierce shark with mouth open, breaking through the water surface. Realistic water effects.",
        "A detailed dragonfly with intricate lace patterns on its wings.",
        "A minimalist skyline of New York City. Single line drawing.",
        "A pair of angel wings. Highly detailed feather texture.",
        "A retro robot toy. Vintage sci-fi style.",
        "A detailed anatomical skull with a crown of roses. Life and death contrast."
    ]
    return random.choice(prompts)

# --- ANA AI FONKSİYONU ---
def generate_tattoo_design(user_prompt, style, placement):
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

        # --- YENİ PROMPT MANTIĞI ---
        # Placement'ı sadece şekil/akış (Flow) için kullanıyoruz. Asla çizdirmiyoruz.
        base_prompt = f"A highly detailed, professional tattoo design showing: {user_prompt}. The design flow and shape is optimized for a '{placement}' placement, BUT show ONLY the isolated artwork on white paper."

        technical_requirements = (
            "CRITICAL OUTPUT RULES: The final image MUST show ONLY the isolated tattoo artwork centered on a plain white background. "
            "It must NOT show any human body parts, skin, arms, legs, or models. "
            "Do NOT generate realistic skin textures, blood, or redness. "
            "The style must be a clean, finished black ink flash design ready for transfer."
        )
        
        final_prompt = f"{base_prompt} Style details: {selected_style_description}. {technical_requirements}"

        # IMAGEN ÇAĞRISI
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=final_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"}
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            return Image.open(BytesIO(image_bytes)), None
        return None, "AI returned empty response."
    except Exception as e:
        return None, str(e)

# --- UYGULAMA AKIŞI ---

if "generated_img_list" not in st.session_state:
    st.session_state["generated_img_list"] = [] 

# State'leri başlatırken varsayılan değerleri ata
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

# 3. STÜDYO ARAYÜZÜ
user = st.session_state["logged_in_user"]
credits = check_user_credits(user)

st.markdown(f"""
<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>
    <div class='fallink-logo' style='font-size: 2rem;'>Fallink</div>
    <div class='credit-info'>{credits} Credits</div>
</div>
""", unsafe_allow_html=True)

# GİRİŞ ALANI (Liste boşsa göster)
if not st.session_state["generated_img_list"]:
    
    # KART 1: Fikir Alanı
    with st.container():
        st.markdown("### 1. Describe Concept")
        
        # Random butonu, text_area'nın değerini güncelleyecek
        if st.button("Random Idea Inspiration", type="secondary", use_container_width=True):
            st.session_state["last_prompt"] = get_random_prompt()
            st.rerun() # Değeri kutuya yansıtmak için sayfayı yenile

        # Text area session state'ten değer alır
        user_prompt = st.text_area("What do you want to create?", height=120, value=st.session_state["last_prompt"], placeholder="E.g. 'A geometric wolf'...")
        
    # KART 2: Seçenekler (PLACEMENT EKLENDİ)
    with st.container():
        st.markdown("### 2. Customize Details")
        
        style_options = ("Fine Line", "Micro Realism", "Dotwork/Mandala", "Old School (Traditional)", "Sketch/Abstract", "Tribal/Blackwork", "Japanese (Irezumi)", "Geometric", "Watercolor", "Neo-Traditional", "Trash Polka", "Cyber Sigilism", "Chicano", "Engraving/Woodcut", "Minimalist")
        style = st.selectbox("Choose Style", style_options)
        
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) 

        # PLACEMENT GERİ GELDİ (Sadece Flow için)
        placement_options = ("Forearm (Inner)", "Forearm (Outer)", "Upper Arm / Bicep", "Shoulder", "Chest", "Back (Upper)", "Back (Full)", "Spine", "Ribs / Side", "Thigh", "Calf", "Ankle", "Wrist", "Hand", "Finger", "Neck", "Behind Ear", "Other (Custom)")
        placement_select = st.selectbox("Body Placement (Defines Flow/Shape Only)", placement_options)
        
        if placement_select == "Other (Custom)":
            placement = st.text_input("Specify placement flow", placeholder="e.g. Knuckles flow")
        else:
            placement = placement_select

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ANA BUTON
    if st.button("GENERATE DESIGN (1 Credit)", type="primary", use_container_width=True):
        if credits < 1: st.error("You're out of credits. Please top up.")
        elif not user_prompt: st.warning("Please describe your idea.")
        else:
            with st.spinner("Creating tattoo design..."):
                new_credits = deduct_credit(user, credits)
                # Placement artık fonksiyona gidiyor
                img, err = generate_tattoo_design(user_prompt, style, placement)
                if img:
                    st.session_state["generated_img_list"].append(img)
                    st.session_state["last_prompt"] = user_prompt
                    st.session_state["last_style"] = style
                    st.session_state["last_placement"] = placement
                    st.session_state["credits"] = new_credits
                    st.rerun()
                else: st.error(err)

# SONUÇ EKRANI (ÇOKLU GÖRSEL)
else:
    st.markdown("<h2 style='text-align:center;'>Generated Designs</h2>", unsafe_allow_html=True)
    st.caption("Click image to zoom. Hover for download icon.")
    
    images = st.session_state["generated_img_list"]
    num_images = len(images)
    
    for i in range(0, num_images, 2):
        cols = st.columns(2)
        with cols[0]:
            render_hover_image(images[i], f"fallink_design_{i+1}.png", i)
        
        if i + 1 < num_images:
            with cols[1]:
                render_hover_image(images[i+1], f"fallink_design_{i+2}.png", i+1)
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    with st.expander("Email latest design to client"):
        st.caption("The last generated image will be sent.")
        customer_email = st.text_input("Customer Email", placeholder="client@example.com")
        if st.button("Send Email Now", type="primary", use_container_width=True):
            if customer_email and images:
                with st.spinner("Sending email..."):
                    latest_img = images[-1]
                    buf = BytesIO()
                    latest_img.save(buf, format="PNG")
                    buf.seek(0)
                    success, msg = send_email_with_design(customer_email, buf, st.session_state["last_prompt"])
                    if success: st.success(f"Sent to {customer_email}.")
                    else: st.error(f"Error: {msg}")

    st.markdown("---")
    
    st.markdown("#### Refine & Create New Version")
    st.caption("Tweak the details to generate a new version.")
    
    with st.container():
        new_prompt_input = st.text_area("Edit concept details:", value=st.session_state["last_prompt"], height=100)
        
        style_options_refine = ("Fine Line", "Micro Realism", "Dotwork/Mandala", "Old School (Traditional)", "Sketch/Abstract", "Tribal/Blackwork", "Japanese (Irezumi)", "Geometric", "Watercolor", "Neo-Traditional", "Trash Polka", "Cyber Sigilism", "Chicano", "Engraving/Woodcut", "Minimalist")
        
        # Hata önleyici index bulma
        try:
            current_style_idx = style_options_refine.index(st.session_state["last_style"])
        except:
            current_style_idx = 0
            
        new_style = st.selectbox("Change Style", style_options_refine, index=current_style_idx)
        
        # Placement seçimi burada da var
        placement_options = ("Forearm (Inner)", "Forearm (Outer)", "Upper Arm / Bicep", "Shoulder", "Chest", "Back (Upper)", "Back (Full)", "Spine", "Ribs / Side", "Thigh", "Calf", "Ankle", "Wrist", "Hand", "Finger", "Neck", "Behind Ear", "Other (Custom)")
        
        # Eski seçimi hatırlama
        try:
            # Eğer custom bir şey yazıldıysa onu listede bulamayız, varsayılan 0 olsun
            if st.session_state["last_placement"] in placement_options:
                current_place_idx = placement_options.index(st.session_state["last_placement"])
            else:
                current_place_idx = 0 
        except:
            current_place_idx = 0

        new_placement_select = st.selectbox("Change Body Placement", placement_options, index=current_place_idx)
        
        if new_placement_select == "Other (Custom)":
            new_placement = st.text_input("Specify placement flow", placeholder="e.g. Knuckles flow")
        else:
            new_placement = new_placement_select
             
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        if st.button("GENERATE NEW VERSION (1 Credit)", type="primary", use_container_width=True):
             if credits < 1: st.error("Not enough credits.")
             else:
                 with st.spinner("Generating new version..."):
                    new_credits = deduct_credit(user, credits)
                    img, err = generate_tattoo_design(new_prompt_input, new_style, new_placement)
                    if img:
                        st.session_state["generated_img_list"].append(img)
                        st.session_state["last_prompt"] = new_prompt_input
                        st.session_state["last_style"] = new_style
                        st.session_state["last_placement"] = new_placement
                        st.session_state["credits"] = new_credits
                        st.rerun()
                    else: st.error(err)

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    if st.button("Start Fresh (Clear All)", type="secondary", use_container_width=True):
        st.session_state["generated_img_list"] = [] 
        st.session_state["last_prompt"] = "" # Promptu da temizle
        st.rerun()
