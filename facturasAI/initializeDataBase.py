import sqlite3

def initialize_database(db_name:str):
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.execute('''
                CREATE TABLE IF NOT EXISTS Empresas
                (id INTEGER PRIMARY KEY AUTOINCREMENT, nombreEmpresa TEXT UNIQUE, prompt TEXT)
                ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jsonFacturas
        (
            id INTEGER PRIMAY KEY UNIQUE,
            idEmpresa INTEGER,
            idShipTo INTEGER,
            fechaEmision TEXT,
            shipDate TEXT,
            subTotal FLOAT,
            total FLOAT,
            FOREIGN KEY (idShipTo) REFERENCES informacionDirecciones(id),
            FOREIGN KEY (idEmpresa) REFERENCES Empresas(id)
        )
        '''
                   )
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS informacionDirecciones
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            EmpresaFacturaID id,
            nombreCliente TEXT,
            direccion TEXT,
            ciudad TEXT,
            estado TEXT,
            pais TEXT,
            codigoPostal INTEGER,
            FOREIGN KEY (EmpresaFacturaID) REFERENCES Empresas(id)
        )
        ''')
    
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS Productos
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                idEmpresaFactura INTEGER,
                idProducto TEXT UNIQUE,
                nombreProducto TEXT,
                precioUnitario float,
                FOREIGN KEY (idEmpresaFactura) REFERENCES Empresas(id)
                )
                ''')
    
    cursor.execute('''
                CREATE TABLE IF NOT EXISTS ProductoFacturas
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                idFactura INTEGER,
                idProducto INTEGER,
                cantidadPedida INTEGER, cantidadEnviada INTEGER , precioAcumulativo INTEGER,
                FOREIGN KEY (idFactura) REFERENCES jsonFacturas(id) ON DELETE CASCADE,
                FOREIGN KEY (idProducto) REFERENCES Productos(id)
                )
                ''')
    
    conn.commit()

    return conn , cursor