# coding: utf-8

# In[2]:


from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from lxml import etree, html
from rtl import reshaper
from PIL import Image as pil

import re
from reportlab.pdfgen.canvas import Canvas
from tesserocr import PyTessBaseAPI
from bidi.algorithm import get_display
import io
import base64
from PyPDF2 import PdfFileWriter,PdfFileReader
from wand.image import Image
# In[4]:

arabic2persian={'ك':'ک','ي':'ی','ة':'ه','ﺁ':'آ','ﻳ':'ی','ﻴ':'ی','ﻰ':'ی','ﻱ':'ی','ي':'ی','آ':'آ','ﺁ':'آ','ﺋ':'ئ','ﻯ':'ی'}


def _multiple_replace(mapping, text):
    """
    Internal function for replace all mapping keys for a input string
    :param mapping: replacing mapping keys
    :param text: user input string
    :return: New string with converted mapping keys to values
    """
    pattern = "|".join(map(re.escape, mapping.keys()))
    return re.sub(pattern, lambda m: mapping[m.group()], str(text))


def polyval(poly, x):
    return x * poly[0] + poly[1]


def get_farsi_text(word):
    # print ('in get_farsi_text method...')
    # print('text dakhel function get %%%%%%%%',word)
    if reshaper.has_arabic_letters(word):
        # for reshaping and concating words
        reshaped_text = reshaper.reshape(word)
        reshaped_text = _multiple_replace(arabic2persian, reshaped_text)
        # for right to left
        bidi_text = get_display(reshaped_text)
        reshaped_words = bidi_text
    else:
        reshaped_words = word
    # reshaped_words.reverse()
    return reshaped_words


def add_text_layer(pdf, hocrfile, image, height, dpi, pathim):
    print ('in add text_layer method ...')
    # pathf=pathim.split('.')[0]
    """Draw an invisible text layer for OCR data"""
    p1 = re.compile('bbox((\s+\d+){4})')
    p2 = re.compile('baseline((\s+[\d\.\-]+){2})')

    hocr = etree.fromstring(hocrfile, html.XHTMLParser())
    for line in hocr.xpath('//*[@class="ocr_line"]'):
        # print ('line:',line)
        linebox = p1.search(line.attrib['title']).group(1).split()
        # print ('linebox:',linebox)
        try:
            baseline = p2.search(line.attrib['title']).group(1).split()
            # print ('baseline:',baseline)
        except AttributeError:
            baseline = [0, 0]
        linebox = [float(i) for i in linebox]
        baseline = [float(i) for i in baseline]
        xpath_elements = './/*[@class="ocrx_word"]'
        if (not (line.xpath('boolean(' + xpath_elements + ')'))):
            # if there are no words elements present,
            # we switch to lines as elements
            # print ('in if (not(....')
            xpath_elements = '.'
        for word in line.xpath(xpath_elements):
            rawtext = word.text_content().strip()
            # print ('rawtext:', rawtext)
            if rawtext == '':
                continue

            box = p1.search(word.attrib['title']).group(1).split()
            # print ('first box:', box)
            box = [float(i) for i in box]
            # print ('second box:', box)
            # width_of_box = box[2] - box[0]
            height_of_box = box[3] - box[1]
            # print('width of box:', width_of_box)
            # print('height of box:', height_of_box)
            font_size = int((height_of_box * 72) / dpi)  # font=Box height per inch
            # print('font size', font_size)
            font_width = pdf.stringWidth(rawtext, 'BZar', font_size)
            """
            stringWidth 3 vorudi daryaft mikonad: string,font,font size
            khoruchi toole string bar asas font size ast
            """
            if font_width <= 0:
                continue
            # print ('font_with:', font_width)
            b = polyval(baseline,
                        (box[0] + box[2]) / 2 - linebox[0]) + linebox[3]
            # print ('b:', b)
            text = pdf.beginText()
            text.setTextRenderMode(3)  # double invisible
            text.setFont('BZar', font_size)
            text.setTextOrigin(box[0] * 72 / dpi, height - (b * 72) / dpi)
            # box_width = (box[2] - box[0]) * 72 / dpi
            # text.setHorizScale(100.0 * width_of_box / font_width)
            tw = get_farsi_text(rawtext)
            text.textLine(tw)
            # print('text.textLine(rawtext)',text.textLine(rawtext))
            pdf.drawText(text)
            # print ('text:',text,'type:',type(text))
            # print ('***************************')


def main( images_list, hocr_list, outpath):
    # """Create a searchable PDF from a pile of HOCR + JPEG"""
    print ('in hocrTOpdf.main method...')
    pdfmetrics.registerFont(TTFont('BZar', '/home/toocr/.fonts/truetype/XBZar/Zar/XB Zar.ttf'))
    # buffer=io.BytesIO()
    pdf = Canvas(outpath, pageCompression=1)
    pdf.setCreator('hocr-tools')
    pdf.setTitle('searchablePDF')

    i = 0
    for image in images_list:
        # im = Image.open(io.BytesIO(image))
        with Image(file=io.BytesIO(image)) as background:
            w, h = background.size
            with Image(filename="watermark1.png") as watermark:
                w_w, h_w = watermark.size
                x1 = int(w / 2) - int(w_w / 2)
                y1 = int(h / 2) - int(h_w / 2)
                background.watermark(watermark, 0.75, x1, y1)

                page_jpeg_bytes = background.make_blob(format="png")
                background.save(filename='result.png')
                page_jpeg_data = io.BytesIO(page_jpeg_bytes)
                im = pil.open(page_jpeg_data)
                # print(type(im))
                try:
                    print('dpi')
                    dpi = im.info['dpi'][0]

                except KeyError:
                    dpi = 72

                width = w * 72 / dpi
                height = h * 72 / dpi
                pdf.setPageSize((width, height))
                # print (type(im))
                side_out = ImageReader(im)  ##baraie in ke imaage PIL be drawImage bedam az ImageReader estefade kardam.
                pdf.drawImage(side_out, 0, 0, width=width, height=height)
                add_text_layer(pdf, hocr_list[i], im, height, dpi, outpath)
                pdf.showPage()
                i = i + 1


    pdf.save()






