import json
import sqlite3
from difflib import SequenceMatcher

def similarity_percentage(str1, str2)->float:
    # Create a SequenceMatcher object
    matcher = SequenceMatcher(None, str1, str2)
    
    # Calculate the similarity ratio
    similarity_ratio = matcher.ratio()
    
    # Convert the ratio to a percentage
    similarity_percentage = similarity_ratio
    
    return similarity_percentage

def addInfoDicc(dictionaryInfo:dict , idEmpresa:int,cursor,conn)->int:
  if not dictionaryInfo or not idEmpresa:
    return None
  infoDicc = [dictionaryInfo["nombreCliente"] , dictionaryInfo["direccion"] , dictionaryInfo["ciudad"] , dictionaryInfo["estado"],dictionaryInfo["pais"],dictionaryInfo["codigoPostal"]]
  minimumPorcentage = [.90 , .85 , .97 , .97 , .97 , .97] #Needs to be the size of the infoDicc
  cursor.execute("""
    SELECT nombreCliente,direccion ,ciudad ,estado ,pais ,codigoPostal,id FROM informacionDirecciones
    WHERE EmpresaFacturaID = ?
  """, (idEmpresa,))

  instances = cursor.fetchall()

  for instance in instances:
    for i in range(len(instance) - 1):
      str1 , str2 = str(infoDicc[i]).lower() , str(instance[i]).lower()
      if minimumPorcentage[i] > similarity_percentage(str1, str2): #We are checking that the similarity of the string are over minimumPorcentage[i]
        continue

      if i == len(instance) - 2:
        return instance[-1] #We return the id of this instance
  
  cursor.execute("""
    INSERT INTO informacionDirecciones(
        EmpresaFacturaID, nombreCliente, direccion, ciudad, estado, pais, codigoPostal
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    RETURNING *;
""", (idEmpresa, infoDicc[0], infoDicc[1], infoDicc[2], infoDicc[3], infoDicc[4], infoDicc[5]))
  idInfo = cursor.fetchone()[0]
  conn.commit()
  return idInfo

def returnTypeData(string:str , isIdProduct:bool = False):
  string = str(string)
  if string.lower() in ["none","null"]:
    return None
  if isIdProduct:
    return string
  if string.isdigit():
    return int(string)
  
  if '.' not in string:
    return string
  for c in string:
    if not c.isdigit() and c != '.':
      return string
  return float(string)
  
def retrieveProductId(idProducto,nombreProducto ,precioUnidad, idEmpresa:int,cursor,conn)->int:
  #print(f"{idProducto} | {nombreProducto} | {idEmpresa}")
  if idProducto == None:
    cursor.execute("""
        SELECT id,precioUnitario FROM Productos
        WHERE 
          idEmpresaFactura = ? AND idProducto IS NULL AND nombreProducto LIKE ?      
      """, (idEmpresa,f"%{nombreProducto}%"))
  else:
    cursor.execute("""
        SELECT id,precioUnitario FROM Productos
        WHERE 
          idEmpresaFactura = ? AND idProducto = ?    
      """, (idEmpresa,idProducto))

  idInstanceProduct = cursor.fetchone()
  if idInstanceProduct:
    oldPrice = idInstanceProduct[1]
    if oldPrice != precioUnidad:
      cursor.execute("""
        UPDATE Productos SET precioUnitario = ? WHERE id = ?
      """,(precioUnidad ,idInstanceProduct[0]))
    idInstanceProduct= idInstanceProduct[0]
    
  else:
    cursor.execute("""
      INSERT INTO Productos(idEmpresaFactura,idProducto,nombreProducto,precioUnitario) VALUES(?,?,?,?) RETURNING *
  """,(idEmpresa,idProducto,nombreProducto,precioUnidad))
    idInstanceProduct = cursor.fetchone()[0]
  conn.commit()
  return idInstanceProduct

def addProduct(listProducts:list ,idFactura,idEmpresa,cursor,conn)->int:
  for i in range(1,len(listProducts)):
    idPr, nombreProducto , cantidadPedida , cantidadEnviada, precioUnidad , precioAcumulativo =returnTypeData(listProducts[i][0],True) ,returnTypeData(listProducts[i][1]),returnTypeData(listProducts[i][2]),returnTypeData(listProducts[i][3]),returnTypeData(listProducts[i][4]),returnTypeData(listProducts[i][5])
    idProducto = retrieveProductId(idPr,nombreProducto,precioUnidad,idEmpresa,cursor,conn)
    cursor.execute("""
      INSERT INTO ProductoFacturas(idFactura,idProducto,cantidadPedida,cantidadEnviada,precioAcumulativo)
      VALUES(?,?,?,?,?)
  """,(idFactura ,idProducto ,cantidadPedida ,cantidadEnviada,precioAcumulativo))
  conn.commit()

def createJsonFactura(idFactura,idEmpresa:int,fecchaEmision,shipDate,idShipTo:int,cursor,conn)->int:
  cursor.execute("""
  INSERT INTO jsonFacturas(id,idEmpresa,idShipTo,fechaEmision,shipDate)
  VALUES (?,?,?,?,?)
""",(idFactura,idEmpresa,idShipTo,fecchaEmision,shipDate)
  )
  conn.commit()
  cursor.execute("""
  SELECT id FROM jsonFacturas WHERE ID = ?
""",(idFactura,)
  )
  return cursor.fetchone()[0]

def addInvoiceToDataBase(nombreEmpresa:str,jsonDictionay:dict,productCVS:list[list],conn , cursor):
  cursor.execute("""
  SELECT id FROM Empresas WHERE
  nombreEmpresa = ?
""",(nombreEmpresa,)
  )

  idEmpresa = cursor.fetchone()
  if not idEmpresa:
    print(f"Empresa {nombreEmpresa} no encontada")
    return
  idEmpresa = idEmpresa[0]
  idInvoice = jsonDictionay["idFactura"]
  cursor.execute("""
  SELECT * FROM jsonFacturas WHERE
  id = ?
""",(idInvoice,)
  )
  factura = cursor.fetchone()
  if factura:
    print(f"La factura {idInvoice} ya esta registrada en la base de datos")
    cursor.execute("""
    DELETE FROM jsonFacturas WHERE id = ?
    """,(idInvoice,)
    )
    conn.commit()
    return
  idShipTo = addInfoDicc(jsonDictionay["shipTo"] , idEmpresa,cursor , conn)
  idJsonFactura = createJsonFactura(idInvoice,idEmpresa,jsonDictionay["fechaEmision"],jsonDictionay["shipDate"],idShipTo,cursor , conn)
  addProduct(productCVS,idJsonFactura,idEmpresa,cursor , conn)
  print(f"Factura {idInvoice} se registro en la base de datos")