from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import redirect
import os
from random import choice
from YT import download_one_video , yt_to_title, long_video
import logging
import os
from time import sleep

logging.basicConfig(filename='email.log', level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


from django.conf import settings

import os
import threading
import re
from django.http import JsonResponse


Password = settings.EMAIL_HOST_PASSWORD

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

def authenticate_using_service_account():
    """Authenticate to Google API using a service account JSON key file."""
    try:
        scopes = ['https://www.googleapis.com/auth/drive']
        json_key_file_path = os.path.join(os.path.dirname(__file__), "django-422416-eda7f29f423d.json")
        credentials = Credentials.from_service_account_file(json_key_file_path, scopes=scopes)
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        logging.error(f"Failed to authenticate using service account: {e}")
        print(f"Failed to authenticate using service account: {e}")
        return None

def upload_to_google_drive(file_path):
    """Upload a file to Google Drive using a service account and return the shareable link.

    Args:
        file_path (str): The path to the file to upload.

    Returns:
        str: The shareable link to the uploaded file.
    """
    try:
        file_metadata = {
            'name': os.path.basename(file_path),
            'mimeType': 'application/octet-stream'
        }
        service = authenticate_using_service_account()
        media = MediaFileUpload(file_path, mimetype='application/octet-stream', resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        # Make the file shareable
        service.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'},
            fields='id'
        ).execute()
        print(f"Uploaded file to Google Drive: {file['webViewLink']}")
        return file['webViewLink']
    except Exception as e:
        print(f"Failed to upload file to Google Drive: {e}")
        return None


def main(request):
    return render(request, 'main.html')


def validate_email(email):
    """Check if the email address is valid.
    
    Args:
        email (str): The email address to validate.
    
    Returns:
        bool: True if the email address is valid, False otherwise.
    """
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def queue_in_background(video_id, output_folder , email):
    try:
        queue(video_id, output_folder, email)  
    except Exception as e:
        print(f"Error processing video (q in back) {video_id}: {e}")

def frame_the_video(request):
    try:
        video_id = request.GET.get('v')
        if video_id:
            email = request.GET.get('email').replace(" ", "")
            print(f"Processing video {video_id} with email {email}")
            if not email:
                return JsonResponse({'status': 'error', 'message': 'Email address is required'}, status=400)
            
            if not validate_email(email):
                return JsonResponse({'status': 'error', 'message': 'Invalid email address'}, status=400)
            
            if long_video(video_id):
                return JsonResponse({'status': 'error', 'message': 'Video is too long.'}, status=400)
            
            output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output_folder', f"{video_id}_frames"))
            os.makedirs(output_folder, exist_ok=True)
            # Start the queue operation in a background thread
            thread = threading.Thread(target=queue_in_background, args=(video_id,output_folder,email))
            thread.start()

            return JsonResponse({'status': 'success', 
                                'message': 'Video is being processed. Please wait a few minutes you can close this tab and check your email inbox later.'},
                                status=200)
        else:
            return JsonResponse({'status': 'error', 'message': 'No video ID provided'}, status=400)
    except Exception as e:
        print(f"Failed to process video: {e}")


def return_title(request):
    try:
        video_id = request.GET.get('v')
        if video_id:
            title = yt_to_title(video_id)
            if title:
                return JsonResponse({'title': title})
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to get title'}, status=500)
        return JsonResponse({'status': 'error', 'message': 'No video ID provided'}, status=400)
    except Exception as e:
        print(f"Failed to get video title: {e}")

def queue(video_id, output_folder,email):
    """download and process the video in the background and send email when done"""
    try:
        frame_skip = 50
        similarity_percentage = 65
        max_frames = 100
        print(f"Processing video {video_id} with email {email}")
        download_one_video(video_id, output_folder, frame_skip, similarity_percentage, max_frames)
        sleep(60*60*1)  # 1 hour
        zip_file_path = os.path.join(output_folder, f"{(video_id)}_frames.zip")
                
        return send_email(email, zip_file_path)
    except Exception as e:
        logging.error(f"Failed to process video (q): {e}")

def messages(request):
    messages = [
        
    "This operation might take a few minutes, please be patient.",
    "This process will generate 100 images. If you require more, please consider upgrading to Pro mode.",
    "This application was created by Bader Alotaibi (BDR-PRO) on GitHub. Check out more projects there!",
    "Experiencing issues? Contact support for assistance.",
    "Thank you for using our YouTube Wallpaper Extractor. We hope you enjoy your wallpapers!",
    "Don't forget to share your favorite wallpapers on social media!",
    "Looking for custom features? Our Pro version offers expanded capabilities.",
    "Stay tuned for updates and new features by following us on social media.",
    "Your feedback is important to us. Please let us know how we can improve your experience.",
    "Check out our other tools and services on our GITHUB (BDR-PRO) to enhance your digital content creation."
]

    return JsonResponse({'message': choice(messages)})





def favicon(request):
    return redirect('https://filmfluency.fra1.cdn.digitaloceanspaces.com/static/other_project/favicon.ico')


def store_in_text(email, zip_file_path):
    if not os.path.exists('email.txt'):
        with open('email.txt', 'w') as f:
            f.write("Emails and Zip file paths\n\n")
    with open('email.txt', 'a') as f:
        f.write(f"Email: {email} \n")
        f.write(f"Zip file path: {zip_file_path} \n\n")
        


def send_email(email, zip_file_path):
    """Send an email with the zip file attached.
    
    Args:
        email (str): The recipient's email address.
        zip_file_path (str): The path to the zip file to be attached.
    """
    try:
        # Create the email object
        
        logging.info(f"Sending email to {email} with zip file {zip_file_path}")
        print(f"Sending email to {email} with zip file {zip_file_path}")
        store_in_text(email, zip_file_path)
        msg = MIMEMultipart()
        msg['Subject'] = 'Your Requested Wallpaper (FrameTheVideo)'
        msg['From'] = 'framethevideo@gmail.com'
        msg['To'] = email

        # Set the body of the email
        body = MIMEText("Hello, \n\nThank you for using FrameTheVideo! \n\nPlease find the attached zip file containing the wallpaper images extracted from the video you requested. \n\nEnjoy! \n\nBest regards, \nBader Alotaibi (BDR-PRO) Github", 'plain')
        msg.attach(body)
        name_of_zip = os.path.basename(zip_file_path).replace(".zip", "")
        msg.attach(MIMEText(f"\n For the video: {name_of_zip}", 'plain'))
        # upload the zip file to google drive
        link = upload_to_google_drive(zip_file_path)
        logging.info(f"Uploaded zip file to Google Drive: {link}")
        print(f"Uploaded zip file to Google Drive: {link}")
        msg.attach(MIMEText(f"\n Download the zip file from Google Drive: {link}", 'plain'))
        
        # Set up the SMTP server and send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('framethevideo@gmail.com', Password)
            server.send_message(msg)
            logging.info(f"Email sent to {email}")
    except Exception as e:
        logging.error(f"Failed to send email to \n {email}: {e}")