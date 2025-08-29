#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print status"""
    print(f"🔄 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {description} completed")
    except subprocess.CalledProcessError:
        print(f"❌ {description} failed")
        return False
    return True

def main():
    print("🚀 Starting AI Story Generator Setup...")
    
    # Check if .env exists
    if not Path('.env').exists():
        print("⚠️  Please create .env file with your Google API key!")
        print("📝 Copy .env.example and add your API key")
        return
    
    # Setup directories
    if run_command("python setup_directories.py", "Setting up directories"):
        
        # Run migrations
        if run_command("python manage.py makemigrations", "Creating migrations"):
            if run_command("python manage.py migrate", "Applying migrations"):
                
                print("\n🎉 Setup complete! Starting development server...")
                print("🌐 Open: http://localhost:8000")
                print("⭐ Press Ctrl+C to stop the server\n")
                
                # Start server
                subprocess.run("python manage.py runserver", shell=True)

if __name__ == "__main__":
    main()
