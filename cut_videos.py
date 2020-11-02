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
        return f"{seconds // 3600:02}:{seconds // 60:02}:{seconds % 60:02}"
    else:
        return f"{seconds // 60:02}:{seconds % 60:02}"

def cut_videos(input_video, splash_screen, cuts):
    path, filename = os.path.split(input_video)
    filebase, ext = os.path.splitext(filename)
    print(ext)
    assert ext == '.mp4'

    info = get_video_info(splash_screen)
    w, h = info['coded_width'], info['coded_height']


    for i, (start_time, end_time) in enumerate(cuts):
        start_ts = to_timestamp(start_time)
        delta = end_time - start_time
        delta_ts = to_timestamp(delta)

        # Cut up the video.
        cmd = (f'ffmpeg -ss {start_ts} -i {path}/{filebase}.mp4 '
               f'-to {delta_ts} -c copy {path}/{filebase}_cut_{i}.mp4 -y')
        
        os.system(cmd)

        # Normalize the volume.
        os.system(f'ffmpeg-normalize {path}/{filebase}_cut_{i}.mp4 '
                  f'-o {path}/{filebase}_cut_norm_{i}.mp4 -c:a aac -f '
                  f'-e "-max_muxing_queue_size 1024"')
        
        info = get_video_info(f'{path}/{filebase}_cut_norm_{i}.mp4')
        aspect_ratio = info['coded_width'] / info['coded_height']

        # Assemble the video from the splash screen and the volume normalized 
        # audio, with a fadein of the cropped video.
        intro = ffmpeg.input(splash_screen)

        cropped_vid = ffmpeg.input(f'{path}/{filebase}_cut_norm_{i}.mp4')        

        if aspect_ratio <= w / h:
            width = int(h*aspect_ratio)

            video = ffmpeg.concat(
                intro.crop(int((w - width) / 2), 0, width, h), 
                cropped_vid.filter('scale', -1, h)
                           .filter('fade', 'in', start_time=0, duration=3), 
            v=1, a=0)        
        else:
            dx = int((w - h * aspect_ratio)/2)
            video = ffmpeg.concat(
                intro, 
                cropped_vid.filter('scale', -1, h)
                           .crop(dx, 0, w, h)
                           .filter('fade', 'in', start_time=0, duration=3), 
            v=1, a=0)

        audio = ffmpeg.concat(
            intro, 
            cropped_vid, v=0, a=1)

        out = f'{path}/{filebase}_{i}_out.mp4'
        args = ffmpeg.output(video, audio, out).compile(overwrite_output=True)

        # Extra parameters for dealing with AAC codec and HW accel.
        args = (args[:5] + ['-strict', 'experimental'] + 
                args[5:] + ['-y', '-hwaccel', 'cuda'])

        stdin_stream = None
        stdout_stream = None
        stderr_stream = None
        process = subprocess.Popen(
            args, stdin=stdin_stream, stdout=stdout_stream, stderr=stderr_stream
        )
        out, err = process.communicate(None)
        retcode = process.poll()

        os.remove(f"{path}/{filebase}_cut_{i}.mp4")
        os.remove(f"{path}/{filebase}_cut_norm_{i}.mp4")


if __name__ == '__main__':
    webinar = 92889278156
    input_video = f'videos/{webinar}.mp4'
    splash_screen = 'videos/splash_1080_aac_30.mp4'

    cuts = [(datetime.timedelta(minutes=1, seconds=8), 
            datetime.timedelta(minutes=16, seconds=4)), 
            (datetime.timedelta(minutes=16, seconds=4), 
            datetime.timedelta(minutes=31, seconds=22)),
            (datetime.timedelta(minutes=31, seconds=22), 
            datetime.timedelta(minutes=49, seconds=20))]

    cut_videos(input_video, splash_screen, cuts)