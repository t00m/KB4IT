= Bookmarks

++++
<div class="uk-flex uk-flex-center"><h1 class="uk-text-large">${var['page']['title']}</h1></div>
<div class ="uk-container uk-overflow-auto">
    <table id="kb4it-datatable" class="uk-table uk-table-small uk-table-hover uk-table-striped" style="width:100%">
        <thead>
            <tr>
                <th><span class="uk-text-bold">Document</span></th>
                <th>Team</th>
                <th>Published</th>
                <th>Author</th>
                <th>Category</th>
                <th>Scope</th>
            </tr>
        </thead>
        <tbody>
        % for doc in var['repo']['bookmarks']:
            <tr>
                <td><a class="uk-link-heading" href="${var['repo']['bookmarks'][doc]['URL']}"><span class="uk-text-small uk-text-truncate">${var['repo']['bookmarks'][doc]['Title'][0]}</span></a></td>
                <td><a class="uk-link-heading" href="#"><span class="uk-text-small">${var['repo']['bookmarks'][doc]['Team'][0]}</span></a></td>
                <td><a class="uk-link-heading" href="#"><span class="uk-text-small">${var['repo']['bookmarks'][doc]['Published'][0]}</span></a></td>
                <td><a class="uk-link-heading" href="#"><span class="uk-text-small">${var['repo']['bookmarks'][doc]['Author'][0]}</span></a></td>
                <td><a class="uk-link-heading" href="#"><span class="uk-text-small">${var['repo']['bookmarks'][doc]['Category'][0]}</span></a></td>
                <td><a class="uk-link-heading" href="#"><span class="uk-text-small">${var['repo']['bookmarks'][doc]['Scope'][0]}</span></a></td>
            </tr>
        % endfor
        </tbody>
        <tfoot>
        </tfoot>
    </table>
</div>
++++
