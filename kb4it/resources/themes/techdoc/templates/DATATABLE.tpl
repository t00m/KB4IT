% if len(var['rows']) > 0:
<table id="kb4it-datatable" class="uk-table uk-table-small uk-table-hover uk-table-striped uk-text-small" style="width: 100%">
    <thead class="">
        <tr class="">
            ${var['header']}
        </tr>
    </thead>
    <tbody class="">
            ${var['rows']}
    </tbody>
    <tfoot class="">
    </tfoot>
</table>
% else:
<div class="uk-flex uk-flex-top uk-flex-center uk-height-viewport uk-background-muted uk-padding-large">
    <div class="uk-card uk-card-small uk-card-hover uk-width-1-2@m">
        <div class="uk-card-header">
            <div class="uk-grid-small uk-flex-middle" uk-grid>
                <div class="uk-width-auto">
                    <span uk-icon="icon: info; ratio: 2"></span>
                </div>
                <div class="uk-width-expand">
                    <h3 class="uk-card-title uk-margin-remove-bottom">Informative Message</h3>
                </div>
            </div>
        </div>
        <div class="uk-card-body">
            <p>No documents found.</p>
        </div>
<!--
        <div class="uk-card-footer">
            <a href="#" class="uk-button uk-button-text">Read more</a>
        </div>
-->
    </div>
</div>
% endif
