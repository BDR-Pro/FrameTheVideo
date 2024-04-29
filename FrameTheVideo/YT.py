import os
import cv2
import uuid
import yt_dlp
from random import choice
from skimage.metrics import structural_similarity as ssim
import zipfile
import imagehash
from PIL import Image

def yt_to_title(video_id):
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
        return info.get('title', None)

def download_video(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info_dict)

def download_youtube_video(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print("Downloading YouTube video ...")
    path = download_video(video_url)
    print(f"Download complete of {path}.")
    return path

def get_images(video_path, output_folder, frame_skip, title):
    frame_skip = int(frame_skip)
    print(f"Extracting frames from video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Could not open video file.")

    images = []
    folder = os.path.join(output_folder, f"{title}_frames")
    os.makedirs(folder, exist_ok=True)

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
            images.append(file_name)
            cv2.imwrite(file_name, frame)
        i += 1
        print(f"Extracted frame {i}")

    cap.release()
    os.remove(video_path)  # Consider whether you want to keep this
    return images

def compare_images(image1, image2, similarity_threshold):
    img1 = cv2.imread(image1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(image2, cv2.IMREAD_GRAYSCALE)
    score = ssim(img1, img2)
    return score * 100 >= similarity_threshold

def remove_similar_images(images, similarity_threshold):

    print("Removing similar images...")
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

    print(f"Removed {removed} similar images.")


def zip_images(title, images):

    image_folder = os.path.dirname(images[0])
    print(f"Zipping images to {image_folder}")
    zip_file_path = (f"{title}_frames.zip")
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for image in os.listdir(image_folder):
            zipf.write(os.path.join(image_folder, image), image)
    print("Images zipped successfully.")
    for i in images:
        os.remove(i)
    os.rmdir(image_folder)
    return zip_file_path

def remove_excess_images(images, max_frames):
    # Ensure that we only attempt to remove images if there are more than max_frames
    while len(images) > max_frames:
        # Randomly select an index to remove
        index_to_remove = choice(range(len(images)))
        # Remove the image at the randomly selected index
        images.pop(index_to_remove)
            
def download_one_video(video_id, output_folder, frame_skip, similarity_percentage, max_frames):
    print(f"Processing video: {video_id}")
    video_path = download_youtube_video(video_id)
    title = yt_to_title(video_id)
    images = get_images(video_path, output_folder, frame_skip, title)
    remove_similar_images(images, similarity_percentage)
    remove_excess_images(images, max_frames)
    zip_file_path = zip_images(title, images)
    zip_file_path = os.path.abspath(zip_file_path)
    print(f"Processing complete. Zip file available at {zip_file_path}")
    return zip_file_path