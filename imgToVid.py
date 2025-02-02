import cv2
import os
import glob

def images_to_video(image_folder, output_video, frame_rate=1, resolution=None):
    image_files = sorted(glob.glob(os.path.join(image_folder, "*.*")), key=os.path.getmtime)
    
    if not image_files:
        print("No images found in the folder!")
        return
    
    first_image = cv2.imread(image_files[0])
    
    if resolution:
        width, height = resolution
    else:
        height, width, _ = first_image.shape
    
    # Define video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 format
    out = cv2.VideoWriter(output_video, fourcc, frame_rate, (width, height))
    
    for img_file in image_files:
        img = cv2.imread(img_file)
        
        if img is None:
            print(f"Skipping invalid image: {img_file}")
            continue
        
        img = cv2.resize(img, (width, height))
        
        out.write(img)
    
    out.release()
    print(f"Video saved as {output_video}")

