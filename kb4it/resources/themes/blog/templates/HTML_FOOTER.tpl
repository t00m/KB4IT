                </div>
                <!-- Sidebar Column :: START-->
                <div class="uk-width-1-3@m" uk-height-viewport="expand: true">
                  <div class="uk-sticky" uk-sticky="offset: 40">
                    <h2 class="uk-heading-line uk-text-center"><a class="uk-link-toggle" href="index.html"><span class="uk-link-heading">${var['repo']['title']}</span></a></h2>
                    <div class="sidebar">
<!--
                      <h5 class="sidebar-title">About</h5>
                      <p class="uk-text-small">${var['repo']['tagline']}</p>

-->

                        <!-- INDEX_TAB_STATS.tpl :: START -->
                        <div class="uk-grid-small uk-text-meta" uk-grid>
                            <div class="uk-width-expand uk-text-bold">
                                <a class="uk-link-heading" href="events.html">Events</a>
                            </div>
                        </div>
                        <div class="uk-grid-small uk-text-meta" uk-grid>
                            <div class="uk-width-expand uk-text-bold" uk-leader>
                                <a class="uk-link-heading" href="all.html">Documents</a>
                            </div>
                            <div>
                                <a href="all.html">${var['count_docs']}</a>
                            </div> <!-- Num of documents -->
                        </div>
                        <div class="uk-grid-small uk-text-meta" uk-grid>
                            <div class="uk-width-expand uk-text-bold" uk-leader>
                                <a class="uk-link-heading" href="properties.html">Properties</a>
                            </div>
                            <div><a href="properties.html">${var['count_keys']}</a></div> <!-- Num of properties or keys -->
                        </div>
                        <!-- Property leader items -->
                    % for item in var['leader_items']:
                        <div class="uk-grid-small uk-text-meta" uk-grid>
                            <div class="uk-width-1-6@m"></div>
                            <div class="uk-width-expand uk-text-bold" uk-leader><a class="uk-link-heading" href="${item['vfkey']}.html">${item['key']}</a></div>
                            <div><a href="${item['vfkey']}.html">${item['count_values']}</a></div>
                        </div>
                    % endfor
                        <!-- Property leader items -->

                      <div class="uk-text-center uk-card uk-card-body uk-card-big">
                        <hr class="uk-divider-icon">
                        <span class="uk-text-small uk-text-muted">Blog updated on<br/>${var['repo']['updated']}</span>
                        <p>
                            <span class="uk-link">
                                <a href="https://github.com/t00m/KB4IT" target="_blank">
                                    <img src="resources/common/images/kb4it-badge-built-with.svg">
                                </a>
                            </span>
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- Sidebar Column :: END-->
            </div>
            <!-- Main Content Column :: END-->
        </div>
        <!-- GRID :: END -->
    </div>
    <!-- Blog container :: END -->
<script>hljs.highlightAll();</script>
</body>
</html>
