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
    _, filename = os.path.split(input_video)
    filebase, ext = os.path.splitext(filename)
    assert ext == '.mp4'

    info = get_video_info(splash_screen)
    w, h = info['coded_width'], info['coded_height']


    for i, (start_time, end_time) in enumerate(cuts):
        if start_time is None:
            continue
        start_ts = to_timestamp(start_time)
        delta = end_time - start_time
        delta_ts = to_timestamp(delta)

        # Cut up the video.
        cmd = (f'ffmpeg -ss {start_ts} -i {input_video} '
               f'-to {delta_ts} -c copy {path}/{filebase}_cut_{i}.mp4 -y')
        
        os.system(cmd)

        # Extract audio
        cmd = (f'ffmpeg -i "{path}/{filebase}_cut_{i}.mp4" "{path}/{filebase}_cut_{i}.wav"')
        os.system(cmd)

        # Normalize the volume.
        os.system(f'ffmpeg-normalize {path}/{filebase}_cut_{i}.wav '
                  f'-o {path}/{filebase}_norm_{i}.wav -ext wav -f '
                  f'-e "-max_muxing_queue_size 1024"')
        
        info = get_video_info(f'{path}/{filebase}_cut_{i}.mp4')
        aspect_ratio = info['coded_width'] / info['coded_height']

        # Assemble the video from the splash screen and the volume normalized 
        # audio, with a fadein of the cropped video.
        intro = ffmpeg.input(splash_screen)

        cropped_vid = ffmpeg.input(f'{path}/{filebase}_cut_{i}.mp4')
        norm_audio = ffmpeg.input(f'{path}/{filebase}_norm_{i}.wav')

        if abs(round(h * aspect_ratio) - w)  / w < .01:
            # This is the perfect aspect ratio.
            # Wide format
            print("Correct aspect ratio")

            video = ffmpeg.concat(
                intro,
                cropped_vid.filter('scale', w, h)
                           .filter('fade', 'in', start_time=0, duration=3) 
                           .filter('fade', 'out', start_time=delta / datetime.timedelta(seconds=1) - 3, duration=3), 
            v=1, a=0)
        elif aspect_ratio <= w / h:
            # Narrow format
            print("Narrow format")
            width = int(round(h*aspect_ratio))


            video = ffmpeg.concat(
                intro.crop(int(round((w - width) / 2)), 0, width, h), 
                cropped_vid.filter('scale', -1, h)
                           .filter('fade', 'in', start_time=0, duration=3)
                           .filter('fade', 'out', start_time=delta / datetime.timedelta(seconds=1) - 3, duration=3), 
            v=1, a=0)        
        else:
            # Wide format
            print("Wide format")
            height = int(round(w / aspect_ratio))

            video = ffmpeg.concat(
                intro.crop(0, int(round((h - height) / 2)), w, height), 
                cropped_vid.filter('scale', w, -1)
                           .filter('fade', 'in', start_time=0, duration=3) 
                           .filter('fade', 'out', start_time=delta / datetime.timedelta(seconds=1) - 3, duration=3), 
            v=1, a=0)

        audio = ffmpeg.concat(
            intro, 
            norm_audio.filter('afade', 'in', start_time=0, duration=1)
                      .filter('afade', 'out', start_time=delta / datetime.timedelta(seconds=1) - 2, duration=2), v=0, a=1)

        out = f'{path}/{filebase}_{i}_out.mp4'
        args = ffmpeg.output(video, audio, out).compile(overwrite_output=True)


        # Extra parameters for dealing with AAC codec and HW accel.
        args = (args[:5] + ['-strict', 'experimental'] + 
                args[5:] + ['-y', '-hwaccel', 'cuda', '-c:a', 'aac'])

        stdin_stream = None
        stdout_stream = None
        stderr_stream = None
        process = subprocess.Popen(
            args, stdin=stdin_stream, stdout=stdout_stream, stderr=stderr_stream
        )
        out, err = process.communicate(None)
        if err:
            raise Exception(err)

        retcode = process.poll()
        print(retcode)

        os.remove(f"{path}/{filebase}_cut_{i}.mp4")
        os.remove(f"{path}/{filebase}_cut_{i}.wav")
        os.remove(f"{path}/{filebase}_norm_{i}.wav")


if __name__ == '__main__':
    # Show how to splice a video, normalize the audio and add a splash screen.
    # Example dataset.
    webinar = 95108214099
    input_video = f'/mnt/d/videos/{webinar}.mp4'

    splash_screen = 'videos/splash_1080_aac_30.mp4'

    # Timings for the individual sub videos.
    cuts = [(datetime.timedelta(minutes=1, seconds=8), 
            datetime.timedelta(minutes=16, seconds=4)), 
            (datetime.timedelta(minutes=16, seconds=4), 
            datetime.timedelta(minutes=31, seconds=22)),
            (datetime.timedelta(minutes=31, seconds=22), 
            datetime.timedelta(minutes=49, seconds=20))]

    cut_videos(input_video, 'videos', splash_screen, cuts)