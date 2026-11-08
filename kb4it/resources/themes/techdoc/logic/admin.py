#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""techdoc admin area: backups and the admin page."""

import os
import shutil
import zipfile
from datetime import datetime

from lxml import etree

from kb4it.core.util import (
    get_human_datetime,
    get_source_docs,
    human_size,
    slugify,
    valid_filename,
)
from kb4it.theme import Feature, q


class Admin(Feature):
    """techdoc's admin area: target/admin/ with a backup page and two zip files (repo.json "admin": true).

    A theme-local feature: it runs after deployment, after the gallery thumbnails and the
    quality index are in the site, so the site zip holds them.
    """

    name = "admin"
    uses = ("gallery", "quality")

    # What the code below reads from the build; theme.internals is set before the first stage.
    @property
    def srvbes(self):
        return self.theme.internals.backend

    @property
    def log(self):
        return self.theme.log

    def template(self, name):
        return self.theme.template(name)

    def after_deploy(self, site):
        """Build the admin area once the site is deployed; only with repo.json "admin": true.

        It writes an admin subdirectory in the target with a backup page and two zip files:
        one holding the source Markdown documents, another holding the whole compiled site.
        """
        repo = site.repo
        if not repo.get('admin', False):
            self.log.debug("[ADMIN] DISABLED")
            return

        admin_dir = os.path.join(site.paths.target, 'admin')
        os.makedirs(admin_dir, exist_ok=True)

        slug = slugify(repo.get('title', ''))
        if not slug:
            slug = valid_filename(os.path.basename(str(self.srvbes.get_path('root'))))
        zip_sources = os.path.join(admin_dir, f"{slug}_sources.zip")
        zip_site = os.path.join(admin_dir, f"{slug}_site.zip")

        self.clean_stale_backups(admin_dir, [zip_sources, zip_site])

        if self.backups_needed(zip_sources, zip_site):
            self.build_zip_sources(zip_sources)
            self.build_zip_site(zip_site, admin_dir)
        else:
            self.log.debug("[ADMIN] ZIP_SKIP reason=no_changes")

        self.build_page_admin(admin_dir, zip_sources, zip_site)

    def clean_stale_backups(self, admin_dir, keep):
        """Delete backups left behind by a previous repository title."""
        current = {os.path.basename(path) for path in keep}
        for filename in os.listdir(admin_dir):
            if filename in current:
                continue
            if filename.endswith(('_sources.zip', '_site.zip')):
                os.unlink(os.path.join(admin_dir, filename))
                self.log.debug(f"[ADMIN] STALE_BACKUP_DELETED file={q(filename)}")

    def backups_needed(self, *paths):
        """Rebuild the backups on a forced build, when the build compiled
        something, or when any of the zip files is missing.
        """
        if self.srvbes.get_value('runtime', 'force_all'):
            return True
        for path in paths:
            if not os.path.exists(path):
                return True
        return (self.srvbes.get_value('runtime', 'ncd') or 0) > 0

    def get_tmp_zip_path(self, zip_path):
        """Return the temporary path a zip file is written to.

        Zip files are built in the temporary directory and moved into the
        target afterwards, so a half written file is never linked and the
        site zip never packs itself.
        """
        tmp_dir = self.srvbes.get_path('tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        return os.path.join(tmp_dir, os.path.basename(zip_path))

    def build_zip_sources(self, zip_path):
        """Pack the source Markdown documents, without assets."""
        docs = sorted(get_source_docs(self.srvbes.get_path('source')))
        tmp_path = self.get_tmp_zip_path(zip_path)
        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zfile:
            for doc in docs:
                zfile.write(doc, os.path.basename(doc))
        shutil.move(tmp_path, zip_path)
        self.log.info(f"[ADMIN] ZIP_BUILT file={q(os.path.basename(zip_path))} docs={len(docs)}")

    def build_zip_site(self, zip_path, admin_dir):
        """Pack the whole compiled site, excluding the admin directory."""
        target = self.srvbes.get_path('target')
        admin_real = os.path.realpath(admin_dir)
        tmp_path = self.get_tmp_zip_path(zip_path)
        count = 0
        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zfile:
            for root, dirs, files in os.walk(target):
                dirs[:] = sorted(d for d in dirs
                                 if os.path.realpath(os.path.join(root, d)) != admin_real)
                for filename in sorted(files):
                    filepath = os.path.join(root, filename)
                    zfile.write(filepath, os.path.relpath(filepath, target))
                    count += 1
        shutil.move(tmp_path, zip_path)
        self.log.info(f"[ADMIN] ZIP_BUILT file={q(os.path.basename(zip_path))} files={q(count)}")

    def get_backup_item(self, path, name, description):
        """Describe a backup file for the admin page."""
        item = {}
        item['name'] = name
        item['description'] = description
        item['filename'] = os.path.basename(path)
        item['href'] = f"admin/{os.path.basename(path)}"
        if os.path.exists(path):
            stat = os.stat(path)
            item['size'] = human_size(stat.st_size)
            item['timestamp'] = get_human_datetime(datetime.fromtimestamp(stat.st_mtime))
        else:
            item['size'] = 'n/a'
            item['timestamp'] = 'n/a'
        return item

    def relocate_links(self, tree, prefix='../'):
        """Prefix relative urls so the page works from a subdirectory."""
        for attribute in ('href', 'src'):
            for element in tree.xpath(f'//*[@{attribute}]'):
                url = element.get(attribute)
                if not url or url.startswith(('#', '/', '../')):
                    continue
                if ':' in url.split('/')[0]:  # http:, mailto:, javascript:, data:
                    continue
                element.set(attribute, prefix + url)

    def build_page_admin(self, admin_dir, zip_sources, zip_site):
        """Write the admin page with the same layout as any other page."""
        HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
        HTML_BODY = self.template('HTML_BODY')
        HTML_FOOTER = self.template('HTML_FOOTER')
        TPL_PAGE_ADMIN = self.template('PAGE_ADMIN')

        var = self.theme.base_var()
        var['page']['title'] = 'Admin'
        var['page']['title-tooltip'] = 'Admin'
        var['SystemPage'] = True
        var['has_toc'] = False
        var['toc'] = ''
        var['metadata'] = ''
        var['fmt'] = 'md'
        var['timestamp'] = get_human_datetime(datetime.now())
        var['actions'] = self.site.features.metadata.actions(var)
        var['backups'] = [
            self.get_backup_item(
                zip_sources, 'Documents only',
                'Every Markdown document in the repository. No assets.'),
            self.get_backup_item(
                zip_site, 'Full site',
                'The whole compiled site: documents, pages and assets.'),
        ]
        var['source_html'] = TPL_PAGE_ADMIN.render(var=var)

        HTML = HTML_HEADER_COMMON.render(var=var)
        HTML += HTML_BODY.render(var=var)
        HTML += HTML_FOOTER.render(var=var)

        page_path = os.path.join(admin_dir, 'index.html')
        HTML = self.theme.internals.builder.inject_head_meta(HTML, 'admin/index.html')
        parser = etree.HTMLParser()
        tree = etree.fromstring(HTML, parser)
        self.relocate_links(tree)
        pretty_html = etree.tostring(tree, pretty_print=True, method="html", encoding="unicode")
        with open(page_path, 'w', encoding='utf-8') as fhtml:
            fhtml.write(f"<!DOCTYPE html>\n{pretty_html}")
        self.log.info(f"[ADMIN] PAGE_BUILT path={q(page_path)}")
