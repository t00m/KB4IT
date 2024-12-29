<!-- Template HTML_BODY_DOC.tpl :: START -->
% if var['has_toc']:

<div id="kb4it-doc-metadata" class="uk-hidden" style="border: 1px solid transparent;">${var['metadata']}</div>

    <!-- This is the nav containing the toggling elements -->
    <ul class="uk-flex uk-flex-center uk-tab noprint uk-hidden" uk-switcher>
        <li><a href="#">Document</a></li>
<!-- <li><a href="#">Related</a></li> -->
    </ul>
    <!-- This is the container of the content items -->
    <ul class="uk-switcher uk-margin">
        <li>${var['source_html']}</li>
<!-- <li>var['related']</li> -->
    </ul>
% else:
    ${var['source_html']}
% endif
<!-- Template HTML_BODY_DOC.tpl :: END -->
</div>
