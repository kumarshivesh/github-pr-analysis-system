# django_app/home/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .tasks import execute_pr_analysis
from celery.result import AsyncResult

@api_view(['POST'])
def create_analysis_task(request):
    """
    API endpoint to create a new pull request analysis task.
    
    Expected POST data:
    - repo_url: GitHub repository URL
    - pr_number: Pull request number
    - github_token: Optional GitHub token for private repos
    
    Returns:
        Task ID and status
    """
    data = request.data
    repo_url = data.get('repo_url')
    pr_number = data.get('pr_number')
    github_token = data.get('github_token')
    
    # Validate required parameters
    if not repo_url or not pr_number:
        return Response({
            "error": "Missing required parameters",
            "message": "Both repo_url and pr_number are required"
        }, status=400)
    
    # Launch the analysis task
    task = execute_pr_analysis.delay(repo_url, pr_number, github_token)

    return Response({
        "task_id": task.id,
        "status": "Analysis task created"
    })


@api_view(['GET'])
def get_task_status(request, task_id):
    """
    API endpoint to check the status of an analysis task.
    
    Args:
        task_id: ID of the task to check
        
    Returns:
        Task status and results if available
    """
    result = AsyncResult(task_id)

    response = {
        'task_id': task_id,
        'status': result.state,
    }

    # Add the result data if the task is complete
    if result.state == 'SUCCESS':
        response['results'] = result.get()
    elif result.state == 'FAILURE':
        response['error'] = str(result.result)

    return Response(response)

