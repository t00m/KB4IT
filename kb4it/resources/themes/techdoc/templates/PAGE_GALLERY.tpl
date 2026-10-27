<%
    items = var['items']
    groups = var['filters']
%>
<!-- GALLERY PAGE :: START -->
<div class="uk-container kb-gallery-page">
% if items:
    <p class="kb-gal-intro"><span id="kb-gal-count">${len(items)} ${'image' if len(items) == 1 else 'images'}</span> from ${var['docs']} ${'document' if var['docs'] == 1 else 'documents'}. Click an image to enlarge it; the panel narrows them down by the properties of their documents.</p>
    <div class="kb-gal">
        <!-- GALLERY GRID :: START -->
        <div class="kb-gal-main">
        <ul class="kb-gal-grid" id="kb-gal-grid">
%     for i, item in enumerate(items):
            <li class="kb-gal-cell" data-i="${i}">
                <figure class="kb-gal-figure">
                    <a class="kb-gal-zoom" href="${item['src']}" title="${item['caption'] or item['title']}"><img loading="lazy" decoding="async" alt="${item['caption']}" src="${item['src']}"></a>
                    <figcaption><a href="${item['href']}">${item['title']}</a></figcaption>
                </figure>
            </li>
%     endfor
        </ul>
        <p class="kb-gal-none" id="kb-gal-none" hidden>No image matches these filters.</p>
        </div>
        <!-- GALLERY GRID :: END -->
        <!-- GALLERY FILTERS :: START -->
        <aside class="kb-gal-panel noprint" aria-label="Filter images">
            <div class="kb-gal-panel-head">
                <strong>Filters</strong>
                <button type="button" class="uk-button uk-button-link kb-gal-clear" id="kb-gal-clear">Clear</button>
            </div>
            <label class="uk-hidden-visually" for="kb-gal-text">Filter by title or caption</label>
            <input class="uk-input uk-form-small kb-gal-text" id="kb-gal-text" type="search" placeholder="Title or caption" autocomplete="off">
%     for f, group in enumerate(groups):
            <details class="kb-gal-group"${' open' if f < 3 else ''}>
                <summary>${group['key']}</summary>
                <ul class="kb-gal-values">
%         for v, entry in enumerate(group['values']):
                    <li>
                        <input class="uk-checkbox" type="checkbox" id="kb-gal-f${f}-${v}" data-key="${group['key']}" value="${entry['value']}">
                        <label for="kb-gal-f${f}-${v}">${entry['value']}</label>
                        <span class="kb-gal-n" data-count="${entry['count']}">${entry['count']}</span>
                    </li>
%         endfor
                </ul>
            </details>
%     endfor
        </aside>
        <!-- GALLERY FILTERS :: END -->
    </div>
    <script type="application/json" id="kb-gal-data">${var['json'] | n}</script>
    <script src="resources/themes/techdoc/framework/kb4it/js/gallery.js" defer></script>
% else:
    <p class="kb-gal-empty">No document shows an image yet. Add one with <code>![What it shows](resources/images/file.png)</code> and the file in <code>source/resources/images/</code>.</p>
% endif
</div>
<!-- GALLERY PAGE :: END -->
