#!/usr/bin/env bash

# This script will extract GPS coordinates from XML data embedded in a video recorded by a Sony
# Alpha camera and write them to standard tags used by services such as Google Photos or Immich.

# Check if the correct number of arguments is provided
if [ "$#" -eq 0 ]; then
	echo "Usage: $0 <input_file"
	exit 1
fi

# This command will read a composite GPS tag from the embedded data in the file and use that to
# write the standard GPS tags. It is preferred over the config-based command found further below.
# It appears to work identically without requiring the more complicated configuration file to read
# the embedded XML. The outdated command is kept for reference.
exiftool -extractEmbedded --duplicates '-GPSLatitude<$GPSLatitude' '-GPSLongitude<$GPSLongitude' '-UserData:GPSCoordinates<$GPSPosition' "$@"
exit $?


# Source: https://exiftool.org/forum/index.php?topic=11812.0
cat > /tmp/join_tags.config <<- EOM
#------------------------------------------------------------------------------
# File:         join_tags.config
#
# Description:  ExifTool config file to generate new tags from XML name/value pairs
#
# Revisions:    2020-11-16 - P. Harvey created
#------------------------------------------------------------------------------

my \$nameTag = 'AcquisitionRecordGroupItemName';
my \$valueTag = 'AcquisitionRecordGroupItemValue';

sub JoinTags(\$$)
{
    my (\$val, \$et) = @_;
    my \$table = Image::ExifTool::GetTagTable('Image::ExifTool::XMP::XML');
    my \$i;
    for (\$i=0; ;++\$i) {
        my \$suffix = \$i ? " (\$i)" : '';
        my \$name = \$et->GetValue("\$nameTag\$suffix") or last;
        my \$value = \$et->GetValue("\$valueTag\$suffix");
        last unless defined \$value;
        my \$tagInfo = Image::ExifTool::AddTagToTable(\$table, \$name, {
            Name => Image::ExifTool::MakeTagName(\$name),
        });
        \$et->FoundTag(\$tagInfo, \$value);
    }
    return undef;
}

%Image::ExifTool::UserDefined = (
    'Image::ExifTool::Composite' => {
        JoinTags => {
            Desire => {
                0 => \$nameTag,
                1 => \$valueTag,
            },
            RawConv => \&JoinTags,
        },
    },
);

1; #end
EOM

exiftool -config join_tags.config '-GPSLatitude<$XML:Latitude $XML:LatitudeRef' '-GPSLongitude<$XML:Longitude $XML:LongitudeRef' '-UserData:GPSCoordinates<$XML:Latitude $XML:LatitudeRef, $XML:Longitude $XML:LongitudeRef' $FILE
