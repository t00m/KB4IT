= Index

++++
<!-- This is the nav containing the toggling elements -->
<ul class="uk-tab" uk-switcher>
    <li><a href="#"><span uk-icon="icon: list"></span><span class="uk-text-bold"> Documents</span></a></li>
    <li><a href="#"><span uk-icon="icon: calendar"></span><span class="uk-text-bold"> Calendar</span></a></li>
</ul>
<!-- This is the container of the content items -->
<ul class="uk-switcher uk-margin">
    <li>
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
                    % for item in var['kbdict']['document']:
                        <%
                            from kb4it.core.util import get_human_datetime, fuzzy_date_from_timestamp
                            def get_key_value(var, item, key):
                                try:
                                    return var['kbdict']['document'][item][key]
                                except:
                                    return ''
                                    
                            title = var['kbdict']['document'][item]['Title'][0]
                            team = ', '.join(get_key_value(var, item, 'Team'))                    
                            title_url = item.replace('.adoc', '.html')
                            try:
                                published = var['kbdict']['document'][item]['Published'][0][0:10]
                            except:
                                published = ''
                            author = ', '.join(get_key_value(var, item, 'Author'))    
                            category = ', '.join(get_key_value(var, item, 'Category'))    
                            scope = ', '.join(get_key_value(var, item, 'Scope'))    
                        %>
                        <tr>
                            <td><a class="uk-link-toggle" href="${title_url}"><span class="uk-text-small uk-text-truncate">${title}</span></a></td>
                            <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${team}</span></a></td>
                            <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${published}</span></a></td>
                            <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${author}</span></a></td>
                            <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${category}</span></a></td>
                            <td><a class="uk-link-toggle" href="#"><span class="uk-text-small">${scope}</span></a></td>
                        </tr>
                    % endfor
                </tbody>
                <tfoot>
                </tfoot>
            </table>
        </div>
    </li>
    <li>
        <div class ="uk-container uk-overflow-auto uk-box-shadow-xlarge">
        ${var['trimester']}
        </div>
    </li>
</ul>
++++