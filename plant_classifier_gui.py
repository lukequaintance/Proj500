#!/usr/bin/env python3
"""
Plant Image Classifier Application

This script processes plant images by running custom and species classifiers,
extracts geolocation from image EXIF data, and provides a GUI for folder selection,
progress tracking, and saving results as JSON. It also includes an option to launch
a separate visualization application.

Usage:
    python this_script.py
"""

# ---------------------
# Imports
# ---------------------
import os
import json
import logging
import traceback
import threading
import subprocess
import sys

import piexif
from tkinter import Tk, Button, Label, filedialog, messagebox
from tkinter.ttk import Progressbar, Style
from PIL import Image

import open_clip  # Used for model loading
from bioclip import CustomLabelsClassifier, TreeOfLifeClassifier, Rank

# ---------------------
# Global Configuration & Variables
# ---------------------

DEBUG_MODE = False  # Toggle debug mode; set to True for debugging.

# Configure logging.
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.WARNING,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Global variables for classifiers and model.
custom_classifier = None
species_classifier = None
model = None
preprocess_train = None
preprocess_val = None
tokenizer = None

# Classifier parameters.
CONFIDENCE_THRESHOLD = 0.1  
HIGH_CONFIDENCE_THRESHOLD = 0.8  # For high-confidence detections.

# ---------------------
# Utility Functions
# ---------------------

def launch_visualization_app():

    # Launch the visualization application (app.py) using the same Python interpreter.

    subprocess.Popen([sys.executable, "Data_Visulisation_App.py"])


def convert_to_degrees(value):

    # Convert EXIF GPS coordinates into decimal degrees.
    
    d = value[0][0] / value[0][1]
    m = value[1][0] / value[1][1]
    s = value[2][0] / value[2][1]
    return d + (m / 60.0) + (s / 3600.0)


def get_geolocation(image_path):

   # Extract GPS latitude and longitude from an image's EXIF data.
    
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

# ---------------------
# Image Processing Functions
# ---------------------
def process_image(image_path):
    """
    Process an individual image: run classifiers, extract geolocation,
    and return a dictionary with all high-confidence results.
    
    """
    try:
        global custom_classifier, species_classifier

        # Run the custom classifier.
        custom_predictions = custom_classifier.predict(image_path)
        # Filter predictions based on a minimum confidence threshold.
        valid_custom = [p for p in custom_predictions if p["score"] >= CONFIDENCE_THRESHOLD]
        # If none pass the threshold, add a default uncertain prediction.
        if not valid_custom:
            valid_custom = [{"classification": "Uncertain", "score": None}]
        # Determine plant status for each prediction.
        for pred in valid_custom:
            pred["plant_status"] = (
                "harmful" if pred["score"] is not None and pred["score"] >= HIGH_CONFIDENCE_THRESHOLD
                else "non-harmful"
            )

        # Run the species classifier.
        species_predictions = species_classifier.predict(image_path, Rank.SPECIES)
        # Filter species predictions for high-confidence results.
        valid_species = [p for p in species_predictions if p["score"] >= HIGH_CONFIDENCE_THRESHOLD]
        # If no species meet the high threshold, fall back to the best species prediction.
        if not valid_species:
            best_species = max(species_predictions, key=lambda p: p["score"], default={"species": "Unknown", "score": None})
            valid_species = [best_species]

        # Get geolocation.
        latitude, longitude = get_geolocation(image_path)
        lat_val = round(latitude, 6) if latitude is not None else None
        lon_val = round(longitude, 6) if longitude is not None else None

        # Prepare and return the result with separate lists for custom and species predictions.
        result = {
            "filename": os.path.basename(image_path),
            "image_path": image_path,
            "latitude": lat_val,
            "longitude": lon_val,
            "custom_predictions": [
                {
                    "classification": p["classification"],
                    "confidence": round(p["score"], 2) if p["score"] is not None else None,
                    "plant_status": p["plant_status"]
                } for p in valid_custom
            ],
            "species_predictions": [
                {
                    "species": sp["species"],
                    "confidence": round(sp["score"], 2) if sp["score"] is not None else None
                } for sp in valid_species
            ]
        }
        return result
    except Exception as e:
        logging.error(f"Error processing image {image_path}: {e}")
        logging.debug(traceback.format_exc())
        return None


