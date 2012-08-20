#!/soft/ascds/DS.release/ots/bin/perl

#use CGI;
#use CGI::Carp;

#BEGIN {
#    use CGI::Carp qw(carpout);
#    open(LOG, ">>/proj/ascwww/AXAF/extra/science/cgi-gen/logs/target_error_log")
#        or die "Unable to append to error_log: $!\n";
#    carpout(*LOG);
#}

#########################################################################################
#											#
#	sot_answer.cgi: SOT version of answer.cgi					#
#											#
#		this version is supported by t. isobe (tisobe@cfa.harvard.edu)		#
#		last update: Feb 28, 2011						#
#											#
#		data are now read from /proj/web-icxc/cgi-bin/obs_ss/sot_ocat.out (etc) #
#											#
#---------------------------------------------------------------------------------------#
#											#
# 	Script to search ObsCat DB on any of several parameters, listed below, given	#
# 	in an html form:								#
#											#
# 	Sequence Number									#
# 	Proposal Number									#
# 	Last Name of Principal Investigator						#
# 	Last Name of Observer on Proposal						#
# 	Target Name									#
# 	Observation ID Number								#
# 	Coordinates of Object.  Either exact or range in units of Degrees or Minutes	#
# 	Science Instrument.  Options being ACIS-I, ACIS-S, HRC-I, HRC-S			#
# 	Grating.  Options being HETG, LETG, NONE					#
# 	Type of Observation.  Options being GO, GTO, CAL, TOO				#
# 	Status of Observation.  Options being Unobserved, Scheduled, Partially		#
#   	Observed, Observed, Archived							#
# 	Science category								#
# 	Observing cycle									#
# 	Options for sorting include, Sequence #, RA and Date of Observation (not	#
#   	currently implemented)								#
#											#
# 	Script works by reading in a dump of the ObsCat DB line-by-line and matching	#
# 	parameters with those entered in the form.  If nothing is entered in the form	#
# 	an error message is returned.  If nothing in the database matches that given	#
# 	in the form an error message is returned.  Script returns a list of all		#
# 	observations matching the selected parameters, including links to the Mission	#
# 	Planning Summary pages or, if these don't exist the USG Parameter pages.	#
#											#
# 	Note that subsequen MP and CDO target pages are dynamically generated		#
# 	from axaf_ocat, but index for searching is updated nightly			#
# 											#
# 	Script written by John Hayes: jhayes@head-cfa.harvard.edu			#
# 	extensively modified by Roy Kilgard: rkilgard@head-cfa.harvard.edu		#
# 	29 August 2000  : added searcy by obs. cycle					#
# 	31 October 2000 : added search by type=DDT, print date observed (really		#
#    	soe_st_sched_date) to output table, fixed comma-separated search		#
# 											#
# 	modified also by Miriam Krauss: miriam@head-cfa.harvard.edu			#
# 	26 January 2001  : added link to Processing Status page				#
# 	26 February 2001 : added Simbad name resolving feature				#
#											#
#########################################################################################

#
#---- set directory paths : updated to read from a file (02/25/2011)
#

open(IN, '/data/udoc1/ocat/Info_save/dir_list');
while(<IN>){
        chomp $_;
        @atemp    = split(/:/, $_);
        $atemp[0] =~ s/\s+//g;
        if($atemp[0] =~ /obs_ss/){
                $obs_ss   = $atemp[1];
        }elsif($atemp[0]  =~ /pass_dir/){
                $pass_dir = $atemp[1];
        }elsif($atemp[0]  =~ /htemp_dir/){
                $temp_dir = $atemp[1];
        }elsif($atemp[0]  =~ /too_dir/){
                $data_dir = $atemp[1];
        }elsif($atemp[0]  =~ /ocat_dir/){
                $real_dir = $atemp[1];
        }elsif($atemp[0]  =~ /test_dir/){
                $test_dir = $atemp[1];
        }elsif($atemp[0]  =~ /cus_dir/){
                $cus_dir  = $atemp[1];
        }
}
close(IN);

#
#--- Read in data from form and split into parameter/value pairs
#

read(STDIN, $temp, $ENV{'CONTENT_LENGTH'});

@pairs = split(/&/, $temp);

foreach $item(@pairs) {
	($key,$content) =  split(/=/,$item,2);
	$content        =~ tr/+/ /;
	$content        =~ s/%(..)/pack("c",hex($1))/ge;
	$fields{$key}   =  $content;
}

