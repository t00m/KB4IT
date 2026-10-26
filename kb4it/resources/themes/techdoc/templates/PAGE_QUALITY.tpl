<%
    q = var['q']
    labels = {'exemplary': 'Exemplary', 'complete': 'Complete', 'basic': 'Basic', 'stub': 'Stub'}
%>
<!-- QUALITY PAGE :: START -->
<div class="uk-container kb-quality-page">
    <p class="kb-q-disclaimer">Scores of every document, and the work that would raise them. The score measures structure, metadata, links and age, not whether the content is correct. <a href="quality-guide.html">How the score works</a></p>

    <!-- TIER MIX :: START -->
    <details class="kb-section kb-collapsible" id="quality-mix" open>
        <summary class="kb-section-title">Tier mix</summary>
% for m in q['mix']:
        <div class="kb-q-mixrow">
            <span class="kb-q-mixpeer">${m['peer']}</span>
            <span class="kb-q-mix">
%     for t in ('exemplary', 'complete', 'basic', 'stub'):
%         if m['counts'][t]:
                <span class="kb-q-${t}" style="width: ${m['pct'][t]}%" title="${labels[t]}: ${m['counts'][t]}"></span>
%         endif
%     endfor
            </span>
            <span class="kb-q-mixlabel">${m['counts']['exemplary']} exemplary, ${m['counts']['complete']} complete, ${m['counts']['basic']} basic, ${m['counts']['stub']} stub of ${m['total']}</span>
        </div>
% endfor
    </details>
    <!-- TIER MIX :: END -->

% if q.get('best'):
    <!-- BEST DOCUMENTS :: START -->
    <details class="kb-section kb-collapsible" id="quality-best" open>
        <summary class="kb-section-title">Best documents</summary>
        <div class="kb-best">
%     for b in q['best']:
            <a class="kb-best-card" href="${b['href']}">
                <span class="kb-q-emblem small kb-q-${b['tier']}"><svg viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15.9" fill="none" stroke="#eee" stroke-width="4"/><circle cx="18" cy="18" r="15.9" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="${b['score']} 100" stroke-linecap="round"/></svg><span class="num">${b['score']}</span></span>
                <span><span class="t">${b['title']}</span><span class="s">${b['type']}${', ' + b['year'] if b['year'] else ''}</span></span>
            </a>
%     endfor
        </div>
    </details>
    <!-- BEST DOCUMENTS :: END -->
% endif

    <!-- EXEMPLARY :: START -->
    <details class="kb-section kb-collapsible" id="quality-exemplary" open>
        <summary class="kb-section-title">Exemplary documents (${len(q['exemplary'])})</summary>
% if q['exemplary']:
        <ol class="kb-q-list">
%     for d in q['exemplary']:
            <li><a href="${d['href']}">${d['title']}</a> <span class="kb-q-list-meta">${d['score']}, ${d['peer']}</span></li>
%     endfor
        </ol>
% else:
        <p class="kb-q-empty">No Exemplary document yet. The quick wins below are the shortest way there.</p>
% endif
    </details>
    <!-- EXEMPLARY :: END -->

    <!-- QUICK WINS :: START -->
    <details class="kb-section kb-collapsible" id="quality-wins" open>
        <summary class="kb-section-title">Quick wins (${len(q['wins'])})</summary>
        <p class="kb-q-intro">Documents one change away from the next tier, closest first.</p>
% if q['wins']:
        <ul class="kb-wins">
%     for w in q['wins']:
            <li><span class="kb-q-chip kb-q-${w['tier']}">${w['score']}</span><a href="${w['href']}">${w['title']}</a><a class="act" href="quality-guide.html#${w['key']}">${w['check']} +${w['gain']}: ${labels[w['next']]}</a></li>
%     endfor
        </ul>
% else:
        <p class="kb-q-empty">None.</p>
% endif
    </details>
    <!-- QUICK WINS :: END -->

    <!-- BROKEN LINKS :: START -->
    <details class="kb-section kb-collapsible" id="quality-broken" open>
        <summary class="kb-section-title">Broken links (${len(q['broken'])})</summary>
% if q['broken']:
        <ul class="kb-q-list">
%     for b in q['broken']:
            <li><a href="${b['href']}">${b['title']}</a> <span class="kb-q-list-meta">links to <code>${b['target']}</code></span></li>
%     endfor
        </ul>
% else:
        <p class="kb-q-empty">None.</p>
% endif
    </details>
    <!-- BROKEN LINKS :: END -->

    <!-- MISSING IMAGES :: START -->
    <details class="kb-section kb-collapsible" id="quality-images">
        <summary class="kb-section-title">Missing images (${len(q['images'])})</summary>
% if q['images']:
        <ul class="kb-q-list">
%     for i in q['images']:
            <li><a href="${i['href']}">${i['title']}</a> <span class="kb-q-list-meta"><code>${i['target']}</code></span></li>
%     endfor
        </ul>
% else:
        <p class="kb-q-empty">None.</p>
% endif
    </details>
    <!-- MISSING IMAGES :: END -->

    <!-- NO SUMMARY :: START -->
    <details class="kb-section kb-collapsible" id="quality-summary">
        <summary class="kb-section-title">Documents without a Summary (${len(q['no_summary'])})</summary>
% if q['no_summary']:
        <ul class="kb-q-list kb-q-columns">
%     for d in q['no_summary']:
            <li><a href="${d['href']}">${d['title']}</a></li>
%     endfor
        </ul>
% else:
        <p class="kb-q-empty">None.</p>
% endif
    </details>
    <!-- NO SUMMARY :: END -->

    <!-- DUPLICATES :: START -->
    <details class="kb-section kb-collapsible" id="quality-duplicates" open>
        <summary class="kb-section-title">Possible duplicates (${len(q['duplicates'])})</summary>
        <p class="kb-q-intro">Titles that share most of their words. Titles that differ only by a date are left out.</p>
% if q['duplicates']:
        <ul class="kb-q-list">
%     for a, b, score in q['duplicates']:
            <li><a href="${a['href']}">${a['title']}</a> <span class="kb-q-list-meta">${a['score']}</span> and <a href="${b['href']}">${b['title']}</a> <span class="kb-q-list-meta">${b['score']}</span></li>
%     endfor
        </ul>
% else:
        <p class="kb-q-empty">None.</p>
% endif
    </details>
    <!-- DUPLICATES :: END -->
</div>
<!-- QUALITY PAGE :: END -->
