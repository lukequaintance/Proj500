import os
import json
import logging
import traceback
import piexif
from tkinter import Tk, Button, Label, filedialog, messagebox, Frame
from tkinter.ttk import Progressbar, Style
from bioclip import CustomLabelsClassifier, TreeOfLifeClassifier, Rank
from PIL import Image

# Toggle debug mode.
DEBUG_MODE = False  # Set to True for debugging.

# Configure logging.
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.WARNING,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Define classifiers.
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
species_classifier = TreeOfLifeClassifier()

# Confidence thresholds.
CONFIDENCE_THRESHOLD = 0.6  
HIGH_CONFIDENCE_THRESHOLD = 0.9  # For high-confidence detections.

# --------------------------
# Helper Functions
# --------------------------

def convert_to_degrees(value):
    """
    Converts EXIF GPS coordinates (stored as a tuple of rationals) into decimal degrees.
    """
    d = value[0][0] / value[0][1]
    m = value[1][0] / value[1][1]
    s = value[2][0] / value[2][1]
    return d + (m / 60.0) + (s / 3600.0)

def get_geolocation(image_path):
    """
    Extracts GPS latitude and longitude from an image's EXIF data using piexif.
    Returns (latitude, longitude) in decimal degrees or (None, None) if not available.
    """
    try:
        exif_dict = piexif.load(image_path)
        gps_ifd = exif_dict.get("GPS", {})
        logging.debug(f"Raw GPS IFD for {image_path}: {gps_ifd}")
        if not gps_ifd:
            return None, None

        gps_latitude = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
        gps_latitude_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef)
        gps_longitude = gps_ifd.get(piexif.GPSIFD.GPSLongitude)
        gps_longitude_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef)

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
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
            return None, None
    except Exception as e:
        logging.error(f"Error extracting GPS data from {image_path}: {e}")
        logging.debug(traceback.format_exc())
        return None, None

def process_image(image_path):
    """
    Processes an individual image: runs classifiers, extracts geolocation,
    and returns a dictionary with the results.
    """
    try:
        # Predict using the custom labels classifier.
        custom_predictions = custom_classifier.predict(image_path)
        best_custom_prediction = max(custom_predictions, key=lambda p: p["score"], default=None)

        # Predict species using the Tree of Life classifier.
        species_predictions = species_classifier.predict(image_path, Rank.SPECIES)
        best_species_prediction = max(species_predictions, key=lambda p: p["score"], default=None)
        actual_species = best_species_prediction["species"] if best_species_prediction else "Unknown"

        # Extract geolocation.
        latitude, longitude = get_geolocation(image_path)
        lat_val = round(latitude, 6) if latitude is not None else None
        lon_val = round(longitude, 6) if longitude is not None else None

        # Determine the custom classification and its confidence.
        if best_custom_prediction and best_custom_prediction["score"] >= CONFIDENCE_THRESHOLD:
            classification = best_custom_prediction["classification"]
            confidence = best_custom_prediction["score"]
        else:
            classification = "Uncertain"
            confidence = None

        # Determine plant status based on confidence.
        plant_status = "harmful" if confidence is not None and confidence >= HIGH_CONFIDENCE_THRESHOLD else "non-harmful"

        return {
            "filename": os.path.basename(image_path),
            "custom_classification": classification,
            "confidence": round(confidence, 2) if confidence is not None else None,
            "species": actual_species,
            "latitude": lat_val,
            "longitude": lon_val,
            "plant_status": plant_status
        }
    except Exception as e:
        logging.error(f"Error processing image {image_path}: {e}")
        logging.debug(traceback.format_exc())
        return None

def process_folder(folder_path, progress_callback=None):
    """
    Processes all image files in the given folder and returns a list of results.
    If provided, progress_callback(current, total) is called after each image is processed.
    """
    results = []
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    total = len(image_files)
    
    for idx, filename in enumerate(image_files, start=1):
        image_path = os.path.join(folder_path, filename)
        logging.info(f"Processing {image_path}...")
        data = process_image(image_path)
        if data:
            results.append(data)
        if progress_callback:
            progress_callback(idx, total)
    return results

def write_json(results, output_file="results.json"):
    """
    Writes the results (a list of dictionaries) to a JSON file.
    """
    try:
        with open(output_file, "w") as f:
            json.dump(results, f, indent=4)
        return output_file
    except Exception as e:
        logging.error(f"Error writing JSON file: {e}")
        return None

# --------------------------
# Tkinter GUI with Progress Bar
# --------------------------

class ImageClassifierApp:
    def __init__(self, master):
        self.master = master
        master.title("Plant Image Classifier")
        master.geometry("450x250")
        
        # Style configuration for progress bar.
        self.style = Style()
        self.style.theme_use("default")
        self.style.configure("blue.Horizontal.TProgressbar", foreground='blue', background='blue')

        # Instruction label.
        self.label = Label(master, text="Select a folder containing images to process:")
        self.label.pack(padx=10, pady=10)

        # Select folder button.
        self.select_button = Button(master, text="Select Folder", command=self.select_folder)
        self.select_button.pack(padx=10, pady=5)

        # Progress bar.
        self.progress = Progressbar(master, style="blue.Horizontal.TProgressbar", orient="horizontal", length=300, mode="determinate")
        self.progress.pack(padx=10, pady=10)

        # Progress percentage label.
        self.progress_label = Label(master, text="Progress: 0%")
        self.progress_label.pack(padx=10, pady=5)

        # Process button.
        self.process_button = Button(master, text="Process Images", command=self.process_images, state="disabled")
        self.process_button.pack(padx=10, pady=10)

        self.folder_path = None


    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Images")
        if folder:
            self.folder_path = folder
            self.progress_label.config(text=f"Folder selected: {folder}")
            self.process_button.config(state="normal")
        else:
            self.progress_label.config(text="No folder selected.")

    def update_progress(self, current, total):
        percent = int((current / total) * 100)
        self.progress["value"] = percent
        self.progress_label.config(text=f"Progress: {percent}% ({current} of {total})")
        self.master.update_idletasks()

    def process_images(self):
        if not self.folder_path:
            messagebox.showerror("Error", "Please select a folder first.")
            return

        # Disable buttons during processing.
        self.select_button.config(state="disabled")
        self.process_button.config(state="disabled")
        self.progress_label.config(text="Processing images...")

        try:
            # Count total image files.
            image_files = [f for f in os.listdir(self.folder_path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
            total = len(image_files)
            self.progress["value"] = 0
            results = process_folder(self.folder_path, progress_callback=self.update_progress)
            if not results:
                messagebox.showinfo("Result", "No valid image files found in the selected folder.")
                self.progress_label.config(text="Processing complete. No images processed.")
                return

            output_file = write_json(results)
            if output_file:
                messagebox.showinfo("Success", f"Processing complete.\nResults saved to: {output_file}")
                self.progress_label.config(text=f"Results saved to {output_file}")
            else:
                messagebox.showerror("Error", "An error occurred while writing the results.")
                self.progress_label.config(text="Error writing results.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during processing:\n{e}")
            logging.error(f"Critical error during processing: {e}")
            self.progress_label.config(text="Error during processing.")
        finally:
            # Re-enable buttons if needed.
            self.select_button.config(state="normal")
            self.process_button.config(state="normal")

def main():
    root = Tk()
    app = ImageClassifierApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
