--OTD Global por año y trimestre
SELECT dt.anio                                                         AS año,
       dt.trimestre,
       Count(*)
       [Total Envios],
       Format(Cast(Sum(CASE
                         WHEN dee.espuntual = 1 THEN 1
                         ELSE 0
                       END) AS FLOAT) / Count(*) * 100, 'N2', 'es-ES') AS
       [% DE OTD]
FROM   factenvios AS fe
       INNER JOIN dimtiempo AS dt
               ON fe.fechaid = dt.fechaid
       INNER JOIN dimestadoenvio AS dee
               ON fe.estadoid = dee.estadoid
GROUP  BY dt.anio,
          dt.trimestre
ORDER  BY año,
          dt.trimestre;

-- Ranking de rutas con mayor tasa de retraso ( origen -> destino ) 

WITH rutas
     AS (SELECT Concat(ao.region, '->', ad.region)
                AS Ruta,
                Count(*)
                AS
                   [Total Envios],
                Sum(CASE
                      WHEN dee.espuntual = 0 THEN 1
                      ELSE 0
                    END)
                AS
                   [Envios Retraso],
                round(Cast(Sum(CASE
                                  WHEN dee.espuntual = 0 THEN 1
                                  ELSE 0
                                END) AS FLOAT) / Count(*) * 100,2)
                AS
                [% Tasa de retraso]
         FROM   factenvios AS fe
                INNER JOIN dimalmacen AS ao
                        ON fe.almacenorigenid = ao.almacenid
                INNER JOIN dimalmacen AS ad
                        ON fe.almacendestinoid = ad.almacenid
                INNER JOIN dimestadoenvio AS dee
                        ON fe.estadoid = dee.estadoid
         GROUP  BY ao.region,
                   ad.region)
SELECT ruta,
       [total envios],
       [envios retraso],
       [% tasa de retraso],
       Rank()
         OVER(
           ORDER BY [% tasa de retraso] DESC) AS rank_rutas
FROM   rutas
ORDER  BY rank_rutas ASC 

--TOP 5 transportistas con peor OTD 
Select TOP 5 dt.NombreConductor as Transportista,  round(Cast(Sum(CASE WHEN dee.espuntual = 1 THEN 1 ELSE 0 END) AS FLOAT) / Count(*) * 100,2) AS  [% ODT]
from FactEnvios as fe
inner join DimTransportista as dt on fe.TransportistaID = dt.TransportistaID
inner join DimEstadoEnvio as dee on fe.EstadoID=dee.EstadoID
group by dt.NombreConductor
order by [% ODT] DESC;

-- Promedio de dias de retraso por estado de envio 
select dee.DescripcionEstado as [Estado de Envio], avg(fe.diasretraso) as [Promedio de dias de retraso] from FactEnvios as fe
inner join DimEstadoEnvio as dee on fe.EstadoID=dee.EstadoID
group by dee.DescripcionEstado
order by [Promedio de dias de retraso] desc

--Evolucion Mensual OTD (TENDENCIA 2020-2024) 
WITH otd as (
select
dt.anio as año,
dt.mes as mes,
round(Cast(Sum(CASE WHEN dee.espuntual = 1 THEN 1 ELSE 0 END) AS FLOAT) / Count(*) * 100,2) AS OTD 
from FactEnvios as fe 
inner join DimTiempo as dt on fe.fechaID=dt.fechaID
inner join DimEstadoEnvio as dee on fe.EstadoID=dee.EstadoID
group by dt.Anio,dt.Mes
),
tendencia_otd as (
select
año,
mes,
OTD,
LAG(OTD) OVER (ORDER BY año, mes) AS otd_mes_anterior,
ROUND(
    (OTD - LAG(OTD) OVER (PARTITION BY año ORDER BY mes))
    / LAG(OTD) OVER (PARTITION BY año ORDER BY mes)
    * 100
, 2) AS variacion_pct 
from 
otd
)
select 
año,
mes,
OTD,
otd_mes_anterior,
variacion_pct
from tendencia_otd
order by año,mes

