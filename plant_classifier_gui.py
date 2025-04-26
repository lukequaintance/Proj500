#!/usr/bin/env python3
"""
Plant Image Classifier Application
"""
import json
import logging
import traceback
import threading
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import piexif
from tkinter import Tk, Toplevel, Button, Label, Listbox, Entry, END, messagebox, Scrollbar, filedialog
from tkinter.ttk import Progressbar, Style

import open_clip
from bioclip import CustomLabelsClassifier, TreeOfLifeClassifier, Rank

# ---------------------
# Configuration & Defaults
# ---------------------
@dataclass(frozen=True)
class Config:
    CONF_THRESHOLD_CUSTOM: float = 0.50
    CONF_THRESHOLD_SPECIES: float = 0.10
    HIGH_CONF_CUSTOM: float = 0.80
    HIGH_CONF_SPECIES: float = 0.10

cfg = Config()

# Default plant labels
DEFAULT_LABELS = [
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
    "Wild-oat", "Wild pansy", "Wild radish", "Winter wild-oat", "Yorkshire-fog", "Gorse", "Hawthorn",
]

# ---------------------
# Utility Functions
# ---------------------

# Launch a visualization app
def launch_visualization_app():
    subprocess.Popen([sys.executable, "Data_Visulisation_App.py"])

# Convert GPS coordinates to degrees
def convert_to_degrees(value):
    d = value[0][0] / value[0][1]
    m = value[1][0] / value[1][1]
    s = value[2][0] / value[2][1]
    return d + (m / 60.0) + (s / 3600.0)

# Extract geolocation from image metadata
def get_geolocation(image_path):
    try:
        exif = piexif.load(image_path)
        gps = exif.get("GPS", {})
        if not gps:
            return None, None
        lat = gps.get(piexif.GPSIFD.GPSLatitude)
        lat_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef)
        lon = gps.get(piexif.GPSIFD.GPSLongitude)
        lon_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef)
        if lat and lat_ref and lon and lon_ref:
            lat_ref = lat_ref.decode() if isinstance(lat_ref, bytes) else lat_ref
            lon_ref = lon_ref.decode() if isinstance(lon_ref, bytes) else lon_ref
            phi = convert_to_degrees(lat)
            if lat_ref.upper() != 'N': phi = -phi
            lam = convert_to_degrees(lon)
            if lon_ref.upper() != 'E': lam = -lam
            return phi, lam
        return None, None
    except Exception as e:
        logging.getLogger(__name__).error(f"GPS extraction error for {image_path}: {e}")
        logging.getLogger(__name__).debug(traceback.format_exc())
        return None, None

# ---------------------
# Classifier Manager
# ---------------------
class ClassifierManager:
    def __init__(self, cfg, labels):
        self.cfg = cfg
        self.custom = None
        self.species = None
        self.labels = labels

    # Load classifiers
    def load(self):
        open_clip.create_model_and_transforms('hf-hub:imageomics/bioclip')
        open_clip.get_tokenizer('hf-hub:imageomics/bioclip')
        if self.labels:
            self.custom = CustomLabelsClassifier(self.labels)
        self.species = TreeOfLifeClassifier()

# ---------------------
# Image Processing
# ---------------------
def process_image(image_path, manager: ClassifierManager, cfg: Config) -> dict:
    try:
        result = {
            "filename": Path(image_path).name,
            "image_path": image_path,
            "latitude": None,
            "longitude": None,
            "custom_predictions": [],
            "species_predictions": []
        }
        # Custom predictions
        if manager.custom:
            cpreds = manager.custom.predict(image_path)
            valid_c = [p for p in cpreds if p.get("score", 0) >= cfg.CONF_THRESHOLD_CUSTOM]
            if not valid_c:
                valid_c = [{"classification": "Uncertain", "score": None}]
            for p in valid_c:
                score = p.get("score") or 0
                p["plant_status"] = "harmful" if score >= cfg.HIGH_CONF_CUSTOM else "non-harmful"
            result["custom_predictions"] = [
                {"classification": p["classification"],
                 "confidence": round(p.get("score", 0), 2) if p.get("score") is not None else None,
                 "plant_status": p["plant_status"]}
                for p in valid_c
            ]
        # Species predictions
        spreds = manager.species.predict(image_path, Rank.SPECIES)
        valid_s = [p for p in spreds if p.get("score", 0) >= cfg.HIGH_CONF_SPECIES]
        if not valid_s:
            valid_s = [max(spreds, key=lambda x: x.get("score", 0), default={"species": "Unknown", "score": None})]
        result["species_predictions"] = [
            {"species": p["species"],
             "confidence": round(p.get("score", 0), 2) if p.get("score") is not None else None}
            for p in valid_s
        ]
        # Geolocation
        lat, lon = get_geolocation(image_path)
        result["latitude"] = round(lat, 6) if lat is not None else None
        result["longitude"] = round(lon, 6) if lon is not None else None
        return result
    except Exception as e:
        logging.getLogger(__name__).error(f"Error processing {image_path}: {e}")
        logging.getLogger(__name__).debug(traceback.format_exc())
        return None

# ---------------------
# Folder Processing & JSON
# ---------------------
def process_folder(folder_path, manager, cfg, progress_callback=None):
    image_paths = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        image_paths.extend(Path(folder_path).glob(ext))
    total = len(image_paths)
    results = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_image, str(img), manager, cfg): img for img in image_paths}
        for idx, fut in enumerate(as_completed(futures), start=1):
            res = fut.result()
            if res:
                results.append(res)
            if progress_callback:
                progress_callback(idx, total)
    return results

