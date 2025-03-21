# django_app/home/utils/github.py
import requests
import base64
from urllib.parse import urlparse


def get_owner_and_repo(url):
    """
    Extract owner and repo from a GitHub URL.
    Handles various GitHub URL formats correctly.
    """
    # Remove trailing slash if present
    url = url.rstrip('/')
    
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip("/").split("/")
    
    if len(path_parts) >= 2:
        owner, repo = path_parts[0], path_parts[1]
        return owner, repo
    return None, None


def fetch_pr_files(repo_url, pr_number, github_token=None):
    """Fetches the files changed in a pull request."""
    owner, repo = get_owner_and_repo(repo_url)
    
    # Safety check
    if not owner or not repo:
        raise ValueError(f"Could not extract owner and repo from URL: {repo_url}")
        
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {github_token}"} if github_token else {}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_file_content(repo_url, file_path, github_token=None):
    """Fetches the raw content of a file from the repository."""
    owner, repo = get_owner_and_repo(repo_url)
    
    # Safety check
    if not owner or not repo:
        raise ValueError(f"Could not extract owner and repo from URL: {repo_url}")
        
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    headers = {"Authorization": f"token {github_token}"} if github_token else {}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    content = response.json()
    return base64.b64decode(content["content"]).decode()