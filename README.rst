trec-dd-simulation-harness
==========================

This is the official "jig" for simulating a user interacting with a TREC
DD system during an interactive query session.

Usage
=====

After installation (see below), you will want run the harness to
generate a run file, you want to use the ``trec_dd_harness`` command.

The purpose of this harness is to interact with your TREC DD system by
issuing queries to your system, and providing feedback (truth data) for
the results produced by your system. While it does this, it keeps track
of the results produced by your system in a ``run file``. After
generating a run file with this harness, you can score the run using
trec\_dd\_scorer

The harness is run via three commands: start, step, stop. Typically, a
system will invoke start, then invoke step multiple times, and then
invoke stop. Every invocation must include the -c argument with a path
to a valid config.yaml file, as illustrated in example/config.yaml.

For efficiency, the first time you run with a new configuration, the truth
data must be loaded into your database using the ``load`` command.

::

   (Postgres example, using psql)
   CREATE USER trec_dd_user PASSWORD 'some_password';
   CREATE DATABASE trec_dd OWNER trec_dd_user

   (back at the Unix shell)
   (set up config.yaml to point to the database and the truth data file)
   trec_dd_harness -c config.yaml load

By default, when you score a system using the harness, all of the topics
are applied to the system in an order selected by the harness. You can
limit the topic\_ids that are used by specifying the topic\_ids property
in the config.yaml

The harness keeps track of the topic\_ids that have not yet been used in
building your system's run file. To reset this state, you must run the
``init`` command.

To progress through the topics, your system must execute this double
while loop, which is exactly what is implemented in the
trec\_dd/system/ambassador\_cli.py example:

::

        `init`
        while 1:
            topic_id <-- `start`
            if topic_id is None: break
            while 1:
                results <-- run your system
                feedback <-- `step(results)`
                if feedback is None or len(feedback) < batch_size:
                    break
                else:
                    your system processes the feedback
            `stop`

Each of the five commands returns a JSON dictionary which your system
can read using a JSON library. The harness always provides feedback for
every result, even if the feedback is that the system has no truth data
for that result. Note that your use of the harness *must* call ``stop``
in the next iteration after any step in which you submit fewer than
batch\_size results. If you fail to do this, the harness will exit.

See trec\_dd/system/ambassador\_cli.py for an example of using the
harness from python.

The harness outputs a runfile, whose path is set in the configuration file.

To score a runfile (see "Scoring the System"):

::

    trec_dd_scorer -c config.yaml run_file_in.txt run_file_scored.json > pretty_table.txt 2> log.txt &

run_file_in.txt is the run file output by the harness.  The scorer
outputs a scored run file in run_file_scored.json, and scores to
stdout.

This repository also provides a baseline system that randomizes subtopic
ordering (see "Example TREC DD Systems"). In particular this baseline
system shows how to hook an a system up to the jig in python. Hooking a
system up to the jig via the command line is further documented below.

::

    trec_dd_random_system -c config.yaml &> log.txt &

The scores for this baseline system using the TREC DD truth data are:

+---------+-----------------------------------+
| Score   | Metric                            |
+=========+===================================+
| 0.438  | average\_err\_arithmetic          |
+---------+-----------------------------------+
| 0.298   | average\_err\_harmonic            |
+---------+-----------------------------------+
| 0.125   | modified\_precision\_at\_recall   |
+---------+-----------------------------------+
| 0.981   | precision\_at\_recall             |
+---------+-----------------------------------+
| 0.075   | reciprocal\_rank\_at\_recall      |
+---------+-----------------------------------+

Installation
============

The recommended way to install and use the scorer is with python
virtualenv, which is a standard tool on all widely used platforms. For
example on Ubuntu:

::

    apt-get install python-virtualenv
    virtualenv vpy

or on CentOS:

::

    yum install python-virtualenv
    virtualenv vpy

or on MacOS X

::

    brew install pyenv-virtualenv
    pyenv-virtualenv vpy

or `on
Windows <http://www.tylerbutler.com/2012/05/how-to-install-python-pip-and-virtualenv-on-windows-with-powershell/>`__.

