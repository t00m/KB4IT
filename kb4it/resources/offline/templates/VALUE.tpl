= %s - %s

++++
<!-- Pagination :: Start-->
%s
<!-- Pagination :: End -->
<!-- Value Filter :: Start -->
<div uk-filter="target: .js-filter">
    <form action="" method="post" class="uk-search uk-search-default uk-width-1-1 uk-margin-medium-bottom">
        <input id="text_filter" type="search" name="" value="" class="uk-search-input uk-padding-small" autocomplete="off" placeholder="Filter results by title..." autofocus/>
    </form>
    <a id="filter" href="#" class="uk-active" uk-filter-control="" hidden></a>
    <!-- Filtered rows :: Start -->
    <ul class="js-filter uk-child-width-1-3@m" uk-grid>
%s
    </ul>
    <!-- Filtered rows :: End -->
</div>
<!-- Value Filter :: End -->
++++


