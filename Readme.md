# Sony Alpha Video Scripts

Scripts for processing videos recorded by a Sony Alpha camera.

## Description

The videos recorded by a Sony Alpha camera have embdedded XML data that is not normally recognized
by most software or preserved when transcoded. These scripts help make use of this information or
preserve it when transcoding.

The root MP4 container has an embedded XML document that contains metadata about the video and the
camera tha recorded it. This is the same XML document that is generated as a sidecar alongside the
video file.

The video also has a 3rd track which contains timestampped XML data indicating information such as
the current F-stop, exposure, ISO, GPS position (if available), orientation and acceleration (on
certain cameras). This is not normally preserved during transcoding, which can be remedied by the
scripts in this project. This project also provides the means by which the GPS position can be
extracted and inserted into more standard tags which are used by services such as Google Photos or
Immich.
