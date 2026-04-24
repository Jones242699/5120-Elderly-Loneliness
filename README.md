# 5120 Elderly Loneliness Web

## 📌 Project Overview

This project aims to reduce loneliness among older adults (60+) in the City of Melbourne by providing location-based support, including:

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
├── infra/     # Infrastructure setup files (AWS CLI generated)
├── README.md
└── .gitignore
```


### 🔹 backend/
Contains all backend logic implemented using **AWS Lambda (Python)**.

Includes:
- API endpoints (via API Gateway)
- Database queries (PostgreSQL + PostGIS)
- Route scoring logic (e.g. shade, pedestrian density)

---

### 🔹 data/
Contains database-related resources, including:
- Data cleaning pipelines
- Dataset integration (e.g. Melbourne open datasets)
- Scripts for preparing data before inserting into database

---

### 🔹 frontend/
This folder contains an **initial Vue.js scaffold**, but it is **not currently in use**.

👉 The active frontend is hosted in a **separate GitHub repository**.

---

### 🔹 infra/
Contains infrastructure-related files generated during setup.

- Initially created using AWS tools
- From **Iteration 2 onwards, AWS CLI is used for infrastructure management**

Includes configurations for:
- Lambda deployment
- API Gateway
- Supporting cloud resources

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
- AWS CLI
- IAM, VPC, Security Groups

### Frontend
- Vue.js (separate repository)

---

## 🚀 Deployment

Backend services are deployed using AWS Lambda and exposed via API Gateway.

Typical workflow:
1. Develop Lambda functions locally
2. Deploy using AWS CLI
3. Connect to RDS database
4. Test via API endpoints (Postman / browser)

---

## 📊 Current Status

| Component   | Status |
|------------|--------|
| Backend     | ✅ Active |
| Database    | ✅ Active |
| Data Pipeline | ✅ Active |
| Frontend (this repo) | ⚠️ Not in use |
| Frontend (separate repo) | ✅ Active |
| Infrastructure | ✅ CLI-based (Iteration 2 onwards) |

---

## 📌 Notes

- This repository focuses primarily on **backend, data, and infrastructure**
- Frontend development is maintained separately
- Infrastructure approach evolved during the project:
  - Early stage: tool-generated setup
  - Iteration 2+: AWS CLI-based management

---

## 👥 Team & Course Context

This project is developed as part of **FIT5120 (Monash University)**.

It follows an **iterative development approach**, with continuous integration of:
- Data-driven features
- Cloud-based architecture
- User-centered design for older adults

---

## 📎 Future Work

- Full frontend integration
- Route recommendation engine
- Event/activity recommendation system
- Enhanced usability for elderly users