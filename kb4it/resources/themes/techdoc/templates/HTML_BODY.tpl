<!-- Template HTML_BODY_DOC.tpl :: START -->
% if var['has_toc']:
<!--
    <div class="uk-flex uk-flex-center"><h1 class="uk-text-large">${var['page']['title']}</h1></div>
-->
    <!-- This is the nav containing the toggling elements -->
    <ul class="uk-flex uk-flex-center uk-tab noprint" uk-switcher>
        <li><a href="#">Document</a></li>
        <!-- <li><a href="#">Related</a></li> -->
    </ul>
    <!-- This is the container of the content items -->
    <ul class="uk-switcher uk-margin">
        <li>${var['source_html']}</li>
        <!-- <li></li> -->
    </ul>
% else:
    ${var['source_html']}
% endif
<!-- Template HTML_BODY_DOC.tpl :: END -->
</div>
