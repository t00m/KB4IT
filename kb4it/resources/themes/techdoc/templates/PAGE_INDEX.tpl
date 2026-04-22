= ${var['page']['title']}

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

<%!
import re

def category_css(category):
    _danger  = {"Change"}
    _warning = {"Incident", "Task"}
    _success = {"Meeting", "Procedure", "Reminder", "Template"}
    _primary = {"Note", "Post"}
    if category in _danger:
        return "uk-label-danger"
    elif category in _warning:
        return "uk-label-warning"
    elif category in _success:
        return "uk-label-success"
    elif category in _primary:
        return "uk-label-primary"
    else:
        return "uk-text-muted"

def category_url(category):
    s = str(category).strip().replace(" ", "_")
    safe = re.sub(r"(?u)[^-\w.]", "", s)
    return "Category_%s.html" % safe
%>

++++
<div class="uk-container kb-index">

    <!-- 0. TRIMESTER CALENDAR (hidden) -->
    <section class="kb-section" style="display:none;">
        <div class="kb-panel kb-trimester">
            <div class="uk-flex uk-flex-between uk-flex-middle uk-margin-small-bottom">
                <h2 class="kb-section-title" style="margin: 0;">Trimester · ${var['page']['trimester']['title']}</h2>
                <a href="events.html" class="uk-text-small" style="text-decoration: none;">
                    All events <span uk-icon="icon: chevron-right; ratio: 0.8"></span>
                </a>
            </div>
            <div class="kb-trimester-grid">
% for month in var['page']['trimester']['months']:
                <div class="kb-trimester-month${' current' if month['current'] else ''}">
                    <h4>${month['name']}</h4>
                    <table>
                        <thead>
                            <tr><th>M</th><th>T</th><th>W</th><th>T</th><th>F</th><th>S</th><th>S</th></tr>
                        </thead>
                        <tbody>
%     for week in month['weeks']:
                            <tr>
%         for cell in week:
%             if cell['kind'] == 'empty':
                                <td class="empty">·</td>
%             elif cell['kind'] == 'today':
                                <td class="today">${cell['n']}</td>
%             elif cell['kind'] == 'event':
                                <td class="event"><a href="${cell['url']}">${cell['n']}</a></td>
%             else:
                                <td>${cell['n']}</td>
%             endif
%         endfor
                            </tr>
%     endfor
                        </tbody>
                    </table>
                </div>
% endfor
            </div>
        </div>
    </section>

    <!-- 1. HERO STATS BAR -->
    <section class="kb-section">
        <div class="kb-hero-bar">
% for i, stat in enumerate(var['page']['stats']):
%     if i > 0:
            <div class="kb-hero-divider"></div>
%     endif
            <a class="kb-hero-stat" href="${stat['url']}">
                <span class="num">${stat['num']}</span>
                <span class="label">${stat['label']}</span>
            </a>
% endfor
        </div>
    </section>

    <!-- 2. DIATAXIS GRID -->
    <section class="kb-section">
        <div class="uk-grid-small uk-grid-match uk-child-width-1-2@s uk-child-width-1-4@m" uk-grid>
% for item in var['page']['diataxis']:
            <div>
% if item['url']:
                <a class="kb-diataxis-card ${item['css']}" href="${item['url']}">
% else:
                <div class="kb-diataxis-card ${item['css']} kb-diataxis-empty">
% endif
                    <div class="kb-diataxis-headline">
                        <span class="kb-diataxis-icon"><span uk-icon="icon: ${item['icon']}; ratio: 0.9"></span></span>
                        <span class="kb-diataxis-count">${item['count']}</span>
                        <span class="kb-diataxis-label">${item['label']}</span>
                    </div>
                    <p class="kb-diataxis-desc">${item['desc']}</p>
% if item['url']:
                </a>
% else:
                </div>
% endif
            </div>
