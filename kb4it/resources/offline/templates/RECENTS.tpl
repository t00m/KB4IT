= Recents

++++
        <!-- RECENTS.tpl :: START -->
        <div uk-filter="target: .js-filter">
            <!-- RECENT FILTER BUTTONS :: START -->
            <ul class="uk-subnav uk-subnav-pill">
                <li uk-filter-control="[data-recent*='Today']"><a href="#"><div class="uk-text-capitalize uk-text-bold">Today</div></a></li>
                <li uk-filter-control="[data-recent*='Week']"><a href="#"><div class="uk-text-capitalize uk-text-bold">This week</div></a></li>
                <li uk-filter-control="[data-recent*='Month']"><a href="#"><div class="uk-text-capitalize uk-text-bold">This month</div></a></li>
            </ul>
            <!-- RECENT FILTER BUTTONS :: END -->

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
        </div> <!-- RECENTS.tpl :: END -->
++++

