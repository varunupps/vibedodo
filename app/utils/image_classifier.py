import os
import base64
import requests
import json
import traceback
from PIL import Image
from io import BytesIO

class ImageClassifier:
    """Utility class to classify images using Claude API"""
    
    # List of model IDs to try (in order)
    CLAUDE_MODELS = [
        "claude-3-5-sonnet-20241022",  # Use the specified model first
        "claude-3-sonnet-20240229",
        "claude-3-sonnet",
        "claude-3-5-sonnet-20240620",
        "claude-3-haiku-20240307",
        "claude-3-haiku",
        "claude-3-opus-20240229",
        "claude-3-opus"
    ]
    
    @staticmethod
    def classify_image(image_path, api_key=None):
        """
        Classifies an image as GAMING or OTHER using Claude models
        
        Args:
            image_path: Path to the image file
            api_key: Claude API key (default: environment variable)
            
        Returns:
            tuple: (classification, is_mock)
                classification: "GAMING" or "OTHER"
                is_mock: True if mock classifier was used, False otherwise
        """
        try:
            # Use environment variable if no API key provided
            if not api_key:
                api_key = os.environ.get('CLAUDE_API_KEY')
                
            if not api_key:
                print("No Claude API key provided. Using mock classification.")
                classification = ImageClassifier.mock_classify(image_path)
                return classification, True  # True indicates mock classifier was used
            
            # Load and encode the image
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                base64_image = base64.b64encode(img_data).decode('utf-8')
            
            print(f"Using API key ending with: ...{api_key[-4:]}")
            
            # Claude API endpoint
            url = "https://api.anthropic.com/v1/messages"
            
            # Request headers
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            # Text prompt for classification
            prompt_text = ("Classify this image as either 'GAMING' or 'OTHER'. \n\n"
                          "GAMING category includes:\n"
                          "- Screenshots from any video game\n"
                          "- Gaming hardware like controllers, consoles, PCs\n"
                          "- Game characters or avatars\n"
                          "- Gaming merchandise or accessories\n"
                          "- Esports or gaming events\n"
                          "- Gaming memes or streamer content\n\n"
                          "All other images should be classified as 'OTHER'.\n\n"
                          "Respond with just one word: either 'GAMING' or 'OTHER'.")
            
            # Try each model in succession until one works
            for model_name in ImageClassifier.CLAUDE_MODELS:
                try:
                    print(f"Trying model: {model_name}")
                    
                    # Request payload
                    payload = {
                        "model": model_name,
                        "max_tokens": 100,
                        "temperature": 0,  # Use deterministic responses
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/jpeg",
                                            "data": base64_image
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": prompt_text
                                    }
                                ]
                            }
                        ]
                    }
                    
                    # Make the request with a timeout
                    response = requests.post(url, headers=headers, json=payload, timeout=15)
                    response_data = response.json()
                    
                    print("=== CLAUDE API RESPONSE ===")
                    print(f"Model: {model_name}")
                    print(f"Status code: {response.status_code}")
                    
                    # Check if the request was successful
                    if response.status_code == 200:
                        print(f"Success with model: {model_name}")
                        print(f"Full response: {json.dumps(response_data, indent=2)}")
                        
                        # Extract classification from response
                        if 'content' in response_data and len(response_data['content']) > 0:
                            classification_text = response_data['content'][0].get('text', '').strip()
                            print(f"Classification text: '{classification_text}'")
                            
                            # Normalize response
                            if "GAMING" in classification_text.upper():
                                print("Found 'GAMING' in response, classifying as GAMING")
                                return "GAMING", False  # False indicates AI classifier was used
                            else:
                                print("Did not find 'GAMING' in response, classifying as OTHER")
                                return "OTHER", False  # False indicates AI classifier was used
                        else:
                            print("No content found in successful response")
                        
                        # Break out of the model loop since we got a 200 response
                        break
                    else:
                        print(f"Failed with model {model_name}: {response_data}")
                except Exception as e:
                    print(f"Error with model {model_name}: {str(e)}")
                    continue
            
            # If we got here, all models failed or returned unexpected responses
            print("All Claude models failed or returned invalid responses. Using mock classifier.")
            classification = ImageClassifier.mock_classify(image_path)
            return classification, True  # True indicates mock classifier was used
                
        except Exception as e:
            print(f"ERROR CLASSIFYING IMAGE: {str(e)}")
            print("Traceback:", traceback.format_exc())
            
            # Default to mock classification on error
            print("Using fallback mock classifier")
            classification = ImageClassifier.mock_classify(image_path)
            return classification, True  # True indicates mock classifier was used
    
    @staticmethod
    def mock_classify(image_path):
        """
        Mock classifier for testing or when API key is not available
        
        Args:
            image_path: Path to the image file
            
        Returns:
            str: "GAMING" or "OTHER"
        """
        try:
            # Get filename without path
            filename = os.path.basename(image_path).lower()
            
            # Simple heuristic - if filename contains gaming-related terms
            gaming_terms = ['game', 'gaming', 'player', 'console', 'nintendo', 'xbox', 'playstation', 
                          'ps5', 'ps4', 'ps3', 'controller', 'minecraft', 'fortnite']
            
            for term in gaming_terms:
                if term in filename:
                    return "GAMING"
            
            # For testing, we'll classify almost all images as GAMING
            import random
            if random.randint(1, 100) <= 90:  # 90% chance of being classified as GAMING
                print("Mock classifier: Classified as GAMING")
                return "GAMING"
            else:
                print("Mock classifier: Classified as OTHER")
                return "OTHER"
                
        except Exception as e:
            print(f"Error in mock classification: {str(e)}")
            return "OTHER"  # Default fallback