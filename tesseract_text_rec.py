import pytesseract
import cv2
import os
from PIL import Image

"""Note:
    When installing tesseract ensure several things:
    -- pip install pytesseract
    -- Install tesseract from: https://github.com/UB-Mannheim/tesseract/wiki (use 3.05 stable)
    -- System variable path contains parent tesseract directory
    -- Create new environment variable called TESSDATA_PREFIX and point it to the parent tesseract directory

    TODO:
    -- crop based on colour
    -- then, once that works crop based on change in colour (since text stands out)
"""
# can change path to image to scan for text
image = cv2.imread("Source_Images/cropped_input.png", 0)

thresholding = input("Please enter the thresholding method to use: thresh or blur\n")

if thresholding is "thresh":
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

elif thresholding is "blur":
    image = cv2.medianBlur(image, 3)

filename = "Results/pytesseract_output.png"
cv2.imwrite(filename, image)
# gets the text from the tesseract model
text = pytesseract.image_to_string(Image.open(filename))
os.remove(filename)
# TODO: write to a file with timestamp?
if text is "":
    print("No text detected, please try again...")
else:
    print(text)
# can remove if not required, for testing
'''image = cv2.resize(image, None, fx=0.2, fy=0.2)
cv2.imshow("Image", image)
cv2.waitKey(0)
cv2.destroyAllWindows()'''