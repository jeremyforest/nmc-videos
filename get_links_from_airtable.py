import dotenv
import os
from pyairtable import Table
import pandas as pd


class Airtable:
    def __init__(self, key:str, base_id:str):
        self.key = key
        self.base_id = base_id


    def load_specific_table(self, table_name:str):
        """Load the specified airtable base using your key
        """
        return Table(key=self.key, base_id=self.base_id, table_name=table_name)


    def get_info(self, airtable_tab:str, infos:dict):
        """Get the info you want from the specified airtable tab
        """
        for record in range(len(airtable_tab.all())):
            talk = airtable_tab.all()[record]
            video_link = talk.get('fields').get(f'{url_col_name}')
            email = talk.get('fields').get(f'{email_col_name}')
            video_links.append(video_link)
            emails.append(email)
        return video_links, emails


    def save_to_df(self, video_links, emails):
        """
        Save the minimal needed data of interest to be able to download the video and then later associate emails with
        youtube urls and IDs
        """
        df = pd.DataFrame({'emails': emails,
                           'video_url': video_links})
        # people can submit multiple times and with different videos - keep the
        # last one only
        df.drop_duplicates(keep='last', inplace=True)
        df.to_csv('videos/data.csv', index=False)


    def update_df(self, video_links, emails):
        """
        Sometimes the data from airtable get updated with late submissions and such after you already have started
        processing. This allows to update the local df file.
        """
        file_path = 'videos/data.csv'
        df = pd.read_csv(file_path)

        df_new = pd.DataFrame({'emails': emails,
                               'video_url': video_links})
        df_new.drop_duplicates(keep='last', inplace=True)

        df = pd.merge(df, df_new, how='right')
        df.to_csv('videos/data.csv', index=False)


if __name__ == '__main__':
    dotenv.load_dotenv()
    AT_BASE_ID = os.getenv('AT_BASE_ID')
    AT_API_KEY = os.getenv('AT_API_KEY')
    TABLE_NAME = 'uploads_2022'

    airtable = Airtable()
    upload_tupab = airtable.load_airtable(key=AT_API_KEY, base_id=AT_BASE_ID, table_name=TABLE_NAME)
    video_links, emails = airtable.get_info(upload_tab, 'email', ' WWN_AWS_URL ')
    if os.path.exists('videos/data.csv'):
        airtable.update_df(video_links, emails)
    else:
        airtable.save_to_df(video_links, emails)
