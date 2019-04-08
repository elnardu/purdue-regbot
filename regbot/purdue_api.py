import requests
from bs4 import BeautifulSoup
from boilerkey import generatePassword

import time

USER_AGENT = "Mozilla/5.0 (compatible; MSIE 10.0; Macintosh; Intel Mac OS X 10_7_3; Trident/6.0)"

class PurdueApi():
    def __init__(self, username=None):
        self.username = username
        self.session = requests.Session()

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
            "password": generatePassword(),
            "submit": "Login",
            "username": self.username
        }

        self.session.post(
            "https://www.purdue.edu/apps/account/cas/login", data=data)

    @classmethod
    def getSectionDataByCRN(cls, term, crn):
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
        # print(res.text)
        bsdoc = BeautifulSoup(res.text, "html.parser")

        courseTitle = bsdoc.find(
            "th", {"class": "ddlabel", "scope": "row"}).get_text()

        availTable = bsdoc.find("table", {
            "summary": "This layout table is used to present the seating numbers."}).find_all("tr")

        availSeats = availTable[1].find_all("td")
        availWaitlistSeats = availTable[2].find_all("td")

        availability = {
            "seats_capacity": int(availSeats[0].get_text()),
            "seats_actual": int(availSeats[1].get_text()),
            "seats_remaining": int(availSeats[2].get_text()),

            "waitlistseats_capacity": int(availWaitlistSeats[0].get_text()),
            "waitlistseats_actual": int(availWaitlistSeats[1].get_text()),
            "waitlistseats_remaining": int(availWaitlistSeats[2].get_text())
        }
        print(availability)

        restrictions = str(bsdoc.find(
            "td", {"class": "dddefault"}).contents[-1])
        si = restrictions.find(
            '<span class="fieldlabeltext">Restrictions:</span>')
        si += len('<span class="fieldlabeltext">Restrictions:</span>')
        fi = restrictions.find('<span', si)
        restrictions = restrictions[si:fi].replace(
            "\n", "").replace("<br/>", "\n").strip()
        # print(restrictions)

    @classmethod
    def getClassDataByNumber(cls, term, subjectCode, number):
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


if __name__ == "__main__":
    # pa = PurdueApi("eutiushe")
    PurdueApi.getSectionDataByCRN("201920", "36593")
    # PurdueApi.getClassDataByNumber("201920", "CS", "37300")
