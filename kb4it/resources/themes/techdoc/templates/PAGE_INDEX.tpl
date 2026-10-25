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
        return ""

def prop_url(key, value):
    s = str(value).strip().replace(" ", "_")
    safe = re.sub(r"(?u)[^-\w.]", "", s)
    return "%s_%s.html" % (key, safe)
%>

<!-- DASHBOARD :: START -->
<div class="uk-container kb-index">

    <!-- SUMMARY COUNTS :: START -->
    <section class="kb-section" aria-labelledby="kb-hero-heading">
        <h2 id="kb-hero-heading" class="uk-hidden-visually">Summary</h2>
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
    <!-- SUMMARY COUNTS :: END -->

    <!-- DOCUMENT TYPES :: START -->
    <section class="kb-section" aria-labelledby="kb-doctypes-heading">
        <h2 id="kb-doctypes-heading" class="uk-hidden-visually">Document types</h2>
        <div class="uk-grid-small uk-grid-match uk-child-width-1-2@s uk-child-width-1-4@m" data-uk-grid>
% for item in var['page']['diataxis']:
            <div>
% if item['url']:
                <a class="kb-diataxis-card ${item['css']}" href="${item['url']}">
% else:
                <div class="kb-diataxis-card ${item['css']} kb-diataxis-empty">
% endif
                    <div class="kb-diataxis-headline">
                        <span class="kb-diataxis-icon"><span data-uk-icon="icon: ${item['icon']}; ratio: 0.9"></span></span>
                        <span class="kb-diataxis-count">${item['count']}</span>
                        <span class="kb-diataxis-label">${item['label']}</span>
                    </div>
                    <p class="kb-diataxis-desc">${item['desc']}</p>
%     if item.get('mix'):
<% m = item['mix'] %>
                    <span class="kb-q-mix">
%         for t in ('exemplary', 'complete', 'basic', 'stub'):
%             if m['counts'][t]:
                        <span class="kb-q-${t}" style="width: ${m['pct'][t]}%"></span>
%             endif
%         endfor
                    </span>
                    <span class="kb-q-mixlabel">${m['counts']['exemplary']} exemplary, ${m['counts']['complete']} complete of ${m['total']}</span>
%     endif
% if item['url']:
                </a>
% else:
                </div>
% endif
            </div>
% endfor
        </div>
    </section>
    <!-- DOCUMENT TYPES :: END -->

% if var['page']['open_items']:
    <!-- OPEN ITEMS :: START -->
    <details class="kb-section kb-collapsible" data-kb-section="open-items" open>
        <summary class="kb-section-title">Open items</summary>
        <div class="kb-panel uk-card-hover uk-box-shadow-large">
            <table class="uk-table uk-table-small uk-table-divider uk-margin-remove kb-events-table">
                <tbody>
%     for row in var['page']['open_items']:
                    <tr>
                        <td class="kb-event-date">${row['date']}</td>
                        <td class="kb-event-title"><a href="${row['url']}">${row['title']}</a></td>
                        <td class="kb-open-badges">
%         if row['priority']:
                            <a class="uk-label kb-badge ${row['priority_css']}" href="${prop_url('Priority', row['priority'])}" title="${row['priority']}">${row['priority']}</a>
%         endif
%         if row['status']:
                            <a class="uk-label kb-badge ${row['status_css']}" href="${prop_url('Status', row['status'])}" title="${row['status']}">${row['status']}</a>
%         endif
%         if row['category']:
                            <a class="uk-label kb-badge ${category_css(row['category'])}" href="${row['category_url']}" title="${row['category']}">${row['category']}</a>
%         endif
                        </td>
                    </tr>
%     endfor
                </tbody>
            </table>
        </div>
    </details>
    <!-- OPEN ITEMS :: END -->
% endif

<% act = var['page']['activity'] %>
% if any(act.values()):
    <!-- ACTIVITY :: START -->
    <details class="kb-section kb-collapsible" data-kb-section="activity" open>
        <summary class="kb-section-title">Activity</summary>
        <div class="kb-activity">
            <ul class="kb-activity-tabs" data-uk-tab="connect: #kb-activity-panels; animation: uk-animation-fade">
%     for name, label in (('changes', 'Changes'), ('incidents', 'Incidents'), ('events', 'Events'), ('monitoring', 'Monitoring')):
%         if act[name]:
                <li data-kb-tab="${name}"><a href="#">${label}</a></li>
%         endif
%     endfor
            </ul>
            <div class="uk-switcher" id="kb-activity-panels">
%     if act['changes']:
            <!-- CHANGES PANEL :: START -->
            <div class="kb-alert-bar">
            <div class="kb-alert-col">
                <div class="kb-alert-header kb-alert-changes">
                    <span data-uk-icon="icon: warning; ratio: 0.75"></span>
                    <a href="${var['page']['alert_bar']['changes_url']}">Changes</a>
                </div>
% if var['page']['alert_bar']['changes']:
                <ul class="kb-alert-list">
%     for item in var['page']['alert_bar']['changes']:
                    <li class="kb-alert-item">
                        <span class="kb-alert-date">${item['date']}</span>
                        <a class="kb-alert-title" href="${item['url']}">${item['title']}</a>
%         if item['status']:
                        <a class="uk-label kb-badge ${item['status_css']}" href="${prop_url('Status', item['status'])}" title="${item['status']}">${item['status']}</a>
