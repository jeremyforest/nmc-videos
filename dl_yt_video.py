from pytube import YouTube
import pandas as pd
# from youtube_dl import YoutubeDL  # to use as backup solution


def dl_yt_video(file_path='videos/data.csv', download=True):
    """Dowload video from youtube and save info locally to csv file.
    """
    # get list of yt links from stored df
    df = pd.read_csv(file_path)

    df_yt = pd.DataFrame(
        columns=['emails', 'title', 'thumbnail_url', 'description', 'caption',
                 'dl_status'])

    if 'dl_status' in df.columns:
        pass
    else:
        df = df.merge(df_yt, how='outer', on='emails')

    for email, yt_video in zip(df['emails'], df['youtube_url']):
        # email = df['emails'][0]
        # yt_video = df['youtube_url'][0]
        # check if already done
        if df[df.emails == email]['dl_status'].tolist()[0] == 'downloaded':
            print(
                f'{email}, {yt_video} already been downloaded for more info \
                see table at index {df[df.emails == email].index.tolist()}')
            continue
        else:
            # access video and getting info
            try:
                yt = YouTube(yt_video)
                title = yt.title
                thumbnail_url = yt.thumbnail_url
                try:
                    caption = yt.captions['en']  # TODO
                except:
                    caption = None
                    pass
                description = yt.description
                # to handle exceptions in titles for later processing by ffmpeg
                if '/' in title:
                    title = title.replace('/', '')
                if ',' in title:
                    title = title.replace(',', '')
                if '.' in title:
                    title = title.replace('.', '')
                if '?' in title:
                    title = title.replace('?', '')
                if ':' in title:
                    title = title.replace(':', '')
                if '|' in title:
                    title = title.replace('|', '')

                if download == True:  # allows to just generate the summary file if set to false
                    try:
                        # download video to folder videos/
                        yt.streams.filter(progressive=True, file_extension='mp4').order_by(
                            'resolution').desc().first().download('videos/')
                        print(f'video - {title} - download done')
                        dl_status = 'downloaded'
                    except:
                        dl_status = 'failed'
                        pass
                else:
                    dl_status = 'dowload=False in function settings'

            except:
                print(f'Video at {yt_video} is unavailable')
                title = 'Unaccessible video'
                thumbnail_url = 'Unaccessible video'
                caption = 'Unaccessible video'
                description = 'Unaccessible video'
                dl_status = 'Unaccessible video'
                pass

            df.loc[df.emails == email, 'title'] = title
            df.loc[df.emails == email, 'thumbnail_url'] = thumbnail_url
            df.loc[df.emails == email, 'description'] = description
            df.loc[df.emails == email, 'caption'] = caption
            df.loc[df.emails == email, 'dl_status'] = dl_status

    df.to_csv(file_path, index=False)


def dl_yt_video_alternate(yt_video):
    '''
    Started to code that as an alternative to PyTube when Youtube changed their
    code and Pytube stopped working just before the deadline for uploading
    videos. Leaving it here as a WIP alternative just in case we need it later.
    '''
    yt_dl = YoutubeDL()
    info = yt_dl.extract_info(url=yt_video, download=False)
    title = info.get('title')
    description = info.get('description')
    thumbnail_url = info.get('thumbnail')
    options = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'}
    YoutubeDL(options).download([yt_video])


if __name__ == '__main__':
    file_path = 'videos/data.csv'
    dl_yt_video(file_path)
