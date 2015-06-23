'''trec_dd.harness.run provides an evaluation jig for TREC Dynamic Domain systems

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.
'''

from __future__ import absolute_import, print_function

import argparse
from collections import defaultdict
from dossier.label import LabelStore, Label, CorefValue
import json
import itertools
import kvlayer
import logging
import os
import sys
import time
import yakonfig

from trec_dd.harness.truth_data import parse_truth_data

logger = logging.getLogger(__name__)


def query_to_topic_id(query):
    return query.replace(' ', '_')


def topic_id_to_query(topic_id):
    return topic_id.replace('_', ' ')


TOPIC_IDS = 'trec_dd_harness_topic_ids'
EXPECTING_STOP = 'trec_dd_harness_expecting_stop'

class Harness(object):

    tables = {
        TOPIC_IDS: (str,),
        EXPECTING_STOP: (str,),
    }

    def __init__(self, config, kvl, label_store):
        self.kvl = kvl
        self.kvl.setup_namespace(self.tables)
        self.label_store = label_store
        self.truth_data_path = config.get('truth_data_path')
        self.run_file_path = config.get('run_file_path')
        self.topic_ids = set(config.get('topic_ids', []))
        self.batch_size = int(config.get('batch_size', 5))

    config_name = 'harness'

    def verify_label_store(self):
        ls = iter(self.label_store.everything())
        try:
            ls.next()
        except StopIteration:
            sys.exit('The label store is empty.  Have you run `trec_dd_harness load`?')
        else:
            return True

    def init(self, topic_ids=None):
        '''Initialize the DB table of topics to apply to the engine under test.
        '''
        self.kvl.clear_table(TOPIC_IDS)
        all_topics = dict()
        for label in self.label_store.everything():
            all_topics[(label.meta['topic_id'],)] = label.meta['topic_name']
        # allow in-process caller to init with topic ids of its choosing
        if topic_ids is not None:
            self.topic_ids = set(topic_ids)
        if self.topic_ids:
            for topic_id in all_topics.keys():
                if topic_id not in self.topic_ids:
                    all_topics.pop(topic_id)
        self.kvl.put(TOPIC_IDS, *all_topics.items())
        return {'num_topics': len(all_topics)}

    def check_expecting_stop(self):
        for (topic_id,), _ in self.kvl.scan(EXPECTING_STOP):
            sys.exit('Harness was expecting you to call stop because you '
                     'submitted fewer than batch_size results.  Fix your '
                     'system and try again.')

    def unset_expecting_stop(self):
        self.kvl.clear_table(EXPECTING_STOP)

    def set_expecting_stop(self, topic_id):
        self.kvl.put(EXPECTING_STOP, ((topic_id,), 'YES'))

    def start(self):
        '''initiates a round of feedback to recommender under evaluation.
        '''
        self.check_expecting_stop()
        self.verify_label_store()
        for (topic_id,), query_string in self.kvl.scan(TOPIC_IDS):
            return {'topic_id': topic_id, 'query': query_string}

        # finished all the topics, so end.
        return {'topic_id': None, 'query': None}

    def stop(self, topic_id):
        '''ends a round of feedback
        '''
        self.unset_expecting_stop()
        for idx, ((_topic_id,), query_string) in enumerate(self.kvl.scan(TOPIC_IDS)):
            if idx == 0:
                if topic_id != _topic_id:
                    sys.exit('%d != %d, which is where the database says we are'
                             % (topic_id, _topic_id))
                self.kvl.delete(TOPIC_IDS, (topic_id,))
                logger.info("Finished with topic: '%s'", topic_id)
        return {'finished': topic_id, 'num_remaining': idx }

    def step(self, topic_id, results):
        '''Generates feedback on one round of recommendations
        '''
        self.check_expecting_stop()
        self.verify_label_store()
        query_string = None
        for (_topic_id,), query_string in self.kvl.scan(TOPIC_IDS):
            break
        if query_string is None:
            sys.exit('got out of sync: topic_id=%r' % topic_id)
        if topic_id != _topic_id:
            sys.exit('%d != %d, which is where the database says we are'
                     % (topic_id, _topic_id))

        if len(results) > 2 * self.batch_size:
            logger.warn('command="step" allows up to twice batch_size (2 x %d = %d) '
                        'input args: stream_id conf stream_id conf ..., not %d = len(%r)',
                        self.batch_size, 2 * self.batch_size, len(results), results)
            return {'error': 'MUST EXIT: submitted too many results'}

        if len(results) < 2 * self.batch_size:
            logger.warn('fewer than the batch size, so automatically calling `stop` '
                        'this query; you must call `start` to move on to the next query.')
            self.set_expecting_stop(topic_id)
    
        pairs = [iter(results)] * 2
        results = [(stream_id, int(conf))
                   for stream_id, conf in itertools.izip_longest(*pairs)]

        # private function for constructing feedback, used in `map` below
        def feedback_for_result(result):            
            stream_id, confidence = result
            if len(stream_id.strip()) == 0:
                sys.exit('Your system submitted a bogus document identifier: %r'
                         % stream_id)
            try:
                assert 0 <= int(confidence) <= 1000
            except:
                sys.exit('Your system submitted a bogus confidence value: %r'
                         % confidence)

            labels_for_doc = self.label_store.directly_connected(stream_id)
            labels_for_doc = filter(lambda l: l.other(stream_id) == topic_id,
                                    labels_for_doc)

            # If any of the labels between the topic_id and
            # the document are negative, we call this document
            # off-topic. If there are no labels between this
            # topic_id and the document, we call this document
            # off-topic. Otherwise, we extract the subtopics
            # from the labels and call the document on-topic.
            if any([label.value == CorefValue.Negative
                    for label in labels_for_doc]):
                subtopic_feedback = []
            else:
                def subtopic_from_label(label):
                    subtopic_id = label.subtopic_for(stream_id)
                    subtopic = {
                        'subtopic_id': label.subtopic_for(topic_id),
                        'subtopic_name': label.meta['subtopic_name'],
                        'passage_text': label.meta['passage_text'],
                        'rating': label.rating,
                    }
                    return subtopic

                subtopic_feedback = [subtopic_from_label(label)
                                     for label in labels_for_doc]

                #subtopic_feedback = []
                #for _, data in subtopic_id_to_data.iteritems():
                #    best = max(data, key=lambda d: d['rating'])
                #    subtopic_feedback.append(best)

            feedback = {
                'topic_id': topic_id,
                'confidence': confidence,
                'stream_id': stream_id,
                'subtopics': subtopic_feedback,
                'on_topic': int(bool(len(subtopic_feedback) > 0))
            }

            return feedback

        all_feedback = map(feedback_for_result, results)
        self.write_feedback_to_run_file(all_feedback)
        return all_feedback


    def write_feedback_to_run_file(self, feedback):
        if self.run_file_path is None:
            return

        # *append* to the run file
        run_file = open(self.run_file_path, 'a')

        for entry in feedback:
            subtopic_stanza = 'NULL'
            if entry['subtopics']:
                subtopic_tuples = []
                for subtopic in entry['subtopics']:
                    subtopic_tuple = ':'.join([subtopic['subtopic_id'],
                                               str(subtopic['rating'])])
                    subtopic_tuples.append(subtopic_tuple)
                subtopic_stanza = '|'.join(subtopic_tuples)

            # <topic> <document-id> <confidence> <on_topic> <subtopic data>
            run_file_line = ('%(topic_id)s\t%(stream_id)s\t%(confidence).6f'
                             '\t%(on_topic)d\t%(subtopic_stanza)s\n')
            output_dict = {'subtopic_stanza': subtopic_stanza,
                           'topic_id': entry['topic_id'],
                           'stream_id': entry['stream_id'],
                           'confidence': entry['confidence'],
                           'on_topic': entry['on_topic'],
                           }
            to_write = run_file_line % output_dict

            assert len(run_file_line.split()) == 5

            run_file.write(to_write)

        run_file.close()

