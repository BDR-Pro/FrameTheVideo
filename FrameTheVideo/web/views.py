from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import redirect
import os
from random import choice
from YT import download_one_video , yt_to_title
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.message import EmailMessage
from django.conf import settings

Password = settings.EMAIL_HOST_PASSWORD

def main(request):
    return render(request, 'main.html')

import os
import threading
from django.http import JsonResponse

def queue_in_background(video_id, output_folder, email):
    try:
        queue(video_id, output_folder, email)  
    except Exception as e:
        print(f"Error processing video {video_id}: {e}")

def frame_the_video(request):
    video_id = request.GET.get('v')
    if video_id:
        email = request.POST.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Email address is required'}, status=400)
        
        output_folder = 'output_folder'
        output_folder = os.path.join(os.path.dirname(__file__), output_folder)
        os.makedirs(output_folder, exist_ok=True)
        output_folder = os.path.abspath(output_folder)
        
        # Start the queue operation in a background thread
        thread = threading.Thread(target=queue_in_background, args=(video_id, output_folder, email))
        thread.start()

        return JsonResponse({'status': 'success', 
                             'message': 'Video is being processed. Please wait a few minutes you can close this tab and check your email inbox later.'},
                            status=200)
    else:
        return JsonResponse({'status': 'error', 'message': 'No video ID provided'}, status=400)


def return_title(request):
    video_id = request.GET.get('v')
    if video_id:
        title = yt_to_title(video_id)
        if title:
            return JsonResponse({'title': title})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to get title'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'No video ID provided'}, status=400)

def queue(video_id, output_folder,email):
    """download and process the video in the background and send email when done"""

    frame_skip = 50
    similarity_percentage = 65
    max_frames = 100
    
    zip_file_path = download_one_video(video_id, output_folder, frame_skip, similarity_percentage, max_frames)
    
            
    return send_email(email, zip_file_path)

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






def send_email(email, zip_file_path):
    """Send an email with the zip file attached.
    
    Args:
        email (str): The recipient's email address.
        zip_file_path (str): The path to the zip file to be attached.
    """
    # Create the email object
    msg = MIMEMultipart()
    msg['Subject'] = 'Your Requested Wallpaper (FrameTheVideo)'
    msg['From'] = 'framethevideo@gmail.com'
    msg['To'] = email

    # Set the body of the email
    msg.attach(EmailMessage("Hello, \n\nThank you for using FrameTheVideo! \n\nPlease find the attached zip file containing the wallpaper images extracted from the video you requested. \n\nEnjoy! \n\nBest regards, \nBader Alotaibi (BDR-PRO) Github ", 'plain'))

    # Attach the zip file
    with open(zip_file_path, 'rb') as file:
        part = MIMEApplication(file.read(), Name=zip_file_path)
    part['Content-Disposition'] = f'attachment; filename="{zip_file_path}"'
    msg.attach(part)

    # Set up the SMTP server and send the email
    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('framethevideo@gmail.com', Password)
        server.send_message(msg)
        print("Email sent successfully!")
