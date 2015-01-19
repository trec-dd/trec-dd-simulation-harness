

from __future__ import division

#from numpy import mean

def mean(l):
    s = sum(l)
    return s / len(l)


def u_err(run):
    scores_by_topic = dict()
    for topic_id, results in run['results'].items():
        scores_by_topic[topic_id] = len(results)

    macro_avg = mean(scores_by_topic.values())
    run['scores']['u_err'] = {'scores_by_topic': scores_by_topic, 'macro_average': macro_avg}

