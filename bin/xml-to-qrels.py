#!/usr/bin/env python2.7

from bs4 import BeautifulSoup
import sys
import collections

qrels = collections.OrderedDict()

with open(sys.argv[1]) as xmlfile:
    dd = BeautifulSoup(xmlfile, 'xml')
    for psg in dd.find_all('passage'):
        subtopic = psg.parent
        topic = subtopic.parent
        domain = topic.parent

        topic_id = topic['id']
        subtopic_id = subtopic['id']
        doc_id = psg.docno.text
        rating = psg.rating.text

        qrels[topic_id + '\t' + subtopic_id + '\t' + doc_id] = rating

for key in qrels:
    print key, '\t', qrels[key]
