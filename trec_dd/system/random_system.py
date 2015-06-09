'''Demonstrate generating a runfile using a random system.

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
from dossier.label import LabelStore
import kvlayer
import random
import yaml

from trec_dd.harness.run import Harness
from trec_dd.system.ambassador import HarnessAmbassador


class RandomSystem(object):
    '''A ranking system that returns a random document id.
    '''

    def __init__(self, doc_store):
        self.doc_store = doc_store

    def search(self, topic_id):
        '''Select 5 random documents.
        '''
        doc_ids = list(self.doc_store.scan_ids())
        rand_docs = random.sample(doc_ids, 5)
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

    def __init__(self, doc_ids):
        self.doc_ids = doc_ids

    def scan_ids(self):
        '''Just iterate over doc ids in memory.
        '''
        for doc_id in self.doc_ids:
            yield doc_id


def main():
    '''Run the random recommender system on a sequence of topics.
    '''
    description = 'Run the random recommender system on a sequence of topics.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('topic_sequence',
                        help='path to file describing which topics to evaluate.')
    parser.add_argument('truth_data', help='path to truth data.')
    parser.add_argument('runfile_path', help='path to output runfile.')
    args = parser.parse_args()

    kvl_config = {'storage_type': 'filestorage',
                  'filename': args.truth_data,
                  'namespace': 'test',
                  'app_name': 'test'}
    kvl = kvlayer.client(kvl_config)
    label_store = LabelStore(kvl)

    topic_sequence = yaml.load(open(args.topic_sequence))

    # build a silly document store. This store will just have
    # documents corresponding to the topic ids specified within
    # the topic sequence.
    doc_ids = []
    for label in label_store.everything():
        if label.content_id1 in topic_sequence:
            doc_id = label.content_id2
            doc_ids.append(doc_id)
        elif label.content_id2 in topic_sequence:
            doc_id = label.content_id1
            doc_ids.append(doc_id)
    doc_store = StubDocumentStore(doc_ids)

    # Set up the system and ambassador.
    system = RandomSystem(doc_store)
    ambassador = HarnessAmbassador(system, label_store,
                                   runfile_path=args.runfile_path)

    # Run through the topic sequence, controlling the ambassador.
    for topic, num_iterations in topic_sequence.iteritems():
        print 'Evaluating topic %s' % topic
        ambassador.start(topic)
        for _ in xrange(num_iterations):
            ambassador.step()
        print 'Stopping topic %s' % topic
        ambassador.stop()

    print 'Finished. Please find runfile at %s' % args.runfile_path

if __name__ == '__main__':
    main()