#
#--- Counters to check # of fields entered
#

&field_checker($fields{seqnbr});
&field_checker($fields{pronbr});
&field_checker($fields{piname});
&field_checker($fields{observ});
&field_checker($fields{target});
&field_checker($fields{obsid});
&field_checker($fields{ra});
&field_checker($fields{dec});
&field_checker($fields{radius});
&field_checker($fields{category});
&field_checker($fields{cycle});

$sciins_counter = 0; 		#--- If a Science Instrument box is checked, this counter

#
#---- assures the field is only counted once, assuring the # of fields with
#---- something entered matches the # of matching fields
#

&field_checker_sciins($fields{sciins1});
&field_checker_sciins($fields{sciins2});
&field_checker_sciins($fields{sciins3});
&field_checker_sciins($fields{sciins4});

$mode_counter = 0; 		#--- If a ACIS Mode box is checked, this counter

#
#---- assures the field is only counted once, assuring the # of fields with
#---- something entered matches the # of matching fields
#

&field_checker_mode($fields{mode1});
&field_checker_mode($fields{mode2});

$gratin_counter = 0; 		#---- If a Grating box is checked, this counter

#
#---- assures the field is only counted once, assuring the # of fields with
#---- something entered matches the # of matching fields
#

&field_checker_gratin($fields{gratin1});
&field_checker_gratin($fields{gratin2});
&field_checker_gratin($fields{gratin3});

$type_counter = 0; 		#--- If a Type box is checked, this counter

#
#---- assures the field is only counted once, assuring the # of fields with
#---- something entered matches the # of matching fields
#

&field_checker_type($fields{type1});
&field_checker_type($fields{type2});
&field_checker_type($fields{type3});
&field_checker_type($fields{type4});
&field_checker_type($fields{type5});

$status_counter = 0; 		#--- If a Status box is checked, this counter

#
#---- assures the field is only counted once, assuring the # of fields with
#---- something entered matches the # of matching fields
#

&field_checker_status($fields{status1});
&field_checker_status($fields{status2});
&field_checker_status($fields{status3});
&field_checker_status($fields{status4});
&field_checker_status($fields{status5});
&field_checker_status($fields{status6});
&field_checker_status($fields{status7});

$joint_counter = 0; 		#--- If a Joint box is checked, this counter

#
#---- assures the field is only counted once, assuring the # of fields with
#---- something entered matches the # of matching fields
#

&field_checker_joint($fields{joint1});
&field_checker_joint($fields{joint2});
&field_checker_joint($fields{joint3});
&field_checker_joint($fields{joint4});
&field_checker_joint($fields{joint5});
&field_checker_joint($fields{joint6});
&field_checker_joint($fields{joint7});
&field_checker_joint($fields{joint8});
&field_checker_joint($fields{joint9});

#
#---- open up html document and print beginning of table
#

print "Content-type: text/html\n\n";

print '<html>';
print '<body BGCOLOR="#FFFFFF">';
print '<ul>';
print '<li>Clicking on the Sequence Number link will take you to the Detailed Target Information Page.';
print '<li>Clicking on the ObsID link (if active) will perform a Chandra Data Archive ADS search for ';
print 'papers relevent to that ObsID.';
print '<li>Clicking on the Status link (if active) will take you to the relevant Processing Status page. ';
print '</ul>';
print '<table border cellpadding=5>';
print '<tr><th align="left">Sequence Number</th>';
print '<th align="left">Proposal Number</th>';
print '<th align="left">Target</th>';
print '<th align="left">ObsID</th>';
print '<th align="left">Exposure Time</th>';
print '<th align="left">Status</th>';
print '<th align="left">Inst/Grat</th>';
print '<th align="left">PI</th>';
print '<th align="left">Observer</th>';
print '<th align="left">Type</th>';
print '<th align="left">Scheduled Obs Start Time</th>';
print '<th align="left">RA</th>';
print '<th align="left">Dec</th></tr>';

#
#---- Make sure a field is entered, if not return error message
#

if ($field_counter == 0) {		#---- $field_counter keeps track of # of entered fields

	print "<h2>Please enter a field.  If you wish to display all observations, ";
	print " you may do so by selecting all Science Instruments.</h2>";
    	print "<a href=\"https://icxc.harvard.edu/mta/CUS/Usint/search.html\">New Search</a>";
	exit(0);
}

