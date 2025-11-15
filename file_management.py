from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google.auth
import io
import os

'''
    download_files:从Google Drive下载所需文件（未完成）
'''
def set_proxy():
    #set proxy if in mainland China
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

def get_credentials(client_secret_path, scopes, token_cache="token.json"):
    """
    Obtains OAuth2 credentials for Google APIs.
    Not use in the final version for external security reason.
    Args:
        client_secret_path (str): Path to the client secret JSON file.
        scopes (list): List of scopes for which to request access.
        token_cache (str): Path to the token cache file.
    Returns:
        google.auth.credentials.Credentials: The obtained credentials.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists(token_cache):
        creds = Credentials.from_authorized_user_file(token_cache, scopes)[0]
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_path, scopes, redirect_uri="http://localhost:8080/"
            )
            creds = flow.run_local_server(port=8080)
        with open(token_cache, "w") as f:
            f.write(creds.to_json())
    return creds

def list_drive_files(service, page_size=10, folder_id=None, show_all=False):
    """
    gets file list from Google Drive and print file info.
    
    Args:
        service: Drive API service instance
        page_size: file number per page (10 by default)
        folder_id: optional, only list files in this folder
        show_all: if show all files, default False (only first page)
    Return:
        file list 
    """
    all_files = []
    page_token = None  # page token for pagination
    
    # construct query string
    query = ["trashed = false"]
    if folder_id:
        query.append(f"'{folder_id}' in parents")  
    query_str = " and ".join(query)
    
    print(f"start to fetch file list({page_size} files per page)\n")
    while True:
        # get file list by Drive API
        results = service.files().list(
            q=query_str,
            pageSize=page_size,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)" 
        ).execute()
        
        items = results.get("files", [])
        all_files.extend(items)
        
        # print file info
        for i, item in enumerate(items, len(all_files) - len(items) + 1):

            print(
                f"{i}. name: {item['name']}\n"
                f"   ID: {item['id']}\n"
                f"   Type: {item['mimeType']}\n"
                f"   ModifiedTime: {item['modifiedTime']}\n"
            )
        
        # check for next page
        page_token = results.get("nextPageToken")
        if not page_token or not show_all:
            break  # exit loop if no more pages or not showing all
    
    total = len(all_files)
    print(f"fetch {total} files totally")
    return all_files

def search_file_id(service, filename, folder_id=None, exact_match=False):
    """
    search file ID(s) by filename in Google Drive.
    
    Args:
        service: Drive API service instance
        filename: file name to search
        folder_id: folder ID to limit search (optional)
        exact_match: whether to match filename exactly (default False)
    Returns:
        ids of matched files
    """
    # construct query string（https://developers.google.com/drive/api/v3/search-files）
    query = []
    # match filename condition
    if exact_match:
        query.append(f"name = '{filename}'")  
    else:
        query.append(f"name contains '{filename}'") 
    # exclude trashed files
    query.append("trashed = false")
    # constrain to specific folder
    if folder_id:
        query.append(f"'{folder_id}' in parents")
    
    
    query_str = " and ".join(query)
    
    # use Drive API to search files
    results = service.files().list(
        q=query_str,
        fields="nextPageToken, files(id, name, mimeType, modifiedTime)"  
    ).execute()
    
    items = results.get("files", [])
    if not items:
        print(f"cannot find matching files(filename: {filename})")
        return []
    
    # 打印搜索结果（供用户选择）
    print(f"\nfound {len(items)} matching files for '{filename}':")
    for i, item in enumerate(items, 1):
        print(f"{i}. name: {item['name']} | ID: {item['id']} | Type:{item['mimeType']} | ModifiedTime: {item['modifiedTime']}")
    
    return [item["id"] for item in items]

def download_file_by_id(service,file_id, save_path):
    try:
        file_metadata = service.files().get(fileId=file_id).execute()
        print(f"start to load{file_metadata['name']}")
        
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(save_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"download progress: {int(status.progress() * 100)}%")
        
        print(f"save to{save_path}")
    except Exception as e:
        print(f"failed: {str(e)}")

def download_files():
    '''
    download needed files from Google Drive.
    '''
    credentials = get_credentials(
        'client_secret_935968549547-63lg10icuv1p6vr61or7s34nsaj78dmq.apps.googleusercontent.com.json',
        scopes=['https://www.googleapis.com/auth/drive.readonly']  # read-only access
    )

    service = build('drive', 'v3', credentials=credentials)
    save_path = ""

    

if __name__ == "__main__":
    #example usage
    set_proxy()#set proxy if needed
    credentials = get_credentials(
        'client_secret_935968549547-63lg10icuv1p6vr61or7s34nsaj78dmq.apps.googleusercontent.com.json',
        scopes=['https://www.googleapis.com/auth/drive.readonly']  # read-only access
    )

    service = build('drive', 'v3', credentials=credentials)
    list_drive_files(service, page_size=10, show_all=True)