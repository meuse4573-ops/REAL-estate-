"""
GLM 5.1 Model Client Wrapper.
Handles all interactions with the GLM 5.1 API for document extraction,
sentiment analysis, email drafting, and more.
"""
from openai import OpenAI
from typing import Optional, Dict, Any
import base64
from core.config import settings


class GLMClient:
    """Client for interacting with GLM 5.1 model."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.GLM_API_KEY,
            base_url=settings.GLM_BASE_URL,
        )
        self.model = settings.GLM_MODEL
    
    async def chat(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> str:
        """
        Send a chat request to GLM 5.1.
        
        Args:
            prompt: User prompt/message
            system: Optional system prompt
            max_tokens: Max tokens in response
            temperature: Sampling temperature
            
        Returns:
            Model's text response
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"GLM API error: {str(e)}")
    
    async def chat_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Send a chat request and parse response as JSON.
        
        Args:
            prompt: User prompt
            system: Optional system prompt
            max_tokens: Max tokens in response
            
        Returns:
            Parsed JSON response
        """
        import json
        
        full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON, no other text."
        
        response = await self.chat(
            prompt=full_prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON response from GLM: {response[:200]}")
    
    async def vision_extract(
        self,
        image_path: str,
        prompt: str,
        max_tokens: int = 4096
    ) -> str:
        """
        Use GLM's vision capabilities for image/PDF extraction.
        
        Args:
            image_path: Path to image file
            prompt: Extraction prompt
            max_tokens: Max tokens in response
            
        Returns:
            Extracted text
        """
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    }
                ]
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"GLM Vision API error: {str(e)}")


glm_client = GLMClient()