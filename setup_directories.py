import os
from pathlib import Path

def setup_project_directories():
    """Create necessary directories for the project"""
    base_dir = Path(__file__).resolve().parent
    
    directories = [
        'media',
        'media/generated_images',
        'media/audio_uploads',
        'static',
        'staticfiles',
        'story_app/templates',
        'story_app/templates/story_app',
        'story_app/static',
        'story_app/static/story_app',
        'story_app/static/story_app/css',
        'story_app/static/story_app/js',
        'story_app/static/story_app/images'
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    print("✅ All directories created successfully!")

if __name__ == "__main__":
    setup_project_directories()
