'''Tools for facilitating communication between a Harness and a System.

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.
'''

from __future__ import absolute_import
import json
import logging
import time

from trec_dd.harness.run import Harness

logger = logging.getLogger(__name__)

class HarnessAmbassador(object):
    '''Facilitates the communication between a Harness and a System.
    '''

    def __init__(self, system, truth_data, run_file_path=None):
        self.system = system
        self.truth_data = truth_data
        self.run_file_path = run_file_path

        self.num_steps = 0

        self.harness = None
        self.curr_topic = None

        self.search_elapsed = 0
        self.feedback_elapsed = 0
        self.process_elapsed = 0
        self.total_start = time.time()

    def start(self, topic_id):
        '''Start harness evaluation on a given topic.
        '''
        logger.info('Starting topic %s' % topic_id)
        self.curr_topic = topic_id
        self.harness = self.make_harness(self.curr_topic)

        result = self.harness.start()
        if not result:
            logger.info('Topic doesn\'t exist: %s' % self.curr_topic)
            return False
        else:
            return True

    def stop(self):
        '''Stop harness evaluation.
        '''
        logger.info('Stopping topic %s' % self.curr_topic)
        self.harness = None
        self.curr_topic = None
        self.num_steps = 0

        total_elapsed = time.time() - self.total_start
        logger.info('%.1f seconds spent so far, %.1f in search, %.1f in '
                    'generating feedback, %.1f in processing feedback',
                    total_elapsed, self.search_elapsed, 
                    self.feedback_elapsed, self.process_elapsed)

    def step(self):
        '''Go through one iteration of harness evaluation.

        This means making a query to the system, getting the results
        communicated from the system, and feeding these results to the
        harness. Then, we take the harness feedback and send it back
        to the system.
        '''
        logger.info('Doing step %d for topic %s' % (self.num_steps, self.curr_topic))

        start_time = time.time()
        results = self.system.search(self.curr_topic)
        self.search_elapsed += time.time() - start_time

        start_time = time.time()
        feedback = self.harness.step(results)
        self.feedback_elapsed += time.time() - start_time

        start_time = time.time()
        self.system.process_feedback(feedback)
        self.process_elapsed += time.time() - start_time

        logger.info(json.dumps(feedback, indent=4, sort_keys=True))
        self.num_steps += 1
        return feedback

    def make_harness(self, topic_id):
        return Harness(topic_id,
                       self.truth_data,
                       self.run_file_path)
