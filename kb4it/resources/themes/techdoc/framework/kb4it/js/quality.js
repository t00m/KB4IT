/* techdoc quality: rank sentence and peer-median ticks, from window.KB_QUALITY (quality-index.js). */
(function () {
    'use strict';

    var PLURALS = {
        'How-to guide': 'how-to guides', 'Reference': 'reference documents', 'Explanation': 'explanations',
        'Tutorial': 'tutorials', 'Change': 'changes', 'Incident': 'incidents', 'Task': 'tasks',
        'Meeting': 'meetings', 'Other': 'documents'
    };
    var SINGULARS = {'Reference': 'reference document', 'Other': 'document'};

    function plural(peer) {
        return PLURALS[peer] || (peer.toLowerCase() + 's');
    }

    function singular(peer) {
        return SINGULARS[peer] || peer.toLowerCase();
    }

    function fill() {
        var data = window.KB_QUALITY;
        if (!data || !data.docs || !data.peers) {
            return;
        }
        document.querySelectorAll('.kb-q-rank[data-kb-doc]').forEach(function (el) {
            var doc = data.docs[el.getAttribute('data-kb-doc')];
            var peer = doc && data.peers[doc.peer];
            if (!peer) {
                return;
            }
            if (peer.count === 1) {
                el.textContent = 'The only ' + singular(doc.peer) + ' so far.';
                return;
            }
            var better = Math.round((1 - (doc.rank - 1) / peer.count) * 100);
            el.textContent = 'Rank ' + doc.rank + ' of ' + peer.count + ' ' + plural(doc.peer) +
                ', better than ' + better + '% of them.';
        });
        document.querySelectorAll('.kb-q-rank-note[data-kb-doc]').forEach(function (el) {
            var doc = data.docs[el.getAttribute('data-kb-doc')];
            var peer = doc && data.peers[doc.peer];
            if (peer && peer.count > 1) {
                el.textContent = ': rank ' + doc.rank + ' of ' + peer.count + ' ' + plural(doc.peer);
            }
        });
        var rank = document.querySelector('.kb-q-rank[data-kb-doc]');
        var doc = rank && data.docs[rank.getAttribute('data-kb-doc')];
        var peer = doc && data.peers[doc.peer];
        if (!peer) {
            return;
        }
        // The tick on each bar marks the median of the documents of the same kind.
        var maxima = {findable: 15, structured: 25, complete: 25, connected: 15, current: 20};
        document.querySelectorAll('.kb-q-dim[data-kb-dim]').forEach(function (row) {
            var dim = row.getAttribute('data-kb-dim');
            var tick = row.querySelector('.kb-q-tick');
            var median = peer.median[dim];
            if (!tick || median === undefined) {
                return;
            }
            tick.style.left = Math.min(100, median / maxima[dim] * 100) + '%';
            tick.title = 'Median of ' + plural(doc.peer) + ': ' + median;
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fill);
    } else {
        fill();
    }
})();
