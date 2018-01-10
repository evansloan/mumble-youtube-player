import os

import pafy
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials as SAC

CLIENT_SECRETS_FILE = 'config/service_client.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


def get_authenticated_service():
    credentials = SAC.from_json_keyfile_name(CLIENT_SECRETS_FILE, SCOPES)
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def get_video_title(video_id):
    client = get_authenticated_service()
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    response = client.videos().list(part='snippet', id=video_id).execute()
    return response['items'][0]['snippet']['title']


def get_video_id(video_title):
    client = get_authenticated_service()
    response = client.search().list(
        part='snippet', maxResults=10, q=video_title, type=''
    ).execute()
    return response['items'][0]['id']['videoId']


def get_audio_stream(link):
    url = f'https://www.youtube.com/watch?v={link}'
    video = pafy.new(url, ydl_opts={'nocheckcertificate': True})
    audiostream = video.getbestaudio()
    command = ['ffmpeg', '-v', 'warning', '-nostdin', '-i', audiostream.url, '-ac', '1', '-f', 's16le', '-ar', '48000', '-']
    return command
