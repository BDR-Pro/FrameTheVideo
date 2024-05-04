from django.shortcuts import render
from django.http import JsonResponse, FileResponse

import os
from random import choice
from YT import download_one_video , yt_to_title


def main(request):
    return render(request, 'main.html')

def frame_the_video(request):
    video_id = request.GET.get('v')
    if video_id:
        try:
            
            output_folder = 'output_folder'
            output_folder = os.path.join(os.path.dirname(__file__), output_folder)
            os.makedirs(output_folder, exist_ok=True)
            
            frame_skip = 50
            similarity_percentage = 65
            max_frames = 100
            
            zip_file_path = download_one_video(video_id, output_folder, frame_skip, similarity_percentage, max_frames)
            
            if zip_file_path and os.path.exists(zip_file_path):
                
                
                
                zip_file = open(zip_file_path, 'rb')
                response = FileResponse(zip_file, as_attachment=True, content_type='application/zip', filename=os.path.basename(zip_file_path))
                response['Content-Length'] = os.path.getsize(zip_file_path)
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(zip_file_path)}"'
                response['Content-Type'] = 'application/zip'
                
                
                return response
            
            else:
                
                return JsonResponse({'status': 'error', 'message': 'File not found'}, status=404)
            
        except Exception as e:
            
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
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


