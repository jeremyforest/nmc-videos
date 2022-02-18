from get_yt_links_from_airtable import get_info, load_airtable, save_to_df
from dl_yt_video import dl_yt_video
from upload_to_yt import get_videos_details_and_upload
from cut_videos import cut_videos
from update_playlist import get_authenticated_service, add_video_to_playlist
import dotenv
import os
import pandas as pd


class NMC4:
    def __init__(self):
        dotenv.load_dotenv()
        self.AT_BASE_ID = os.getenv('AT_BASE_ID')
        self.AT_API_KEY = os.getenv('AT_API_KEY')
        self.AIRTABLE_TABLE_NAME = 'uploads'
        self.data_file_path = 'videos/data.csv'

    def run(self):
        # get yt video links from airtable
        if os.path.exists(self.data_file_path):
            pass
        else:
            airtable = load_airtable(self.AT_API_KEY,
                                     self.AT_BASE_ID, self.AIRTABLE_TABLE_NAME)
            yt_links, emails = get_info(airtable)
            save_to_df(yt_links, emails)

        # download yt videos locally and save related info in csv file
        dl_yt_video(self.data_file_path)

        # splice in the splash screen
        df = pd.read_csv(self.data_file_path)
        titles = df.title.tolist()

        if 'processing_status' in df.columns:
            pass
        else:
            df['processing_status'] = None

        for title in titles:
            input_video = f'videos/{title}.mp4'
            splash_screen = 'videos/NMC4_splashscreen.mkv'
            cuts = None
            path = 'videos'
            try:
                cut_videos(input_video, path, splash_screen, cuts)
                processing_status = 'success'
            except:
                print("------\n\nfailed\n\n--------")
                processing_status = 'failed'
                pass
            df.loc[df.title == title, 'processing_status'] = processing_status
        df.to_csv(self.data_file_path)

        # upload to youtube
        # get_videos_details_and_upload(df)  # upload to nma channel.

        # update to the right playlist
        # playlist_id = 'PL8rU-NsQ9kf1wYm9Ir_oGpFrXUM_EVUVl'  # NMC4 playlist
        # youtube = get_authenticated_service()
        # for response_id in df.response_id:
        #     add_video_to_playlist(youtube, response_id, playlist_id)


if __name__ == '__main__':
    nmc4 = NMC4()
    nmc4.run()
