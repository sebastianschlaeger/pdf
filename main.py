import streamlit as st
import io
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import DecodedStreamObject, EncodedStreamObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image

def replace_text(content, search_text, replacement_text):
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if search_text in line:
            lines[i] = line.replace(search_text, replacement_text)
    return "\n".join(lines)

def replace_image_on_page(page, new_image):
    for img_index, img in enumerate(page.images):
        # Lesen Sie das neue Bild
        img_byte_arr = io.BytesIO()
        new_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # Ersetzen Sie das alte Bild durch das neue
        img.data = img_byte_arr
        img.filter = "/FlateDecode"

def edit_pdf(input_pdf, text_replacements, new_image):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        for obj in page.get("/Contents", ()):
            if isinstance(obj, DecodedStreamObject) or isinstance(obj, EncodedStreamObject):
                data = obj.get_data()
                for search_text, replacement_text in text_replacements:
                    data = replace_text(data.decode('utf-8'), search_text, replacement_text).encode('utf-8')
                obj.set_data(data)
        
        if new_image:
            replace_image_on_page(page, new_image)
        writer.add_page(page)

    output_pdf = io.BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf

st.title('PDF Editor App')

uploaded_file = st.file_uploader("Wählen Sie eine PDF-Datei aus", type="pdf")

if uploaded_file is not None:
    st.write("PDF erfolgreich hochgeladen!")

    # Text-Ersetzungen
    st.subheader("Text-Ersetzungen")
    num_replacements = st.number_input("Anzahl der Text-Ersetzungen", min_value=1, value=1)
    text_replacements = []
    for i in range(num_replacements):
        col1, col2 = st.columns(2)
        with col1:
            search_text = st.text_input(f"Zu ersetzender Text {i+1}")
        with col2:
            replacement_text = st.text_input(f"Neuer Text {i+1}")
        if search_text and replacement_text:
            text_replacements.append((search_text, replacement_text))

    # Bild-Ersetzung
    st.subheader("Bild-Ersetzung")
    new_image = st.file_uploader("Wählen Sie ein neues Bild aus (optional)", type=["png", "jpg", "jpeg"])
    
    if st.button("PDF bearbeiten"):
        if text_replacements or new_image:
            new_image_pil = Image.open(new_image) if new_image else None
            edited_pdf = edit_pdf(uploaded_file, text_replacements, new_image_pil)
            
            st.download_button(
                label="Bearbeitete PDF herunterladen",
                data=edited_pdf,
                file_name="edited_document.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Bitte geben Sie mindestens eine Text-Ersetzung ein oder wählen Sie ein neues Bild aus.")

st.info("Hinweis: Diese App funktioniert am besten mit einfachen PDFs. Komplexe Layouts oder verschlüsselte PDFs können Probleme verursachen.")
