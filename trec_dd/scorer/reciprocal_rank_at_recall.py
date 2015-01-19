'''trec_dd.scorer.reciprocal_rank_at_recall provides a the
   reciprocal rank at full recall score for TREC DD

   This assumes binary relevance, but can be easily upgraded.

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


def reciprocal_rank_at_recall(run, label_store):

    scores_by_topic = dict()

    ## score for each topic
    for topic_id, results in run['results'].items():
        
        ## get all subtopics for the topic
        subtopic_ids = set(get_all_subtopics(label_store, topic_id))

        seen_subtopics = set()


        for idx, result in enumerate(results):
            assert idx == result['rank'] - 1

            # check off seen subtopics

            for subtopic, conf in result['subtopics']:
                seen_subtopics.add(subtopic)

            if len(seen_subtopics) == len(subtopic_ids):
                break
            

        scores_by_topic[topic_id] = 1/(idx + 1) 




    ## macro average over all the topics
    macro_avg = mean(scores_by_topic.values())
    run['scores']['reciprocal_rank_at_recall'] = \
        {'scores_by_topic': scores_by_topic, 'macro_average': macro_avg}