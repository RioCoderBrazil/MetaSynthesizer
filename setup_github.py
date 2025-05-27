#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
REPO_URL = "https://github.com/RioCoderBrazil/MetaSynthesizer.git"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PROJECT_DIR = Path('/home/gryan/Projects/MetaSynthesizer')

def run_command(command, cwd=PROJECT_DIR):
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

def init_repo():
    """Initialize the git repository"""
    print("\n=== Initializing Git repository ===")
    
    # Check if .git directory already exists
    if (PROJECT_DIR / '.git').exists():
        print(".git directory already exists - repository already initialized")
        return True
    
    return run_command(["git", "init"])

def create_gitignore():
    """Create a .gitignore file"""
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
    with open(PROJECT_DIR / '.gitignore', 'w') as f:
        f.write(gitignore_content)
    return True

def add_remote():
    """Add GitHub remote using token authentication"""
    print("\n=== Adding GitHub remote ===")
    
    # Create the remote URL with token
    token_url = f"https://{GITHUB_TOKEN}@github.com/RioCoderBrazil/MetaSynthesizer.git"
    
    # Check if remote already exists
    result = subprocess.run(["git", "remote", "-v"], cwd=PROJECT_DIR, 
                          capture_output=True, text=True)
    
    if "origin" in result.stdout:
        print("Remote 'origin' already exists, updating...")
        run_command(["git", "remote", "set-url", "origin", token_url])
    else:
        run_command(["git", "remote", "add", "origin", token_url])
    
    return True

def add_and_commit():
    """Add all files and make initial commit"""
    print("\n=== Adding files and making initial commit ===")
    
    # Create a README.md file if it doesn't exist
    if not (PROJECT_DIR / 'README.md').exists():
        with open(PROJECT_DIR / 'README.md', 'w') as f:
            f.write("# MetaSynthesizer\n\nA tool for analyzing documents with color-coded sections.")
    
    run_command(["git", "add", "."])
    run_command(["git", "commit", "-m", "Initial commit with corrected document processing"])
    return True

def push_to_github():
    """Push to GitHub"""
    print("\n=== Pushing to GitHub ===")
    return run_command(["git", "push", "-u", "origin", "main"])

def main():
    """Main function to set up and push to GitHub"""
    print("Setting up GitHub repository for MetaSynthesizer...")
    
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN not found in .env file")
        return False
    
    setup_git_config()
    init_repo()
    create_gitignore()
    add_remote()
    add_and_commit()
    result = push_to_github()
    
    if result:
        print("\n✅ Successfully pushed MetaSynthesizer to GitHub!")
        print(f"Repository URL: {REPO_URL}")
    else:
        print("\n❌ Failed to push to GitHub. Please check the error messages above.")
    
    return result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