def process_folder(folder_path, progress_callback=None):
    """
    Process all image files in the given folder and return a list of results.
    Calls progress_callback(current, total) after each image is processed.

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


def write_json(results):

    # Prompt user to select a location and write the results to a JSON file.

    output_file = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All Files", "*.*")],
        title="Save Results As"
    )
    
    if not output_file:
        messagebox.showwarning("Save Cancelled", "No file selected. Results were not saved.")
        return None
    
    try:
        # Wrap the results list in a dictionary under the key "plant_data"
        output_data = {"plant_data": results}
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=4)
        return output_file
    except Exception as e:
        logging.error(f"Error writing JSON file: {e}")
        messagebox.showerror("Error", "An error occurred while saving the results.")
        return None

# ---------------------
# GUI Application with Threading
# ---------------------
class ImageClassifierApp:
    """
    GUI Application for the Plant Image Classifier.
    
    Provides functionality to select a folder, process images, and display progress.

    """
    def __init__(self, master):
        self.master = master
        master.title("Plant Image Classifier")
        master.geometry("500x300")
        
        # Configure style for progress bar.
        self.style = Style()
        self.style.theme_use("default")
        self.style.configure("blue.Horizontal.TProgressbar", foreground='blue', background='blue')

        # Label for model loading status.
        self.model_status_label = Label(master, text="Loading model...")
        self.model_status_label.pack(padx=10, pady=10)

        # Label with instructions for folder selection.
        self.label = Label(master, text="Select a folder containing images to process:")
        self.label.pack(padx=10, pady=5)

        # Button to select folder.
        self.select_button = Button(master, text="Select Folder", command=self.select_folder, state="disabled")
        self.select_button.pack(padx=10, pady=5)

        # Progress bar.
        self.progress = Progressbar(master, style="blue.Horizontal.TProgressbar", orient="horizontal", length=300, mode="determinate")
        self.progress.pack(padx=10, pady=10)

        # Label to display progress percentage.
        self.progress_label = Label(master, text="Progress: 0%")
        self.progress_label.pack(padx=10, pady=5)

        # Button to start processing images.
        self.process_button = Button(master, text="Process Images", command=self.start_processing, state="disabled")
        self.process_button.pack(padx=10, pady=10)

        # Button to launch visualization app.
        self.visualize_button = Button(master, text="Launch Visualization App", command=launch_visualization_app)
        self.visualize_button.pack(padx=10, pady=5)

        self.folder_path = None

        # Start a background thread to load the model and classifiers.
        threading.Thread(target=self.load_classifier, daemon=True).start()

    def load_classifier(self):
        """
        Load the classifier model, tokenizer, and classifier objects in a background thread.
        Once loaded, update the UI.

        """
        global custom_classifier, species_classifier, model, preprocess_train, preprocess_val, tokenizer
        try:
            # Preload the model and tokenizer via open_clip. This downloads or loads cached files.
            model, preprocess_train, preprocess_val = open_clip.create_model_and_transforms('hf-hub:imageomics/bioclip')
            tokenizer = open_clip.get_tokenizer('hf-hub:imageomics/bioclip')
            # Instantiate the classifiers.
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
                "Wild-oat", "Wild pansy", "Wild radish", "Winter wild-oat", "Yorkshire-fog"
            ])
            species_classifier = TreeOfLifeClassifier()
        except Exception as e:
            logging.error("Error loading classifier: " + str(e))
            self.master.after(0, lambda: messagebox.showerror("Error", "Failed to load classifier."))
            return

        # Once the model is loaded, update the UI in the main thread.
        self.master.after(0, self.classifier_loaded)

    def classifier_loaded(self):
        """
        Called in the main thread once the classifier has been loaded.
        Updates the UI elements to reflect the loaded state.
        """
        self.model_status_label.config(text="Model loaded.")
        self.select_button.config(state="normal")
        # Enable processing if a folder is already selected.
        if self.folder_path:
            self.process_button.config(state="normal")

    def select_folder(self):

        # Open a folder dialog for the user to select a folder.

        folder = filedialog.askdirectory(title="Select Folder with Images")
        if folder:
            self.folder_path = folder
            self.progress_label.config(text=f"Folder selected: {folder}")
            # Enable processing if model is already loaded.
            if custom_classifier is not None and species_classifier is not None:
                self.process_button.config(state="normal")
        else:
            self.progress_label.config(text="No folder selected.")

    def update_progress(self, current, total):

        # Update progress bar and label in the main thread.

        percent = int((current / total) * 100)
        self.progress["value"] = percent
        self.progress_label.config(text=f"Progress: {percent}% ({current} of {total})")

    def start_processing(self):
        """
        Start image processing in a background thread.
        Disables buttons during processing to prevent multiple runs.

        """
        if not self.folder_path:
            messagebox.showerror("Error", "Please select a folder first.")
            return

        # Disable buttons during processing.
        self.select_button.config(state="disabled")
        self.process_button.config(state="disabled")
        self.progress_label.config(text="Processing images...")
        self.progress["value"] = 0

        # Start the processing in a separate thread.
        threading.Thread(target=self.process_images_thread, daemon=True).start()

    def process_images_thread(self):

        # Background thread to process images and update progress via the main thread.

        results = process_folder(
            self.folder_path,
            progress_callback=lambda cur, tot: self.master.after(0, self.update_progress, cur, tot)
        )
        if not results:
            self.master.after(0, lambda: messagebox.showinfo("Result", "No valid image files found in the selected folder."))
            self.master.after(0, lambda: self.progress_label.config(text="Processing complete. No images processed."))
        else:
            output_file = write_json(results)
            if output_file:
                self.master.after(0, lambda: messagebox.showinfo("Success", f"Processing complete.\nResults saved to: {output_file}"))
                self.master.after(0, lambda: self.progress_label.config(text=f"Results saved to {output_file}"))
            else:
                self.master.after(0, lambda: messagebox.showerror("Error", "An error occurred while writing the results."))
                self.master.after(0, lambda: self.progress_label.config(text="Error writing results."))
        # Re-enable buttons in the main thread after processing.
        self.master.after(0, lambda: self.select_button.config(state="normal"))
        self.master.after(0, lambda: self.process_button.config(state="normal"))

# ---------------------
# Main Entry Point
# ---------------------
def main():

    #Initializes the Tkinter root and starts the main loop.

    root = Tk()
    app = ImageClassifierApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
