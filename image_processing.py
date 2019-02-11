import cv2
import numpy as np
import pytesseract
import os
import requests
from PIL import Image
from urllib.request import urlretrieve, Request, urlopen
from urllib.error import HTTPError

"""
Note:
    When installing tesseract ensure several things:
    -- pip install pytesseract
    -- Install tesseract from: https://github.com/UB-Mannheim/tesseract/wiki (use 3.05 stable)
    -- System variable path contains parent tesseract directory
    -- Create new environment variable called TESSDATA_PREFIX and point it to the parent tesseract directory
"""

class ImageProcess():
    def __init__(self):
        # face cascades required for cat detection using detectMultiScale
        self.face_cascade = cv2.CascadeClassifier('haar_cascades/haarcascade_frontalcatface.xml')
        self.extended_face_cascade = cv2.CascadeClassifier('haar_cascades/haarcascade_frontalcatface_extended.xml')

    def detect_cat(self, cat_image) -> int:
        """
        Uses haar cascades, taking trained features from the OpenCV github, to detect cats
        
        Returns:
        message -- a check for the main discord_bot.py file to count the number of cats
        """
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
        return num_cats

    def tesseract_process(self, tess_image) -> str:
        """Uses google's tesseract to recognise text in an image and return it as a single string
        
        Returns:
        text -- the text that has been detected after passing the image to tesseract
        """
        # can change path to image to scan for text
        tess_image = cv2.cvtColor(tess_image, cv2.COLOR_BGR2GRAY)
        tess_image = cv2.threshold(tess_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        output = "Results/pytesseract_output.png"
        # TODO: write to a file with timestamp?
        cv2.imwrite(output, tess_image)
        # PIL is used for reliability with formatting (as OpenCV uses BGR rather than RGB colour channels)
        text = pytesseract.image_to_string(Image.open(output))
        os.remove(output)
        
        return text

    @staticmethod
    def scrape_image(url: str, optional_name: str = "") -> list:
        """
        Scrapes an image from the provided url

        Keyword arguments:
        url -- the URL of the image to webscrape

        Returns:
        image -- image object that has been acquired from the URL
        error_message -- if an error occurred the message for the bot to say is passed in this string
        """
        if ''.join(url.split(".")[-1:]) == "gif" and optional_name:
            with open(f"Other_Images/{optional_name}.gif", "wb") as gif_file:
                gif_file.write(requests.get(url).content)
            return

        error_message = ""
        image = []
        try:
            output = 'Source_Images/url_scrape_output.jpg'
            urlretrieve(url, output)
            image = cv2.imread(output)
        
        except FileNotFoundError as file_err:
            print(f"Error finding file: {file_err}")
            error_message = 'There is an error on my end, please wait...'

        except HTTPError as http_err:
            print(f"Error with HTTP: {http_err}")
            error_message = 'URL not accepted, image cannot be found'

        return image, error_message