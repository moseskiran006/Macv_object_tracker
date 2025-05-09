import cv2
import numpy as np
from collections import defaultdict
from ultralytics import YOLO
import os

class ObjectTracker:
    def __init__(self, video_path, output_path, report_path):
        self.video_path = video_path
        self.output_path = output_path
        self.report_path = report_path
        self.model = YOLO('yolov8n.pt')
        self.track_history = defaultdict(list)
        self.object_times = defaultdict(float)
        self.unique_ids = set()
        self.prev_time = {}
        self.frame_count = 0
        self.fps = 0
        
    def calculate_metrics(self):
        cap = cv2.VideoCapture(self.video_path)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        
    def process_video(self):
        self.calculate_metrics()
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError("Error opening video file")
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Define codec and create VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'vp90')
        out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (width, height))
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
                
            self.frame_count += 1
            
            results = self.model.track(frame, persist=True, tracker="bytetrack.yaml")
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist() if results[0].boxes.id is not None else []
            
            annotated_frame = results[0].plot()
            
            current_time = self.frame_count / self.fps
            for box, track_id in zip(boxes, track_ids):
                x, y, w, h = box
                centroid = (int(x), int(y))
                
                self.track_history[track_id].append(centroid)
                self.unique_ids.add(track_id)
                
                if track_id in self.prev_time:
                    time_elapsed = current_time - self.prev_time[track_id]
                    self.object_times[track_id] += time_elapsed
                self.prev_time[track_id] = current_time
                
                cv2.circle(annotated_frame, centroid, 5, (0, 255, 0), -1)
                
                track = self.track_history[track_id][-30:]
                for i in range(1, len(track)):
                    cv2.line(annotated_frame, track[i-1], track[i], (0, 255, 255), 2)
            
            cv2.putText(annotated_frame, f"Unique Objects: {len(self.unique_ids)}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            out.write(annotated_frame)
            
        final_time = self.frame_count / self.fps
        for track_id in self.prev_time:
            self.object_times[track_id] += final_time - self.prev_time[track_id]
            
        cap.release()
        out.release()
        self.generate_report()
        
    def generate_report(self):
        report = {
            "total_unique_objects": len(self.unique_ids),
            "object_times": {str(k): f"{v:.2f} seconds" for k, v in self.object_times.items()},
            "video_duration": f"{self.frame_count / self.fps:.2f} seconds",
            "processing_fps": f"{self.fps:.2f}"
        }
        
        with open(self.report_path, 'w') as f:
            for key, value in report.items():
                if isinstance(value, dict):
                    f.write(f"{key}:\n")
                    for subkey, subvalue in value.items():
                        f.write(f"  {subkey}: {subvalue}\n")
                else:
                    f.write(f"{key}: {value}\n")