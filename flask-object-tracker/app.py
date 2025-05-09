from flask import Flask, render_template, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
from object_tracker import ObjectTracker
import time

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(input_path)
            
            # Generate unique output filename
            timestamp = str(int(time.time()))
            output_filename = f"result_{timestamp}.webm"
            output_path = os.path.join(app.config['RESULT_FOLDER'], output_filename)
            report_filename = f"report_{timestamp}.txt"
            report_path = os.path.join(app.config['RESULT_FOLDER'], report_filename)
            
            # Process the video
            tracker = ObjectTracker(input_path, output_path, report_path)
            tracker.process_video()
            
            return redirect(url_for('show_results', 
                                 video=output_filename, 
                                 report=report_filename))
    
    return render_template('index.html')

@app.route('/results')
def show_results():
    video = request.args.get('video')
    report = request.args.get('report')
    return render_template('results.html', video=video, report=report)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(RESULT_FOLDER, exist_ok=True)
    app.run(debug=True)