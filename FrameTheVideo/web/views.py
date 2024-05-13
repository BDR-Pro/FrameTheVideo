from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
import os
from random import choice
from YT import download_one_video , yt_to_title, long_video
import os
from time import sleep


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


from django.conf import settings

import os
import threading
import re
from django.http import JsonResponse
Password = settings.EMAIL_HOST_PASSWORD
aws_access_key_id = settings.AWS_ACCESS_KEY_ID
aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
import boto3
from botocore.exceptions import NoCredentialsError
import random
import string

def random_64_string():
    """Generate a random 64-character string.
    
    Returns:
        str: A random 64-character string.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=64))

def upload_file_to_s3(file_path, object_name, aws_access_key_id, aws_secret_access_key):
    """Upload a file to an S3 bucket using provided AWS credentials.

    Args:
        file_path (str): The path to the file to upload.
        object_name (str): The name of the object in the bucket.
        aws_access_key_id (str): AWS access key ID.
        aws_secret_access_key (str): AWS secret access key.

    Returns:
        str: The URL of the uploaded file or None if upload fails.
    """
    try:
        url = "https://framethevideo.fra1.cdn.digitaloceanspaces.com"
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        s3.upload_file(file_path, "framethevideo", object_name)
        obj_url = f"{url}/{object_name}"
        return obj_url
    except NoCredentialsError:
        print("No AWS credentials available")
        return None
    

def delete_s3_object(object_name, aws_access_key_id, aws_secret_access_key):
    """Delete an object from an S3 bucket using provided AWS credentials.

    Args:
        object_name (str): The name of the object to delete.
        aws_access_key_id (str): AWS access key ID.
        aws_secret_access_key (str): AWS secret access key.

    Returns:
        str: Message indicating deletion status.
    """
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        s3.delete_object(Bucket="framethevideo", Key=object_name)
        return "Deleted"
    except Exception as e:
        print(f"Failed to delete S3 object {object_name}: {e}")
        return "Deletion failed"
    
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
                
        return send_email(email, zip_file_path, yt_to_title(video_id))
    except Exception as e:
        print(f"Failed to process video (q): {e}")

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
        


def send_email(email, zip_file_path, title):
    """Send an email with the zip file attached.
    
    Args:
        email (str): The recipient's email address.
        zip_file_path (str): The path to the zip file to be attached.
    """
    try:
        # Create the email object
        
        print(f"Sending email to {email} with zip file {zip_file_path}")
        print(f"Sending email to {email} with zip file {zip_file_path}")
        store_in_text(email, zip_file_path)
        msg = MIMEMultipart()
        msg['Subject'] = 'Your Requested Wallpaper (FrameTheVideo)'
        msg['From'] = 'framethevideo@gmail.com'
        msg['To'] = email

        # Set the body of the email
        body = MIMEText("Hello, \n\nThank you for using FrameTheVideo! \n\nPlease find the attached zip file containing the wallpaper images extracted from the video you requested. \n\nEnjoy! \n\nBest regards, \nBader Alotaibi (BDR-PRO) Github", 'plain')
        msg.attach(body)
        
        msg.attach(MIMEText(f"\n\nFor the video: {title}", 'plain'))
        # upload the zip file to google drive
        random=random_64_string()+".zip"
        link = upload_file_to_s3(zip_file_path, random)
        print(f"Uploaded zip file to Mega: {link}")
        remove = "framethevideo.com"+"/delete/"+random
        msg.attach(MIMEText(f"\nDownload the zip file from Our Website: {link} \n ", 'plain'))
        msg.attach(MIMEText(f"\To Delete the zip file from Our Website: {remove} \n ", 'plain'))
        # Set up the SMTP server and send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('framethevideo@gmail.com', Password)
            server.send_message(msg)
            print(f"Email sent to {email}")
    except Exception as e:
        print(f"Failed to send email to \n {email}: {e}")