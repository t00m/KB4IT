                </div>
                <!-- Sidebar Column :: START-->
                <div class="uk-width-1-3@m">
                  <div class="uk-sticky" uk-sticky="offset: 40">
                    <h2 class="uk-heading-line uk-text-center"><span>My Simple Blog</span></h2>
                    <div class="sidebar">
                      <h3 class="sidebar-title">About</h3>
                      <p>Welcome to my simple blog. Here I share thoughts on web development, design, and technology.</p>
                      <h3 class="sidebar-title">Topics</h3>
                          <div>
                            % for topic in var['topics']:
                                <span class="tag"><a href="Topic_${topic}.html">${topic}</a></span>
                            % endfor
                        </div>
                      <h3 class="sidebar-title">Tags</h3>
                          <div>
                            % for tag in var['tags']:
                                <span class="tag"><a href="Tag_${tag}.html">${tag}</a></span>
                            % endfor
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
