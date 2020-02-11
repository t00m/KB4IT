
            <!-- PROPERTY_FILTER.tpl // Filter :: Start -->
            <div uk-filter="target: .js-filter">
                <!-- Filter buttons :: Start -->
                <ul class="uk-subnav uk-subnav-pill">
                    <!-- <li class="uk-active" uk-filter-control><a href="#"><div class="uk-text-capitalize uk-text-bold">All</div></a></li> -->
%s
                </ul> <!-- Filter buttons :: End -->

                <!-- Search entry :: Start -->
                <form action="" method="post" class="uk-search uk-search-default uk-width-1-1 uk-margin-medium-bottom">
                    <input id="text_filter" type="search" name="" value="" class="uk-search-input uk-padding-small" autocomplete="off" placeholder="Filter results by title..." autofocus/>
                </form>
                <a id="filter" href="#" class="uk-active" uk-filter-control="[data-*='#nodata#']" hidden></a>
                <!-- Search entry :: End -->

                <!-- Filtered rows :: Start -->
                <ul class="js-filter uk-child-width-1-3@m" uk-grid>
%s
                </ul> <!-- Filtered rows :: End -->
            </div> <!-- PROPERTY_FILTER.tpl // Filter :: End -->
