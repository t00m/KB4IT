<%
    strip = var['strip']
%>
% if strip['badges'] or strip['links']:
<!-- HEADER STRIP :: START -->
<div class="kb-doc-strip">
%     for badge in strip['badges']:
    <a class="uk-label kb-badge ${badge['css']}" href="${badge['url']}" title="${badge['key']}: ${badge['text']}">${badge['text']}</a>
%     endfor
%     if strip['links']:
    <span class="meta">
%         for link in strip['links']:
        <span><span class="k">${link['key']}</span>
%             for item in link['items']:
            <a href="${item['url']}">${item['text']}</a>${'' if loop.last else ','}
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
