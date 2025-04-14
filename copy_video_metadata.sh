#!/usr/bin/env bash

# This script copies the non-standard data stream and metadata from a video recorded by a Sony Alpha
# camera to a destination video. This can be used for a video that was presviously transcoded and
# lost such information during the transcoding process.

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
	echo "Usage: $0 <input_file> <output_file>"
	exit 1
fi

INFILE=$1
OUTFILE=$2

# Copy the non-standard data stream and metadata that FFmpeg refuses to handle
MP4Box -add ${INFILE}#3 $OUTFILE
MP4Box -dump-xml /tmp/${INFILE}.xml $INFILE
MP4Box -set-meta META -set-xml /tmp/${INFILE}.xml $OUTFILE

# Remove the temporary XML file
rm /tmp/${INFILE}.xml
