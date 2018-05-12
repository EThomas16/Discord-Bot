import cv2
import numpy as np

class HaarClassifier():
    def __init__(self):
        self.image = cv2.imread('Source_Images/cat_image.jpg')
        self.grey_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.face_cascade = cv2.CascadeClassifier('haar_cascades/haarcascade_frontalcatface.xml')
        self.extended_face_cascade = cv2.CascadeClassifier('haar_cascades/haarcascade_frontalcatface_extended.xml')
        self.message = ''
        self.file = ''

    def cat_detect(self):
        num_cats = 0
        cat_bounding_boxes = self.face_cascade.detectMultiScale(self.grey_image, scaleFactor=1.1, minNeighbors=5, minSize=(50,50))

        for (i, (x, y, w, h)) in enumerate (cat_bounding_boxes):
            cv2.rectangle(self.image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(self.image, 'Cat #{}'.format(i + 1), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
            num_cats = i + 1

        cv2.imwrite('Results/cat_image_result.jpg', self.image)
        if num_cats <= 0:
            self.message = 'There are no cats...'
        else:
            self.message = '{} cats detected'.format(num_cats)
        return self.message