#
#---- Use Simbad to get coordinates for object
#

if ($fields{simbad} && !$fields{target}) {
	$fields{simbad} = "";
}

if ($fields{simbad}) {
	&sim2coord($fields{target});
	$field_counter++;
}

#
#---- Convert hegidecimal coordinates to decimal for RA and Dec
#
if ($fields{ra} && !$fields{simbad}) {
    	&ra2deci($fields{ra});
}

if ($fields{dec} && !$fields{simbad}) {
	&dec2deci($fields{dec});
}

#
#---- Choose file to be opened depending on which sort method is selected
#

if ($fields{sorted} =~ /Sequence Number/) {

#
#---- Open the ObsCat database in the file sequence_sorted.out
#
	open (TABLE, "$obs_ss/sot_ocat.out");

} elsif ($fields{sorted} =~ /RA/) {

#
#---- Open the ObsCat database in the file ra_sorted.out
#
	open (TABLE, "$obs_ss/sot_ocat_ra.out");
}

#
#---- useful variables for science category and observing cycle
#

$cat   = $fields{category};
$cycle = $fields{cycle};

#
#---- Process each line as it is read in
#

FILE: 			#---- Name for while loop so next operator can talk about it
while (<TABLE>) {
	$counter = 0; 	#---- $counter keeps track of number of matching fields

#
#---- Split each line into its fields
#
	chomp $_;

    	($nothing,$obsid,$targid,$seq_nbr,$targname,$obj_flag,$object,$ra,$dec,$approved_exposure_time,$proposal_id,$grating,$instrument,$soe_st_sched_date,$type,$lts_lt_plan,$status,$PI_name,$Observer,$proposal_number,$proposal_title,$ao_string,$joint) = split /\^/, $_;

#
#---- remove white space from $obsid, $seq_nbr, $proposal_number, $targname, $status, 
#---- $approved_exposure_time, $PI_name, $Observer, $instrument, $grating, $type
#

	$obsid                  =~ s/\s+//g;
	$seq_nbr                =~ s/\s+//g;
	$proposal_number        =~ s/\s+//g;
	$targname               =~ s/\s+//g;
	$status                 =~ s/\s*(\w+(|\s)\w+)\s*/$1/;
	$approved_exposure_time =~ s/\s+//g;
	$PI_name                =~ s/\s+//g;
	$Observer               =~ s/\s+//g;
	$instrument             =~ s/\s*(\w+(|\s)\w+)\s*/$1/;
	$grating                =~ s/\s*(\w+(|\s)\w+)\s*/$1/;
	$type                   =~ s/\s*(\w+(|\s)\w+)\s*/$1/;
	$ao_string              =~ s/\s+//g;
	$joint                  =~ s/\s+//g;

#
#---- find matching fields and increment $counter
#

	$fields{seqnbr}   && &match_fields_range($seq_nbr, $fields{seqnbr});
	$fields{pronbr}   && &match_fields_range($proposal_number, $fields{pronbr});
	$fields{piname}   && &match_fields($PI_name, $fields{piname});
	$fields{observ}   && &match_fields($Observer, $fields{observ});
	$fields{target}   && &match_fields_target($targname, $fields{target});
	$fields{obsid}    && &match_fields_range($obsid, $fields{obsid});
	$fields{category} && &match_fields_cat($proposal_number, $cat, $seq_nbr);
	$fields{cycle}    && &match_fields_cycle($ao_string, $cycle);
	
	$fields{sciins1}  && &match_fields($instrument, $fields{sciins1});
	$fields{sciins2}  && &match_fields($instrument, $fields{sciins2});
	$fields{sciins3}  && &match_fields($instrument, $fields{sciins3});
	$fields{sciins4}  && &match_fields($instrument, $fields{sciins4});
	
	$fields{mode1}    && &match_fields_mode($exp_mode, $fields{mode1});
	$fields{mode2}    && &match_fields_mode($exp_mode, $fields{mode2});
	
	$fields{gratin1}  && &match_fields($grating, $fields{gratin1});
	$fields{gratin2}  && &match_fields($grating, $fields{gratin2});
	$fields{gratin3}  && &match_fields($grating, $fields{gratin3});
	
	$fields{type1}    && &match_fields($type, $fields{type1});
	$fields{type2}    && &match_fields($type, $fields{type2});
	$fields{type3}    && &match_fields($type, $fields{type3});
	$fields{type4}    && &match_fields($type, $fields{type4});
	$fields{type5}    && &match_fields($type, $fields{type5});

#
#---- status uses different subroutine because spacing is different (i.e. 
#---- "Partially Observed")
#

	$fields{status1} && &match_fields_status($status, $fields{status1});
	$fields{status2} && &match_fields_status($status, $fields{status2});
	$fields{status3} && &match_fields_status($status, $fields{status3});
	$fields{status4} && &match_fields_status($status, $fields{status4});
	$fields{status5} && &match_fields_status($status, $fields{status5});
	$fields{status6} && &match_fields_status($status, $fields{status6});
	$fields{status7} && &match_fields_status($status, $fields{status7});

#
#---- joint proposal flag
#
	$fields{joint1} && &match_fields_joint($joint, $fields{joint1}, $ao_string, 
				$hsttime, $noaotime, $xmmtime, $rxtetime, $vlatime, $vlbatime);
	$fields{joint2} && &match_fields_joint($joint, $fields{joint2}, $ao_string, 
				$hsttime, $noaotime, $xmmtime, $rxtetime, $vlatime, $vlbatime);
	$fields{joint3} && &match_fields_joint($joint, $fields{joint3}, $ao_string, 
				$hsttime, $noaotime, $xmmtime, $rxtetime, $vlatime, $vlbatime);
	$fields{joint4} && &match_fields_joint($joint, $fields{joint4}, $ao_string, 
				$hsttime, $noaotime, $xmmtime, $rxtetime, $vlatime, $vlbatime);
	$fields{joint5} && &match_fields_joint($joint, $fields{joint5}, $ao_string, 
				$hsttime, $noaotime, $xmmtime, $rxtetime, $vlatime, $vlbatime);
	$fields{joint6} && &match_fields_joint($joint, $fields{joint6}, $ao_string, 
				$hsttime, $noaotime, $xmmtime, $rxtetime, $vlatime, $vlbatime);
	$fields{joint7} && &match_fields_joint($joint, $fields{joint7}, $ao_string, 
				$hsttime, $noaotime, $xmmtime, $rxtetime, $vlatime, $vlbatime);
	$fields{joint8} && &match_fields_joint($joint, $fields{joint8}, $ao_string, 
				$hsttime, $noaotime, $xmmtime, $rxtetime, $vlatime, $vlbatime);
	$fields{joint9} && &match_fields_joint($joint, $fields{joint9}, $ao_string, 
				$hsttime, $noaotime, $xmmtime, $rxtetime, $vlatime, $vlbatime);

#
#---- for a coordinate search
#

	&coor_search($fields{ra}, $fields{dec}, $fields{radcho}, $fields{radius});

#
#---- if counters are equal print out entry (serach results are printed out here)
#

	if (($counter == $field_counter && $status ne 'canceled') 
			|| ($counter == $field_counter && $fields{status6})) {

		print "<tr><td><a href=\"http://cxc.harvard.edu/cgi-gen/mp/target.cgi?$seq_nbr\">$seq_nbr</a></td>";
		print "<td>$proposal_number</td>";
		print "<td>$targname</td>";

    		if (($status eq 'observed') || ($status eq 'archived') 
			|| ($status eq 'discarded') || ($status eq 'canceled')) {
#			print "<td>$obsid</a></td>";
			print "<td><a href=\"http://cxc.harvard.edu/cgi-gen/target_param.cgi?$obsid\">$obsid</a></td>";
		}else{
			print "<td><a href=\"https://icxc.harvard.edu/mta/CUS/Usint/ocatdata2html.cgi?$obsid\">$obsid</a></td>";
		}

    		if (($status eq 'unobserved') || ($status eq 'discarded') || ($status eq 'canceled')) {
			print "<td>$approved_exposure_time</td>";
			print "<td>$status</td>";
    		} else {
			print "<td>$approved_exposure_time</td>";
			print "<td><a href=\"/cgi-bin/op/op_status_table.cgi?field=ObsId&id=$obsid&out=long&tab_del=HTML\">$status</a></td>";
		}

		print "<td>$instrument/$grating</td>";
		print "<td>$PI_first $PI_name</td>";
		print "<td>$Obs_first $Observer </td>";
		print "<td>$type</td>";
		print "<td>$soe_st_sched_date</td>";

#
#---- Convert $ra from decimal to hms
#
		&deci2ra($ra);

#
#---- Convert $dec from decimal to dms
#
		&deci2dec($dec);

#
#---- Continue printing out entry
#
		print "<td>$ra</td>";
		print "<td>$dec</td></tr>";
	
		$error_counter++; 		#---- keep track of number of entries
    	}
 
}
  
