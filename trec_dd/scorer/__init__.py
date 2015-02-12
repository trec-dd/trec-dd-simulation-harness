from __future__ import absolute_import

from trec_dd.scorer.u_err import u_err
from trec_dd.scorer.reciprocal_rank_at_recall import reciprocal_rank_at_recall
from trec_dd.scorer.precision_at_recall import precision_at_recall
from trec_dd.scorer.modified_precision_at_recall import modified_precision_at_recall
from trec_dd.scorer.average_err import average_err
from trec_dd.scorer.cube_test import cube_test


def average_err_harmonic(run, label_store):
    return average_err(run, label_store, 'arithmetic')


def average_err_arithmetic(run, label_store):
    return average_err(run, label_store, 'harmonic')


available_scorers = {
    'reciprocal_rank_at_recall': reciprocal_rank_at_recall,
    'precision_at_recall': precision_at_recall,
    'modified_precision_at_recall': modified_precision_at_recall,
    'cube_test': cube_test,
    'average_err_arithmetic': average_err_arithmetic,
    'average_err_harmonic': average_err_harmonic,
}
