#!/usr/bin/perl 

#
#--- this script find out which cron logs contains a line saved in "$input" file.
#--- for the input line avoid a line like /data/mta/, since "/" won't act well
#--- use something like "this is a test input."
#
#--- this works only for mta logs (the path is hard coded)
#

$dir = '/home/mta/Logs/';

$input = $ARGV[0];		#--- a file name which contains the line you want to find
$test  = `cat $input`;

$input = `ls $dir/*cron`;
@list  = split(/\n/, $input);

foreach $ent (@list){
	$line = `cat $ent`;
	if($line =~ /$test/){
		$out = `ls -l $ent`;
		print "$out\n";
	}
}

