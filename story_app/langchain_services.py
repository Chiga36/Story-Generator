import os
import logging
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import google.generativeai as genai
from PIL import Image, ImageDraw
import requests
import uuid
import time
import textwrap
import random
from django.conf import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StoryGenerationService:
    """
    LangChain service for generating stories and character descriptions
    using Google's Gemini model
    """
    
    def __init__(self):
        """Initialize the service with Google Gemini API"""
        self.api_key = settings.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in settings")
        
        # Initialize Gemini model through LangChain
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key,
            temperature=0.7,
            max_output_tokens=1000
        )
        
        # Configure Google AI for image generation
        genai.configure(api_key=self.api_key)
        
        # Create story generation chain
        self._setup_story_chain()
        
        # Create character description chain
        self._setup_character_chain()
    
    def _setup_story_chain(self):
        """Setup LangChain for story generation"""
        story_template = """
        You are a creative storyteller. Based on the user's prompt, create an engaging short story.
        
        Requirements:
        - 150-300 words
        - Clear beginning, middle, and end
        - Vivid descriptions
        - Engaging narrative
        - Family-friendly content
        
        User Prompt: {user_prompt}
        
        Story:
        """
        
        self.story_prompt = PromptTemplate(
            input_variables=["user_prompt"],
            template=story_template
        )
        
        # Modern LangChain chaining syntax
        self.story_chain = self.story_prompt | self.llm | StrOutputParser()
    
    def _setup_character_chain(self):
        """Setup LangChain for character description"""
        character_template = """
        Based on the story provided, create a detailed description of the main character.
        
        Requirements:
        - Physical appearance (height, build, hair, eyes, clothing)
        - Personality traits
        - Key characteristics that make them unique
        - 80-150 words
        - Suitable for visual representation
        
        Story: {story}
        
        Character Description:
        """
        
        self.character_prompt = PromptTemplate(
            input_variables=["story"],
            template=character_template
        )
        
        # Modern LangChain chaining syntax
        self.character_chain = self.character_prompt | self.llm | StrOutputParser()

