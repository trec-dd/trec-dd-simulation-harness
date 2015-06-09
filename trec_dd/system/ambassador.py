'''Tools for facilitating communication between a Harness and a System.
'''

from __future__ import absolute_import

from trec_dd.harness.run import Harness


class HarnessAmbassador(object):
    '''Facilitates the communication between a Harness and a System.
    '''

    def __init__(self, system, truth_data, runfile_path=None):
        self.system = system
        self.truth_data = truth_data
        self.runfile_path = runfile_path

        self.num_steps = 0

        self.harness = None
        self.curr_topic = None

    def start(self, topic_id):
        '''Start harness evaluation on a given topic.
        '''
        print 'Starting topic %s' % topic_id
        self.curr_topic = topic_id
        self.harness = self.make_harness(self.curr_topic)

        result = self.harness.start()
        if not result:
            print 'Topic doesn\'t exist: %s' % self.curr_topic
            return False
        else:
            return True

    def stop(self):
        '''Stop harness evaluation.
        '''
        print 'Stopping topic %s' % self.curr_topic
        self.harness = None
        self.curr_topic = None
        self.num_steps = 0

    def step(self):
        '''Go through one iteration of harness evaluation.

        This means making a query to the system, getting the results
        communicated from the system, and feeding these results to the
        harness. Then, we take the harness feedback and send it back
        to the system.
        '''
        print 'Doing step %d for topic %s' % (self.num_steps, self.curr_topic)
        results = self.system.search(self.curr_topic)
        feedback = self.harness.step(results)
        self.system.process_feedback(feedback)
        print feedback
        self.num_steps += 1
        return feedback

    def make_harness(self, topic_id):
        return Harness(topic_id,
                       self.truth_data,
                       self.runfile_path)
