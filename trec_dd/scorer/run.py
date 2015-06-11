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
import sys
import yakonfig

from trec_dd.harness.truth_data import parse_truth_data
from trec_dd.scorer import available_scorers


logger = logging.getLogger(__name__)


def load_run(run_file_path):
    '''factory function that loads a run file into memory, checking its
validity, and returning a dictionary keyed on topic_id with values
that are dictionaries of

    batch_num, rank, stream_id, confidence, on_topic, subtopics

where subtopics is a list of two-tuples of (subtopic_id, rating)

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
        if len(parts) == 4:
            parts.append('')
        topic_id, stream_id, confidence, on_topic, subtopics_and_ratings = parts
        on_topic = on_topic == 'True'
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
        if not subtopics_and_ratings:
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


def main():
    parser = argparse.ArgumentParser(__doc__,
                                     conflict_handler='resolve')
    parser.add_argument('truth_data_path', help='path to truthdata.')
    parser.add_argument('run_file_path', help='path to run file to score.')
    parser.add_argument('--verbose', action='store_true', default=False,
                        help='display verbose log messages.')
    parser.add_argument('--scorer', action='append', default=[],
        dest='scorers', help='names of scorer functions')

    modules = [yakonfig]
    args = yakonfig.parse_args(parser, modules)

    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)

    config = {'storage_type': 'local',
              'namespace': 'test',
              'app_name': 'test'}
    kvl = kvlayer.client(config)
    label_store = LabelStore(kvl)

    parse_truth_data(label_store, args.truth_data_path)

    run = load_run(args.run_file_path)

    for scorer_name in args.scorers:
        scorer = available_scorers.get(scorer_name)
        scorer(run, label_store)

    print(json.dumps(run, indent=4))


if __name__ == '__main__':
    main()
