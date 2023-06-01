import subprocess
import os
import math
import moviepy.editor as mpy
from tkinter import Tk
from tkinter.filedialog import askopenfilenames
import concurrent.futures

def split_video(video_path, output_dir):
    duration = get_video_duration(video_path)
    num_parts = math.ceil(duration / 300)  # Split into 5-minute sections

    os.makedirs(output_dir, exist_ok=True)
    output_paths = []

    audio_output_dir = os.path.join(output_dir, "mp3s")
    os.makedirs(audio_output_dir, exist_ok=True)

    for i in range(num_parts):
        start_time = i * 300
        end_time = min((i + 1) * 300, duration)

        output_file = f"part{i+1}.mp4"
        output_path = os.path.join(output_dir, output_file)
        output_paths.append(output_path)

        audio_file = f"audio{i+1}.mp3"
        print(f"Audio Output {audio_file} And Video Output {output_file}")
        audio_output_path = os.path.join(audio_output_dir, audio_file)

        command = [
            "ffmpeg",
            "-i", video_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy",
            "-avoid_negative_ts", "1",
            output_path
        ]

        subprocess.run(command, capture_output=True)

        audio_command = [
            "ffmpeg",
            "-i", output_path,
            "-vn",
            "-acodec", "libmp3lame",
            audio_output_path
        ]

        subprocess.run(audio_command, capture_output=True)

    return output_paths

def get_video_duration(video_path):
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    result = subprocess.run(command, capture_output=True, text=True)
    duration = float(result.stdout)
    return duration

def crop_video(video_path, output_path):
    clip = mpy.VideoFileClip(video_path)
    (w, h) = clip.size
    crop_width = h * 9 / 16
    x1, x2 = (w - crop_width) // 2, (w + crop_width) // 2
    y1, y2 = 0, h
    cropped_clip = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
    resized_filename = os.path.join(os.path.basename(os.path.splitext(output_path)[0]) + "-resized.mp4")
    resized_filepath = os.path.join(resized_dir, resized_filename)
    cropped_clip.write_videofile(resized_filepath)
    clip.close()

if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    video_paths = askopenfilenames(filetypes=[("MP4 files", "*.mp4")])

    for video_path in video_paths:
        base_dir = os.path.dirname(video_path)
        split_dir = os.path.join(base_dir, "split")
        resized_dir = os.path.join(base_dir, "Resized")

        split_output_paths = split_video(video_path, split_dir)
        
        os.makedirs(resized_dir, exist_ok=True)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for output_path in split_output_paths:
                futures.append(executor.submit(crop_video, output_path, output_path))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error processing video: {e}")
