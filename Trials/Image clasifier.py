import os
import logging
import traceback
import piexif
from bioclip import CustomLabelsClassifier, TreeOfLifeClassifier, Rank
from PIL import Image

# Toggle this flag to enable/disable debug logging.
DEBUG_MODE = False  # Set to True for debugging, False for normal running mode.

# Configure logging based on DEBUG_MODE.
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.WARNING,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Define classifiers with a broad list of simplified terms.
custom_classifier = CustomLabelsClassifier([
    "Annual meadow-grass", "Awned canary-grass", "Barley", "Barren brome", "Black bent",
    "Black-bindweed", "Black-grass", "Black mustard", "Black nightshade", "Broad-leaved dock",
    "Canadian fleabane", "Charlock", "Cleavers", "Cock’s-foot", "Common chickweed", "Common couch",
    "Common field-speedwell", "Common fumitory", "Common hemp-nettle", "Common mouse-ear", "Common nettle",
    "Common orache", "Common poppy", "Corn spurrey", "Cornflower", "Cow parsley", "Creeping bent",
    "Creeping thistle", "Crested dog’s-tail", "Curled dock", "Cut-leaved crane’s-bill", "Daisy", "Dandelion",
    "Dove’s-foot crane’s-bill", "Fat hen", "Field bean", "Field bindweed", "Field forget-me-not",
    "Field horsetail", "Field pansy", "Fool’s parsley", "Garlic mustard", "Great brome", "Green field-speedwell",
    "Groundsel", "Hedge mustard", "Hemlock", "Henbit dead-nettle", "Italian rye-grass", "Ivy-leaved speedwell",
    "Knapweed", "Knot-grass", "Linseed", "Long-headed poppy", "Loose silky bent", "Meadow brome", "Nipplewort",
    "Oat", "Oilseed rape", "Onion couch", "Pale persicaria", "Parsley-piert", "Pea", "Perennial rye-grass",
    "Perennial sow-thistle", "Pineappleweed", "Potato", "Prickly sow-thistle", "Ragwort", "Red dead-nettle",
    "Red fescue", "Redshank", "Rough-stalked meadow-grass", "Round-leaved fluellen", "Rye brome", "Scarlet pimpernel",
    "Scented mayweed", "Scentless mayweed", "Sharp-leaved fluellen", "Shepherd’s-needle", "Shepherd’s-purse",
    "Small nettle", "Smooth sow-thistle", "Soft brome", "Spear thistle", "Spreading hedge-parsley", "Sugar beet",
    "Sunflower", "Timothy", "Venus’s-looking-glass", "Wall speedwell", "Wheat", "White campion", "Wild carrot",
    "Wild-oat", "Wild pansy", "Wild radish", "Winter wild-oat", "Yorkshire-fog", "Red Clover", "Bird's-foot Trefoil", 
    "Common Knapweed", "Oxeye Daisy", "Yarrow", "Wild Carrot", "Field Poppy", "Yellow Rattle", "Selfheal", "Meadow Buttercup"
])

# Plant lists (no longer used in the plant status decision).
GOOD_PLANTS = [
    "Red Clover", "Bird's-foot Trefoil", "Common Knapweed", "Oxeye Daisy", "Yarrow",
    "Wild Carrot", "Field Poppy", "Yellow Rattle", "Selfheal", "Meadow Buttercup"
]

