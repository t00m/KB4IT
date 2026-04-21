= ${var['page']['title']}

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

<%!
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
%>

++++
<div class="uk-container kb-index">

    <!-- 1. TRIMESTER CALENDAR (hidden) -->
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

    <!-- 2. HERO STATS BAR -->
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

    <!-- 3. DIATAXIS GRID -->
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

    <!-- 4. UPCOMING EVENTS -->
    <section class="kb-section">
        <h2 class="kb-section-title">Upcoming events</h2>
        <div class="kb-panel">
            <div class="uk-grid-small" uk-grid>
% for side in ('current', 'next'):
<%  panel = var['page']['events_panel'][side] %>
                <div class="uk-width-1-2@m">
                    <div class="kb-events-month-header">${panel['label']}</div>
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
                                <td><span class="uk-flex uk-flex-center uk-label ${category_css(row['category'])}">${row['category']}</span></td>
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
        <div class="kb-panel">
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
                        <td><span class="uk-flex uk-flex-center uk-label ${category_css(row['category'])}">${row['category']}</span></td>
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
