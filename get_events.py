import pandas as pd
import requests
from bs4 import BeautifulSoup   
from datetime import datetime, timedelta


class GetEvents(object):

    def __init__(self, url):

        # Scrape data from events page
        res = requests.get(url)
        soup = BeautifulSoup(res.content,'lxml')
        posts = soup.find_all('div', {'class':'post'})

        # Loop over events and gather data into dictionary
        attributes = ['event_title', 'date', 'time', 'event_location']
        events = []
        for post in posts:
            ext = {}
            for attribute in attributes:
                try:
                    ext[attribute] = post.find_all('div', {'class':attribute})[0].text
                except:
                    try:
                        ext[attribute] = post.find_all('span', {'class':attribute})[0].text
                    except:
                        print('Desired attribute \"{}\" not found'.format(attribute))

            event = self.post_to_event(ext)
            events.append(event)

        self.events = events

    # Convert CSS post format to Google Calendar API format
    @staticmethod
    def post_to_event(post):

        event = {}
        event["summary"] = post["event_title"]
        event["location"] = post["event_location"].replace('\n','').replace('Location:','')

        dt = (post["date"]+' '+post["time"]).replace('\n','')
        dt = datetime.strptime(dt, '%B %d, %Y %I:%M %p')
        event["start"] = {
            'dateTime': dt.strftime('%Y-%m-%dT%H:%M:%S-08:00'),
            'timeZone': 'America/Los_Angeles',
        }
        event["end"] = {
            'dateTime': (dt+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S-08:00'),
            'timeZone': 'America/Los_Angeles',
        }

        return event


if __name__ == '__main__':

    ge = GetEvents("http://www.cms.caltech.edu/seminars")
    print(ge.events)