import dotenv
import os
from pyairtable import Table
import pandas as pd


def load_airtable(key, base_id, table_name):
    at = Table(key, base_id, table_name)
    return at


def get_info(airtable_tab):
    yt_links, emails = [], []

    for record in range(len(airtable_tab.all())):
        talk = airtable_tab.all()[record]
        yt_link = talk.get('fields').get('youtube_url')
        email = talk.get('fields').get('email')
        yt_links.append(yt_link)
        emails.append(email)
    return yt_links, emails


def save_to_df(yt_links, emails):
    df = pd.DataFrame({'emails': emails,
                       'youtube_url': yt_links})
    # people can submit multiple times and with different videos - keep the
    # last one only
    df.drop_duplicates(keep='last', inplace=True)
    df.to_csv('videos/data.csv', index=False)


def update_df(yt_links, emails):
    file_path = 'videos/data.csv'
    df = pd.read_csv(file_path)

    df_new = pd.DataFrame({'emails': emails,
                           'youtube_url': yt_links})
    df_new.drop_duplicates(keep='last', inplace=True)

    df = pd.merge(df, df_new, how='right')
    df.to_csv('videos/data.csv', index=False)


if __name__ == '__main__':
    dotenv.load_dotenv()
    AT_BASE_ID = os.getenv('AT_BASE_ID')
    AT_API_KEY = os.getenv('AT_API_KEY')
    TABLE_NAME = 'uploads'
    upload_tab = load_airtable(AT_API_KEY, AT_BASE_ID, TABLE_NAME)
    yt_links, emails = get_info(upload_tab)
    if os.path.exists('videos/data.csv'):
        update_df(yt_links, emails)
    else:
        save_to_df(yt_links, emails)
