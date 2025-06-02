from flask import Flask, render_template_string, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

VENICE_API_KEY = os.getenv("VENICE_API_KEY")
VENICE_ENDPOINT = "https://api.venice.ai/api/v1/image/generate"
MODEL_NAME = "hidream"

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meme Generator</title>
    <style>
        /* Dark theme styling */
        body, html {
            margin: 0;
            padding: 0;
            background: #121212;
            color: white;
            font-family: Arial, sans-serif;
        }

        /* Main content area */
        .content {
            padding: 20px;
            padding-bottom: 100px;
        }

        /* Text input container */
        .input-container {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 10px;
            width: 80%;
            max-width: 600px;
        }

        /* Text input */
        .text-input {
            background: #2d2d2d;
            color: white;
            padding: 10px 20px;
            flex: 1;
            border: none;
            border-radius: 25px;
            font-size: 18px;
        }

        /* Send button */
        .send-btn {
            background: #4CAF50;
            border: none;
            color: white;
            padding: 12px 16px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 18px;
            transition: background-color 0.3s;
        }

        .send-btn:hover {
            background: #45a049;
        }

        .send-btn:disabled {
            background: #333;
            cursor: not-allowed;
        }

        .meme-container {
            max-width: 800px;
            margin: 50px auto;
            text-align: center;
        }

        img {
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .loading {
            display: none;
            font-size: 18px;
            color: #888;
            margin: 20px 0;
        }

        .spinner {
            border: 4px solid #333;
            border-top: 4px solid #888;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 10px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            color: #ff6b6b;
            font-size: 16px;
            margin: 10px 0;
        }

        .text-input:disabled {
            background: #1a1a1a;
            cursor: not-allowed;
        }

        /* Redo button */
        .redo-btn {
            display: none;
            background: #555;
            border: none;
            color: white;
            padding: 10px 15px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            margin: 15px auto;
            transition: background-color 0.3s;
        }

        .redo-btn:hover {
            background: #666;
        }

        .redo-btn:disabled {
            background: #333;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    
    <div class="content">
        <div class="meme-container">
            <h1>Meme Generator</h1>
            <div id="loading" class="loading">
                <div class="spinner"></div>
                Generating meme...
            </div>
            <div id="error" class="error"></div>
            <img id="meme-image" src="#" alt="Generated Meme" style="display: none;">
            <button id="redo-btn" class="redo-btn">🔄 Generate Again</button>
        </div>
    </div>

    
    <div class="input-container">
        <input type="text" class="text-input" id="prompt-input" placeholder="Enter your meme text..." autocomplete="off">
        <button id="send-btn" class="send-btn">➤</button>
    </div>

    <script>
        let lastPrompt = '';

        function generateMeme(prompt) {
            const textInput = document.querySelector('.text-input');
            const sendBtn = document.getElementById('send-btn');
            const redoBtn = document.getElementById('redo-btn');

            // Show loading state
            textInput.disabled = true;
            sendBtn.disabled = true;
            redoBtn.disabled = true;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('error').textContent = '';
            document.getElementById('meme-image').style.display = 'none';
            redoBtn.style.display = 'none';

            fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: prompt})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                document.getElementById('meme-image').src = data.image_url;
                document.getElementById('meme-image').style.display = 'block';
                redoBtn.style.display = 'block';
                lastPrompt = prompt;
            })
            .catch(error => {
                document.getElementById('error').textContent = 'Error: ' + error.message;
            })
            .finally(() => {
                // Hide loading state
                document.getElementById('loading').style.display = 'none';
                textInput.disabled = false;
                sendBtn.disabled = false;
                redoBtn.disabled = false;
            });
        }

        // Form submission handling
        document.querySelector('.text-input').addEventListener('keydown', function(e) {
            if(e.key === 'Enter' && !this.disabled) {
                const prompt = this.value.trim();
                if (!prompt) return;

                generateMeme(prompt);
                this.value = ''; // Clear input
            }
        });

        // Send button click
        document.getElementById('send-btn').addEventListener('click', function() {
            const textInput = document.querySelector('.text-input');
            const prompt = textInput.value.trim();
            if (!prompt || this.disabled) return;

            generateMeme(prompt);
            textInput.value = ''; // Clear input
        });

        // Redo button click
        document.getElementById('redo-btn').addEventListener('click', function() {
            if (lastPrompt && !this.disabled) {
                generateMeme(lastPrompt);
            }
        });
    </script>
</body>
</html>
''')

@app.route('/generate', methods=['POST'])
def generate_meme():
    # Check if API key is configured
    if not VENICE_API_KEY:
        return jsonify({'error': 'API key not configured'}), 500
    
    data = request.json
    if not data:
        return jsonify({'error': 'No JSON data received'}), 400
    
    user_prompt = data.get('prompt', '').strip()
    if not user_prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    # Format the prompt for meme generation
    formatted_prompt = f"""Create a meme image with the following joke/text: "{user_prompt}"

Generate an image that visually represents the text entered by the user exactly as spelled, including every word, and with no duplication. The image should be suitable for a meme format and include the exact text "{user_prompt}" displayed prominently on the image in a clear, readable meme-style font. The image should be funny, relatable, and capture the essence of the joke. Use appropriate visual elements, characters, or scenarios that complement the humor of the text."""
    
    try:
        response = requests.post(VENICE_ENDPOINT, headers={
            'Authorization': f'Bearer {VENICE_API_KEY}',
            'Content-Type': 'application/json'
        }, json={
            'model': MODEL_NAME,
            'prompt': formatted_prompt,
            'width': 1024,
            'height': 1024,
            'steps': 20,
            'cfg_scale': 7.5,
            'format': 'webp',
            'safe_mode': False,
            'return_binary': False,
            'hide_watermark': True
        }, timeout=60)
        
        if response.status_code == 200:
            response_data = response.json()
            if 'images' in response_data and len(response_data['images']) > 0:
                # The API returns base64 encoded images, create data URL
                base64_image = response_data['images'][0]
                image_url = f"data:image/webp;base64,{base64_image}"
                return jsonify({'image_url': image_url})
            else:
                return jsonify({'error': 'No images in response'}), 500
        else:
            error_message = f'API returned status {response.status_code}'
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_message = error_data['error']
            except:
                pass
            return jsonify({'error': error_message}), 500
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out (60s)'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
