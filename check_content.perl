#!/usr/bin/perl 

$line = `ls *perl *cgi`;
@input = split(/\s+/, $line);

foreach $ent (@input){
	$content = `cat $ent`;
	if ($content =~ /mailx/){
		if($content =~ /-rcus/){
			print "$ent\n";
		}
	}
}
