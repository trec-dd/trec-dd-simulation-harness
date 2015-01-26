'''trec_dd.scorer.cube_test provides the
   cube test for each subtopic and then takes their mean.

   http://dl.acm.org/citation.cfm?id=2523648
   https://github.com/trec-dd/trec-dd-metrics/tree/master/cube-test

   This requires graded relevance.

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

'''
from __future__ import division
import sys
from operator import attrgetter
from collections import defaultdict

#from numpy import mean

from trec_dd.utils import get_all_subtopics

def mean(l):
    s = sum(l)
    return s / len(l)

def cube_test(run, label_store):
    '''
    iterate over topics and do cube test
    '''

    scores_by_topic = dict()

    ## score for each topic
    for topic_id, results in run['results'].items():
        
        ## get all subtopics for the topic
        subtopic_ids = list(set(get_all_subtopics(label_store, topic_id)))

        scores_by_topic[topic_id] = score_topic(topic_id, subtopic_ids, results)


       

    ## macro average over all the topics
    macro_avg = mean(scores_by_topic.values())

    run['scores']['cube_test'] = \
        {'scores_by_topic': scores_by_topic, 'macro_average': macro_avg}


def score_topic(topic_id, subtopic_ids, results):
    '''
    Runs the cube-test on a query topic.

    Cube-test requires computing the Gain of the results
    and the Time it takes to process them. The cube-test
    score is a measure of gain per time.

    `topic_id' is the current topic query to be scored
    `subtopic_ids' is a list of all the subtopics
    `results' is a dict containing results of the query,
              a ranked list
    '''

    ## this is where we would put relative importance of 
    ## the subtopics. at the moment, it's uniform
    theta = dict()
    for subtopic in subtopic_ids:
        theta[subtopic] = 1/len(subtopic_ids)

    ## this parameter sets the discount factor
    ## for topics already seen
    gamma = 0.5

    ## this dictionary allows us to compute the discount
    nrel = defaultdict(int)


    ## need to track when a subtopic overflows top of cube
    ## (i.e. when we fill up that subtopic)
    ## we assume the cube has unit height
    ## (really doesn't matter, is a normalization issue)
    tot_sub_rel = defaultdict(float)


    ## document length, in words
    ## since we don't collect, assuming default
    doc_len = 100

    time = 0
    score = 0

    for idx, result in enumerate(results):
        assert idx == result['rank'] - 1

        ## relevance of the document to the topic
        rel_to_topic = result['on_topic']

        gain_i = 0
        for subtopic, conf in result['subtopics']:
            
            ## compute gain
            rel = (2**conf - 1)/2**4 ## magic formula for relevance
            Gamma = gamma**nrel[subtopic]
            gain_i += Gamma*theta[subtopic]*rel*(tot_sub_rel[subtopic] < 1)

            ## update parameters
            nrel[subtopic] += 1
            tot_sub_rel[subtopic] += rel


        ## compute the time for this doc
        if rel_to_topic:
            r_i = 0.64
        else:
            r_i = 0.39
        time += 4.4 + r_i*(0.018*doc_len +7.8)

        ## compute the cube-test score
        score += (1/len(results))*(gain_i/time)

        ## Note on above:
        ## for an infinite stream, this score goes to 0
        ## rather than converge to a constant
        ## I feel like it should not have the 1/len(results)
        ## out front, or maybe use marginal rather than cumulative time

    return score










