import psycopg2
import pandas as pd
import requests
import json
from datetime import datetime

# Database connection settings
db_name = 'scrapydb'
db_user = 'user'
db_pass = 'password'
db_host = 'localhost'
db_port = '5432'

# Ollama API settings
ollama_url = "http://localhost:11434/api/generate"
ollama_model = "llama3.2"

# Function to handle Ollama streaming responses
def generate_text_with_ollama(prompt):
    payload = {
        "model": ollama_model,
        "prompt": f"generate a unique title for this '{prompt}' title",
        "max_length": 50
    }
    try:
        response = requests.post(ollama_url, json=payload, stream=False)
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

        # Clean up and return only the first valid rewritten title
        if generated_text:
            titles = [line.strip() for line in generated_text.split("\n") if line.strip()]
            return titles[1] if titles else "No title generated."
        else:
            return "No output generated."
        
    except requests.exceptions.RequestException as e:
        return f"Request Error: {e}"


# Function to generate a short description using title, city_name, and room_type
def generate_description(title, city_name, room_type):
    prompt = f"Create a short description for a hotel room. Title: '{title}', City: '{city_name}', Room Type: '{room_type}'."
    
    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "max_length": 100  # Allow some extra length for a description
    }

    try:
        response = requests.post(ollama_url, json=payload, stream=False)
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

        # Return the generated description, or a default message if there's an issue
        if generated_description:
            return generated_description.strip()
        else:
            return "No description generated."
        
    except requests.exceptions.RequestException as e:
        return f"Request Error: {e}"


# Connect to PostgreSQL
try:
    conn = psycopg2.connect(
        database=db_name,
        user=db_user,
        password=db_pass,
        host=db_host,
        port=db_port
    )
    cur = conn.cursor()
    query = "SELECT city_name, hotel_id, title, rating, room_type, location, latitude, longitude, image FROM hotels;"
    cur.execute(query)

    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=columns)

    # Generate new title and description for each hotel
    if 'title' in df.columns and 'city_name' in df.columns and 'room_type' in df.columns:
        # Generate title using the previously defined method
        df['generated_title'] = df['title'].apply(generate_text_with_ollama)
        
        # Generate short description
        df['short_description'] = df.apply(lambda row: generate_description(row['title'], row['city_name'], row['room_type']), axis=1)
        
        print(df[['title', 'generated_title', 'short_description']])

        # Save the data to an Excel file with a timestamp
        output_file = f"hotels_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        print(f"Data saved to '{output_file}'.")
    else:
        print("Columns 'title', 'city_name', and 'room_type' not found in the DataFrame.")

except psycopg2.Error as db_error:
    print(f"Database Error: {db_error}")

finally:
    # Close the cursor and connection
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
