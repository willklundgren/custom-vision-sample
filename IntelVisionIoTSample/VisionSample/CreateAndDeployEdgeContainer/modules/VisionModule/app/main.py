"""
 Copyright (c) 2019 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

 Usage : $python3 main.py <customvision onnx model url>
 Author: Pradeep, Sakhamoori <pradeep.sakhamoori@intel.com>
 
"""

import sys, os
import onnxruntime
import numpy as np
import cv2
import json

from object_detection import ObjectDetection

class ONNXRuntimeObjectDetection(ObjectDetection):
    """Object Detection class for ONNX Runtime
    """
    def __init__(self, config_filename):

        f = open(config_filename)
        data = json.load(f)

        self.model_filename = str(data["MODEL_FILENAME"])
        self.label_filename = str(data["LABELS_FILENAME"])
        self.video_inp = str(data["Input"])
        self.model_inp_width = int(data["ScaleWidth"])
        self.model_inp_height = int(data["ScaleHeight"])
        self.disp = int(data["display"])
        self.anchors = np.array(data["Anchors"])
        self.iou_threshold = data["IOU_THRESHOLD"]
        self.input_format = str(data["InputFormat"])

        with open(self.label_filename, 'r') as f:
            labels = [l.strip() for l in f.readlines()]

        super(ONNXRuntimeObjectDetection, self).__init__(labels)
        print("\n Triggering Inference...")
        self.session = onnxruntime.InferenceSession(self.model_filename)
        print("\n Started Inference...")
        self.input_name = self.session.get_inputs()[0].name 
        if self.disp == 0:
           print("Press Ctl+C to exit...")
  
    def predict(self, preprocessed_image):
        inputs = np.array(preprocessed_image, dtype=np.float32)[np.newaxis,:,:,(2,1,0)] # RGB -> BGR
        inputs = np.ascontiguousarray(np.rollaxis(inputs, 3, 1))
        outputs = self.session.run(None, {self.input_name: inputs})
        return np.squeeze(outputs).transpose((1,2,0))

def main():
    
    # Config file for Object Detection
    ret = os.path.exists('../model/model.config')

    # Check for model.config file
    if ret is False:
       print("\n ERROR: No model.config file found under model dir")
       print("\n Exisiting....")
       model_dir_clean_up("../model")
       sys.exit(0)

    od_model = ONNXRuntimeObjectDetection("../model/model.config")

    cap = cv2.VideoCapture(0)
    # Reading widht and height details
    img_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    img_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if cap == None:
       print("Error: Input Camera device not found/detected")

    color = (255, 0 , 0)
    thickness = 2
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 1

    while(True):
       # Caputre frame-by-frame
       ret, frame = cap.read()
       predictions = od_model.predict_image(frame)

       for d in predictions:
           x = int(d['boundingBox']['left'] * img_width)
           y = int(d['boundingBox']['top'] * img_height)
           w = int(d['boundingBox']['width'] * img_width)
           h = int(d['boundingBox']['height'] * img_height)

           x_end = x+w
           y_end = y+h

           start = (x,y)
           end = (x_end,y_end)

           frame = cv2.rectangle(frame,start,end,color,thickness)
           out_label = str(d['tagName'])
           score = str(int(d['probability']*100))
           frame = cv2.putText(frame, out_label, (x-5, y), font,
                   fontScale, color, thickness, cv2.LINE_AA)
           frame = cv2.putText(frame, score, (x+w-50, y), font,
                   fontScale, color, thickness, cv2.LINE_AA)

       if od_model.disp == 1:
           # Displaying the image
           cv2.imshow("Inference results", frame)
           if cv2.waitKey(1) & 0xFF == ord('q'):
              break
       else:
          for d in predictions:
             print("Object(s) List: ", str(d['tagName'])) 

       #input("Press Enter to continue...")
       #print(predictions)
    
    # when everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print('USAGE: {} customvision Vision DevKit url (with onnx model)'.format(sys.argv[0]))
    else:
        main(sys.argv[1])