%         endif
%         if item['priority']:
                        <a class="uk-label kb-badge ${item['priority_css']}" href="${prop_url('Priority', item['priority'])}" title="${item['priority']}">${item['priority']}</a>
%         endif
                    </li>
%     endfor
                </ul>
% else:
                <div class="kb-alert-empty">No recent changes.</div>
% endif
            </div>
            </div>
            <!-- CHANGES PANEL :: END -->
%     endif
%     if act['incidents']:
            <!-- INCIDENTS PANEL :: START -->
            <div class="kb-alert-bar">
            <div class="kb-alert-col">
                <div class="kb-alert-header kb-alert-incidents">
                    <span data-uk-icon="icon: warning; ratio: 0.75"></span>
                    <a href="${var['page']['alert_bar']['incidents_url']}">Incidents</a>
                </div>
% if var['page']['alert_bar']['incidents']:
                <ul class="kb-alert-list">
%     for item in var['page']['alert_bar']['incidents']:
                    <li class="kb-alert-item">
                        <span class="kb-alert-date">${item['date']}</span>
                        <a class="kb-alert-title" href="${item['url']}">${item['title']}</a>
%         if item['status']:
                        <a class="uk-label kb-badge ${item['status_css']}" href="${prop_url('Status', item['status'])}" title="${item['status']}">${item['status']}</a>
%         endif
%         if item['priority']:
                        <a class="uk-label kb-badge ${item['priority_css']}" href="${prop_url('Priority', item['priority'])}" title="${item['priority']}">${item['priority']}</a>
%         endif
                    </li>
%     endfor
                </ul>
% else:
                <div class="kb-alert-empty">No recent incidents.</div>
% endif
            </div>
            </div>
            <!-- INCIDENTS PANEL :: END -->
%     endif
%     if act['events']:
            <!-- EVENTS PANEL :: START -->
            <div>
            <h3 class="kb-activity-sub">Upcoming</h3>
        <div class="kb-panel uk-card-hover uk-box-shadow-large">
            <div class="uk-grid-small" data-uk-grid>
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
                                <td class="kb-open-badges"><a class="uk-label kb-badge ${category_css(row['category'])}" href="${row['category_url']}" title="${row['category']}">${row['category']}</a></td>
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
            <h3 class="kb-activity-sub">Recent</h3>
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
                        <td class="kb-open-badges"><a class="uk-label kb-badge ${category_css(row['category'])}" href="${row['category_url']}" title="${row['category']}">${row['category']}</a></td>
% else:
                        <td></td>
% endif
                    </tr>
% endfor
                </tbody>
            </table>
% endif
        </div>
            </div>
            <!-- EVENTS PANEL :: END -->
%     endif
%     if act['monitoring']:
            <!-- MONITORING PANEL :: START -->
            <div>
        <div class="kb-panel uk-card-hover uk-box-shadow-large">
% if len(var['page']['monitoring_panel']) == 0:
            <div class="kb-events-empty">No monitoring articles found.</div>
% else:
            <div class="uk-grid-small" data-uk-grid>
% for group in var['page']['monitoring_panel']:
                <div class="uk-width-1-${ len(var['page']['monitoring_panel']) }@m">
                    <div class="kb-events-month-header">
                        <a href="${group['url']}">${group['periodicity']}</a>
                    </div>
% if len(group['rows']) == 0:
                    <div class="kb-events-empty">No articles.</div>
% else:
                    <table class="uk-table uk-table-small uk-table-divider uk-margin-remove kb-events-table">
                        <tbody>
% for row in group['rows']:
                            <tr>
                                <td class="kb-event-title"><a href="${row['url']}">${row['title']}</a></td>
                            </tr>
% endfor
                        </tbody>
                    </table>
% endif
                </div>
% endfor
            </div>
% endif
        </div>
            </div>
            <!-- MONITORING PANEL :: END -->
%     endif
            </div>
        </div>
    </details>
    <!-- ACTIVITY :: END -->
    <!-- ACTIVITY TAB MEMORY :: START -->
    <script>
    // The Activity card opens on the tab the reader chose last.
    (function () {
        var tabs = document.querySelector('.kb-activity-tabs');
        if (!tabs || typeof UIkit === 'undefined') { return; }
        var names = Array.prototype.map.call(tabs.children, function (li) { return li.getAttribute('data-kb-tab'); });
        try {
            var i = names.indexOf(window.localStorage.getItem('kb-activity-tab'));
            if (i > 0) { UIkit.tab(tabs).show(i); }
        } catch (e) { /* private window: start on the first tab */ }
        tabs.addEventListener('click', function (event) {
            var li = event.target.closest('li');
            if (!li) { return; }
            try { window.localStorage.setItem('kb-activity-tab', li.getAttribute('data-kb-tab')); } catch (e) { /* not kept */ }
        });
    })();
    </script>
    <!-- ACTIVITY TAB MEMORY :: END -->
% endif

</div>
<!-- DASHBOARD :: END -->
<script>
    // Remember which dashboard sections the reader folded, in this browser only.
    document.querySelectorAll("details.kb-collapsible").forEach(function (box) {
        var key = "kb4it-dashboard-" + box.dataset.kbSection;
        try { if (localStorage.getItem(key) === "closed") { box.open = false; } } catch (e) {}
        box.addEventListener("toggle", function () {
            try { if (box.open) { localStorage.removeItem(key); } else { localStorage.setItem(key, "closed"); } } catch (e) {}
        });
    });
</script>
