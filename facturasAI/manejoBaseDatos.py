import json
import sqlite3
from difflib import SequenceMatcher
from facturasAI.information import statusEscaneoFactura


def similarity_percentage(str1, str2) -> float:
    # Create a SequenceMatcher object
    matcher = SequenceMatcher(None, str1, str2)

    # Calculate the similarity ratio
    similarity_ratio = matcher.ratio()

    # Convert the ratio to a percentage
    similarity_percentage = similarity_ratio

    return similarity_percentage


def addInfoDicc(dictionaryInfo: dict, idEmpresa: int, cursor, conn) -> int:
    if not dictionaryInfo or not idEmpresa:
        return None
    infoDicc = [dictionaryInfo["nombreCliente"], dictionaryInfo["direccion"], dictionaryInfo["ciudad"],
                dictionaryInfo["estado"], dictionaryInfo["pais"], dictionaryInfo["codigoPostal"]]
    # Needs to be the size of the infoDicc
    minimumPorcentage = [.90, .85, .97, .97, .97, .97]
    cursor.execute("""
    SELECT nombreCliente,direccion ,ciudad ,estado ,pais ,codigoPostal,id FROM informacionDirecciones
    WHERE EmpresaFacturaID = ?
  """, (idEmpresa,))

    instances = cursor.fetchall()

    for instance in instances:
        for i in range(len(instance) - 1):
            str1, str2 = str(infoDicc[i]).lower(), str(instance[i]).lower()
            # We are checking that the similarity of the string are over minimumPorcentage[i]
            if minimumPorcentage[i] > similarity_percentage(str1, str2):
                continue

            if i == len(instance) - 2:
                return instance[-1]  # We return the id of this instance

    cursor.execute("""
    INSERT INTO informacionDirecciones(
        EmpresaFacturaID, nombreCliente, direccion, ciudad, estado, pais, codigoPostal
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    RETURNING *;
""", (idEmpresa, infoDicc[0], infoDicc[1], infoDicc[2], infoDicc[3], infoDicc[4], infoDicc[5]))
    idInfo = cursor.fetchone()[0]
    conn.commit()
    return idInfo


def returnTypeData(string: str, isIdProduct: bool = False):
    string = str(string)
    if string.lower() in ["none", "null"]:
        return None
    if isIdProduct:
        return string
    if string.isdigit():
        return int(string)

    if '.' not in string:
        return string
    count = 0
    for c in string:
        if count > 1:
            break
        if not c.isdigit() and c not in [',', '.']:
            return string

        elif c == ',':
            count += 1

    return float(string.replace(',', ""))


def retrieveProductId(idProducto, nombreProducto, precioUnidad, idEmpresa: int, cursor, conn) -> int:
    # print(f"{idProducto} | {nombreProducto} | {idEmpresa}")
    if idProducto == None:
        cursor.execute("""
        SELECT id,precioUnitario FROM Productos
        WHERE 
          idEmpresaFactura = ? AND idProducto IS NULL AND nombreProducto LIKE ?      
      """, (idEmpresa, f"%{nombreProducto}%"))
    else:
        cursor.execute("""
        SELECT id,precioUnitario FROM Productos
        WHERE 
          idEmpresaFactura = ? AND idProducto = ?    
      """, (idEmpresa, idProducto))

    idInstanceProduct = cursor.fetchone()
    if idInstanceProduct:
        oldPrice = idInstanceProduct[1]
        if oldPrice != precioUnidad:
            cursor.execute("""
        UPDATE Productos SET precioUnitario = ? WHERE id = ?
      """, (precioUnidad, idInstanceProduct[0]))
        idInstanceProduct = idInstanceProduct[0]

    else:
        cursor.execute("""
      INSERT INTO Productos(idEmpresaFactura,idProducto,nombreProducto,precioUnitario) VALUES(?,?,?,?) RETURNING *
  """, (idEmpresa, idProducto, nombreProducto, precioUnidad))
        idInstanceProduct = cursor.fetchone()[0]
    conn.commit()
    return idInstanceProduct


