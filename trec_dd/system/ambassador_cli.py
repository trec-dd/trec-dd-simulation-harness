'''Tools for facilitating communication between a Harness and a System.

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.
'''

from __future__ import absolute_import
import json
import logging
import time
import subprocess
import sys

logger = logging.getLogger(__name__)

class HarnessAmbassadorCLI(object):
    '''Facilitates the communication between a Harness and a System using
    the command line.

    '''

    def __init__(self, system, config_file_path, batch_size=5):
        self.system = system
        self.config_file_path = config_file_path
        self.batch_size = batch_size

        self.num_topics = 0
        self.num_steps = 0
        self.topic_id = None
        self.query = None
        self.search_elapsed = 0
        self.feedback_elapsed = 0
        self.process_elapsed = 0
        self.total_start = time.time()

    @staticmethod
    def run_command(cmd):
        p = subprocess.Popen(cmd,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE,
        )
        out, err = p.communicate(0)
        if p.returncode != 0:
            raise Exception(err)
        try:
            return json.loads(out)
        except:
            logger.critical('failed to get JSON: %r', out, exc_info=True)
            logger.critical(err)
            sys.exit(err)

    def init_harness(self):
        out = self.run_command(['trec_dd_harness', '-c', 
                                self.config_file_path, 'init'])
        assert 'num_topics' in out, out

    def start(self):
        '''Start harness evaluation on a given topic.
        '''
        out = self.run_command(['trec_dd_harness', '-c', 
                          self.config_file_path, 'start'])
        assert 'topic_id' in out, out
        assert 'query' in out, out
        self.topic_id = out['topic_id']
        self.query = out['query']

        if self.topic_id is None:
            logger.info('We have finished %d topics', self.num_topics)
        else:
            self.num_topics += 1
            logger.info('Starting topic %s' % self.topic_id)

    def stop(self, out=None):
        '''Stop harness evaluation.
        '''
        logger.info('Stopping topic %s: %r', self.topic_id, self.query)
        if out is None:
            out = self.run_command(['trec_dd_harness', '-c', 
                                    self.config_file_path, 'stop', self.topic_id])

        assert 'finished' in out, out
        assert 'num_remaining' in out, out
        self.topic_id = None
        self.query = None
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
        self.num_steps += 1
        logger.info('Doing step %d for topic %s: %r',
                    self.num_steps, self.query, self.topic_id)

        start_time = time.time()
        results = self.system.search(self.query, self.num_steps)
        self.search_elapsed += time.time() - start_time

        logger.info('got %d results for %r page %d', 
                    len(results), self.query, self.num_steps)
        if not results:
            # signal to run loop that we are done with this topic
            return

        assert len(results) % 2 == 0
        # expect [str, int, str, int, ... up to batch_size pairs]

        cmd = ['trec_dd_harness', '-c', 
               self.config_file_path, 'step', self.topic_id]
        cmd += results
        feedback = self.run_command(cmd)
        assert isinstance(feedback, list), feedback

        start_time = time.time()
        self.system.process_feedback(feedback)
        self.process_elapsed += time.time() - start_time

        logger.info(json.dumps(feedback, indent=4, sort_keys=True))
        return feedback

    def run(self):
        self.init_harness()
        while 1:
            self.start()
            if self.topic_id is None: break
            while 1:
                feedback = self.step()
                if feedback is None or len(feedback) < self.batch_size: break
            self.stop()
        logger.info('finished run loop')
