# Vision360

**AI-powered multi-camera surveillance and analytics platform** — real-time computer vision detection (PPE compliance, theft, attendance, and more), built on Django REST Framework, Celery, and React.

<p>
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/YOLOv8-111F68?style=for-the-badge&logo=ultralytics&logoColor=white" />
</p>

---

## Overview

Vision360 lets an organization connect RTSP camera feeds, assign one or more AI detection models per camera, and view real-time compliance/security events on a live dashboard. It's built around a **pluggable model adapter architecture** — new detection models can be added without touching the core inference pipeline.

## Features

- 🔐 **JWT authentication & RBAC** — secure multi-user access via `dj-rest-auth` / `django-allauth`
- 📷 **Camera management** — add, test, and monitor RTSP camera connections with live status (online/offline)
- 🧠 **Pluggable AI model registry** — five detection models running behind a single unified interface:
  | Model | Type | Detects |
  |---|---|---|
  | PPE Detection | Custom YOLOv8 | Hardhat / safety vest compliance |
  | Theft Detection | Roboflow hosted API | Theft / suspicious activity |
  | Shoplifting Detection | Custom YOLOv8 | Shoplifting / suspicious activity |
  | Attendance | YOLOv8n (COCO) | Person presence |
  | Facial Expression | Hugging Face ViT | Emotion classification |
- ⚙️ **Per-camera model assignment** — toggle which models run on which cameras, with full audit logging
- 🔄 **Async detection pipeline** — Celery + Redis handle scheduled RTSP frame capture and inference without blocking the API
- 📊 **KPI rollup engine** — aggregates raw detections into 1-hour / 1-day / 1-week compliance metrics
- 📈 **Live dashboard API** — per-camera KPI tiles, recent events feed, and model health status
- 🐳 **Fully Dockerized** — one-command local setup via Docker Compose

## Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│   React     │◄────►│  Django REST API │◄────►│ PostgreSQL  │
│  Frontend   │      │   (DRF + JWT)    │      │             │
└─────────────┘      └────────┬─────────┘      └─────────────┘
                               │
                      ┌────────▼─────────┐
                      │  Celery Beat/Worker│
                      │  (Redis broker)    │
                      └────────┬─────────┘
                               │
                      ┌────────▼─────────┐
                      │  Model Adapter    │
                      │  Registry         │
                      │ ┌───┬───┬───┬───┐ │
                      │ │PPE│Thf│Att│Exp│ │
                      │ └───┴───┴───┴───┘ │
                      └───────────────────┘
```

Each model implements a common `BaseModelAdapter` interface (`load()`, `run(frame)`, `health()`), registered via a decorator pattern — adding a new detection model means writing one adapter class, no changes to the worker loop or API layer.

## Tech Stack

**Backend:** Django, Django REST Framework, PostgreSQL, Celery, Redis, Docker
**Frontend:** React.js
**AI/ML:** YOLOv8 (Ultralytics), Hugging Face Transformers, OpenCV, Roboflow Inference API
**Auth:** JWT (SimpleJWT), django-allauth, dj-rest-auth

## Getting Started

### Prerequisites
- Docker & Docker Compose
- A Google/Roboflow/Hugging Face API key where applicable (see `.env.example`)

### Setup

```bash
git clone https://github.com/<your-username>/vision360.git
cd vision360
cp .env.example .env   # fill in DB credentials, API keys
docker compose up --build
```

The backend will be available at `http://localhost:8000`, and the frontend at `http://localhost:5173`.

### Running migrations
```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

## API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/cameras/` | GET/POST | List / create cameras |
| `/api/cameras/:id/test_connection/` | POST | Test an RTSP camera connection |
| `/api/cameras/:id/models/:model_name/` | PATCH | Enable/disable a model for a camera |
| `/api/detections/` | GET | List detections (filterable by camera, model, date range) |
| `/api/dashboard/?camera=:id` | GET | KPI tiles, recent events, and model status for a camera |
| `/api/assignments/` | GET/POST | Manage camera–model assignments |

## Project Structure

```
vision360/
├── core/
│   ├── adapters.py       # Model adapter registry (PPE, Theft, Attendance, etc.)
│   ├── models.py         # Camera, Detection, ModelAssignment, KpiRollup, AuditLog
│   ├── tasks.py          # Celery tasks: run_inference, rollup_kpis
│   ├── views.py          # DRF viewsets
│   ├── serializers.py
│   └── urls.py
├── frontend/              # React app
├── docker-compose.yml
└── requirements.txt
```

## Known Limitations

- Live RTSP → WebSocket frame streaming to the frontend is not yet implemented (dashboard currently polls detection data rather than showing live video)
- Report export (CSV/PDF) is planned but not yet built
- Some model dependencies (OpenCV, PyTorch, `inference-sdk`) require pinned versions — see `requirements.txt` for tested combinations

## License

This project is licensed under the MIT License.

## Author

**Sufiyan Sikander**
[LinkedIn](https://www.linkedin.com/in/sufiyan-sikander-122269319/) · [GitHub](https://github.com/Sufiyan-Sikander) · sufiyansikander786@gmail.com
