## CubeTest Implementation For TREC Dynamic Domain Track Evaluation

## For Linux Unix Platform

## This software is released under an MIT/X11 open source license. Copyright 2015 @ Georgetown University

## Version: lgc

## Date: 12/03/2014

#########################################

#!/usr/bin/perl -w

#########################################

#### Parameter setup and initialization
$usage = "Usage: perl score/cubeTest.pl qrel run_file cutoff\n
- qrel: qrel file. It is a trec qrel file that converted from topics.xml. Its format is topic_id subtopic_id doc_no rating, which is located at ./truth_data/qrel.txt.\n
- run_file: Your run for submission.  It is in TREC format.\n
- cutoff: the number of iterations where you run cubetest over your results.\n
";
#index_path: index path \n

$MAX_JUDGMENT = 4; # Maximum gain value allowed in qrels file.

$MAX_HEIGHT = 5; #max hight for the test cube

$beta =1; #a factor decide recall-oritention or precision-oritention

$gamma = 0.5;

$arg = 0;
$QRELS = $ARGV[$arg++] or die $usage;
$RUN = $ARGV[$arg++] or die $usage;
$K = $ARGV[$arg++] or die $usage; 
#$index = $ARGV[$arg++] or die $usage; 

# $topic $docno $subtopic $judgement
%qrels=();
#$topic $subtopic $area
%subtopicWeight=();
# $topic $subtopic $gainHeights
%currentGainHeight=();
# $topic $subtopic $ocurrences
%subtopicCover = ();
# $docID $docLength
%docLengthMap = ();
%seen=();

#########################################

#### Read qrels file(groundtruth), check format, and sort

open (QRELS, $QRELS) || die "$0: cannot open \"$QRELS\": !$\n";
while (<QRELS>) {
  s/[\r\n]//g;
  ($topic, $subtopic, $docno, $judgment) = split ('\s+');
  $subTWeigt = 1;
  $topic =~ s/^.*\-//;
  die "$0: format error on line $. of \"$QRELS\"\n"
    unless
      $topic =~ /^[0-9]+$/ 
      && $judgment =~ /^-?[0-9.]+$/; #&& $judgment <= $MAX_JUDGMENT
  if ($judgment > 0) {
    $qrels{$topic}{$docno}{$subtopic}=$judgment/$MAX_JUDGMENT;
    if(!exists $subtopicWeight{$topic}{$subtopic}){
      if(defined $subTWeigt && length $subTWeigt> 0){
         $subtopicWeight{$topic}{$subtopic} = $subTWeigt;
      }      
      $currentGainHeight{$topic}{$subtopic} = 0;
      $subtopicCover{$topic}{$subtopic} = 0;
    }

    $seen{$topic}++;
  }
}
close (QRELS);

#########################################

#### Normalize subtopic weight

for my $tkey (keys %subtopicWeight){
    my %subs = %{$subtopicWeight{$tkey}};
    my $maxWeight = &getMaxWeight($tkey);
    for my $skey (keys %subs){        
        $subtopicWeight{$tkey}{$skey} = $subtopicWeight{$tkey}{$skey}/$maxWeight;
    }
}

sub getMaxWeight{
  my ($topic) = @_;
  my $maxWeight = 0;
  my %subtopics = %{$subtopicWeight{$topic}};
  for my $skey (keys %subtopics){
      $maxWeight += $subtopics{$skey};
  }
  return $maxWeight;
}

$topics = 0;
$runid = "?????";

#########################################

