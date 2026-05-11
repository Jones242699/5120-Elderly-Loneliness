# 5120 Elderly Loneliness Web

## 📌 Project Overview

This project aims to reduce loneliness among older adults (60+) in the City of Melbourne by leveraging spatial data, cloud infrastructure, and location-based services.

Key features include:

- Walkable route suggestions
- Access to nearby support services (e.g. counselling centres)
- Integration of urban data (e.g. tree canopy, pedestrian density)
- Data-driven route scoring and recommendations

The system is designed as a cloud-based web application using AWS services, with a focus on scalability, modularity, and data-driven decision making.

---

## 🏗️ Project Structure

```text
├── backend/   # AWS Lambda functions (core backend logic)
├── data/      # Database-related files and data processing scripts
├── frontend/  # Frontend Git submodule (separate repository)
├── infra/     # Infrastructure as Code (AWS CDK)
├── README.md
└── .gitignore
```

The project uses a modular repository structure, where the frontend is linked as a Git submodule while backend and infrastructure are maintained in this repository.

---

### 🔹 backend/

Contains all backend logic implemented using **AWS Lambda (Python)**.

Includes:

- API endpoints (via API Gateway)
- Database queries (PostgreSQL + PostGIS)
- Route scoring logic:
  - Shade score (tree canopy)
  - Pedestrian density score
- Nearby services and places search
- Route recommendation support APIs

---

### 🔹 data/

Contains database-related resources, including:

- Data cleaning pipelines
- Dataset integration (City of Melbourne open datasets)
- Scripts for preparing and inserting data into PostgreSQL
- Spatial data processing for PostGIS

---

### 🔹 frontend/

This folder contains the active frontend application integrated as a **Git submodule**.

The frontend is maintained in a **separate GitHub repository**, but linked into this project for unified project structure and easier collaboration.

The frontend includes:

- Vue.js application
- Google Maps integration
- Route visualization
- User interaction and UI components
- API integration with backend services

---

### 🔹 infra/

Contains infrastructure definitions using **AWS CDK (Infrastructure as Code)**.

Includes configuration for:

- API Gateway
- Lambda functions
- IAM roles and permissions
- VPC and Security Groups (for RDS access)
- Event scheduling for automated data sync

The system is organised into multiple stacks (e.g. ApiStack, PlacesStack, PedestrianScoreStack, etc.) for modular deployment.

---

## ⚙️ Tech Stack

### Backend
- AWS Lambda (Python 3.x)
- API Gateway
- PostgreSQL (RDS)
- PostGIS (spatial queries)

### Data
- City of Melbourne Open Data
- Custom data processing pipelines

### Infrastructure
- AWS CDK (Infrastructure as Code)
- IAM
- VPC
- Security Groups
- EventBridge Scheduler

### Frontend
- Vue.js
- Google Maps API
- Git Submodule integration

---

## 🔌 API Overview

Base URL:

```text
https://<your-api-id>.execute-api.ap-southeast-2.amazonaws.com
```

---

### Available Endpoints

### GET /places

Retrieve nearby places based on user location.

Supports:
- Radius filtering
- Category filtering
- Distance-based sorting

---

### GET /places/{id}

Retrieve detailed information about a specific place.

---

### GET /venues

Retrieve nearby venues such as cafes, restaurants, and community spaces.

Supports:
- User location filtering
- Category filtering
- Radius filtering

---

### GET /venues/{id}

Retrieve detailed information about a specific venue.

---

### GET /benches

Retrieve nearby public benches using spatial bounding box queries.

---

### GET /counseling-centers

Find nearby counselling and support services.

---

### GET /crowd-density

Retrieve live pedestrian density data for map overlays and crowd visualization.

---

### POST /score/pedestrian

Calculate pedestrian density scores for routes using live pedestrian data.

---

### POST /score/shade

Calculate shade scores based on nearby tree canopy coverage.

---

### POST /routes

Generate and rank walking routes using:
- Google Maps routing
- Shade score
- Pedestrian density score

Routes are ranked using a weighted scoring system.

---

## 🚀 Deployment

The backend infrastructure is deployed using AWS CDK with multiple modular stacks.

### Typical workflow

1. Define infrastructure using CDK stacks

2. Deploy infrastructure:

```bash
cd infra
source .venv/bin/activate
cdk deploy --all
```

3. Lambda functions are automatically integrated with API Gateway

4. PostgreSQL (RDS + PostGIS) is accessed through configured VPC networking

5. APIs are tested using:
- Postman
- Browser requests
- CloudWatch Logs

---

## 📊 Current Status

| Component | Status |
|---|---|
| Backend | ✅ Active |
| Database | ✅ Active |
| Data Pipeline | ✅ Active |
| Frontend Submodule | ✅ Active |
| Infrastructure | ✅ CDK-based |

---

## 📌 Notes

- This repository primarily focuses on:
  - Backend services
  - Spatial data processing
  - Cloud infrastructure
  - API development

- Frontend development is maintained in a separate repository and linked via Git submodule

- Infrastructure evolved during the project:
  - Early stage: manual / tool-generated setup
  - Iteration 2+: AWS CDK (Infrastructure as Code)

- The system uses spatial queries through PostGIS to support location-aware features

---

## 👥 Team & Course Context

This project is developed as part of **FIT5120 (Monash University)**.

The project follows an iterative development approach with continuous integration of:

- Data-driven features
- Cloud-based architecture
- Spatial computing
- User-centered design for older adults

---

## 📎 Future Work

- Intelligent route recommendation based on:
  - Shade coverage (tree canopy)
  - Pedestrian density
  - Accessibility (benches, toilets)

- Community event integration

- Personalized memory and feeling tracking for visited places

- Improved UI/UX for accessibility:
  - Larger fonts
  - Simplified navigation
  - Elderly-friendly interaction design

- Enhanced social engagement recommendations