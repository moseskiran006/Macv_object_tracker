# MacV Object Tracker

![Object Tracking Demo](demo.gif) *Example of object tracking with tail lines*

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Output Format](#output-format)
- [Technical Approach](#technical-approach)
- [Evaluation Metrics](#evaluation-metrics)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)
- [License](#license)

## Features

✔ **Core Tracking Functionality**
- Real-time object detection using YOLOv8
- Persistent tracking with ByteTrack algorithm
- Visualizations:
  - Bounding boxes
  - Object centroids
  - Movement tail lines (30-frame history)

✔ **Analytics**
- Time-in-frame for each object
- Unique object count
- Frame-by-frame tracking data

✔ **Output Options**
- WebM video (browser compatible)
- MP4 video (alternative format)
- Text report with metrics

## Installation

### Requirements
- Python 3.8+
- FFmpeg (for video processing)
- Modern web browser (for HTML viewer)

### Setup Steps

```bash
# Clone repository
git clone https://github.com/yourusername/macv-object-tracker.git
cd macv-object-tracker

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
