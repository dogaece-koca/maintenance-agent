import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
from pypdf import PdfReader

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    api_key = None

if not api_key:
    st.error("API Key not found! Please add it from Streamlit settings.")
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key
genai.configure(api_key=api_key)
MODEL_NAME = "gemini-2.5-flash"

# ---SAYFA AYARLARI ---
st.set_page_config(
    page_title="Field Maintenance Assistant",
    page_icon="🔧",
    layout="wide"
)

# ---BAŞLIK VE AÇIKLAMA ---
st.title("🔧 Maintenance Agent")
st.markdown("""This system analyzes uploaded **technical documents (PDF)** and provides instant support to technicians in the field using the **Gemini 2.5** model. 
You can also upload images to diagnose malfunctions.
""")

# --- YAN PANEL (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Settings")
    st.header("📄 Documentation")
    uploaded_file = st.file_uploader("Upload Maintenance Manual (PDF)", type="pdf")

    if uploaded_file is not None:
        if "last_uploaded_file" not in st.session_state or st.session_state["last_uploaded_file"] != uploaded_file.name:
            try:
                reader = PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"

                st.session_state["manual_content"] = text
                st.session_state["last_uploaded_file"] = uploaded_file.name

                st.success(f"✅ PDF Processed Successfully! ({len(reader.pages)} pages)")

                st.rerun()

            except Exception as e:
                st.error(f"Error reading PDF: {e}")

try:
    system_instruction = f"""
    Role: You are an expert industrial maintenance assistant.

    REFERENCE SOURCE (Use this primarily):
    {st.session_state.get('manual_content', 'No manual loaded yet. Use general knowledge.')}

    CRITICAL RULES:
    1. **LANGUAGE DETECTION:** If the user asks in Turkish, MUST reply in TURKISH. If the user asks in English, MUST reply in ENGLISH.
    2. Stick to the reference manual provided above.
    3. Keep answers short, clear, and suitable for field technicians.
    4. Always state SAFETY WARNINGS first (High Voltage, Pressure, etc.).
    """

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=system_instruction
    )
except Exception as e:
    st.error(f"Model initialization failed. Check API Key: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message:
            st.image(message["image"], caption="Uploaded Image", width=300)

# ---KULLANICI GİRDİ ALANI ---
with st.expander("📷 Add Image (Optional)"):

    uploaded_image = st.file_uploader("Upload a photo of the faulty part", type=["jpg", "jpeg", "png"])

# Metin Girişi
if prompt := st.chat_input("Ask a question about maintenance..."):
    user_message = {"role": "user", "content": prompt}

    img_data = None
    if uploaded_image:
        img_data = Image.open(uploaded_image)
        user_message["image"] = img_data

    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(prompt)
        if img_data:
            st.image(img_data, width=300)

    # --- AI CEVABI OLUŞTURMA ---
    with st.chat_message("assistant"):
        with st.spinner("Analyzing manual and generating response..."):
            try:
                full_prompt = f"QUESTION: {prompt}"

                if img_data:
                    response = model.generate_content([full_prompt, img_data])
                else:
                    response = model.generate_content(full_prompt)

                st.markdown(response.text)

                st.session_state.messages.append({"role": "assistant", "content": response.text})

            except Exception as e:
                st.error(f"An error occurred: {e}")