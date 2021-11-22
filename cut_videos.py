import datetime
import ffmpeg
import os
import subprocess


def get_video_info(path):
    probe = ffmpeg.probe(path)

    for stream in probe["streams"]:
        if stream["codec_type"] == "video":
            return stream


def to_timestamp(timedelta):
    seconds = int(timedelta / datetime.timedelta(seconds=1))

    if seconds > 3600:
        return f"{seconds // 3600:02}:{((seconds // 60) % 60):02}:{seconds % 60:02}"
    else:
        return f"{seconds // 60:02}:{seconds % 60:02}"


def cut_videos(input_video, path, splash_screen, cuts):
    print(
        f'\n\n------------------{input_video}------------------------------')

    _, filename = os.path.split(input_video)
    filebase, ext = os.path.splitext(filename)
    assert ext == '.mp4'

    info = get_video_info(splash_screen)
    # w, h = info['coded_width'], info['coded_height']
    w, h = info['width'], info['height']

    if cuts == None:  # basically just add the splash screen
        metadata = ffmpeg.probe(input_video)
        length = float(metadata['streams'][0]['duration'])
        start_time = datetime.timedelta(minutes=0, seconds=0)
        end_time = datetime.timedelta(minutes=0, seconds=length)
        cuts = [(start_time, end_time)]

    for i, (start_time, end_time) in enumerate(cuts):
        if start_time is None:
            continue
        start_ts = to_timestamp(start_time)
        delta = end_time - start_time
        delta_ts = to_timestamp(delta)

        # Cut up the video.
        cmd = (f'ffmpeg -ss {start_ts} -i "{input_video}" '
               f'-to {delta_ts} -c copy "{path}/{filebase}_cut_{i}.mp4" -y')

        os.system(cmd)

        # Extract audio
        cmd = (
            f'ffmpeg -i "{path}/{filebase}_cut_{i}.mp4" "{path}/{filebase}_cut_{i}.wav"')
        os.system(cmd)

        # Normalize the volume.
        os.system(f'ffmpeg-normalize "{path}/{filebase}_cut_{i}.wav" '
                  f'-o "{path}/{filebase}_norm_{i}.wav" -ext wav -f '
                  f'-e "-max_muxing_queue_size 1024"')

        info = get_video_info(f'{path}/{filebase}_cut_{i}.mp4')
        # aspect_ratio = info['coded_width'] / info['coded_height']
        aspect_ratio = info['width'] / info['height']

        # Assemble the video from the splash screen and the volume normalized
        # audio, with a fadein of the cropped video.
        intro = ffmpeg.input(splash_screen)

        cropped_vid = ffmpeg.input(f'{path}/{filebase}_cut_{i}.mp4')
        norm_audio = ffmpeg.input(f'{path}/{filebase}_norm_{i}.wav')

        if abs(round(h * aspect_ratio) - w) / w < .01:
            # This is the perfect aspect ratio.
            # Wide format
            print("Correct aspect ratio")

            video = ffmpeg.concat(
                intro,
                cropped_vid.filter('scale', w, h)
                # .filter('fade', 'in', start_time=0, duration=3)
                           .filter('fade', 'out', start_time=delta / datetime.timedelta(seconds=1) - 3, duration=3),
                v=1, a=0)
        elif aspect_ratio <= w / h:
            # Narrow format
            print("Narrow format")
            width = int(round(h*aspect_ratio))

            video = ffmpeg.concat(
                intro.crop(int(round((w - width) / 2)), 0, width, h),
                cropped_vid.filter('scale', -1, h)
                # .filter('fade', 'in', start_time=0, duration=3)
                           .filter('fade', 'out', start_time=delta / datetime.timedelta(seconds=1) - 3, duration=3),
                v=1, a=0)
        else:
            # Wide format
            print("Wide format")
            height = int(round(w / aspect_ratio))

            video = ffmpeg.concat(
                intro.crop(0, int(round((h - height) / 2)), w, height),
                cropped_vid.filter('scale', w, -1)
                # .filter('fade', 'in', start_time=0, duration=3)
                           .filter('fade', 'out', start_time=delta / datetime.timedelta(seconds=1) - 3, duration=3),
                v=1, a=0)

        audio = ffmpeg.concat(
            intro,
            # norm_audio.filter('afade', 'in', start_time=0, duration=1)
            norm_audio.filter(
                'afade', 'out', start_time=delta / datetime.timedelta(seconds=1) - 2, duration=2),
            v=0, a=1)

        out = f'{path}/{filebase}_{i}_out.mp4'
        args = ffmpeg.output(video, audio, out).compile(
            overwrite_output=True)

        # Extra parameters for dealing with AAC codec and HW accel.
        args = (args[:5] + ['-strict', 'experimental'] +
                args[5:] + ['-y', '-hwaccel', 'cuda', '-c:a', 'aac'])

        stdin_stream = None
        stdout_stream = None
        stderr_stream = None
        process = subprocess.Popen(
            args, stdin=stdin_stream, stdout=stdout_stream, stderr=stderr_stream
        )
        process.args
        out, err = process.communicate(None)
        if err:
            raise Exception(err)
            print('----- \n error \n -----')

        retcode = process.poll()
        print(retcode)

        os.remove(f"{path}/{filebase}_cut_{i}.mp4")
        os.remove(f"{path}/{filebase}_cut_{i}.wav")
        os.remove(f"{path}/{filebase}_norm_{i}.wav")

        if retcode == 1:
            processing_status = 'failed'
        else:
            processing_status = 'success'

    return processing_status


if __name__ == '__main__':

    # Show how to splice a video, normalize the audio and add a splash screen.
    import pandas as pd

    data_file_path = 'videos/data.csv'
    df = pd.read_csv(data_file_path)
    titles = df.title.tolist()

    if 'processing_status' in df.columns:
        pass
    else:
        df['processing_status'] = None

    # titles = [
    #     'Flash Talk A unique signaling feature for bursts in the visual cortex']

    for title in titles:
        try:
            if df[df.title == title]['processing_status'].tolist()[0] == 'success':
                print(
                    f'{title} has already been processed')
                continue
            else:
                input_video = f'videos/{title}.mp4'
                splash_screen = 'videos/NMC4_splashscreen.mkv'
                cuts = None
                path = 'videos'

                processing_status = cut_videos(
                    input_video, path, splash_screen, cuts)
                if processing_status == 'failed':
                    print("------\n\nfailed\n\n--------")
                df.loc[df.title == title,
                       'processing_status'] = processing_status
        except:
            processing_status = 'failed'
            df.loc[df.title == title,
                   'processing_status'] = processing_status
            pass
    df.to_csv(data_file_path, index=False)

    '''
    ffmpeg -i 'videos/NMC4_splashscreen.mkv' \
    -i 'videos/Modeling the Temporal Dynamic of Neurons in the IT cortex_cut_0.mp4' -strict experimental \
    -i 'videos/Modeling the Temporal Dynamic of Neurons in the IT cortex_norm_0.wav' -filter_complex \
    [0]crop=1920:927:0:76[s0];[1]scale=1920:-1[s1];[s1]fade=out:duration=3:start_time=425.92[s2];[s0][s2]concat=a=0:n=2:v=1[s3];[2]afade=out:duration=2:start_time=426.92[s4];[0][s4]concat=a=1:n=2:v=0[s5] \
    -map [s3] -map [s5] 'videos/Modeling the Temporal Dynamic of Neurons in the IT cortex_0_out.mp4' -y -y -hwaccel cuda -c:a aac
    '''
