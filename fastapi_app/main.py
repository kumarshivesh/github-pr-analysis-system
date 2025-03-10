"""
To run program: 
TERMINAL 1: 
cd fastapi_app
uvicorn main:app --reload --port 8000  # http://127.0.0.1:8000/docs/
TERMINAL 2:
cd django_app
python manage.py runserver 8001
TERMINAL 3:
cd django_app
celery -A django_app worker -l info -P eventlet 
TERMINAL 4:
cd django_app
celery -A django_app flower --port=5555 # http://localhost:5555/tasks
"""
# fastapi_app/main.py
import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import httpx
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Get base URL from environment variable
DJANGO_APP_BASE_URL = os.getenv('DJANGO_APP_BASE_URL', 'http://127.0.0.1:8001')

class PRAnalysisRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: Optional[str] = None

@app.post("/api/analyze-pr")
async def initiate_pr_analysis(analysis_request: PRAnalysisRequest):
    """
    Initiate a new pull request analysis task by forwarding the request to Django.
    """
    request_data = {
        "repo_url": analysis_request.repo_url,
        "pr_number": analysis_request.pr_number,
        "github_token": analysis_request.github_token
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{DJANGO_APP_BASE_URL}/api/tasks/create/",
            json=request_data
        )

        if response.status_code != 200:
            return {"error": "Failed to initiate analysis", "details": response.text}
    
    print(f"Analysis initiated for PR #{analysis_request.pr_number} in {analysis_request.repo_url}")
    task_id = response.json().get('task_id')
    return {"task_id": task_id, "status": "Analysis started"}

@app.get("/api/task-status/{task_id}/")
async def get_task_status(task_id: str):
    """
    Retrieve the current status of a PR analysis task by its ID.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{DJANGO_APP_BASE_URL}/api/tasks/{task_id}/status/")
        print(f"Status check for task {task_id}: {response.status_code}")
        return response.json()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)