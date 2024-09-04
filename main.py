import streamlit as st
import io
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import DecodedStreamObject, EncodedStreamObject, NameObject, ArrayObject
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def replace_text(content, search_text, replacement_text):
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if search_text in line:
            lines[i] = line.replace(search_text, replacement_text)
    return "\n".join(lines)

def edit_pdf(input_pdf, text_replacements):
    try:
        logger.debug("Starting PDF editing process")
        reader = PdfReader(input_pdf)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            logger.debug(f"Processing page {i+1}")
            if '/Contents' in page:
                content = page['/Contents']
                if isinstance(content, ArrayObject):
                    for j, obj in enumerate(content):
                        if isinstance(obj, (DecodedStreamObject, EncodedStreamObject)):
                            data = obj.get_data()
                            for search_text, replacement_text in text_replacements:
                                data = replace_text(data.decode('utf-8'), search_text, replacement_text).encode('utf-8')
                            obj.set_data(data)
                            content[j] = obj
                elif isinstance(content, (DecodedStreamObject, EncodedStreamObject)):
                    data = content.get_data()
                    for search_text, replacement_text in text_replacements:
                        data = replace_text(data.decode('utf-8'), search_text, replacement_text).encode('utf-8')
                    content.set_data(data)
                page[NameObject('/Contents')] = content

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

st.title('PDF Text Editor App')

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
    
    if st.button("PDF bearbeiten"):
        if text_replacements:
            edited_pdf = edit_pdf(uploaded_file, text_replacements)
            
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
            st.warning("Bitte geben Sie mindestens eine Text-Ersetzung ein.")

st.info("Hinweis: Diese App funktioniert am besten mit einfachen PDFs. Komplexe Layouts oder verschlüsselte PDFs können Probleme verursachen.")
