import threading
import time

from file_management import download_files

"""
    start_download_thread:启动周期性更新器
"""
def periodic_updater(analysis_data):
    while True:
        try:
           
            if  download_files(True):
            
                analysis_data.update_data()
                print("data updated")
            print("no change")
        except Exception as e:
            print(f"Error in loop: {e}")
        
        
        time.sleep(60)

def start_download_thread(analysis_data):
    t = threading.Thread(target=periodic_updater,kwargs={
        "analysis_data": analysis_data
    })
    t.daemon = True 
    t.start()


    
