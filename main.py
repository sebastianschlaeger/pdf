import streamlit as st
import io
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import DecodedStreamObject, EncodedStreamObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def replace_text(content, search_text, replacement_text):
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if search_text in line:
            lines[i] = line.replace(search_text, replacement_text)
    return "\n".join(lines)

def replace_image_on_page(page, new_image):
    logger.debug("Attempting to replace image on page")
    if '/Resources' in page and '/XObject' in page['/Resources']:
        xObject = page['/Resources']['/XObject']
        for obj in xObject:
            if xObject[obj]['/Subtype'] == '/Image':
                logger.debug(f"Found image object: {obj}")
                # Lesen Sie das neue Bild
                img_byte_arr = io.BytesIO()
                new_image.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()

                # Ersetzen Sie das alte Bild durch das neue
                if isinstance(xObject[obj], EncodedStreamObject):
                    logger.debug("Image object is EncodedStreamObject")
                    new_obj = DecodedStreamObject()
                    new_obj.set_data(img_byte_arr)
                    xObject[obj] = new_obj
                elif isinstance(xObject[obj], DecodedStreamObject):
                    logger.debug("Image object is DecodedStreamObject")
                    xObject[obj].set_data(img_byte_arr)
                else:
                    logger.warning(f"Unexpected object type: {type(xObject[obj])}")
                    continue

                xObject[obj].update({
                    '/Filter': '/FlateDecode',
                    '/Width': new_image.width,
                    '/Height': new_image.height,
                    '/ColorSpace': '/DeviceRGB',
                    '/BitsPerComponent': 8,
                    '/Length': len(img_byte_arr)
                })
                logger.debug("Image replacement successful")
                return
    logger.warning("No suitable image found for replacement")

def edit_pdf(input_pdf, text_replacements, new_image):
    try:
        logger.debug("Starting PDF editing process")
        reader = PdfReader(input_pdf)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            logger.debug(f"Processing page {i+1}")
            if '/Contents' in page:
                content = page['/Contents']
                if isinstance(content, list):
                    for obj in content:
                        if isinstance(obj, (DecodedStreamObject, EncodedStreamObject)):
                            data = obj.get_data()
                            for search_text, replacement_text in text_replacements:
                                data = replace_text(data.decode('utf-8'), search_text, replacement_text).encode('utf-8')
                            obj.set_data(data)
                elif isinstance(content, (DecodedStreamObject, EncodedStreamObject)):
                    data = content.get_data()
                    for search_text, replacement_text in text_replacements:
                        data = replace_text(data.decode('utf-8'), search_text, replacement_text).encode('utf-8')
                    content.set_data(data)
            
            if new_image:
                replace_image_on_page(page, new_image)
            writer.add_page(page)

        logger.debug("PDF editing complete, preparing output")
        output_pdf = io.BytesIO()
        writer.write(output_pdf)
        output_pdf.seek(0)
        return output_pdf
    except Exception as e:
        logger.exception(f"Error occurred while editing PDF: {str(e)}")
        st.error(f"Fehler beim Bearbeiten der PDF: {str(e)}")
        return None

# Der Rest des Streamlit-Codes bleibt unverändert
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
            
            if edited_pdf:
                st.download_button(
                    label="Bearbeitete PDF herunterladen",
                    data=edited_pdf,
                    file_name="edited_document.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Die PDF konnte nicht bearbeitet werden. Bitte überprüfen Sie die Datei und versuchen Sie es erneut.")
        else:
            st.warning("Bitte geben Sie mindestens eine Text-Ersetzung ein oder wählen Sie ein neues Bild aus.")

st.info("Hinweis: Diese App funktioniert am besten mit einfachen PDFs. Komplexe Layouts oder verschlüsselte PDFs können Probleme verursachen.")
