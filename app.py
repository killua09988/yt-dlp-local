import os
import tempfile
import subprocess
from flask import Flask, render_template_string, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# HTML template for the form
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Downloader</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        input[type="url"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            background-color: #007bff;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
        }
        button:hover {
            background-color: #0056b3;
        }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .alert-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Video Downloader</h1>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-error">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="POST" action="{{ url_for('download') }}">
            <div class="form-group">
                <label for="video_url">Video URL:</label>
                <input type="url" id="video_url" name="video_url" required 
                       placeholder="https://www.youtube.com/watch?v=..."
                       value="{{ request.form.get('video_url', '') }}">
            </div>
            <button type="submit">Download Video</button>
        </form>
        
        <div class="footer">
            <p>created with Comet Assistant</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page with video URL form"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    """Download video using yt-dlp and return the file"""
    video_url = request.form.get('video_url')
    
    if not video_url:
        flash('Please provide a video URL')
        return redirect(url_for('index'))
    
    # Create a temporary directory for safe file handling
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Configure yt-dlp to download to temp directory
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')
        
        # Build yt-dlp command
        cmd = [
            'yt-dlp',
            '--format', 'best[height<=720]',  # Limit quality to reduce file size
            '--output', output_template,
            '--no-playlist',  # Only download single video
            video_url
        ]
        
        # Execute yt-dlp
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            flash(f'Error downloading video: {result.stderr}')
            return redirect(url_for('index'))
        
        # Find the downloaded file
        downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
        
        if not downloaded_files:
            flash('No file was downloaded')
            return redirect(url_for('index'))
        
        # Get the first (and should be only) downloaded file
        filename = downloaded_files[0]
        filepath = os.path.join(temp_dir, filename)
        
        # Create a secure filename
        secure_name = secure_filename(filename)
        
        # Send file and clean up in the teardown
        def remove_file(response):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            return response
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=secure_name,
            mimetype='application/octet-stream'
        )
        
    except subprocess.TimeoutExpired:
        flash('Download timed out. Please try again.')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}')
        return redirect(url_for('index'))
    finally:
        # Clean up temp directory if still exists
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
