# AI Story Generator - Django + LangChain

A Django web application that generates stories with characters and images using LangChain and Google's free AI APIs.

## 🚀 Features

- **Text/Audio Input**: Enter prompts or upload audio files
- **AI Story Generation**: Powered by Google Gemini Pro via LangChain
- **Character Descriptions**: Detailed character creation
- **Image Generation**: Character and background images
- **Image Composition**: Combined scene creation
- **Story Gallery**: Browse all generated stories
- **Responsive Design**: Mobile-friendly Bootstrap interface

## 🛠️ Technology Stack

- **Backend**: Django 5.0.7, LangChain 0.2.11
- **AI Services**: Google Gemini Pro, Google Cloud AI
- **Frontend**: Bootstrap 5, JavaScript, HTML5
- **Database**: SQLite (development)
- **Image Processing**: Pillow (PIL)

## 📦 Installation

### 1. Clone and Setup
git clone <your-repo-url>
cd story_generator
pip install -r requirements.txt

### 2. Environment Configuration
Create `.env` file:
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=your_django_secret_key
DEBUG=True
conda activate base
to Run - python manage.py runserver

### 3. Get Google API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

### 4. Setup Directories and Database
python setup_directories.py
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser # Optional

### 5. Run Development Server
python manage.py runserver

Visit: http://localhost:8000

## 📁 Project Structure

story_generator/
├── manage.py
├── requirements.txt
├── README.md
├── .env
├── setup_directories.py
├── story_generator/
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
├── story_app/
│ ├── models.py
│ ├── views.py
│ ├── forms.py
│ ├── urls.py
│ ├── langchain_services.py
│ ├── admin.py
│ └── templates/story_app/
└── media/generated_images/

## 🎯 Usage

1. **Enter Prompt**: Type your story idea
2. **Or Upload Audio**: MP3/WAV file for speech-to-text
3. **Generate**: Click "Generate Story" 
4. **Wait**: Processing takes 30-60 seconds
5. **View Results**: See story, character, and images
6. **Browse Gallery**: View all generated stories

## 🧠 Architecture Overview

### LangChain Services
- **StoryGenerationService**: Text generation via Gemini Pro
- **ImageGenerationService**: Image creation and composition
- **StoryOrchestratorService**: Workflow coordination

### Django Models
- **StoryGeneration**: Stores stories, characters, images
- **AudioUpload**: Handles speech-to-text processing

### API Integration
- **Google Gemini Pro**: Story and character text generation
- **Google Cloud AI**: Image generation services
- **Django ORM**: Database operations and relationships

## 🔧 Key Components

### 1. Story Generation Flow
User Input → LangChain → Gemini Pro → Story Text
Story Text → Character Description → Images → Combined Scene

### 2. Image Processing
- Character image generation
- Background scene creation
- PIL-based image composition
- File management and serving

### 3. Web Interface
- Bootstrap responsive design
- AJAX status polling
- Form validation
- Error handling

## 🎥 Video Explanation Topics

When recording your video explanation, cover:

1. **Project Overview** (2 min)
   - What it does and key features
   - Technology stack explanation

2. **Code Architecture** (5 min)
   - Django app structure
   - LangChain service classes
   - Model relationships
   - View function logic

3. **LangChain Integration** (3 min)
   - Google Gemini Pro setup
   - Prompt engineering
   - Chain creation and execution

4. **Frontend & UX** (2 min)
   - Template inheritance
   - Form handling
   - Image display
   - Status polling

5. **Demo** (3 min)
   - Live story generation
   - Show generated results
   - Gallery walkthrough

## 🚨 Troubleshooting

**API Key Issues:**
- Ensure GOOGLE_API_KEY is set in .env
- Check API key permissions in Google Cloud Console

**Image Generation:**
- Currently using placeholder images for free tier
- Can integrate with Stable Diffusion or other free APIs

**Database Errors:**
- Run `python manage.py migrate`
- Check file permissions for db.sqlite3

## 📊 Quiz Preparation

Be ready to explain:
- LangChain chain composition
- Django MVC architecture
- Google API integration
- Image processing workflow
- Database model relationships
- Template inheritance system
- AJAX implementation
- Error handling strategies

## 🎯 Submission Checklist

- ✅ All code files included
- ✅ requirements.txt complete
- ✅ README.md documentation
- ✅ .env.example file
- ✅ Database migrations
- ✅ Working demo screenshots
- ✅ Video explanation recorded
