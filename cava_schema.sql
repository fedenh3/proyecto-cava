-- Esquema de Base de Datos para Proyecto CAVA (Estadísticas de Fútbol)
-- Respetando 3ra Forma Normal (3FN) y Buenas Prácticas de Integridad Referencial
-- Motor: SQLite

-- Habilitar foreign keys (aunque se hace en conexión, es bueno saberlo)
PRAGMA foreign_keys = ON;

-- 1. Tablas Maestras (Dimensiones)

CREATE TABLE IF NOT EXISTS torneos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL,
    temporada VARCHAR(20) NOT NULL,
    UNIQUE(nombre, temporada) -- Evita duplicar torneos
);

CREATE TABLE IF NOT EXISTS rivales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    -- Normalización de nombres: se recomienda guardar en mayúsculas desde App/ETL
    CONSTRAINT nombre_no_vacio CHECK(length(nombre) > 0)
);

CREATE TABLE IF NOT EXISTS arbitros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    CONSTRAINT nombre_arb_no_vacio CHECK(length(nombre) > 0)
);

CREATE TABLE IF NOT EXISTS tecnicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    CONSTRAINT nombre_dt_no_vacio CHECK(length(nombre) > 0)
);

CREATE TABLE IF NOT EXISTS jugadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100),
    apellido VARCHAR(100) NOT NULL,
    posicion VARCHAR(50), 
    goles_iniciales INTEGER DEFAULT 0,
    -- En un caso real usaríamos DNI, a falta de este, Title Case y Apellido son Unique.
    -- Ojo: Dos 'Juan Perez' romperían esto. En clubes de barrio es aceptable, en Pro no.
    UNIQUE(nombre, apellido) 
);

-- 2. Tablas Transaccionales (Hechos)

CREATE TABLE IF NOT EXISTS partidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE, 
    id_torneo INTEGER NOT NULL,
    id_rival INTEGER NOT NULL,
    id_arbitro INTEGER, -- Nullable porque puede no tener dato
    id_tecnico INTEGER, -- Nullable 
    condicion CHAR(1) CHECK(condicion IN ('L', 'V', 'N')), 
    goles_favor INTEGER DEFAULT 0 CHECK(goles_favor >= 0),
    goles_contra INTEGER DEFAULT 0 CHECK(goles_contra >= 0),
    
    FOREIGN KEY (id_torneo) REFERENCES torneos(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_rival) REFERENCES rivales(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_arbitro) REFERENCES arbitros(id) ON DELETE SET NULL,
    FOREIGN KEY (id_tecnico) REFERENCES tecnicos(id) ON DELETE SET NULL,
    
    -- Restricción de Negocio: CAVA no puede jugar dos veces contra el mismo rival en la misma fecha (y torneo)
    UNIQUE(fecha, id_rival, id_torneo)
);

CREATE TABLE IF NOT EXISTS presencias (
    -- Clave Primaria Compuesta: Un jugador solo está una vez por partido
    id_partido INTEGER NOT NULL,
    id_jugador INTEGER NOT NULL,
    
    es_titular BOOLEAN DEFAULT 0,
    minutos_jugados INTEGER DEFAULT 0 CHECK(minutos_jugados >= 0), 
    goles INTEGER DEFAULT 0 CHECK(goles >= 0),
    amarillas INTEGER DEFAULT 0 CHECK(amarillas >= 0),
    rojas INTEGER DEFAULT 0 CHECK(rojas >= 0),
    
    PRIMARY KEY (id_partido, id_jugador),
    
    FOREIGN KEY (id_partido) REFERENCES partidos(id) ON DELETE CASCADE, -- Si borro partido, borro presencias
    FOREIGN KEY (id_jugador) REFERENCES jugadores(id) ON DELETE CASCADE -- Si borro jugador, borro sus presencias
);
