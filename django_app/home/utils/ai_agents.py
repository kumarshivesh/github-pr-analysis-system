# django_app/home/utils/ai_agents.py
import uuid
from groq import Groq
import os
import sys
from .github import fetch_pr_files, fetch_file_content
from .prompts import code_analysis_prompt
import json

# Get API key from environment variable
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

def analyze_file_with_llm(file_content, file_name):
    """
    Analyzes code file content using the Groq LLM API to identify issues.
    
    Args:
        file_content: The content of the file to analyze
        file_name: The name of the file being analyzed
        
    Returns:
        JSON formatted analysis of the code with identified issues
    """
    prompt = f"""
    Analyze the following code for:
    - Code style and formatting issues
    - Potential bugs or errors
    - Performance improvements
    - Best practices

    File: {file_name}
    Content: {file_content}

    Provide a detailed JSON output with the structure:
    {{
        "issues": [
            {{
                "type": "<style|bug|performance|best_practice>",
                "line": <line_number>,
                "description": "<description>",
                "suggestion": "<suggestion>"
            }}
        ]
    }}
    ``json
    """

    client = Groq(
        api_key=GROQ_API_KEY
    )
    
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {'role': 'system', 'content': code_analysis_prompt},
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,  # Lower temperature for more deterministic outputs
            top_p=1,
            response_format={
                "type": "json_object"
            }
        )
        
        print(f"Analysis completed for {file_name}")
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error analyzing file {file_name}: {str(e)}")
        return json.dumps({"issues": []})


def analyze_pull_request(repo_url, pr_number, github_token=None):
    """
    Analyzes all files in a pull request to identify code issues.
    
    Args:
        repo_url: URL of the GitHub repository
        pr_number: Pull request number to analyze
        github_token: Optional GitHub token for private repositories
        
    Returns:
        Analysis results for the entire pull request
    """
    task_id = str(uuid.uuid4())
    try:
        pr_files = fetch_pr_files(repo_url, pr_number, github_token)

        analysis_results = {
            "files": [], 
            "summary": {
                "total_files": 0, 
                "total_issues": 0, 
                "critical_issues": 0
            }
        }

        for file in pr_files:
            file_name = file["filename"]
            
            # Skip binary files, images, etc.
            if file_name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip')):
                continue
                
            raw_content = fetch_file_content(repo_url, file_name, github_token)

            # Analyze with LLM
            analysis_result = analyze_file_with_llm(raw_content, file_name)

            try:
                analysis_data = json.loads(analysis_result)
            except json.JSONDecodeError as e:
                return {
                    "task_id": task_id, 
                    "status": "error", 
                    "message": f"JSON decode error for {file_name}: {str(e)}"
                }

            total_issues = len(analysis_data["issues"])
            critical_issues = sum(1 for issue in analysis_data["issues"] if issue["type"] == "bug")

            analysis_results["files"].append({
                "name": file_name, 
                "issues": analysis_data["issues"]
            })

            analysis_results["summary"]["total_files"] += 1
            analysis_results["summary"]["total_issues"] += total_issues
            analysis_results["summary"]["critical_issues"] += critical_issues

        return {
            "task_id": task_id, 
            "status": "completed", 
            "results": analysis_results
        }
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        error_details = f"Error in {fname} line {exc_tb.tb_lineno}: {str(e)}"
        print(error_details)
        return {
            "task_id": task_id, 
            "status": "error", 
            "message": error_details
        }