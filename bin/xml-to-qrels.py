#!/usr/bin/env python2.7

from bs4 import BeautifulSoup
import sys

with open(sys.argv[1]) as xmlfile:
    dd = BeautifulSoup(xmlfile, 'xml')
    for psg in dd.find_all('passage'):
        subtopic = psg.parent
        topic = subtopic.parent
        domain = topic.parent

        topic_id = topic['id']
        subtopic_id = subtopic['id']
        doc_id = psg.docno.text
        psg_id = psg['id']
        rating = psg.rating.text

        print "\t".join([topic_id, subtopic_id, doc_id, psg_id, rating])
