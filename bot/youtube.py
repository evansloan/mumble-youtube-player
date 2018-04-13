import os

import pafy
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials as SAC

CLIENT_SECRETS_FILE = 'config/service_client.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


def get_authenticated_service():
    secrets_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__,))), CLIENT_SECRETS_FILE)
    credentials = SAC.from_json_keyfile_name(secrets_path, SCOPES)
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def get_video_id(video_title):
    client = get_authenticated_service()
    response = client.search().list(
        part='snippet', maxResults=1, q=video_title, type=''
    ).execute()
    return response['items'][0]['id']['videoId']


class YTStream:
    def __init__(self, url):
        self.video = pafy.new(url, ydl_opts={'nocheckcertificate': True})
        self.duration = self.video.duration
        self.title = self.video.title
        self.video_id = self.video.videoid
        self.video_url = f'https://www.youtube.com/watch?v={self.video_id}'

    @property
    def audio(self):
        audio = self.video.getbestaudio()
        return ['ffmpeg', '-v', 'warning', '-nostdin', '-i', audio.url, '-ac', '1', '-f', 's16le', '-ar', '48000', '-']