usage = '''The purpose of this harness is to interact with your TREC DD system
by issuing queries to your system, and providing feedback (truth data)
for the results produced by your system.  While it does this, it keeps
track of the results produced by your system in a `run file`.  After
generating a run file with this harness, you can score the run using
trec_dd_scorer

The harness is run via  three commands: start, step, stop.  Typically,
a system will invoke start, then  invoke step multiple times, and then
invoke stop.   Every invocation  must include the  -c argument  with a
path   to    a   valid    config.yaml   file,   as    illustrated   in
example/config.yaml.  For  efficiency, the first  time you run  with a
new configuration,  the truth data  must be loaded into  your database
using the `load` command.  

By default, when you score a system using the harness, all of the
topics are applied to the system in an order selected by the harness.
You can limit the topic_ids that are used by specifying the topic_ids
property in the config.yaml

The harness keeps track of the topic_ids that have not yet been used
in building your system's run file.  To reset this state, you must run
the `init` command.

To progress through the topics, your system must execute this double
while loop, which is exactly what is implemented in the
trec_dd/system/ambassador_cli.py example:

        `init`
        while 1:
            topic_id <-- `start`
            if topic_id is None: break
            while 1:
                results <-- run your system
                feedback <-- `step(results)`
                if feedback is None or len(feedback) < batch_size:
                    break
                else:
                    your system processes the feedback
            `stop`

Each of the five commands returns a JSON dictionary which your system
can read using a JSON library.  The harness always provides feedback
for every result, even if the feedback is that the system has no truth
data for that result.  Note that your use of the harness *must* call
`stop` in the next iteration after any step in which you submit fewer
than batch_size results.  If you fail to do this, the harness will
exit.

See trec_dd/system/ambassador_cli.py for an example of using the
harness from python.

'''

