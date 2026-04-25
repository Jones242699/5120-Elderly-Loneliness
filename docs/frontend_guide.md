# Frontend Integration Guide

## 📌 Overview

This guide explains how to integrate and use the Places API in frontend applications.

---

## 🌐 Base URL

```bash
https://j5d3dob643.execute-api.ap-southeast-2.amazonaws.com
```

---

## 🚀 Fetch Nearby Places

### Example (JavaScript)

```javascript
fetch(
  "https://j5d3dob643.execute-api.ap-southeast-2.amazonaws.com/places?lat=-37.81&lng=144.96&radius=2000"
)
  .then(res => res.json())
  .then(data => console.log(data));
```

---

### 🔧 Parameters

| Parameter | Required | Description            |
| --------- | -------- | ---------------------- |
| lat       | ❌        | User latitude          |
| lng       | ❌        | User longitude         |
| radius    | ❌        | Search radius (meters) |
| limit     | ❌        | Number of results      |
| category  | ❌        | Filter category        |

---

### 📌 Behaviour

* If `lat/lng` not provided → default Melbourne CBD
* Results sorted by distance (nearest first)
* Distance returned in meters

---

### 📤 Response Structure

```json
{
  "places": [
    {
      "id": 1,
      "name": "...",
      "category": "...",
      "latitude": ...,
      "longitude": ...,
      "distance": ...
    }
  ],
  "total": 20
}
```

---

## 🥈 Fetch Place Detail

### Example (JavaScript)

```javascript
fetch(
  "https://j5d3dob643.execute-api.ap-southeast-2.amazonaws.com/places/1"
)
  .then(res => res.json())
  .then(data => console.log(data));
```

---

### 📤 Response

```json
{
  "id": 1,
  "name": "...",
  "category": "...",
  "address": "...",
  "artist": "...",
  "year": "...",
  "description": "...",
  "latitude": ...,
  "longitude": ...
}
```

---

## 🧠 UI Usage Suggestions

### 🟦 List View (Cards)

Use fields:

* name
* category
* distance
* location

---

### 🟩 Detail View (Side Panel)

Use fields:

* artist
* year
* description
* full address

---

## ⚠️ Important Notes

* Always handle empty results
* Always handle API errors (500 / 404)
* Do not assume all fields are present

---

## ❗ Error Handling Example

```javascript
fetch(url)
  .then(res => {
    if (!res.ok) throw new Error("API Error");
    return res.json();
  })
  .then(data => console.log(data))
  .catch(err => console.error(err));
```

---

## 🎯 Summary

Frontend should:

* Call `/places` for list
* Call `/places/{id}` for detail
* Pass location when available
* Render based on returned data structure
