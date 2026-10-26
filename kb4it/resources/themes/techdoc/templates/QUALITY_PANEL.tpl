<%
    q = var['q']
%>
<div class="kb-q-panel kb-q-${q['tier']}">
    <div>
        <span class="kb-q-emblem big kb-q-${q['tier']}"><svg viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15.9" fill="none" stroke="#eee" stroke-width="3"/><circle cx="18" cy="18" r="15.9" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="${q['score']} 100" stroke-linecap="round"/></svg><span class="num">${q['score']}</span></span>
        <div class="kb-q-chipline"><a class="kb-q-chip kb-q-${q['tier']}" href="quality-guide.html#tiers" title="Tiers: Exemplary 75 and up, Complete 60 to 74, Basic 40 to 59, Stub under 40" data-uk-tooltip="pos: top-left">
% if q['tier'] == 'exemplary':
            <svg viewBox="0 0 20 20" aria-hidden="true"><path fill="currentColor" d="M10 1l2.7 5.8 6.3.7-4.7 4.3 1.3 6.2L10 14.9 4.4 18l1.3-6.2L1 7.5l6.3-.7z"/></svg>
% endif
            ${q['label']}</a></div>
        <div class="kb-q-rank" data-kb-doc="${q['page']}"></div>
    </div>
    <div>
% for dim in q['dims']:
        <div class="kb-q-dim" data-kb-dim="${dim['key']}" title="${dim['tip']}" data-uk-tooltip="pos: top-left">
            <span><a href="quality-guide.html#dim-${dim['key']}">${dim['label']}</a></span>
            <span class="kb-q-bar"><span class="fill" style="width: ${dim['percent']}%"></span><span class="kb-q-tick"></span></span>
            <span>${dim['points']} / ${dim['max']}</span>
        </div>
% endfor
        <ul class="kb-q-checks">
% for item in q['checklist']:
%     if item['kind'] == 'ok':
            <li class="ok" title="${item['tip']}" data-uk-tooltip="pos: top-left"><a href="quality-guide.html#${item['key']}">${item['text']}</a></li>
%     else:
            <li class="todo" title="${item['tip']}" data-uk-tooltip="pos: top-left"><a href="quality-guide.html#${item['key']}">${item['text']}</a><span class="gain">+${item['gain']}</span></li>
%     endif
% endfor
        </ul>
        <p class="kb-q-disclaimer">Quality measures structure, metadata, links and age. It does not check that the content is correct. <a href="quality-guide.html">How the score works</a></p>
    </div>
</div>
