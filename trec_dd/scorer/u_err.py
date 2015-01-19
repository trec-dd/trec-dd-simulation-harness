'''trec_dd.scorer.u_err provides a u-ERR scorer for TREC DD

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

'''

from __future__ import division
from operator import attrgetter

#from numpy import mean

from trec_dd.utils import get_all_subtopics

def mean(l):
    s = sum(l)
    return s / len(l)


def u_err(run, label_store):
    scores_by_topic = dict()
    for topic_id, results in run['results'].items():
        #subtopic_ids = map(attrgetter('subtopic_id'), 
        #                   get_all_subtopics(label_store, topic_id))
        subtopic_ids = set(get_all_subtopics(label_store, topic_id))
        scores_by_topic[topic_id] = len(results) / len(subtopic_ids)        

    macro_avg = mean(scores_by_topic.values())
    run['scores']['u_err'] = {'scores_by_topic': scores_by_topic, 'macro_average': macro_avg}