#
#---- if no entries, print out error message
#

if ($error_counter == 0) {
	print "<h2>Sorry!  There are no entries which match the selected parameters.</h2>";
    	print "<a href=\"https://icxc.harvard.edu/mta/CUS/Usint/search.html\">New Search</a>";
    	exit(0);
}

#
#---- end html code
#

print "$error_counter observation(s) match your search criteria.<br>";
print "</table></body></html>";

################################################################################
### field_checker:  Counter to check # of fields entered                     ###
################################################################################

sub field_checker { 
    	if ($_[0]) {
		$field_counter++;
    	}
}

################################################################################
### field_checker_sciins: Counter to check # of fields entered for Science  ####
###                       Instrument					    ####
################################################################################

sub field_checker_sciins {
    	if (($_[0]) && ($sciins_counter == 0)){
		$field_counter++;
		$sciins_counter++;
    	}
}

################################################################################
### field_checker_mode: Counter to check # of fields entered for ACIS Mode  ####
################################################################################

sub field_checker_mode {
    	if (($_[0]) && ($mode_counter == 0)){
		$field_counter++;
		$mode_counter++;
    	}
}

################################################################################
### field_checker_gratin: Counter to check # of fields entered for Grating  ####
################################################################################

sub field_checker_gratin {
    	if (($_[0]) && ($gratin_counter == 0)){
		$field_counter++;
		$gratin_counter++;
    	}
}

