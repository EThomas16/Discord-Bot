import cv2
import numpy as np

IM_PATH = 'Source_Images/cat_image.jpg'
OUT_IM_PATH = 'Results/cat_image_result.jpg'
FACE_CASC = cv2.CascadeClassifier('haar_cascades/haarcascade_frontalcatface.xml')
EXT_FACE_CASC = cv2.CascadeClassifier('haar_cascades/haarcascade_frontalcatface_extended.xml')

def cat_detect() -> int:
    image = cv2.imread(IM_PATH)
    # grey image is created separately as colour image will be shown to the user at the end
    grey_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    num_cats = 0
    cat_bnd_boxes = FACE_CASC.detectMultiScale(grey_image, scaleFactor=1.1, minNeighbors=5, minSize=(50,50))
    # Draws bounding boxes onto the image, labelling each cat with a number
    for (i, (x, y, w, h)) in enumerate (cat_bnd_boxes):
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(image, f'Cat #{i + 1}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        num_cats = i + 1
    
    cv2.imwrite(OUT_IM_PATH, image)
    
    return num_cats