'''trec_dd.harness.run provides an evaluation jig for TREC Dynamic Domain systems

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

'''

from __future__ import absolute_import, print_function

import argparse
from dossier.label import LabelStore, Label, CorefValue
import json
import itertools
import kvlayer
import logging
from random import random as rand
import sys
import time
import yakonfig

logger = logging.getLogger(__name__)


def query_to_topic_id(query):
    return query.replace(' ', '_')


def topic_id_to_query(topic_id):
    return topic_id.replace('_', ' ')


class Harness(object):

    def __init__(self, topic_query, label_store, runfile_path=None):
        self.runfile_path = runfile_path
        self.label_store = label_store
        self.topic_query = topic_query

    config_name = 'harness'

    default_config = {
        'runfile_path': 'runfile.txt',
        'topic': None,
        'batch_size': 5
    }

    # Tell yakonfig that you can replace these at the command
    # line.
    runtime_keys = {
        'topic': 'topic',
        'runfile_path': 'runfile_path',
        'batch_size': 'batch_size'
    }

    @staticmethod
    def add_arguments(parser):
        parser.add_argument('--topic',
                            help='topic on which to work')
        parser.add_argument('--runfile-path', type=str,
                            help='where to write runfile')
        parser.add_argument('--batch_size', type=int,
                            help='number of results per batch')

    def start(self):
        topic_id = query_to_topic_id(self.topic_query)

        # Ping labels table to see if our topic even exists.
        labels = list(self.label_store.directly_connected(topic_id))
        if len(labels) == 0:
            logger.error("Topic doesn't exist: '%s'.", self.topic_query)
            return False

        return True

    def stop(self):
        logger.info("Stopping topic: '%s'", self.topic_query)

    def step(self, results):
        def feedback_for_result(result):
            stream_id, confidence = result
            topic = query_to_topic_id(self.topic_query)
            labels_for_doc = self.label_store.directly_connected(stream_id)
            labels_for_doc = filter(lambda l: l.other(stream_id) == topic,
                                    labels_for_doc)

            def subtopic_from_label(label):
                subtopic_id = label.subtopic_for(stream_id)
                if '|' not in subtopic_id:
                    offset, text = ('', '')
                else:
                    offset, text = subtopic_id.split('|')
                    text = topic_id_to_query(text)
                subtopic = {
                    'subtopic_id': label.subtopic_for(topic),
                    'offset': offset,
                    'text': text,
                    'rating': label.rating
                }
                return subtopic

            subtopics = map(subtopic_from_label, labels_for_doc)

            feedback = {
                'topic_id': self.topic_query.replace(' ', '_'),
                'confidence': confidence,
                'stream_id': stream_id,
                'subtopics': subtopics,
                'on_topic': len(subtopics) > 0
            }

            return feedback

        all_feedback = map(feedback_for_result, results)
        self.write_feedback_to_runfile(all_feedback)
        return all_feedback

    def write_feedback_to_runfile(self, feedback):
        if self.runfile_path is None:
            return

        runfile = open(self.runfile_path, 'a')

        # <topic> <document-id> <on_topic> <subtopic> <rating>
        runfile_line = '{}\t{}\t{}\t{}\t{}\t{}\n'

        for entry in feedback:
            if entry['subtopics']:
                for subtopic in entry['subtopics']:
                    to_write = runfile_line.format(query_to_topic_id(entry['topic_id']),
                                                   entry['stream_id'],
                                                   entry['confidence'],
                                                   entry['on_topic'],
                                                   subtopic['subtopic_id'].replace(' ', '_'),
                                                   subtopic['rating'])
                    runfile.write(to_write)
            else:
                to_write = runfile_line.format(query_to_topic_id(entry['topic_id']),
                                               entry['stream_id'],
                                               entry['confidence'],
                                               entry['on_topic'],
                                               'null',
                                               'null')

                runfile.write(to_write)

        runfile.close()

def main():
    parser = argparse.ArgumentParser(__doc__,
                                     conflict_handler='resolve')
    parser.add_argument('command', help='must be "start", "step", or "stop"')
    parser.add_argument('args', help='input for given command',
                        nargs=argparse.REMAINDER)

    modules = [yakonfig, kvlayer, Harness]
    args = yakonfig.parse_args(parser, modules)

    logging.basicConfig(level=logging.DEBUG)

    if args.command not in set(['start', 'step', 'stop']):
        sys.exit('The only known commands are "start", "step", and "stop".')

    kvl = kvlayer.client()
    label_store = LabelStore(kvl)
    config = yakonfig.get_global_config('harness')
    harness = Harness(config['topic'], config['runfile_path'], label_store)

    if args.command == 'start':
        result = harness.start()

        if result:
            logger.info('Ready for input.')

    elif args.command == 'stop':
        harness.stop()

    elif args.command == 'step':
        parts = args.args
        if len(parts) != 2 * config['batch_size']:
            sys.exit('command="step" requires twice batch_size (2 x %d = %d) '
                     'input args: stream_id conf stream_id conf ..., not %r'
                     % (config['batch_size'], 2 * config['batch_size'], args.args))

        pairs = [iter(parts)] * 2
        results = [(stream_id, int(conf))
                   for stream_id, conf in itertools.izip_longest(*pairs)]

        feedback = harness.step(results)
        print(json.dumps(feedback, indent=4, sort_keys=True))

if __name__ == '__main__':
    main()
