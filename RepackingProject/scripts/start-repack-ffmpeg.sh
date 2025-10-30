#!/bin/bash

while [[ $# -gt 0 ]]; do
  case $1 in
    -r|--resource)
      RESOURCE="$2"
      shift # past argument
      shift # past value
      ;;
    -i|--recording_id)
      RECORDING_ID="$2"
      shift # past argument
      shift # past value
      ;;
    -o|--output_dir)
      OUTPUT_DIR="$2"
      shift # past argument
      shift # past value
      ;;
  esac
done

if [ -z "$RESOURCE" ]
then
  echo "Tag -r is required arg";
  exit 1;
fi

if [ -z "$RECORDING_ID" ]
then
  echo "Tag -i is required arg"
  exit 1;
fi

if [ -z "$OUTPUT_DIR" ]
then
  echo "Tag -o is required arg"
  exit 1;
fi


PREFIX="https://$RESOURCE/presentation/$RECORDING_ID"
OUT="$OUTPUT_DIR/$RECORDING_ID.mp4"

DESKSHARE="$PREFIX/deskshare/deskshare.webm"
WEBCAMS="${PREFIX}/video/webcams.webm"

FILTER_COMPLEX="[1]scale=320:-1,setpts=PTS-STARTPTS[pip];\
                [0]pad=w=1630:h=ih+20:x=10:y=10:color=LightGrey,setpts=PTS-STARTPTS[slides];\
                [slides][pip] overlay=main_w-overlay_w-10:main_h-overlay_h-10[v]"

echo "OUT = $OUT"
echo "PREFIX = $PREFIX"
echo "DESKSHARE = $DESKSHARE"
echo "WEBCAMS = $WEBCAMS"

echo "Start repack videos FFMPEG"


ffmpeg -i $DESKSHARE -i $WEBCAMS -y -filter_complex "${FILTER_COMPLEX}" -map "[v]" -map "1:a" \
    -c:v h264 -crf 21 -c:a aac -q:a 0.8 $OUT
