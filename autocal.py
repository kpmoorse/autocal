from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from get_events import GetEvents
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class AutoCal(object):

    def __init__(self):

        self.id = 'ebp8v9gv8n3gtu1iqlm1gd2u3o@group.calendar.google.com'
        self.event_list = []
        self.event_buffer = []
        self.service = []

        self.auth()
        self.get_old_events()

    def auth(self):

        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)

    def get_old_events(self):

        now = datetime.utcnow()
        pastweek = now - timedelta(days=7)
        pastweek = pastweek.isoformat() + 'Z' # 'Z' indicates UTC time
        events_result = self.service.events().list(calendarId=self.id, timeMin=pastweek,
                                        maxResults=100, singleEvents=True,
                                        orderBy='startTime').execute()
        events = events_result.get('items', [])
        self.event_list = events

    def get_new_events(self, url):

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

        self.event_buffer += events

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

    def create_event(self, event):

        event = self.service.events().insert(calendarId=self.id, body=event).execute()
        # print('Event created: %s' % (event.get('htmlLink')))

    def add_events(self, events):

        title_list = [x["summary"] for x in self.event_list]
        count = 0
        for event in events:
            if event["summary"] not in title_list:
                self.create_event(event)
                count += 1
        print("{} new events created".format(count))


if __name__ == '__main__':

    autocal = AutoCal()
    autocal.get_new_events("http://www.cms.caltech.edu/seminars")
    autocal.add_events(autocal.event_buffer)