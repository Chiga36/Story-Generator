from django.db import models
from django.contrib.auth.models import User
import uuid

class StoryGeneration(models.Model):
    """
    Model to store story generation results and metadata
    """
    # Unique identifier for each generation
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User input
    user_prompt = models.TextField(
        max_length=1000,
        help_text="User's original prompt for story generation"
    )
    
    # Generated content
    story = models.TextField(
        null=True, 
        blank=True,
        help_text="Generated story content"
    )
    
    character_description = models.TextField(
        null=True, 
        blank=True,
        help_text="Generated character description"
    )
    
    # Image file paths (stored as filenames, not full paths)
    character_image = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Filename of generated character image"
    )
    
    background_image = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Filename of generated background image"
    )
    
    combined_image = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text="Filename of final combined scene image"
    )
    
    # Generation metadata
    generation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    error_message = models.TextField(
        null=True, 
        blank=True,
        help_text="Error message if generation failed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Link to user (if you want to track who generated what)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User who created this story (optional)"
    )
    
    class Meta:
        ordering = ['-created_at']  # Most recent first
        verbose_name = "Story Generation"
        verbose_name_plural = "Story Generations"
    
    def __str__(self):
        return f"Story: {self.user_prompt[:50]}..." if self.user_prompt else f"Story {self.id}"
    
    @property
    def character_image_url(self):
        """Return full URL for character image"""
        if self.character_image:
            return f"/media/generated_images/{self.character_image}"
        return None
    
    @property
    def background_image_url(self):
        """Return full URL for background image"""
        if self.background_image:
            return f"/media/generated_images/{self.background_image}"
        return None
    
    @property
    def combined_image_url(self):
        """Return full URL for combined image"""
        if self.combined_image:
            return f"/media/generated_images/{self.combined_image}"
        return None

class AudioUpload(models.Model):
    """
    Model for optional audio file uploads (speech-to-text feature)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Audio file
    audio_file = models.FileField(
        upload_to='audio_uploads/',
        help_text="Uploaded audio file for transcription"
    )
    
    # Transcription results
    transcribed_text = models.TextField(
        null=True, 
        blank=True,
        help_text="Transcribed text from audio"
    )
    
    transcription_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # Link to story generation
    story_generation = models.OneToOneField(
        StoryGeneration,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audio_upload'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Audio: {self.audio_file.name}"
