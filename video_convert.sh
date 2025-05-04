#!/usr/bin/env bash

# This script will take a video recorded by a Sony Alpha camera and convert it using FFmpeg.
# The data stream and metadata that FFmpeg doesn't handle will be copied over to the transcoded video.

# Check if the correct number of arguments is provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input_file> <output_file> [ffmpeg_output_options...]"
    exit 1
fi

INFILE="$1"
OUTFILE="$2"
shift 2 # Remove input and output file from arguments

# Collect any additional ffmpeg output arguments
FFMPEG_ARGS=("$@")

# Convert the input file
ffmpeg -i "$INFILE" \
       -map_metadata 0 -map_metadata:s:v 0:s:v -map_metadata:s:a 0:s:a \
       -movflags use_metadata_tags+faststart \
       -copy_unknown \
       "${FFMPEG_ARGS[@]}" \
       "$OUTFILE"

# Copy the non-standard data stream and metadata that FFmpeg refuses to handle
MP4Box -add ${INFILE}#3 $OUTFILE
MP4Box -dump-xml /tmp/${INFILE}.xml $INFILE
MP4Box -set-meta META -set-xml /tmp/${INFILE}.xml $OUTFILE

# Remove the temporary XML file
rm /tmp/${INFILE}.xml
