# Carbon Foot Print Estimator
*A powerful platform to estimate the carbon footprint of food items and recipes, helping users make sustainable dietary choices.*

![Carbon FootPrint Banner](https://github.com/vipulc2580/Carbon_Food_Print_Estimator/blob/main/images/Streamlit_ui.png)  

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Acknowledgements](#acknowledgements)

## Introduction

Carbon Food Print Estimator is a full-featured web application designed to help users understand the environmental impact of their food choices. It supports ingredient-level carbon footprint calculations, user authentication, and interactive visualizations. The project leverages FastAPI for the backend, Streamlit for the frontend, and uses Celery with Redis for background tasks like sending emails and heavy computations.

## Features

- **User Authentication**  
  Secure registration, login, logout, email verification, password reset, and profile management.

- **Carbon Footprint Estimation**  
  Estimate the carbon footprint per ingredient /entire dish based on data inferred from LLM.

- **Recipe Input & Tracking**  
  Input recipes manually or via file upload, and track previously estimated analysis.

- **Background Tasks & Notifications**  
  Celery-powered background processing for email verification, password reset, and carbon footprint analysis caching.

- **Interactive Frontend**  
  Streamlit-based interface for user-friendly interaction and visualization of results.

- **Database Management**  
  PostgreSQL database (initial DB: Reewild) for storing users data,probably carbon footprint analysis persistence..

## Technologies Used

- **Backend:**:Python, FastAPI
- **Frontend:**:Streamlit 
- **Database:**:PostgreSQL
- **Task Queue & Cache**:Celery, Redis
- **Others:**:Pandas, NumPy, Plotly / Matplotlib, RESTful APIs

## Installation & Setup

1. **Clone the repository:**

   ```bash
   https://github.com/vipulc2580/Carbon_Food_Print_Estimator
   cd Carbon_Food_Print_Estimator
    ```

2. **Create and activate a virtual environment:**
    ```python 
      python -m venv env
      env\Scripts\activate  # On macOS/Linux use: source env/bin/activate
    ```

3. **Install dependencies:**
    ```python
       pip install -r requirements.txt
    ```    

4. **Configure PostgreSQL database:**
    - Create a database named Reewild.
    - Update the database credentials in your .env as example_env

5. **Start Redis server (for Celery broker and cache):**
    ```bash
     redis-server
    ```
6. **Start Celery worker:**
   ```python
       celery -A src.utils.celery_tasks.celery_app worker --pool=solo -l info
   ```

7. **Run the FastAPI server:**
    ```python
      fastapi dev .\src     
    ```
8. **Run the Streamlit frontend:**
   ```python
     streamlit run .\frontend\app.py  
    ```
9. **Access the application:**
    - FastAPI docs: http://localhost:8000/api/v1/docs
    - Streamlit UI: http://localhost:8501

# Usage
  ## User Journey:
  - Register/login to your account.
  - Verify themselves using verification email
  - Visit the Streamlit UI Enter / Upload Dish using Search or Vision Tabs
  - Get Complete Dish Carbon Food Print Estimation Analysis
  - Interactive charts and graphs displaying carbon footprint trends
  ![Carbon FootPrint UI Interactive](https://github.com/vipulc2580/Carbon_Food_Print_Estimator/blob/main/images/Streamlit_ui_2.png)

  ## Admin / Backend::
  - Manage users and database.
  - Monitor Celery tasks and Redis cache.
  - Access API endpoints for automation or integration.

# API Documentation
  - FastAPI automatically generates interactive docs available at:
    - http://localhost:8000/api/v1/docs
  - Auth Service Endpoints: Registration, login, logout, email verification, password reset.
  - Estimator Service Endpoints: Ingredient carbon footprint calculation, recipe submissions, history retrieval.
![Carbon FootPrint API Banner](https://github.com/vipulc2580/Carbon_Food_Print_Estimator/blob/main/images/API_DOC_IMAGE.png)  
 
 # Acknowledgements
  - Thanks to FastAPI, Streamlit, Celery, Redis, and PostgreSQL communities for enabling modern web development.
  - Inspired by environmental sustainability initiatives and modern data-driven applications.
  - Special thanks to open-source contributors who maintain libraries used in this project.

