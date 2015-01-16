from __future__ import absolute_import

import argparse
from dossier.label import LabelStore, Label, CorefValue
import kvlayer
from md5 import md5
from random import random
import time


def random_sid():
    return '%d-%s' % (time.time() - random() * 10000, md5(str(random())).hexdigest())


def random_confidence():
    return '%d' % (random() * 1000)


def build_demo_data(kvl):

    label_store = LabelStore(kvl)

    topic = 'where_are_aid_workers_housed_near_Monrovia'
    subtopics = ['Tanji_Fish_Curing_Site',
                 'Camp_Ramrod',
                 'Town_of_Wamba']
    subtopic_to_documents = {
        0: [(random_sid(), '15-93|we_drove_out_to_the_other_side_' +
             'of_the_river_delta_to_a_small_fish_smoking_camp', 3)],
        1: [(random_sid(), '200-217|Ramrod_(Facility)', 2)],
        2: [(random_sid(), '53-63|Wamba_Town', 2),
            (random_sid(), '44-50|Woomba', 1)]
    }

    for idx, subtopic in enumerate(subtopics):
        for doc_id, subtopic_id2, relevance in subtopic_to_documents[idx]:

            print doc_id

            label = Label(topic, doc_id, 'John', CorefValue.Positive,
                          subtopic_id1=subtopic,
                          subtopic_id2=subtopic_id2,
                          relevance=relevance)
            label_store.put(label)


def build_test_data(kvl):
    topics = ['topic1', 'topic2', 'topic3']
    subtopics = ['subtopic1', 'subtopic2', 'subtopic3']
    relevances = [[1, 2, 3]]*3
    offset = '13-235'

    label_store = LabelStore(kvl)

    for t_idx, topic in enumerate(topics):
        for s_idx, subtopic in enumerate(subtopics):
            label = Label(topic, 'doc'+str(t_idx)+str(s_idx),
                          'me', CorefValue.Positive,
                          subtopic_id1=subtopic,
                          subtopic_id2=offset+'|'+'some text',
                          relevance=relevances[t_idx][s_idx])
            label_store.put(label)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dest_path',
                        help='File into which you want to store test data')

    args = parser.parse_args()

    kvl = kvlayer.client(config={'filename': args.dest_path},
                         storage_type='filestorage',
                         namespace='test',
                         app_name='test')

    build_demo_data(kvl)

if __name__ == '__main__':
    main()
