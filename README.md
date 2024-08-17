# Face Detection and Tracking Model
This repository contains a face detection and tracking model using OpenCV's pre-trained Caffe model (res10_300x300_ssd_iter_140000.caffemodel) for face detection and Deep SORT (Simple Online and Realtime Tracking with a Deep Association Metric) for tracking.

## Overview
Face Detection: Utilizes the res10_300x300_ssd_iter_140000.caffemodel pre-trained model to detect faces in images or video frames.
Face Tracking: Uses Deep SORT to track detected faces across multiple frames.
## Getting Started
To get started with the project, follow these steps:

## Prerequisites
Python 3.x
OpenCV
Deep SORT
Other dependencies (listed in requirements.txt)

## Installation
1. **Clone the repository**:

   ```
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
2. **Install the required Python packages**:

```pip install -r requirements.txt```

## Download the Pre-trained Model
1. **Download the Caffe model**:

    You need to download the res10_300x300_ssd_iter_140000.caffemodel file. You can download it from the official OpenCV repository.

2. **Save the model**:

    Save the downloaded res10_300x300_ssd_iter_140000.caffemodel file in the models folder of the repository. Create the models folder if it does not exist:

## Run Face Detection and Tracking:

You can run the face detection and tracking script on a video file or webcam feed. Replace input_video.mp4 with the path to your video file, or use 0 for webcam input.

```python main_face.py --input input_video.mp4 --output output_video.mp4```
## Options:

--input: Path to the input video file or 0 for webcam.

--output: Path to save the output video with tracked faces.

## Example
Here is an example command to run the script:

```python main_face.py --input video.mp4 --output tracked_output.mp4```

## Example

Here is an example of the face detection and tracking model in action:


<img src="output/Screenshot%20(14).png" alt="Face Detection Example" width="500"/>

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
OpenCV for providing the pre-trained Caffe model.
Deep SORT for robust tracking.
