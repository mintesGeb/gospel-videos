#!/bin/sh
# usage: add_music.sh <silent_dir> <out_dir> <music_dir>
# Rotates the music tracks (mp3) across videos, using a different 15s section each time.
S="$1"; O="$2"; M="$3"; mkdir -p "$O"
set -- $(ls "$M"/*.mp3 | sort); N=$#; TRACKS="$*"
i=0
for v in $(ls "$S"/*.mp4 | sort); do
  k=$((i % N + 1)); T=$(echo $TRACKS | cut -d' ' -f$k)
  D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$T" | cut -d. -f1)
  MAX=$((D - 18)); [ $MAX -lt 1 ] && MAX=1
  OFF=$(( (i * 23 + 7) % MAX ))
  ffmpeg -loglevel error -y -i "$v" -ss $OFF -t 15 -i "$T" -map 0:v -map 1:a -c:v copy \
    -af "afade=t=in:d=0.5,afade=t=out:st=13.5:d=1.5" -c:a aac -b:a 192k -shortest "$O/$(basename $v)"
  i=$((i+1))
done
