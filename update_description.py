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

def cutoff(title, chars):
    if len(title) > chars:
        return title[:chars-1] + '…'
    else:
        return title

def generate_title(info):
    if 'Keynote' in info['talk_format']:
        title = 'Keynote: '
    elif 'Special' in info['talk_format']:
        title = 'Special event: '
    else:
        title = 'Talk: '

    return cutoff(title + info['title'], 100)


def generate_description(info):
    if 'fullname' in info and 'institution' in info:
        speaker = f"Speaker: {info['fullname']}, {info['institution']}"
    elif 'fullname' in info:
        speaker = f"Speaker: {info['fullname']}"
    else:
        speaker = f""

    lines = info['extra_info'].split('\n')
    legit_lines = []
    for line in lines:
        parts = line.split(':')
        if len(parts) >= 2 and parts[1].strip():
            line = line.strip()
            if line[0] in ('*-'):
                line = line[1:].strip()

            line = line[0].upper() + line[1:]
            legit_lines.append(line)

    if info['Name (from emcee)'][0] == "External emcee":
        emcee = ""
    else:
        emcee = f"Emcee: {info['Name (from emcee)'][0]}"

    if 'abstract' in info:
        summary = f"Summary: {info['abstract']}"
    else:
        summary = ""

    extra_info = '\n'.join(legit_lines)

    template = (
f"""{speaker}
Title: {info['title']}
{emcee}
Backend host: {info['Name (from backend)'][0]}
Details: https://neuromatch.io/abstract?submission_id={info['submission_id']}
{extra_info}
Presented during Neuromatch Conference 3.0, Oct 26-30, 2020. 

{summary}
""")

    return cutoff(template, 2900).replace('<', '＜').replace('>', '＞')


def checked(column, fields):
    return ((column in fields) and fields[column])

def gather_video_descriptions():
    at_orange = Airtable(os.getenv('AT_APP_KEY_ORANGE'), 
                  'Session hosting',
                  os.getenv('AT_API_KEY'))

    at_optin = Airtable(os.getenv('AT_APP_KEY_ORANGE'), 
                  'optin',
                  os.getenv('AT_API_KEY'))

    at_gray = Airtable(os.getenv('AT_APP_KEY_GRAY'), 
                  'submissions',
                  os.getenv('AT_API_KEY'))

    payloads = []
    for row in at_orange.get_all():
        submission_ids = row['fields']['submission_ids'].split(', ')
        for num, submission_id in enumerate(submission_ids):
            col = f'videoid_{num}'
            if col not in row['fields']:
                continue

            if checked(f'posted_{num}', row['fields']):
                # No use in reposting the information
                continue

            matches = at_optin.search('submission_id', submission_id)
            yes = 'I want my presentation video posted to YouTube'
            if not all([match['fields']['choice'] == yes for match in matches]) or len(matches) == 0 and (not checked('manually_approved', row['fields'])):
                # Not yet approved to send out
                continue

            extended_info = at_gray.match('submission_id', submission_id)
            all_info = {**row['fields'], **extended_info['fields']}
            
            if f'extra_info_{num}' in all_info:
                all_info['extra_info'] = all_info[f'extra_info_{num}']
            else:
                all_info['extra_info'] = ""

            print(all_info['extra_info'])

            payload = {
                'id': row['fields'][col],
                'snippet': {
                    'title': generate_title(all_info),  # Max 100 characters
                    'description': generate_description(all_info),  # Max 5000 bytes
                    'categoryId': "28",
                    'defaultLanguage': 'en',
                },
                'status': {
                    'embeddable': True,
                    'license': 'youtube',
                    'privacyStatus': 'public',
                    'publicStatsViewable': True,
                    'selfDeclaredMadeForKids': False,
                },
                'recordingDetails': {
                    'recordingDate': all_info['starttime']
                }
            }

            payloads.append(payload)
    return payloads

def update_video_descriptions(payloads, access_token):
    for payload in payloads:
        url = "https://youtube.googleapis.com/youtube/v3/videos"
        #url += f'?key={os.getenv("GOOGLE_API_KEY")}'
        url += f'?part=snippet,status,recordingDetails'

        pprint(payload)
        response = requests.put(url, json=payload, headers=get_auth_header(access_token))
        assert response.status_code == 200


def mark_posted():
    at_orange = Airtable(os.getenv('AT_APP_KEY_ORANGE'), 
                  'Session hosting',
                  os.getenv('AT_API_KEY'))

    for row in at_orange.get_all():
        for num in range(3):
            col = f'videoid_{num}'
            if col in row['fields']:
                if checked(f'posted_{num}', row['fields']):
                    continue
                url = "https://youtube.googleapis.com/youtube/v3/videos"
                url += f'?part=snippet,status,recordingDetails'
                url += f"&id={row['fields'][col]}"

                response = requests.get(url, headers=get_auth_header(access_token))
                assert response.status_code == 200

                body = response.json()

                assert len(body['items']) == 1
                item = body['items'][0]

                if item['status']['privacyStatus'] == 'public':
                    at_orange.update(row['id'], {f'posted_{num}': True})


if __name__ == "__main__":
    dotenv.load_dotenv()
    playlist_id = 'PL8rU-NsQ9kf268CuUATNXymhb4F9Ys9r8'

    access_token = refresh_token()
    mark_posted()
    payloads = gather_video_descriptions()
    pprint(payloads)
    print(len(payloads))
    update_video_descriptions(payloads, access_token)
    mark_posted()
    
