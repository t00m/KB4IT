                </div>
                <!-- Sidebar Column :: START-->
                <div class="uk-width-1-3@m" uk-height-viewport="expand: true">
                  <div class="uk-sticky" uk-sticky="offset: 40">
                    <h2 class="uk-heading-line uk-text-center"><a class="uk-link-toggle" href="index.html"><span class="uk-link-heading">${var['repo']['title']}</span></a></h2>
                    <div class="sidebar">
                      <h5 class="sidebar-title">About</h5>
                      <p class="uk-text-small">${var['repo']['tagline']}</p>
                      <h5 class="sidebar-title">Topics</h5>
                          <div>
                            % for topic in var['topics']:
                                <span class="tag"><a href="Topic_${topic}.html">${topic}</a></span>
                            % endfor
                        </div>
                      <h5 class="sidebar-title">Tags</h5>
                          <div>
                            % for tag in var['tags']:
                                <span class="tag"><a href="Tag_${tag}.html">${tag}</a></span>
                            % endfor
                        </div>
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
</body>
</html>