BAD_PLANTS = [
    "Annual meadow-grass", "Awned canary-grass", "Barley", "Barren brome", "Black bent",
    "Black-bindweed", "Black-grass", "Black mustard", "Black nightshade", "Broad-leaved dock",
    "Canadian fleabane", "Charlock", "Cleavers", "Cock’s-foot", "Common chickweed", "Common couch",
    "Common field-speedwell", "Common fumitory", "Common hemp-nettle", "Common mouse-ear", "Common nettle",
    "Common orache", "Common poppy", "Corn spurrey", "Cornflower", "Cow parsley", "Creeping bent",
    "Creeping thistle", "Crested dog’s-tail", "Curled dock", "Cut-leaved crane’s-bill", "Daisy", "Dandelion",
    "Dove’s-foot crane’s-bill", "Fat hen", "Field bean", "Field bindweed", "Field forget-me-not",
    "Field horsetail", "Field pansy", "Fool’s parsley", "Garlic mustard", "Great brome", "Green field-speedwell",
    "Groundsel", "Hedge mustard", "Hemlock", "Henbit dead-nettle", "Italian rye-grass", "Ivy-leaved speedwell",
    "Knapweed", "Knot-grass", "Linseed", "Long-headed poppy", "Loose silky bent", "Meadow brome", "Nipplewort",
    "Oat", "Oilseed rape", "Onion couch", "Pale persicaria", "Parsley-piert", "Pea", "Perennial rye-grass",
    "Perennial sow-thistle", "Pineappleweed", "Potato", "Prickly sow-thistle", "Ragwort", "Red dead-nettle",
    "Red fescue", "Redshank", "Rough-stalked meadow-grass", "Round-leaved fluellen", "Rye brome", "Scarlet pimpernel",
    "Scented mayweed", "Scentless mayweed", "Sharp-leaved fluellen", "Shepherd’s-needle", "Shepherd’s-purse",
    "Small nettle", "Smooth sow-thistle", "Soft brome", "Spear thistle", "Spreading hedge-parsley", "Sugar beet",
    "Sunflower", "Timothy", "Venus’s-looking-glass", "Wall speedwell", "Wheat", "White campion", "Wild carrot",
    "Wild-oat", "Wild pansy", "Wild radish", "Winter wild-oat", "Yorkshire-fog"
]
species_classifier = TreeOfLifeClassifier()

# Define input folder and output file.
INPUT_FOLDER = "trial images"
OUTPUT_FILE = "results.csv"

# Confidence thresholds.
CONFIDENCE_THRESHOLD = 0.6  
HIGH_CONFIDENCE_THRESHOLD = 0.9  # For highlighting high confidence detections.

def convert_to_degrees(value):
    """
    Converts EXIF GPS coordinates (stored as a tuple of rationals) into decimal degrees.
    
    Args:
        value (tuple): A tuple of three tuples (degrees, minutes, seconds).
    
    Returns:
        float: Coordinate in decimal degrees.
    """
    d = value[0][0] / value[0][1]
    m = value[1][0] / value[1][1]
    s = value[2][0] / value[2][1]
    return d + (m / 60.0) + (s / 3600.0)

def get_geolocation(image_path):
    """
    Extracts GPS latitude and longitude from an image's EXIF data using piexif.
    
    Args:
        image_path (str): Path to the image file.
    
    Returns:
        tuple: (latitude, longitude) in decimal degrees if available; otherwise, (None, None).
    """
    try:
        exif_dict = piexif.load(image_path)
        gps_ifd = exif_dict.get("GPS", {})
        logging.debug(f"Raw GPS IFD for {image_path}: {gps_ifd}")
        if not gps_ifd:
            logging.debug(f"No GPS IFD found in EXIF for {image_path}")
            return None, None

        # Retrieve the required GPS tags.
        gps_latitude = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
        gps_latitude_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef)
        gps_longitude = gps_ifd.get(piexif.GPSIFD.GPSLongitude)
        gps_longitude_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef)

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            # Decode reference values if stored as bytes.
            lat_ref = gps_latitude_ref.decode("utf-8") if isinstance(gps_latitude_ref, bytes) else gps_latitude_ref
            lon_ref = gps_longitude_ref.decode("utf-8") if isinstance(gps_longitude_ref, bytes) else gps_longitude_ref

            lat = convert_to_degrees(gps_latitude)
            if lat_ref.upper() != "N":
                lat = -lat

            lon = convert_to_degrees(gps_longitude)
            if lon_ref.upper() != "E":
                lon = -lon

            return lat, lon
        else:
            logging.debug(f"Incomplete GPS data for {image_path}: {gps_ifd}")
            return None, None
    except Exception as e:
        logging.error(f"Error extracting GPS data from {image_path} using piexif: {e}")
        logging.debug(traceback.format_exc())
        return None, None

