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
from dossier.label import LabelStore
import kvlayer
import logging
import random
import yaml

from trec_dd.harness.run import Harness
from trec_dd.harness.truth_data import parse_truth_data
from trec_dd.system.ambassador import HarnessAmbassador

logger = logging.getLogger(__name__)

class RandomSystem(object):
    '''A ranking system that returns a random document id.
    '''

    def __init__(self, doc_store):
        self.doc_store = doc_store

    def search(self, topic_id):
        '''Select 5 random documents.
        '''
        doc_ids = list(self.doc_store.scan_ids(topic_id))
        rand_docs = random.sample(doc_ids, min(len(doc_ids), 5))
        confidences = [random.random() for _ in xrange(5)]
        return zip(rand_docs, confidences)

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


def main():
    '''Run the random recommender system on a sequence of topics.
    '''
    description = 'Run the random recommender system on a sequence of topics.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('truth_data_path', help='path to truth data.')
    parser.add_argument('run_file_path', help='path to output a run file.')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    kvl_config = {'storage_type': 'local',
                  'namespace': 'test',
                  'app_name': 'test'}
    kvl = kvlayer.client(kvl_config)
    label_store = LabelStore(kvl)

    parse_truth_data(label_store, args.truth_data_path)

    all_topics = set()
    for label in label_store.everything():
        all_topics.add(label.meta['topic_id'])
    topic_sequence = dict([(topic, 5) for topic in all_topics])

    # build a silly document store. This store will just have
    # documents corresponding to the topic ids specified within
    # the topic sequence.
    topic_id_to_doc_ids = defaultdict(list)
    for label in label_store.everything():
        if label.content_id1 in topic_sequence:
            doc_id = label.content_id2
            topic_id = label.content_id1
            topic_id_to_doc_ids[topic_id].append(doc_id)
        elif label.content_id2 in topic_sequence:
            doc_id = label.content_id1
            topic_id = label.content_id2
            topic_id_to_doc_ids[topic_id].append(doc_id)
    doc_store = StubDocumentStore(topic_id_to_doc_ids)

    # Set up the system and ambassador.
    system = RandomSystem(doc_store)
    ambassador = HarnessAmbassador(system, label_store,
                                   run_file_path=args.run_file_path)

    # Run through the topic sequence, controlling the ambassador.
    for topic, num_iterations in topic_sequence.iteritems():
        logger.info('Evaluating topic %s' % topic)
        ambassador.start(topic)
        for _ in xrange(num_iterations):
            ambassador.step()
        logger.info('Stopping topic %s' % topic)
        ambassador.stop()

    logger.info('Finished. Please find run_file at %s' % args.run_file_path)

if __name__ == '__main__':
    main()
