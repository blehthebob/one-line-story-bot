import cv2
import os
import glob

def images_to_video(image_folder, output_video, frame_rate=30, resolution=None):
    # Get all image files in the folder (supports common formats)
    image_files = sorted(glob.glob(os.path.join(image_folder, "*.*")), key=os.path.getmtime)
    
    if not image_files:
        print("No images found in the folder!")
        return
    
    # Read the first image to determine video resolution
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
        
        # Resize image if needed
        img = cv2.resize(img, (width, height))
        
        # Write frame to video
        out.write(img)
    
    out.release()
    print(f"Video saved as {output_video}")

# Example usage
image_folder = "path/to/images"  # Change this to your folder
output_video = "output_video.mp4"
frame_rate = 30  # Adjust as needed
resolution = (1280, 720)  # Set resolution (optional), or leave None for auto

images_to_video(image_folder, output_video, frame_rate, resolution)
