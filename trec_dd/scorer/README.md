# Runfile Scoring System

This directory contains scripts for scoring runfiles produced
by a recommender system interacting with the simulation harness.

# Gathering Scores

## Requirements

You must have a runfile generated for your system if you wish to score
it. You must also have access to the truth data used by the harness
when generating the runfile.

## Running the Scorer

The top-level scoring script trec\_dd/scorer/run.py is used to generate
scores. To run it:

    python run.py path/to/runfile path/to/truthdata.kvl --scorer scorer1 scorer2 ...

This will go through your runfile and use all of the specified scorers to
evaluate the run of your system. The scorers specified after the --scorer
option must be the names of scorers known to the system. These are
exactly the following:

 * reciprocal\_rank\_at\_recall
 * precision\_at\_recall
 * modified\_precision\_at\_recall
 * average\_err\_arithmetic
 * average\_err\_harmonic
 * average\_err\_arithmetic\_binary
 * average\_err\_harmonic\_binary

Please see the description of each scorer below.

# Description of Scorers

 * reciprocal\_rank\_at\_recall calculates the reciprocal of the rank by which
 every subtopic for a topic is accounted for.

 * precision\_at\_recall calculates the precision of all results up to the point
 where every subtopic for a topic is accounted for.

 * average\_err\_arithmetic calculates the expected reciprocal rank
 for each subtopic, and then average the scores accross subtopics
 using an arithmetic average. It uses a graded relevance for computing
 stopping probabilities.

 * average\_err\_arithmetic\_binary calculates the expected reciprocal
 rank for each subtopic, and then averages the scores accross
 subtopics using an arithmetic average. It uses binary relevance for
 computing stopping probabilities. Hence, this scorer ignores the
 'rating' field in the runfile.

 * average\_err\_harmonic calculates the expected reciprocal rank for
 each subtopic, and then averages the scores accross subtopics using
 an arithmetic average. It uses graded relevance for computing
 stopping probabilities.

 * average\_err\_harmonic\_binary average\_err\_harmonic calculates the expected reciprocal rank for
 each subtopic, and then averages the scores accross subtopics using
 an arithmetic average. It uses binary relevance for computing stopping probabilities. Hence,
 this scorer ignores the 'rating' field in the runfile.
