<%!
from kb4it.core.util import valid_filename
%>
<!-- HTML_BODY :: START -->
<main class="page">
% if var['SystemPage'] or not var.get('reading'):
    <div class="wrap">
        ${var['source_html']}
    </div>
% else:
<% rd = var['reading'] %>\
<% info = rd['info'] %>\
<% book = rd['book'] %>\
    <div class="wrap">
        <div class="crumb">
            <a href="index.html">Library</a><span class="sep">&#9656;</span>
            <a href="${book['url']}">${book['short']}</a><span class="sep">&#9656;</span>
            <a href="${book['url']}">${rd['part_label']}</a><span class="sep">&#9656;</span>
            <span class="here">Ch ${info['chapter']} &middot; ${info['title']}</span>
            <span class="chip mono jump">On this page &darr;</span>
        </div>

        <div class="reader">
            <nav class="chapnav">
                <div class="partlabel">${rd['part_label']} &middot; chapters</div>
% for sib in rd['siblings']:
                <a class="${'cur' if sib['is_current'] else ''}" href="${sib['url']}">
                    <span class="cnum">${sib['cnum']}</span> ${sib['title']}
                    <span class="dot ${sib['bucket']}" style="margin-left:auto"></span>
                </a>
% if sib['is_current']:
                <div class="chapnav-subs" id="bk-chapnav-subs"></div>
% endif
% endfor
                <div class="navdiv"></div>
                <a href="${book['url']}"><span class="cnum">&#128213;</span> Book overview</a>
            </nav>

            <article class="article">
                <div class="meta-top">
                    <span class="chip accent"><span class="dot ${info['bucket']}"></span> ${info['status']}</span>
% if info['doctype']:
                    <span class="chip">${info['doctype']}</span>
% endif
                    <span class="chip mono">~${var['read_min']} min</span>
                </div>
                <h1>${info['title']}</h1>

                <div class="chapter-body">
                    ${var['source_html']}
                </div>

                <div class="prevnext">
% if rd['prev']:
                    <a class="pn" href="${rd['prev']['url']}">
                        <span class="dir"><span class="ar">&larr;</span> Previous &middot; ${rd['prev']['cnum']}</span>
                        <span class="t">${rd['prev']['title']}</span>
                    </a>
% else:
                    <span></span>
% endif
% if rd['next']:
                    <a class="pn next" href="${rd['next']['url']}">
                        <span class="dir">Next &middot; ${rd['next']['cnum']} <span class="ar">&rarr;</span></span>
                        <span class="t">${rd['next']['title']}</span>
                    </a>
% else:
                    <span></span>
% endif
                </div>

                <section class="print-only print-appendix">
                    <h2><span class="n">&#9000;</span> Command reference</h2>
% if rd['commands']:
                    <ul class="appendix-cmds">
% for cmd in rd['commands']:
                        <li><b>${cmd}</b></li>
% endfor
                    </ul>
% endif
% if rd['tags']:
                    <p class="appendix-tags"><b>Tags:</b> ${' &middot; '.join(rd['tags'])}</p>
% endif
                </section>

                <div class="docmeta">
                    <div class="row"><span class="k">Book</span><span>${book['title']}</span></div>
                    <div class="row"><span class="k">Part</span><span>${rd['part_label']}${(' &middot; ' + rd['part_title']) if rd['part_title'] else ''}</span></div>
                    <div class="row"><span class="k">Chapter</span><span>${info['chapter']}</span></div>
% if info['author']:
                    <div class="row"><span class="k">Author</span><span>${info['author']}</span></div>
% endif
                    <div class="row"><span class="k">Updated</span><span>${info['date'][:16]} &middot; ${info['status']}</span></div>
                </div>
            </article>

            <aside class="rail">
                <div class="rail-card">
                    <div class="rh"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 5h12M4 10h12M4 15h8"></path></svg><span class="eyebrow">On this page</span></div>
                    <div class="rb toc" id="bk-toc"></div>
                </div>
% if rd['commands']:
                <div class="rail-card">
                    <div class="rh"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="14" height="12" rx="2"></rect><path d="M6 8l2 2-2 2M11 12h3"></path></svg><span class="eyebrow">Commands in this chapter</span></div>
                    <div class="cheat">
% for cmd in rd['commands']:
                        <a class="ci" href="Command_${valid_filename(cmd)}.html"><div class="cmdname">${cmd}</div></a>
% endfor
                    </div>
                </div>
% endif
% if rd['tags']:
                <div class="rail-card">
                    <div class="rh"><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 7l7-4 7 4-7 4-7-4z"></path><path d="M3 13l7 4 7-4"></path></svg><span class="eyebrow">Tags</span></div>
                    <div class="props">
% for tag in rd['tags']:
                        <a class="chip mono" href="Tag_${valid_filename(tag)}.html">${tag}</a>
% endfor
                    </div>
                </div>
% endif
            </aside>
        </div>
    </div>
% endif
</main>
<!-- HTML_BODY :: END -->
