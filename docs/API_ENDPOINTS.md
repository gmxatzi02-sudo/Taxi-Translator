# API Endpoints Documentation

This document provides detailed descriptions of the REST API endpoints for the Taxi Translator application.

## Base URL

The base URL for all API requests is:

```
https://api.taxitranslator.example.com/v1
```

## Authentication

All API requests require authentication using a Bearer token.

## Endpoints

### 1. Get All Translations
- **Endpoint:** `/translations`
- **Method:** `GET`
- **Auth Required:** Yes

#### Request
```http
GET /translations HTTP/1.1
Authorization: Bearer {token}
```

#### Response
- **Status:** `200 OK`
- **Content:**
```json
[
    {
        "id": "12345",
        "original": "Hello",
        "translated": "Hola"
    },
    {
        "id": "12346",
        "original": "Goodbye",
        "translated": "Adiós"
    }
]
```

### 2. Create a Translation
- **Endpoint:** `/translations`
- **Method:** `POST`
- **Auth Required:** Yes

#### Request
```http
POST /translations HTTP/1.1
Authorization: Bearer {token}
Content-Type: application/json

{
    "original": "Good Morning",
    "language": "es"
}
```

#### Response
- **Status:** `201 Created`
- **Content:**
```json
{
    "id": "12347",
    "original": "Good Morning",
    "translated": "Buenos Días"
}
```

### 3. Get Translation by ID
- **Endpoint:** `/translations/{id}`
- **Method:** `GET`
- **Auth Required:** Yes

#### Request
```http
GET /translations/12347 HTTP/1.1
Authorization: Bearer {token}
```

#### Response
- **Status:** `200 OK`
- **Content:**
```json
{
    "id": "12347",
    "original": "Good Morning",
    "translated": "Buenos Días"
}
```

### 4. Delete Translation
- **Endpoint:** `/translations/{id}`
- **Method:** `DELETE`
- **Auth Required:** Yes

#### Request
```http
DELETE /translations/12347 HTTP/1.1
Authorization: Bearer {token}
```

#### Response
- **Status:** `204 No Content`

## Error Responses

When an error occurs, the API responds with an appropriate HTTP status code and error message.

### Example of an Error Response

- **Status:** `404 Not Found`
- **Content:**
```json
{
    "error": "Translation not found"
}
```

## Conclusion

This document outlines the fundamental API endpoints for the Taxi Translator application. For further details, please refer to individual endpoint documentation.