def addProduct(listProducts: list, idFactura, idEmpresa, cursor, conn):
    productosError = []
    totalFactura = 0
    for i in range(1, len(listProducts)):
        idPr, nombreProducto, cantidadPedida, cantidadEnviada, precioUnidad, precioAcumulativo = returnTypeData(listProducts[i][0], True), returnTypeData(
            listProducts[i][1]), returnTypeData(listProducts[i][2]), returnTypeData(listProducts[i][3]), returnTypeData(listProducts[i][4]), returnTypeData(listProducts[i][5])
        idProducto = retrieveProductId(
            idPr, nombreProducto, precioUnidad, idEmpresa, cursor, conn)
        calculoPrecioAcumulativo = round(cantidadEnviada * precioUnidad, 2)
        # Si la cantidad enviada esta mal calculada agregar producto a productosError
        if calculoPrecioAcumulativo != precioAcumulativo:
            toAdd = idPr if idPr else nombreProducto
            productosError.append(toAdd)

        # Sumar al total
        totalFactura += precioAcumulativo

        cursor.execute("""
      INSERT INTO ProductoFacturas(idFactura,idProducto,cantidadPedida,cantidadEnviada,precioAcumulativo)
      VALUES(?,?,?,?,?)
  """, (idFactura, idProducto, cantidadPedida, cantidadEnviada, precioAcumulativo))
    conn.commit()
    return totalFactura, productosError


def createJsonFactura(idFactura, idEmpresa: int, fecchaEmision, shipDate, idShipTo: int, subTotal: float, total: float, cursor, conn) -> int:
    cursor.execute("""
  INSERT INTO jsonFacturas(id,idEmpresa,idShipTo,fechaEmision,shipDate,subTotal,total)
  VALUES (?,?,?,?,?,?,?)
""", (idFactura, idEmpresa, idShipTo, fecchaEmision, shipDate, subTotal, total)
    )
    conn.commit()
    cursor.execute("""
  SELECT id FROM jsonFacturas WHERE ID = ?
""", (idFactura,)
    )
    return cursor.fetchone()[0]


def addInvoiceToDataBase(nombreEmpresa: str, jsonDictionay: dict, productCVS: list[list], conn, cursor):
    cursor.execute("""
  SELECT id FROM Empresas WHERE
  nombreEmpresa = ?
""", (nombreEmpresa,)
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
""", (idInvoice,)
    )
    factura = cursor.fetchone()
    status = statusEscaneoFactura.copy()
    if factura:
        print(f"La factura {idInvoice} ya esta registrada en la base de datos")
        cursor.execute("""
    DELETE FROM jsonFacturas WHERE id = ?
    """, (idInvoice,)
        )
        conn.commit()
        return status
    # Agrege ahora el apartado total a la base de datos
    idShipTo = addInfoDicc(jsonDictionay["shipTo"], idEmpresa, cursor, conn)
    idJsonFactura = createJsonFactura(
        idInvoice, idEmpresa, jsonDictionay["fechaEmision"], jsonDictionay["shipDate"], idShipTo, jsonDictionay['subTotal'], jsonDictionay['total'], cursor, conn)
    cantidadAcumulativaTotal, Productos_ID_Error = addProduct(
        productCVS, idJsonFactura, idEmpresa, cursor, conn)
    cantidadAcumulativaTotal = round(cantidadAcumulativaTotal, 2)
    status = statusEscaneoFactura.copy()
    if Productos_ID_Error:
        status["Errores"]["precioAcumulativo"], status["Status"] = Productos_ID_Error, False

    subTotal = returnTypeData(jsonDictionay['subTotal']) if jsonDictionay['subTotal'] else returnTypeData(
        jsonDictionay['total'])  # Tomar cantidad total en llegado caso que la factura no haya registrado SubTotal
    if cantidadAcumulativaTotal != subTotal:
        status["Errores"]["total"], status["Status"] = False, False
        status["Errores"]["mensajeError"] += f"La suma de los totales dio ${cantidadAcumulativaTotal} cuando en la factura dio un total de ${subTotal}"

    return status
