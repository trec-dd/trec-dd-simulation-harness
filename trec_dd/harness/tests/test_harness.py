from __future__ import absolute_import

from ..run import Harness

from dossier.label import LabelStore, Label, CorefValue
import csv
import kvlayer
import os
import pytest


@pytest.fixture
def local_kvl():
    kvl = kvlayer.client(config={},
                         storage_type='local',
                         namespace='test',
                         app_name='test')

    build_test_data(kvl)

    return kvl


def build_test_data(kvl):
    topics = ['topic1', 'topic2', 'topic3']
    subtopics = ['subtopic1', 'subtopic2', 'subtopic3']
    offset = '13,235'
    ratings = [[1, 2, 3]]*3

    label_store = LabelStore(kvl)

    for t_idx, topic in enumerate(topics):
        for s_idx, subtopic in enumerate(subtopics):
            meta = dict(topic_name=topic, topic_id=str(t_idx),
                        passage_text='howdy',
                        subtopic_name='bye bye',
            )
            label = Label(str(t_idx), 'doc'+str(t_idx)+str(s_idx),
                          'me', CorefValue.Positive,
                          subtopic_id1=subtopic,
                          subtopic_id2=offset,
                          rating=ratings[t_idx][s_idx],
                          meta=meta,
            )
            label_store.put(label)


def test_start(local_kvl):
    label_store = LabelStore(local_kvl)
    config = dict(run_file_path='some_path.txt')
    harness = Harness(config, local_kvl, label_store)
    harness.start()


def test_step(local_kvl, tmpdir):
    run_file_path = os.path.join(str(tmpdir), 'runfile.txt')
    label_store = LabelStore(local_kvl)
    config = dict(run_file_path=run_file_path)
    harness = Harness(config, local_kvl, label_store)
    results = ['doc02', 244, 'doc01', 100, 'doc12', 999,
               'doc22', 445, 'doc11', 773]

    response = harness.init()
    response = harness.start()
    topic_id = response['topic_id']
    feedback = harness.step(topic_id, results)
    assert len(feedback) == 5
    idx = 0
    for entry in feedback:
        assert results[idx] == entry['stream_id']
        assert results[idx + 1] == entry['confidence']
        idx += 2

    assert feedback[0]['on_topic']
    assert feedback[1]['on_topic']
    assert not feedback[2]['on_topic']
    assert not feedback[3]['on_topic']
    assert not feedback[4]['on_topic']

    assert len(feedback[0]['subtopics']) == 1
    assert len(feedback[1]['subtopics']) == 1
    assert len(feedback[2]['subtopics']) == 0
    assert len(feedback[3]['subtopics']) == 0
    assert len(feedback[4]['subtopics']) == 0

    # Check write file
    run_file = open(run_file_path, 'r')
    for idx, line in enumerate(csv.reader(run_file, delimiter='\t')):
        topic, doc_id, confidence, on_topic, subtopic_data = line
        assert topic == feedback[idx]['topic_id']
        assert doc_id == feedback[idx]['stream_id']
        assert on_topic == str(feedback[idx]['on_topic'])

        if idx in [0, 1]:
            assert subtopic_data
            subtopic, rating = subtopic_data.split(':')
            assert rating
            assert subtopic
        else:
            assert subtopic_data == 'NULL'
