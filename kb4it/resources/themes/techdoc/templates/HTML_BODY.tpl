<!-- Template HTML_BODY_DOC.tpl :: START -->
<!-- This is the nav containing the toggling elements -->
<ul class="uk-subnav uk-subnav-pill" uk-switcher>
    <li><a href="#">Document</a></li>
    <li><a href="#">Related</a></li>
    <li><a href="#">Metadata</a></li>
    <li><a href="#">Source</a></li>
    <li><a href="#">Actions</a></li>
</ul>
<!-- This is the container of the content items -->
<ul class="uk-switcher uk-margin">
    <li>${var['content']}</li>
    <li>${var['related']}</li>
    <li>${var['metadata']}</li>
    <li>${var['source']}</li>
    <li>${var['actions']}</li>
</ul>
<!-- Template HTML_BODY_DOC.tpl :: END -->