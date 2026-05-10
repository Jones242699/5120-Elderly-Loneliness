# Places API Documentation

## 📌 Overview

The Places API provides location-based discovery of nearby public artworks and places in Melbourne.

It supports:

* Location-based search (distance + radius)
* Category filtering
* Default fallback location
* Detailed place information retrieval

---

## 🌐 Base URL

```bash
https://j5d3dob643.execute-api.ap-southeast-2.amazonaws.com
```

---

## 🥇 Get Nearby Places

### 📍 Endpoint

```http
GET /places
```

---

### 📥 Query Parameters

| Parameter | Type   | Required | Description                             |
| --------- | ------ | -------- | --------------------------------------- |
| lat       | float  | ❌        | User latitude                           |
| lng       | float  | ❌        | User longitude                          |
| radius    | float  | ❌        | Search radius in meters (default: 5000) |
| limit     | int    | ❌        | Number of results (default: 20)         |
| category  | string | ❌        | Filter by category                      |

---

### 📌 Default Behaviour

If no location is provided:

```bash
lat = -37.8136
lng = 144.9631
```

(Melbourne CBD is used as default location)

---

### 📤 Response

```json
{
  "places": [
    {
      "id": 1,
      "name": "Black Swan Memorial Drinking Fountain",
      "category": "Monument",
      "address": "Alexandra Gardens, Melbourne",
      "latitude": -37.81957,
      "longitude": 144.97182,
      "distance": 850.23
    }
  ],
  "total": 20
}
```

---

### 🧠 Notes

* Results are sorted by distance (nearest first)
* Distance is returned in meters
* Only lightweight fields are returned for performance
* Uses PostGIS spatial functions

---

### 🧪 Example Request

```http
GET /places?lat=-37.81&lng=144.96&radius=2000
```

---

### 🧪 Example Response

```json
{
  "places": [
    {
      "id": 3,
      "name": "Statue of Meditation",
      "category": "Art",
      "address": "Melbourne Park",
      "latitude": -37.81,
      "longitude": 144.97,
      "distance": 120.5
    }
  ],
  "total": 1
}
```

---

## 🥈 Get Place Detail

### 📍 Endpoint

```http
GET /places/{id}
```

---

### 📥 Path Parameter

| Parameter | Type | Description     |
| --------- | ---- | --------------- |
| id        | int  | Unique place ID |

---

### 📤 Response

```json
{
  "id": 1,
  "name": "Black Swan Memorial Drinking Fountain",
  "category": "Monument",
  "address": "Alexandra Gardens, Melbourne",
  "artist": "Raymond B. Ewers",
  "year": "1974",
  "description": "Bluestone drinking fountain with bronze plaque",
  "latitude": -37.81957,
  "longitude": 144.97182
}
```

---

### ❗ Error Response

```json
{
  "error": "Place not found"
}
```

---

## 🧠 Design Decisions

### 🔹 Separation of List and Detail APIs

* `/places` returns lightweight data for UI cards
* `/places/{id}` returns full details for side panel

This improves performance and scalability.

---

### 🔹 Location-Based Search

Implemented using PostGIS spatial functions:

* `ST_DWithin` → radius filtering
* `ST_Distance` → distance calculation
* Results are sorted by proximity

---

### 🔹 Default Location Fallback

Ensures usability when:

* User denies location access
* Location is unavailable

---

## ⚙️ Tech Stack

* AWS Lambda (Python 3.12)
* API Gateway (HTTP API)
* Amazon RDS (PostgreSQL + PostGIS)
* psycopg2 (Lambda Layer)

---

## ⚠️ Limitations

* Category filter supports only single value
* No pagination (limit-based only)
* Distance unit fixed in meters

---

## 🚀 Future Improvements

* Multi-category filtering
* Pagination (page / offset)
* Distance formatting (meters → km)
* Image support
* Caching for performance
