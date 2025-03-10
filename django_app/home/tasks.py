# django_app/home/task.py
from celery import Celery
from celery import shared_task
from home.utils.ai_agents import analyze_pull_request

# Set up Celery in Django
app = Celery('django_app')
app.config_from_object('django.conf:settings', namespace='CELERY')

@shared_task
def execute_pr_analysis(repo_url, pr_number, github_token=None):
    """
    Celery task for analyzing a GitHub pull request.
                
    Args:
        repo_url: URL of the GitHub repository
        pr_number: Pull request number to analyze
        github_token: Optional GitHub token for private repositories
        
    Returns:
        Results of the pull request analysis
    """
    print(f"Starting analysis for PR #{pr_number} in {repo_url}")
    result = analyze_pull_request(repo_url, pr_number, github_token)
    print(f"Analysis completed for PR #{pr_number}, found {result.get('results', {}).get('summary', {}).get('total_issues', 0)} issues")
    return result