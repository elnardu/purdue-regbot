import time

import requests
from bs4 import BeautifulSoup
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo

from .boilerkey import BoilerKey

USER_AGENT = "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)"
ERROR_MESSAGE = "We are sorry, but the site has received too many requests. Please try again later."

from loguru import logger


# class RateLimitException(Exception):
#     pass


class PurdueApi():

    def __init__(self, username=None, boilerkey=None):
        self.username = username
        self.session = requests.Session()
        self.boilerkey = boilerkey

    def _auth(self):
        assert self.username

        doc = self.session.get(
            "https://www.purdue.edu/apps/account/cas/login")
        bsdoc = BeautifulSoup(doc.text, "html.parser")

        successMessage = bsdoc.find(
            'div', {'id': 'msg', 'class': 'success'})

        if successMessage:
            return

        ltParam = bsdoc.find(
            'input', {'name': 'lt', 'type': 'hidden'}).get('value')

        assert ltParam

        data = {
            "execution": "e1s1",
            "_eventId": "submit",
            "lt": ltParam,
            "password": self.boilerkey.generate_password(),
            "submit": "Login",
            "username": self.username
        }

        self.session.post(
            "https://www.purdue.edu/apps/account/cas/login", data=data)

    @on_exception(expo, RateLimitException)
    @limits(calls=1, period=5)
    def getSectionDataByCRN(self, term, crn):
        res = requests.get(
            "https://selfservice.mypurdue.purdue.edu/prod/bwckschd.p_disp_detail_sched",
            headers={
                "User-Agent": USER_AGENT
            },
            params={
                "term_in": term,
                "crn_in": crn
            }
        )

        if ERROR_MESSAGE in res.text:
            # logger.warn("Too many requests to purdue class api. Retrying..")
            raise RateLimitException("", 1)

        bsdoc = BeautifulSoup(res.text, "html.parser")

        courseTitle = bsdoc.find(
            "th", {"class": "ddlabel", "scope": "row"}).get_text()

        availTable = bsdoc.find("table", {
            "summary": "This layout table is used to present the seating numbers."}).find_all("tr")

        availSeats = availTable[1].find_all("td")
        availWaitlistSeats = availTable[2].find_all("td")

        restrictions = str(bsdoc.find(
            "td", {"class": "dddefault"}).contents[-1])
        si = restrictions.find(
            '<span class="fieldlabeltext">Restrictions:</span>')
        si += len('<span class="fieldlabeltext">Restrictions:</span>')
        fi = restrictions.find('<span', si)
        restrictions = restrictions[si:fi].replace(
            "\n", "").replace("<br/>", "\n").strip()

        course_struct = {
            "title": courseTitle,
            "restrictions": restrictions,
            "crn": crn,

            "seats_capacity": int(availSeats[0].get_text()),
            "seats_actual": int(availSeats[1].get_text()),
            "seats_remaining": int(availSeats[2].get_text()),

            "waitlistseats_capacity": int(availWaitlistSeats[0].get_text()),
            "waitlistseats_actual": int(availWaitlistSeats[1].get_text()),
            "waitlistseats_remaining": int(availWaitlistSeats[2].get_text())
        }

        return course_struct

    def getClassDataByNumber(self, term, subjectCode, number):
        res = requests.get(
            "https://selfservice.mypurdue.purdue.edu/prod/bwckctlg.p_display_courses",
            headers={
                "User-Agent": USER_AGENT,
                "Referer": "https://selfservice.mypurdue.purdue.edu/prod/bwckschd.p_get_crse_unsec"
            },
            params={
                "term_in": term,
                "one_subj": subjectCode,
                "sel_crse_strt": number,
                "sel_crse_end": number,
                "sel_subj": "",
                "sel_levl": "",
                "sel_schd": "",
                "sel_coll": "",
                "sel_divs": "",
                "sel_dept": "",
                "sel_attr": ""
            }
        )

        print(res.text)

