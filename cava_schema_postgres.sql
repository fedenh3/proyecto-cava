-- =============================================================================
-- ESQUEMA DE BASE DE DATOS: CAVA STATS (VERSION POSTGRESQL)
-- =============================================================================

-- 1. TABLAS MAESTRAS

CREATE TABLE IF NOT EXISTS posiciones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS rivales (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS torneos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    temporada VARCHAR(20) NOT NULL,
    UNIQUE(nombre, temporada)
);

CREATE TABLE IF NOT EXISTS arbitros (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tecnicos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'admin',
    nombre VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS jugadores (
    id SERIAL PRIMARY KEY,
    id_excel VARCHAR(20) UNIQUE,
    nombre VARCHAR(100),
    apellido VARCHAR(100) NOT NULL,
    id_posicion INTEGER,
    
    pj_inicial INTEGER DEFAULT 0,
    goles_marcados_inicial INTEGER DEFAULT 0,
    goles_recibidos_inicial INTEGER DEFAULT 0,
    asistencias_inicial INTEGER DEFAULT 0,
    amarillas_inicial INTEGER DEFAULT 0,
    rojas_inicial INTEGER DEFAULT 0,
    titular_inicial INTEGER DEFAULT 0,
    suplente_inicial INTEGER DEFAULT 0,
    
    fecha_debut DATE,
    rival_debut VARCHAR(100),
    resultado_debut VARCHAR(20),
    
    comentarios_gf TEXT,
    
    FOREIGN KEY (id_posicion) REFERENCES posiciones(id),
    UNIQUE(nombre, apellido) 
);

-- 2. TABLAS TRANSACCIONALES

CREATE TABLE IF NOT EXISTS partidos (
    id SERIAL PRIMARY KEY,
    fecha_calendario DATE,
    nro_fecha VARCHAR(10),
    id_torneo INTEGER NOT NULL,
    id_rival INTEGER NOT NULL,
    id_arbitro INTEGER, 
    id_tecnico INTEGER, 
    condicion CHAR(1) CHECK(condicion IN ('L', 'V', 'N')), 
    goles_favor INTEGER DEFAULT 0,
    goles_contra INTEGER DEFAULT 0,
    
    goles_detalle TEXT,
    rojas_cava INTEGER DEFAULT 0,
    rojas_rival INTEGER DEFAULT 0,
    expulsados_nombres TEXT,
    
    penales_favor INTEGER DEFAULT 0,
    penales_favor_detalle TEXT,
    penales_contra INTEGER DEFAULT 0,
    penales_contra_detalle TEXT,
    
    FOREIGN KEY (id_torneo) REFERENCES torneos(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_rival) REFERENCES rivales(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_arbitro) REFERENCES arbitros(id) ON DELETE SET NULL,
    FOREIGN KEY (id_tecnico) REFERENCES tecnicos(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS stats (
    id_partido INTEGER NOT NULL,
    id_jugador INTEGER NOT NULL,
    
    es_titular BOOLEAN DEFAULT FALSE,
    minutos_jugados INTEGER DEFAULT 0 CHECK(minutos_jugados >= 0), 
    goles_marcados INTEGER DEFAULT 0 CHECK(goles_marcados >= 0),
    goles_recibidos INTEGER DEFAULT 0 CHECK(goles_recibidos >= 0),
    asistencias INTEGER DEFAULT 0 CHECK(asistencias >= 0),
    amarillas INTEGER DEFAULT 0 CHECK(amarillas >= 0),
    rojas INTEGER DEFAULT 0 CHECK(rojas >= 0),
    
    PRIMARY KEY (id_partido, id_jugador),
    
    FOREIGN KEY (id_partido) REFERENCES partidos(id) ON DELETE CASCADE,
    FOREIGN KEY (id_jugador) REFERENCES jugadores(id) ON DELETE CASCADE
);
