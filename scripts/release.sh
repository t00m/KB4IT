#!/usr/bin/env bash
#
# Prepare a KB4IT release: set the version, date the changelog, draft the
# release notes, check everything, and commit. It never tags and never
# pushes: master only takes pull requests, so the tag goes on the merge
# commit, by hand. See RELEASING.md.
#
# Usage:
#   scripts/release.sh [X.Y.Z|major|minor|patch] [--date YYYY-MM-DD] [--dry-run]
#   scripts/release.sh [X.Y.Z|...] --commit [--allow-dirty]
#   scripts/release.sh --open X.Y.Z          start the next cycle (target version)
#
# Without a version it releases the one in kb4it/VERSION, which names the
# release being built. A plain run writes files and stops so the release
# notes can be written; --commit checks everything again and commits.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

log()  { echo "[release] $*"; }
die()  { echo "[release] ERROR: $*" >&2; exit 1; }

TARGET=""
DATE="$(date '+%Y-%m-%d')"
DRY_RUN=0
DO_COMMIT=0
ALLOW_DIRTY=0
OPEN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --date)        DATE="${2:-}"; shift 2 ;;
        --dry-run)     DRY_RUN=1; shift ;;
        --commit)      DO_COMMIT=1; shift ;;
        --allow-dirty) ALLOW_DIRTY=1; shift ;;
        --open)        OPEN="${2:-}"; shift 2 ;;
        -h|--help)     sed -n '2,17p' "$0"; exit 0 ;;
        -*)            die "unknown option $1" ;;
        *)             TARGET="$1"; shift ;;
    esac
done

CURRENT="$(tr -d '[:space:]' < kb4it/VERSION)"
[[ "$CURRENT" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "kb4it/VERSION is '$CURRENT', not X.Y.Z"
[[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || die "--date must be YYYY-MM-DD"

bump() {
    local major minor patch
    IFS=. read -r major minor patch <<< "$CURRENT"
    case "$1" in
        major) echo "$((major + 1)).0.0" ;;
        minor) echo "${major}.$((minor + 1)).0" ;;
        patch) echo "${major}.${minor}.$((patch + 1))" ;;
        *)     echo "$1" ;;
    esac
}

set_version() {
    printf '%s' "$1" > kb4it/VERSION
    sed -i -E "s/^version = \"[^\"]*\"$/version = \"$1\"/" pyproject.toml
}

tree_is_clean() { [[ -z "$(git status --porcelain --untracked-files=no)" ]]; }

# Start the next cycle: the version names the release being built.
if [[ -n "$OPEN" ]]; then
    [[ "$OPEN" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "--open needs X.Y.Z"
    tree_is_clean || die "the working tree has uncommitted changes"
    log "target version $CURRENT -> $OPEN"
    [[ $DRY_RUN -eq 1 ]] && exit 0
    set_version "$OPEN"
    git add kb4it/VERSION pyproject.toml
    git commit -q -m "chore: target version $OPEN" || die "commit failed"
    log "committed: chore: target version $OPEN"
    exit 0
fi

VERSION="$(bump "${TARGET:-$CURRENT}")"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "'$VERSION' is not X.Y.Z"
TAG="v$VERSION"
NOTES="releases/$VERSION.md"

# Guards that apply before anything is written.
FAILED=0
guard() { if eval "$2"; then log "ok    $1"; else log "FAIL  $1"; FAILED=1; fi; }

log "release $VERSION (kb4it/VERSION is $CURRENT), date $DATE"
if [[ $ALLOW_DIRTY -eq 0 && $DO_COMMIT -eq 0 ]]; then
    guard "working tree is clean" tree_is_clean
fi
guard "tag $TAG does not exist locally" "! git rev-parse -q --verify refs/tags/$TAG >/dev/null"
guard "tag $TAG does not exist on origin" "! git ls-remote --exit-code --tags origin refs/tags/$TAG >/dev/null 2>&1"
guard "CHANGELOG.md has a [$VERSION] section or a non-empty [Unreleased]" \
    "grep -q '^## \[$VERSION\]' CHANGELOG.md || python3 scripts/devel/changelog.py has-unreleased"

if [[ $DRY_RUN -eq 1 ]]; then
    [[ -f "$NOTES" ]] && log "notes $NOTES exist" || log "notes $NOTES would be drafted"
    [[ $FAILED -eq 0 ]] && log "dry run: nothing written" || log "dry run: fix the failures above first"
    exit $FAILED
fi
[[ $FAILED -eq 0 ]] || die "guards failed, nothing written"

# Write the version, date the changelog, draft the notes. Safe to run twice.
set_version "$VERSION"
python3 scripts/devel/changelog.py release "$VERSION" "$DATE" || die "could not update CHANGELOG.md"
if [[ ! -f "$NOTES" ]]; then
    mkdir -p releases
    python3 scripts/devel/changelog.py notes "$VERSION" > "$NOTES" || die "could not draft $NOTES"
    log "drafted $NOTES: write it, then delete its TODO line"
fi

if [[ $DO_COMMIT -eq 0 ]]; then
    log "files written. Edit $NOTES, then run: scripts/release.sh $VERSION --commit"
    exit 0
fi

# Everything below must pass before the release commit exists.
log "checking"
FAILED=0
guard "only release files are modified" \
    "[[ -z \"\$(git status --porcelain --untracked-files=no -- . ':!kb4it/VERSION' ':!pyproject.toml' ':!CHANGELOG.md')\" ]]"
guard "release notes have no TODO line" "! grep -q 'TODO' '$NOTES'"
guard "CHANGELOG.md has a dated [$VERSION] section" "grep -q '^## \[$VERSION\] - $DATE' CHANGELOG.md || grep -q '^## \[$VERSION\] - ' CHANGELOG.md"
guard "kb4it/VERSION and pyproject.toml agree" "grep -q '^version = \"$VERSION\"$' pyproject.toml && [[ \"\$(cat kb4it/VERSION)\" == '$VERSION' ]]"
guard "tests pass" "./scripts/devel/test.sh -q >/tmp/kb4it-release-tests.log 2>&1"
guard "every tracked theme is compliant" "./scripts/devel/check_themes.sh --worktree >/tmp/kb4it-release-themes.log 2>&1"
guard "the wheel holds every tracked theme" "rm -rf dist && uv build --wheel >/dev/null 2>&1 && python3 scripts/devel/check_wheel_themes.py >/dev/null"
[[ $FAILED -eq 0 ]] || die "checks failed, nothing committed (logs in /tmp/kb4it-release-*.log)"

git add kb4it/VERSION pyproject.toml CHANGELOG.md "$NOTES"
git commit -q -m "chore(release): $VERSION" || die "commit failed"
log "committed: chore(release): $VERSION"
cat <<EOF
[release] next steps (yours):
  1. push this branch and open a pull request to master
  2. after the merge:  git checkout master && git pull --ff-only
  3. tag the merge:    git tag $TAG && git push origin $TAG
     The publish workflow then checks the tag, publishes to PyPI and creates
     the GitHub release from $NOTES.
  4. start the next cycle:  scripts/release.sh --open <next version>
EOF
