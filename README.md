# ⚽ CAVA Stats - Sistema de Inteligencia Deportiva

![CAVA Logo](https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Escudo_del_Club_Atl%C3%A9tico_Victoriano_Arenas.svg/1200px-Escudo_del_Club_Atl%C3%A9tico_Victoriano_Arenas.svg.png)

Bienvenido a **CAVA Stats**, una plataforma integral de análisis estadístico para el **Club Atlético Victoriano Arenas**. Esta aplicación transforma datos históricos de planillas de Excel en un sistema de base de datos relacional dinámico, permitiendo un análisis profundo del rendimiento del primer equipo.

## 🚀 Características Principales

*   **📊 Dashboard de Análisis:** Métricas globales de campaña (PJ, PG, PE, PP, GF, GC).
*   **👤 Fichas de Jugadores:** Historial detallado por jugador, incluyendo minutos jugados, goles, tarjetas y comentarios de análisis técnico.
*   **👔 Efectividad de DTs:** Ranking dinámico de rendimiento por cuerpo técnico basado en puntos obtenidos.
*   **🏟️ Historial por Rival:** Buscador histórico para conocer el historial completo contra cada club enfrentado.
*   **⚖️ Motor ETL Inteligente:** Procesador de datos que automatiza la carga desde Excel, vinculando automáticamente goleadores y detalles de partidos.

## 🛠️ Tecnología

*   **Lenguaje:** Python 3.x
*   **Interfaz:** [Streamlit](https://streamlit.io/) (Framework moderno para Apps de Datos)
*   **Base de Datos:** SQLite3 (Motor relacional ligero y veloz)
*   **Procesamiento:** Pandas & Regular Expressions (NLP básico para lectura de texto)
*   **Visualización:** Altair Charts

## 📂 Estructura del Proyecto

*   `app.py`: Interfaz de usuario y visualizaciones.
*   `etl_process.py`: Motor de migración de datos Excel -> SQL.
*   `cava_functions.py`: Lógica de negocios y consultas estadísticas.
*   `cava_schema.sql`: Diseño de la arquitectura de la base de datos.
*   `db_config.py` & `db_init.py`: Configuración e inicialización del entorno.

## ⚙️ Instalación y Uso

1. Clonar el repositorio.
2. Instalar dependencias: `pip install -r requirements.txt`.
3. Inicializar base de datos: `python db_init.py`.
4. Cargar datos desde el Excel: `python etl_process.py`.
5. Ejecutar App: `streamlit run app.py`.

---
*Desarrollado para el análisis y seguimiento histórico del CAVA.*