class ImageGenerationService:
    """
    Service for generating images using multiple APIs with enhanced fallbacks
    """
    
    def __init__(self):
        """Initialize image generation service"""
        self.hf_api_key = os.getenv('HUGGINGFACE_API_TOKEN')
        self.base_url = "https://api-inference.huggingface.co/models"
        self.headers = {"Authorization": f"Bearer {self.hf_api_key}"} if self.hf_api_key else {}
    
    def generate_character_image(self, character_description: str) -> Optional[str]:
        """Generate character image with multiple fallbacks"""
        try:
            # Create detailed prompt for character
            prompt = f"portrait of {character_description}, digital art, high quality, detailed character design, fantasy art style"
            
            # Try Hugging Face API first
            result = self._generate_image_huggingface(prompt, "character")
            if result:
                return result
            
            # Try Pollinations AI (free, no token required)
            result = self._generate_image_pollinations(prompt, "character")
            if result:
                return result
            
            # Fallback to enhanced placeholder
            return self._create_enhanced_placeholder(character_description, "character")
            
        except Exception as e:
            logger.error(f"Character image generation failed: {e}")
            return self._create_enhanced_placeholder(character_description, "character")
    
    def generate_background_image(self, story: str) -> Optional[str]:
        """Generate background image with multiple fallbacks"""
        try:
            # Extract and enhance setting description
            setting = self._extract_setting(story)
            prompt = f"{setting}, beautiful landscape, digital art, high quality, detailed environment, fantasy setting"
            
            # Try Hugging Face API first
            result = self._generate_image_huggingface(prompt, "background")
            if result:
                return result
            
            # Try Pollinations AI
            result = self._generate_image_pollinations(prompt, "background")
            if result:
                return result
            
            # Fallback to enhanced placeholder
            return self._create_enhanced_placeholder(setting, "background")
            
        except Exception as e:
            logger.error(f"Background image generation failed: {e}")
            return self._create_enhanced_placeholder("magical landscape", "background")
    
    def _generate_image_huggingface(self, prompt: str, filename_prefix: str) -> Optional[str]:
        """Generate image using Hugging Face API with model fallbacks"""
        if not self.hf_api_key:
            logger.info("No Hugging Face token provided, skipping HF generation")
            return None
        
        # List of models to try (in order of preference)
        models_to_try = [
            "stabilityai/stable-diffusion-2-1",
            "stabilityai/stable-diffusion-2-base",
            "CompVis/stable-diffusion-v1-4",
            "runwayml/stable-diffusion-v1-5"  # This might work again
        ]
        
        for model_name in models_to_try:
            try:
                api_url = f"{self.base_url}/{model_name}"
                
                payload = {
                    "inputs": prompt,
                    "parameters": {
                        "num_inference_steps": 15,
                        "guidance_scale": 7.0,
                        "width": 512,
                        "height": 512
                    }
                }
                
                logger.info(f"Trying Hugging Face model: {model_name}")
                response = requests.post(api_url, headers=self.headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    # Success! Save the image
                    filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
                    filepath = os.path.join(settings.MEDIA_ROOT, 'generated_images', filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"✅ HF image generated with {model_name}: {filename}")
                    return filename
                    
                elif response.status_code == 503:
                    logger.info(f"⏳ Model {model_name} is loading, trying next model...")
                    continue
                    
                else:
                    logger.warning(f"⚠️ Model {model_name} failed with {response.status_code}, trying next...")
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Error with HF model {model_name}: {e}")
                continue
        
        logger.info("All Hugging Face models failed")
        return None
    
    def _generate_image_pollinations(self, prompt: str, filename_prefix: str) -> Optional[str]:
        """Generate image using Pollinations AI (free, no token required)"""
        try:
            import urllib.parse
            
            # Pollinations API endpoint
            encoded_prompt = urllib.parse.quote(prompt)
            api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            
            # Add parameters for better results
            params = {
                'width': 512,
                'height': 512,
                'model': 'flux',
                'seed': random.randint(1, 10000)
            }
            
            logger.info(f"🎨 Generating with Pollinations AI...")
            response = requests.get(api_url, params=params, timeout=60)
            
            if response.status_code == 200:
                filename = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(settings.MEDIA_ROOT, 'generated_images', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✅ Pollinations image saved: {filename}")
                return filename
            else:
                logger.error(f"Pollinations API failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Pollinations generation failed: {e}")
            return None
    
    def _extract_setting(self, story: str) -> str:
        """Extract and enhance setting information from story"""
        setting_keywords = {
            'forest': 'mystical enchanted forest with tall trees and magical lighting',
            'castle': 'majestic medieval castle with towers and battlements',
            'city': 'bustling fantasy city with cobblestone streets',
            'village': 'peaceful medieval village with cottages',
            'mountain': 'towering snow-capped mountains with dramatic peaks',
            'beach': 'serene beach with crystal clear waters and golden sand',
            'space': 'vast cosmic space with stars and nebulae',
            'garden': 'beautiful magical garden with blooming flowers',
            'cave': 'mysterious glowing cave with crystal formations',
            'library': 'ancient magical library with floating books',
            'door': 'magical doorway glowing with mystical energy'
        }
        
        story_lower = story.lower()
        for keyword, description in setting_keywords.items():
            if keyword in story_lower:
                return description
        
        # Default magical setting
        return "magical fantasy landscape with ethereal lighting"
    
    def _create_enhanced_placeholder(self, description: str, filename_prefix: str) -> str:
        """Create a beautiful, professional-looking placeholder"""
        try:
            # Create different sizes for character vs background
            if filename_prefix == "character":
                # Character placeholder - Portrait orientation
                img_size = (400, 600)
                bg_color = '#4A90E2'
                header_color = '#2C5F91'
                icon = "👤"
                title = "🧙‍♂️ CHARACTER"
                subtitle = "AI Generated Description"
            else:
                # Background placeholder - Landscape orientation  
                img_size = (600, 400)
                bg_color = '#27AE60'
                header_color = '#1E8449'
                icon = "🏰"
                title = "🌟 STORY SETTING"
                subtitle = "AI Generated Environment"
            
            # Create image with gradient-like effect
            img = Image.new('RGB', img_size, color=bg_color)
            draw = ImageDraw.Draw(img)
            
            # Add header section
            header_height = 80 if filename_prefix == "character" else 60
            draw.rectangle([0, 0, img_size[0], header_height], fill=header_color)
            
            # Add title and subtitle
            draw.text((20, 15), title, fill='white')
            draw.text((20, 40), subtitle, fill='lightblue' if filename_prefix == "character" else 'lightgreen')
            
            # Add large icon
            icon_y = 100 if filename_prefix == "character" else 120
            icon_x = img_size[0] // 2 - 40
            draw.text((icon_x, icon_y), icon, fill='white')
            
            # Wrap and add description text
            wrapped_text = textwrap.fill(description, width=45)
            lines = wrapped_text.split('\n')
            
            text_start_y = 220 if filename_prefix == "character" else 200
            max_lines = 12 if filename_prefix == "character" else 8
            
            for i, line in enumerate(lines[:max_lines]):
                y_pos = text_start_y + i * 22
                draw.text((20, y_pos), line, fill='white')
            
            # Add decorative footer
            footer_y = img_size[1] - 30
            footer_text = "💫 Powered by AI Story Generator"
            draw.text((20, footer_y), footer_text, fill='lightblue' if filename_prefix == "character" else 'lightgreen')
            
            # Save with unique filename
            filename = f"{filename_prefix}_enhanced_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(settings.MEDIA_ROOT, 'generated_images', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            img.save(filepath)
            
            logger.info(f"✨ Enhanced placeholder created: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Enhanced placeholder creation failed: {e}")
            return self._create_simple_placeholder(filename_prefix, description)
    
    def _create_simple_placeholder(self, filename_prefix: str, description: str) -> str:
        """Ultra-simple fallback placeholder"""
        try:
            img = Image.new('RGB', (400, 400), color='#6C7B7F')
            draw = ImageDraw.Draw(img)
            
            draw.text((20, 20), f"{filename_prefix.upper()}", fill='white')
            draw.text((20, 50), "Generated Content", fill='lightgray')
            
            # Add truncated description
            short_desc = description[:200] + "..." if len(description) > 200 else description
            wrapped = textwrap.fill(short_desc, width=35)
            
            y_offset = 100
            for line in wrapped.split('\n')[:10]:
                draw.text((20, y_offset), line, fill='white')
                y_offset += 20
            
            filename = f"{filename_prefix}_simple_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(settings.MEDIA_ROOT, 'generated_images', filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            img.save(filepath)
            
            return filename
            
        except Exception as e:
            logger.error(f"Simple placeholder failed: {e}")
            return f"error_{uuid.uuid4().hex[:8]}.txt"
    
    def combine_images(self, character_filename: str, background_filename: str) -> Optional[str]:
        """Combine character and background images into a unified scene"""
        try:
            char_path = os.path.join(settings.MEDIA_ROOT, 'generated_images', character_filename)
            bg_path = os.path.join(settings.MEDIA_ROOT, 'generated_images', background_filename)
            
            # Open images
            background = Image.open(bg_path)
            character = Image.open(char_path)
            
            # Resize images to standard size
            bg_size = (800, 600)
            background = background.resize(bg_size)
            
            # Create character overlay (smaller, positioned on right)
            char_width = int(bg_size[0] * 0.3)  # 30% of background width
            char_height = int(character.height * (char_width / character.width))
            character = character.resize((char_width, char_height))
            
            # Create combined image
            combined = background.copy()
            
            # Position character on the right side
            char_x = bg_size[0] - char_width - 20
            char_y = bg_size[1] - char_height - 20
            
            # Paste character onto background
            if character.mode == 'RGBA':
                combined.paste(character, (char_x, char_y), character)
            else:
                combined.paste(character, (char_x, char_y))
            
            # Save combined image
            filename = f"combined_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(settings.MEDIA_ROOT, 'generated_images', filename)
            combined.save(filepath)
            
            logger.info(f"✅ Combined image saved: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Image combination failed: {e}")
            return None

class StoryOrchestratorService:
    """
    Main orchestrator that coordinates story generation, character creation, and image generation
    """
    
    def __init__(self):
        """Initialize all services"""
        self.story_service = StoryGenerationService()
        self.image_service = ImageGenerationService()
    
    def generate_complete_story(self, user_prompt: str) -> Dict[str, Any]:
        """
        Main method that orchestrates the entire story generation process
        
        Args:
            user_prompt: User's input prompt for story generation
            
        Returns:
            Dictionary containing story, character description, and image paths
        """
        try:
            logger.info(f"Starting story generation for prompt: {user_prompt}")
            
            # Step 1: Generate story using modern invoke method
            logger.info("Generating story...")
            story = self.story_service.story_chain.invoke({"user_prompt": user_prompt})
            
            # Step 2: Generate character description using modern invoke method
            logger.info("Generating character description...")
            character_description = self.story_service.character_chain.invoke({"story": story})
            
            # Step 3: Generate character image
            logger.info("Generating character image...")
            character_image = self.image_service.generate_character_image(character_description)
            
            # Step 4: Generate background image
            logger.info("Generating background image...")
            background_image = self.image_service.generate_background_image(story)
            
            # Step 5: Combine images
            combined_image = None
            if character_image and background_image:
                logger.info("Combining images...")
                combined_image = self.image_service.combine_images(character_image, background_image)
            
            result = {
                'story': story,
                'character_description': character_description,
                'character_image': character_image,
                'background_image': background_image,
                'combined_image': combined_image,
                'success': True,
                'error_message': None
            }
            
            logger.info("Story generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            return {
                'story': None,
                'character_description': None,
                'character_image': None,
                'background_image': None,
                'combined_image': None,
                'success': False,
                'error_message': str(e)
            }
