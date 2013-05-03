#!/usr/local/bin/python2.7
import config

import os
import sys
import getpass

import youtube_upload
from youtube_upload import debug

import lxml.etree
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

input_dir = config.upload_source_dir
output_dir = config.uploaded_files_dir
dry_run = True


if not(dry_run):
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
    
    upload_log = open(output_dir + '/upload_log.txt', 'a')

youtube_upload.init_parser()


#daten = urllib.urlopen("http://re-publica.de/schedule-data.xml").read()
#schedule = lxml.etree.fromstring(daten).getroottree()

#daten = unicode(daten, "utf8")
schedule = lxml.etree.parse("schedule-data.xml")
option_parser = youtube_upload.init_parser()
html_parser = HTMLParser()

default_options = option_parser.get_default_values()

files = [ str(a)+'.mp4' for a in [1532, 5051, 1981, 1137, 5866, 5134]]
#files = os.listdir(input_dir)
for index, filename in enumerate(files):
    
    #event_id =     '5115'
    event_id = os.path.splitext(filename)[0]
    event = schedule.xpath('.//event[@id="' + event_id + '"]')[0]
    
    persons = event.find('persons').getchildren()
    
    
    options = default_options
    
    title = event.find('title').text
    if len(persons) == 1:
        options.title = 're:publica 2013 ' + persons[0].text + ': ' + title
    elif len(persons) == 2:
        options.title = 're:publica 2013 ' + persons[0].text + ', ' + persons[1].text + ': ' + title
    else:
        options.title = 're:publica 2013: ' + title
    
    description = strip_tags(html_parser.unescape(event.find('description').text))
    options.description = '''Find out more at: http://13.re-publica.de/node/{event_id}

{abstract}
{description} 
'''.format({
        'event_id': event_id, 
        'abstract': event.find('abstract').text,
        'description': description[:1000] + (description[1000:] and '�'),
    })
    for p in persons:
        options.description += '[Vorname Nachname Speaker(1)] | Webseite | Twitter | Facebook \nWebseite Der Organisation'
    keywords = ['#rp13', 'rp13', 're:publica', 'republica', event.find('track').text, event.find('room').text] + [p.text for p in persons]
    options.keywords = ', ' . join(keywords)
    options.category = 'Education'
    options.private = True

    
    video_path = input_dir + '/' + filename;
    
    print options.title 
    print options.description
    print options.keywords
    print
    
    if not(dry_run):
        url = youtube_upload.upload_video(youtube, options, video_path, len(files), index)
        output.write(event_id + '\t' + url + "\n")
        upload_log.write(event_id + '\t' + url + "\n")
        os.rename(video_path, output_dir + '/' + filename)
