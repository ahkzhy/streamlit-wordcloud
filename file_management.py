


import io


def download_file_from_google(service,file_id, save_path):
    # request = service.files().get_media(fileId=file_id)
    # file_handle = io.BytesIO()  # 内存缓冲区
    # downloader = MediaIoBaseDownload(file_handle, request)

    # done = False
    # while not done:
    #     status, done = downloader.next_chunk()
    #     print(f"download：{int(status.progress() * 100)}%")
    print("code not completed yet")

def download_files():
    # credentials = service_account.Credentials.from_service_account_file(
    #     'your_credentials.json',
    #     scopes=['https://www.googleapis.com/auth/drive.readonly']  # read-only access
    # )

    # service = build('drive', 'v3', credentials=credentials)
    file_id = ""
    save_path = ""

    download_file_from_google(file_id, save_path)