--Envios Perdidos y devueltos por region de destino 
select da.region as RegionDestino, Cast(Sum(CASE WHEN dee.EstadoID = 3 THEN 1 ELSE 0 END) AS FLOAT)  as Devueltos,
Cast(Sum(CASE WHEN dee.EstadoID = 4 THEN 1 ELSE 0 END) AS FLOAT)  as Perdidos 
from FactEnvios as fe 
inner join DimAlmacen as da on fe.AlmacenDestinoID=da.AlmacenID
inner join DimEstadoEnvio as dee on fe.EstadoID=dee.EstadoID
group by da.Region

--Costo Promedio por KG Enviado por año 
select dt.anio as año, Round((Sum(fe.CostoEnvio) / sum(fe.PesoKg)),2) as [Costo Promedio] from FactEnvios as fe 
inner join DimTiempo as dt on fe.FechaID=dt.FechaID
group by dt.Anio
order by [Costo Promedio] desc;

--TOP 10 clientes por costo total de envio 
select top 10 dc.NombreEmpresa as Cliente, sum(fe.CostoEnvio) as [Costo Envio] from FactEnvios as fe
inner join DimCliente as dc on fe.ClienteID=dc.ClienteID
group by dc.NombreEmpresa
order by [Costo Envio] desc;

--Comparativa Costo vs OTD por transportista 
with costo as (
select
TransportistaID,
sum(CostoEnvio) as [Costo Total],
Count(*) as TotalEnvios
from FactEnvios 
group by TransportistaID
),
otd as (
select
fe.TransportistaID,
round(cast(sum(case when dee.EsPuntual = 1 then 1 else 0 end ) as float) / Count(*) * 100,2) as OTD
from FactEnvios as fe 
inner join DimEstadoEnvio as dee on fe.EstadoID = dee.EstadoID
group by fe.TransportistaID
)
SELECT
dt.NombreConductor as Transportista,
c.[Costo Total],
c.TotalEnvios,
Format(round(c.[Costo Total] / c.TotalEnvios,2),'N0','es-ES') as [Costo Promedio],
o.OTD,
Case
    when Round(c.[Costo Total] / c.TotalEnvios,2)< 570 and o.OTD >=65 then 'Eficiente'
    when Round(c.[Costo Total] / c.TotalEnvios,2)>= 570 and o.OTD >=65 then 'Caro pero Puntual'
    when Round(c.[Costo Total] / c.TotalEnvios,2)< 570 and o.OTD <65 then 'Barato Perdio'
    else 'Problematico' 
    END as Clasificacion
FROM 
DimTransportista as dt 
inner join costo as c on dt.TransportistaID=c.TransportistaID
inner join otd as o on dt.TransportistaID=o.TransportistaID

--Costo Total por Categoria de Producto
select dp.Categoria, SUM(fe.CostoEnvio) as [Costo Total] from FactEnvios as fe 
inner join DimProducto as dp on fe.ProductoID = dp.ProductoID
group by dp.Categoria
order by [Costo Total] desc

--Rutas mas Costosa en Promedio 
select Concat(ao.Region,' ',' -> ',ad.Region) as Ruta, ROUND(SUM(fe.CostoEnvio) / COUNT(*), 2) AS [Costo Promedio x Envio] 
from FactEnvios as fe 
inner join DimAlmacen as ao on fe.AlmacenOrigenID=ao.AlmacenID
inner join DimAlmacen as ad on fe.AlmacenDestinoID=ad.AlmacenID
group by ao.Region,ad.Region
order by [Costo Promedio x Envio] desc

--Costo Mensual acumulado y Corrido (YTD)
with Costo_Mensual as (
select dt.anio as año, dt.NombreMes as Mes,dt.Mes as nmes, sum(fe.CostoEnvio)  as [Costo Mensual]
from FactEnvios as fe 
inner join DimTiempo as dt on fe.FechaID=dt.FechaID
group by dt.Anio,dt.Mes,dt.NombreMes
)
select
año,
Mes,
SUM([Costo Mensual]) over (Order by año,nmes) as Total_Corrido,
SUM([Costo Mensual]) over(Partition by año order by nmes) as YTD
FROM Costo_Mensual 
order by año,nmes

