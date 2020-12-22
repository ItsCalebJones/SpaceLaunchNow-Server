import logging
import urllib
import pytz

from datetime import datetime, timedelta

from api.models import RoadClosure, RoadClosureStatus
from bs4 import BeautifulSoup
from dateutil import tz

logger = logging.getLogger('bot.digest')


def get_road_closure():
    tzTex = pytz.timezone('US/Central')
    url = "http://www.cameroncounty.us/spacex/"
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    request = urllib.request.Request(url, headers={'User-Agent': user_agent})
    try:
        response = urllib.request.urlopen(request)
    except Exception as e:
        logger.error(e)
        return
    if response.code != 200:
        logger.error("Received bad response code %s" % response.code)
        return
    html_content = response.read()

    # Parse the html content
    soup = BeautifulSoup(html_content, "lxml")
    tableRows = []
    gdp_table = soup.find("table")
    gdp_table_data = gdp_table.tbody.find_all("tr")  # contains 2 rows
    for row in gdp_table_data:
        aux = ''
        for cell in row.find_all("td"):
            aux += str(cell.text.strip()) + '|'
        tableRows.append(aux[:-1])

    closures = []
    for row in tableRows:
        row = row.replace('a.m.', 'AM')
        row = row.replace('p.m.', 'PM')

        dtP1 = row.split('|')[1]
        dtP2 = row.split('|')[2]
        dtP2B = dtP2.split(' to ')[0].strip()
        dtP2E = dtP2.split(' to ')[1].strip()

        dtSta = dtP1 + ' ' + dtP2B
        staTex = tzTex.localize(datetime.strptime(dtSta, "%A, %b %d, %Y %I:%M %p"))

        dtEnd = dtP1 + ' ' + dtP2E
        endTex = tzTex.localize(datetime.strptime(dtEnd, "%A, %b %d, %Y %I:%M %p"))
        if 'PM' in dtP2B and 'AM' in dtP2E:
            endTex += timedelta(days=1)

        nowTex = datetime.now(tz=pytz.utc)

        if endTex < nowTex:
            continue

        name = row.split('|')[0]
        status = row.split('|')[3].replace('Closure ', '')
        closures.append([staTex, endTex, name, status])

    logger.info("Found %s closures" % len(closures))
    for closure in closures:
        window_start = closure[0].astimezone(tz.tzutc())
        window_end = closure[1].astimezone(tz.tzutc())
        status_text = closure[3]
        status, created = RoadClosureStatus.objects.get_or_create(name=status_text)
        try:
            obj = RoadClosure.objects.get(window_start__exact=window_start,
                                          window_end__exact=window_end)
            obj.status = status
        except RoadClosure.DoesNotExist:
            obj = RoadClosure.objects.create(title=closure[2],
                                             window_start=window_start,
                                             window_end=window_end,
                                             status=status)
            logger.info("Creating new Road Closure %s" % obj)
        obj.save()
