<!-- DOCUMENT FILTER :: START -->
% if var.get('list'):
<div id="${var['list']}-filter" class="kb-dt-facets noprint" data-kb-list="${var['list']}" hidden>
% else:
<div id="${var['table_id']}-filter" class="kb-dt-facets noprint" data-kb-table="${var['table_id']}" hidden>
% endif
% for group in var['groups']:
    <div class="kb-dt-facet" data-kb-key="${group['slug']}">
        <span class="kb-dt-facet-key">${group['key']}</span>
        <ul class="uk-subnav uk-subnav-pill">
            <li class="uk-active"><a href="#" role="button" aria-pressed="true" data-kb-value="">All</a></li>
% for value in group['values']:
            <li><a href="#" role="button" aria-pressed="false" data-kb-value="${value['slug']}">${value['name']} <span class="kb-dt-facet-n">${value['count']}</span></a></li>
% endfor
        </ul>
    </div>
% endfor
    <button type="button" class="uk-button uk-button-link kb-dt-facets-clear" hidden>Clear filters</button>
</div>
<!-- DOCUMENT FILTER :: END -->