################################################################################
### field_checker_type: Counter to check # of fields entered for Observation ###
###                     Type						     ###
################################################################################

sub field_checker_type {
    	if (($_[0]) && ($type_counter == 0)){
		$field_counter++;
		$type_counter++;
    	}
}

################################################################################
### field_checker_status:  Counter to check # of fields entered for          ###
### 			   Observation Status				     ###	
################################################################################

sub field_checker_status {
    	if (($_[0]) && ($status_counter == 0)){
		$field_counter++;
		$status_counter++;
    	}
}

################################################################################
### field_checker_joint: Counter to check # of fields entered for            ###
###                      Joint proposal					     ###
################################################################################

sub field_checker_joint { 
    	if (($_[0]) && ($joint_counter == 0)){
		$field_counter++;
		$joint_counter++;
    	}
}

################################################################################
### match_fields:  Finds matching fields and increments counters             ###
################################################################################

sub match_fields {
    	if ($_[0] =~ /.*$_[1].*/i) {
		$counter++;
    	}
}

################################################################################
### match_fields_mode: Finds matching fields and increments counters         ###
################################################################################

sub match_fields_mode {
    	if ($_[0] =~ /^$_[1].*/i) {
		$counter++;
    	}
}

################################################################################
### match_fields_cat:   Finds matching categories and increments counters    ###  
### 			needs to be 3rd digit of 0 matches 1 EXACTLY.        ###
###			Note, 2/23/02: added code that checks for NULL value ###
###			of proposal number (for cal observations).  	     ###
### 			This now checks the first digit in the sequence      ###
###			number against the first digit in the category; may  ###
###			result in some spurious matches but will err on the  ###
###			side of finding too much (better than missing some.) ###
################################################################################

sub match_fields_cat { 
    	if ($_[0] =~ /NULL/) {
		$ocatCat = substr($_[2], 0, 1);
		$myCat   = substr($_[1], 0, 1);

		if ($ocatCat eq $myCat) {
	    		$counter++;
		}
    	}
    	@propid = split ("", $_[0]);
    	$catt   = "$propid[2]$propid[3]";

    	if ($catt =~ /$_[1]/i) {
		$counter++;
    	}
}

################################################################################
### match_fields_cycle: Finds matching observing cycle                       ###
################################################################################

sub match_fields_cycle {
    	if ($_[0] =~ /$_[1]/) {
		$counter++;
    	}
}

################################################################################
### match_fields_status: Finds matching fields and increments counters       ###
###                      for status					     ###
################################################################################

sub match_fields_status {
    	if ($_[0] =~ /^$_[1]/i) {
		$counter++;
    	}
}

