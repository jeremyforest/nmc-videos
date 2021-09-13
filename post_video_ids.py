from airtable import Airtable
import dotenv
import json
import os
from pprint import pprint
import requests

def get_auth_header(access_token):
    return {'content-type': "application/json",
            'authorization': f"Bearer {access_token}"}

def refresh_token():
    """Refresh the OAuth token"""
    with open(".tokens") as f:
        token = json.load(f)
    
    endpoint = f"https://accounts.google.com/o/oauth2/token"
    payload = {"client_id": os.getenv("GOOGLE_CLIENT_ID"),
               "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
               "refresh_token": token['refresh_token'],
               "grant_type": "refresh_token",
               }

    result = requests.request("POST", endpoint, data=payload)

    if result.status_code == 200:
        try:
            body = result.json()
            with open('.tokens', 'w') as f:
                body['refresh_token'] = token['refresh_token']
                json.dump(body, f)
            return body['access_token']
        except:
            raise Exception("Response is not parseable")
    else:
        print(result)
        print(result.text)
        raise Exception("Did not get a 200 response upon refreshing token.")


def list_videos(playlist_id, access_token):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    url += f'?key={os.getenv("GOOGLE_API_KEY")}'
    url += f'&part=id,snippet,status,contentDetails'
    url += f'&playlistId={playlist_id}'
    url += f'&maxResults=50'
    
    next_page_token = ""

    items = []
    while 1:
        response = requests.get(url + next_page_token, headers=get_auth_header(access_token))
        results = response.json()
        items += results['items']
        if 'nextPageToken' in results:
            next_page_token = f"&pageToken={results['nextPageToken']}"
        else:
            return items

def find_video_by_title(title, videos):
    for video in videos:
        if video['snippet']['title'] == title:
            return video['contentDetails']['videoId']

def post_video_ids(videos):
    at = Airtable(os.getenv('AT_APP_KEY_ORANGE'), 
                  'Session hosting',
                  os.getenv('AT_API_KEY'))

    for row in at.get_all():
        updates = {}
        submissions = row['fields']['submission_ids'].split(', ')

        webinar = '9' + row['fields']['zoom_link'].split('/j/9')[-1][:10]

        for num in range(len(submissions)):
            if f'videoid_{num}' not in row['fields']:
                video = find_video_by_title(f'{webinar} {num} out', videos)
                if video is not None:
                    updates[f'videoid_{num}'] = video
            else:
                print(f"There is already an id for this one :")
                print(row['fields'][f'videoid_{num}'])
                
        if updates:
            print('Updating')
            print(updates)
            at.update(row['id'], updates)

if __name__ == "__main__":
    dotenv.load_dotenv()

    playlist_id = 'PL8rU-NsQ9kf268CuUATNXymhb4F9Ys9r8'

    access_token = refresh_token()
    videos = list_videos(playlist_id, access_token)
    post_video_ids(videos)
