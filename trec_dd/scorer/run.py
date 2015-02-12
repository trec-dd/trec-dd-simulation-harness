'''trec_dd.harness.run provides an evaluation jig for TREC Dynamic Domain systems

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

'''

from __future__ import absolute_import, print_function, division

import argparse
from collections import defaultdict
import json
import kvlayer
import logging
import sys
import yakonfig

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
    prev_rank = None
    prev_topic_id = None
    seen_topic_ids = set()
    for line in fh:
        if line.startswith('#'): continue
        parts = line.split()
        if len(parts) == 8:
            parts.append('')
        assert len(parts) == 9, (len(parts), parts, line)
        team_id, system_id, batch_num, rank, topic_id, stream_id, \
                                    confidence, on_topic, subtopics_and_ratings = parts
        assert on_topic in set(['false', 'true']), line
        on_topic = json.loads(on_topic)
        confidence = int(confidence)
        batch_num = int(batch_num)
        rank = int(rank)
        if prev_team_id is None: prev_team_id = team_id
        assert prev_team_id == team_id, line
        if prev_system_id is None: prev_system_id = system_id
        assert prev_system_id == system_id
        if prev_topic_id is None: prev_topic_id = topic_id
        if prev_topic_id != topic_id:
            ## switching to a new topic!!!
            if topic_id in seen_topic_ids:
                sys.exit('run file returns to a previously finished topic!\n%r' % line)
            else:
                seen_topic_ids.add(topic_id)
                assert batch_num == 1, line
                assert rank == 1, line
                prev_batch_num = None
                prev_rank = None

        if prev_batch_num is None:
            prev_batch_num = batch_num
        else:
            assert batch_num in set([prev_batch_num, prev_batch_num + 1]), \
                (batch_num, prev_batch_num, line)
            prev_batch_num = batch_num

        if prev_rank is None:
            prev_rank = rank
        else:
            assert rank == prev_rank + 1, (rank, prev_rank, line)
            prev_rank = rank


        subtopics = []
        if not subtopics_and_ratings:
            assert on_topic is False, (line, subtopics_and_ratings)

        else:
            for rec in subtopics_and_ratings.split('|'):
                subtopic_id, rating = rec.split(':')
                subtopics.append((subtopic_id, int(rating)))

        results_by_topic['results'][topic_id].append(dict(
                batch_num=batch_num, rank=rank,
                stream_id=stream_id, confidence=confidence, on_topic=on_topic,
                subtopics=subtopics,
                ))

    return results_by_topic


def main():
    parser = argparse.ArgumentParser(__doc__,
                                     conflict_handler='resolve')
    parser.add_argument('run')
    parser.add_argument('--scorer', action='append', default=[],
        dest='scorers', help='names of scorer functions')

    modules = [yakonfig, kvlayer]
    args = yakonfig.parse_args(parser, modules)

    logging.basicConfig(level=logging.DEBUG)

    kvl = kvlayer.client()
    label_store = LabelStore(kvl)
    # config = yakonfig.get_global_config('')

    run = load_run(args.run)

    for scorer_name in args.scorers:
        scorer = available_scorers.get(scorer_name)
        scorer(run, label_store)

    print(json.dumps(run, indent=4))


if __name__ == '__main__':
    main()
