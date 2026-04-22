"""
API client for OpenAI-compatible endpoints.
Handles communication with vision language models for photo analysis.
"""

import json
import requests
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class VisionAPIClient(QObject):
    """
    Client for OpenAI-compatible vision API endpoints.
    
    Supports any OpenAI-compatible endpoint including:
    - OpenAI API (chat.openai.com)
    - Local LLMs (Ollama, LM Studio)
    - Other cloud providers with compatible APIs
    """
    
    # Signals for async operations
    analysis_complete = pyqtSignal(str, list)  # photo_id, results
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int, int)  # current, total
    
    def __init__(self):
        super().__init__()
        self.endpoint_url = ""
        self.api_key = ""
        self.model_name = ""
    
    def configure(self, endpoint: str, api_key: str, model: str):
        """
        Configure the API client with connection details.
        
        Args:
            endpoint: Base URL for the OpenAI-compatible endpoint
            api_key: API key or token for authentication
            model: Model name to use for analysis
        """
        self.endpoint_url = endpoint.rstrip('/')
        self.api_key = api_key
        self.model_name = model
    
    def check_connection(self) -> tuple[bool, str]:
        """
        Test connection to the API endpoint.
        
        Returns (success, error_message).
        """
        try:
            # Try a simple health check or model listing
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            # Check if this is an OpenAI-style endpoint
            response = requests.get(
                f"{self.endpoint_url}/models",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                model_names = [m.get("id") for m in models]
                return True, f"Connected. Available models: {', '.join(model_names[:5])}"
            
            # Try chat completions endpoint
            response = requests.post(
                f"{self.endpoint_url}/chat/completions",
                headers=headers,
                json={"model": self.model_name or "default", "messages": []},
                timeout=5
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
                
            return False, f"Unexpected status code: {response.status_code}"
            
        except requests.exceptions.ConnectionError as e:
            return False, f"Could not connect to endpoint: {str(e)}"
        except requests.exceptions.Timeout:
            return False, "Connection timed out"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def analyze_photo(self, photo_data: bytes, 
                     prompt_template: str = None) -> List[Dict[str, Any]]:
        """
        Analyze a single photo using the vision model.
        
        Args:
            photo_data: Raw image bytes
            prompt_template: Optional custom prompt template
            
        Returns list of analysis results.
        """
        if not self.endpoint_url or not self.api_key:
            raise ValueError("API not configured. Call configure() first.")
        
        # Build the request payload
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a photo analysis assistant. Analyze the image and categorize it.
Return your response as JSON with:
- category: one of 'memories', 'todo', 'research'
- confidence: float between 0 and 1
- tags: list of relevant keywords
- description: brief summary of what's in the photo"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Classify this photo into one of these categories:
- memories: Personal/family photos, important moments, events
- todo: Photos containing tasks, instructions, reminders (recipes, lists, diagrams)
- research: Reference materials, documents, articles

Analyze the content and return your classification in JSON format."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{photo_data.decode('latin1')}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0.3
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.post(
                f"{self.endpoint_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                
                # Try to parse JSON from response
                try:
                    parsed = json.loads(content)
                    return [parsed]
                except json.JSONDecodeError:
                    # If model didn't return clean JSON, return raw content
                    return [{"raw_response": content}]
            else:
                self.error_occurred.emit(f"API error: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(str(e))
            return []
    
    def analyze_batch(self, photo_data_list: List[tuple], 
                     batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze multiple photos.
        
        Args:
            photo_data_list: List of (photo_id, photo_bytes) tuples
            batch_size: Number of concurrent requests
            
        Returns list of results for each photo.
        """
        total = len(photo_data_list)
        results = []
        
        for i in range(0, total, batch_size):
            batch = photo_data_list[i:i + batch_size]
            
            # Update progress
            self.progress_updated.emit(min(i + batch_size, total), total)
            
            for photo_id, photo_data in batch:
                try:
                    result = self.analyze_photo(photo_data)
                    results.append({"photo_id": photo_id, "results": result})
                except Exception as e:
                    results.append({"photo_id": photo_id, "error": str(e)})
        
        return results