################################################################################
### match_fields_joint: Finds matching fields and increments counters for joint#
################################################################################

sub match_fields_joint {
    	if ($_[2] eq "05") {
		if ($_[0] eq "HST"){
	    		$_[0] = "HST-CXO"
		}	    
		if ($_[0] eq "XMM"){
			$_[0] = "XMM-CXO"    
		}
	}	    
    	if ($_[0] eq $_[1]) {
#
#----- filter out if joint telescope time is not approved
#
		if ($_[2] eq "04" || $_[2] eq "05") {
	    		return if ($_[0] eq "NOAO"     and ($_[4] =~ /NULL/));
	    		return if ($_[0] eq "HST-CXO"  and ($_[3] =~ /NULL/));
	    		return if ($_[0] eq "NOAO+HST" and ($_[3] =~ /NULL/) and ($_[4] =~ /NULL/));
	    		return if ($_[0] eq "XMM-CXO"  and ($_[5] =~ /NULL/));
	    		return if ($_[0] eq "RXTE"     and ($_[6] =~ /NULL/));
	    		return if ($_[0] eq "VLA"      and ($_[7] =~ /NULL/));
	    		return if ($_[0] eq "VLBA"     and ($_[8] =~ /NULL/));
		}
		$counter++;
    	}
}

#
###### working section for name resolving....
#

################################################################################
### match_fields_target: Finds matching targets and increments counters      ###
###                      for statuts					     ###
################################################################################

sub match_fields_target {
    	$from_ocat = $_[0];
    	$from_form = $_[1];
    	$from_form =~ s/\s+//g; 

    	if ($from_ocat =~ /^$from_form/i) {
		$counter++;
    	} elsif ($from_ocat eq $from_form) {
		$counter++;
    	}
}

################################################################################
### match_fields_range: Finds matching fields and increments counters for    ###
###			 range searches: used for ObsID, SeqNum, and PropNum ###
################################################################################

sub match_fields_range {

#
#----  Remove white space from input(s), rename variables:
#
	my($ocat) = $_[0];
	my($form) = $_[1];
	$form     =~ s/\s+//g;

	if ($form =~ /^\d+--\d+$/) {
		($first, $last) = split(/--/, $form);
		if (($ocat >= $first) && ($ocat <= $last)) {
			$counter++;
		}
	}
#
#----  May be a comma-delimited list- works for single entries as well
#
    	else { @array = split(/,/, $form);
		foreach $arg (@array) {
#
#---- If there's a wildcard at the end of the string
#
	    		if ($arg =~ /^\d+\*$/) {
				$arg =~ s/\*//i;
				if ($ocat =~ /^$arg.*$/i) {
		    			$counter++;
				}
	    		}
#
#----- If there's a wildcard at the beginning of the string
#
	    		elsif ($arg =~ /^\*\d+$/) {
				$arg =~ s/\*//;
				if ($ocat =~ /^.*$arg$/i) {
		    			$counter++;
				}
	    		}
#
#---- If there's a wildcard at each end of the string
#
	    		elsif ($arg =~ /^\*\d+\*$/) {
				$arg =~ s/\*//g;
				if ($ocat =~ /^.*$arg.*$/i) {
		    			$counter++;
				}
	    		}
	    		elsif ($ocat == $arg) {
				$counter++;
	    		}
		}
    	}
}

################################################################################
### ra2deci: Convert $ fields{ra} from hms to decimal	                     ###
################################################################################

sub ra2deci {
    	($hour,$minute,$second) = split(/:|\s/,$fields{ra});
    	$second     = $second / 60;
    	$minute     = $minute + $second;
    	$minute     = $minute / 60;
    	$hour       = $hour + $minute;
    	$fields{ra} = $hour * 15;
}

################################################################################
### dec2deci:  Convert $ fields{dec} from dms to decimal                     ###
################################################################################

sub dec2deci {
    	($degree,$minute,$second) = split(/:|\s/,$fields{dec});
    
    	if ($degree =~ /-/) { # set sign
        	$sign = -1;
        	$degree *= -1;
    	} else {
		$sign = 1;
	}

    	$second      = $second / 60;
    	$minute      = $minute + $second;
    	$minute      = $minute / 60;
    	$degree      = $degree + $minute;
    	$fields{dec} = $degree * $sign;
}

################################################################################
### coor_search: Searches on coordinates - both exact and radius searches    ###
################################################################################

