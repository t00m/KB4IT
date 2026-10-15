<div class="kb4it-backlinks" style="margin-top:2em;padding-top:.5em;border-top:1px solid rgba(128,128,128,.35)">
<p class="kb4it-backlinks-title" style="font-weight:600;margin:0 0 .3em">Linked from</p>
<ul class="kb4it-backlinks-list">
% for item in var['backlinks']:
<li><a href="${item['href']}">${item['title']}</a></li>
% endfor
</ul>
</div>
