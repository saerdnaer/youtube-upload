import config

import lxml.etree
import os

import youtube_upload
from youtube_upload import debug

import sys
import getpass

# python-gdata (>= 1.2.4)
import gdata.service

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


output = sys.stdout
youtube = None

input_dir = 'final'
output_dir = 'done'


#required_options = ["email", "title", "category"]

if config.password is None:
    password = getpass.getpass("Password for account <%s>: " % config.email)
elif config.password == "-":
    password = sys.stdin.readline().strip()
else:
    password = config.password
youtube = youtube_upload.Youtube(youtube_upload.DEVELOPER_KEY)
debug("Login to Youtube API: email='%s', password='%s'" %
      (config.email, "*" * len(password)))
try:
    youtube.login(config.email, password) #, captcha_token=options.captcha_token,
        #       captcha_response=options.captcha_response)
except gdata.service.BadAuthentication:
    raise youtube_upload.BadAuthentication("Authentication failed")
except gdata.service.CaptchaRequired:
    token = youtube.service.captcha_token
    message = [
        "Captcha request: %s" % youtube.service.captcha_url,
        "Re-run the command with: --captcha-token=%s --captcha-response=CAPTCHA" % token,
    ]
    raise youtube_upload.CaptchaRequired("\n".join(message))

youtube_upload.init_parser()


#daten = urllib.urlopen("http://re-publica.de/schedule-data.xml").read()
#schedule = lxml.etree.fromstring(daten).getroottree()

#daten = unicode(daten, "utf8")
schedule = lxml.etree.parse("schedule-data.xml")
option_parser = youtube_upload.init_parser()
html_parser = HTMLParser()

default_options = option_parser.get_default_values()

files = {'5115.mp4'}#os.listdir(input_dir)
for index, filename in enumerate(files):
    
    event_id =     '5115'
    #event_id = os.path.splitext(filename)[0]
    event = schedule.xpath('.//event[@id="' + event_id + '"]')[0]
    
    options = default_options
    options.title = event.find('title').text
    options.description = strip_tags(html_parser.unescape(event.find('description').text))
    options.category = 'Education'
    options.private = True
    options.keywords = {}
    
    video_path = input_dir + '/' + filename;
    
    print options.description
    
    url = youtube_upload.upload_video(youtube, options, video_path, len(files), index)
    output.write(event_id + '\t' + url + "\n")
    
    os.rename(video_path, output_dir + '/' + filename)
