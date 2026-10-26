<%
    strip = var['strip']
    q = var.get('quality')
%>
% if q and q['tier'] == 'exemplary':
<!-- EXEMPLARY NOTE :: START -->
<div class="kb-exemplary-note kb-noprint" data-kb-peer="${q['peer']}"><svg width="14" height="14" viewBox="0 0 20 20" aria-hidden="true"><path fill="currentColor" d="M10 1l2.7 5.8 6.3.7-4.7 4.3 1.3 6.2L10 14.9 4.4 18l1.3-6.2L1 7.5l6.3-.7z"/></svg> <span>Exemplary ${q['peer_name']}<span class="kb-q-rank-note" data-kb-doc="${q['page']}"></span></span></div>
<!-- EXEMPLARY NOTE :: END -->
% endif
% if strip['badges'] or strip['links'] or q:
<!-- HEADER STRIP :: START -->
<div class="kb-doc-strip">
%     if q:
    <a class="kb-q-emblem-link kb-noprint" href="#kb-info-quality" title="Quality ${q['score']} of 100, ${q['label']}" aria-label="Quality ${q['score']} of 100, ${q['label']}"><span class="kb-q-emblem kb-q-${q['tier']}"><svg viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15.9" fill="none" stroke="#eee" stroke-width="3.5"/><circle cx="18" cy="18" r="15.9" fill="none" stroke="currentColor" stroke-width="3.5" stroke-dasharray="${q['score']} 100" stroke-linecap="round"/></svg><span class="num">${q['score']}</span></span></a>
%     endif
%     for badge in strip['badges']:
    <a class="uk-label kb-badge ${badge['css']}" href="${badge['url']}" title="${badge['key']}: ${badge['text']}">${badge['text']}</a>
%     endfor
%     if strip['links']:
    <span class="meta">
%         for link in strip['links']:
        <span><span class="k">${link['key']}</span>
%             for item in link['items']:
%                 if item['time']:
            <a class="kb-date" href="${item['url']}" title="${item['full']}"><span class="kb-day">${item['text']}</span><span class="kb-time">${item['time']}</span></a>${'' if loop.last else ','}
%                 else:
            <a href="${item['url']}">${item['text']}</a>${'' if loop.last else ','}
%                 endif
%             endfor
        </span>
%         endfor
    </span>
%     endif
</div>
<!-- HEADER STRIP :: END -->
% endif
% if var['summary']:
<!-- SUMMARY :: START -->
<p class="kb-summary">${var['summary']}</p>
<!-- SUMMARY :: END -->
% endif
% if var['banners']:
<!-- BANNERS :: START -->
%     for banner in var['banners']:
<div class="kb-banner ${banner['kind']}" role="note"><strong>${banner['label']}</strong> ${banner['text']}</div>
%     endfor
<!-- BANNERS :: END -->
% endif
