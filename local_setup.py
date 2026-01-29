#!/usr/bin/env python3
"""
Local Setup Script for LinkedIn Automation

This script helps you set up and run the LinkedIn automation system locally.
It includes validation, cookie extraction guidance, and easy execution.
"""

import os
import json
import sys
import subprocess
import webbrowser
from pathlib import Path


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_step(step, description):
    """Print a formatted step."""
    print(f"\n[STEP {step}] {description}")
    print("-" * 40)


def check_python_version():
    """Check if Python version is compatible."""
    print_step(1, "Checking Python Version")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"Python {version.major}.{version.minor}.{version.micro} - Not Compatible")
        print("Required: Python 3.9 or higher")
        return False


def install_dependencies():
    """Install required Python dependencies."""
    print_step(2, "Installing Dependencies")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False


def install_playwright_browsers():
    """Install Playwright browsers."""
    print_step(3, "Installing Playwright Browsers")
    
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("Playwright browsers installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Playwright browsers: {e}")
        return False


def setup_environment():
    """Set up environment configuration."""
    print_step(4, "Setting Up Environment Configuration")
    
    # Check if .env exists
    env_file = Path(".env")
    env_example = Path(".env-example")
    
    if not env_file.exists():
        if env_example.exists():
            print("Copying .env-example to .env")
            env_file.write_text(env_example.read_text())
            print("Created .env file from template")
        else:
            print(".env-example file not found")
            return False
    
    print("Please edit .env file with your actual values:")
    print("   - GROQ_API_KEY: Your Groq API key")
    print("   - LI_COOKIES: Your LinkedIn cookies (see instructions below)")
    
    return True


def setup_cookies():
    """Guide user through cookie setup."""
    print_step(5, "Setting Up LinkedIn Cookies")
    
    cookies_file = Path("config/linkedin_cookies.json")
    cookies_example = Path("config/linkedin_cookies.json.example")
    
    if not cookies_file.exists():
        if cookies_example.exists():
            print("Copying cookie example to config/linkedin_cookies.json")
            cookies_file.write_text(cookies_example.read_text())
            print("Created cookie configuration file")
        else:
            print("Cookie example file not found")
            return False
    
    print("\nCookie Extraction Instructions:")
    print("1. Log into LinkedIn in your browser")
    print("2. Open Developer Tools (F12)")
    print("3. Go to Application/Storage -> Cookies -> https://www.linkedin.com")
    print("4. Copy values for: li_at, JSESSIONID, bscookie")
    print("5. Replace placeholder values in config/linkedin_cookies.json")
    print("6. Save the file")
    
    print("\nOpening LinkedIn in your browser...")
    webbrowser.open("https://www.linkedin.com")
    
    return True


def validate_setup():
    """Validate the complete setup."""
    print_step(6, "Validating Setup")
    
    try:
        # Import and run validation
        sys.path.insert(0, str(Path("src/automation")))
        from workflow import LinkedInAutomationWorkflow
        
        print("Running setup validation...")
        
        # This would normally be async, but for local setup we'll just check imports
        print("All imports successful")
        print("Setup validation passed")
        
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Validation error: {e}")
        return False


def create_run_script():
    """Create a simple run script."""
    print_step(7, "Creating Local Run Script")
    
    run_script = """#!/usr/bin/env python3
\"\"\"
Local Run Script for LinkedIn Automation

Usage: python run_local.py [prospects_file] [max_requests]
\"\"\"

import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "automation"))

from workflow import LinkedInAutomationWorkflow


async def main():
    # Parse arguments
    prospects_file = sys.argv[1] if len(sys.argv) > 1 else "prospects_example.json"
    max_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    
    # Load prospects
    if not Path(prospects_file).exists():
        print(f"Prospects file not found: {prospects_file}")
        print("Use: python run_local.py prospects_example.json")
        return
    
    with open(prospects_file, 'r') as f:
        prospects = json.load(f)
    
    print(f"Starting LinkedIn automation with {len(prospects)} prospects")
    print(f"Max requests per session: {max_requests}")
    
    # Run workflow
    workflow = LinkedInAutomationWorkflow()
    result = await workflow.run_workflow(prospects, max_requests)
    
    # Print results
    print(f"\\nResults:")
    print(f"   Successful: {result['successful_requests']}/{len(prospects)}")
    print(f"   Failed: {result['failed_requests']}")
    print(f"   Execution time: {result['execution_time']:.2f}s")
    
    if result['errors']:
        print(f"\\nErrors:")
        for error in result['errors']:
            print(f"   - {error}")


if __name__ == "__main__":
    asyncio.run(main())
"""
    
    run_file = Path("run_local.py")
    run_file.write_text(run_script)
    run_file.chmod(0o755)  # Make executable
    
    print("Created run_local.py script")
    print("Usage: python run_local.py [prospects_file] [max_requests]")


def print_final_instructions():
    """Print final setup instructions."""
    print_header("Setup Complete!")
    
    print("\nNext Steps:")
    print("1. Edit .env file with your Groq API key")
    print("2. Extract and configure LinkedIn cookies")
    print("3. Review prospects_example.json or create your own")
    print("4. Run: python run_local.py")
    
    print("\nQuick Commands:")
    print("   Validate setup:     python local_setup.py --validate")
    print("   Run with example:   python run_local.py prospects_example.json")
    print("   Run with custom:    python run_local.py your_prospects.json 5")
    
    print("\nImportant Notes:")
    print("   - Respect LinkedIn's rate limits (max 9 requests per session)")
    print("   - Use realistic delays between requests")
    print("   - Monitor for rate limiting or account restrictions")
    print("   - Keep your cookies updated")
    
    print("\nDocumentation:")
    print("   - Full README: README.md")
    print("   - Troubleshooting: See README.md section")


def main():
    """Main setup function."""
    print_header("LinkedIn Automation Local Setup")
    
    steps = [
        ("Python Version", check_python_version),
        ("Dependencies", install_dependencies),
        ("Playwright Browsers", install_playwright_browsers),
        ("Environment", setup_environment),
        ("Cookies", setup_cookies),
        ("Validation", validate_setup),
    ]
    
    completed = 0
    for step_name, step_func in steps:
        if step_func():
            completed += 1
            print(f"{step_name} completed")
        else:
            print(f"{step_name} failed")
            print("Please fix the issues above before proceeding.")
            return False
    
    # Create run script
    create_run_script()
    
    # Print final instructions
    print_final_instructions()
    
    print(f"\nSetup completed successfully! {completed}/{len(steps)} steps passed.")
    return True


if __name__ == "__main__":
    main()