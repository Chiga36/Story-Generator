import os
import logging
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import google.generativeai as genai
from PIL import Image
import requests
import uuid
import time
import textwrap
import random
from django.conf import settings
from io import BytesIO
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoryGenerationService:
    """
    LangChain service for generating stories and character descriptions.
    """
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in settings")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key,
            temperature=0.7,
            max_output_tokens=1000
        )
        self._setup_chains()

    def _setup_chains(self):
        story_template = """
        You are a master storyteller. From the user's prompt, create an imaginative and family-friendly short story (150-300 words).
        User Prompt: {user_prompt}
        Story:
        """
        self.story_prompt = PromptTemplate(template=story_template, input_variables=["user_prompt"])
        self.story_chain = self.story_prompt | self.llm | StrOutputParser()

        character_template = """
        Based on the story, describe the main character's appearance and personality in 80-150 words.
        Story: {story}
        Character Description:
        """
        self.character_prompt = PromptTemplate(template=character_template, input_variables=["story"])
        self.character_chain = self.character_prompt | self.llm | StrOutputParser()

class ImageGenerationService:
    """
    Service for generating three separate images: Character, Background, and a cohesive Story Scene.
    All images are generated using the reliable Pollinations.ai API.
    """
    def _generate_image_via_pollinations(self, prompt: str, prefix: str, width: int = 1024, height: int = 768) -> Optional[str]:
        """
        Generates a single image using the Pollinations.ai API.
        """
        try:
            # Enhance the prompt with artistic keywords for better results
            enhanced_prompt = f"{prompt}, beautiful digital art, cinematic lighting, fantasy illustration, high detail"
            encoded_prompt = urllib.parse.quote(enhanced_prompt)
            api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            
            params = {
                'width': width,
                'height': height,
                'model': 'flux',
                'seed': random.randint(1, 10000)
            }
            
            logger.info(f"🎨 Generating {prefix} image with Pollinations AI (Prompt: {prompt})...")
            response = requests.get(api_url, params=params, timeout=90)
            
            if response.status_code == 200:
                filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(settings.MEDIA_ROOT, 'generated_images', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✅ {prefix.capitalize()} image saved: {filename}")
                return filename
            else:
                logger.error(f"Pollinations API failed for {prefix} with status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Pollinations.ai image generation for {prefix} failed: {e}")
            return None

    def generate_character_image(self, character_description: str) -> Optional[str]:
        """Generates a portrait of the character."""
        prompt = f"portrait of {character_description}, detailed character design, beautiful lighting"
        return self._generate_image_via_pollinations(prompt, "character", width=800, height=1024)

    def generate_background_image(self, story: str) -> Optional[str]:
        """Generates the background landscape."""
        setting = self._extract_setting(story)
        prompt = f"{setting}, beautiful landscape, detailed environment, no characters"
        return self._generate_image_via_pollinations(prompt, "background")

    def generate_story_scene_image(self, user_prompt: str) -> Optional[str]:
        """Generates the final, cohesive story scene directly from the user's prompt."""
        return self._generate_image_via_pollinations(user_prompt, "story_scene")

    def _extract_setting(self, story: str) -> str:
        """Extracts the setting from the story for the background prompt."""
        story_lower = story.lower()
        keywords = {
            'forest': 'a mystical enchanted forest', 'castle': 'a majestic medieval castle',
            'garden': 'a beautiful magical garden with a glowing door', 'cave': 'a mysterious glowing cave',
            'mountain': 'towering snow-capped mountains', 'beach': 'a serene beach with golden sand',
            'city': 'a bustling fantasy city', 'space': 'vast cosmic space with stars and nebulae'
        }
        for keyword, setting in keywords.items():
            if keyword in story_lower:
                return setting
        return "a magical fantasy landscape"

class StoryOrchestratorService:
    """
    Main orchestrator that coordinates the full story generation process.
    """
    def __init__(self):
        self.story_service = StoryGenerationService()
        self.image_service = ImageGenerationService()
    
    def generate_complete_story(self, user_prompt: str) -> Dict[str, Any]:
        try:
            logger.info(f"Starting final workflow for prompt: {user_prompt}")
            
            # Generate story and character description text
            story = self.story_service.story_chain.invoke({"user_prompt": user_prompt})
            character_description = self.story_service.character_chain.invoke({"story": story})
            
            # --- IMAGE GENERATION ---
            # 1. Generate the Character portrait
            character_image = self.image_service.generate_character_image(character_description)
            
            # 2. Generate the Background landscape
            background_image = self.image_service.generate_background_image(story)
            
            # 3. Generate the cohesive Story Scene from the original prompt
            story_scene_image = self.image_service.generate_story_scene_image(user_prompt)
            
            result = {
                'story': story,
                'character_description': character_description,
                'character_image': character_image,
                'background_image': background_image,
                'combined_image': story_scene_image, # This now holds the cohesive scene
                'success': True,
                'error_message': None
            }
            
            logger.info("Final workflow completed successfully!")
            return result
            
        except Exception as e:
            logger.error(f"Full story generation failed: {e}")
            return {'success': False, 'error_message': str(e)}

