# trec-dd-simulation-harness

This is the official "jig" for simulating a user interacting with a
TREC DD system during an interactive query session.

# Usage

To evaluate an example "random" system (see "Example TREC DD Systems"):

    python -m trec_dd.system.random_system truth_data.csv run_file_out.csv

To score a runfile (see "Scoring the System"):

    trec_dd_score run_file.csv truth_data.csv --scorer scorer1 scorer2 ..
   

# Simulation Harness

If you wish to evaluate a TREC DD system, you must run it against the
TREC DD simulation harness. A system interacting with the simulation
harness will produce a "runfile" that summarizes the simulation
session.  The "runfile", for each of the system's response, encodes
information such as (1) "was the system's response on topic?" (2)
"what subtopics were contained within the system's response?"  and (3)
"how relevant was the system's response?". Please see the
specification for a "runfile" for more information.

A TREC DD system can interact with the simulation harness in a couple
of ways. If the system is written in python, it can use the
HarnessAmbassador interfact found under trec\_dd/system. Otherwise,
the TREC DD system must invoke harness commands via the command
line. Please see trec_dd/harness for more information.

Once you have a "runfile", you may then score your run. Please
see the section "Gathering Scores" for more information.

# Example TREC DD Systems

The directory trec\_dd/system holds example TREC DD systems to
demonstrate interaction with the simulation harness using a TREC DD
system. Right now, the only example system is random_system.py.

# Executing the Random System

## Requirements

To run the example systems, you must have a truth data csv file.

## Running the System

You can run the random system in the simulation harness by
calling

    python -m trec_dd.system.random_system. truth_data.csv runfile_out.csv

After this command executes, you should find the resulting system
runfile at the path you specified in the command. The runfile summarizes
the responses the random system gave to the harness, as well as the harness's
thoughts on those responses. This runfile captures everything one needs to
know in order to give a system a score.

## Scoring the System

To score your runfile, you may use the trec_dd/scorer/run.py script.

    trec_dd_scorer run_file.csv truth_data.csv --scorer scorer1 scorer2 scorer3 ...

Please see the section titled "Gathering Scores" for more information on the scoring
subsystem.

# Gathering Scores

## Requirements

You must have a runfile generated for your system if you wish to score
it. You must also have access to the truth data used by the harness
when generating the runfile.

## Running the Scorer

The top-level scoring script trec\_dd/scorer/run.py is used to generate
scores. To run it:

    trec_dd_scorer run_file.csv truth_data.csv --scorer scorer1 scorer2 ...

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
