/* ============================================================================
   KB4IT - "Bookshelf" theme  .  runtime behaviour
   ----------------------------------------------------------------------------
   - turns plain Markdown <pre><code> blocks into the dark .code component
     (language label + copy button + light shell highlighting)
   - numbers the article sections and feeds the right rail "On this page" TOC
   - fills the left chapter-nav sub-anchors under the current chapter
   - scroll-spy that keeps TOC and sub-anchors in sync with the viewport
   - the prototype page switcher is intentionally NOT shipped here
   ============================================================================ */
(function () {
    "use strict";

    var SHELL_LANGS = {
        "": 1, "bash": 1, "sh": 1, "shell": 1, "console": 1,
        "zsh": 1, "text": 1, "plaintext": 1
    };

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    /* Light shell highlighting on an already HTML-escaped line. */
    function highlightShellLine(line, isShell) {
        if (line.trim() === "") {
            return line;
        }
        // whole-line comment
        if (/^\s*#/.test(line)) {
            return '<span class="cmt">' + line + "</span>";
        }
        // split a trailing inline comment ( # ... ) off the code part
        var comment = "";
        var hash = line.search(/\s#/);
        if (hash !== -1) {
            comment = '<span class="cmt">' + line.slice(hash) + "</span>";
            line = line.slice(0, hash);
        }
        // flags: -x or --long, kept readable
        line = line.replace(/(^|\s)(--?[A-Za-z][\w-]*)/g,
            function (m, pre, flag) { return pre + '<span class="flag">' + flag + "</span>"; });
        // command name: first token of the line
        if (isShell) {
            line = line.replace(/^(\s*)([A-Za-z][\w./-]*)/,
                function (m, pre, cmd) { return pre + '<span class="cmd">' + cmd + "</span>"; });
        }
        return line + comment;
    }

    function decorateCodeBlocks(root) {
        var pres = root.querySelectorAll("pre");
        pres.forEach(function (pre) {
            if (pre.closest(".code")) { return; }
            var code = pre.querySelector("code");
            var raw = (code ? code.textContent : pre.textContent).replace(/\n$/, "");

            var lang = "code";
            if (code) {
                var cls = (code.className || "").match(/language-([\w-]+)/);
                if (cls) { lang = cls[1]; }
            }
            var isShell = !!SHELL_LANGS[lang === "code" ? "" : lang];

            var html = raw.split("\n").map(function (line) {
                return highlightShellLine(escapeHtml(line), isShell);
            }).join("\n");

            var box = document.createElement("div");
            box.className = "code";
            box.innerHTML =
                '<div class="code-bar">' +
                    '<span class="lang">' + escapeHtml(lang) + "</span>" +
                    '<button class="copy" type="button">Copy</button>' +
                "</div>" +
                "<pre><code>" + html + "</code></pre>";
            box.dataset.raw = raw;
            pre.parentNode.replaceChild(box, pre);
        });
    }

    function wireCopyButtons(root) {
        root.querySelectorAll(".code .copy").forEach(function (btn) {
            btn.addEventListener("click", function () {
                var box = btn.closest(".code");
                var text = box ? (box.dataset.raw || box.querySelector("code").innerText) : "";
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(text).catch(function () {});
                }
                var old = btn.textContent;
                btn.textContent = "Copied ✓";
                setTimeout(function () { btn.textContent = old; }, 1400);
            });
        });
    }

    /* Number the article H2s and return [{id, text}] for the navigators. */
    function numberSections(article) {
        var sections = [];
        var heads = article.querySelectorAll("h2");
        heads.forEach(function (h, i) {
            if (!h.id) { h.id = "section-" + (i + 1); }
            if (!h.querySelector(".n")) {
                var n = document.createElement("span");
                n.className = "n";
                n.textContent = ("0" + (i + 1)).slice(-2);
                h.insertBefore(n, h.firstChild);
            }
            sections.push({ id: h.id, text: h.textContent.replace(/^\d+\s*/, "").trim() });
        });
        return sections;
    }

    function buildToc(container, sections) {
        if (!container) { return; }
        container.innerHTML = sections.map(function (s) {
            return '<a href="#' + s.id + '">' + s.text + "</a>";
        }).join("");
    }

    function buildChapnavSubs(container, sections) {
        if (!container) { return; }
        container.innerHTML = sections.map(function (s) {
            return '<a class="sub" href="#' + s.id + '">' + s.text + "</a>";
        }).join("");
    }

    /* Highlight the section nearest the top of the viewport. */
    function setupScrollSpy(sections) {
        if (!sections.length) { return; }
        var links = {};
        sections.forEach(function (s) {
            links[s.id] = document.querySelectorAll('a[href="#' + s.id + '"]');
        });
        var current = null;
        function spy() {
            var offset = 120;
            var active = sections[0].id;
            for (var i = 0; i < sections.length; i++) {
                var el = document.getElementById(sections[i].id);
                if (el && el.getBoundingClientRect().top - offset <= 0) {
                    active = sections[i].id;
                }
            }
            if (active === current) { return; }
            current = active;
            sections.forEach(function (s) {
                (links[s.id] || []).forEach(function (a) {
                    a.classList.toggle("cur", s.id === active);
                });
            });
        }
        window.addEventListener("scroll", spy, { passive: true });
        spy();
    }

    function init() {
        var article = document.querySelector(".article");
        var scope = article || document.querySelector(".wrap") || document.body;

        decorateCodeBlocks(scope);
        wireCopyButtons(scope);

        if (article) {
            var sections = numberSections(article);
            buildToc(document.getElementById("bk-toc"), sections);
            buildChapnavSubs(document.getElementById("bk-chapnav-subs"), sections);
            setupScrollSpy(sections);
        }

        var top = document.querySelector(".foot-top");
        if (top) {
            top.addEventListener("click", function (e) {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: "smooth" });
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
