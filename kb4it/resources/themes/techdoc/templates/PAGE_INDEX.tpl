= ${var['page']['title']}

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

++++
<div class="uk-container kb-index">

    <!-- 1. TRIMESTER CALENDAR -->
    <section class="kb-section">
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
            <div class="kb-hero-stat">
                <span class="num">${stat['num']}</span>
                <span class="label">${stat['label']}</span>
            </div>
% endfor
        </div>
    </section>

    <!-- 3. DIATAXIS GRID -->
    <section class="kb-section">
        <h2 class="kb-section-title">Browse by type</h2>
        <div class="uk-grid-small uk-grid-match uk-child-width-1-2@s uk-child-width-1-4@m" uk-grid>
% for item in var['page']['diataxis']:
            <div>
                <a class="kb-diataxis-card ${item['css']}" href="${item['url']}">
                    <div class="kb-diataxis-headline">
                        <span class="kb-diataxis-icon"><span uk-icon="icon: ${item['icon']}; ratio: 0.9"></span></span>
                        <span class="kb-diataxis-count">${item['count']}</span>
                        <span class="kb-diataxis-label">${item['label']}</span>
                    </div>
                    <p class="kb-diataxis-desc">${item['desc']}</p>
                </a>
            </div>
% endfor
        </div>
    </section>

    <!-- 4. EVENTS PANEL -->
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
                                <td><span class="uk-label">${row['category']}</span></td>
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

</div>
++++
