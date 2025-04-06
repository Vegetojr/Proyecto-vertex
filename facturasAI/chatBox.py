import vertexai
from tkinter import filedialog
from vertexai.generative_models import GenerativeModel, ChatSession, Part
from google.oauth2 import service_account
import google.auth  # Importa el módulo google.auth
import sqlite3
import json
from facturasAI import information
from facturasAI import initializeDataBase
from facturasAI import manejoBaseDatos
from facturasAI.ocrXD import obtenerNombreEmpresaDePDF

# Configure Vertex AI
# Reemplaza con la ruta correcta
credentials, project = google.auth.default()
PROJECT_ID = 'chatboxchuyi'
LOCATION = 'us-central1'
MODEL_NAME = "gemini-2.0-flash-001"
DATABASE_NAME = "DB.db"


def retrievePDF(pdf_path: str) -> Part:
    with open(pdf_path, "rb") as f:
        pdf_file = Part.from_data(f.read(), mime_type="application/pdf")
    return pdf_file


def generateJsonFIle(model, pdfFile, prompt: str):
    prompt += ("\n" + information.BaseJSON)
    JSON = model.generate_content([prompt, pdfFile])
    return JSON


def cleanResponse(responseString):
    responseString = responseString.replace("`", "")
    responseString = responseString.split("\n")
    i = 0
    while i < len(responseString) and "csv" not in responseString[i].lower():
        i += 1
    if i == len(responseString)-1:
        print("No se encontrro el CSV en el Response")
    jsonString = responseString[:i]
    cvsString = responseString[i+1:]

    while "{" not in jsonString[0]:
        jsonString.pop(0)

    while "}" not in jsonString[-1]:
        jsonString.pop()

    jsonString = "\n".join(jsonString)
    try:
        jsonDict = json.loads(jsonString)

    except ValueError:
        print("Error a la hora de convertir el Json")
        return None, None

    products = []
    for line in cvsString:
        if line in ["\n", ""] or "csv" in line.lower():
            continue
        products.append(line.split(";"))

    return jsonDict, products


def process_file(file_path, model):

    try:
        conn, cursor = initializeDataBase.initialize_database(DATABASE_NAME)
        nameCompany = obtenerNombreEmpresaDePDF(file_path)
        if not nameCompany:
            print(f"No se encontro el nombre de la empresa en: {file_path}")
            conn.close()
            return 'ERROR'

        pdfFile = retrievePDF(file_path)
        cursor.execute(
            "SELECT prompt FROM Empresas Where nombreEmpresa = ?", (nameCompany,))
        promptToUse = cursor.fetchone()
        if not promptToUse:
            print(
                f"Generando prompt para las facturas de la empresa {nameCompany}")
            promptToUse = information.PromptToGeneratePrompts
            response = model.generate_content([promptToUse, pdfFile])
            try:
                promptToUse = response.text
                cursor.execute('''
                    INSERT INTO Empresas(nombreEmpresa, prompt)
                    VALUES (?, ?)
                ''', (nameCompany, promptToUse))
                conn.commit()
                print(
                    f"Prompt for the Company {nameCompany} Succesfully created")
            except sqlite3.IntegrityError as e:
                print("Error al crear el prompt")
                conn.close()
                return 'ERROR'
        else:
            promptToUse = promptToUse[0]

        response = generateJsonFIle(model, pdfFile, promptToUse).text
        print(response)
        jsonDict, poductCVS = cleanResponse(response)
        if None in [jsonDict, poductCVS]:
            print("hubo un error con JSON o CVS")
            conn.close()
            return 'ERROR'

        manejoBaseDatos.addInvoiceToDataBase(
            nameCompany, jsonDict, poductCVS, conn, cursor)
        conn.close()
        print(f"Archivo {file_path} procesado con éxito.")
        return 'PROCESADO'

    except Exception as e:
        print(f"Error al procesar {file_path}: {e}")
        if 'conn' in locals():
            conn.close()
        return 'ERROR'


def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION,
                  credentials=credentials)
    model = GenerativeModel(MODEL_NAME)
    chat = model.start_chat()

    results = {}

    filePaths = filedialog.askopenfilenames(
        title="Select a PDF file",
        filetypes=(("Text files", ".pdf"), ("All files", ".*")))

    if not filePaths:
        return 0

    for filePath in filePaths:
        results[filePath] = process_file(filePath, model)

    print("Resultados del procesamiento:", results)
    return results
