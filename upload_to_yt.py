#!/usr/bin/python

import http.client
import httplib2
import os
import random
import sys
import time
import pandas as pd
from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError,
                        http.client.NotConnected, http.client.IncompleteRead,
                        http.client.ImproperConnectionState,
                        http.client.CannotSendRequest,
                        http.client.CannotSendHeader,
                        http.client.ResponseNotReady,
                        http.client.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = "client_secrets.json"
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
MISSING_CLIENT_SECRETS_MESSAGE = "missing client secret file"
VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def get_authenticated_service(data):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, data)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def initialize_upload(youtube, data):
    tags = None
    if data['keywords']:
        tags = data['keywords'].split(",")

    body = dict(
        snippet=dict(
            title=data['title'],
            description=data['description'],
            tags=tags,
            categoryId=data['category']
        ),
        status=dict(
            privacyStatus=data['privacyStatus']
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(list(body.keys())),
        body=body,
        media_body=MediaFileUpload(data['file'], chunksize=-1, resumable=True)
    )

    response_id = resumable_upload(insert_request)
    return response_id


def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    response_id = response['id']
                    print("Video id '%s' was successfully uploaded." %
                          response['id'])
                else:
                    exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                     e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)
    return response_id


def upload(file, title, description, category, keywords, privacyStatus):

    data = {
        'auth_host_name': 'localhost',
        'noauth_local_webserver': False,
        'auth_host_port': [8080, 8090],
        'logging_level': 'ERROR',
        'file': file,
        'title': title,
        'description': description,
        'category': category,
        'keywords': keywords,
        'privacyStatus': privacyStatus
    }

    if not os.path.exists(data['file']):
        exit("Please specify a valid file path")

    youtube = get_authenticated_service(data)
    try:
        response_id = initialize_upload(youtube, data)
    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
    return response_id


def get_videos_details_and_upload(df):
    if 'upload' in df.columns:
        pass
    else:
        df['upload'] = None

    if 'response_id' in df.columns:
        pass
    else:
        df['response_id'] = None

    for row_nb in range(df.shape[0]):
        if df.loc[row_nb, 'upload'] == 'uploaded':
            pass
        else:
            try:
                title = df.iloc[row_nb, :].title
                file = f'videos/{title}_0_out.mp4'
                description = df.iloc[row_nb, :].description
                if pd.isna(df.iloc[row_nb, :].description):
                    description = 'None'
                category = '28'  # Science & Technology
                keywords = 'NMC4, Neuromatch Conference 4'
                privacyStatus = 'private'
                response_id = upload(file, title, description,
                                     category, keywords, privacyStatus)
                df.loc[row_nb, 'upload'] = 'uploaded'
                df.loc[row_nb, 'response_id'] = response_id
            except:
                df.loc[row_nb, 'upload'] = 'failed upload'
                pass

    df.to_csv('videos/data.csv', index=False)


if __name__ == '__main__':
    df = pd.read_csv('videos/data.csv')
    get_videos_details_and_upload(df)
