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