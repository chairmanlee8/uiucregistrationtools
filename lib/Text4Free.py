# Text4Free.py
# Written by Andrew Lee (github: smiley325)

import Image
import math
import mechanize
import re
import time
import urllib2

from copy import deepcopy

#
# Subroutines: CAPTCHA stuff
#

def line_template_correlation(dict, source, coef):
		# dict : {key Object, template Image}
		# source : Image
		# coef : correlation threshold [0,1]
		# returns an array of objects
		
		listAbscissa = []
		
		sourceWidth, sourceHeight = source.size
		sourcePix = source.load()
			
		for keyObject, templateImage in dict.items():		
			templateWidth, templateHeight = templateImage.size
			templateImagePix = templateImage.load()
			
			for x in range(sourceWidth-templateWidth):
				for y in range(sourceHeight-templateHeight):
					# match the template object
					n = 0
					diff = 0.0
					
					for xoffs in range(templateWidth):
						if (x + xoffs) >= sourceWidth or (x + xoffs) < 0:
							continue						
						for yoffs in range(templateHeight):
							if (y + yoffs) >= sourceHeight or (y + yoffs) < 0:
								continue
								
							n += 1
							sourceR, sourceG, sourceB = sourcePix[x+xoffs, y+yoffs]
							tempR, tempG, tempB = templateImagePix[xoffs, yoffs]
							diff += math.sqrt((sourceR-tempR)**2+(sourceG-tempG)**2+(sourceB-tempB)**2)/math.sqrt(3*(255**2))
							#import pdb; pdb.set_trace()
							
					if(1-diff/n > coef):
						# matched, add to list
						listAbscissa.append((x, keyObject))
						
		# sort listAbscissa and flatten
		sortedList = sorted(listAbscissa, key=lambda x: x[0])
		return [x[1] for x in sortedList]
		
def solve_captcha(filename):
	# Clean up the CAPTCHA so line_template_correlation can decode it
	timage = Image.open(filename).convert("RGB")
	timagePix = timage.load()
	timageWidth, timageHeight = timage.size

	for x in range(timageWidth):
		for y in range(timageHeight):
			if(timagePix[x,y] != (0, 0, 0)):
				timagePix[x,y] = (255, 255, 255)
				
	timage.save(filename)

	# Break the CAPTCHA
	pngimg = Image.open(filename).convert("RGB")
	captchaTemplates = {}

	for i in range(10):
		captchaTemplates[str(i)] = Image.open(str(i) + ".png").convert("RGB")
	
	solution = "".join(line_template_correlation(captchaTemplates, pngimg, 0.95))
	return solution
    
#
# Text4Free interface
#

class Text4Free(object):
    @staticmethod
    def send_text(message, phone, carrier):
        # Text my cell right now!!
        br = mechanize.Browser()
        br.set_handle_robots(False)

        br.open("http://www.text4free.net/")
        br.select_form(name="sendtext")
        br["numbers[]"] = str(phone)
        br["prov[]"] = [str(carrier)]
        br["message"] = str(message)
        
        # Grab the CAPTCHA
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(br._ua_handlers["_cookies"].cookiejar))
        resp = opener.open("http://www.text4free.net/seccode.php")
        pngdata = resp.read()
        pngfile = open('temp.png', 'wb')
        pngfile.write(pngdata)
        pngfile.close()
        
        br["secCode"] = solve_captcha('temp.png')
        resp = br.submit()