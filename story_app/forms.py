from django import forms
from .models import StoryGeneration, AudioUpload

class StoryPromptForm(forms.ModelForm):
    """
    Form for users to input their story prompt
    """
    class Meta:
        model = StoryGeneration
        fields = ['user_prompt']
        
    user_prompt = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter your story prompt here... (e.g., "A brave knight discovers a magical forest")',
            'maxlength': 1000
        }),
        label="Story Prompt",
        help_text="Describe the story you'd like to generate (max 1000 characters)",
        max_length=1000,
        required=True
    )
    
    def clean_user_prompt(self):
        """Custom validation for user prompt"""
        prompt = self.cleaned_data['user_prompt']
        prompt = prompt.strip()
        
        if len(prompt) < 10:
            raise forms.ValidationError("Please provide a more detailed prompt (at least 10 characters).")
        
        return prompt

class AudioUploadForm(forms.ModelForm):
    """
    Form for optional audio upload with speech-to-text
    """
    class Meta:
        model = AudioUpload
        fields = ['audio_file']
        
    audio_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.mp3,.wav,.m4a,.ogg',
            'id': 'audio-upload'
        }),
        label="Audio File (Optional)",
        help_text="Upload an audio file to convert to text (MP3, WAV, M4A, OGG - max 10MB)",
        required=False
    )
    
    def clean_audio_file(self):
        """Validate audio file upload"""
        audio_file = self.cleaned_data.get('audio_file')
        if audio_file:
            if audio_file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Audio file must be smaller than 10MB.")
                
            valid_extensions = ['.mp3', '.wav', '.m4a', '.ogg']
            file_extension = audio_file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in valid_extensions:
                raise forms.ValidationError("Please upload a valid audio file (MP3, WAV, M4A, or OGG).")
                
        return audio_file

class CombinedStoryForm(forms.Form):
    """
    Combined form that handles both text input and optional audio upload
    """
    user_prompt = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter your story prompt here... or record audio below',
            'maxlength': 1000,
            'id': 'prompt-input'
        }),
        label="Story Prompt",
        help_text="Describe the story you'd like to generate",
        max_length=1000,
        required=False
    )
    
    audio_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'audio/*',
            'id': 'audio-input',
            'style': 'display: none;'
        }),
        label="Or Upload Audio File",
        help_text="Upload an audio file to convert to text",
        required=False
    )
    
    def clean(self):
        """Ensure either text prompt or audio file is provided"""
        cleaned_data = super().clean()
        user_prompt = cleaned_data.get('user_prompt')
        audio_file = cleaned_data.get('audio_file')
        
        if not user_prompt and not audio_file:
            raise forms.ValidationError(
                "Please provide either a text prompt or upload an audio file."
            )
        
        return cleaned_data
    
    def clean_user_prompt(self):
        """Validate text prompt"""
        prompt = self.cleaned_data.get('user_prompt')
        if prompt:
            prompt = prompt.strip()
            if len(prompt) < 10:
                raise forms.ValidationError("Please provide a more detailed prompt (at least 10 characters).")
        return prompt
    
    def clean_audio_file(self):
        """Validate audio file"""
        audio_file = self.cleaned_data.get('audio_file')
        if audio_file:
            if audio_file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Audio file must be smaller than 10MB.")
                
            valid_extensions = ['.mp3', '.wav', '.m4a', '.ogg']
            file_extension = audio_file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in valid_extensions:
                raise forms.ValidationError("Please upload a valid audio file format.")
                
        return audio_file
