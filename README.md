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

## ⚙️ Instalación y Ejecución del Proyecto

### 🧱 Requisitos Previos

Antes de comenzar asegúrate de tener instalado:

- [Python 3.9+](https://www.python.org/downloads/)
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install)
- [Docker](https://docs.docker.com/get-docker/)
- PowerShell (para ejecutar el script `deploy_cloudrun.ps1` en Windows)
- Cuenta de Google Cloud con permisos para usar Cloud Run

---

### 🧩 1️⃣ Clonar el Repositorio

```bash
git clone https://github.com/usuario/deacero-steel-rebar-api.git
cd deacero-steel-rebar-api
```
---

### 🧰 2️⃣ Crear y Activar un Entorno Virtual
En Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 📦 3️⃣ Instalar Dependencias
```bash
pip install -r requirements.txt
```

🚀 4️⃣ Ejecutar la API Localmente
```bash
uvicorn app.api.main:app --reload
```

☁️ 5️⃣ Despliegue en Google Cloud Run
```bash
.\deploy_cloudrun.ps1
```
