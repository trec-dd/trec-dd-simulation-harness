'''evaluation jig for TREC Dynamic Domain systems

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

'''

from __future__ import absolute_import, print_function, division

import argparse
from dossier.label import LabelStore
from collections import defaultdict
import json
import kvlayer
import logging
import os
import sys
import yakonfig

from trec_dd.scorer import available_scorers


logger = logging.getLogger(__name__)


def load_run(run_file_path):
    '''factory function that loads a run file into memory, checking its
validity, and returning a dictionary keyed on topic_id with values
that are dictionaries of

    topic_id, stream_id, confidence, on_topic, subtopics

where subtopics is a pipe-delimited list of colon-delimited two-tuples
of (subtopic_id, rating)

    '''
    fh = open(run_file_path)
    results_by_topic = dict(scores=defaultdict(dict), results=defaultdict(list))
    prev_team_id = None
    prev_system_id = None
    prev_batch_num = None
    prev_topic_id = None
    seen_topic_ids = set()
    rank = 1
    for line in fh:
        if line.startswith('#'): continue
        parts = line.split()
        if len(parts) != 5:
            sys.exit('Your run file is invalid, because line '
                     '%d has %d parts instead of 5' 
                     % (line_idx, len(parts)))

        topic_id, stream_id, confidence, on_topic, subtopics_and_ratings = parts
        on_topic = bool(int(on_topic))
        confidence = float(confidence)

        if prev_topic_id is None: prev_topic_id = topic_id
        if prev_topic_id != topic_id:
            ## switching to a new topic!!!
            if topic_id in seen_topic_ids:
                sys.exit('run file returns to a previously finished topic!\n%r' % line)
            else:
                rank = 1
                seen_topic_ids.add(topic_id)
                prev_topic_id = topic_id
                assert rank == 1, line
                prev_batch_num = None

        subtopics = []
        if subtopics_and_ratings == 'NULL':
            assert on_topic is False, (line, subtopics_and_ratings)

        else:
            for rec in subtopics_and_ratings.split('|'):
                subtopic_id, rating = rec.split(':')
                subtopics.append((subtopic_id, int(rating)))

        results_by_topic['results'][topic_id].append(dict(
                rank=rank,
                stream_id=stream_id, confidence=confidence, on_topic=on_topic,
                subtopics=subtopics,
                ))
        rank += 1

    return results_by_topic


row = '%(macro_average).3f\t%(scorer_name)s'
def format_scores(run):
    parts = []
    for scorer_name, rec in sorted(run['scores'].items()):
        _rec = dict(scorer_name=scorer_name)
        _rec.update(rec)
        parts.append(row % _rec)
    return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(__doc__,
                                     conflict_handler='resolve')
    parser.add_argument('run_file_path', help='path to run file to score.')
    parser.add_argument('scored_run_file_output_path',
                        help='path to file to create with scores inserted'
                        'into run file.')
    parser.add_argument('--overwrite', action='store_true', default=False,
                        help='overwrite any existing run file.')
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='display verbose log messages.')
    parser.add_argument('--scorer', action='append', default=[],
        dest='scorers', help='names of scorer functions to run;'
                        ' if none are provided, it runs all of them')

    modules = [yakonfig, kvlayer]
    args = yakonfig.parse_args(parser, modules)

    if os.path.exists(args.scored_run_file_output_path):
        if args.overwrite:
            os.remove(args.scored_run_file_output_path)
        else:
            sys.exit('%r already exists' % args.scored_run_file_output_path)

    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)

    kvl = kvlayer.client()
    label_store = LabelStore(kvl)

    run = load_run(args.run_file_path)

    if len(args.scorers) == 0:
        args.scorers = available_scorers.keys()

    for scorer_name in args.scorers:
        scorer = available_scorers.get(scorer_name)
        logger.info('running %s', scorer_name)
        # this modifies the run['scores'] object itself
        scorer(run, label_store)

    print(format_scores(run))

    open(args.scored_run_file_output_path, 'wb').\
        write(json.dumps(run, indent=4))


if __name__ == '__main__':
    main()
