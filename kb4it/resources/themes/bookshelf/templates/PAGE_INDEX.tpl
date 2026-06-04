<!-- PAGE_INDEX :: START -->
<% bk = var['bk'] %>\
<% stats = bk['stats'] %>\
<% cb = bk.get('current_book') %>\
<div class="pagehead">
    <div>
        <div class="eyebrow">Your study library</div>
        <h1>The shelf</h1>
    </div>
    <span class="sub">${stats['books']} certification book${'s' if stats['books'] != 1 else ''} &middot; pick one and keep reading.</span>
</div>

<div class="shelf-wrap">
    <div class="legend" style="margin-bottom:16px">
        <span class="eyebrow" style="letter-spacing:.08em">Spine height = length &middot; fill = progress</span>
        <span style="margin-left:auto"></span>
        <span><span class="dot done"></span> done</span>
        <span><span class="dot reading"></span> reading</span>
        <span><span class="dot todo"></span> to-do</span>
    </div>
    <div class="shelf">
% for b in bk['books']:
        <a class="spine ${b['palette']}" style="height:${b['height']}px" href="${b['url']}" title="${b['title']}">
            <span class="vtitle">${b['short']}</span>
% if b['code']:
            <span class="ex">${b['code']}</span>
% endif
            <span class="pct"><i style="width:${b['percent']}%"></i></span>
        </a>
% endfor
    </div>
    <div class="shelf-board"></div>
</div>

% if cb:
<div class="continue">
    <div class="mini-cover" style="background:${cb['gradient']}"></div>
    <div>
        <div class="eyebrow">Continue where you left off</div>
        <h3>Chapter ${cb['chapter']} &middot; ${cb['chapter_title']}</h3>
        <div class="crumb">${cb['short']}<span class="sep">&#9656;</span>${cb['part_label']}${('<span class="sep">&#9656;</span>' + cb['part_title']) if cb['part_title'] else ''}</div>
    </div>
    <a class="resume" href="${cb['chapter_url']}">Resume reading
        <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 10h11M11 5l5 5-5 5"></path></svg>
    </a>
</div>
% endif

<div class="section-h"><h2>At a glance</h2><span class="rule"></span></div>
<div class="stat-strip">
    <a class="stat" href="Book.html"><div class="n">${stats['books']}</div><div class="l">Books</div></a>
    <div class="stat"><div class="n">${stats['parts']}</div><div class="l">Parts</div></div>
    <a class="stat" href="all.html"><div class="n">${stats['chapters']}</div><div class="l">Chapters</div></a>
    <div class="stat"><div class="n">${stats['read']}</div><div class="l">Chapters read</div></div>
    <a class="stat" href="Command.html"><div class="n">${stats['commands']}</div><div class="l">Commands indexed</div></a>
</div>

<div class="section-h"><h2>All books</h2><span class="count">${stats['books']} in library</span><span class="rule"></span></div>
<div class="cards">
% for b in bk['books']:
    <a class="book-card ${'' if b['started'] else 'empty'}" href="${b['url']}">
        <div class="top">
            <div class="cover" style="background:${b['gradient']}"></div>
            <div>
                <div class="title">${b['short']}</div>
                <div class="author">${b['author']}${(' &middot; ' + b['code']) if b['code'] else ''}</div>
            </div>
        </div>
        <div class="struct">
            <span class="s"><b>${b['part_count']}</b> Parts</span>
            <span class="s"><b>${b['total']}</b> Chapters</span>
            <span class="s"><span class="dot ${b['current_bucket']}"></span> ${b['current_part']}</span>
        </div>
        <div class="bar"><i style="width:${b['percent']}%"></i></div>
        <div class="foot">
            <span class="pctn">${b['done']} / ${b['total']} chapters</span>
% if b['started']:
            <span class="chip accent">${b['percent']}%</span>
% else:
            <span class="chip">New</span>
% endif
        </div>
    </a>
% endfor
</div>
<!-- PAGE_INDEX :: END -->
