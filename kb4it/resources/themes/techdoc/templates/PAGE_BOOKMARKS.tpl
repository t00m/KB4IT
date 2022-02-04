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
                <th>Category</th>
                <th>Scope</th>
            </tr>
        </thead>
        <tbody>
        % for doc in var['repo']['bookmarks']:
            <%
                title = var['repo']['bookmarks'][doc]['Title'][0]
                title_url = var['repo']['bookmarks'][doc]['URL']
                team = var['repo']['bookmarks'][doc]['Team'][0]
                team_url = "Team_%s.html" % team
                published = var['repo']['bookmarks'][doc]['Published'][0]
                category = var['repo']['bookmarks'][doc]['Category'][0]
                category_url = "Category_%s.html" % category
                scope = var['repo']['bookmarks'][doc]['Scope'][0]
                scope_url = "Scope_%s.html" % scope
            %>
            <tr>
                <td><a class="uk-link-heading" href="${title_url}"><span class="uk-text-small uk-text-truncate">${title}</span></a></td>
                <td><a class="uk-link-heading" href="${team_url}"><span class="uk-text-small">${team}</span></a></td>
                <td><a class="uk-link-heading" href="#"><span class="uk-text-small">${published}</span></a></td>
                <td><a class="uk-link-heading" href="${category_url}"><span class="uk-text-small">${category}</span></a></td>
                <td><a class="uk-link-heading" href="${scope_url}"><span class="uk-text-small">${scope}</span></a></td>
            </tr>
        % endfor
        </tbody>
        <tfoot>
        </tfoot>
    </table>
</div>
++++
