import xml.etree.ElementTree as ET
import os


def sony_xml_to_xmp(input_file: str) -> str:
	"""
	Convert Sony XML metadata file to XMP format.

	Args:
		input_file_path (str): Path to Sony XML metadata file

	Returns:
		str: XMP formatted metadata as string
	"""

	# Parse the XML file
	tree = ET.parse(input_file)
	root = tree.getroot()

	# Define the namespaces
	# The XML file has a default namespace of something like urn:schemas-professionalDisc:nonRealTimeMeta:ver.2.00,
	# but the version number may be different in different cameras. Since the namespace is not needed for parsing,
	# we can ignore it by using a wildcard.
	namespaces = {
		'any': '*'
	}

	xmp_elements = []

	if (creation_date := root.find('./any:CreationDate', namespaces)) is not None:
		date = creation_date.attrib.get('value', '')
		xmp_elements.append(f'<xmp:CreateDate>{date}</xmp:CreateDate>')
	else:
		raise ValueError("No creation date found in the XML file.")

	# Get device information
	if (device := root.find('./any:Device', namespaces)) is not None:
		manufacturer = device.attrib.get('manufacturer', '')
		model_name = device.attrib.get('modelName', '')
		serial_no = device.attrib.get('serialNo', '')

		xmp_elements.append(f'<tiff:Make>{manufacturer}</tiff:Make>')
		xmp_elements.append(f'<tiff:Model>{model_name}</tiff:Model>')
		xmp_elements.append(f'<tiff:SerialNumber>{serial_no}</tiff:SerialNumber>')
		xmp_elements.append(f'<xmp:CreatorTool>{manufacturer} {model_name}</xmp:CreatorTool>')
		xmp_elements.append(f'<xmpDM:cameraModel>{manufacturer} {model_name}</xmpDM:cameraModel>')
	else:
		raise ValueError("No device information found in the XML file.")

	# Get video information
	if (video_layout := root.find('.//any:VideoLayout', namespaces)) is not None:
		pixel_x = video_layout.attrib.get('pixel', '0')
		pixel_y = video_layout.attrib.get('numOfVerticalLine', '0')
		xmp_elements.append(f'<exif:PixelXDimension>{pixel_x}</exif:PixelXDimension>')
		xmp_elements.append(f'<exif:PixelYDimension>{pixel_y}</exif:PixelYDimension>')
	else:
		raise ValueError("No video layout found in the XML file.")

	if (video_frame := root.find('.//any:VideoFrame', namespaces)) is not None:
		capture_fps = video_frame.attrib.get('captureFps', '0')
		xmp_elements.append(f'<xmpDM:videoFrameRate>{capture_fps}</xmpDM:videoFrameRate>')
	else:
		raise ValueError("No video frame found in the XML file.")

	# Get GPS information (may not be present)
	if (gps_group := root.find(".//any:Group[@name='ExifGPS']", namespaces)) is not None:
		lat_str = lon_str = ''
		lat_ref = lon_ref = ''

		for item in gps_group.findall('.//Item', None):
			name = item.attrib.get('name', '')
			if name == 'Latitude':
				lat_str = item.attrib.get('value', '')
			elif name == 'Longitude':
				lon_str = item.attrib.get('value', '')
			elif name == 'LatitudeRef':
				lat_ref = item.attrib.get('value', '')
			elif name == 'LongitudeRef':
				lon_ref = item.attrib.get('value', '')

		# Convert DMS to DDM
		gps_latitude = gps_decimal_to_ddm(gps_dms_to_decimal(lat_str, ';', lat_ref), True, ',')
		gps_longitude = gps_decimal_to_ddm(gps_dms_to_decimal(lon_str, ';', lon_ref), False, ',')

		xmp_elements.append(f'<exif:GPSLatitude>{gps_latitude}</exif:GPSLatitude>')
		xmp_elements.append(f'<exif:GPSLongitude>{gps_longitude}</exif:GPSLongitude>')

	# Create the XMP content
	xmp_content = f'''<?xpacket begin="{"\xEF\xBB\xBF"}" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 6.0.0">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
      xmlns:xmp="http://ns.adobe.com/xap/1.0/"
      xmlns:exif="http://ns.adobe.com/exif/1.0/"
      xmlns:tiff="http://ns.adobe.com/tiff/1.0/"
      xmlns:xmpDM="http://ns.adobe.com/xmp/1.0/DynamicMedia/">
        {'\n        '.join(xmp_elements)}
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>'''

	return xmp_content


def gps_dms_to_decimal(coordinate: str, delim: str, ref: str) -> float:
	"""
	Convert DMS (degrees, minutes, seconds) to decimal degrees

	Args:
		coordinate : String in format "DD;MM;SS.ss"

	Returns:
		float: Decimal degrees
	"""
	if not coordinate:
		return 0.0

	parts = coordinate.split(delim)
	if len(parts) != 3:
		return 0.0

	try:
		degrees = float(parts[0])
		minutes = float(parts[1])
		seconds = float(parts[2])

		decimal = degrees + minutes/60 + seconds/3600

		if ref == 'S' or ref == 'W':
			decimal = -decimal

		return decimal
	except ValueError:
		return 0.0

def gps_decimal_to_ddm(coordinate: float, is_latitude: bool, delim: str) -> str:
	"""
	Convert decimal degrees to DDM (degrees, decimal minutes)

	Args:
		degrees : Decimal degrees

	Returns:
		str: String in format "DD;MM.mm"
	"""
	if coordinate == 0.0:
		return f"0{delim}0.00"

	neg = coordinate < 0
	coordinate = abs(coordinate)

	degrees = int(coordinate)
	minutes = (coordinate - degrees) * 60

	if neg:
		direction = 'S' if is_latitude else 'W'
	else:
		direction = 'N' if is_latitude else 'E'

	return f"{degrees}{delim}{minutes:.5f}{direction}"


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description="Convert Sony XML metadata to XMP format")

	parser.add_argument("input_file", help="Path to the input Sony XML file")
	parser.add_argument("-o", "--output_file", help="Path to the output XMP file (optional)")
	parser.add_argument("-s", "--preserve-suffix", action="store_true", help="Don't remove the 'M01' suffix from the inferred output file name")

	args = parser.parse_args()

	xmp_data = sony_xml_to_xmp(args.input_file)

	if args.output_file:
		output_file = args.output_file
	else:
		output_file = os.path.splitext(args.input_file)[0] + ".xmp"

		if not args.preserve_suffix:
			output_file = output_file.replace("M01", "")

	with open(output_file, "w", encoding="utf-8") as f:
		f.write(xmp_data)
