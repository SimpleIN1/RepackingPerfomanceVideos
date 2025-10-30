from ffmpeg import FFmpeg


PREFIX = "https://{0}/presentation/{1}"
I1 = f"{PREFIX}/deskshare/deskshare.webm"
I2 = f"{PREFIX}/video/webcams.webm"
OUTPUT = "{0}.mp4"

FILTER_COMPLEX = "[1]scale=320:-1,setpts=PTS-STARTPTS[pip];" \
                "[0]pad=w=1630:h=ih+20:x=10:y=10:color=LightGrey,setpts=PTS-STARTPTS[slides];" \
                "[slides][pip] overlay=main_w-overlay_w-10:main_h-overlay_h-10[v]"


def repack_video(resource, record_id):
    ffmpeg = FFmpeg() \
        .input(I1.format(resource, record_id)) \
        .input(I2.format(resource, record_id)) \
        .output(
            OUTPUT.format(record_id),
            filter_complex=FILTER_COMPLEX,
            crf=21,
            y=None,
            map=["[v]", "1:a"],
            options={
                "c:v": "h264",
                "c:a": "aac",
                "q:a": 0.8,
            }
        )
    ffmpeg.terminate()
    ffmpeg.execute()
