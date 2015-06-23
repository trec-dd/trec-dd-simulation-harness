'''Generate truth data from a truth_data_file.

A truth_data_file may be produced by a human being, so sometimes
it should be considered truth data. This file provides
utilities for turning a truth_data_file of a certain format into
truth data the harness understands.
'''

from __future__ import absolute_import
import argparse
import json
from bs4 import BeautifulSoup
import logging
import sys

from dossier.label import Label, LabelStore, CorefValue
import kvlayer
import yakonfig

logger = logging.getLogger(__name__)

def parse_passage(p):
    '''Extract a line_data dict from a passage's XML data and context.
    '''
    line_data = {}
    domain = p.parent.parent.parent
    topic = p.parent.parent
    subtopic = p.parent
    line_data['domain_id'] = domain['id'].encode('utf-8')
    line_data['domain_name'] = domain['name'].encode('utf-8')
    line_data['userid'] = 'dropped'
    line_data['username'] = 'dropped'
    line_data['topic_id'] = topic['id'].encode('utf-8')
    line_data['topic_name'] = topic['name'].encode('utf-8')
    line_data['subtopic_id'] = subtopic['id'].encode('utf-8')
    line_data['subtopic_name'] = subtopic['name'].encode('utf-8')
    line_data['passage_id'] = p['id'].encode('utf-8')
    line_data['passage_name'] = p.find('text').text.encode('utf-8')
    line_data['docno'] = p.docno.text.encode('utf-8')
    line_data['grade'] = p.rating.text.encode('utf-8')
    return line_data
    
def make_full_doc_id(doc_id, offset_start, offset_end):
    '''A full doc_id is of the form: doc_id#offset_start,offset_end
    '''
    offset_string = ','.join([offset_start, offset_end])
    return '#'.join([doc_id, offset_string])

def make_offset_string(offset_start, offset_end):
    '''Create an offset string from a pair of offsets.

    :param offset_start: str
    :param offset_end: str
    '''
    return ','.join([offset_start, offset_end])

def label_from_truth_data_file_line(line_data):
    '''Create a label from a *parsed* truth_data_file line.

    :param line_data: dict
    '''
    # document data
    doc_id = line_data['docno']
    if not doc_id.strip():
        logger.warn('dropping invalid truth data line: '
                    'bad docno: %r: %r'
                    % (doc_id, line_data))
        return None

    if len(line_data['passage_name'].strip()) < 1:
        logger.warn('dropping empty passage: %r', line_data)
        return None

    # annotation data
    topic_id = line_data['topic_id']
    subtopic_id = line_data['subtopic_id']
    passage_id = line_data['passage_id']
    annotator = line_data['userid']

    # value data
    value = CorefValue.Positive
    try:
        rating = int(line_data['grade'])
    except ValueError:
        logger.warn('replacing bogus grade with zero = %r',
                    line_data['grade'])
        rating = 0

    if rating < 0:
        value = CorefValue.Negative
        rating = 0

    # meta data
    meta = {'domain_name': line_data['domain_name'],
            'domain_id': line_data['domain_id'],
            'username': line_data['username'],
            'topic_name': line_data['topic_name'],
            'topic_id': line_data['topic_id'],
            'subtopic_name': line_data['subtopic_name'],
            'passage_text': line_data['passage_name']}

    label = Label(topic_id, doc_id, annotator, value,
                  subtopic_id1=subtopic_id, subtopic_id2=passage_id,
                  rating=rating, meta=meta)
    return label

def parse_truth_data(label_store, truth_data_path, batch_size=10000):
    data_file = open(truth_data_path, 'r')
    data = BeautifulSoup(data_file, 'xml')

    labels_to_put = []
    num_labels = 0
    for psg in data.find_all('passage'):
        line_data = parse_passage(psg)
        label = label_from_truth_data_file_line(line_data)
        if label is not None:
            labels_to_put.append(label)
            num_labels += 1
            if num_labels % 1000 == 0:
                logger.debug('Converted %d labels.' % num_labels)
            if len(labels_to_put) >= batch_size:
                label_store.put(*labels_to_put)
                labels_to_put = []
    if len(labels_to_put) > 0:
        label_store.put(*labels_to_put)

def main():
    parser = argparse.ArgumentParser('test tool for checking that we can load '
                                     'the truth data as distributed by NIST for '
                                     'TREC 2015')
    parser.add_argument('truth_data_path', help='path to truth data file')
    modules = [yakonfig, kvlayer]
    args = yakonfig.parse_args(parser, modules)
    logging.basicConfig(level=logging.DEBUG)
    kvl = kvlayer.client()
    label_store = LabelStore(kvl)
    parse_truth_data(label_store, args.truth_data_path)
    logger.debug('Done!  The truth data was loaded into this kvlayer backend: %r',
                 json.dumps(yakonfig.get_global_config('kvlayer'), indent=4,
                            sort_keys=True))

if __name__ == '__main__':
    main()
