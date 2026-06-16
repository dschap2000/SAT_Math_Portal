import streamlit as st
import google.generativeai as genai
import fitz  # PyMuPDF for PDF handling
from PIL import Image
import io
import os

# --- Configuration & Setup ---
st.set_page_config(page_title="Math Practice Portal", page_icon="📝", layout="centered")

# Configure the Gemini API Key securely using Streamlit Secrets
# In Streamlit Cloud, you add this in the App Settings > Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key not found. Please add GEMINI_API_KEY to your Streamlit secrets.")
    st.stop()

# Load the fast vision model
model = genai.GenerativeModel('gemini-2.5-flash')

# --- Helper Functions ---
def process_upload(uploaded_file):
    """Converts the uploaded file into a list of PIL Images."""
    images = []
    if uploaded_file.name.lower().endswith('.pdf'):
        # Read PDF and convert pages to images
        pdf_bytes = uploaded_file.read()
        doc = fitz.open("pdf", pdf_bytes)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150) # 150 DPI is a good balance of quality and speed
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            images.append(img)
    else:
        # It's an image file
        img = Image.open(uploaded_file)
        images.append(img)
    return images

def analyze_worksheet(images):
    """Sends the images to Gemini to check for completion."""
    prompt = """
    You are a strict but fair automated grader. 
    Look at the provided image(s) of a math worksheet. 
    Analyze the blank space directly below every single numbered question. 
    Has the student written handwritten text, numbers, or math in EVERY single workspace? 
    Ignore the correctness of the math. We only care about attempt/effort.
    
    If ALL problems have visible handwriting below them, respond with EXACTLY and ONLY the word: TRUE
    If ANY problem is missing handwriting (left completely blank), respond with EXACTLY and ONLY the word: FALSE
    """
    
    # Pass the prompt and the list of images to the model
    try:
        response = model.generate_content([prompt] + images)
        return response.text.strip().upper() == "TRUE"
    except Exception as e:
        st.error(f"Error communicating with the Vision API: {e}")
        return False

# --- App UI ---
st.title("Jackson's SAT Math Portal 🚀")
st.write("Upload a photo or PDF of your completed worksheet. Once the system verifies you've attempted every problem, your answer key will unlock automatically.")

# File Uploader
uploaded_file = st.file_uploader("Upload Worksheet (PDF, JPG, PNG)", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display a small preview of the upload
    st.success("File uploaded successfully! Processing...")
    
    with st.spinner("Analyzing your hard work..."):
        # 1. Convert to images
        worksheet_images = process_upload(uploaded_file)
        
        # 2. Run Vision Analysis
        is_complete = analyze_worksheet(worksheet_images)
        
    # 3. The Gateway Logic
    if is_complete:
        st.success("✅ Excellent work! It looks like you've attempted every problem.")
        st.balloons()
        
        # Load the Answer Key PDF to be downloaded
        # Make sure 'SAT_Math_Answer_Key.pdf' is in the same directory as this script
        try:
            with open("SAT_Math_Answer_Key.pdf", "rb") as pdf_file:
                PDFbyte = pdf_file.read()
            
            st.download_button(
                label="📥 Download Answer Key",
                data=PDFbyte,
                file_name="SAT_Math_Answer_Key.pdf",
                mime="application/pdf",
                type="primary"
            )
        except FileNotFoundError:
            st.error("The answer key file is currently unavailable. Please contact your tutor.")
            
    else:
        st.warning("⚠️ Almost there! It looks like there are still some blank problems. Give them your best guess and re-upload when finished.")
