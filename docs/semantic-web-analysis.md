# Adding Semantic Web capabilities to KB4IT — analysis

- **Status:** investigation / proposal (no implementation yet)
- **Date:** 2026-07-13
- **Scope:** RDF export, embedded structured data, SPARQL querying, vocabulary selection

## 1. Summary

KB4IT's in-memory database is already, structurally, an RDF graph: every entry
is `document → property → values`, which maps 1:1 onto triples
(`subject → predicate → object`). Adding Semantic Web support is therefore an
*export and mapping* problem, not a redesign.

Recommended approach, in shippable phases:

1. Embed **JSON-LD** (schema.org) in every generated page.
2. Emit a whole-repo **RDF dump** (`kb.ttl` / `kb.jsonld`) at build time using `rdflib`.
3. Offer **client-side SPARQL** in the browser with Comunica — keeps the site
   100% static, true to KB4IT's serverless philosophy.
4. Optionally, a **`kb4it sparql` CLI command** wrapping `rdflib-endpoint` for a
   real SPARQL 1.1 Protocol endpoint.

Vocabularies: **Dublin Core Terms** as the backbone, **schema.org** for in-page
JSON-LD, **SKOS** for tags/categories, **FOAF** for authors, **DCAT + VoID** to
describe the dump itself, plus a small repo-local namespace for arbitrary
custom frontmatter keys.

## 2. Why KB4IT is a natural fit

The data model in `kb4it/services/database.py` is
`self.db[docId][key] = [values]` — a document with multi-valued properties.
In RDF terms:

```turtle
<https://example.org/kb/daily-backup-runbook.html>
    dcterms:title    "Daily backup runbook" ;
    dcterms:creator  [ a foaf:Person ; foaf:name "Tomás Vírseda" ] ;
    dcterms:date     "2026-05-19"^^xsd:date ;
    dcterms:subject  <https://example.org/kb/concept/tag/backup> ,
                     <https://example.org/kb/concept/tag/housekeeping> .
```

The key/value index pages KB4IT already generates (`Tag_backup.html`, …) are
essentially materialized SPARQL queries of the form
`SELECT ?doc WHERE { ?doc kb:Tag "backup" }`. The semantic layer formalizes
what KB4IT already does.

**Prerequisite:** RDF requires absolute URIs, and KB4IT currently produces
purely relative links. A new optional `repo.json` key is needed, e.g.
`"url": "https://t00m.github.io/techdoc/"`, used as the base for minting
document and concept URIs. Without it, the exporter can fall back to a
placeholder base and still work locally.

## 3. Recommended architecture: three layers

### Layer 1 — JSON-LD embedded in every page (cheap, big win)

During page generation (natural hooks: `builder.py`'s `build_page` /
`page_hook_post`, or `apply_transformations` where lxml post-processing already
happens), inject a `<script type="application/ld+json">` block into each
document page using schema.org types (`TechArticle` for techdoc, `BlogPosting`
for blog). Immediate SEO / rich-results benefit; every page becomes
self-describing. No new runtime, no new dependencies.

### Layer 2 — Build-time RDF dump (the knowledge graph)

A new service, e.g. `kb4it/services/semantic.py`, running after compilation
(alongside `post_activities`), walks `Database.db` and emits to `target/`:

- `kb.ttl` — Turtle dump of all documents, properties, and concept schemes
- `kb.jsonld` — the same graph as JSON-LD
- optionally `void.ttl` / DCAT metadata describing the dataset itself

Implementation with `rdflib` (mature, pure Python, BSD). Make it an optional
extra — `pip install kb4it[semantic]` — so the core stays lean, consistent with
the current minimal dependency set (Mako, Markdown, PyYAML, lxml). The export
is a single linear pass over the in-memory DB (negligible build cost) and can
participate in incremental builds: the dump only needs regeneration when any
metadata hash changed.

### Layer 3 — SPARQL, two flavors

**Option A — client-side SPARQL, zero servers (recommended default).**
[Comunica](https://comunica.dev/docs/query/getting_started/query_browser_app/)
is a JavaScript SPARQL engine that runs entirely in the browser and evaluates
full SPARQL 1.1 queries directly over the published Turtle file. A theme ships
a `sparql.html` page with a query textarea that loads `kb.ttl` and executes
queries client-side. This preserves KB4IT's core promise (static, serverless,
host on GitHub Pages / S3 / nginx) while making the knowledge base genuinely
queryable. Mirrors how the existing "pseudo-dynamic search" works. Turtle is
fine into the tens of thousands of documents.

