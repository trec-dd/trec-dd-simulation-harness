'''trec_dd.scorer.average_err provides the
   err score for each subtopic and then takes their mean.

   This requires graded relevance.

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

'''

from __future__ import division
from operator import attrgetter
from collections import defaultdict

#from numpy import mean

from trec_dd.utils import get_all_subtopics

def mean(l):
    s = sum(l)
    return s / len(l)


def average_err(run, label_store):

    scores_by_topic = dict()

    ## score for each topic
    for topic_id, results in run['results'].items():
        
        ## get all subtopics for the topic
        subtopic_ids = list(set(get_all_subtopics(label_store, topic_id)))

        # for each subtopic, compute a running stopping_p
        # and score
        p_continue = defaultdict(lambda: 1)
        score = defaultdict(float)

        for idx, result in enumerate(results):
            assert idx == result['rank'] - 1

            for subtopic, conf in result['subtopics']:
                rel = (2**conf - 1)/2**4 ## magic formula for relevance

                p_stop_here = p_continue[subtopic]*rel
                score[subtopic] += p_stop_here/(idx+1)

                ## update stopping probabilities
                p_continue[subtopic] *= (1-rel)

        print score

            
        ## precision is number of documents relevant at stopping point

        scores_by_topic[topic_id] = mean(score.values())




    ## macro average over all the topics
    macro_avg = mean(scores_by_topic.values())
    run['scores']['average_err'] = \
        {'scores_by_topic': scores_by_topic, 'macro_average': macro_avg}