import calendar
from calendar import HTMLCalendar, monthrange
from datetime import datetime, timedelta

from kb4it.core.service import Service
from kb4it.core.util import valid_filename
from kb4it.core.util import guess_datetime

class EventsCalendar(Service, HTMLCalendar):
    """Credit to: https://github.com/garthhumphreys/How-to-Use-Python-To-Create-A-Beautiful-Web-Calendar"""

    def initialize(self):
        super(HTMLCalendar, self).__init__(calendar.MONDAY)
        self.ml = {} # ??
        self.now = datetime.now()
        self.get_services()

    def get_services(self):
        self.srvbld = self.get_service('Builder')

    def set_events_days(self, events_days):
        """
        FIXME: Document this method properly

        Attach the list of event days as a property, so we can access it
        anywhere.
        """
        self.events_days = events_days
        for year in events_days:
            self.ml[year] = {}
            for i in range(1,13):
                self.ml[year][i] = False
            for month, day in events_days[year]:
                self.ml[year][month] = True

    def set_events_docs(self, docs):
        self.events_docs = docs

    def set_events_html(self, html):
        self.events_html = html

    def formatday(self, day, weekday):
        """Return a day as a table cell."""
        eday = 0 # var for checking if it's a event day
        cal_date = (self.month, day) # create a tuple of the calendar month and day
        EVENTCAL_TD_NODAY = self.srvbld.template('EVENTCAL_TD_NODAY')
        EVENTCAL_TD_DAY_LINK = self.srvbld.template('EVENTCAL_TD_DAY_LINK')
        EVENTCAL_TD_DAY_LINK_TODAY = self.srvbld.template('EVENTCAL_TD_DAY_LINK_TODAY')
        EVENTCAL_TD_DAY_NOLINK = self.srvbld.template('EVENTCAL_TD_DAY_NOLINK')
        EVENTCAL_TD_DAY_NOLINK_TODAY = self.srvbld.template('EVENTCAL_TD_DAY_NOLINK_TODAY')
        EVENT_PAGE = "events_%4d%02d%02d" % (self.year, self.month, day)
        EVENT_PAGE_VALID_FNAME = valid_filename(EVENT_PAGE)
        link = {}
        link['class'] = self.cssclasses[weekday]
        link['vfname'] = EVENT_PAGE_VALID_FNAME
        link['day'] = day
        HTML = ''
        if day == 0:
            return EVENTCAL_TD_NODAY.render(var=link) # day outside month
        else:
            try:
                self.events_days[self.year]
                if cal_date in self.events_days[self.year]:
                    eday = day

                if day == eday:
                    if self.year == self.now.year and self.month == self.now.month and day == self.now.day:
                        return EVENTCAL_TD_DAY_LINK_TODAY.render(var=link)
                    else:
                        return EVENTCAL_TD_DAY_LINK.render(var=link)
                else:
                    if self.year == self.now.year and self.month == self.now.month and day == self.now.day:
                        return EVENTCAL_TD_DAY_NOLINK_TODAY.render(var=link)
                    else:
                        return EVENTCAL_TD_DAY_NOLINK.render(var=link)
            except Exception as error:
                if self.year == self.now.year and self.month == self.now.month and day == self.now.day:
                    return EVENTCAL_TD_DAY_NOLINK_TODAY.render(var=link)
                else:
                    return EVENTCAL_TD_DAY_NOLINK.render(var=link)

    def formatweek(self, theweek):
        """Return a complete week as a table row."""
        week = {}
        EVENTCAL_TR_WEEK = self.srvbld.template('EVENTCAL_TR_WEEK')
        week['content'] = ''
        for d, wd in theweek:
            try:
                week['content'] += self.formatday(d, wd)
            except Exception as error:
                pass
        return EVENTCAL_TR_WEEK.render(var=week)

    def formatweekheader(self):
        """Return a header for a week as a table row."""
        header = {}
        EVENTCAL_TR_WEEK_HEADER = self.srvbld.template('EVENTCAL_TR_WEEK_HEADER')
        header['content'] = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return EVENTCAL_TR_WEEK_HEADER.render(var=header)

    def formatweekday(self, nd):
        EVENTCAL_WEEKDAY_HEADER = self.srvbld.template('EVENTCAL_WEEKDAY_HEADER')
        day_format = {}
        day_format[0] = ("mon", "Monday", "M")
        day_format[1] = ("tue", "Tuesday", "T")
        day_format[2] = ("wed", "Wednesday", "W")
        day_format[3] = ("thu", "Thursday", "T")
        day_format[4] = ("fri", "Friday", "F")
        day_format[5] = ("sat", "Saturday", "S")
        day_format[6] = ("sun", "Sunday", "S")
        return EVENTCAL_WEEKDAY_HEADER.render(var=day_format[nd])

    def formatmonthname(self, theyear, themonth, withyear=True):
        """Return a formatted month name."""
        LINK_URL = self.srvbld.template('LINK')
        LINK_CLASS = self.srvbld.render_template('EVENTCAL_MONTHNAME_A_CLASS')
        dt = guess_datetime("%4d-%02d-01" % (theyear, themonth))
        month_name = datetime.strftime(dt, "%B %Y")
        var = {}
        var['title'] = month_name
        var['class'] = LINK_CLASS
        try:
            events = self.ml[theyear][themonth]
            if events:
                var['url'] = "events_%4d%02d.html" % (theyear, themonth)
            else:
                var['url'] = "#"
        except KeyError:
            var['url'] = "#"

        link = LINK_URL.render(var=var)
        return link

    def formatmonth(self, theyear, themonth, withyear=False):
        """Override in order to add the month as a property."""
        self.year = theyear
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
                thismonth = {}
                thismonth['content'] = self.formatmonth(theyear, m, withyear=False)
                # self.log.error(thismonth)
                TD_YEAR_MONTH += EVENTCAL_TABLE_YEAR_TD_MONTH.render(var=thismonth)
            td = {}
            td['content'] = TD_YEAR_MONTH
            MONTHS += EVENTCAL_TABLE_YEAR_TR_MONTHROW.render(var=td)
        table = {}
        table['content'] = MONTHS
        v.append(EVENTCAL_TABLE_YEAR.render(var=table))
        return ''.join(v)

    def formatyearpage(self, theyear, width=4, css='calendar.css', encoding=None):
        """Return a formatted year as a complete HTML page."""
        return self.formatyear(theyear, width)

    def build_year_pagination(self, years):
        EVENTCAL_YEAR_PAGINATION = self.srvbld.template('EVENTCAL_YEAR_PAGINATION')
        EVENTCAL_YEAR_PAGINATION_ITEM = self.srvbld.template('EVENTCAL_YEAR_PAGINATION_ITEM')
        var = {}
        var['items'] = ''
        ITEMS = ''
        for yp in sorted(years):
            item = {}
            item['year'] = yp
            ITEMS += EVENTCAL_YEAR_PAGINATION_ITEM.render(var=item)
        var['items'] = ITEMS
        return EVENTCAL_YEAR_PAGINATION.render(var=var)

    def format_trimester(self, theyear, themonth):
        """Return a formatted year as a table of tables."""
        EVENTCAL_TABLE_YEAR = self.srvbld.template('EVENTCAL_TABLE_TRIMESTER')
        EVENTCAL_TABLE_YEAR_TR_MONTHROW = self.srvbld.template('EVENTCAL_TABLE_YEAR_TR_MONTHROW')
        EVENTCAL_TABLE_YEAR_TD_MONTH = self.srvbld.template('EVENTCAL_TABLE_YEAR_TD_MONTH')
        var = {}
        dt_cur = datetime.strptime("%d.%d.01" % (theyear, themonth), "%Y.%m.%d")
        dt_cur_lastday = dt_cur.replace(day = monthrange(dt_cur.year, dt_cur.month)[1]).date()
        dt_prv = dt_cur - timedelta(days=1)
        dt_nxt = dt_cur_lastday + timedelta(days=1)
        v = []
        MONTHS = ''
        TD_YEAR_MONTH = ''
        var['content'] = self.formatmonth(dt_prv.year, dt_prv.month, withyear=True)
        TD_YEAR_MONTH += EVENTCAL_TABLE_YEAR_TD_MONTH.render(var=var)
        var['content'] = self.formatmonth(dt_cur.year, dt_cur.month, withyear=True)
        TD_YEAR_MONTH += EVENTCAL_TABLE_YEAR_TD_MONTH.render(var=var)
        var['content'] = self.formatmonth(dt_nxt.year, dt_nxt.month, withyear=True)
        TD_YEAR_MONTH += EVENTCAL_TABLE_YEAR_TD_MONTH.render(var=var)
        var['content'] = TD_YEAR_MONTH
        MONTHS += EVENTCAL_TABLE_YEAR_TR_MONTHROW.render(var=var)
        var['content'] = MONTHS
        v.append(EVENTCAL_TABLE_YEAR.render(var=var))
        return ''.join(v)

