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

params=("$OUTPUT_DIR" "$RECORDING_ID" "$RESOURCE")

for param in "${params[@]}"; do
  if [ -z "$param" ]
  then
    echo "Tags -r, -i, -o is required arg";
    exit 1;
  fi
done


PREFIX="https://$RESOURCE/presentation/$RECORDING_ID"
OUT="$OUTPUT_DIR/$RECORDING_ID.mp4"

DESKSHARE="$PREFIX/deskshare/deskshare.webm"
WEBCAMS="${PREFIX}/video/webcams.webm"


wget_http_code() {
  local url=$1
  http_status=$( wget -S --spider "$url" 2>&1 | grep "HTTP/" | awk '{print $2}')
  echo "$http_status"
}

http_status_webcams=$(wget_http_code "$WEBCAMS")
http_status_deskshare=$(wget_http_code "$DESKSHARE")

echo "http_status_webcams - $http_status_webcams"
echo "http_status_deskshare - $http_status_deskshare"

if [[ "$http_status_deskshare" -ne 200 ]]; then
  DESKSHARE="static/white.jpg"
fi


echo "OUT = $OUT"
echo "PREFIX = $PREFIX"
echo "DESKSHARE = $DESKSHARE"
echo "WEBCAMS = $WEBCAMS"

echo "Start repack videos FFMPEG"


FILTER_COMPLEX="[1]scale=320:-1,setpts=PTS-STARTPTS[pip];\
              [0]pad=w=1630:h=ih+20:x=10:y=10:color=LightGrey,setpts=PTS-STARTPTS[slides];\
              [slides][pip] overlay=main_w-overlay_w-10:main_h-overlay_h-10[v]"

ffmpeg -i $DESKSHARE -i $WEBCAMS -y -filter_complex "${FILTER_COMPLEX}" -map "[v]" -map "1:a" \
    -c:v h264 -crf 21 -c:a aac -q:a 0.8 $OUT