#### Read run file(returned document rank lists), check format, and sort
$maxIteration=0;
open (RUN, $RUN) || die "$0: cannot open \"$RUN\": !$\n";
my $rank = "";
while (<RUN>) {
  s/[\r\n]//g;
  ($topic, $q0, $docno, $rank, $score, $runid, $iteration) = split ('\s+');
  if($maxIteration < $iteration){
	$maxIteration = $iteration;
  }
  $doclength = 1; #`./bin/getDocLength $docno $index`;
  #$doclength =~ s/[\r\n]//g;
  $topic =~ s/^.*\-//;
  die "$0: format error on line $. of \"$RUN\"\n"
    unless
      $topic =~ /^[0-9]+$/ && $q0 eq "Q0" && $docno;
  $run[$#run + 1] = "$topic $docno $score $iteration";

  if(defined $doclength && length $doclength > 0){
     if(!exists $docLengthMap{$docno}){
     	$docLengthMap{$docno} = $doclength;
     }
  } 
}
#########################################

#### Process runs: compute measures for each topic and average

print "runid,topic,ct_speed\@$K,ct_accel\@$K\n";
$topicCurrent = -1;
for ($i = 0; $i <= $#run; $i++) {
  ($topic, $docno, $score, $iteration) = split (' ', $run[$i]);
  if ($topic != $topicCurrent) {
    if ($topicCurrent >= 0) {
      &topicDone ($RUN, $topicCurrent, \@docls, \@iterations );
      $#docls = -1;
      $#iterations = -1;
    }
    $topicCurrent = $topic;
  }
  $docls[$#docls + 1] = $docno;
  $iterations[$#iterations + 1] = $iteration;
}
if ($topicCurrent >= 0) {  
  &topicDone ($RUN, $topicCurrent, \@docls, \@iterations);
  $#docls = -1;
  $#iterations = -1;
}
if ($topics > 0) {
  $ctAvg = $ctTotal/$topics;
  $accelAvg = $ct_accuTotal/$topics;

  printf "$RUN,amean,%.10f,%.10f\n",$ctAvg,$accelAvg;
} else {
  print "$RUN,amean,0.00000,0.00000\n";
}

exit 0;

#########################################

#### Compute and report information for current topic

sub topicDone {
  my ($runid, $topic, $ref_docls, $ref_iterations) = @_;
  if (exists $seen{$topic}) {
    my $_ct = &ct($K, $topic, $ref_docls, $ref_iterations);
    my $_time = &getTime($K, $topic, $ref_docls, $ref_iterations);

    my $ct_accu = 0;
    my $limit = ($K <= $maxIteration? $K : $maxIteration);
    for($count =0 ; $count < $limit; $count ++){
        &clearEnv;
        my $accel_ct = &ct($count + 1, $topic, $ref_docls, $ref_iterations);
        my $accel_time = &getTime($count + 1, $topic, $ref_docls, $ref_iterations);

        $ct_accu += $accel_ct / $accel_time;
    }
    $ct_accu = $ct_accu / $limit;
    $ct_accuTotal += $ct_accu;
    
    my $ct_speed = $_ct / $_time;
    $ctTotal += $ct_speed;
    $topics++;
    printf  "$runid,$topicCurrent,%.10f,%.10f\n",$ct_speed,$ct_accu;
  }
}

sub clearEnv{
  for my $tkey (keys %currentGainHeight){
      my %subs = %{$currentGainHeight{$tkey}};
      for my $skey (keys %subs){
          $currentGainHeight{$tkey}{$skey}=0;
      }
  }

  for my $tkey (keys %subtopicCover){
      my %subs = %{$subtopicCover{$tkey}};
      for my $skey (keys %subs){
          $subtopicCover{$tkey}{$skey}=0;
      }
  }  
}

#########################################

#### Compute ct over a sorted array of gain values, reporting at depth $k

sub ct {
 my ($k, $topic, $ref_docls, $ref_iterations) = @_;

 my @local_docls = @{$ref_docls};
 my @local_iterations = @{$ref_iterations};

 my ($i, $score) = (0, 0);
 for ($i = 0; $i <= $#local_docls && $k >= $local_iterations[$i] ; $i++) {
   my $docGain = &getDocGain($topic, $local_docls[$i], $i + 1);
   $score += $docGain;
 }
 return $score;
}

sub getDocGain{
  my ($topic, $docno, $rank) = @_;
  my $rel = 0;
  
  if(exists $qrels{$topic}{$docno}){
    my %subtopics = %{$qrels{$topic}{$docno}};
    my $inFlag = -1;
    for my $subKey(keys %subtopics){
        if(&isStop($topic, $subKey) < 0 ){
           my $boost = 1;
           for my $subKey1(keys %subtopics){
               if(exists $currentGainHeight{$topic}{$subKey1} && $subKey != $subKey1){
                  my $areaW = &getArea($topic, $subKey1);
                  my $heightW =  $currentGainHeight{$topic}{$subKey1};
                  $boost += $beta * $areaW * $heightW;
               }               
           }

           my $pos = 0;
           if(exists $subtopicCover{$topic}{$subKey}){
              $pos = $subtopicCover{$topic}{$subKey};
           }

           my $height = &getHeight($topic, $docno, $subKey,$pos + 1, $boost);

           my $area = &getArea($topic, $subKey);

           $rel = $beta * $area * $height;
        }
    }

    for my $subKey (keys %subtopics){
           $subtopicCover{$topic}{$subKey}++;
    }
    
  }

  return $rel;   
}

#########################################

#### Get subtopic importance

sub getArea{
  my ($topic, $subtopic) = @_;
  
  if(exists $subtopicWeight{$topic}{$subtopic}){
     return $subtopicWeight{$topic}{$subtopic};
  }else{
     $subtopicWeight{$topic}{$subtopic} = &getDiscount($subtopic)/&getMaxArea($topic);
     return $subtopicWeight{$topic}{$subtopic};
  }

  return 0;
}

sub getHeight{
  my ($topic, $docno, $subtopic, $pos, $benefit) = @_;
  
  #set $benefit = 1 if don't want to consider boost effect
  $benefit = 1;
  my $rel = &getHeightDiscount($pos) * $qrels{$topic}{$docno}{$subtopic} * $benefit;

  $currentGainHeight{$topic}{$subtopic} += $rel;

  return $rel;
}

sub getHeightDiscount{
  my ($pos) = @_;

  return ($gamma) ** $pos;
}


sub isStop{
  my ($topic, $subtopic) = @_;
  if($currentGainHeight{$topic}{$subtopic} < $MAX_HEIGHT){
    return -1;
  }

  return 0;
}

#sub getTime{
#  my ($pos, $topic, $ref_docls, $ref_iterations) = @_;
#  my @local_docls = @{$ref_docls};
#  my @local_iterations = @{$ref_iterations};
#
#  my $time =0;
#  for (my $count = 0; $local_iterations[$count] <= $pos && $count <= $#local_docls ; $count++) {
#       my $prob = 0.39;
#       if (exists $qrels{$topic}{$local_docls[$count]}){
#         $prob = 0.64;
#       }
#
# 	$time += 4.4 + (0.018*$docLengthMap{$local_docls[$count]} +7.8)*$prob;
#  }
#
#  return $time;
#}

sub getTime{
  my ($pos, $topic, $ref_docls, $ref_iterations) = @_;

  my $time = $pos;

  if($pos > $maxIteration){
     $time = $maxIteration;
  }

  return $time;
}

sub getDiscount{
  my ($pos) = @_;

  return 1/(log($pos + 1)/log(2));
}

sub getMaxArea{
  my ($topic) = @_;

  my %subtopics = %{$subtopicCover{$topic}};
  my @subs = keys %subtopics;
  my $subtopicNum = $#subs + 1;

  my $maxArea = 0;
  for($count = 0;$count < $subtopicNum; $count++){
     $maxArea += &getDiscount($count + 1);
  }

  return $maxArea;
}
