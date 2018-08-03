import cv2
import numpy as np
import pytesseract
import os
from PIL import Image

"""Note:
    When installing tesseract ensure several things:
    -- pip install pytesseract
    -- Install tesseract from: https://github.com/UB-Mannheim/tesseract/wiki (use 3.05 stable)
    -- System variable path contains parent tesseract directory
    -- Create new environment variable called TESSDATA_PREFIX and point it to the parent tesseract directory
"""

class ImProcess():
    def __init__(self):
        # face cascades required for cat detection using detectMultiScale
        self.face_cascade = cv2.CascadeClassifier('haar_cascades/haarcascade_frontalcatface.xml')
        self.extended_face_cascade = cv2.CascadeClassifier('haar_cascades/haarcascade_frontalcatface_extended.xml')
        self.message = ''
        self.file = ''

    def cat_detect(self):
        """Uses haar cascades, taking trained features from the OpenCV github, to detect cats
        
        Returns:
        message -- a check for the main discord_bot.py file to count the number of cats
        """
        cat_image = cv2.imread("Source_Images/cat_image.jpg")
        # TODO: check whether the image declaration and conversion lines can be merged
        # greyscale is required for detectMultiScale
        cat_grey_image = cv2.cvtColor(cat_image, cv2.COLOR_BGR2GRAY)
        num_cats = 0
        cat_bounding_boxes = self.face_cascade.detectMultiScale(cat_grey_image, scaleFactor=1.1, minNeighbors=5, minSize=(50,50))
        for (i, (x, y, w, h)) in enumerate(cat_bounding_boxes):
            cv2.rectangle(cat_image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(cat_image, 'Cat #{}'.format(i + 1), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
            num_cats = i + 1

        cv2.imwrite('Results/cat_image_result.jpg', cat_image)
        """ TODO: alter the method of showing how many cats there are, options:
            -- return an integer and perform a check in discord_bot.py
            -- return an integer and insert into the bot's message string using .format
            -- leave it as is (not preferred)
        """
        if num_cats <= 0:
            self.message = 'There are no cats...'
        else:
            self.message = '{} cats detected'.format(num_cats)
        return self.message

    def tesseract_process(self):
        """Uses google's tesseract to recognise text in an image and return it as a single string
        
        Returns:
        text -- the text that has been detected after passing the image to tesseract
        """
        # can change path to image to scan for text
        tess_image = cv2.imread("Source_Images/tesseract_input.jpg", 0)
        tess_image = cv2.threshold(tess_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        filename = "Results/pytesseract_output.png"
        # TODO: write to a file with timestamp?
        cv2.imwrite(filename, tess_image)
        # PIL is used for reliability with formatting (as OpenCV uses BGR rather than RGB colour channels)
        text = pytesseract.image_to_string(Image.open(filename))
        os.remove(filename)
        
        if text is "":
            return ""
        else:
            return text