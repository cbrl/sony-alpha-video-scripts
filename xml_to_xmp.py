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
	# Register the namespaces used in Sony XML
	namespaces = {
		'sony': 'urn:schemas-professionalDisc:nonRealTimeMeta:ver.2.20',
		'lib': 'urn:schemas-professionalDisc:lib:ver.2.10',
		'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
	}

	# Parse the XML file
	tree = ET.parse(input_file)
	root = tree.getroot()

	# Extract metadata using namespaces
	creation_date = root.find('.//sony:CreationDate', namespaces).attrib.get('value', '')

	# Get video information
	video_layout = root.find('.//sony:VideoLayout', namespaces)
	pixel_x = video_layout.attrib.get('pixel', '0') if video_layout is not None else '0'
	pixel_y = video_layout.attrib.get('numOfVerticalLine', '0') if video_layout is not None else '0'

	video_frame = root.find('.//sony:VideoFrame', namespaces)
	capture_fps = video_frame.attrib.get('captureFps', '0') if video_frame is not None else '0'

	# Get device information
	device = root.find('.//sony:Device', namespaces)
	manufacturer = device.attrib.get('manufacturer', '') if device is not None else ''
	model_name = device.attrib.get('modelName', '') if device is not None else ''
	serial_no = device.attrib.get('serialNo', '') if device is not None else ''

	# Get GPS information
	lat_str = lon_str = ''
	lat_ref = lon_ref = ''
	gps_group = root.find(".//sony:Group[@name='ExifGPS']", namespaces)
	if gps_group is not None:
		for item in gps_group.findall('.//sony:Item', namespaces):
			if item.attrib.get('name') == 'Latitude':
				lat_str = item.attrib.get('value', '')
			elif item.attrib.get('name') == 'Longitude':
				lon_str = item.attrib.get('value', '')
			elif item.attrib.get('name') == 'LatitudeRef':
				lat_ref = item.attrib.get('value', '')
			elif item.attrib.get('name') == 'LongitudeRef':
				lon_ref = item.attrib.get('value', '')

	# Convert DMS to DDM
	gps_latitude = gps_decimal_to_ddm(gps_dms_to_decimal(lat_str, ';', lat_ref), True, ',')
	gps_longitude = gps_decimal_to_ddm(gps_dms_to_decimal(lon_str, ';', lon_ref), False, ',')

	# Create the XMP content
	xmp_content = f'''<?xpacket begin="{"\xEF\xBB\xBF"}" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 6.0.0">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
	<rdf:Description rdf:about=""
	  xmlns:xmp="http://ns.adobe.com/xap/1.0/"
	  xmlns:exif="http://ns.adobe.com/exif/1.0/"
	  xmlns:tiff="http://ns.adobe.com/tiff/1.0/"
	  xmlns:xmpDM="http://ns.adobe.com/xmp/1.0/DynamicMedia/">
		<xmp:CreateDate>{creation_date}</xmp:CreateDate>
		<xmp:CreatorTool>{manufacturer} {model_name}</xmp:CreatorTool>
		<tiff:Make>{manufacturer}</tiff:Make>
		<tiff:Model>{model_name}</tiff:Model>
		<tiff:SerialNumber>{serial_no}</tiff:SerialNumber>
		<exif:PixelXDimension>{pixel_x}</exif:PixelXDimension>
		<exif:PixelYDimension>{pixel_y}</exif:PixelYDimension>
		<exif:GPSLatitude>{gps_latitude}</exif:GPSLatitude>
		<exif:GPSLongitude>{gps_longitude}</exif:GPSLongitude>
		<xmpDM:cameraModel>{manufacturer} {model_name}</xmpDM:cameraModel>
		<xmpDM:videoFrameRate>{capture_fps}</xmpDM:videoFrameRate>
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