You will also need a database. We recommend postgres or mysql. You can
install this on your system using standard tools. The connection
information must be written into the config.yaml file referenced in the
commands above. See `config.yaml <examples/config.yaml>`__ for an
example.

Once you have a virtualenv, the following commands will install the
trec\_dd scorer. You should choose whether you are using mysql or
postgres and specify that as a pip extras declaration in square brackets
as follows:

::

    . vpy/bin/activate
    pip install trec_dd[mysql]

or to use postgres:

::

    . vpy/bin/activate
    pip install trec_dd[postgres]

That will create the shell entry points for running the two commands
illustrated at the top of this file.

Simulation Harness
==================

If you wish to evaluate a TREC DD system, you must run it against the
TREC DD simulation harness. A system interacting with the simulation
harness will produce a "runfile" that summarizes the simulation session.
The "runfile", for each of the system's response, encodes information
such as (1) "was the system's response on topic?" (2) "what subtopics
were contained within the system's response?" and (3) "how relevant was
the system's response?". Please see the specification for a "runfile"
for more information.

A TREC DD system interacts with the simulation harness by invoking
commands at the command line. Systems written in python may use the
`HarnessAmbassadorCLI <trec_dd/system/ambassador_cli.py>`__ to
facilitate this communication. The HarnessAmbassadorCLI is also useful
documentation for how one should interact with the harness via the
command line.

Once you have a "runfile", you may then score your run. Please see the
section "Gathering Scores" for more information.

Example TREC DD Systems
=======================

The directory trec\_dd/system holds example TREC DD systems to
demonstrate interaction with the simulation harness using a TREC DD
system. Right now, the only example system is random\_system.py.

Executing the Random System
===========================

Requirements
------------

To run the example systems, you must have a truth data XML file.  Make
sure your database is set up as per your config.yaml, and load the
truth data into the database:

::

   trec_dd_harness -c config.yaml load 

Running the System
------------------

You can run the random system in the simulation harness by calling

::

    trec_dd_random_system -c config.yaml >log.txt 2>&1

After this command executes, you should find the resulting system
runfile at the path you specified in the configuration. The runfile summarizes
the responses the random system gave to the harness, as well as the
harness's thoughts on those responses. This runfile captures everything
one needs to know in order to give a system a score.

Scoring the System
------------------

To score your runfile, you may use the trec\_dd/scorer/run.py script.

::

    trec_dd_scorer -c config.yaml run_file_in.txt run_file_scored.json > pretty_table.txt 2> log.txt &

Please see the section titled "Gathering Scores" for more information on
the scoring subsystem.

Gathering Scores
================

Requirements
------------

You must have a runfile generated for your system if you wish to score
it. You must also have access to the truth data used by the harness when
generating the runfile.

Running the Scorer
------------------

The top-level scoring script trec\_dd/scorer/run.py is used to generate
scores. To run it:

::

    trec_dd_scorer -c config.yaml run_file_in.txt run_file_scored.json > pretty_table.txt 2> log.txt &

This will go through your runfile and run each TREC DD
scorer. run_file_in.txt is the runfile produced as output by the
harness.  The scorer outputs an annotated version of your run in
run_file_scored.json, and the scores to stdout.

If you wish to run specific scorers, rather than all of them, please see the
'--scorer' option on the trec\_dd\_scorer command. The scorers specified
after the --scorer option must be the names of scorers known to the
system. These are exactly the following:

-  reciprocal\_rank\_at\_recall
-  precision\_at\_recall
-  modified\_precision\_at\_recall
-  average\_err\_arithmetic
-  average\_err\_harmonic

Description of Scorers
======================

-  reciprocal\_rank\_at\_recall calculates the reciprocal of the rank by
   which every subtopic for a topic is accounted for.

-  precision\_at\_recall calculates the precision of all results up to
   the point where every subtopic for a topic is accounted for.

-  average\_err\_arithmetic calculates the expected reciprocal rank for
   each subtopic, and then average the scores accross subtopics using an
   arithmetic average. It uses a graded relevance for computing stopping
   probabilities.

-  average\_err\_harmonic calculates the expected reciprocal rank for
   each subtopic, and then averages the scores accross subtopics using
   an arithmetic average. It uses graded relevance for computing
   stopping probabilities.
