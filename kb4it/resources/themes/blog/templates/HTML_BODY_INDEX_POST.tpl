++++
<!-- Template HTML_BODY_INDEX.tpl :: START -->
<!-- Blog Post :: START -->
<article class="post-card uk-card uk-card-default uk-card-body uk-margin-medium-bottom">
    <h2 class="uk-card-title"><a href="${var['post']['filename'].replace('adoc','html')}">${var['post']['Title']}</a></h2>
    <div class="post-meta uk-margin-small-bottom">
        <span>Published by <a href="${var['post']['Author_0_Url']}">${var['post']['Author'][0]}</a>  on ${var['post']['updated_human']}</span>
        <br/>
        <span>About  
                % for topic in var['post']['Topic']:
                    <a href="Topic_${topic}.html">${topic}</a>, 
                % endfor
        </span>
        <br/>
        <span>Tags: 
                % for tag in var['post']['Tag']:
                    <a href="Tag_${tag}.html">${tag}</a>, 
                % endfor
        </span>
    </div>
    <p class="uk-text-justify">
        ${var['post']['body']}
    </p>
    <div class="">
        <div class="uk-card-footer">
            <div class="uk-grid-small uk-flex-middle" uk-grid>
	        <div class="uk-width-expand">
                <h3 class="uk-card-title uk-margin-remove-bottom uk-text-center">Topics</h3>
		% for topic in var['post']['Topic']:
		    <span class="tag"><a href="Topic_${topic}.html">${topic}</a></span>
		% endfor
                </div>  
		<div class="uk-width-expand">
                <h3 class="uk-card-title uk-margin-remove-bottom uk-text-center">Tags</h3>
		% for tag in var['post']['Tag']:
		    <span class="tag"><a href="Tag_${tag}.html">${tag}</a></span>
		% endfor
                </div>   
            </div>
        </div>
    </div>
</article>
<!-- Template HTML_BODY_INDEX.tpl :: END -->
++++


