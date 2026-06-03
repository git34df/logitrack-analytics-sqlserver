import pyodbc
import random
from datetime import date, timedelta
from faker import Faker

fake = Faker("es_MX")
random.seed(42)

# ============================================================
# CONFIGURACIÓN DE CONEXIÓN — ajusta según tu entorno
# ============================================================
SERVER   = ""          # o tu instancia, ej: ".\SQLEXPRESS"
DATABASE = ""

# Autenticación Windows (recomendado si usas SQL Server local)
conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
    f"TrustServerCertificate=yes;"
)


# ============================================================
# DATOS MAESTROS — catálogos ficticios pero realistas
# ============================================================

REGIONES_PERU = {
    "Lima"       : ["Lima", "Miraflores", "San Isidro", "Callao"],
    "Arequipa"   : ["Arequipa", "Cayma", "Yanahuara"],
    "La Libertad": ["Trujillo", "Víctor Larco", "El Porvenir"],
    "Piura"      : ["Piura", "Sullana", "Talara"],
    "Cusco"      : ["Cusco", "San Jerónimo", "Wanchaq"],
}

SECTORES = ["Retail", "Manufactura", "Farmacéutico", "Construcción",
            "Alimentos", "Tecnología", "Textil", "Automotriz"]

SEGMENTOS = ["Pequeño", "Mediano", "Grande"]

TIPOS_ALMACEN = ["Central", "Regional", "Tránsito"]

TIPOS_CARGA = ["Estándar", "Frágil", "Pesado", "Refrigerado"]

CATEGORIAS_PRODUCTO = {
    "Electrónica"   : ("Estándar", 12.5),
    "Alimentos"     : ("Refrigerado", 8.0),
    "Maquinaria"    : ("Pesado", 95.0),
    "Farmacéutico"  : ("Frágil", 3.5),
    "Textil"        : ("Estándar", 5.0),
    "Construcción"  : ("Pesado", 120.0),
    "Cosméticos"    : ("Frágil", 2.0),
    "Autopartes"    : ("Estándar", 18.0),
}

TIPOS_VEHICULO = ["Camión", "Furgoneta", "Trailer", "Moto"]

CAPACIDADES_KG = {
    "Camión"   : 5000,
    "Furgoneta": 1500,
    "Trailer"  : 20000,
    "Moto"     : 80,
}

ESTADOS_ENVIO = [
    ("Entregado a tiempo", 1),
    ("Entregado con retraso", 0),
    ("Devuelto", 0),
    ("Perdido", 0),
]

# ============================================================
# HELPERS
# ============================================================

def fecha_a_id(d: date) -> int:
    """Convierte date a entero YYYYMMDD."""
    return int(d.strftime("%Y%m%d"))

def fechas_rango(inicio: date, fin: date):
    """Genera todas las fechas entre inicio y fin inclusive."""
    actual = inicio
    while actual <= fin:
        yield actual
        actual += timedelta(days=1)

def ciudad_region_aleatoria():
    region = random.choice(list(REGIONES_PERU.keys()))
    ciudad = random.choice(REGIONES_PERU[region])
    return ciudad, region

# ============================================================
# FUNCIONES DE INSERCIÓN POR TABLA
# ============================================================

