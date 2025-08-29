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

def index(request):
    """
    Home page view - displays the story generation form
    """
    if request.method == 'POST':
        form = CombinedStoryForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Process the form and redirect to generation
            return process_story_generation(request, form)
    else:
        form = CombinedStoryForm()
    
    # Show recent story generations (optional)
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
        # Get cleaned data
        user_prompt = form.cleaned_data.get('user_prompt')
        audio_file = form.cleaned_data.get('audio_file')
        
        # Create StoryGeneration instance
        story_generation = StoryGeneration.objects.create(
            user_prompt=user_prompt or "Audio input provided",
            generation_status='processing',
            user=request.user if request.user.is_authenticated else None
        )
        
        # Handle audio upload if provided
        if audio_file and not user_prompt:
            # Create AudioUpload instance
            audio_upload = AudioUpload.objects.create(
                audio_file=audio_file,
                story_generation=story_generation,
                transcription_status='processing'
            )
            
            # In a real implementation, you'd transcribe the audio here
            # For now, we'll use a placeholder
            transcribed_text = "A brave knight discovers a magical forest filled with talking animals."
            audio_upload.transcribed_text = transcribed_text
            audio_upload.transcription_status = 'completed'
            audio_upload.save()
            
            # Update story generation with transcribed text
            story_generation.user_prompt = transcribed_text
            story_generation.save()
        
        # Redirect to generation processing page
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
        # Get story generation instance
        story_generation = get_object_or_404(StoryGeneration, id=generation_id)
        
        # If already completed, redirect to results
        if story_generation.generation_status == 'completed':
            return redirect('story_result', generation_id=generation_id)
        
        # If failed, show error
        if story_generation.generation_status == 'failed':
            return redirect('story_result', generation_id=generation_id)
        
        # Initialize orchestrator service
        orchestrator = StoryOrchestratorService()
        
        # Generate the complete story package
        result = orchestrator.generate_complete_story(story_generation.user_prompt)
        
        # Update the story generation with results
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
        
        # Redirect to results page
        return redirect('story_app:story_result', generation_id=generation_id)

        
    except Exception as e:
        logger.error(f"Story generation process error: {e}")
        
        # Update status to failed
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
        
        return render(request, 'story_app/detail.html', context)
        
    except Http404:
        messages.error(request, "Story not found or not yet completed.")
        return redirect('story_gallery')

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
                'combined_image_url': story_generation.combined_image_url
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

from django.shortcuts import render, get_object_or_404

def story_detail(request, generation_id):  # Changed from story_id to generation_id
    """Display full details of a specific story"""
    story = get_object_or_404(StoryGeneration, id=generation_id)  # Changed from story_id to generation_id
    
    context = {
        'story': story,
        'page_title': 'Story Details'
    }
    
    return render(request, 'story_app/story_detail.html', context)