def process_image(image_path):
    """
    Processes an individual image: predicts classifications, extracts GPS data,
    and returns a CSV row.
    
    Args:
        image_path (str): Path to the image file.
    
    Returns:
        str: CSV-formatted row with image results.
    """
    try:
        # Predict using the custom labels classifier.
        custom_predictions = custom_classifier.predict(image_path)
        best_custom_prediction = max(custom_predictions, key=lambda p: p["score"], default=None)

        # Predict species classification using the Tree of Life classifier.
        species_predictions = species_classifier.predict(image_path, Rank.SPECIES)
        best_species_prediction = max(species_predictions, key=lambda p: p["score"], default=None)
        actual_species = best_species_prediction["species"] if best_species_prediction else "Unknown"

        # Extract geolocation information.
        latitude, longitude = get_geolocation(image_path)
        lat_str = f"{latitude:.6f}" if latitude is not None else "NA"
        lon_str = f"{longitude:.6f}" if longitude is not None else "NA"

        # Get the Encyclopedia of Life (EOL) URL.
        # In the Bioclip demo, the species prediction includes an 'eol_url' key.
        # If not provided, a fallback EOL search URL is constructed.
        if best_species_prediction and "eol_url" in best_species_prediction:
            species_link = best_species_prediction["eol_url"]
        elif actual_species != "Unknown":
            species_link = f"https://eol.org/search?q={actual_species.replace(' ', '+')}"
        else:
            species_link = "NA"


        # Determine custom classification and confidence.
        if best_custom_prediction and best_custom_prediction["score"] >= CONFIDENCE_THRESHOLD:
            classification = best_custom_prediction["classification"]
            confidence = best_custom_prediction["score"]
        else:
            classification = "Uncertain classification"
            confidence = None

        # Flag image if classified as ragwort (either by custom classifier or species classification).
        is_ragwort = (classification.lower() == "ragwort" or "ragwort" in actual_species.lower())

        if confidence is not None:
            if is_ragwort and confidence >= HIGH_CONFIDENCE_THRESHOLD:
                class_str = "RAGWORT ***HIGH CONFIDENCE***"
            else:
                class_str = classification
            conf_str = f"{confidence:.2f}"
        else:
            class_str = classification
            conf_str = "NA"

        # --- Modified code to determine plant status based on the custom classification score ---
        plant_status = ""
        if confidence is not None and confidence >= HIGH_CONFIDENCE_THRESHOLD:
            plant_status = "harmfull"
        # --- End modified code ---

        # Create a CSV-formatted row with results.
        filename = os.path.basename(image_path)
        csv_row = f"{filename},{class_str},{conf_str},{actual_species},{lat_str},{lon_str},{species_link},{plant_status}\n"
        logging.info(f"Processed {filename}: {csv_row.strip()}")
        return csv_row

    except Exception as e:
        logging.error(f"Error processing image {image_path}: {e}")
        logging.debug(traceback.format_exc())
        return None

def main():
    """
    Main function to process images from the input folder and save the results to a CSV file.
    """
    try:
        with open(OUTPUT_FILE, "w") as f:
            # Write CSV header (added new column "Plant Status").
            f.write("Filename,Custom Classification,Confidence,Species Classification,Latitude,Longitude,Plant Status\n")

            # Process each image in the input folder.
            for filename in os.listdir(INPUT_FOLDER):
                if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    image_path = os.path.join(INPUT_FOLDER, filename)
                    csv_row = process_image(image_path)
                    if csv_row:
                        f.write(csv_row)
        logging.info(f"Classification results saved to {OUTPUT_FILE}")

    except Exception as e:
        logging.critical(f"Critical error in main processing: {e}")
        logging.debug(traceback.format_exc())

if __name__ == "__main__":
    main()
