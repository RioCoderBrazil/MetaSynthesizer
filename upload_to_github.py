#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and print output"""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    
    if result.stdout:
        print(f"Output: {result.stdout}")
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def setup_git_config():
    """Setup basic git configuration"""
    print("\n=== Setting up Git configuration ===")
    run_command(["git", "config", "--global", "user.name", "RioCoderBrazil"])
    run_command(["git", "config", "--global", "user.email", "riocoder@example.com"])
    return True

def create_gitignore():
    """Create a .gitignore file to exclude sensitive data"""
    print("\n=== Creating .gitignore file ===")
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env

# Large data files (if needed)
*.zip
*.tar.gz

# Virtual environment
venv/
ENV/

# IDE specific files
.idea/
.vscode/
*.swp
*.swo

# OS specific files
.DS_Store
Thumbs.db
"""
    with open(".gitignore", 'w') as f:
        f.write(gitignore_content)
    return True

def setup_and_push():
    """Main function to set up git and push to GitHub"""
    # Repository information
    repo_url = "https://github.com/RioCoderBrazil/MetaSynthesizer.git"
    
    # Set up git configuration
    setup_git_config()
    
    # Create .gitignore file
    create_gitignore()
    
    # Initialize git repository if not already initialized
    if not os.path.exists(".git"):
        print("\n=== Initializing Git repository ===")
        if not run_command(["git", "init"]):
            return False
    
    # Create README.md if it doesn't exist
    if not os.path.exists("README.md"):
        print("\n=== Creating README.md ===")
        with open("README.md", 'w') as f:
            f.write("# MetaSynthesizer\n\n")
            f.write("A tool for analyzing colored sections in audit reports.\n\n")
            f.write("## Project Structure\n\n")
            f.write("- `01_colored_reports/`: Original highlighted documents\n")
            f.write("- `02_chunked_data_CORRECTED/`: Extracted text chunks with proper labels\n")
            f.write("- `03_extracted_data/`: Further processed data\n")
            f.write("- `04_html_reports_correct/`: HTML reports for visualization\n")
            f.write("- `05_visualizations/`: Data visualizations\n")
    
    # Add all files
    print("\n=== Adding files to git ===")
    if not run_command(["git", "add", "."]):
        return False
    
    # Commit changes
    print("\n=== Committing changes ===")
    if not run_command(["git", "commit", "-m", "Initial commit of MetaSynthesizer project"]):
        return False
    
    # Add remote repository
    print("\n=== Adding remote repository ===")
    run_command(["git", "remote", "rm", "origin"])  # Remove if exists
    if not run_command(["git", "remote", "add", "origin", repo_url]):
        return False
    
    # Push to GitHub
    print("\n=== Pushing to GitHub ===")
    if not run_command(["git", "push", "-u", "origin", "master", "--force"]):
        # Try main branch if master fails
        if not run_command(["git", "push", "-u", "origin", "main", "--force"]):
            return False
    
    print("\n✅ Successfully pushed to GitHub!")
    print(f"Repository URL: {repo_url}")
    return True

if __name__ == "__main__":
    # Change to project directory
    os.chdir("/home/gryan/Projects/MetaSynthesizer")
    success = setup_and_push()
    sys.exit(0 if success else 1)
