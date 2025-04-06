BaseJSON = '''
      {
      "idFactura":,
    "nombreEmpresa":,
    "fechaEmision":,
    "shipDate":,
    "shipTo": {
      "nombreCliente":,
      "direccion":,
      "ciudad":,
      "estado":,
      "pais":,
      "codigoPostal":
    },
    "total":
    }
'''

BaseCSV = """
idProducto;nombreProducto;cantidadPedida;cantidadEnviada;precioUnidad;precioAcumulativo
"""

PromptToGeneratePrompts = f"""
  You are an expert extracting Information i need you to create me a prompt that can help to obatin information and put it on a JSON and CSV file.
  You need to specify that the CSV is only fo the products and all the rest of information its for the JSON.
  But Understand that rightnow i just need a prompt that gives details to how to find the information to fill the Json and the CSV 

  **JsonFormat**
  {BaseJSON}

  **Csv Format**
  {BaseCSV}
  
  Return te prompt of the indications to how to find each information of he can put it on the JSON and CSV, dont add specific information of this JSON because REMEBER this its the tample , i will pass you a lot of these files so give details of how to find these information in the prompt.
  And at the end of the prompt add the empty json and CSV format so he can know what json and csv format he needs to return.

  The CSV its only for the products because its vey often that there are a lot of products so its for optimization, the rest put it on a JSON.

  Notes that you need to know
  -CP its Codigo Postal so try to not add it on others fields
  -The total on the JSON its all the sum of the precioAcumulativo on the producst, but it's always in the json so there is no need to calculate it.
  -Dont add special characters like line breaks, etc.
  -SPECIFY THAT in THE CSV of the producst, the idProducto are UNIQUE so if you see that multiple product have the same id set them as Null, please this is very important and check really carefull this this.
  -Also Specify that the nombreProducto needs to be complete, try to fetch the full name of the produc often found in Description, its common that you doesn't put the full name so check this carefully.
  -Specify that at the time to return don't add unesesary information just return the JSON and CSV and betwen the JSON and the CSV add ------CSV------ so i can know when the CSV STARTS.
  -Its important to really specify dont that he doesn't need to add any extra information i just only want the JSON and CSV
"""

TERMINOS_EMPRESA_EN = [
    r"Inc.",
    r"CORP.",
    r"Ltd.",
    r"Co.",
    r"Company",
    r"PLC",
    r"LLC",
    r"LLP",
    r"LP",
    r"ULC",
    r"ULtd",
    r"ULtd.",
    r"Assoc.",
    r"Associates",
    r"Foundation",
    r"Enterprises",
    r"Group",
    r"Holdings",
    r"Investments",
    r"Ventures",
    r"Technologies",
    r"International",
    r"Global",
    r"Systems",
    r"Solutions",
    r"Services",
    r"Consulting",
    r"Management",
    r"Capital",
    r"Finance",
    r"Industries",
    r"Resources",
    r"Partners",
    r"Bros.",
    r"Brothers",
    r"Tool",
    r"Products",
    r"Securities",
    r"Center",
    r"LAMINATING",
]