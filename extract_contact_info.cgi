#!/usr/bin/env /home/ascds/DS.release/ots/bin/perl

#use CGI;
#use CGI::Carp;

#################################################################################
#										#
#	extract_contact_info.cgi: this script is called from index.html page	#
#				  and look for a contact information for a given#
#				  information (seq #, etc).			#
#										#
#		the input is given from /data/mta4/CUS/www/index.html		#
#			(https://cxc.cfa.harvard.edu/cus/index.html)		#
#										#
#		author: t. isobe (tisobe@cfa.harvard.edu)			#
#										#
#		last update: Mar 27, 2013					#
#										#
#################################################################################

print "Content-type: text/html; charset=utf-8\n\n";

print "<!DOCTYPE html>";
print "<html>";
print "<head>";
print "<title>Ocat Data Check Page</title>";
print "<style  type='text/css'>";
print "table{text-align:center;margin-left:auto;margin-right:auto;border-style:solid;border-spacing:8px;border-width:2px;border-collapse:separate}";
print "a:link {color:blue;}";
print "a:visited {color:teal;}";
print "</style>";
print "</head>";

print "<body style='color:#000000;background-color:#FFFFE0'>";


read(STDIN, $temp, $ENV{'CONTENT_LENGTH'});
chomp $temp;
@atemp = split(/=/, $temp);
$temp  = $atemp[1];
$temp  =~ s/\s+//g;
if($temp =~ /\%/){
	@atemp = split(/\%/, $temp);
	$temp  = $atemp[0];
}

#
#--- this one is a copy of /pool14/chandra/contactinfo.txt, updated a few times a day by cron job
#

open(FH, "/data/mta4/CUS/www/Usint/ocat/Info_save/contactinfo.txt");

@save = ();
OUTER:
while(<FH>){
	chomp $_;
	if($_ =~ /$temp/){
		@atemp = split(/\|/, $_);
		$prop  = $atemp[1];
		$prop  =~ s/\s+//g;
		$obsid = $atemp[2];
		$obsid =~ s/\s+//g;
		$seq   = $atemp[3];
		$seq   =~ s/\s+//g;
		if($prop == $temp || $obsid == $temp || $seq == $temp){			#--- extact match
#		if($prop =~ /$temp/ || $obsid =~ /$temp/ || $seq =~ /$temp/){		#--- fuzzy match
			$line = $_;
#			last OUTER;
			push(@save, $line);
		}
	}
}
close(FH);

@header=('prop_num','obsid','seq_nbr','targname','type','pi_title','pi_fname','pi_mname','pi_lname','pi_email','pi_phone','pi_fax','pi_inst','pi_dept','pi_mstop','pi_street','pi_city','pi_state','pi_zip','obsvr_title','obsvr_fname','obsvr_mname','obsvr_lname','obsvr_email','obsvr_phone','obsvr_fax','obsvr_inst','obsvr_dept','obsvr_mstop','obsvr_street','obsvr_city','obsvr_state','obsvr_zip');


print "<h2>Contact Information</h2>";

foreach $ent (@save){
	@atemp = split(/\|/, $ent);
	print '<table border=1>';

	$j = 1;
	OUTER:
	foreach $ent (@header){
		if($atemp[$j] =~ /NULL/i){
			$j++;
			next OUTER;
		}	
		print "<tr><th>$ent</th><td>$atemp[$j]</td></tr>";
		$j++;
	}
	print '</table>';
	print '<br />';
}

print "</body>";
print "</html>";
