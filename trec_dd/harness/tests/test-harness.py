


stream_ids = [('%d-%s' % (time.time() - rand() * 10000, md5(str(rand())).hexdigest()),
               int(1000 * rand()))
              for i in range(5)]

print "trec_dd_harness --step " + " ".join(['%s %d' % (stream_id, confidence) for stream_id, confidence in stream_ids])
