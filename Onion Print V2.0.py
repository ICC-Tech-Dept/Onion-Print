'''

Main
Version 2.0.1 Insider Preview

Added Explainations
Modified Layout

'''

__author__ = 'DessertFox-M'
__original_design__ = '-T.K.-'
__created_on__ = '5/27/2019'
__last_modify__ = '5/27/2019'
__descended_from__ = 'Onion Print V1.4'

import itchat
import time
import os
import datetime
from PyPDF2 import PdfFileReader, PdfFileWriter
import win32print
import win32api
# logging is not included


'''Variables'''
# Request Storage
data = []
# Global Variable
val = {
    # Stage of Process
    'status': 0,
    # Time of QR Send
    'submit_time': 0,
    # Time of Printing of the first side in double sided printing
    'continue_time': 0,
    # Black and White Price
    'black': 0.10,
    # Color Price
    'color': 0.50,
    # Used to number the files received
    'number': 0,
    # Color Printer Name
    'color_printer': 'Canon LBP7010C/7018C',
    # Black Only Printer Name
    'black_printer': 'HP LaserJet Professional M1136 MFP',
}


# Set black printer as default
win32print.SetDefaultPrinter(val['black_printer'])


class User:
    black = 0.1
    color = 0.5

    def __init__(self, name, wechat, filename, price, color, orientation, double, number):
        self.name = name
        self.wechat = wechat
        self.filename = filename
        self.price = price
        self.color = color
        self.orientation = orientation
        self.double = double
        self.number = number

    def total_page(self):
        pages = PdfFileReader(self.filename).getNumPages()

    def total_price(self):
        if color == 0:
            price = self.price *
