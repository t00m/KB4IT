++++
<!-- Template HTML_BODY_INDEX.tpl :: START -->
<!-- Blog Post :: START -->
<article class="post-card uk-card uk-card-default uk-card-body uk-margin-medium-bottom">
    <h2 class="uk-card-title"><a href="${var['post']['filename'].replace('adoc','html')}">${var['post']['Title']}</a></h2>
    <div class="post-meta uk-margin-small-bottom">
        <span>By <a href="${var['post']['Author_0_Url']}">${var['post']['Author'][0]}</a></span> |
        <span>${var['post']['Updated'][0]}</span>
        <span></span>
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