--almacenes con stock por debajo del minimo
select 
dt.anio as año,
dt.NombreMes as mes,
dp.Categoria,
dp.NombreProducto as Producto,
da.NombreAlmacen as Almacen,
da.Region,
fi.StockMinimo,
fi.StockDisponible,
(fi.StockMinimo-fi.StockDisponible) as [Unidades Faltantes]
from FactInventario as fi
inner join DimTiempo as dt on dt.FechaID=fi.FechaID
inner join DimProducto as dp on dp.ProductoID=fi.ProductoID
inner join DimAlmacen as da on da.AlmacenID=fi.AlmacenID
where fi.BajoStockMinimo = 1
order by año,dt.Mes

--Rotacion de Inventario
WITH rotacion as(
select 
dt.anio as año, 
dt.NombreMes as Mes,
dt.Mes as nmes,
dp.NombreProducto as Producto, 
Round(Sum(fi.UnidadesDespachadas) / nullif(avg(StockDisponible),0),2) as [Rotacion Inventario]
from FactInventario as fi 
inner join DimTiempo as dt  on fi.FechaID=dt.FechaID
inner join DimProducto as dp on fi.ProductoID=dp.ProductoID
group by dt.Anio,dp.NombreProducto,dt.NombreMes,dt.Mes
)
select
año,
Mes
Producto,
[Rotacion Inventario],
Rank() OVER(Partition by año,nmes ORDER BY [Rotacion Inventario] desc) as [Rank Rotacion] 
from rotacion
order by año,nmes

--Ranking de almacenes por promedio de Ocupacion
With Ocupacion as(
select
da.NombreAlmacen as Almacen,
da.Region,
Round(avg(cast(fi.stockDisponible as float) / nullif(fi.StockMaximo,0))*100,2) as [% Ocupacion Promedio]
from FactInventario as fi 
inner join DimAlmacen as da on fi.AlmacenID=da.AlmacenID
group by da.NombreAlmacen,da.Region
)
select
Almacen,
Region,
[% Ocupacion Promedio],
Rank() OVER(ORDER BY [% Ocupacion Promedio] desc) as Rank_Ocupacion
from Ocupacion
order by Rank_Ocupacion

--Meses con Mayor recepcion de mercaderia por almacen
select dt.NombreMes as Mes, SUM(fi.UnidadesRecibidas) as Recepcion from FactInventario as fi
inner join DimTiempo as dt on fi.FechaID=dt.FechaID
group by dt.NombreMes
order by Recepcion desc

--Evolucion del Stock de un producto critico a lo largo del tiempo
WITH stock_mensual AS (
    SELECT
        dt.Anio                          AS año,
        dt.Mes                           AS nmes,
        dt.NombreMes                     AS mes,
        dp.NombreProducto                AS Producto,
        dp.Categoria,
        AVG(fi.StockDisponible)          AS StockPromedio,
        MIN(fi.StockMinimo)              AS StockMinimo
    FROM FactInventario AS fi
    INNER JOIN DimTiempo   AS dt ON fi.FechaID    = dt.FechaID
    INNER JOIN DimProducto AS dp ON fi.ProductoID = dp.ProductoID
    WHERE fi.BajoStockMinimo = 1
    GROUP BY dt.Anio, dt.Mes, dt.NombreMes, dp.NombreProducto, dp.Categoria
),
con_yoy AS (
    SELECT
        año,
        mes,
        nmes,
        Producto,
        Categoria,
        StockPromedio,
        StockMinimo,
        LAG(StockPromedio, 12) OVER (
            PARTITION BY Producto 
            ORDER BY año, nmes
        ) AS Stock_Año_Anterior,
        ROUND(
            (StockPromedio - LAG(StockPromedio, 12) OVER (
                PARTITION BY Producto ORDER BY año, nmes)
            ) / NULLIF(LAG(StockPromedio, 12) OVER (
                PARTITION BY Producto ORDER BY año, nmes), 0) * 100
        ,0) AS Variacion_YoY_Pct
    FROM stock_mensual
)
SELECT
    año,
    mes,
    Producto,
    Categoria,
    StockPromedio,
    StockMinimo,
    Stock_Año_Anterior,
    Variacion_YoY_Pct,
    CASE
        WHEN Variacion_YoY_Pct < 0  THEN 'Deterioro'
        WHEN Variacion_YoY_Pct >= 0 THEN 'Mejora'
        ELSE 'Sin dato anterior'
    END AS Tendencia
FROM con_yoy
ORDER BY Producto, año, nmes
