from django.contrib import admin
from .models import StoryGeneration, AudioUpload

@admin.register(StoryGeneration)
class StoryGenerationAdmin(admin.ModelAdmin):
    """
    Admin interface for StoryGeneration model
    """
    list_display = [
        'user_prompt_preview', 
        'generation_status', 
        'has_combined_image', 
        'created_at', 
        'user'
    ]
    
    list_filter = [
        'generation_status', 
        'created_at', 
        'user'
    ]
    
    search_fields = [
        'user_prompt', 
        'story', 
        'character_description'
    ]
    
    readonly_fields = [
        'id', 
        'created_at', 
        'updated_at', 
        'character_image_url', 
        'background_image_url', 
        'combined_image_url'
    ]
    
    fieldsets = (
        ('Input', {
            'fields': ('user_prompt', 'user')
        }),
        ('Generated Content', {
            'fields': ('story', 'character_description')
        }),
        ('Images', {
            'fields': (
                'character_image', 'character_image_url',
                'background_image', 'background_image_url',
                'combined_image', 'combined_image_url'
            )
        }),
        ('Status', {
            'fields': ('generation_status', 'error_message')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_prompt_preview(self, obj):
        """Show truncated prompt in list view"""
        return (obj.user_prompt[:50] + '...') if obj.user_prompt and len(obj.user_prompt) > 50 else obj.user_prompt
    
    user_prompt_preview.short_description = "Prompt"
    
    def has_combined_image(self, obj):
        """Show if combined image exists"""
        return bool(obj.combined_image)
    
    has_combined_image.boolean = True
    has_combined_image.short_description = "Combined Image"

@admin.register(AudioUpload)
class AudioUploadAdmin(admin.ModelAdmin):
    """
    Admin interface for AudioUpload model
    """
    list_display = [
        'audio_file', 
        'transcription_status', 
        'has_story_generation', 
        'created_at'
    ]
    
    list_filter = [
        'transcription_status', 
        'created_at'
    ]
    
    readonly_fields = [
        'id', 
        'created_at'
    ]
    
    def has_story_generation(self, obj):
        """Check if linked to a story generation"""
        return bool(obj.story_generation)
    
    has_story_generation.boolean = True
    has_story_generation.short_description = "Linked to Story"
