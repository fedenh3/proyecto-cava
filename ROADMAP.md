# 🗺️ Roadmap de CAVA Stats

Este documento detalla las funcionalidades pendientes y las ideas para futuras versiones del Sistema de Inteligencia Deportiva de Victoriano Arenas.

---

## 🛠️ Próxima Implementación: "Módulo Comentarista"
*Objetivo: Brindar datos rápidos y visuales para el análisis durante las transmisiones.*

### 1. Panel de Árbitros (Visual)
- **Qué falta:** Agregar la pestaña "Árbitros" en la App.
- **Utilidad:** Saber si con un árbitro específico el equipo tiene tendencia a ganar, empatar o recibir muchas tarjetas.
- **Estado:** La función `get_referee_stats()` ya existe en el backend.

### 2. Métricas de Arqueros (Visual)
- **Qué falta:** Mostrar "Vallas Invictas" y "Penales Atajados/Recibidos" en la ficha del jugador.
- **Utilidad:** Valorar el rendimiento defensivo y la efectividad individual del 1.

### 3. Analítica de Goles (Visual)
- **Qué falta:** Insertar el gráfico de torta en la sección de Análisis.
- **Utilidad:** Identificar fortalezas (ej: "Marcamos mucho de pelota parada") o debilidades.

---

## 💡 Ideas para el Futuro

### 📋 Gestión Técnica e Inteligencia
- **Análisis de Cambios:** Estadísticas de cómo cambia el equipo con los suplentes (goles convertidos x jugadores que entraron desde el banco).
- **Racha de Jugadores:** Identificar quiénes son los jugadores con mejores métricas en los últimos 5 partidos (quién llega "encendido").
- **Historial vs Rivales Detallado:** Quién es nuestro máximo goleador contra un equipo específico.

### 📱 Experiencia de Usuario (UX)
- **Modo Comentarista (Dark Mode):** Una interfaz oscura y de alto contraste optimizada para ser leída en cabinas de transmisión con poca luz.
- **Exportación de Fichas:** Un botón para generar un PDF con el resumen del partido y datos históricos del rival, listo para imprimir.
- **Buscador de Jugadores:** Filtro rápido por nombre o apellido cuando el plantel crezca.

### 🏟️ Contexto de Partidos
- **Clima y Horario:** Poder registrar si el partido fue con lluvia, sol o de noche, para ver si influye en el rendimiento.
- **Estadios:** Un mapa o lista de estadios visitados y efectividad en cada uno.

---
*Documento generado el 26 de enero de 2026.*
