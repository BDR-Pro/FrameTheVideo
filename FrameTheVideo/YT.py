import os
import cv2
import yt_dlp
import subprocess
from random import sample
from skimage.metrics import structural_similarity as ssim
import zipfile
import threading
from time import sleep

def translate_string(string):
    return string.translate(str.maketrans('', '', '\/:*?"<>|')).replace(' ', '_').replace('.', '_').replace(',', '_').replace(';', '_').replace(':', '_').replace('!', '_').replace('?', '_').replace('(', '_').replace(')', '_').replace('[', '_').replace(']', '_').replace('{', '_').replace('}', '_').replace('-', '_').replace('+', '_').replace('=', '_').replace('&', '_').replace('%', '_').replace('#', '_').replace('@', '_').replace('$', '_').replace('^', '_').replace('*', '_').replace('~', '_').replace('`', '_').replace('\'', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('\\', '_').replace('/', '_')

def yt_to_title(video_id):
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True,
            'force_generic_extractor': True,
            'force_title': True,
            'force_filename': True,
            'outtmpl': '%(title)s.%(ext)s',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            print(f"Title for video ID {video_id}: {info.get('title', None)}")
            return info.get('title', None)
    except Exception as e:
        return None

def download_video(url):
    try:
        out_dir = os.path.join(os.path.dirname(__file__), 'videos')
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]/best[ext=mp4]',
            'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            print(f"Downloaded video from URL {url} to {ydl.prepare_filename(info_dict)}")
            return convert_to_mp4(ydl.prepare_filename(info_dict))
    except Exception as e:
        print(f"Failed to download video from URL {url}: \n {str(e)}")
        return None

def convert_to_mp4(video_path):
    try:
        if not os.path.exists(video_path):
            raise Exception(f"Video file does not exist \n {video_path}.")
        if video_path.endswith('.mp4'):
            print(f"Video {video_path} is already in mp4 format.")
            return video_path
        out_dir = os.path.join(os.path.dirname(__file__), 'videos')
        output_path = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}.mp4")
        os.system(f"ffmpeg -i {video_path} -c:v libx264 -c:a aac -strict experimental {output_path}")
        print(f"Converted video {video_path} to {output_path}")
        os.remove(video_path)
        return output_path
    except Exception as e:
        print(f"Failed to convert video {video_path} to mp4: \n {str(e)}")
        return None

