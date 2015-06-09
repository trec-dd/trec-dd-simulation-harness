'''Generate truth data from a runfile.

A runfile may be produced by a human being, so sometimes
it should be considered truth data. This file provides
utilities for turning a runfile of a certain format into
truth data the harness understands.
'''

from __future__ import absolute_import
import argparse
import csv

from dossier.label import Label, LabelStore, CorefValue
import kvlayer


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

def make_subtopic(offset_start, offset_end):
    return ','.join([offset_start, offset_end])

def label_from_runfile_line(line_data):
    # content_id1, content_id2, subtopic_id1, subtopic_id2, annotator, value
    # document data
    doc_id = line_data['docno']
    offset_str = make_subtopic(line_data['offset_start'],
                               line_data['offset_end'])

    # annotation data
    topic = line_data['topic_id']
    print topic
    subtopic = line_data['subtopic_id']
    annotator = line_data['userid']

    # meta data
    try:
        rating = int(line_data['grade'])
    except ValueError:
        rating = 0

    if rating < 0:
        rating = 0

    label = Label(topic, doc_id, annotator, CorefValue.Positive,
                  subtopic_id1=subtopic, subtopic_id2=offset_str,
                  rating=rating)
    return label

def strip_iter(fh):
    '''Yields stripped lines from a file.
    '''
    for line in fh:
        stripped = line.strip()
        stripped = stripped.replace('\r', '')
        stripped = stripped.replace('\n', '')
        yield stripped

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('runfile', help='path to runfile')
    parser.add_argument('labels_out', help='path to labels output file')
    args = parser.parse_args()

    kvl_config = {'storage_type': 'filestorage',
                  'filename': args.labels_out,
                  'namespace': 'test',
                  'app_name': 'test'}
    kvl = kvlayer.client(kvl_config)
    label_store = LabelStore(kvl)

    runfile_path = args.runfile
    runfile = open(runfile_path, 'r')
    runfile = strip_iter(runfile)
    csv_reader = csv.reader(runfile)

    csv_reader.next() # skip first line which is a header.

    for line in csv_reader:
        print 'visiting line.'
        line_data = parse_line(line)
        label = label_from_runfile_line(line_data)
        label_store.put(label)

if __name__ == '__main__':
    main()