# Save results to JSON
def write_json(results):
    output_file = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All Files", "*.*")],
        title="Save Results As"
    )
    if not output_file:
        messagebox.showwarning("Save Cancelled", "No file selected.")
        return None
    try:
        with open(output_file, "w") as f:
            json.dump({"plant_data": results}, f, indent=4)
        return output_file
    except Exception as e:
        logging.getLogger(__name__).error(f"Error writing JSON: {e}")
        messagebox.showerror("Error", "Error saving results.")
        return None

# ---------------------
# GUI Application
# ---------------------
class ImageClassifierApp:
    def __init__(self, master):
        self.master = master
        master.title("Plant Image Classifier")
        master.geometry("550x420")
        self.style = Style()
        self.style.theme_use("default")
        self.style.configure("blue.Horizontal.TProgressbar", background='blue')

        # State
        self.labels = DEFAULT_LABELS.copy()
        self.manager = None
        self.folder_path = None

        # UI Elements
        Label(master, text="Customize your weed labels before loading the model:").pack(pady=5)
        Button(master, text="Customize Labels", command=self.open_label_editor).pack(pady=5)
        self.load_btn = Button(master, text="Load Model & Classifiers", command=self.load_classifier, state="disabled")
        self.load_btn.pack(pady=5)
        self.status_label = Label(master, text="Model not loaded.")
        self.status_label.pack(pady=10)

        Label(master, text="Select folder & process images:").pack(pady=5)
        self.select_btn = Button(master, text="Select Folder", command=self.select_folder, state="disabled")
        self.select_btn.pack(pady=5)
        self.progress = Progressbar(master, style="blue.Horizontal.TProgressbar",
                                    orient="horizontal", length=360, mode="determinate")
        self.progress.pack(pady=10)
        self.progress_label = Label(master, text="Progress: 0%")
        self.progress_label.pack(pady=5)
        self.process_btn = Button(master, text="Process Images", command=self.start_processing, state="disabled")
        self.process_btn.pack(pady=10)
        Button(master, text="Launch Visualization App", command=launch_visualization_app).pack(pady=5)

    # Open label editor
    def open_label_editor(self):
        editor = Toplevel(self.master)
        editor.title("Edit Weed Labels")
        lb = Listbox(editor, selectmode="single", width=40, height=15)
        lb.pack(side="left", fill="y", padx=5, pady=5)
        scroll = Scrollbar(editor, orient="vertical", command=lb.yview)
        scroll.pack(side="left", fill="y")
        lb.config(yscrollcommand=scroll.set)
        for label in self.labels:
            lb.insert(END, label)

        entry = Entry(editor)
        entry.pack(pady=5)

        def add_label():
            val = entry.get().strip()
            if val:
                self.labels.append(val)
                lb.insert(END, val)
                entry.delete(0, END)

        def remove_label():
            sel = lb.curselection()
            if sel:
                idx = sel[0]
                self.labels.pop(idx)
                lb.delete(idx)

        def remove_all():
            self.labels.clear()
            lb.delete(0, END)

        Button(editor, text="Add", command=add_label).pack(pady=2)
        Button(editor, text="Remove Selected", command=remove_label).pack(pady=2)
        Button(editor, text="Remove All", command=remove_all).pack(pady=2)

        def done():
            editor.destroy()
            self.load_btn.config(state="normal")

        Button(editor, text="Done", command=done).pack(pady=10)

    # Load classifier
    def load_classifier(self):
        self.manager = ClassifierManager(cfg, self.labels)
        threading.Thread(target=self._load_thread, daemon=True).start()
        self.status_label.config(text="Loading model...")
        self.load_btn.config(state="disabled")

    def _load_thread(self):
        try:
            self.manager.load()
            self.master.after(0, self.on_loaded)
        except Exception as e:
            logging.getLogger(__name__).error(f"Loading error: {e}")
            self.master.after(0, lambda: messagebox.showerror("Error", "Failed to load classifier."))

    def on_loaded(self):
        self.status_label.config(text="Model loaded.")
        self.select_btn.config(state="normal")

    # Select folder
    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Images")
        if folder:
            self.folder_path = folder
            self.progress_label.config(text=f"Folder: {folder}")
            self.process_btn.config(state="normal")

    # Update progress bar
    def update_progress(self, cur, tot):
        pct = int(cur / tot * 100)
        self.progress['value'] = pct
        self.progress_label.config(text=f"Progress: {pct}% ({cur}/{tot})")

    # Start processing images
    def start_processing(self):
        if not self.folder_path:
            messagebox.showerror("Error", "Please select a folder first.")
            return
        self.select_btn.config(state="disabled")
        self.process_btn.config(state="disabled")
        threading.Thread(target=self._process_thread, daemon=True).start()

    def _process_thread(self):
        results = process_folder(self.folder_path, self.manager, cfg,
                                 progress_callback=lambda c, t: self.master.after(0, self.update_progress, c, t))
        if results:
            out = write_json(results)
            if out:
                self.master.after(0, lambda: messagebox.showinfo("Success", f"Results saved to {out}"))
                self.master.after(0, lambda: self.progress_label.config(text=f"Saved to {out}"))
            else:
                self.master.after(0, lambda: messagebox.showerror("Error", "Error saving results."))
        else:
            self.master.after(0, lambda: messagebox.showinfo("Done", "No images processed."))
        self.master.after(0, lambda: self.select_btn.config(state="normal"))
        self.master.after(0, lambda: self.process_btn.config(state="normal"))

# ---------------------
# Main
# ---------------------
def main():
    root = Tk()
    app = ImageClassifierApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