sub coor_search {
    	if ($fields{radcho} && !$fields{radius}) {
		$fields{radcho} = "";
    	}

#
#---- for exact search
#

    	if ($fields{ra} =~ /\w+/  && $fields{dec} =~ /\w+/  && !$fields{radcho}) { 
		$ra_radius = (0.066666666667)/cos($fields{dec}*0.0174532925199) unless $fields{dec}==90;

		if (($fields{ra} <= ($ra + $ra_radius)) && ($fields{ra} >= ($ra - $ra_radius)) 
			&& ($fields{dec} <= ($dec + (0.066666666667))) 
			&& ($fields{dec} >= ($dec - (0.066666666667)))){
	    		$counter++;
	    		$counter++;
		}
    	}

#
#---- for radius searches
#

    	if ($fields{radcho} eq 'degrees') {

		if ($fields{ra} =~ /\w+/ && $fields{dec} =~ /\w+/  && $fields{radius}) {
	    		$ra_radius = $fields{radius}/cos($fields{dec}*0.0174532925199) unless $fields{dec}==90;

	    		if (($fields{ra} <= ($ra + $ra_radius)) && ($fields{ra} >= ($ra - $ra_radius)) 
				&& ($fields{dec} <= ($dec + $fields{radius})) 
				&& ($fields{dec} >= ($dec - $fields{radius}))){
				$counter++;
				$counter++;
				$counter++;
	    		}
		}
    	} elsif ($fields{radcho} eq 'arcmin') {

		if ($fields{ra} =~ /\w+/  && $fields{dec} =~ /\w+/  && $fields{radius}) {
	    		$ra_radius = $fields{radius}/cos($fields{dec}*0.0174532925199) unless $fields{dec}==90;

	    		if (($fields{ra} <= ($ra + ($ra_radius/60))) && ($fields{ra} >= ($ra - ($ra_radius/60))) 				&& ($fields{dec} <= ($dec + ($fields{radius}/60))) 
				&& ($fields{dec} >= ($dec - ($fields{radius}/60)))){
				$counter++;
				$counter++;
				$counter++;
	    		}
		}
    	}
}

################################################################################
### deci2ra: Convert $ra from decimal to hms                                 ###
################################################################################

sub deci2ra {
    	$hh = int($ra/15);
    	$mm = 60 * ($ra / 15 - $hh);
    	$ss = 60 * ($mm - int($mm));

    	if ($ss >= 59.95) {
		$ss  = 0.0;
		$mm += 1.0;
    	}
    	$mm = int($mm);

    	if ($mm >= 59.5) {
		$mm = 0.0;
		$hh += 1.0;
    	}
    	$ra = sprintf("%02d:%02d:%05.2f", $hh, $mm, $ss);
}

################################################################################
### deci2dec:  Convert $dec from decimal to dms                              ###
################################################################################

sub deci2dec {

#
#--- set sign
#
    	if ($dec < 0) {
		$sign = "-";
		$dec *= -1;
    	} else {
		$sign = "+";
	}

    	$dd = int($dec);
    	$mm = 60 * ($dec - $dd);
    	$ss = 60 * ($mm - int($mm));

    	if ($ss >= 59.95) {
		$ss  = 0.0;
		$mm += 1.0;
    	}
    	$mm = int($mm);

    	if ($mm >= 59.5) {
		$mm  = 0.0;
		$dd += 1.0;
    	}
    	$dec = sprintf("%.1s%02d:%02d:%05.2f", $sign, $dd, $mm, $ss); 
}

################################################################################
### sim2coord: Gets the coordinates from Simbad                              ###
################################################################################

sub sim2coord {
###    	$coords    = `/opt/local/bin/expect /proj/web-cxc/cgi-gen/clicoord.tcl $fields{target}`;
    	$coords    = `/opt/local/bin/expect $obs_ss/clicoord.tcl $fields{target}`;
    	@lines     = split("\n", $coords);
    	$coordline = $lines[3];

    	if ($coordline =~ /B2000/){
		@radec       = split(" ",$coordline);
		$fields{ra}  = $radec[3];
		$fields{dec} = $radec[4];
    	} else {
		print "<h2>Simbad could not resolve coordinates.</h2>";
		print "<a href=\"https://icxc.harvard.edu/mta/CUS/Usint/search.html\">New Search</a>";
		exit(0);
    	}

    	$fields{target} = "";
}
    













