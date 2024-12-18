<div id="timeline-embed" style="width: 100%; height: 600px;"></div>

<script src="resources/themes/techdoc/framework/TimelineJS/js/timeline.js"></script>
<script>
    var options = {
            start_at_end: true,
    zoom_sequence: [0.5, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89],
    initial_zoom: 10,
    scale_factor: 1
        }
    var timeline = new TL.Timeline('timeline-embed', '${var['timeline']['filename']}', options);
</script>
