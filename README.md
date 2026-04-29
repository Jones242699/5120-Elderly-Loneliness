# 5120 Elderly Loneliness Web

## 📌 Project Overview

This project aims to reduce loneliness among older adults (60+) in the City of Melbourne by leveraging spatial data, cloud infrastructure, and location-based services.

Key features include:

- Walkable route suggestions (future)
- Access to nearby support services (e.g. counselling centres)
- Integration of urban data (e.g. tree canopy, pedestrian density)

The system is designed as a cloud-based web application using AWS services, with a focus on scalability, modularity, and data-driven decision making.

---

## 🏗️ Project Structure

```
├── backend/   # AWS Lambda functions (core backend logic)
├── data/      # Database-related files and data processing scripts
├── frontend/  # Initial Vue structure (not in use)
├── infra/     # Infrastructure as Code (AWS CDK)
├── README.md
└── .gitignore
```

---

### 🔹 backend/

Contains all backend logic implemented using **AWS Lambda (Python)**.

Includes:

- API endpoints (via API Gateway)
- Database queries (PostgreSQL + PostGIS)
- Route scoring logic:
  - Shade score (tree canopy)
  - Pedestrian density score

---

### 🔹 data/

Contains database-related resources, including:

- Data cleaning pipelines
- Dataset integration (City of Melbourne open datasets)
- Scripts for preparing and inserting data into PostgreSQL

---

### 🔹 frontend/

This folder contains an **initial Vue.js scaffold**, but it is **not currently in use**.

👉 The active frontend is hosted in a **separate GitHub repository**.

---

### 🔹 infra/

Contains infrastructure definitions using **AWS CDK (Infrastructure as Code)**.

Includes configuration for:

- API Gateway
- Lambda functions
- IAM roles and permissions
- VPC and Security Groups (for RDS access)

The system is organised into multiple stacks (e.g. ApiStack, PlacesStack, etc.) for modular deployment.

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
- IAM, VPC, Security Groups

### Frontend
- Vue.js (separate repository)

---

## 🔌 API Overview

Base URL:
```
https://<your-api-id>.execute-api.ap-southeast-2.amazonaws.com
```

### Available Endpoints

- **GET /places**  
  Retrieve nearby places based on user location

- **GET /benches**  
  Retrieve nearby benches using bounding box query

- **GET /counseling-centers**  
  Find nearby counselling and support services

- **POST /score/pedestrian**  
  Calculate pedestrian density score for routes

- **POST /score/shade**  
  Calculate shade score based on tree canopy coverage

---

## 🚀 Deployment

The backend is deployed using AWS CDK with multiple stacks.

### Typical workflow:

1. Define infrastructure using CDK stacks
2. Deploy using:

```bash
cd infra
source .venv/bin/activate
cdk deploy --all
```

3. Lambda functions are automatically integrated with API Gateway
4. RDS (PostgreSQL + PostGIS) is accessed via VPC
5. APIs are tested using Postman or browser

---

## 📊 Current Status

| Component   | Status |
|------------|--------|
| Backend     | ✅ Active |
| Database    | ✅ Active |
| Data Pipeline | ✅ Active |
| Frontend (this repo) | ⚠️ Not in use |
| Frontend (separate repo) | ✅ Active |
| Infrastructure | ✅ CDK-based |

---

## 📌 Notes

- This repository focuses on **backend, data, and infrastructure**
- Frontend development is maintained separately
- Infrastructure evolved during the project:
  - Early stage: manual / tool-generated setup
  - Iteration 2+: AWS CDK (Infrastructure as Code)

---

## 👥 Team & Course Context

This project is developed as part of **FIT5120 (Monash University)**.

It follows an **iterative development approach**, with continuous integration of:

- Data-driven features
- Cloud-based architecture
- User-centered design for older adults

---

## 📎 Future Work

- Intelligent route recommendation based on:
  - Shade coverage (tree canopy)
  - Pedestrian density
  - Accessibility (benches, toilets)
- Community event integration
- Improved UI/UX for accessibility (larger fonts, simplified navigation)