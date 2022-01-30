<!-- Template HTML_BODY_DOC.tpl :: START -->
% if var['has_toc']:
    <!-- This is the nav containing the toggling elements -->
    <ul class="uk-tab" uk-switcher>
        <li><a href="#">Document</a></li>
        <li><a href="#">Related</a></li>
        <li><a href="#">Metadata</a></li>
        <li><a href="#">Source</a></li>
        <li><a href="#">Actions</a></li>
    </ul>
    <!-- This is the container of the content items -->
    <ul class="uk-switcher uk-margin">
        <li>${var['source_html']}</li>
        <li>${var['related']}</li>
        <li>${var['metadata']}</li>
        <li>
            <div class="content">
                <div class="listingblock">
                    <div class="content">
                        <pre class="CodeRay highlight nowrap">
                            <code data-lang="ruby">
${var['source_adoc']}</code>
                        </pre>
                    </div>
                </div>
            </div>
        </li>
        <li>
            ${var['actions']}
        </li>
    </ul>
% else:
    ${var['source_html']}
% endif
<!-- Template HTML_BODY_DOC.tpl :: END -->
