import rasterio
from rasterio.transform import Affine
from scipy.ndimage import rotate
import numpy as np
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import os

class GeoTIFFRotator(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("GeoTIFF Rotator")
        self.geometry("400x300")
        
        # Create main container
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(fill=BOTH, expand=YES)
        
        # Title
        title_label = ttk.Label(
            self.main_frame,
            text="GeoTIFF Rotator",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # File selection frame
        file_frame = ttk.Frame(self.main_frame)
        file_frame.pack(fill=X, pady=(0, 20))
        
        self.file_label = ttk.Label(
            file_frame,
            text="No file selected",
            font=("Helvetica", 10)
        )
        self.file_label.pack(side=LEFT, fill=X, expand=YES)
        
        self.select_btn = ttk.Button(
            file_frame,
            text="Select File",
            command=self.select_file,
            style="primary.TButton",
            width=15
        )
        self.select_btn.pack(side=RIGHT, padx=(10, 0))
        
        # Rotation angle frame
        angle_frame = ttk.Frame(self.main_frame)
        angle_frame.pack(fill=X, pady=(0, 20))
        
        angle_label = ttk.Label(
            angle_frame,
            text="Rotation Angle (clockwise):",
            font=("Helvetica", 10)
        )
        angle_label.pack(side=LEFT)
        
        # Create a frame for the spinbox and degree symbol
        spinbox_frame = ttk.Frame(angle_frame)
        spinbox_frame.pack(side=RIGHT)
        
        self.angle_var = ttk.IntVar(value=25)  # Default value
        self.angle_spinbox = ttk.Spinbox(
            spinbox_frame,
            from_=0,
            to=360,
            textvariable=self.angle_var,
            width=5,
            justify=CENTER
        )
        self.angle_spinbox.pack(side=LEFT, padx=(0, 5))
        
        degree_label = ttk.Label(
            spinbox_frame,
            text="°",
            font=("Helvetica", 10)
        )
        degree_label.pack(side=LEFT)
        
        # Status label
        self.status_label = ttk.Label(
            self.main_frame,
            text="Ready",
            font=("Helvetica", 10)
        )
        self.status_label.pack(pady=(0, 10))
        
        # Process button
        self.process_btn = ttk.Button(
            self.main_frame,
            text="Process",
            command=self.process_file,
            style="success.TButton",
            state=DISABLED,
            width=15
        )
        self.process_btn.pack()
        
        self.input_path = None

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select GeoTIFF file",
            filetypes=[("GeoTIFF files", "*.tif;*.tiff"), ("All files", "*.*")]
        )
        
        if file_path:
            self.input_path = file_path
            self.file_label.configure(text=os.path.basename(file_path))
            self.process_btn.configure(state=NORMAL)
            self.status_label.configure(text="File selected. Click Process to continue.")

    def process_file(self):
        if not self.input_path:
            return
            
        # Disable buttons during processing
        self.select_btn.configure(state=DISABLED)
        self.process_btn.configure(state=DISABLED)
        self.angle_spinbox.configure(state=DISABLED)
        self.status_label.configure(text="Processing...")
        
        try:
            # Create output directory
            output_dir = r"C:\Users\Kunnop.ko\Desktop\Thermal\M3T\Rotate_Crop"
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output path
            input_filename = os.path.basename(self.input_path)
            name_without_ext = os.path.splitext(input_filename)[0]
            output_path = os.path.join(output_dir, f"{name_without_ext}_cropped.tif")
            
            # Get rotation angle
            angle = self.angle_var.get()
            
            # Process the file
            with rasterio.open(self.input_path) as src:
                data = src.read(1)
                profile = src.profile.copy()
                old_transform = src.transform
                nodata = src.nodata if src.nodata is not None else 0

                # Rotate the image (reshape=True to fit all data)
                rotated = rotate(
                    data,
                    angle,
                    reshape=True,
                    order=1,
                    mode='constant',
                    cval=nodata
                )

                # Find the bounding box of non-nodata (non-zero) pixels
                mask = rotated > 0
                if not np.any(mask):
                    raise ValueError("All pixels are nodata after rotation.")

                rows = np.any(mask, axis=1)
                cols = np.any(mask, axis=0)
                row_min, row_max = np.where(rows)[0][[0, -1]]
                col_min, col_max = np.where(cols)[0][[0, -1]]

                # Crop the rotated image
                cropped = rotated[row_min:row_max+1, col_min:col_max+1]

                # Update the transform for the crop
                new_transform = old_transform * Affine.translation(
                    -((rotated.shape[1] - data.shape[1]) / 2 + col_min),
                    -((rotated.shape[0] - data.shape[0]) / 2 + row_min)
                )

                # Update profile for new shape
                profile.update({
                    'height': cropped.shape[0],
                    'width': cropped.shape[1],
                    'transform': new_transform,
                    'nodata': nodata
                })

                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(cropped.astype(data.dtype), 1)

            messagebox.showinfo("Success", f"Successfully saved to:\n{output_path}")
            self.status_label.configure(text="Processing complete!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
            self.status_label.configure(text="Processing failed!")
            
        finally:
            # Re-enable buttons
            self.select_btn.configure(state=NORMAL)
            self.process_btn.configure(state=NORMAL)
            self.angle_spinbox.configure(state=NORMAL)

if __name__ == "__main__":
    app = GeoTIFFRotator()
    app.mainloop()
