'''trec_dd.utils provides tools for interacting with labels in TREC DD

.. This software is released under an MIT/X11 open source license.
   Copyright 2015 Diffeo, Inc.

'''

def get_all_subtopics(label_store, topic_id):
    labels = label_store.directly_connected(topic_id)

    def subtopic_from_label(label):
        subtopic_id = label.subtopic_for(topic_id)
        return subtopic_id

        ## oops, I thought we needed this for the special format used
        ## in TREC DD label table...
        offset, text = subtopic_id.split('|')
        text = topic_id_to_query(text)
        subtopic = {
            'subtopic_id': label.subtopic_for(topic),
            'offset': offset,
            'text': text,
            'rating': label.rating
        }
        return subtopic

    subtopics = map(subtopic_from_label, labels)
    return subtopics
