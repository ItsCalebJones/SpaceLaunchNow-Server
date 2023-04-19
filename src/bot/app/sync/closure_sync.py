import logging
import urllib
from datetime import datetime, timedelta

import pytz
from api.models import RoadClosure, RoadClosureStatus
from bs4 import BeautifulSoup
from dateutil import parser, tz

logger = logging.getLogger(__name__)

user_agent = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/35.0.1916.47 "
    "Safari/537.36"
)


def parse_date(date_string):
    tzTex = pytz.timezone("US/Central")
    try:
        datetime = tzTex.localize(parser.parse(date_string))
    except Exception:
        datetime = tzTex.localize(parser.parse(date_string.split(", ", 1)[1]))
    return datetime


def get_road_closure():

    url = "https://www.cameroncountytx.gov/spacex/"
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
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
    gdp_table = soup.find_all("tbody")
    gdp_table_data = []
    for table in gdp_table:
        gdp_table_data.append(table.find_all("tr"))  # contains 2 rows
    for table in gdp_table_data:
        for row in table:
            aux = ""
            for cell in row.find_all("td"):
                aux += str(cell.text.strip()) + "|"
            tableRows.append(aux[:-1])

    closures = []
    for row in tableRows:
        try:
            if len(row) > 3:
                row = row.replace("a.m.", "AM")
                row = row.replace("p.m.", "PM")

                start_date = row.split("|")[1]
                closure_time = row.split("|")[2]
                start_time = closure_time.split(" to ")[0].strip()
                closure_end = closure_time.split(" to ")[1].strip()

                start_string = start_date + " " + start_time
                start_datetime = parse_date(start_string)

                now = datetime.now(tz=pytz.utc)
                if "of" in closure_end:
                    closure_end = closure_end.split("of")[0].strip()
                if "–" in closure_end:
                    end_date = closure_end.split("–")[0].strip()
                    end_time = closure_end.split("–")[1].strip()
                    end_date = datetime.strptime(end_date, "%B %d").replace(year=now.year).strftime("%A, %B %d, %Y")
                    end_string = end_date + " " + end_time
                else:
                    end_string = start_date + " " + closure_end
                end_datetime = parse_date(end_string)
                if end_datetime < start_datetime:
                    end_datetime += timedelta(days=1)
                print(f"start: {start_datetime} end: {end_datetime}")

                if end_datetime < now:
                    print("skipping as end date is in the past")
                    continue

                name = row.split("|")[0]
                status = row.split("|")[3].replace("Closure", "").strip()
                closures.append([start_datetime, end_datetime, name, status])
        except Exception as e:
            logger.error(row)
            logger.error(e)
            continue

    logger.info("Found %s closures" % len(closures))
    for closure in closures:
        window_start = closure[0].astimezone(tz.tzutc())
        window_end = closure[1].astimezone(tz.tzutc())
        status_text = closure[3]
        status, created = RoadClosureStatus.objects.get_or_create(name=status_text)
        try:
            obj = RoadClosure.objects.get(window_start__exact=window_start, window_end__exact=window_end)
            obj.status = status
        except RoadClosure.DoesNotExist:
            obj = RoadClosure.objects.create(
                title=closure[2], window_start=window_start, window_end=window_end, status=status
            )
            logger.info("Creating new Road Closure %s" % obj)
        obj.save()
