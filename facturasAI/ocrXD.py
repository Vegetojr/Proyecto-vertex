import tkinter as tk
from tkinter import filedialog
import pytesseract
from PIL import Image
import os
from pdf2image import convert_from_path
import re
from facturasAI.information import TERMINOS_EMPRESA_EN

# Lista de términos comunes en nombres de empresas
# Le pregunte a vertex


def subir_archivo():
    root = tk.Tk()
    root.withdraw()

    archivo_path = filedialog.askopenfilename(
        title="Seleccionar archivo PDF",
        filetypes=(("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*"))
    )
    if not archivo_path:
        print("No se seleccionó ningún archivo.")
        return None
    else:
        print(f"Archivo seleccionado: ")
        return archivo_path


def ocr_pdf(pdf_path):
    try:
        # Aqui se hace una lista de las hojas de las imagenes
        images = convert_from_path(pdf_path)
        if not images:
            print("El PDF no contiene páginas.")
            return None

        image = images[0]  # Aqui hago que solo tome la primera

        '''
        Habia otra forma de hacerlo poniendo 
        el atributo max_page=1 pero mi libreria 
        aunque estuviera actualizada no me dejaba 
        asi que obte por hacerlo asi'''

        # Aqui obtengo el ancho de la imagen para que se quede en su forma original
        width = image.size[0]

        # Defino cuantto es lo que voy a recortar
        left = 0
        top = 0

        '''
        Aunque los 2 de arriba esten vacios es 
        necesarios definirlos para que la imagen 
        se corte como debe
        '''

        right = width
        bottom = 700  # Lo defini como 700 porque es donde la informacion relevante para identificar la emrpesa esta

        cropped_image = image.crop(
            (left, top, right, bottom))  # Se recorta la imagen
        image_path = "temp_cropped.png"
        cropped_image.save(image_path, "PNG")

        texto = pytesseract.image_to_string(Image.open(
            image_path), lang='eng')  # extraifo el texto

        os.remove(image_path)

        return texto

    except Exception as e:
        print('hola error')
        print(f"Error durante el OCR del PDF: {e}")
        return None


# Esto me ayudo vertex :D pero aca machin
def identificar_empresa_por_patron(texto_extraido):
    """Identifica un nombre de empresa genérico en el texto extraído usando patrones."""
    for termino in TERMINOS_EMPRESA_EN:
        patron = r"([A-Za-z0-9\s&'-]+ " + termino + \
            r"[\.,]?)"  # Patrón general
        match = re.search(patron, texto_extraido, re.IGNORECASE | re.MULTILINE)
        print('Si')
        if match:
            # AGARRAMOS EL NOMBRE DE LA EMPRESA
            empresa = match.group(1).strip()
            return empresa

    return None


def obtenerNombreEmpresaDePDF(pdfPATH: str) -> str:

    texto_extraido = ocr_pdf(pdfPATH)
    nombre_empresa = identificar_empresa_por_patron(texto_extraido)
    return nombre_empresa