def insertar_dim_tiempo(cursor, inicio: date, fin: date):
    print("  → Insertando DimTiempo...")
    nombres_mes = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                   "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    nombres_dia = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    sql = """
        INSERT INTO dbo.DimTiempo
            (FechaID, Fecha, Dia, Mes, NombreMes, Trimestre,
             Anio, DiaSemana, NombreDia, EsFinDeSemana)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """
    batch = []
    for d in fechas_rango(inicio, fin):
        dia_semana = d.weekday() + 1   # 1=Lunes, 7=Domingo
        batch.append((
            fecha_a_id(d),
            d,
            d.day,
            d.month,
            nombres_mes[d.month - 1],
            (d.month - 1) // 3 + 1,
            d.year,
            dia_semana,
            nombres_dia[d.weekday()],
            1 if dia_semana >= 6 else 0,
        ))
    cursor.executemany(sql, batch)
    print(f"     {len(batch)} fechas insertadas.")
    return [fecha_a_id(d) for d in fechas_rango(inicio, fin)]


def insertar_dim_cliente(cursor, n=30):
    print("  → Insertando DimCliente...")
    sql = """
        INSERT INTO dbo.DimCliente
            (NombreEmpresa, Sector, Segmento, Ciudad, Region, Activo)
        VALUES (?,?,?,?,?,?)
    """
    batch = []
    for _ in range(n):
        ciudad, region = ciudad_region_aleatoria()
        batch.append((
            fake.company(),
            random.choice(SECTORES),
            random.choice(SEGMENTOS),
            ciudad,
            region,
            1,
        ))
    cursor.executemany(sql, batch)
    cursor.execute("SELECT ClienteID FROM dbo.DimCliente")
    ids = [r[0] for r in cursor.fetchall()]
    print(f"     {len(ids)} clientes insertados.")
    return ids


def insertar_dim_almacen(cursor, n=10):
    print("  → Insertando DimAlmacen...")
    sql = """
        INSERT INTO dbo.DimAlmacen
            (NombreAlmacen, TipoAlmacen, Ciudad, Region, CapacidadM3, Activo)
        VALUES (?,?,?,?,?,?)
    """
    batch = []
    for _ in range(n):
        ciudad, region = ciudad_region_aleatoria()
        tipo = random.choice(TIPOS_ALMACEN)
        batch.append((
            f"Almacén {ciudad} {tipo}",
            tipo,
            ciudad,
            region,
            round(random.uniform(500, 5000), 2),
            1,
        ))
    cursor.executemany(sql, batch)
    cursor.execute("SELECT AlmacenID FROM dbo.DimAlmacen")
    ids = [r[0] for r in cursor.fetchall()]
    print(f"     {len(ids)} almacenes insertados.")
    return ids


def insertar_dim_producto(cursor):
    print("  → Insertando DimProducto...")
    sql = """
        INSERT INTO dbo.DimProducto
            (NombreProducto, Categoria, TipoCarga, PesoProm_Kg, Activo)
        VALUES (?,?,?,?,?)
    """
    batch = []
    for categoria, (tipo_carga, peso_base) in CATEGORIAS_PRODUCTO.items():
        for i in range(1, 4):   # 3 productos por categoría = 24 productos
            batch.append((
                f"{categoria} Producto {i:02d}",
                categoria,
                tipo_carga,
                round(peso_base * random.uniform(0.8, 1.2), 2),
                1,
            ))
    cursor.executemany(sql, batch)
    cursor.execute("SELECT ProductoID FROM dbo.DimProducto")
    ids = [r[0] for r in cursor.fetchall()]
    print(f"     {len(ids)} productos insertados.")
    return ids


def insertar_dim_transportista(cursor, n=20):
    print("  → Insertando DimTransportista...")
    sql = """
        INSERT INTO dbo.DimTransportista
            (NombreConductor, TipoVehiculo, Placa, CapacidadKg, Activo)
        VALUES (?,?,?,?,?)
    """
    batch = []
    placas_usadas = set()
    for _ in range(n):
        tipo = random.choice(TIPOS_VEHICULO)
        while True:
            placa = (f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
                     f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
                     f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
                     f"-{random.randint(100,999)}")
            if placa not in placas_usadas:
                placas_usadas.add(placa)
                break
        batch.append((
            fake.name(),
            tipo,
            placa,
            round(CAPACIDADES_KG[tipo] * random.uniform(0.85, 1.0), 2),
            1,
        ))
    cursor.executemany(sql, batch)
    cursor.execute("SELECT TransportistaID FROM dbo.DimTransportista")
    ids = [r[0] for r in cursor.fetchall()]
    print(f"     {len(ids)} transportistas insertados.")
    return ids


def insertar_dim_estado_envio(cursor):
    print("  → Insertando DimEstadoEnvio...")
    sql = """
        INSERT INTO dbo.DimEstadoEnvio (DescripcionEstado, EsPuntual)
        VALUES (?,?)
    """
    cursor.executemany(sql, ESTADOS_ENVIO)
    cursor.execute("SELECT EstadoID, EsPuntual FROM dbo.DimEstadoEnvio")
    rows = cursor.fetchall()
    print(f"     {len(rows)} estados insertados.")
    # Retorna dict {EstadoID: EsPuntual}
    return {r[0]: r[1] for r in rows}


def insertar_fact_envios(cursor, fecha_ids, cliente_ids, almacen_ids,
                         transportista_ids, producto_ids, estado_dict, n=5000):
    print("  → Insertando FactEnvios...")

    # Pesos de probabilidad para estados (realista: mayoría a tiempo)
    estado_ids   = list(estado_dict.keys())
    estado_pesos = [0.65, 0.25, 0.07, 0.03]   # a tiempo, retraso, devuelto, perdido

    sql = """
        INSERT INTO dbo.FactEnvios
            (FechaID, ClienteID, AlmacenOrigenID, AlmacenDestinoID,
             TransportistaID, ProductoID, EstadoID,
             PesoKg, CostoEnvio, TiempoEstimadoDias, TiempoRealDias)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """
    batch = []
    for _ in range(n):
        estado_id  = random.choices(estado_ids, weights=estado_pesos, k=1)[0]
        es_puntual = estado_dict[estado_id]

        tiempo_est = random.randint(1, 10)
        if es_puntual:
            tiempo_real = tiempo_est
        else:
            tiempo_real = tiempo_est + random.randint(1, 7)

        origen, destino = random.sample(almacen_ids, 2)
        peso   = round(random.uniform(1.0, 500.0), 2)
        costo  = round(peso * random.uniform(0.8, 3.5) + random.uniform(5, 50), 2)

        batch.append((
            random.choice(fecha_ids),
            random.choice(cliente_ids),
            origen,
            destino,
            random.choice(transportista_ids),
            random.choice(producto_ids),
            estado_id,
            peso,
            costo,
            tiempo_est,
            tiempo_real,
        ))

    
    lote = 500
    for i in range(0, len(batch), lote):
        cursor.executemany(sql, batch[i:i+lote])

    print(f"     {n} envíos insertados.")


def insertar_fact_inventario(cursor, fecha_ids, almacen_ids, producto_ids):
    """
    Snapshot mensual: primer día de cada mes por cada combinación
    almacén-producto. Genera ~10 almacenes × 24 productos × 60 meses = ~14,400 filas.
    """
    print("  → Insertando FactInventario...")

    # Filtrar solo primer día de cada mes
    fechas_mensuales = [fid for fid in fecha_ids if str(fid)[6:] == "01"]

    sql = """
        INSERT INTO dbo.FactInventario
            (FechaID, AlmacenID, ProductoID,
             StockDisponible, StockMinimo, StockMaximo,
             UnidadesRecibidas, UnidadesDespachadas)
        VALUES (?,?,?,?,?,?,?,?)
    """
    batch = []
    for fid in fechas_mensuales:
        for alm in almacen_ids:
            for prod in producto_ids:
                stock_min  = random.randint(10, 50)
                stock_max  = stock_min * random.randint(4, 10)
                stock_disp = random.randint(0, stock_max)
                recibidas  = random.randint(0, 200)
                despachadas= random.randint(0, recibidas + 50)
                batch.append((
                    fid, alm, prod,
                    stock_disp, stock_min, stock_max,
                    recibidas, despachadas,
                ))

    lote = 500
    for i in range(0, len(batch), lote):
        cursor.executemany(sql, batch[i:i+lote])

    print(f"     {len(batch)} snapshots de inventario insertados.")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 55)
    print("  LogiTrack Analytics — Ingesta de Datos")
    print("=" * 55)

    print("\n[1/2] Conectando a SQL Server...")
    conn   = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print("      Conexión establecida.")

    print("\n[2/2] Insertando datos...\n")

    INICIO = date(2020, 1, 1)
    FIN    = date(2024, 12, 31)

    try:
        fecha_ids          = insertar_dim_tiempo(cursor, INICIO, FIN)
        cliente_ids        = insertar_dim_cliente(cursor, n=30)
        almacen_ids        = insertar_dim_almacen(cursor, n=10)
        producto_ids       = insertar_dim_producto(cursor)
        transportista_ids  = insertar_dim_transportista(cursor, n=20)
        estado_dict        = insertar_dim_estado_envio(cursor)

        insertar_fact_envios(
            cursor, fecha_ids, cliente_ids, almacen_ids,
            transportista_ids, producto_ids, estado_dict, n=5000
        )
        insertar_fact_inventario(
            cursor, fecha_ids, almacen_ids, producto_ids
        )

        conn.commit()
        print("\n✓ Todos los datos insertados y confirmados (COMMIT).")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error durante la ingesta — se hizo ROLLBACK.")
        print(f"  Detalle: {e}")
        raise

    finally:
        cursor.close()
        conn.close()
        print("  Conexión cerrada.")

    print("\n" + "=" * 55)
    print("  Ingesta completada exitosamente.")
    print("=" * 55)


if __name__ == "__main__":
    main()
