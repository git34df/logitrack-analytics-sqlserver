# LogiTrack Analytics — SQL Server

Análisis de operaciones logísticas para una empresa
peruana ficticia: modelo dimensional con dos tablas
de hechos en SQL Server, ETL con Python y 18 consultas
analíticas sobre envíos, OTD, costos e inventario.

---

## Stack

![SQL Server](https://img.shields.io/badge/SQL_Server-2022-CC2927?style=flat&logo=microsoftsqlserver&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-ETL-150458?style=flat&logo=pandas&logoColor=white)

---

## Objetivo

Construir un Data Warehouse logístico que permita medir
la eficiencia operativa de envíos, identificar cuellos
de botella por ruta y transportista, y monitorear el
estado del inventario por almacén y producto, usando
OTD como KPI principal.

---

## Arquitectura
Python (ETL) → SQL Server (modelo dimensional) → Consultas analíticas

## Modelo de datos

| Tabla | Tipo | Descripción |
|---|---|---|
| `FactEnvios` | Fact | Envíos con costo, peso, estado y fechas |
| `FactInventario` | Fact | Stock disponible, mínimo y máximo por almacén |
| `DimTiempo` | Dimensión | Tabla de fechas con año, mes y trimestre |
| `DimAlmacen` | Dimensión | Almacenes — rol-playing: origen y destino |
| `DimTransportista` | Dimensión | Conductores y transportistas |
| `DimCliente` | Dimensión | Empresas cliente |
| `DimProducto` | Dimensión | Productos y categorías |
| `DimEstadoEnvio` | Dimensión | Estados: puntual, retrasado, devuelto, perdido |

> `DimAlmacen` se usa como dimensión rol-playing:
> se une dos veces a `FactEnvios` como origen y destino.

---

## Contenido

| Carpeta | Archivo | Descripción |
|---|---|---|
| `src/` | `logitrack_etl.py` | ETL de carga hacia SQL Server |
| `sql/` | `analytical_queries.sql` | 18 consultas analíticas |
| `diagrams/` | `schema.png` | Diagrama del modelo dimensional |

---

## Consultas analíticas (18)

Organizadas en dos bloques según tabla de hechos:

### FactEnvios — Operaciones y OTD (12 consultas)
OTD global por año y trimestre, ranking de rutas
con mayor tasa de retraso, top 5 transportistas
con peor cumplimiento, promedio de días de retraso
por estado, evolución mensual del OTD con variación
MoM (2020–2024), envíos perdidos y devueltos por
región de destino, costo promedio por KG por año,
top 10 clientes por costo total, rutas más costosas
en promedio, costo total por categoría de producto,
costo mensual acumulado con YTD y comparativa
Costo vs OTD por transportista con clasificación:
Eficiente / Caro pero Puntual / Barato Perdió / Problemático.

### FactInventario — Stock y Almacenes (6 consultas)
Almacenes con stock por debajo del mínimo,
rotación de inventario con ranking por período,
ranking de almacenes por porcentaje de ocupación
promedio, meses con mayor recepción de mercadería,
evolución del stock de productos críticos con
variación YoY y clasificación Deterioro / Mejora.

→ Ver todas las consultas en `sql/analytical_queries.sql`

---

## Técnicas SQL utilizadas

| Técnica | Uso |
|---|---|
| CTEs encadenadas | OTD mensual, comparativa Costo vs OTD, YoY inventario |
| Window Functions | `RANK()`, `LAG()`, `SUM() OVER()` |
| Role-playing dimension | `DimAlmacen` unida como origen y destino |
| YTD con `PARTITION BY` | Costo corrido y acumulado por año |
| `NULLIF` | Prevención de división por cero en rotación |
| `CASE WHEN` | Clasificación de transportistas y tendencia de stock |
| `FORMAT` con locale | Formato numérico en español (`es-ES`) |

---

## Cómo ejecutar

```bash
# 1. Instalar dependencias
pip install pandas sqlalchemy pyodbc

# 2. Configurar servidor en config.py
cp config.example.py config.py

# 3. Ejecutar ETL
python src/logitrack_etl.py

# 4. Correr consultas analíticas
# Abrir sql/analytical_queries.sql en SSMS y ejecutar
```

> Requiere SQL Server con Windows Authentication
> y ODBC Driver 17 for SQL Server instalado.

---

## Autor

**Diego Torres Andrade**
Estudiante de Ingeniería de Sistemas — UPN Lima
Orientado a Data Analytics & Business Intelligence

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Conectar-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/tu-usuario)
[![Portfolio](https://img.shields.io/badge/Portfolio-Ver_más-1a1a2e?style=flat)](https://tu-portfolio.vercel.app)