% endfor
        </div>
    </section>

    <!-- 3. CHANGES & INCIDENTS BAR -->
    <section class="kb-section">
        <div class="kb-alert-bar">
            <div class="kb-alert-col">
                <div class="kb-alert-header kb-alert-changes">
                    <span uk-icon="icon: warning; ratio: 0.75"></span>
                    <a href="Category_Change.html">Changes</a>
                </div>
% if var['page']['alert_bar']['changes']:
                <ul class="kb-alert-list">
%     for item in var['page']['alert_bar']['changes']:
                    <li class="kb-alert-item">
                        <span class="kb-alert-date">${item['date']}</span>
                        <a class="kb-alert-title" href="${item['url']}">${item['title']}</a>
                    </li>
%     endfor
                </ul>
% else:
                <div class="kb-alert-empty">No recent changes.</div>
% endif
            </div>
            <div class="kb-alert-divider"></div>
            <div class="kb-alert-col">
                <div class="kb-alert-header kb-alert-incidents">
                    <span uk-icon="icon: warning; ratio: 0.75"></span>
                    <a href="Category_Incident.html">Incidents</a>
                </div>
% if var['page']['alert_bar']['incidents']:
                <ul class="kb-alert-list">
%     for item in var['page']['alert_bar']['incidents']:
                    <li class="kb-alert-item">
                        <span class="kb-alert-date">${item['date']}</span>
                        <a class="kb-alert-title" href="${item['url']}">${item['title']}</a>
                    </li>
%     endfor
                </ul>
% else:
                <div class="kb-alert-empty">No recent incidents.</div>
% endif
            </div>
        </div>
    </section>

    <!-- 4. UPCOMING EVENTS -->
    <section class="kb-section">
        <h2 class="kb-section-title">Upcoming events</h2>
        <div class="kb-panel uk-card-hover uk-box-shadow-large">
            <div class="uk-grid-small" uk-grid>
% for side in ('current', 'next'):
<%  panel = var['page']['events_panel'][side] %>
                <div class="uk-width-1-2@m">
                    <div class="kb-events-month-header"><a href="${panel['url']}">${panel['label']}</a></div>
%     if len(panel['rows']) == 0:
                    <div class="kb-events-empty">No events scheduled.</div>
%     else:
                    <table class="uk-table uk-table-small uk-table-divider uk-margin-remove kb-events-table">
                        <tbody>
%         for row in panel['rows']:
                            <tr>
                                <td class="kb-event-date">${row['date']}</td>
                                <td class="kb-event-title"><a href="${row['url']}">${row['title']}</a></td>
%             if row['category']:
                                <td class="uk-flex uk-flex-right"><a class="uk-flex uk-flex-center uk-label ${category_css(row['category'])}" href="${category_url(row['category'])}">${row['category']}</a></td>
%             else:
                                <td></td>
%             endif
                            </tr>
%         endfor
                        </tbody>
                    </table>
%     endif
                </div>
% endfor
            </div>
        </div>
    </section>

    <!-- 5. RECENT EVENTS -->
    <section class="kb-section">
        <h2 class="kb-section-title">Recent events</h2>
        <div class="kb-panel uk-card-hover uk-box-shadow-large">
% if len(var['page']['recent_events']) == 0:
            <div class="kb-events-empty">No events in the past month.</div>
% else:
            <table class="uk-table uk-table-small uk-table-divider uk-margin-remove kb-events-table">
                <tbody>
% for row in var['page']['recent_events']:
                    <tr>
                        <td class="kb-event-date">${row['date']}</td>
                        <td class="kb-event-title"><a href="${row['url']}">${row['title']}</a></td>
% if row['category']:
                        <td class="uk-flex uk-flex-right"><span class="uk-flex uk-flex-center uk-label ${category_css(row['category'])}">${row['category']}</span></td>
% else:
                        <td></td>
% endif
                    </tr>
% endfor
                </tbody>
            </table>
% endif
        </div>
    </section>

</div>
++++