**Option B — real SPARQL endpoint via a new CLI command.**
[`rdflib-endpoint`](https://github.com/vemonet/rdflib-endpoint) (actively
maintained, [PyPI](https://pypi.org/project/rdflib-endpoint/)) wraps an rdflib
graph in a FastAPI app implementing the SPARQL 1.1 Protocol, with a built-in
YASGUI query UI and CORS support. A
`kb4it sparql <config.json> [--port 8000]` subcommand would load
`target/kb.ttl` and serve `/sparql` — roughly 50 lines, fitting the existing
CLI dispatch (`main.py` → `workflow.py`). It has an `[oxigraph]` extra for a
faster Rust-backed store.

For heavy production use, the same `kb.ttl` loads into Apache Jena Fuseki or an
Oxigraph server — the dump makes KB4IT triplestore-agnostic, which is the right
boundary: **KB4IT produces the graph; serving it at scale is the host's job.**

## 4. Vocabulary selection

Do not invent a big ontology — reuse established vocabularies, map known
frontmatter keys onto them, and fall back to a repo-local namespace for
everything else.

| KB4IT concept | Vocabulary | Terms |
|---|---|---|
| Core document metadata | Dublin Core Terms (`dcterms:`) | `title`, `creator`, `date`, `modified`, `subject`, `type`, `language` |
| Page-level markup / SEO | schema.org (`schema:`) | `TechArticle`, `BlogPosting`, `headline`, `author`, `datePublished`, `keywords`, `about` |
| Tags, Categories, Topics | SKOS (`skos:`) | each `Tag`/`Category` value becomes a `skos:Concept` in a `skos:ConceptScheme`; `skos:broader` later enables real taxonomies |
| Authors / People | FOAF (`foaf:`) | `foaf:Person`, `foaf:name` |
| The dataset/dump itself | DCAT + VoID | `dcat:Dataset`, `dcat:distribution`, `void:triples` |
| Arbitrary custom keys (`OS`, `Product`, `Status`, …) | repo-local namespace | e.g. `kb: <https://example.org/kb/ns#>` → `kb:OS`, `kb:Product` |

The two-tier mapping is the key design decision: KB4IT frontmatter is
deliberately free-form, so a complete hardcoded mapping is impossible. Known
keys (`Author`, `Date`, `Tag`, `Category`, `DocType`) map to standard terms;
unknown keys get predicates minted in the repo's own namespace. Power users can
override the mapping in `repo.json`:

```json
"semantic": {
  "url": "https://t00m.github.io/techdoc/",
  "mappings": { "Team": "schema:contributor", "Status": "kb:status" }
}
```

SIOC was considered for the blog theme and rejected: schema.org's
`BlogPosting` covers the case with far wider adoption.

### 4.1 Dublin Core Terms (`dcterms:`)

Namespace: `http://purl.org/dc/terms/`

The oldest and most universal metadata vocabulary, maintained by the Dublin
Core Metadata Initiative (DCMI); originated at a 1995 workshop in Dublin, Ohio.
~55 properties for describing any resource: `dcterms:title`,
`dcterms:creator`, `dcterms:date`, `dcterms:subject`, `dcterms:modified`,
`dcterms:language`, `dcterms:license`. Deliberately generic — it says nothing
about *what kind* of thing is described, only its bibliographic-style
attributes.

Use the modern `dcterms:` namespace (defined ranges and datatypes), not the
legacy Dublin Core Elements 1.1 (`dc:`, `http://purl.org/dc/elements/1.1/`).

For KB4IT: the natural backbone. `Author → dcterms:creator`,
`Date → dcterms:date`, `Tag/Category → dcterms:subject`, H1 title →
`dcterms:title`.

- Spec: <https://www.dublincore.org/specifications/dublin-core/dcmi-terms/>
- DCMI home: <https://www.dublincore.org/>

### 4.2 schema.org (`schema:`)

Namespace: `https://schema.org/`

Large pragmatic vocabulary launched in 2011 by Google, Microsoft, Yahoo and
Yandex so search engines could understand page content. ~800 types in a
hierarchy (`Thing → CreativeWork → Article → TechArticle` / `BlogPosting`)
plus properties (`headline`, `author`, `datePublished`, `keywords`, `about`).
Less about formal knowledge representation, more about broad interoperability —
it powers Google's rich results; idiomatic serialization is JSON-LD in a
`<script type="application/ld+json">` tag.

For KB4IT: the vocabulary for the in-page layer (Phase 1). Marking each page as
`TechArticle` / `BlogPosting` yields SEO benefits immediately, independent of
any SPARQL story.

- Home / type tree: <https://schema.org/>
- Getting started: <https://schema.org/docs/gs.html>
- `TechArticle`: <https://schema.org/TechArticle>

### 4.3 SKOS — Simple Knowledge Organization System (`skos:`)

Namespace: `http://www.w3.org/2004/02/skos/core#`

W3C Recommendation (2009) for representing knowledge organization systems:
taxonomies, thesauri, tag systems, classification schemes. Each term becomes a
`skos:Concept` with a URI, labels (`skos:prefLabel`, `skos:altLabel`), and
relations: `skos:broader` / `skos:narrower` (hierarchy), `skos:related`
(association). Concepts group into a `skos:ConceptScheme`. Standard across
national libraries, EU vocabularies, UNESCO, Getty.

For KB4IT: the biggest conceptual upgrade. Today `Tag: backup` is just a
string; as SKOS, `backup` becomes a first-class concept with its own URI (which
can be the existing `Tag_backup.html` page URL). Later,
`backup skos:broader sysadmin` gives hierarchical navigation essentially for
free.

- Spec: <https://www.w3.org/TR/skos-reference/>
- Primer: <https://www.w3.org/TR/skos-primer/>

### 4.4 FOAF — Friend of a Friend (`foaf:`)

Namespace: `http://xmlns.com/foaf/0.1/`

One of the earliest Semantic Web vocabularies (2000), for describing people,
their attributes, and their social/organizational connections: `foaf:Person`,
`foaf:name`, `foaf:mbox`, `foaf:homepage`, `foaf:knows`, plus
`foaf:Organization` and `foaf:Document`. Small, stable, universally understood
by RDF tooling — the conventional way to say "this creator is a person with
this name" rather than an opaque string.

For KB4IT: the object side of `dcterms:creator` — each distinct `Author` value
becomes a `foaf:Person` with `foaf:name`, enabling queries like "all documents
by authors who also wrote about X".

- Spec: <http://xmlns.com/foaf/spec/>
- Project page: <http://xmlns.com/foaf/0.1/>

### 4.5 DCAT + VoID — describing the dataset itself

These describe not the documents but the *RDF dump as a dataset*, which makes
the knowledge base discoverable as Linked Data.

**DCAT — Data Catalog Vocabulary** (`dcat:`, `http://www.w3.org/ns/dcat#`).
W3C Recommendation (current version DCAT 3, 2024) for describing datasets and
catalogs: a `dcat:Dataset` with `dcat:distribution` entries (one per format —
`kb.ttl`, `kb.jsonld`), each with `dcat:downloadURL` and `dcat:mediaType`.
The standard behind government open-data portals (data.europa.eu, data.gov).

- Spec: <https://www.w3.org/TR/vocab-dcat-3/>

**VoID — Vocabulary of Interlinked Datasets** (`void:`,
`http://rdfs.org/ns/void#`). Older, complementary W3C Interest Group Note
specifically for RDF datasets: statistics (`void:triples`, `void:entities`),
vocabularies used (`void:vocabulary`), access points (`void:sparqlEndpoint`,
`void:dataDump`), linksets to other datasets. Convention: publish at
`/.well-known/void`.

- Spec: <https://www.w3.org/TR/void/>

For KB4IT: a small auto-generated `void.ttl`/DCAT block in the dump — "this
knowledge base has 342 documents and 4,812 triples, uses dcterms/skos/foaf,
download it here, query it there" — costs a few lines of code and lets crawlers
and federated query engines (like Comunica) discover what's available.

### 4.6 How they fit together in one graph

```turtle
<kb.ttl>              a dcat:Dataset, void:Dataset ;     # DCAT/VoID: the dump itself
    void:triples      4812 .

<daily-backup.html>   a schema:TechArticle ;             # schema.org: what it is
    dcterms:title     "Daily backup runbook" ;           # DCTERMS: core metadata
    dcterms:creator   <person/tomas-virseda> ;
    dcterms:subject   <concept/tag/backup> .

<person/tomas-virseda> a foaf:Person ;                   # FOAF: the author
    foaf:name         "Tomás Vírseda" .

<concept/tag/backup>  a skos:Concept ;                   # SKOS: the tag as a concept
    skos:prefLabel    "backup"@en ;
    skos:broader      <concept/tag/sysadmin> .
```

Each vocabulary covers one concern, they compose cleanly in a single graph, and
all five are the de-facto standard for their niche — generic RDF tools,
validators, and other people's SPARQL queries understand the data without
custom documentation.

## 5. Suggested phasing

1. **Phase 1:** `url` config key + JSON-LD injection in document pages (no new
   dependencies).
2. **Phase 2:** `semantic.py` service + `rdflib` optional extra → `kb.ttl` /
   `kb.jsonld` dumps with the dcterms/SKOS/FOAF mapping.
3. **Phase 3:** `sparql.html` theme page with Comunica for in-browser querying
   (stays static).
4. **Phase 4:** `kb4it sparql` command wrapping `rdflib-endpoint` for a
   protocol-compliant endpoint.

Each phase is independently shippable; phases 1–3 never violate the
"no runtime" principle in the README. Phase 1+2 together make a well-scoped
first PR.

## 6. References

- Comunica — querying in a browser app:
  <https://comunica.dev/docs/query/getting_started/query_browser_app/>
- Comunica query docs: <https://comunica.dev/docs/query/>
- Comunica on GitHub: <https://github.com/comunica/comunica>
- Comunica browser builds: <http://rdf.js.org/comunica-browser/>
- rdflib: <https://github.com/RDFLib/rdflib>
- rdflib-endpoint: <https://github.com/vemonet/rdflib-endpoint>
  (PyPI: <https://pypi.org/project/rdflib-endpoint/>)
- Apache Jena Fuseki: <https://jena.apache.org/documentation/fuseki2/>
- Oxigraph: <https://github.com/oxigraph/oxigraph>
