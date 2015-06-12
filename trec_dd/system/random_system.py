'''Demonstrate generating a run_file using a random system.

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

This file sets up a very silly system for evaluation. All the system
does when given a query is return a collection of random document ids
from a set of known document ids.

We feed this system into a HarnessAmbassador, which orchestrates the
communication between the Harness and the system being
evaluated. Because our random system is in python, we can use the
Harness's python interface for simplicity.
'''
from __future__ import absolute_import
import argparse
from collections import defaultdict
from itertools import chain
import logging
import os
import random
import sys
import yaml

from dossier.label import LabelStore
import kvlayer
import yakonfig

from trec_dd.harness.run import Harness
from trec_dd.harness.truth_data import parse_truth_data
from trec_dd.system.ambassador_cli import HarnessAmbassadorCLI

logger = logging.getLogger(__name__)

class RandomSystem(object):
    '''A ranking system that returns a random document id.
    '''

    def __init__(self, doc_store):
        self.doc_store = doc_store

    def search(self, query, page_number):
        '''Select 5 random documents.
        '''
        if page_number >= 5: return []
        doc_ids = list(self.doc_store.scan_ids(query))
        rand_docs = random.sample(doc_ids, min(len(doc_ids), 5))
        confidences = [str(int(1000 * random.random())) for _ in xrange(5)]
        results = list(chain(*zip(rand_docs, confidences)))
        assert len(results) % 2 == 0, results
        return results

    def process_feedback(self, feedback):
        '''Ignore the feedback from the harness.
        '''
        pass


class StubDocumentStore(object):
    '''Trivial document store.

    Allows for one to just iterate over a predefined set
    of document ids stored in memory.
    '''

    def __init__(self, topic_id_to_doc_ids):
        self.topic_id_to_doc_ids = topic_id_to_doc_ids

    def scan_ids(self, topic_id):
        '''Just iterate over doc ids in memory.
        '''
        for doc_id in self.topic_id_to_doc_ids[topic_id]:
            yield doc_id

def make_doc_store(label_store):

    all_topics = set()
    for label in label_store.everything():
        all_topics.add(str(label.meta['topic_id']))

    # build a silly document store. This store will just have
    # documents corresponding to the topic ids specified within
    # the topic sequence.
    topic_id_to_doc_ids = defaultdict(list)
    for label in label_store.everything():
        if label.content_id1 in all_topics:
            doc_id = label.content_id2
            if not doc_id.strip(): 
                logger.warn('skipping bogus document identifer: %r' % doc_id)
                continue
            topic_id = label.content_id1
            query = label.meta['topic_name']
            topic_id_to_doc_ids[query].append(doc_id)
        elif label.content_id2 in all_topics:
            doc_id = label.content_id1
            if not doc_id.strip(): 
                logger.warn('skipping bogus document identifer: %r' % doc_id)
                continue
            topic_id = label.content_id2
            query = label.meta['topic_name']
            topic_id_to_doc_ids[query].append(doc_id)
    doc_store = StubDocumentStore(topic_id_to_doc_ids)
    return doc_store

def main():
    '''Run the random recommender system on a sequence of topics.
    '''
    description = ('A baseline recommender system that uses the truth data to'
                   ' create output that has perfect recall and would also have'
                   ' perfect precision if you ignore subtopic diversity/novelty.'
                   ' This generates output directly from the truth data and'
                   ' randomly shuffles the truth data per topic, so that'
                   ' the ordering of passages does not attempt to optimize any'
                   ' particular quality metric.')
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--overwrite', action='store_true')
    args = yakonfig.parse_args(parser, [yakonfig])

    logging.basicConfig(level=logging.DEBUG)

    config = yakonfig.get_global_config('harness')
    batch_size = config.get('batch_size', 5)
    run_file_path = config['run_file_path']
    if os.path.exists(run_file_path):
        if args.overwrite:
            os.remove(run_file_path)
        else:
            sys.exit('%r already exists' % run_file_path)

    kvl_config = {'storage_type': 'local',
                  'namespace': 'test',
                  'app_name': 'test'}
    kvl = kvlayer.client(kvl_config)
    label_store = LabelStore(kvl)

    parse_truth_data(label_store, config['truth_data_path'])

    # Set up the system
    doc_store = make_doc_store(label_store)
    system = RandomSystem(doc_store)
    ambassador = HarnessAmbassadorCLI(system, args.config, batch_size)
    ambassador.run()


if __name__ == '__main__':
    main()
