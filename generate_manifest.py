import os
import hashlib
import xml.etree.ElementTree as ET
from xml.dom import minidom

def calculate_md5(file_path):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {str(e)}")
        return None

def update_version():
    """Update version.xml or create it with 1.0.0 if missing, using the new format"""
    version_file = "version.xml"
    new_version = "1.0.0"
    
    if os.path.exists(version_file):
        try:
            tree = ET.parse(version_file)
            root = tree.getroot()
            # Check new structure first
            version_element = root.find("version")
            if version_element is None:
                # Fallback to old structure (root is <version>)
                if root.tag == "version":
                    version = root.text
                else:
                    raise ET.ParseError("Invalid version.xml structure")
            else:
                version = version_element.text
            
            parts = list(map(int, version.split('.')))
            parts[-1] += 1  # Increment the last part
            new_version = '.'.join(map(str, parts))
        except Exception as e:
            print(f"Error reading version: {str(e)}, resetting to 1.0.0")
    
    # Create new structure with formatting
    game_element = ET.Element("game")
    version_element = ET.SubElement(game_element, "version")
    version_element.text = new_version
    
    # Format XML
    xml_str = ET.tostring(game_element, encoding="utf-8")
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")
    
    with open(version_file, "wb") as f:
        f.write(pretty_xml)
    
    print(f"Version updated to: {new_version}")

def generate_manifest(game_folder=".", output_file="files_manifest.xml"):
    """Generate manifest file with file paths and their MD5 hashes"""
    update_version()
    
    root = ET.Element("files")
    
    exclude_files = {
        os.path.normpath(output_file),
        os.path.normpath("version.xml"),
        os.path.normpath(os.path.basename(__file__))
    }
    
    for root_dir, _, files in os.walk(game_folder):
        for filename in files:
            file_path = os.path.join(root_dir, filename)
            rel_path = os.path.relpath(file_path, game_folder)
            
            if os.path.normpath(rel_path) in exclude_files:
                continue
            
            file_hash = calculate_md5(file_path)
            if file_hash is None:
                continue
                
            file_element = ET.SubElement(root, "file")
            ET.SubElement(file_element, "path").text = rel_path.replace("\\", "/")
            ET.SubElement(file_element, "hash").text = file_hash
    
    # Format XML
    xml_str = ET.tostring(root, encoding="utf-8")
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")
    
    with open(output_file, "wb") as f:
        f.write(pretty_xml)
    print(f"Manifest generated: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate files manifest for game")
    parser.add_argument("--folder", help="Path to game folder (default: current dir)", default=".")
    parser.add_argument("-o", "--output", help="Output file name", default="files_manifest.xml")
    args = parser.parse_args()
    
    generate_manifest(args.folder, args.output)