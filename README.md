# Stateful Backend Workflow System

## Live Demo
https://stateful-backend-workflow.onrender.com/docs


## Overview

This project is a backend system built using FastAPI and PostgreSQL to manage workflows and their state transitions.

It supports secure user authentication, controlled workflow progression, and maintains both current state and historical records.

---

## Features

* REST APIs built using FastAPI
* PostgreSQL database with relational schema
* JWT-based authentication for protected endpoints
* Controlled workflow state transitions
* Transaction handling for data consistency
* Workflow history tracking
* SQL JOINs for relational data retrieval

---

## Tech Stack

* Python
* FastAPI
* PostgreSQL
* psycopg
* JWT (python-jose)

---

## Setup Instructions

### 1. Clone the repository

git clone <your-repo-url>

### 2. Navigate to project

cd stateful-backend-workflow

### 3. Create virtual environment

python -m venv venv

### 4. Activate virtual environment

venv\Scripts\activate

### 5. Install dependencies

pip install -r requirements.txt

### 6. Run server

uvicorn app.main:app --reload

---

## API Endpoints

### Auth

POST /login

### Users

POST /users

### Workflows

POST /workflows
PUT /workflows/{workflow_id}/state
GET /workflows/{workflow_id}

---

## Key Concepts Implemented

* Stateless authentication using JWT
* Transaction management for consistency
* State machine validation for workflows
* Separation of current state and historical data
* Secure identity handling using token-based user context

---

## Notes

This project is designed for learning backend fundamentals and demonstrating system design and data consistency concepts in interviews.