def main():
    parser = argparse.ArgumentParser(
        'Command line interface to the office TREC DD jig.',
        usage=usage,
        conflict_handler='resolve')
    parser.add_argument('command', help='must be "load", "init", "start", "step", or "stop"')
    parser.add_argument('args', help='input for given command',
                        nargs=argparse.REMAINDER)
    modules = [yakonfig, kvlayer, Harness]
    args = yakonfig.parse_args(parser, modules)

    logging.basicConfig(level=logging.DEBUG)

    if args.command not in set(['load', 'init', 'start', 'step', 'stop']):
        sys.exit('The only valid commands are "load", "init", "start", "step", and "stop".')

    kvl = kvlayer.client()
    label_store = LabelStore(kvl)
    config = yakonfig.get_global_config('harness')
    harness = Harness(config, kvl, label_store)

    if args.command == 'load':
        if not config.get('truth_data_path'):
            sys.exit('Must provide --truth-data-path as an argument')
        if not os.path.exists(config['truth_data_path']):
            sys.exit('%r does not exist' % config['truth_data_path'])
        parse_truth_data(label_store, config['truth_data_path'])
        logger.info('Done!  The truth data was loaded into this '
                     'kvlayer backend:\n%s',
                    json.dumps(yakonfig.get_global_config('kvlayer'),
                               indent=4, sort_keys=True))

    elif args.command == 'init':
        response = harness.init()
        print(json.dumps(response))

    elif args.command == 'start':
        response = harness.start()
        print(json.dumps(response))

    elif args.command == 'stop':
        response = harness.stop(args.args[0])
        print(json.dumps(response))

    elif args.command == 'step':
        parts = args.args
        topic_id = parts.pop(0)
        feedback = harness.step(topic_id, parts)
        print(json.dumps(feedback))

if __name__ == '__main__':
    main()
