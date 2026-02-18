# Project Structure

This document outlines the directory organization for both the Python FastAPI backend and React frontend of the Taxi Translator project.

## Root Directory
- **/backend**: Contains the FastAPI backend code.
- **/frontend**: Contains the React frontend code.
- **/docker**: Docker configuration files.
- **/docs**: Documentation files.

## Backend Directory (`/backend`)
- **main.py**: Entry point for the FastAPI application.
- **/api**: Contains API route definitions.
- **/models**: Database models.
- **/schemas**: Pydantic schemas for data validation.
- **/services**: Logic for handling requests and responses.
- **/tests**: Unit tests for the backend.

## Frontend Directory (`/frontend`)
- **src/**: Contains all the React application source code.
- **public/**: Static files such as images and index.html.
- **package.json**: Lists dependencies and scripts for the React application.

## Additional Directories
- **/config**: Configuration files for both backend and frontend.
- **/scripts**: Utility scripts for setup and maintenance.