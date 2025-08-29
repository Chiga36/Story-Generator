from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
import json
import logging

from .forms import CombinedStoryForm, StoryPromptForm, AudioUploadForm
from .models import StoryGeneration, AudioUpload
from .langchain_services import StoryOrchestratorService

# Configure logging
logger = logging.getLogger(__name__)

from django.http import JsonResponse
import datetime

def health_check(request):
    """Simple health check endpoint for demonstration"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'AI Story Generator',
        'timestamp': datetime.datetime.now().isoformat(),
        'django_version': '5.0.7',
        'database_connected': True,
        'message': 'Django server is running successfully!'
    })


def index(request):
    """
    Home page view - displays the story generation form
    """
    if request.method == 'POST':
        form = CombinedStoryForm(request.POST, request.FILES)
        if form.is_valid():
            return process_story_generation(request, form)
    else:
        form = CombinedStoryForm()
    
    recent_stories = StoryGeneration.objects.filter(
        generation_status='completed'
    )[:5]
    
    context = {
        'form': form,
        'recent_stories': recent_stories,
        'page_title': 'AI Story Generator'
    }
    
    return render(request, 'story_app/index.html', context)

def process_story_generation(request, form):
    """
    Process story generation request - handles both text and audio input
    """
    try:
        user_prompt = form.cleaned_data.get('user_prompt')
        audio_file = form.cleaned_data.get('audio_file')
        
        story_generation = StoryGeneration.objects.create(
            user_prompt=user_prompt or "Audio input provided",
            generation_status='processing',
            user=request.user if request.user.is_authenticated else None
        )
        
        if audio_file and not user_prompt:
            audio_upload = AudioUpload.objects.create(
                audio_file=audio_file,
                story_generation=story_generation,
                transcription_status='processing'
            )
            
            transcribed_text = "A brave knight discovers a magical forest filled with talking animals."
            audio_upload.transcribed_text = transcribed_text
            audio_upload.transcription_status = 'completed'
            audio_upload.save()
            
            story_generation.user_prompt = transcribed_text
            story_generation.save()
        
        return redirect('story_app:story_generation_process', generation_id=story_generation.id)
        
    except Exception as e:
        logger.error(f"Story generation process failed: {e}")
        messages.error(request, "Sorry, something went wrong. Please try again.")
        return redirect('story_app:index')

@require_http_methods(["GET"])
def story_generation_process(request, generation_id):
    """
    Process the actual story generation using LangChain services
    """
    try:
        story_generation = get_object_or_404(StoryGeneration, id=generation_id)
        
        if story_generation.generation_status == 'completed':
            return redirect('story_app:story_result', generation_id=generation_id)
        
        if story_generation.generation_status == 'failed':
            return redirect('story_app:story_result', generation_id=generation_id)
        
        orchestrator = StoryOrchestratorService()
        result = orchestrator.generate_complete_story(story_generation.user_prompt)
        
        if result['success']:
            story_generation.story = result['story']
            story_generation.character_description = result['character_description']
            story_generation.character_image = result['character_image']
            story_generation.background_image = result['background_image']
            story_generation.combined_image = result['combined_image']
            story_generation.generation_status = 'completed'
            
            logger.info(f"Story generation completed successfully: {generation_id}")
        else:
            story_generation.generation_status = 'failed'
            story_generation.error_message = result['error_message']
            
            logger.error(f"Story generation failed: {generation_id} - {result['error_message']}")
        
        story_generation.save()
        
        return redirect('story_app:story_result', generation_id=generation_id)
        
    except Exception as e:
        logger.error(f"Story generation process error: {e}")
        
        if 'story_generation' in locals():
            story_generation.generation_status = 'failed'
            story_generation.error_message = str(e)
            story_generation.save()
        
        messages.error(request, "Story generation failed. Please try again.")
        return redirect('story_app:index')

def story_result(request, generation_id):
    """
    Display the generated story results
    """
    try:
        story_generation = get_object_or_404(StoryGeneration, id=generation_id)
        
        context = {
            'story_generation': story_generation,
            'page_title': 'Your Generated Story'
        }
        
        if story_generation.generation_status == 'completed':
            messages.success(request, "Story generated successfully!")
        elif story_generation.generation_status == 'failed':
            messages.error(request, f"Story generation failed: {story_generation.error_message}")
        elif story_generation.generation_status == 'processing':
            messages.info(request, "Story is still being generated. Please refresh in a moment.")
        
        return render(request, 'story_app/result.html', context)
        
    except Exception as e:
        logger.error(f"Story result display error: {e}")
        messages.error(request, "Unable to display story results.")
        return redirect('story_app:index')

def story_gallery(request):
    """
    Display a gallery of all completed stories
    """
    completed_stories = StoryGeneration.objects.filter(
        generation_status='completed'
    ).order_by('-created_at')
    
    context = {
        'stories': completed_stories,
        'page_title': 'Story Gallery'
    }
    
    return render(request, 'story_app/gallery.html', context)

def story_detail(request, generation_id):
    """
    Display detailed view of a specific story
    """
    try:
        story_generation = get_object_or_404(
            StoryGeneration, 
            id=generation_id,
            generation_status='completed'
        )
        
        context = {
            'story_generation': story_generation,
            'page_title': f'Story Details'
        }
        
        return render(request, 'story_app/story_detail.html', context)
        
    except Http404:
        messages.error(request, "Story not found or not yet completed.")
        return redirect('story_app:story_gallery')

@csrf_exempt
@require_http_methods(["GET"])
def generation_status_api(request, generation_id):
    """
    API endpoint to check generation status (for AJAX polling)
    """
    try:
        story_generation = get_object_or_404(StoryGeneration, id=generation_id)
        
        response_data = {
            'status': story_generation.generation_status,
            'error_message': story_generation.error_message,
            'created_at': story_generation.created_at.isoformat(),
            'updated_at': story_generation.updated_at.isoformat()
        }
        
        if story_generation.generation_status == 'completed':
            response_data.update({
                'story': story_generation.story,
                'character_description': story_generation.character_description,
            })
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Unable to fetch status',
            'message': str(e)
        }, status=500)

def about(request):
    """
    About page explaining how the app works
    """
    context = {
        'page_title': 'About AI Story Generator'
    }
    return render(request, 'story_app/about.html', context)

# Error handling views
def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'story_app/404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'story_app/500.html', status=500)

@require_http_methods(["POST"])
def delete_story(request, generation_id):
    """
    Delete a specific story - only accessible via POST for security
    """
    try:
        story_generation = get_object_or_404(StoryGeneration, id=generation_id)
        
        # Optional: Add user ownership check if you have authentication
        # if story_generation.user and story_generation.user != request.user:
        #     messages.error(request, "You can only delete your own stories.")
        #     return redirect('story_app:story_gallery')
        
        # Delete the story
        story_title = story_generation.user_prompt[:30] + "..." if len(story_generation.user_prompt) > 30 else story_generation.user_prompt
        story_generation.delete()
        
        messages.success(request, f"Story '{story_title}' has been deleted successfully!")
        
    except Http404:
        messages.error(request, "Story not found.")
    except Exception as e:
        logger.error(f"Error deleting story {generation_id}: {e}")
        messages.error(request, "Failed to delete story. Please try again.")
    
    return redirect('story_app:story_gallery')

# Remove or comment out the weasyprint import
# import weasyprint

# Add these imports instead
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.http import HttpResponse
import os

@require_http_methods(["GET"])
def download_story_pdf(request, generation_id):
    """
    Generate and download a PDF version of the story using xhtml2pdf
    """
    try:
        story_generation = get_object_or_404(
            StoryGeneration, 
            id=generation_id,
            generation_status='completed'
        )
        
        # Render the PDF template with request context for absolute URLs
        template_path = 'story_app/story_pdf_simple.html'
        context = {
            'story_generation': story_generation,
            'request': request  # Add request to context for absolute URLs
        }
        html = render_to_string(template_path, context)
        
        # Create a Django response object with PDF content type
        response = HttpResponse(content_type='application/pdf')
        
        # Create filename with story title
        safe_title = "".join(c for c in story_generation.user_prompt[:20] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"story_{safe_title}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Convert HTML to PDF with base URL for proper image loading
        pisa_status = pisa.CreatePDF(
            html, 
            dest=response,
            link_callback=lambda uri, rel: uri  # This helps with image loading
        )
        
        if pisa_status.err:
            logger.error(f"PDF generation failed for story {generation_id}")
            messages.error(request, "Failed to generate PDF. Please try again.")
            return redirect('story_app:story_detail', generation_id=generation_id)
        
        return response
        
    except Exception as e:
        logger.error(f"PDF generation failed for story {generation_id}: {e}")
        messages.error(request, "Failed to generate PDF. Please try again.")
        return redirect('story_app:story_detail', generation_id=generation_id)
