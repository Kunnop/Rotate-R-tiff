import rasterio
from rasterio.transform import Affine
from scipy.ndimage import rotate
import numpy as np

input_path = "C:/Users/Kunnop.ko/Downloads/R-TIFF-orthophoto_rotate.tif"   # Change to your input file
output_path = "C:/Users/Kunnop.ko/Downloads/rotated_61deg_cropped.tif"

angle = -61  # negative for clockwise

with rasterio.open(input_path) as src:
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

print(f"Cropped rotated image saved as {output_path}")
