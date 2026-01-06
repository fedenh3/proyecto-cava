-- Esquema de Base de Datos para Proyecto CAVA (Estadísticas de Fútbol)
-- Auditado para Máxima Atomicidad y 3FN
-- Motor: SQLite

PRAGMA foreign_keys = ON;

-- 1. Tablas Maestras (Dimensiones)

CREATE TABLE IF NOT EXISTS torneos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL,
    temporada VARCHAR(20) NOT NULL,
    UNIQUE(nombre, temporada)
);

CREATE TABLE IF NOT EXISTS rivales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
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

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'admin',
    nombre VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jugadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100),
    apellido VARCHAR(100) NOT NULL,
    posicion VARCHAR(50), 
    goles_iniciales INTEGER DEFAULT 0,
    UNIQUE(nombre, apellido) 
);

-- 2. Tablas Transaccionales (Hechos)

CREATE TABLE IF NOT EXISTS partidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE, 
    id_torneo INTEGER NOT NULL,
    id_rival INTEGER NOT NULL,
    id_arbitro INTEGER, 
    id_tecnico INTEGER, 
    condicion CHAR(1) CHECK(condicion IN ('L', 'V', 'N')), 
    goles_favor INTEGER DEFAULT 0 CHECK(goles_favor >= 0),
    goles_contra INTEGER DEFAULT 0 CHECK(goles_contra >= 0),
    
    FOREIGN KEY (id_torneo) REFERENCES torneos(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_rival) REFERENCES rivales(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_arbitro) REFERENCES arbitros(id) ON DELETE SET NULL,
    FOREIGN KEY (id_tecnico) REFERENCES tecnicos(id) ON DELETE SET NULL,
    
    UNIQUE(fecha, id_rival, id_torneo)
);

-- Tabla renombrada a 'stats' con mayor detalle atómico
CREATE TABLE IF NOT EXISTS stats (
    id_partido INTEGER NOT NULL,
    id_jugador INTEGER NOT NULL,
    
    es_titular BOOLEAN DEFAULT 0,
    minutos_jugados INTEGER DEFAULT 0 CHECK(minutos_jugados >= 0), 
    goles_marcados INTEGER DEFAULT 0 CHECK(goles_marcados >= 0),
    goles_recibidos INTEGER DEFAULT 0 CHECK(goles_recibidos >= 0), -- Específico para Arqueros
    asistencias INTEGER DEFAULT 0 CHECK(asistencias >= 0),
    amarillas INTEGER DEFAULT 0 CHECK(amarillas >= 0),
    rojas INTEGER DEFAULT 0 CHECK(rojas >= 0),
    
    PRIMARY KEY (id_partido, id_jugador),
    
    FOREIGN KEY (id_partido) REFERENCES partidos(id) ON DELETE CASCADE,
    FOREIGN KEY (id_jugador) REFERENCES jugadores(id) ON DELETE CASCADE
);
