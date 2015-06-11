'''Generate truth data from a truth_data_file.

A truth_data_file may be produced by a human being, so sometimes
it should be considered truth data. This file provides
utilities for turning a truth_data_file of a certain format into
truth data the harness understands.
'''

from __future__ import absolute_import
import argparse
import csv
import logging

from dossier.label import Label, LabelStore, CorefValue
import kvlayer

logger = logging.getLogger(__name__)

def parse_line(line):
    '''Given a csv line, return a dict.
    '''
    line_data = {}
    line_data['domain_id'] = line[0]
    line_data['domain_name'] = line[1]
    line_data['userid'] = line[2]
    line_data['username'] = line[3]
    line_data['topic_id'] = line[4]
    line_data['topic_name'] = line[5]
    line_data['subtopic_id'] = line[6]
    line_data['subtopic_name'] = line[7]
    line_data['passage_id'] = line[8]
    line_data['passage_name'] = line[9]
    line_data['docno'] = line[10]
    line_data['offset_start'] = line[11]
    line_data['offset_end'] = line[12]
    line_data['grade'] = line[13]
    line_data['timestamp'] = line[14]
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
    offset_str = make_offset_string(line_data['offset_start'],
                                    line_data['offset_end'])

    # annotation data
    topic = line_data['topic_id']
    subtopic = line_data['subtopic_id']
    annotator = line_data['userid']

    # value data
    value = CorefValue.Positive
    try:
        rating = int(line_data['grade'])
    except ValueError:
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

    label = Label(topic, doc_id, annotator, value,
                  subtopic_id1=subtopic, subtopic_id2=offset_str,
                  rating=rating, meta=meta)
    return label

def strip_iter(fh):
    '''Yields stripped lines from a file.
    '''
    for line in fh:
        stripped = line.strip()
        stripped = stripped.replace('\r', '')
        stripped = stripped.replace('\n', '')
        yield stripped

def parse_truth_data(label_store, truth_data_path):
    data = open(truth_data_path, 'r')
    # cleanse the nasty Window's characters
    data = strip_iter(data)
    csv_reader = csv.reader(data)

    csv_reader.next() # skip first line which is a header.

    num_labels = 0
    for line in csv_reader:
        line_data = parse_line(line)
        label = label_from_truth_data_file_line(line_data)
        label_store.put(label)
        num_labels += 1
        logger.debug('Converted %d labels.' % num_labels)

def main():
    parser = argparse.ArgumentParser('test tool for checking that we can load '
                                     'the truth data as distributed by NIST for '
                                     'TREC 2015')
    parser.add_argument('truth_data_path', help='path to truth data file')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    kvl_config = {'storage_type': 'local',
                  'namespace': 'test',
                  'app_name': 'test'}
    kvl = kvlayer.client(kvl_config)
    label_store = LabelStore(kvl)
    parse_truth_data(label_store, args.truth_data_path)
    logger.debug('Done!  The data was loaded into memory, and worked, and now we are exiting.')

if __name__ == '__main__':
    main()
