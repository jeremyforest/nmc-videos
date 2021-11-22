import httplib2
import os
import sys

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow

CLIENT_SECRETS_FILE = "client_secrets.json"
MISSING_CLIENT_SECRETS_MESSAGE = "Missing client secrets file"
YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def get_authenticated_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def add_video_to_playlist(youtube, videoID, playlistID):
    youtube.playlistItems().insert(
        part="snippet",
        body={
            'snippet': {
                'playlistId': playlistID,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': videoID
                }
            }
        }
    ).execute()


if __name__ == '__main__':

    import pandas as pd
    df = pd.read_csv('videos/data.csv')

    if 'updated_to_playlist' in df.columns:
        pass
    else:
        df['updated_to_playlist'] = None

    # update to the right playlist
    playlist_id = 'PL8rU-NsQ9kf1wYm9Ir_oGpFrXUM_EVUVl'  # NMC4 playlist
    youtube = get_authenticated_service()

    for row_nb in range(df.shape[0]):
        if df.loc[row_nb, 'updated_to_playlist'] == 'updated_to_playlist':
            pass
        else:
            try:
                df.iloc[row_nb, :].response_id
                add_video_to_playlist(youtube, response_id, playlist_id)
                df.loc[row_nb, 'updated_to_playlist'] = 'updated_to_playlist'
            except:
                df.loc[row_nb, 'updated_to_playlist'] = 'failed'
                pass
    df.to_csv('videos/data.csv', index=False)
