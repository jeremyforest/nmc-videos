from cut_videos import cut_videos

from airtable import Airtable
import datetime
import dotenv
import os


def pad(x):
    if x is not None:
        return x + datetime.timedelta(seconds=4)


def to_timedelta(ts):
    if (ts[0] == '-') or ('x' in ts.lower()):
        return None

    parts = ts.split(':')
    multiplier = datetime.timedelta(seconds=1)
    delta = datetime.timedelta()
    for p in parts[::-1]:
        delta += int(p) * multiplier
        multiplier = multiplier * 60
    return delta


if __name__ == '__main__':
    dotenv.load_dotenv()
    at = Airtable(os.getenv("AT_APP_KEY_ORANGE"),
                  "Session hosting",
                  os.getenv("AT_API_KEY"))

    for row in at.get_all():
        print(row)
        if (('ts0_end' not in row['fields']) or
            ('ts1_end' not in row['fields']) or
                ('ts2_end' not in row['fields'])):
            # Not annotated yet
            continue

        if 'manual_edit' in row['fields'] and row['fields']['manual_edit']:
            continue

        cuts = [(to_timedelta(row['fields']['ts0_start']),
                 pad(to_timedelta(row['fields']['ts0_end']))),
                (to_timedelta(row['fields']['ts1_start']),
                 pad(to_timedelta(row['fields']['ts1_end']))),
                (to_timedelta(row['fields']['ts2_start']),
                 pad(to_timedelta(row['fields']['ts2_end'])))]

        print(cuts)
        if cuts[0][0] is None and cuts[1][0] is None and cuts[2][0] is None:
            continue

        webinar = '9' + row['fields']['zoom_link'].split('/j/9')[-1][:10]

        # Check whether we have the timestamps ready for this one.
        print(webinar)

        input_video = f'/mnt/d/videos/{webinar}.mp4'

        assert os.path.exists(input_video)

        splash_screen = '/mnt/d/NMC_IntroVid_Final.mp4'

        if (os.path.exists(f'/mnt/d/cut_videos/{webinar}_0_out.mp4') or
            os.path.exists(f'/mnt/d/cut_videos/{webinar}_1_out.mp4') or
            os.path.exists(f'/mnt/d/cut_videos/{webinar}_2_out.mp4') or
            os.path.exists(f'/mnt/d/cut_videos/uploaded/{webinar}_0_out.mp4') or
            os.path.exists(f'/mnt/d/cut_videos/uploaded/{webinar}_1_out.mp4') or
            os.path.exists(f'/mnt/d/cut_videos/uploaded/{webinar}_2_out.mp4') or
            os.path.exists(f'/mnt/d/cut_videos/to_upload/{webinar}_0_out.mp4') or
            os.path.exists(f'/mnt/d/cut_videos/to_upload/{webinar}_1_out.mp4') or
                os.path.exists(f'/mnt/d/cut_videos/to_upload/{webinar}_2_out.mp4')):
            print(f"Skipping file {webinar}")
            continue

        cut_videos(input_video, '/mnt/d/cut_videos', splash_screen, cuts)
