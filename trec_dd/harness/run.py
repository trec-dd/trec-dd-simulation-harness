'''trec_dd.harness.run provides an evaluation jig for TREC Dynamic Domain systems

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

'''

## TODO: convert this quick prototype to actually using `yakonfig` and
## `Cmd` so that it takes a -c to our regular config.yaml file that
## tells it how to reach kvlayer to access dossier.label.  When this
## gets published for TREC, we should just provide a kvlayer *file*
## backend.

from __future__ import absolute_imports, print_function
import argparse
import json
import itertools
from hashlib import md5
import logging
import random
from random import random as rand
import time

logger = logging.getLogger(__name__)

class Harness(object):
    def __init__(self, truth_data_path, run_file_path):
        self.truth_data = open(truth_data_path, mode='rb')
        if os.path.exists(run_file_path):
            logger.warn('appending to existing run file at %r', run_file_path)
            self.run_file = open(run_file_path, mode='ab')
        else:
            logger.warn('starting new run file at %r', run_file_path)
            self.run_file = open(run_file_path, mode='wb')

    def start(self, topic_id):
        ## TOOD: check that the topic_id exists in the input data
        return

    def step(self, results):
        ## TODO: make this actually lookup data in dossier.label
        feedback = []
        for stream_id, conf in results:
            subtopics = []
            ## make some random data:
            for i in range(int(rand() * 4)):
                words = ' '.join(['word'] * int(rand() * 10))
                subtopic_id = int(rand() * 6)
                subtopics.append(
                    {"subtopic_id": subtopic_id, 
                     "offset": {
                            "first": int(rand() * 3000), 
                            "length": len(words)
                            }, 
                     "rating": int(rand() * 4), 
                     "string": words})

            ## more random
            on_topic = rand() < 0.4
            res = {"stream_id": stream_id, "on_topic": on_topic, 
                   "confidence": conf, "subtopics": []}
            if on_topic:
                res['subtopics'] = subtopics

            feedback.append(res)

        return feedback

    def stop(self, topic_id):
        ## TODO, more tidying up in the run file?  maybe comments
        self.truth_data.close()
        self.run_file.close()


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('command', help='must be "start", "step", or "stop"')
    parser.add_argument('args', help='input for given command')
    parser.add_argument('--batch-size', type=int, default=5, help='number of results per step')
    parser.add_argument(
        '--one-line', action='store_true', default=False, 
        help='instead of pretty printed JSON, print feedback for each `step` on a single line')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)
    
    if args.command not in set(['start', 'step', 'stop']):
        sys.exit('The only known commands are "start", "step", and "stop".')


    harness = None

    if args.command == 'start':
        parts = args.args.split()
        if len(parts) != 3:
            sys.exit('command="start" requires three input args: ' + \
                     'path/to/truth_data.json, topic_id path/to/run_file.txt, not %r' % args.args)
        truth_data_path, topic_id, run_file_path = parts

        harness = Harness(run_file_path)
        harness.start(topic_id)


    elif args.command = 'stop':
        parts = args.args.split()
        if len(parts) != 1:
            sys.exit('command="stop" requires one input arg: topic_id, not %r' % args.args)
        harness.stop(parts[0])


    elif args.command == 'step':
        if harness is None: 
            sys.exit('must call "start" before "step"')
        
        parts = args.args.split()
        if len(parts) != 2 * args.batch_size:
            sys.exit('command="step" requires twice batch_size (2 x %d = %d) ' + \
                     'input args: stream_id conf stream_id conf ..., not %r' % (
                     args.batch_size, 2 * args.batch_size, args.args))

        pairs = [iter(parts)] * 2
        results = [(stream_id, int(conf))
                   for stream_id, conf in itertools.izip_longest(*pairs):]

        feedback = harness.step(results)
        print(json.dumps(feedback, indent=4, sort_keys=True))
        

if __name__ == '__main__':
    main()
