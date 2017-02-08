
import pprint

import json # for configuration file

from datetime import datetime
import caldav
import urllib3
from caldav.elements import dav, cdav

from ics import Calendar

from flask import Flask
from flask_ask import Ask, statement

from datetime import timedelta
app = Flask(__name__)
ask = Ask(app, '/')

def connectCalendar():
    with open('../conf/config.json') as json_data_file:
        data = json.load(json_data_file)

    client = caldav.DAVClient(data["url"], username=data["username"], password=data["password"])
    principal = client.principal()
    return principal.calendars()

def getCalDavEvents(begin, end):

  calendars = connectCalendar()

  speech_text = "Ich konnte mich leider nicht mit dem Kalender verbinden"

  if len(calendars) > 0:
      calendar = calendars[0]
      results = calendar.date_search(begin,end)

      if len(results)>0:
          flatten = lambda l: [item for sublist in l for item in sublist]
          eventList = flatten([Calendar(event._data).events for event in results])
          sortedEventList = sorted(eventList,key=lambda icsEvent: icsEvent.begin)

          #pp = pprint.PrettyPrinter(indent=4)
          #pp.pprint(sortedEventList)

          speech_text = "<speak>\n"
          speech_text += '  Es sind folgende Termine auf dem Kalender: <break time="1s"/>\n'
          for icsEvent in sortedEventList:
              speech_text += '  '+icsEvent.begin.humanize(locale='de') + " ist " + icsEvent.name + '.<break time="1s"/>\n'
          speech_text += "</speak>"
      else:
          speech_text = "Es sind keine Termine eingetragen heute"

  return speech_text

#@ask.intent('GetTodayEventsIntent')
#def getTodayEvents():
#    speech_text = getCalDavEvents(datetime.now(), datetime.now() + timedelta(days=1))
#    print(speech_text)
#    return statement(speech_text).simple_card('Kalendertermine', speech_text)

@ask.intent('GetEventsIntent',
    mapping={'date': 'Date', 'enddate' : 'EndDate'}, convert={ 'date': 'date', 'enddate': 'date' })
def getDateEvents(date, enddate):

    print(str(date) + " " + str(type(date)))
    print(str(enddate) + " " + str(type(enddate)))

    # in case that default "enddate" does not comply to "date",
    # the enddate is set to end of the day of "date"
    if date==None:
        date=datetime.now()

    if enddate==None or date>=enddate:
        enddate = datetime(date.year, date.month, date.day+1)

    print(str(date))
    print(str(enddate))

    speech_text = getCalDavEvents(date, enddate)
    print(speech_text)
    return statement(speech_text).simple_card('Kalendertermine', speech_text)

@ask.intent('SetEventIntent',
    mapping={'date': 'Date', 'time': 'Time', 'duration' : 'Duration' },
    convert={'date': 'date', 'time':'time', 'duration' : 'timedelta'})
def setEvent(date, time, duration):
    d = datetime.combine(date,time)

    print(date)
    print(time)
    print(duration)

    creationDate = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    startDate = d.strftime("%Y%m%dT%H%M%SZ")
    endDate = (d + duration).strftime("%Y%m%dT%H%M%SZ")

    vcal = "BEGIN:VCALENDAR"+"\n"
    vcal += "VERSION:2.0"+"\n"
    vcal += "PRODID:-//Example Corp.//CalDAV Client//EN"+"\n"
    vcal += "BEGIN:VEVENT"+"\n"
    vcal += "UID:1234567890"+"\n"
    vcal += "DTSTAMP:" + creationDate +"\n"
    vcal += "DTSTART:" + startDate +"\n"
    vcal += "DTEND:" + endDate +"\n"
    vcal += "SUMMARY:" + "FooBar"+"\n"
    vcal += "END:VEVENT"+"\n"
    vcal += "END:VCALENDAR"

    print(vcal)


    calendars = connectCalendar()
    speech_text = "Termin konnte nicht eingetragen werden!"

    if len(calendars) > 0:
        calendar = calendars[0]
        event = calendar.add_event(vcal)
        speech_text = "Termin wurde eingetragen!"


    return statement(speech_text).simple_card('Kalendertermine', speech_text)




#print getTodayEvents()
if __name__ == '__main__':
    app.run(host="0.0.0.0")
