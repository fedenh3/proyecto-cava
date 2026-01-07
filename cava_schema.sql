-- =============================================================================
-- ESQUEMA DE BASE DE DATOS: CAVA STATS
-- Este archivo define la estructura de tablas y sus relaciones (PK y FK).
-- =============================================================================

-- 1. TABLAS MAESTRAS (Dimensiones únicas para evitar duplicados)

-- Almacena los puestos de los jugadores (ARQ, DEF, VOL, DEL)
CREATE TABLE IF NOT EXISTS posiciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

-- Lista de todos los clubes rivales
CREATE TABLE IF NOT EXISTS rivales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Lista de torneos/temporadas (ej: Apertura 2024, 2018/2019)
CREATE TABLE IF NOT EXISTS torneos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL,
    temporada VARCHAR(20) NOT NULL,
    UNIQUE(nombre, temporada)
);

-- Lista de árbitros oficiales
CREATE TABLE IF NOT EXISTS arbitros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Lista de los cuerpos técnicos que pasaron por el club
CREATE TABLE IF NOT EXISTS tecnicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Usuarios con acceso al sistema (Admin)
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'admin',
    nombre VARCHAR(100)
);

-- TABLA DE JUGADORES: Información maestra del deportista y saldos históricos del Excel
CREATE TABLE IF NOT EXISTS jugadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_excel VARCHAR(20) UNIQUE, -- El código J001, J002 del Excel
    nombre VARCHAR(100),
    apellido VARCHAR(100) NOT NULL,
    id_posicion INTEGER,
    
    -- Saldos Iniciales: Estadísticas acumuladas en el Excel antes de este sistema
    pj_inicial INTEGER DEFAULT 0,
    goles_marcados_inicial INTEGER DEFAULT 0,
    goles_recibidos_inicial INTEGER DEFAULT 0,
    asistencias_inicial INTEGER DEFAULT 0,
    amarillas_inicial INTEGER DEFAULT 0,
    rojas_inicial INTEGER DEFAULT 0,
    titular_inicial INTEGER DEFAULT 0,
    suplente_inicial INTEGER DEFAULT 0,
    
    -- Hitos históricos del debut del jugador
    fecha_debut DATE,
    rival_debut VARCHAR(100),
    resultado_debut VARCHAR(20),
    
    -- Notas y comentarios del analista Guido Franck
    comentarios_gf TEXT,
    
    FOREIGN KEY (id_posicion) REFERENCES posiciones(id),
    UNIQUE(nombre, apellido) 
);

-- 2. TABLAS TRANSACCIONALES (Hechos de cada partido)

-- Registro de cada encuentro oficial disputado
CREATE TABLE IF NOT EXISTS partidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_calendario DATE,  -- Fecha real del evento
    nro_fecha VARCHAR(10),  -- Clasificación de jornada (F1, F2...)
    id_torneo INTEGER NOT NULL,
    id_rival INTEGER NOT NULL,
    id_arbitro INTEGER, 
    id_tecnico INTEGER, 
    condicion CHAR(1) CHECK(condicion IN ('L', 'V', 'N')), -- Local, Visitante, Neutral
    goles_favor INTEGER DEFAULT 0,
    goles_contra INTEGER DEFAULT 0,
    
    -- Detalle textual para el historial visual de la App
    goles_detalle TEXT,            -- Ejemplo: "Coselli (x2), Arrubarrena"
    rojas_cava INTEGER DEFAULT 0,  -- Cantidad de expulsados propios
    rojas_rival INTEGER DEFAULT 0, -- Cantidad de expulsados rivales
    expulsados_nombres TEXT,       -- Nombres de los sancionados
    
    -- Información sobre penales (fundamental para arqueros)
    penales_favor INTEGER DEFAULT 0,
    penales_favor_detalle TEXT,     -- Ejemplo: "Convertido", "Errado"
    penales_contra INTEGER DEFAULT 0,
    penales_contra_detalle TEXT,    -- Ejemplo: "Atajado", "Gol"
    
    FOREIGN KEY (id_torneo) REFERENCES torneos(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_rival) REFERENCES rivales(id) ON DELETE RESTRICT,
    FOREIGN KEY (id_arbitro) REFERENCES arbitros(id) ON DELETE SET NULL,
    FOREIGN KEY (id_tecnico) REFERENCES tecnicos(id) ON DELETE SET NULL
);

-- STATS: Rendimiento INDIVIDUAL de cada jugador en un partido específico
CREATE TABLE IF NOT EXISTS stats (
    id_partido INTEGER NOT NULL,
    id_jugador INTEGER NOT NULL,
    
    es_titular BOOLEAN DEFAULT 0,
    minutos_jugados INTEGER DEFAULT 0 CHECK(minutos_jugados >= 0), 
    goles_marcados INTEGER DEFAULT 0 CHECK(goles_marcados >= 0),
    goles_recibidos INTEGER DEFAULT 0 CHECK(goles_recibidos >= 0), -- Goles que le hicieron al arquero
    asistencias INTEGER DEFAULT 0 CHECK(asistencias >= 0),
    amarillas INTEGER DEFAULT 0 CHECK(amarillas >= 0),
    rojas INTEGER DEFAULT 0 CHECK(rojas >= 0),
    
    PRIMARY KEY (id_partido, id_jugador),
    
    FOREIGN KEY (id_partido) REFERENCES partidos(id) ON DELETE CASCADE,
    FOREIGN KEY (id_jugador) REFERENCES jugadores(id) ON DELETE CASCADE
);
