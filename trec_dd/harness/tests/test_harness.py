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
    offset = '13-235'
    ratings = [[1, 2, 3]]*3

    label_store = LabelStore(kvl)

    for t_idx, topic in enumerate(topics):
        for s_idx, subtopic in enumerate(subtopics):
            label = Label(topic, 'doc'+str(t_idx)+str(s_idx),
                          'me', CorefValue.Positive,
                          subtopic_id1=subtopic,
                          subtopic_id2=offset + '|' + 'some_text',
                          rating=ratings[t_idx][s_idx])
            label_store.put(label)


def test_start(local_kvl):
    label_store = LabelStore(local_kvl)
    harness = Harness('topic1', label_store, runfile_path='some_path.txt')
    harness.start()


def test_step(local_kvl, tmpdir):
    runfile_path = os.path.join(str(tmpdir), 'runfile.txt')
    label_store = LabelStore(local_kvl)
    harness = Harness('topic1', label_store, runfile_path=runfile_path)
    results = [('doc02', 244), ('doc01', 100), ('doc12', 999),
               ('doc22', 445), ('doc11', 773)]
    feedback = harness.step(results)
    assert len(feedback) == 5
    for idx, entry in enumerate(feedback):
        assert results[idx][0] == entry['stream_id']
        assert results[idx][1] == entry['confidence']

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
    runfile = open(runfile_path, 'r')
    for idx, line in enumerate(csv.reader(runfile, delimiter='\t')):
        topic, doc_id, confidence, on_topic, subtopic, rating = line
        assert topic == feedback[idx]['topic_id']
        assert doc_id == feedback[idx]['stream_id']
        assert on_topic == str(feedback[idx]['on_topic'])

        if idx in [0, 1]:
            assert subtopic != 'null'
            assert rating != 'null'
        else:
            assert subtopic == 'null'
            assert rating == 'null'
