"""techdoc quality: the score of every document, the Quality and Quality guide pages and quality-index.js.

A theme-local feature. It scores the documents in prepare(), once per build and before any page
is built, so the tables of the property pages, the search index and the document pages all read
the same scores.
"""

import os
from datetime import datetime

from kb4it.core.people import named_people, person_status
from kb4it.core.util import html_id_for
from kb4it.theme import Feature

from .quality import (DIM_LABELS, DIMENSIONS, MAXIMA, TIER_LABELS, DocInput, assess, checklist, index_js,
                      load_skeletons, peer_stats, profile)
from .quality_guide import CHECKS as GUIDE_CHECKS
from .quality_guide import DIMS as GUIDE_DIMS
from .quality_page import duplicates, quick_wins, tier_mix
from .records import work_type

THEME_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKELETONS = os.path.join(THEME_DIR, 'templates', 'skeletons')


class Quality(Feature):
    """scores: {doc id: assessment}; stats: the peer statistics of quality-index.js."""

    name = "quality"
    requires = ("table_filter",)  # the Quality page filters its lists with the table filter bar
    templates = ("PAGE_QUALITY", "PAGE_QUALITY_GUIDE", "QUALITY_PANEL")
    reserves = ("quality-guide.md", "quality.md")

    def __init__(self, theme, engine):
        super().__init__(theme, engine)
        self.scores = {}
        self.stats = {}

    @property
    def db(self):
        return self.theme.internals.db

    @property
    def log(self):
        return self.theme.log

    def profile(self):
        return profile({'quality': self.theme.config.quality})

    def on(self):
        """Quality scores are on unless repo.json sets "quality": false or theme.json turns them off."""
        return self.site.repo.get('quality', True) is not False and self.profile().get('enabled', True)

    # --------------------------------------------------------------- scoring
    def prepare(self, site):
        """Score every document once per build."""
        self.scores, self.stats = {}, {}
        if not self.on():
            return
        prof = self.profile()
        skeletons = load_skeletons(SKELETONS)
        source_dir = site.paths.source
        db = self.db
        docs = [doc.id for doc in site.documents]
        known = set(docs)
        profile_docs = {p.doc_id for p in db.people.all_profiles()}
        profiles_on = self.author_profiles_on(prof)
        links = {}  # person -> Add page link, once per build: an Edit link reads the profile file
        today = datetime.now().date()
        for doc_id in docs:
            path = os.path.join(source_dir, doc_id)
            try:
                with open(path, encoding='utf-8') as fh:
                    text = fh.read()
            except OSError:
                continue
            doc = site.doc(doc_id)
            meta = {key: list(db.get_values(doc_id, key)) for key in db.get_doc_keys(doc_id)}
            data = DocInput(text, meta, len(doc.backlinks), known, source_dir, work_type(db, doc_id),
                            profile_docs, *(self.people_input(meta, links) if profiles_on else ({}, {})))
            self.scores[doc_id] = assess(data, prof, skeletons, today)
        self.stats = peer_stats(self.scores)
        tiers = [a.tier for a in self.scores.values()]
        counts = ' '.join(f'{t}={tiers.count(t)}' for t in ('exemplary', 'complete', 'basic', 'stub', 'retired'))
        self.log.info(f"[THEME] QUALITY docs={len(tiers)} {counts}")

    def author_profiles_on(self, prof):
        """Profile checks: theme.json quality.author_profiles true, false, or "auto" (on once there is a profile)."""
        mode = prof.get('author_profiles', 'auto')
        if mode not in (True, False, 'auto'):
            self.log.warning(f"[THEME] QUALITY_SETTING key=author_profiles value={mode!r} using=auto")
            mode = 'auto'
        return mode is True or (mode == 'auto' and len(self.db.people) > 0)

    def people_input(self, meta, links):
        """({person: status}, {person: Add page link}) of the people a document names, for the profile checks."""
        builder = self.theme.internals.builder
        settings, people = builder.people_settings(), self.db.people
        statuses = {}
        for name in named_people(meta, people, settings):
            found = people.lookup(name)
            statuses[name] = person_status(found, settings)
            if statuses[name] != 'ok' and name not in links:
                actions = builder.profile_actions(name, found)
                links[name] = actions['create'] or actions['edit']
        return statuses, {name: links[name] for name in statuses if name in links}

    # ----------------------------------------------------------------- views
    def view(self, doc_id):
        """What the header, the note and the Quality tab show for a document; None when there is no score."""
        assessment = self.scores.get(doc_id)
        if assessment is None or assessment.tier == 'retired':
            return None
        peer = assessment.peer
        return {
            'score': assessment.score,
            'tier': assessment.tier,
            'label': TIER_LABELS[assessment.tier],
            'peer': peer,
            'peer_name': 'document' if peer == 'Other' else peer.lower(),
            'page': html_id_for(doc_id),
            'dims': [{'key': d, 'label': DIM_LABELS[d], 'points': round(assessment.dims[d]), 'max': MAXIMA[d],
                      'percent': round(100 * assessment.dims[d] / MAXIMA[d]), 'tip': GUIDE_DIMS[d][1]} for d in DIMENSIONS],
            'checklist': checklist(assessment),
        }

    # ----------------------------------------------------------------- pages
    def pages(self, site):
        self.write_guide(site)
        self.write_quality_page(site)

    def write_guide(self, site):
        """The system page every Quality tab item links to: tiers, every check with an example, the skeletons."""
        if not self.on():
            return
        prof = self.profile()
        dims = []
        for key in DIMENSIONS:
            title, what = GUIDE_DIMS[key]
            checks = [dict(entry, key=check_key) for check_key, entry in GUIDE_CHECKS.items() if entry['dim'] == key]
            dims.append({'key': key, 'title': title, 'what': what, 'max': MAXIMA[key], 'checks': checks})
        skeletons = []
        for name, skeleton in sorted(load_skeletons(SKELETONS).items()):
            with open(os.path.join(SKELETONS, f'{name}-SKELETON.md'), encoding='utf-8') as fh:
                text = fh.read().strip()
            skeletons.append({'key': name.lower(), 'title': name.capitalize(),
                              'headings': [h.capitalize() for h in skeleton.headings], 'text': text})
        page = self.theme.template('PAGE_QUALITY_GUIDE').render(var={
            'tiers': prof['tiers'], 'retired': prof['retired_status'], 'dims': dims, 'skeletons': skeletons})
        site.page('quality-guide', 'Quality guide', page, markdown=True)

    def best(self, site, per_type=3):
        """Top documents per DocType for the Quality page Best documents section."""
        if not self.scores:
            return []
        floor = self.profile()['tiers']['complete']
        shelf = []
        for name in ('Tutorial', 'How-to guide', 'Reference', 'Explanation'):
            docs = sorted((d for d, a in self.scores.items() if a.peer == name and a.tier != 'retired' and a.score >= floor),
                          key=lambda d: (-self.scores[d].score, d))[:per_type]
            for doc_id in docs:
                a = self.scores[doc_id]
                doc = site.doc(doc_id)
                shelf.append({'title': doc.value('Title', doc_id), 'href': doc.url,
                              'score': a.score, 'tier': a.tier, 'type': name, 'year': (doc.date or '')[:4]})
        return shelf

    def write_quality_page(self, site):
        """The Quality page: tier mix, Exemplary documents, quick wins, broken links, missing images, no Summary, duplicates."""
        if not self.scores:
            return

        def title(doc_id):
            return site.doc(doc_id).value('Title', doc_id)

        live = {d: a for d, a in self.scores.items() if a.tier != 'retired'}
        bar, facets = site.features.table_filter.list_filter(sorted(live), 'kb-quality-lists')

        def ref(doc_id, **extra):
            return dict({'title': title(doc_id), 'href': html_id_for(doc_id), 'facets': facets(doc_id)}, **extra)

        broken, images = [], []
        for doc_id, a in sorted(live.items()):
            for c in a.checks:
                if c.key == 'check-broken-link' and not c.passed:
                    broken.append(ref(doc_id, target=c.todo.rsplit(' to ', 1)[-1]))
                elif c.key == 'check-missing-image' and not c.passed:
                    images.append(ref(doc_id, target=c.todo.rsplit(' image ', 1)[-1]))
        best = sorted((d for d, a in live.items() if a.tier == 'exemplary'), key=lambda d: (-live[d].score, d))
        pairs = duplicates({d: title(d) for d in live})
        quality_page = {
            'mix': tier_mix(self.scores),
            'best': self.best(site),
            'exemplary': [ref(d, score=live[d].score, peer=live[d].peer) for d in best],
            'wins': [dict(ref(w['doc']), **w) for w in quick_wins(live, self.profile())],
            'broken': broken,
            'images': images,
            'no_summary': [ref(d) for d in sorted(live) if not any(c.key == 'check-summary' and c.passed for c in live[d].checks)],
            'duplicates': [(ref(a, score=live[a].score), ref(b, score=live[b].score), facets([a, b]))
                           for a, b, _ in pairs],
            'filter': bar,
        }
        site.page('quality', 'Quality', self.theme.template('PAGE_QUALITY').render(var={'q': quality_page}))

    def after_deploy(self, site):
        """quality-index.js, which the search page reads for the tier of each result; removed when quality is off."""
        index_path = os.path.join(site.paths.target, 'quality-index.js')
        if self.scores:
            with open(index_path, 'w', encoding='utf-8') as fh:
                fh.write(index_js(self.stats))
        elif os.path.exists(index_path):
            os.unlink(index_path)
