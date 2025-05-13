from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, Response
import os
from werkzeug.utils import secure_filename
from object_tracker import ObjectTracker
import time
import traceback
from datetime import datetime
import subprocess
import shutil

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()  # Secure random key

# Configuration
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
MAX_FILE_SIZE_MB = 500

app.config.update({
    'UPLOAD_FOLDER': UPLOAD_FOLDER,
    'RESULT_FOLDER': RESULT_FOLDER,
    'MAX_CONTENT_LENGTH': MAX_FILE_SIZE_MB * 1024 * 1024,
    'ALLOWED_EXTENSIONS': ALLOWED_EXTENSIONS
})

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_dirs():
    """Ensure required directories exist"""
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

def ensure_web_compatible(video_path):
    """Convert video to web-compatible format using ffmpeg"""
    try:
        # Check if ffmpeg is available
        ffmpeg_check = subprocess.run(["ffmpeg", "-version"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
        
        if ffmpeg_check.returncode != 0:
            app.logger.warning("FFmpeg not found, skipping video conversion")
            return False
        
        # Create temporary output file
        temp_output = video_path + ".web.mp4"
        
        # Run ffmpeg conversion
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path,
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",  # Ensure pixel format compatibility 
            "-movflags", "+faststart",  # Optimize for web playback
            "-an",  # No audio
            temp_output
        ]
        
        result = subprocess.run(ffmpeg_cmd, 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
        
        if result.returncode == 0 and os.path.exists(temp_output) and os.path.getsize(temp_output) > 0:
            # Replace original with web-compatible version
            shutil.move(temp_output, video_path)
            app.logger.info(f"Successfully converted {video_path} to web compatible format")
            return True
        else:
            app.logger.warning(f"Failed to convert video: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        app.logger.error(f"Video conversion error: {str(e)}")
        return False

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    create_dirs()  # Ensure directories exist
    
    if request.method == 'POST':
        # Validate file presence
        if 'file' not in request.files:
            flash('No file part in request', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Validate file selection
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        # Validate file type
        if not allowed_file(file.filename):
            flash(f'Allowed file types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}', 'error')
            return redirect(request.url)
        
        try:
            # Secure filename and create paths
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{secure_filename(file.filename)}"
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save uploaded file
            file.save(input_path)
            
            # Verify file was saved
            if not os.path.exists(input_path):
                raise RuntimeError("Failed to save uploaded file")
            
            # Prepare output paths
            output_filename = f"tracked_{timestamp}.mp4"
            output_path = os.path.join(app.config['RESULT_FOLDER'], output_filename)
            report_filename = f"report_{timestamp}.txt"
            report_path = os.path.join(app.config['RESULT_FOLDER'], report_filename)
            
            # Process video
            tracker = ObjectTracker(input_path, output_path, report_path)
            tracker.start_time = time.time()  # For timing measurements
            tracker.process_video()
            
            # Verify outputs
            if not os.path.exists(output_path):
                raise RuntimeError("Tracking output not generated")
            if not os.path.exists(report_path):
                raise RuntimeError("Report file not generated")
            
            # Ensure video is web compatible
            ensure_web_compatible(output_path)
            
            return redirect(url_for('show_results',
                                   video=output_filename,
                                   report=report_filename))
            
        except Exception as e:
            app.logger.error(f"Processing error: {str(e)}\n{traceback.format_exc()}")
            flash(f'Processing failed: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('index.html', MAX_FILE_SIZE_MB=MAX_FILE_SIZE_MB)

@app.route('/results')
def show_results():
    video = request.args.get('video')
    report = request.args.get('report')
    
    # Validate parameters
    if not video or not report:
        flash('Invalid results parameters', 'error')
        return redirect(url_for('upload_file'))
    
    video_path = os.path.join(app.config['RESULT_FOLDER'], video)
    report_path = os.path.join(app.config['RESULT_FOLDER'], report)
    
    # Verify files exist
    if not os.path.exists(video_path):
        flash('Video file not found', 'error')
        return redirect(url_for('upload_file'))
    
    if not os.path.exists(report_path):
        flash('Report file not found', 'error')
        return redirect(url_for('upload_file'))
    
    # Get file size for display
    video_size = os.path.getsize(video_path) // (1024 * 1024)  # MB
    
    return render_template('results.html',
                         video=video,
                         report=report,
                         video_size=video_size)

# Enhanced video streaming route for better playback
@app.route('/stream/<path:filename>')
def stream_video(filename):
    video_path = os.path.join(app.config['RESULT_FOLDER'], filename)
    
    # Check if file exists
    if not os.path.exists(video_path):
        return "Video not found", 404
        
    def generate():
        with open(video_path, 'rb') as video_file:
            data = video_file.read(1024 * 1024)  # Read 1MB at a time
            while data:
                yield data
                data = video_file.read(1024 * 1024)
    
    return Response(generate(), 
                  mimetype='video/mp4',
                  headers={'Accept-Ranges': 'bytes'})

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    create_dirs()
    app.run(host='0.0.0.0', port=5000, debug=True)  # Enable debug mode during development
