<!-- PAGE_BOOK :: START -->
<% book = var['book'] %>\
<div class="crumb">
    <a href="index.html">Library</a><span class="sep">&#9656;</span><span class="here">${book['title']}</span>
</div>

<div class="kanban-head">
    <div class="bookline">
        <div class="cover-xs" style="background:${book['gradient']}"></div>
        <div>
            <h1 style="font-size:1.5rem">${book['title']}</h1>
            <div class="sub" style="color:var(--ink-3);font-size:0.84rem">${book['author']}${(' &middot; ' + book['code']) if book['code'] else ''} &middot; ${book['part_count']} part${'s' if book['part_count'] != 1 else ''} &middot; ${book['total']} chapter${'s' if book['total'] != 1 else ''}</div>
        </div>
    </div>
    <div class="whole">
        <span class="eyebrow">Whole book</span>
        <div class="bar"><i style="width:${book['percent']}%"></i></div>
        <span class="mono" style="font-size:0.8rem;color:var(--ink-2)">${book['percent']}%</span>
    </div>
</div>

<div class="legend" style="margin-bottom:14px">
    <span class="eyebrow" style="letter-spacing:.08em">Each Part is a column &mdash; push chapters toward done</span>
    <span style="margin-left:auto"></span>
    <span><span class="dot done"></span> done</span>
    <span><span class="dot reading"></span> reading</span>
    <span><span class="dot todo"></span> to-do</span>
</div>

<div class="board">
% for col in book['columns']:
    <div class="col ${'current' if col['is_current'] else ''}">
        <div class="col-head">
            <div class="pnum">PART ${col['roman']}${' &middot; CURRENT' if col['is_current'] else ''}</div>
% if col['title']:
            <div class="ptitle">${col['title']}</div>
% endif
            <div class="meta">
                <div class="bar ${'done' if col['percent'] == 100 else ''}"><i style="width:${col['percent']}%"></i></div>
                <span class="frac">${col['done']}/${col['total']}</span>
            </div>
        </div>
        <div class="col-body">
% for card in col['cards']:
            <a class="ch-card ${card['bucket']} ${'current' if card['is_current'] else ''}" href="${card['url']}">
                <span class="cnum">${card['cnum']}</span>
                <span class="ctitle">${card['title']}</span>
                <span class="dot ${card['bucket']}"></span>
            </a>
% endfor
        </div>
    </div>
% endfor
</div>
<!-- PAGE_BOOK :: END -->
