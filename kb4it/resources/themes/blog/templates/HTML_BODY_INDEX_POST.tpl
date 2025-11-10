++++
<!-- Template HTML_BODY_INDEX.tpl :: START -->
<!-- Blog Post :: START -->
<article class="post-card uk-card uk-card-default uk-card-body uk-margin-medium-bottom">
    <h2 class="uk-card-title">${var['post']['Title']}</h2>
    <div class="post-meta uk-margin-small-bottom">
        <span>By ${var['post']['Author'][0]}</span> | <span>${var['post']['Updated'][0]} </span> | <span>${var['post']['filename']}</span>
    </div>
    <p class="uk-text-justify">
        ${var['post']['body']}
    </p>
    <div class="uk-flex uk-flex-between uk-flex-middle">
        <div>
            <span class="category">Web Development</span>
        </div>
        <div class="post-tags">
            <span class="tag">UIkit</span>
            <span class="tag">CSS Framework</span>
            <span class="tag">Frontend</span>
        </div>
    </div>
</article>
<!-- Template HTML_BODY_INDEX.tpl :: END -->
++++


