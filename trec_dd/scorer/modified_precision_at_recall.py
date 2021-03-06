'''trec_dd.scorer.modified_precision_at_recall provides the
   precision at full recall score for TREC DD, where in this 
   case a document is counted towards precision in terms of
   the fraction of new subtopics (out of total subtopics) 
   it provides. This may or may not be a good idea.

   This assumes binary relevance, but can be easily upgraded.

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

'''

from __future__ import division
from operator import attrgetter

#from numpy import mean

from trec_dd.utils import get_all_subtopics, get_best_subtopics

def mean(l):
    if len(l) == 0:
        return 0.0

    s = sum(l)
    return s / len(l)


def modified_precision_at_recall(run, label_store):

    scores_by_topic = dict()

    ## score for each topic
    for topic_id, results in run['results'].items():
        ## get all subtopics for the topic
        subtopic_ids = set(get_all_subtopics(label_store, topic_id))

        seen_subtopics = set()
        relevant_docs = 0

        for idx, result in enumerate(results):
            assert idx == result['rank'] - 1

            result_subtopics = \
                {subtopic for subtopic, conf in get_best_subtopics(result['subtopics'])}


            if len(result_subtopics) > 0:
                frac = len(result_subtopics.difference(seen_subtopics)) \
                        / len(result_subtopics) 
            else:
                frac = 0

            relevant_docs += frac

            seen_subtopics.update(result_subtopics)
            if len(seen_subtopics) == len(subtopic_ids):
                break
        ## precision is number of documents relevant at stopping point
        p = relevant_docs/(idx + 1)
        scores_by_topic[topic_id] = p

    ## macro average over all the topics
    macro_avg = mean(scores_by_topic.values())
    run['scores']['modified_precision_at_recall'] = \
        {'scores_by_topic': scores_by_topic, 'macro_average': macro_avg}
