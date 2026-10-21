---
DocType: How-to guide
Feature: Publishing
HelpId: web-server
Keyword: nginx, apache, rsync, http.server, intranet, file share
Level: basic
Order: 420
Section: Guides
Summary: Share the website by copying one folder to a web server, a file share or a laptop.
---

# Publish on any web server

The website is the `target/` folder. It is plain HTML, CSS and JavaScript, so anything that serves files can publish it. No PHP, database or KB4IT is needed on the server.

## Copy it to a server {#copy}

```bash
rsync -av --delete ~/mykb/target/ www.example.com:/var/www/kb/
```

`--delete` removes pages you deleted from the knowledge base. Run the command after every build, or add it to `bin/compile.sh`.

## Serve it with nginx {#nginx}

```nginx
server {
    listen 80;
    server_name kb.example.com;
    root /var/www/kb;
    index index.html;
}
```

## Show your own page for a missing address {#not-found}

techdoc, blog and bookshelf write `404.html` at the top of the site. GitHub Pages shows it on its own. Other servers need one line.

nginx, inside the `server` block:

```nginx
error_page 404 /404.html;
```

Apache, in the site configuration or `.htaccess`:

```apache
ErrorDocument 404 /404.html
```

The server shows the same file for a missing address at any depth, so a relative link in it only works at the top of the site. Set `site_url` in `repo.json` and the page uses absolute links and a `<base>` element, which works at any depth. `kb4it serve` also answers a missing page with `404.html` and status 404.

## Preview it on your computer {#preview}

Most pages work when opened from disk. To test it as a real website:

```bash
cd ~/mykb/target
python3 -m http.server 8000
```

Then open `http://localhost:8000/`. The [terminal interface](howto-use-tui.md) does the same with **Browse via Web Server**.

## Share it without a server {#share}

Copy `target/` to a shared folder or a USB stick and open `index.html`. The techdoc theme can also offer the whole site as a zip file on an admin page; see [techdoc](reference-theme-techdoc.md#admin).

!!! warning "Private documents"
    Anyone who can open the website can read every page, and the Markdown sources unless `"publish_sources": false`. Protect the server with the access control your web server offers.
