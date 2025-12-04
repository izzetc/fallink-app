import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO
import base64

# Sayfa Ayarları (Başlık ve ikon)
st.set_page_config(
    page_title="JustArt AI Tattoo Stencil Generator",
    page_icon="🎨",
    layout="centered"
)

# --- API ANAHTARINI BURAYA YAPIŞTIR ---
# (Not: Gerçek bir sitede bu anahtarı bu şekilde açık bırakmayız,
# "Secrets" denen gizli bölüme koyarız. Şimdilik test için böyle yapıyoruz.)
API_KEY = "AIzaSyD2BN8tmMSYnOIHBYJrOJnBNXDF2OnjPVI"

# --- FONKSİYONLAR ---

# 1. Resmi İndirilebilir Linke Çeviren Fonksiyon
def get_image_download_link(img, filename, text):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}" style="text-decoration: none;"><button style="background-color: #4CAF50; border: none; color: white; padding: 10px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 8px;">📥 {text} İndir</button></a>'
    return href

# 2. Dövme Üreten Ana Fonksiyon
def generate_tattoo_stencil(user_prompt, style):
    # Google İstemcisini başlat
    client = genai.Client(api_key=API_KEY)
    
    # Prompt Mühendisliği (Kullanıcının isteğini profesyonel komuta çeviriyoruz)
    base_prompt = f"Tattoo design concept: {user_prompt}."
    
    if style == "Fine Line (İnce Çizgi)":
        style_prompt = "Style: Minimalist fine line tattoo, clean single needle work, delicate details, black ink only, no shading, white background."
    elif style == "Dotwork (Nokta Çalışması)":
        style_prompt = "Style: Dotwork shading tattoo, stippling texture, geometric patterns, blackwork, high contrast, white background."
    elif style == "Engraving (Gravür)":
        style_prompt = "Style: Vintage engraving illustration, cross-hatching shading, linocut print look, black ink, detailed linework."
    elif style == "Sketch (Eskiz)":
        style_prompt = "Style: Pencil sketch tattoo design, rough lines, hand-drawn look, black and grey, artistic, white paper background."
    else: # Varsayılan (Blackwork)
        style_prompt = "Style: Bold blackwork tattoo, solid black areas, clean outlines, high contrast, traditional feel, white background."

    # Nihai Prompt (İstek + Stil + Stencil Kuralı)
    final_prompt = f"{base_prompt} {style_prompt} Output must be a clean, black and white tattoo stencil design on a plain white background, ready for transfer."

    try:
        # Görsel Üretimi (Imagen 4.0 ile)
        response = client.models.generate_images(
            model="imagen-4.0-generate-001", 
            prompt=final_prompt,
            config={"number_of_images": 1, "aspect_ratio": "1:1"} # Kare format
        )
        
        # Sonucu Döndür
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            img = Image.open(BytesIO(image_bytes))
            return img, None # Resim var, hata yok
        else:
            return None, "Resim oluşturulamadı (Boş veri)."
            
    except Exception as e:
        return None, str(e) # Resim yok, hata mesajı var

# --- ANA SAYFA TASARIMI (Frontend) ---

# Başlık ve Logo
col1, col2 = st.columns([1, 5])
with col1:
    # Buraya kendi logonun linkini koyabilirsin
    st.image("https://cdn-icons-png.flaticon.com/512/2913/2913482.png", width=60) 
with col2:
    st.title("AI Tattoo Stencil Oluşturucu")
    st.caption("JustArtTattoo.com için özel olarak hazırlanmıştır.")

st.markdown("---")

# Giriş Alanları
st.header("1. Tasarımını Tarif Et")
user_input = st.text_area("Ne çizdirmek istiyorsun?", height=100, placeholder="Örnek: Kask takmış, puro içen bir astronot şempanze...")

st.header("2. Bir Stil Seç")
selected_style = st.radio(
    "Dövmenin tarzı nasıl olsun?",
    ("Fine Line (İnce Çizgi)", "Dotwork (Nokta Çalışması)", "Engraving (Gravür)", "Sketch (Eskiz)", "Blackwork (Koyu)"),
    horizontal=True
)

st.markdown("---")

# Oluştur Butonu
if st.button("✨ Tasarımı ve Stencili Oluştur ✨", type="primary", use_container_width=True):
    if not user_input:
        st.warning("Lütfen önce ne çizdirmek istediğinizi yazın.")
    else:
        with st.spinner('Yapay zeka tasarımınızı hazırlıyor... Lütfen bekleyin (Yaklaşık 10-15 sn)'):
            # Fonksiyonu çağır
            generated_image, error_message = generate_tattoo_stencil(user_input, selected_style)
            
            if generated_image:
                st.success("Tasarım başarıyla oluşturuldu!")
                
                # Sonucu Göster
                st.image(generated_image, caption=f"{selected_style} Stilinde Tasarım", use_column_width=True)
                
                # İndirme Butonu
                st.markdown(get_image_download_link(generated_image, "tattoo_stencil.png", "Stencili (PNG)"), unsafe_allow_html=True)
                st.info("Bu görseli dövme sanatçınıza göstererek stencilini çıkartabilirsiniz.")
                
            else:
                st.error(f"Bir hata oluştu: {error_message}")

# Alt Bilgi
st.markdown("---")
st.markdown("Powered by **Google Imagen 4.0 AI** | © 2024 JustArtTattoo")