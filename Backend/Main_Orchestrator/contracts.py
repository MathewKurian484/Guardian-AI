def legal_analyst_tool(pdf_file_path: str, question: str) -> str:
    return """Technical Brief:
    - All image elements must have valid alt attributes
    - User data must be encrypted during transmission
    - Password fields must implement minimum strength requirements
    - CSRF tokens must be present in all forms
    - API endpoints must implement rate limiting"""

def code_auditor_agent(repo_url: str, technical_brief: str) -> str:
    import json
    mock_violations = [
        {
            "file": "frontend/components/ImageGallery.js",
            "line": 15,
            "violating_code": "<img src='/logo.png' />",
            "explanation": "Image element missing alt attribute for accessibility",
            "rule_violated": "All image elements must have valid alt attributes"
        },
        {
            "file": "backend/auth.py",
            "line": 45,
            "violating_code": "password = request.form['password']",
            "explanation": "No password strength validation implemented",
            "rule_violated": "Password fields must implement minimum strength requirements"
        }
    ]
    return json.dumps(mock_violations, indent=2)