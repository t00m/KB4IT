import calendar
from calendar import HTMLCalendar
from datetime import datetime
from kb4it.core.service import Service
from kb4it.core.util import valid_filename, guess_datetime

class EventsCalendar(Service, HTMLCalendar):
    """Credit to: https://github.com/garthhumphreys/How-to-Use-Python-To-Create-A-Beautiful-Web-Calendar"""

    def initialize(self):
        super(HTMLCalendar, self).__init__(calendar.MONDAY)
        self.current_year = None
        self.ml = {}
        self.get_services()
        print

    def set_events_days(self, events_days):
        """
        Attach the list of event days as a property, so we can access it
        anywhere.
        """
        self.events_days = events_days #
        for i in range(1,13):
            self.ml[i] = False
        for month, day in events_days:
            self.ml[month] = True

    def set_events_docs(self, docs):
        self.events_docs = docs

    def set_events_html(self, html):
        self.events_html = html

    def get_services(self):
        self.srvbld = self.get_service('Builder')

    def formatday(self, day, weekday):
        """Return a day as a table cell."""
        eday = 0 # var for checking if it's a event day
        cal_date = (self.month, day) # create a tuple of the calendar month and day
        EVENTCAL_TD_NODAY = self.srvbld.template('EVENTCAL_TD_NODAY')
        EVENTCAL_TD_DAY_LINK = self.srvbld.template('EVENTCAL_TD_DAY_LINK')
        EVENTCAL_TD_DAY_NOLINK = self.srvbld.template('EVENTCAL_TD_DAY_NOLINK')
        if cal_date in self.events_days: # check if current calendar tuple date exist in our list of events days
            eday = day # if it does exist set the event day var with it
        if day == 0:
            return EVENTCAL_TD_NODAY # day outside month
        elif day == eday: # check if this is one of the events days, then change the
            EVENT_PAGE = "events_%4d%02d%02d" % (self.current_year, self.month, day)
            EVENT_PAGE_VALID_FNAME = valid_filename(EVENT_PAGE)
            return EVENTCAL_TD_DAY_LINK % (self.cssclasses[weekday], EVENT_PAGE_VALID_FNAME, day)
        else:
            return EVENTCAL_TD_DAY_NOLINK % (self.cssclasses[weekday], day)

    def formatweek(self, theweek):
        """Return a complete week as a table row."""
        EVENTCAL_TR_WEEK = self.srvbld.template('EVENTCAL_TR_WEEK')
        s = ''.join(self.formatday(d, wd) for (d, wd) in theweek)
        return EVENTCAL_TR_WEEK % s

    def formatweekheader(self):
        """Return a header for a week as a table row."""
        EVENTCAL_TR_WEEK_HEADER = self.srvbld.template('EVENTCAL_TR_WEEK_HEADER')
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return EVENTCAL_TR_WEEK_HEADER % s

    def formatweekday(self, nd):
        day_format = {}
        day_format[0] = ("mon", "Monday", "M")
        day_format[1] = ("tue", "Tuesday", "T")
        day_format[2] = ("wed", "Wednesday", "W")
        day_format[3] = ("thu", "Thursday", "T")
        day_format[4] = ("fri", "Friday", "F")
        day_format[5] = ("sat", "Saturday", "S")
        day_format[6] = ("sun", "Sunday", "S")
        return """<th class="%s"><a class="uk-link-heading uk-text-bolder uk-link-muted" href="#" uk-tooltip="%s">%s</a></th>""" % day_format[nd]

    def formatmonthname(self, theyear, themonth, withyear=True):
        """Return a formatted month name."""
        LINK = self.srvbld.template('LINK')
        dt = guess_datetime("%4d-%02d-01" % (theyear, themonth))
        if withyear:
            month_name = datetime.strftime(dt, "%B %Y")
        else:
            month_name = datetime.strftime(dt, "%B")

        if self.ml[themonth]:
            link = LINK % ("uk-link-heading", "events_%4d%02d.html" % (theyear, themonth), "uk-text-uppercase uk-text-muted", month_name)
        else:
            # ~ link = LINK % ("uk-link-heading", "", "", month_name)
            link = """<span class="%s">%s</span>""" % ("uk-text-uppercase uk-text-muted", month_name)
        return link

    def formatmonth(self, theyear, themonth, withyear=False):
        """Override in order to add the month as a property."""
        self.month = themonth
        month = super(EventsCalendar, self).formatmonth(theyear, themonth, withyear=False)
        return month

    def formatyear(self, theyear, width=4):
        """Return a formatted year as a table of tables."""
        EVENTCAL_TABLE_YEAR = self.srvbld.template('EVENTCAL_TABLE_YEAR')
        EVENTCAL_TABLE_YEAR_TR_MONTHROW = self.srvbld.template('EVENTCAL_TABLE_YEAR_TR_MONTHROW')
        EVENTCAL_TABLE_YEAR_TD_MONTH = self.srvbld.template('EVENTCAL_TABLE_YEAR_TD_MONTH')
        v = []
        width = max(width, 1)
        MONTHS = ''
        January = 1
        for i in range(January, January+12, width):
            months = range(i, min(i+width, 13))
            TD_YEAR_MONTH = ''
            for m in months:
                TD_YEAR_MONTH += EVENTCAL_TABLE_YEAR_TD_MONTH % self.formatmonth(theyear, m, withyear=False)
            MONTHS += EVENTCAL_TABLE_YEAR_TR_MONTHROW % TD_YEAR_MONTH
        v.append(EVENTCAL_TABLE_YEAR % MONTHS)
        return ''.join(v)

    def formatyearpage(self, theyear, width=4, css='calendar.css', encoding=None):
        """Return a formatted year as a complete HTML page."""
        self.current_year = theyear
        return self.formatyear(theyear, width)

    def build_year_pagination(self, years):
        EVENTCAL_YEAR_PAGINATION = self.srvbld.template('EVENTCAL_YEAR_PAGINATION')
        EVENTCAL_YEAR_PAGINATION_ITEM = self.srvbld.template('EVENTCAL_YEAR_PAGINATION_ITEM')
        ITEMS = ''
        for yp in sorted(years):
            ITEMS += EVENTCAL_YEAR_PAGINATION_ITEM % (yp, yp)
        return EVENTCAL_YEAR_PAGINATION % ITEMS
