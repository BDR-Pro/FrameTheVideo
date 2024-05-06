import os
import cv2
import uuid
import yt_dlp
from random import sample
from skimage.metrics import structural_similarity as ssim
import zipfile
import imagehash
from PIL import Image
import logging
import threading
from time import sleep
# Configure logging
logging.basicConfig(filename='yt.log', level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')



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
            logging.info(f"Title for video ID {video_id}: {info.get('title', None)}")
            return info.get('title', None)
    except Exception as e:
        logging.error(f"Failed to get title for video ID {video_id}: \n {str(e)}")
        return None

def download_video(url):
    try:
        out_dir = os.path.join(os.path.dirname(__file__), 'videos')
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]/best[ext=mp4]',
            'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
            #'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            logging.info(f"Downloaded video from URL {url} to {ydl.prepare_filename(info_dict)}")
            return convert_to_mp4(ydl.prepare_filename(info_dict))
    except Exception as e:
        logging.error(f"Failed to download video from URL {url}: \n {str(e)}")
        return None

def convert_to_mp4(video_path):
    """using ffmpeg to convert video to mp4 format"""
    try:
        if not os.path.exists(video_path):
            raise Exception(f"Video file does not exist \n {video_path}.")
        if video_path.endswith('.mp4'):
            logging.info(f"Video {video_path} is already in mp4 format.")
            return video_path
        out_dir = os.path.join(os.path.dirname(__file__), 'videos')
        output_path = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}.mp4")
        os.system(f"ffmpeg -i {video_path} -c:v libx264 -c:a aac -strict experimental {output_path}")
        logging.info(f"Converted video {video_path} to {output_path}")
        os.remove(video_path)
        return output_path
    except Exception as e:
        logging.error(f"Failed to convert video {video_path} to mp4: \n {str(e)}")
        return None
    
def download_youtube_video(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    return download_video(video_url)
    

def get_images(video_path, output_folder, frame_skip, title):
    frame_skip = int(frame_skip)
    logging.info(f"Getting images from video {video_path} with frame skip {frame_skip}")
    logging.info(f"Output folder: {output_folder}")
    logging.info(f"Title: {title}")
    logging.info(f"Frames in video {video_path}: {int(cv2.VideoCapture(video_path).get(cv2.CAP_PROP_FRAME_COUNT))}")
    if not os.path.exists(video_path):
        raise Exception(f"Video file does not exist \n {video_path}.")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Could not open video file.")

    
    folder = os.path.join(output_folder, f"{title}_frames")
    os.makedirs(folder, exist_ok=True)
    
    try:
        i = 0
        while True:
            success, frame = cap.read()
            if not success:
                break
            if i % frame_skip == 0:
                frame_index = int(i / frame_skip)
                unique_id = str(uuid.uuid4())
                file_name = os.path.join(folder, f"frame_{frame_index}_{unique_id[:5]}.jpg")
                file_name = os.path.abspath(file_name)
                cv2.imwrite(file_name, frame)
            i += 1
    except Exception as e:
        logging.error(f"Failed to get images from video {video_path}: \n {str(e)}")
        return None
            

    cap.release()
    os.remove(video_path)  
    logging.info(f"Downloaded {count_files(folder)} images from video {video_path}")
    return [os.path.join(folder, file) for file in os.listdir(folder)]

def compare_images(image1, image2, similarity_threshold):
    img1 = cv2.imread(image1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image2, cv2.IMREAD_GRAYSCALE)
    score = ssim(img1, img2)
    return score * 100 >= similarity_threshold

def remove_similar_images(images, similarity_threshold):

    
    hashes = {}
    removed = 0

    for img_path in images[:]:  # Create a copy of the list for safe iteration
        img = Image.open(img_path)
        img_hash = str(imagehash.average_hash(img))

        if img_hash in hashes:
            if compare_images(hashes[img_hash], img_path, similarity_threshold):
                os.remove(img_path)
                images.remove(img_path)
                removed += 1
        else:
            hashes[img_hash] = img_path
    logging.info(f"Removed {removed} similar images from {len(images)} images")
    
def count_files(folder):
    return len([name for name in os.listdir(folder) if os.path.isfile(os.path.join(folder, name))])

def zip_images(title, images, max_frames):

    image_folder = os.path.dirname(images[0])
    if count_files(image_folder) > max_frames:
        remove_excess_images(image_folder, max_frames)
    zip_file_path = (f"{title}_frames.zip")
    current_folder = os.path.dirname(__file__)
    current_folder = os.path.join(current_folder, 'web')
    zip_folder = 'output_folder'
    zip_file_path = os.path.join(current_folder,zip_folder, zip_file_path)
    
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for image in os.listdir(image_folder):
            zipf.write(os.path.join(image_folder, image), image)
    
    return zip_file_path

def remove_excess_images(image_dir, max_frames):
    logging.info(f"Removing excess images from {image_dir}")
    files = os.listdir(image_dir)
    if len(files) <= max_frames:
        return files
    
    excess_files = len(files) - max_frames
    files_to_remove = sample(files, excess_files)
    
    for file in files_to_remove:
        file_path = os.path.join(image_dir, file)
        os.remove(file_path)
    
    remaining_files = [file for file in files if file not in files_to_remove]
    logging.info(f"Removed {len(excess_files)} images from {image_dir}")
    return remaining_files

def download_one_video(video_id, output_folder, frame_skip, similarity_percentage, max_frames):
    
    title = yt_to_title(video_id)
    #check if it is already downloaded
    if os.path.exists(os.path.join(output_folder, f"{title}_frames.zip")):
        
        return os.path.join(output_folder, f"{title}_frames.zip")
    
    video_path = download_youtube_video(video_id)
    images = get_images(video_path, output_folder, frame_skip, title)
    remove_similar_images(images, similarity_percentage)

    zip_file_path = zip_images(title,images, max_frames)
    zip_file_path = os.path.abspath(zip_file_path)
    
    delete_folder_and_files(images)
    
    thread_to_delete_zip = threading.Thread(target=delete_folder_and_files, args=(zip_file_path))
    thread_to_delete_zip.start()
    
    return zip_file_path


def delete_folder_and_files(images):
    dir_path = os.path.dirname(images[0])
    # Delete all files in the directory 
    for file in os.listdir(dir_path):
        os.remove(os.path.join(dir_path, file))
    # Delete the directory
    os.rmdir(dir_path)
    
    
def delete_folder_and_files(zip_file_path):
    sleep(60*60*3) # 3 hours
    os.remove(zip_file_path)
    
    
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
            logging.info(f"Video {video_id} is too long. Duration: {duration}")
            return True
    return False