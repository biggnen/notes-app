# Document Management System with Public API

This is a FastAPI-based document system example that integrates with a PostgreSQL database and uses JWT authentication for securing the endpoints.

### Table of Contents
- [Setup Instructions](#setup-instructions)
- [Using the Public API](#using-the-public-api)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Consul Integration](#consul-integration)
- [Notes](#notes)

---

## Setup Instructions

- Set Up Docker Containers

   This project uses Docker and Docker Compose for deployment.

   - Ensure Docker and Docker Compose are installed.
   - From the project directory, run the following command to build and start the containers:

        ```
        docker compose up --build
        ```

   This will start the following services:
   - PostgreSQL: A PostgreSQL database to store documents, attachments, and relationships.
   - Consul: A service discovery tool to register and discover services.
   - Notes API (Public API): A FastAPI service that interacts with the PostgreSQL database and exposes various endpoints.

- Access the Services
   - PostgreSQL: The database is running in a Docker container. You can connect to it from within the Docker network. Don't do that though.
   - Consul UI: Accessible in the docker network at `http://localhost:8500` (ensure the network configuration allows this). Again, please don't connect
   - Public API: The public API service is available at `http://localhost:8080`.

---

## Using the Public API

The public API is a FastAPI service that allows you to perform CRUD operations on documents and manage document attachments.

# Authentication

1. Get JWT Token
    - Request:
        ```
        curl -X 'POST' \
          'http://localhost:8000/token' \
          -H 'Content-Type: application/json' \
          -d '{
          "username": "your_username",
          "password": "your_password"
        }'
        ```

    - Response:
        ```json
        {
          "access_token": "<jwt_token>",
          "token_type": "bearer"
        }
        ```

---

# Documents

2. List all documents
    - Request:
        ```
        curl -X 'GET' \
          'http://localhost:8000/documents' \
          -H 'Authorization: Bearer <jwt_token>'
        ```

3. Get a specific document by ID
    - Request:
        ```
        curl -X 'GET' \
            'http://localhost:8000/documents/{document_id}' \
            -H 'Authorization: Bearer <jwt_token>'
        ```

4. Create a new document
    - Request:

        ```
        curl -X 'POST' \
          'http://localhost:8000/documents' \
          -H 'Content-Type: application/json' \
          -H 'Authorization: Bearer <jwt_token>' \
          -d '{
          "title": "New Document Title",
          "content": "This is the content of the document."
        }'
        ```

5. Update an existing document
    - Request:
        ```
        curl -X 'PUT' \
          'http://localhost:8000/documents/{document_id}' \
          -H 'Content-Type: application/json' \
          -H 'Authorization: Bearer <jwt_token>' \
          -d '{
          "title": "Updated Document Title",
          "content": "This is the updated content."
        }'
        ```

6. Delete a document
    - Request:
        ```
        curl -X 'DELETE' \
          'http://localhost:8000/documents/{document_id}' \
          -H 'Authorization: Bearer <jwt_token>'
        ```

---

# Attachments

7. Create an attachment for a document
    - Request:
        ```
        curl -X 'POST' \
          'http://localhost:8000/documents/{document_id}/attachments' \
          -H 'Authorization: Bearer <jwt_token>' \
          -F 'file=@/path/to/your/file.txt'
        ```

8. Delete an attachment for a document
    - Request:
        ```
        curl -X 'DELETE' \
          'http://localhost:8000/documents/{document_id}/attachments/{attachment_id}' \
          -H 'Authorization: Bearer <jwt_token>'
        ```

---

# Document Relations

9. Create a relationship between two documents
    - Request:
        ```
        curl -X 'POST' \
          'http://localhost:8000/documents/{document_id}/relationships' \
          -H 'Content-Type: application/json' \
          -H 'Authorization: Bearer <jwt_token>' \
          -d '{
          "target_document_id": "target_document_id",
          "relationship_type": "link"
        }'
        ```

10. Get relationships for a specific document
    - Request:
        ```
        curl -X 'GET' \
            'http://localhost:8000/documents/{document_id}/relationships' \
            -H 'Authorization: Bearer <jwt_token>'
        ```

---

# Search

11. Search documents
    - Request:
        ```
        curl -X 'GET' \
            'http://localhost:8000/documents/search?query=search_query' \
            -H 'Authorization: Bearer <jwt_token>'
        ```

### Public API Endpoints

See `http://localhost:8080/docs`

