# 🏗️ DeAcero – Steel Rebar Price Prediction API

API REST desarrollada como parte del reto técnico de **DeAcero** para predecir el **precio de cierre del día siguiente de la varilla corrugada (steel rebar)** en USD por tonelada métrica.  
El modelo combina datos de commodities y tipo de cambio obtenidos de fuentes públicas y se despliega automáticamente en **Google Cloud Run**.

---

## 🚀 Descripción General

- **Objetivo:** Predecir el precio de cierre diario de la varilla corrugada (steel rebar) en función de indicadores económicos globales.  
- **Modelo:** `RandomForestRegressor` entrenado con cuatro variables macroeconómicas.  
- **Despliegue:** Contenedor Docker desplegado con **Google Cloud Run** usando script PowerShell (`deploy_cloudrun.ps1`).  
- **Documentación interactiva:** 👉 [https://steel-rebar-api-759941914967.us-central1.run.app/docs](https://steel-rebar-api-759941914967.us-central1.run.app/docs)

---

## 🧩 Arquitectura del Sistema

```text
┌───────────────────────────────┐
│   Yahoo Finance / Investing   │
│   (Datos históricos)          │
└───────────────┬───────────────┘
                │
        Extracción y Limpieza
                │
                ▼
    RandomForestRegressor Model
    Entrenamiento y Serialización (.pkl)
                │
                ▼
        FastAPI REST Endpoints
                │
                ▼
       Despliegue en Cloud Run
