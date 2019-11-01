
        <div uk-filter="target: .js-filter"> <!-- Filter :: Start -->
            <ul class="uk-subnav uk-subnav-pill"> <!-- Filter buttons :: Start -->
                <li class="uk-active" uk-filter-control><a href="#"><div class="uk-text-capitalize uk-text-bold">All</div></a></li> <!-- ALL button -->
%s
            </ul> <!-- Filter buttons :: End -->
            <form action="" method="post" class="uk-search uk-search-default uk-width-1-1 uk-margin-medium-bottom">
                <input id="text_filter" type="search" name="" value="" class="uk-search-input uk-padding-small" autocomplete="off" placeholder="Filter results by title..." autofocus/>
            </form>
            <a id="filter" href="#" class="uk-active" uk-filter-control="" hidden></a>
            <ul class="js-filter uk-child-width-1-3@m" uk-grid> <!-- Filter rows :: Start -->
%s
            </ul>
        </div> <!-- Filter :: End -->
