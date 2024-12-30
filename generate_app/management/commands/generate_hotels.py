import json
import requests
from django.core.management.base import BaseCommand
from generate_app.models import Hotel
from django.db import connections

# Ollama API settings
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

# Function to generate a rewritten title using Ollama
def generate_text_with_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"Generate a unique title for this '{prompt}' title",
        "max_length": 50
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=False)
        response.raise_for_status()

        generated_text = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    generated_text += data.get("response", "")
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON line: {line}")

        return generated_text.strip() if generated_text else "No title generated."
        
    except requests.exceptions.RequestException as e:
        return f"Request Error: {e}"

# Function to generate a short description using title, city_name, and room_type
def generate_description(title, city_name, room_type):
    prompt = f"Create a short description for a hotel room. Title: '{title}', City: '{city_name}', Room Type: '{room_type}'."
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_length": 100
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=False)
        response.raise_for_status()

        generated_description = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    generated_description += data.get("response", "")
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON line: {line}")

        return generated_description.strip() if generated_description else "No description generated."
        
    except requests.exceptions.RequestException as e:
        return f"Request Error: {e}"

# Django Management Command
class Command(BaseCommand):
    help = "Generate unique titles and descriptions for hotels and update the database."

    def handle(self, *args, **kwargs):
        # Fetch hotel data from the external database (scrapy)
        with connections['scrapy'].cursor() as cursor:
            cursor.execute("SELECT id, title, city_name, room_type FROM hotels LIMIT 5")
            properties = cursor.fetchall()

            print(properties)

        # Update each hotel with generated title and description
        for prop in properties:
            hotel_id, title, city_name, room_type = prop
            
            generated_title = generate_text_with_ollama(title)
            short_description = generate_description(title, city_name, room_type)

            # Save to the Hotel model
            hotel, created = Hotel.objects.update_or_create(
                original_id=hotel_id,
                defaults={
                    'original_title': title,
                    'rewritten_title': generated_title,
                    'short_description': short_description
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created new hotel record for ID {hotel_id}."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated hotel record for ID {hotel_id}."))

        self.stdout.write(self.style.SUCCESS("Hotel records have been updated."))