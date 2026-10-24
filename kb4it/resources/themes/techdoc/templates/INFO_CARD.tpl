<%
    card = var['card']
    history = card['history']
%>
<!-- INFO CARD :: START -->
<section class="kb-info-card${' kb-open' if card['open'] else ''}" id="kb-info-card" aria-label="Document information">
    <div class="kb-info-bar kb-noprint">
        <ul class="kb-info-tabs" data-uk-tab="connect: #kb-info-panels; animation: uk-animation-fade">
            <li class="uk-active" data-kb-tab="details"><a href="#kb-info-details">Details</a></li>
% if card.get('quality_html'):
            <li data-kb-tab="quality"><a href="#kb-info-quality">Quality</a></li>
% endif
% if card.get('related'):
            <li data-kb-tab="related"><a href="#kb-info-related">Related</a></li>
% endif
            <li data-kb-tab="history"><a href="#kb-info-history">History</a></li>
        </ul>
        <button class="kb-info-toggle kb-noprint" type="button" aria-expanded="${'true' if card['open'] else 'false'}" aria-controls="kb-info-panels" title="Show or hide the document information"><span data-uk-icon="icon: chevron-down"></span></button>
    </div>
    <div class="kb-info-panels" id="kb-info-panels">
        <!-- DETAILS PANEL :: START -->
        <div id="kb-info-details" class="${'kb-print' if card['print']['details'] else 'kb-noprint'} uk-active">
            <h2 class="kb-info-heading">Document details</h2>
            <div class="kb-groups">
% for group in card['groups']:
                <div class="kb-group">
                    <h3>${group['name']}</h3>
                    <dl>
%     for item in group['items']:
                        <dt>${item['key']}</dt>
                        <dd>
%         for value in item['values']:
%             if group['chips']:
                            <a class="kb-obj" href="${value['url']}">${value['text']}</a>
%             else:
                            <a href="${value['url']}">${value['text']}</a>${'' if loop.last else ','}
%             endif
%         endfor
                        </dd>
%     endfor
                    </dl>
                </div>
% endfor
            </div>
        </div>
        <!-- DETAILS PANEL :: END -->
% if card.get('quality_html'):
        <!-- QUALITY PANEL :: START -->
        <div id="kb-info-quality" class="${'kb-print' if card['print']['quality'] else 'kb-noprint'}">
            <h2 class="kb-info-heading">Quality</h2>
${card['quality_html'] | n}
        </div>
        <!-- QUALITY PANEL :: END -->
% endif
% if card.get('related'):
<% rel = card['related'] %>
        <!-- RELATED PANEL :: START -->
        <div id="kb-info-related" class="${'kb-print' if card['print']['related'] else 'kb-noprint'}">
            <h2 class="kb-info-heading">Related</h2>
%     if rel['linked']:
            <h3 class="kb-related-title">Linked from</h3>
            <ul class="kb-related">
%         for item in rel['linked']:
                <li><a href="${item['href']}">${item['title']}</a>
%             if item['chip']:
                    <span class="kb-q-chip kb-q-${item['chip']['tier']}">${item['chip']['label']}</span>
%             endif
                </li>
%         endfor
            </ul>
%     endif
%     if rel['similar']:
            <h3 class="kb-related-title">Related documents</h3>
            <ul class="kb-related">
%         for item in rel['similar']:
                <li><a href="${item['href']}">${item['title']}</a>
%             if item['chip']:
                    <span class="kb-q-chip kb-q-${item['chip']['tier']}">${item['chip']['label']}</span>
%             endif
                    <span class="kb-related-shared">${item['shared']}</span></li>
%         endfor
            </ul>
%     endif
        </div>
        <!-- RELATED PANEL :: END -->
% endif
        <!-- HISTORY PANEL :: START -->
        <div id="kb-info-history" class="${'kb-print' if card['print']['history'] else 'kb-noprint'}">
            <h2 class="kb-info-heading">History</h2>
            <dl class="kb-history">
% if history['date']:
                <dt>Date</dt>
                <dd>${history['date']}</dd>
% endif
                <dt>Source file</dt>
                <dd><code>${history['source']}</code>: <a href="#modal-full-source" data-uk-toggle>View source</a>
% if history['edit_url']:
                    , <a href="${history['edit_url']}" target="_blank" rel="noopener">Edit</a>
% endif
                </dd>
                <dt>Built</dt>
                <dd>${history['built']}</dd>
            </dl>
        </div>
        <!-- HISTORY PANEL :: END -->
    </div>
</section>
<!-- INFO CARD :: END -->
