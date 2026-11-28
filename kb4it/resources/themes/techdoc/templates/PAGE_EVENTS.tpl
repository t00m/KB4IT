<!-- EVENTS :: START -->
<div class="uk-container uk-margin-top">
  <div class="kb-ev-layout" data-kb-events data-kb-table="${var['table_id']}">

    <!-- EVENTS PANEL :: START -->
    <aside class="kb-ev-panel noprint" aria-label="Events calendar">
      <div class="kb-ev-year">
        <button type="button" class="kb-ev-step" data-kb-step="older" aria-label="Previous year">&lsaquo;</button>
        <button type="button" class="kb-ev-year-label" aria-haspopup="true" aria-expanded="false" aria-controls="kb-ev-years">
          <span class="kb-ev-year-name">Events</span>
          <span class="kb-ev-year-count"></span>
        </button>
        <button type="button" class="kb-ev-step" data-kb-step="newer" aria-label="Next year">&rsaquo;</button>
        <ul id="kb-ev-years" class="kb-ev-years" hidden></ul>
      </div>
      <div class="kb-ev-strip" role="group" aria-label="Events per month"></div>
      <div class="kb-ev-cal"></div>
      <div class="kb-ev-foot"></div>
    </aside>
    <!-- EVENTS PANEL :: END -->

    <!-- EVENTS LIST :: START -->
    <div class="kb-ev-list">
      ${var['datatable'] | n}
    </div>
    <!-- EVENTS LIST :: END -->

  </div>
</div>
<script type="application/json" id="kb-events-data">${var['data'] | n}</script>
<script src="resources/themes/techdoc/framework/kb4it/js/events.js" defer></script>
<!-- EVENTS :: END -->
