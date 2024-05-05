import schedule
import shutil
import os 

def remove_output_folder():
    output_folder = 'output_folder'
    output_folder = os.path.join(os.path.dirname(__file__), output_folder)
    shutil.rmtree(output_folder)

# Schedule the task to run daily at a specific time
schedule.every().day.at("12:00").do(remove_output_folder)

# Keep the schedule running
while True:
    schedule.run_pending()
    
    
