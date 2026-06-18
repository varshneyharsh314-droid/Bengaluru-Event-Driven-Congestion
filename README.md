# AI Command Center: Bengaluru Traffic Police

A production-grade, event-driven traffic congestion prediction, crowd estimation, and emergency dispatcher platform for the Bengaluru Traffic Police Command Center.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Getting Started](#getting-started)
3. [Project Directory Structure](#project-directory-structure)
4. [Technical Specifications & System Guides](#technical-specifications--system-guides)
   - [Exploratory Data Analysis (EDA) & Feature Engineering](#1-exploratory-data-analysis-eda--feature-engineering)
   - [XGBoost Congestion Classifier & Model Retraining Pipeline](#2-xgboost-congestion-classifier--model-retraining-pipeline)
   - [Graph Theory Routing & Emergency Corridor Engine](#3-graph-theory-routing--emergency-corridor-engine)
   - [Nearest Police Station Proximity Alert System](#4-nearest-police-station-proximity-alert-system)
   - [YOLOv8 & SAHI Adaptive Crowd Estimation Pipeline](#5-yolov8--sahi-adaptive-crowd-estimation-pipeline)
   - [Closed-Loop Feedback & Self-Learning Audit System](#6-closed-loop-feedback--self-learning-audit-system)
   - [Resource Optimization & Tactical Dispatch Engine](#7-resource-optimization--tactical-dispatch-engine)
   - [Interactive Spatial Heatmaps & Timeline Replay](#8-interactive-spatial-heatmaps--timeline-replay)

---

## Architecture Overview

The project has transitioned from a legacy monolithic Streamlit design to a decoupled full-stack microservice-inspired architecture:

- **Frontend**: A modern React web dashboard built with TypeScript, TailwindCSS (styling), Leaflet (interactive spatial mapping), and Chart.js. Exposes high-fidelity widgets for real-time dispatch, route recommendations, and visual analytics. (Default port: `5173`)
- **Backend**: FastAPI web server with SQLAlchemy ORM (configured with an SQLite local fallback), Pydantic schemas, and endpoints for AI/ML inference pipelines. (Default port: `8000`)
- **ML Services**: 
  - **XGBoost Congestion Model**: Predicts traffic congestion severity and queues based on incident characteristics (planned/unplanned, zones, durations, etc.).
  - **YOLOv8 Object Detection**: Estimates crowd density and counts pedestrians from CCTV image/video uploads.

---

## Getting Started

### Prerequisites
- Node.js (v18+) & npm
- Python (v3.10+)

### 1. Launch the Backend API
1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   python -m app.main
   ```
   *The server runs at `http://localhost:8000`. Database tables will initialize and seed automatically on startup.*

### 2. Launch the React Frontend
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *Open `http://localhost:5173` in your web browser. Use `admin@bengalurutraffic.gov.in` and password `password` to log in.*

---

## Project Directory Structure

```text
├── backend/
│   ├── app/
│   │   ├── api/            # Route routers and endpoints
│   │   ├── core/           # Security, db initialization, settings config
│   │   ├── db/             # SQLAlchemy schemas and database models
│   │   ├── models/         # Pydantic schemas for request validation
│   │   ├── services/       # Core business logic / ML models integration
│   │   └── worker.py       # Celery background tasks definition
│   ├── requirements.txt    # Production Python dependencies
│   └── traffic_ops.db      # SQLite local database instance
│
├── frontend/
│   ├── src/
│   │   ├── pages/          # React views (Dashboard, Heatmap, Dispatcher, etc.)
│   │   ├── services/       # Axios API integration
│   │   ├── App.tsx         # Root routes and layouts
│   │   └── main.tsx        # React entrypoint
│   └── package.json        # Frontend NPM configurations
```

---

## Technical Specifications & System Guides

### 1. Exploratory Data Analysis (EDA) & Feature Engineering
Based on the analysis of historical events (such as waterlogging, accidents, protests, VIP movements, etc.), the system utilizes key variables to predict traffic impacts:
* **Missing Value Treatment**: Empty categorical columns (`event_type`, `event_cause`, `zone`, `junction`) are imputed with the mode, while numerical columns are imputed using median values to ensure robust inference input.
* **Feature Extraction**:
  - `hour`: Calculated from event start timestamps to capture peak commute shifts.
  - `day_of_week`: Extracted index (0 to 6) to model weekday-vs-weekend patterns.
  - `duration_hours`: Calculated as `(end_datetime - start_datetime) / 3600` to determine the temporal weight of the blockade.
* **Domain-Driven Congestion Score (DDCS)**: Designed to label historical datasets by mapping raw blockades to risk severity classes (Low, Medium, High). DDCS increases exponentially when road closures are required or if priority levels are marked as High.

### 2. XGBoost Congestion Classifier & Model Retraining Pipeline
An XGBoost classification model is used to predict traffic congestion levels (Low, Medium, High) from input incidents:
* **Preprocessing Pipeline**: Categorical features are converted via one-hot encoding, and numerical values (like event duration) are scaled using a standard scaler.
* **XGBoost Training**: The model is optimized using multiclass log-loss and serialized into `congestion_model.joblib`.
* **Retraining Pipeline**: The system includes a closed-loop retraining terminal. When new audited feedback reports arrive, if accuracy falls below a set threshold, a background task retrains the XGBoost model with the accumulated data, ensuring the classifier self-learns and adapts.

### 3. Graph Theory Routing & Emergency Corridor Engine
The emergency corridor recommendation engine dynamically routes around blockades and high-congestion zones in Bengaluru:
* **Graph Representation**: Major junctions (Silk Board, HSR Layout, Agara, Ibblur, Bellandur, Madiwala, Koramangala, BTM) are modeled as a **Weighted Directed Graph** using `networkx`. Edge weights represent travel time in minutes.
* **Dijkstra's Algorithm**: Uniform-cost search determines the baseline optimal route under free-flow or current conditions.
* **A* (A-Star) Search & Haversine Heuristic**: Re-routes emergency vehicles around dynamically blocked links. A custom Haversine heuristic estimates travel times from any junction to the target node using:
  $$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta\text{lon}}{2}\right)}\right)$$
  The heuristic dynamically guides the search, saving significant compute cycles and ensuring rapid re-routing.

### 4. Nearest Police Station Proximity Alert System
To coordinate rapid on-site incident response, the dispatch manager identifies the closest responder station:
* **Mathematical Selection**: Calculates the physical distance between the incident coordinates and all seeded police stations (such as Madivala, HSR Layout, Koramangala, etc.) using the Haversine formula.
* **ETA & Alert Generation**: Predicts transit time assuming standard dispatch speeds, audits current officer availability in the database, generates structured alerts, and logs SMS dispatch requests.

### 5. YOLOv8 & SAHI Adaptive Crowd Estimation Pipeline
Standard object detectors suffer from vehicle misclassifications, background noise, and overlapping duplicate detections. The platform addresses these through a robust, multi-stage filtering pipeline:
* **Multi-Stage Filtering**:
  1. *Class Filtering*: Prunes non-pedestrian boxes (restricts class to `person` / class 0).
  2. *Confidence Pruning*: Dynamically filters out low-confidence boxes.
  3. *Size Constraints*: Removes tiny, out-of-focus background boxes.
  4. *Global NMS Deduplication*: Applies custom Non-Maximum Suppression to remove overlapping duplicates.
* **Slicing Aided Hyper Inference (SAHI)**: High-density crowds cause significant undercounting in default models. The system runs a fast first-pass assessment to evaluate baseline density. If density is high (e.g., rallies or protests), it dynamically divides the CCTV frame into overlapping grids (2x2 up to 4x4) to run localized inference, combining results with NMS to ensure precision.

### 6. Closed-Loop Feedback & Self-Learning Audit System
Ensuring continuous model calibration, the system records user audits in an SQLite/PostgreSQL schema:
* **`feedback_audit_logs` Schema**:
  - `id`: Primary key.
  - `incident_id`: Foreign key referencing the historical incident log.
  - `model_prediction`: The XGBoost predicted congestion level.
  - `ground_truth`: The human-audited congestion level.
  - `drift_detected`: Boolean indicating if the model misclassified.
  - `comments`: Qualitative auditor feedback.
* **Calibration Triggers**: An endpoint evaluates the mismatch rate. If the model's accuracy drops below the configured threshold, it automatically triggers background calibration.

### 7. Resource Optimization & Tactical Dispatch Engine
A rule-based optimization engine converts predictions and crowd metrics into tactical actions:
* **Police Allocation**: Establishes a base count (Low: 2, Medium: 4, High: 8, Extreme: 15) and applies modifiers for road closures (+4), unplanned incidents (+2), and extreme crowd densities (up to +12).
* **Barricade Deployment**: Scales units depending on safety cordons and crowd density levels.
* **Intersection Signal Overrides**: Flags adjacent intersections for manual green-light extensions to clear oncoming congestion.

### 8. Interactive Spatial Heatmaps & Timeline Replay
Spatial data is fully integrated into visual dashboards:
* **Folium/Leaflet Maps**: Translates coordinates into interactive layers, overlaying incident markers (color-coded by severity) and safety buffers.
* **Timeline Replay**: An animated playback control allows operators to slide through hours (e.g., 4 PM to 8 PM) to observe the propagation and clearing of gridlock and crowd hotspots across the city graph over time.
