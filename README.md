# ⚽ CAVA Stats - Sistema de Inteligencia Deportiva

![CAVA Logo](https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Escudo_del_Club_Atl%C3%A9tico_Victoriano_Arenas.svg/1200px-Escudo_del_Club_Atl%C3%A9tico_Victoriano_Arenas.svg.png)

Bienvenido a **CAVA Stats**, una plataforma integral de análisis estadístico para el **Club Atlético Victoriano Arenas**. Esta aplicación transforma datos históricos de planillas de Excel en un sistema de base de datos relacional dinámico, permitiendo un análisis profundo del rendimiento del primer equipo.

## 🚀 Características Principales

*   **📊 Dashboard de Análisis:** Métricas globales de campaña (PJ, PG, PE, PP, GF, GC), rachas y efectividad.
*   **👤 Fichas de Jugadores:** Historial detallado por jugador, incluyendo minutos jugados, goles, tarjetas y comentarios técnicos.
*   **👔 Efectividad de DTs:** Ranking dinámico de rendimiento por cuerpo técnico.
*   **🏟️ Historial por Rival:** Buscador histórico para conocer el historial completo contra cada club.
*   **🛠️ Panel de Administración:** Gestión completa de la temporada 2026 (carga de partidos, torneos, rivales y plantel).
*   **⚖️ Motor ETL Inteligente:** Procesador de datos que automatiza la carga desde Excel vinculando automáticamente toda la información.

## 🛠️ Tecnología

*   **Lenguaje:** Python 3.x
*   **Interfaz:** [Streamlit](https://streamlit.io/) (Framework moderno para Apps de Datos).
*   **Base de Datos:** Soporte híbrido para **PostgreSQL** (Producción/Cloud) y **SQLite3** (Local).
*   **Procesamiento:** Pandas & Regular Expressions para el motor ETL.
*   **Visualización:** Altair Charts para gráficos interactivos.

## 📂 Estructura del Proyecto

*   `app.py`: Interfaz de usuario y visualizaciones principales.
*   `admin_module.py`: Lógica del panel de administración y seguridad.
*   `etl_process.py`: Motor de migración de datos Excel -> SQL.
*   `cava_functions.py`: Lógica de negocios y consultas estadísticas.
*   `db_config.py` & `db_init.py`: Configuración e inicialización del entorno.

## ⚙️ Instalación y Uso Local

1.  **Clonar el repositorio.**
2.  **Instalar dependencias:** `pip install -r requirements.txt`.
3.  **Configurar base de datos:** El sistema utiliza SQLite por defecto de forma local.
4.  **Carga Inicial:** Por razones de privacidad, el archivo de Excel original no está incluido en el repositorio. Al ejecutar la app por primera vez, el sistema solicitará la carga del archivo `.xlsx` para inicializar la base de datos local.
5.  **Ejecutar App:** `streamlit run app.py`.

---
*Desarrollado para el análisis y seguimiento histórico del CAVA.*
