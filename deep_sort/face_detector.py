import cv2
import os
import numpy as np
def get_face_detector(model_param_path):
    """
    Get the face detection caffe model of OpenCV's DNN module
    
    Parameters
    ----------
    modelFile : string, optional
        Path to model file. The default is "models/res10_300x300_ssd_iter_140000.caffemodel" or models/opencv_face_detector_uint8.pb" based on quantization.
    configFile : string, optional
        Path to config file. The default is "models/deploy.prototxt" or "models/opencv_face_detector.pbtxt" based on quantization.
    quantization: bool, optional
        Determines whether to use quantized tf model or unquantized caffe model. The default is False.
    
    Returns
    -------
    model : dnn_Net
    """
    modelFile = os.path.join(model_param_path,"res10_300x300_ssd_iter_140000.caffemodel")
    configFile = os.path.join(model_param_path,"deploy.prototxt")
    model = cv2.dnn.readNetFromCaffe(configFile, modelFile)
    model.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    model.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)
    return model
model_param_path=r"D:\AKS\Reflexion-AI-Face-ms - Copy\Models\Emotion_recogntion"
detector = get_face_detector(model_param_path)

def face_detector(frame):
    #frame=cv2.imread(image,1)
    h, w = frame.shape[:2]
    size = frame.shape
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    detector.setInput(blob)
    faces = detector.forward()
    boxes=[]
    confs=[]
    for i  in range(0, faces.shape[2]):                
        confidence = faces[0, 0, i, 2]                
        if confidence > 0.1:
            box = faces[0, 0, i, 3:7] * np.array([w, h, w, h])
            boxes.append(box)
            confs.append(confidence)
    boxes = np.array(boxes)
    confs = np.array(confs)
    return boxes,confs