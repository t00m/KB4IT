= ${var['page']['title']}

// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

% if var['repo']['webserver']:
++++
<!-- Tabs header :: START -->
<ul class="uk uk-flex-center" uk-tab>
    <li><a href="#">Timeline</a></li>
    <li><a href="#">Table</a></li>
</ul>
<!-- Tabs header :: END -->

<!-- Tabs content :: START-->
<ul class="uk-switcher uk-margin">
    <!-- Timeline :: Start -->
    <li>
        <div id="timeline-embed" style="width: 100%; height: 600px;"></div>

        <script src="resources/themes/techdoc/framework/TimelineJS/js/timeline.js"></script>
        <script>
            var options = {
                    start_at_end: true,
                initial_zoom: "2"
                }
            var timeline = new TL.Timeline('timeline-embed', 'timeline_main.json', options);
        </script>
    </li>
    <!-- Timeline :: End -->
    <!-- Table :: Start -->
    <li>
        <div class ="uk-container uk-overflow-auto">
        ${var['page']['dt_documents']}
        </div>
    </li>
    <!-- Table :: End -->
</u>

++++

% else:

++++
<div class ="uk-container uk-overflow-auto">
${var['page']['dt_documents']}
</div>
++++

% endif


