#!/usr/bin/env bash

# This script will take a video recorded by a Sony Alpha camera and convert it to a specified codec
# and bitrate using FFmpeg. The data stream and metadata that FFmpeg doesn't handle will be copied
# over to the transcoded video.

CODEC=libx265
BITRATE=20M

# Check if the correct number of arguments is provided
if [ "$#" -lt 2 ]; then
	echo "Usage: $0 [-c|--codec codec] [-b|--bitrate bitrate] <input_file> <output_file>"
	echo "Default codec is $CODEC"
	echo "Default bitrate is $BITRATE"
	exit 1
fi

# Parse command-line options
while [[ $# -gt 2 ]]; do
  case "$1" in
    -c|--codec)
      CODEC="$2"
      shift 2
      ;;
    -b|--bitrate)
      BITRATE="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

INFILE=$1
OUTFILE=$2

# Convert the input file
ffmpeg -i $INFILE -map_metadata 0 -map_metadata:s:v 0:s:v -map_metadata:s:a 0:s:a -movflags use_metadata_tags+faststart -copy_unknown -c:v $CODEC -b:v $BITRATE -c:a copy $OUTFILE

# Copy the non-standard data stream and metadata that FFmpeg refuses to handle
MP4Box -add ${INFILE}#3 $OUTFILE
MP4Box -dump-xml /tmp/${INFILE}.xml $INFILE
MP4Box -set-meta META -set-xml /tmp/${INFILE}.xml $OUTFILE

# Remove the temporary XML file
rm /tmp/${INFILE}.xml