def download_youtube_video(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    return download_video(video_url)


def capture_frames_ffmpeg(video_path, output_folder, frame_skip):
    """
    Capture frames from a video at intervals of 'frame_skip' frames using ffmpeg and OpenCV for frame rate.
    
    Parameters:
    video_path (str): Path to the video file.
    output_folder (str): Folder to save the screenshots.
    frame_skip (int): Number of frames to skip between screenshots.
    """
    fps = get_video_fps(video_path)
    # Calculate effective fps to capture at
    effective_fps = fps / frame_skip

    # Ensure video path is safe for command line use
    safe_video_path = f'"{video_path}"'

    # Frame extraction command using ffmpeg
    ffmpeg_cmd = (
        f'ffmpeg -i {safe_video_path} -vf "fps={effective_fps}" '
        f'"{output_folder}/frame_%04d.png"'
    )
    try:
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
        print(f"Frames saved to {output_folder} at 1 frame every {frame_skip} frames.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to extract frames: {e}")
        print(f"stderr: {e.stderr}")


def get_video_fps(video_path):


    # Load video using cv2 to get the frame rate
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return fps

def compare_images(image1, image2, similarity_threshold):
    img1 = cv2.imread(image1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image2, cv2.IMREAD_GRAYSCALE)
    score = ssim(img1, img2)
    return score * 100 >= similarity_threshold

def remove_similar_images(video_id, similarity_threshold, max_frames, title):
    folder = os.path.join(os.path.dirname(__file__), 'output_folder', f"{video_id}_frames")
    images = [os.path.join(folder, f) for f in os.listdir(folder)]
    images.sort()
    i = 0
    while i < len(images) - 1:
        if compare_images(images[i], images[i + 1], similarity_threshold):
            os.remove(images[i + 1])
            images.pop(i + 1)
        else:
            i += 1
    return os.path.abspath(zip_images(title,  video_id , max_frames))

def count_files(folder):
    return len([name for name in os.listdir(folder) if os.path.isfile(os.path.join(folder, name))])


def zip_images(title, video_id, max_frames):
    # Sanitize the title to remove any problematic characters
    title = title.translate(str.maketrans('', '', '\/:*?"<>|'))

    # Construct the path to the image folder
    image_folder = os.path.join(os.path.dirname(__file__), 'output_folder', f"{video_id}_frames")
    
    # Remove excess images if necessary
    if count_files(image_folder) > max_frames:
        remove_excess_images(image_folder, max_frames)
    
    # Ensure the directory for the zip file exists
    zip_directory = os.path.join(os.path.dirname(__file__), 'output_folder')
    if not os.path.exists(zip_directory):
        os.makedirs(zip_directory)
    
    # Construct the path for the zip file
    zip_file_path = os.path.join(zip_directory, f"{title}_frames.zip")
    
    # Print the path for debugging
    print(f"Creating zip file at: {zip_file_path}")
    
    # Create the zip file and add images
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for image in os.listdir(image_folder):
            image_path = os.path.join(image_folder, image)
            zipf.write(image_path, os.path.basename(image_path))
    
    # Return the path to the created zip file
    return zip_file_path


def remove_excess_images(image_dir, max_frames):
    print(f"Removing excess images from {image_dir}")
    files = os.listdir(image_dir)
    if len(files) <= max_frames:
        return files

    excess_files = len(files) - max_frames
    files_to_remove = sample(files, excess_files)

    for file in files_to_remove:
        file_path = os.path.join(image_dir, file)
        os.remove(file_path)

    remaining_files = [file for file in files if file not in files_to_remove]
    print(f"Removed {len(excess_files)} images from {image_dir}")
    return remaining_files

def download_one_video(video_id, output_folder, frame_skip, similarity_percentage, max_frames):
    title = yt_to_title(video_id)
    if os.path.exists(os.path.join(output_folder, f"{title}_frames.zip")):
        return os.path.join(output_folder, f"{title}_frames.zip")
    
    video_path = download_youtube_video(video_id)
    video_id = translate_string(video_id)
    thread_to_delete_zip = threading.Thread(target=delete_folder_and_files)
    thread_to_delete_zip.start()
    
    thread_to_process_video = threading.Thread(target=process_video, args=(video_path, output_folder, frame_skip, similarity_percentage, max_frames, title, video_id))
    thread_to_process_video.start()
    print(f"Processing video {video_id} with title {title} in the background and sending email when done. Please wait (170).")



def process_video(video_path, output_folder, frame_skip, similarity_percentage, max_frames, title, video_id):
    capture_frames_ffmpeg(video_path, output_folder, frame_skip)
    return remove_similar_images(video_id, similarity_percentage, max_frames, title)


def delete_folder_and_files():
    sleep(60*60*3)  # 3 hours
    folders = [f for f in os.listdir(os.path.join(os.path.dirname(__file__), 'output_folder')) if os.path.isdir(f)]
    for folder in folders:
        folder_path = os.path.join(os.path.dirname(__file__), 'output_folder', folder)
        files = os.listdir(folder_path)
        for file in files:
            os.remove(os.path.join(folder_path, file))
        os.rmdir(folder_path)
    return delete_zip_files()

def delete_zip_files():
    zip_files = [f for f in os.listdir(os.path.join(os.path.dirname(__file__), 'output_folder')) if f.endswith('.zip')]
    for file in zip_files:
        os.remove(os.path.join(os.path.dirname(__file__), 'output_folder', file))
    return delete_video_folder()

def delete_video_folder():
    video_folder = os.path.join(os.path.dirname(__file__), 'videos')
    files = os.listdir(video_folder)
    for file in files:
        os.remove(os.path.join(video_folder, file))
    return os.rmdir(video_folder)

def long_video(video_id):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': True,
        'force_title': True,
        'force_filename': True,
        'outtmpl': '%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        duration = info.get('duration', 0)
        if duration > 60*35:
            print(f"Video {video_id} is too long. Duration: {duration}")
            return True
    return False
