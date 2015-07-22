#!/usr/bin/perl

BEGIN
{
#    $ENV{SYBASE} = "/soft/SYBASE_OCS15.5";
    $ENV{SYBASE} = "/soft/SYBASE15.7";
}

use DBI;
use DBD::Sybase;
use CGI qw/:standard :netscape /;

use Fcntl qw(:flock SEEK_END); # Import LOCK_* constants

###############################################################################
#
#HISTORY OF UPDATES
#-------------------
# This is a first-draft script to dynamically create a page based on obsid.
# It works, as far as I can tell....
# Note:  Currently, this script MUST use the above version of perl and contain
# all the use statements above.
# Ok, that's probably not true - I don't think I'm using DBlib at all.
# It is more complex to use CTlib, but I'm told by the experts that
# DBlib is going to be discontinued.
# -Roy Kilgard, April 2000
#
# Some new inputs are added by T. Isobe (01 May, 2001)
#
# Preference selection added/ACIS window filter function modified
#                       T. Isobe (27 Jul. 2001)
#
# bugs related comments and remarks fixed (06 Sep. 2001)
# uninterrupt added (22 Jul. 2002)
#
# added several more entries (27 Aug. 2002)
# multitelescope  observatories
# From TOO database   type  trig  start,  stop  followup,  remarks
# proposal_hst, proposal_noao, proposal_xmm
#
# Major modifications are performed (29 Apr. 2003). Changes are:
#       1. submit.cgi and oredit.cgi are now absorbed into ocatdata2html.cgi.
#       2. ordr for time, roll, and window constraints are now able to handle
#          mulitiple ranks (upto 30).
#       3. tstart and tstop input time format are more flexible.
#       4. input error checking mechanism are updated.
#
#
# Adjusted for AO5 input/Sherry's requests, and several bugs fixed
# (15 Aug 2003)
#	1. added passowrd entry, special user status added
#
# The script is modified to accomodate both user and usint use, and
# several updates are done. The user version is moved to a secure are
#  (Oct 2, 2003)
#
# New display format is added
#   (Mar 23, 2004)
#
# Added automatic acis window constraints setting for the case energy filter lowest 
# energy is > 0.5 keV.
# General cleaning up of the code 
#   (June 15, 2006)
#
# Added: a new user sign off capacity (ask USINT to do everything)
#	 CCD selection has OPT1-5.
#   (Jul 20, 2006)
# 
# A fully updated to adjust AO8 requirements.
#   (Sep 28, 2006)
#
# Double entry revision # bug is fixed.
#   (Mar 20, 2007)
#
# sending email to MP only when the obs. is on OR list, and there are actually
# some modificaiton.
#   (Jul 17, 2007)
#
#  1. sub array type is now use subarray: yes/no
#
#  2. following entires are removed (no reading from DB and no display on the page):
#     bias_after, frequency, bias_request, fep, standard_chips, subarray_frame_time, bias_after
#   (Sep. 19, 2007)
#
#
#  canceled/archived/discarded/observed observation displays the status at the top.
#  it also does not show the link to thoese observations at monitoring constraint.
#  (Oct. 29, 2007)
#
#  for usint version, only usint users now can have full access to the file. All others ca
#  read, but edit
#  (Dec. 06, 2007)
#
#   description of the note changed
#   Aimpoint    1/8   1/4   1/2
#
#   ACIS-I    897   769   513
#   ACIS-S    449   385   257"
#   (Dec. 18, 2007)
#
#  all perl/cgi/html links are now have absolute pathes
#  (Feb. 05, 2008)
#
#  environment setting changed:
#	/proj/DS.ots/perl-5.10.0.SunOS5.8/bin/perl
#	 $ENV{SYBASE} = "/soft/SYBASE_OCS15"
#  (May 19, 2008)
#
#  a new value added: multitelescope_interval
#  (Sept 02, 2008)
#
#  si mode is required when submitted for approval
#  (Sept. 22, 2008)
#
#  when group id exists pre_id etc. can be visible, but not editable. 
#  if no group id or monitoring flag, all "pre" paramters will be null.
#  (Nov. 04, 2008)
#  a bug related to above is fixed.
#  (Nov 20, 2008)
#
#  A warning "CDO approval is requred" is changed to "Has CDO approved this instrument change?"
#  (Nov 24, 2008)
#
# https://icxc.harvard.edu/mta/CUS/ ---> https://icxc.harvard.edu/cus/index.html
#  (Aug 26, 2009)
#
# sub oredit is exported to oredit_sub.perl to increase speed and avoid double entiries of obsid
#  (Sep 23, 2009)
#
# dss/rosat/rass image access path fixed
#  (Oct 27, 2009)
#
# corrected ra/dec conversion problem./remvoed nohup option when running oredit_sub.perl
#  (Dec 07, 2009)
#
# duplicated start_form() tags are removed
#  (Dec 09, 2009)
#
#
#  perl pointing is changed from: /proj/DS.ots/perl-5.10.0.SunOS5.8/bin/perl 
#	                      to: /soft/ascds/DS.release/ots/bin/perl 
#  to accomodate Solaris 10.
#   (Apr 23, 2010)
#
#  determination of AO # is updated; it is now obtained from "prop_info", not from "target"
#   (Jul 06, 2010)
#
#  added notification of a wrong user name login attempt
#   (Jul 13, 2010)
#
#  special window bug fixed (no include option, if a new window is added)
#   (Jul, 20, 2010)
#
# oredit_sub.perl is re-integrated as sub oredit_sub, and some change of sccs routine to 
# shorten the potential hang up.
#  (Aug 09, 2010)
#
# ACIS Window Constraints format is updated. now you can assign "ordr", too.
#  (Oct 28, 2010)
#
# PHOTOMETORY_FLAG bug fixed
#  (Nov 22, 2010)
#
# a bug related to a left over junk file fixed
#  (Feb 24, 2011)
#
# directory paths is now read from a file kept in the info site
#  (Mar 01, 2011)
#
# updates_table.list permission change to 755
#  (Mar 08, 2011)
#
# multiple_spectral_lines and spectra_max_count are added to ACIS parameters
# (Mar 31, 2011)
#
# Min Int/Max Int names are modified with <br />(pre_min_lead)
# (Apr. 13 2011)
#
# EXTENDED_SRC is added / some descriptions are updated
# (Aug. 01, 2011)
#
# LOWER_THRESHOLD, PHA_RANGE etc  modified, and check mechanism updated.
# (Aug. 05, 2011)
#
# New requirements for ACIS-I/None Grating case check added.
# (Sep. 23, 2011)
#
# Time constraint and Roll Constraint now have null rank removing capacity
# (Oct, 20, 2011)
#
# sql reading update: $sqlh1 = $dbh1->prepare(qq(select soe_roll from soe where obsid=$obsid and unscheduled='N'));
# (Oct, 27, 2011)
#
# sccs is now pointing to /usr/local/bin/
# (Aug 28, 2012)
#
# sccs is replaced by flock
# (Oct 01, 2012)
#
# mailx -r option removed
# (Oct 02, 2012)
#
# time, order, and acis window constraint setting changed
# (Oct 18, 2012)
#
# flock bug fixed
# (Nov 28, 2012)
#
# ocat data value conversion problem corrected (line starting 9140 as of Nov 29, 2012)
# (Nov 29, 2012)
#
# window_flag/roll_flag bug fixed
# (Dec 06, 2012)
#
# https://cxc version
# (Mar 26, 2013)
#
# link to cdo changed to http://icxc.harvard.edu
# (Apr 03, 2013)
#
# mailx's  -r$cus_email option removed
# (Jun 27, 2013)
#
# BEP_PEAK option changed (F, VF, F+B, G ---  default: F)
# (Sep, 23, 2013)
#
# Link to PSPC page removed
# (Sep 25, 2013)
#
# Highest Energy display added
#  (Nov 14, 2013)
#
# BEP_PACK now has "NULL" option when the instrument is HRC
#  (Nov 14, 2013)
#
# Preference/Constraint change warning capacity added
#  (Nov 18, 2013)
#
# Definition of "Use Subarray" is modified 
# ACIS-I :	897	128	769	256	513	original
# ACIS-I :	897	128	768	256	513	
#  (Jan 09, 2014)
#
# Added a checking mechanism which notify REMARKS and COMMENTS are delted
#  (Feb 25, 2014)
#
# Input for Roll and Roll_tolerance is now limited to digit
#  (May 21, 2014)
#
# If the original value is <blank>, "Blank" will be desplayed on output
#  (Jun 12, 2014)
# Planned Roll has now have a range. 
#  (Aug 26, 2014)
#
# SYBASE link update (/soft/SYBASE15.7)
#  (Sep 23, 2014)
#
# Note to window constraint (exclusion) added.
#  (Oct 30, 2014)
# 
# Exposure Time is now not editable
# (Dec 21, 2014)
#
# CDO warning on change of Y/Z det offset added (>10arcmin)
# (Feb 13, 2015)
#
# Reordering the ranks of aciswin in increasing order
# (Jul 17, 2015)
#
#  /soft/ascds/DS.release/ots/bin/perl ---> /usr/bin/perl  (accessible from cxc)
#
#-----Up to here were done by t. isobe (tisobe@cfa.harvard.edu)-----
#
# ----------
# sub list:
# ---------
#   password_check: 	open a user - a password input page
#
#   match_user: 	check a user and a password matches
#
#   special_user: 	check whether the user is a special user
#
#   pi_check: 		check whether pi has an access to the datau
#
#   pass_param: 	passing cgi parameter values to the next window
#
#   read_databases:	 read out values from databases
#
#   data_close_page: 	display data for closed observation
#
#   data_input_page: 	create data input page--- Ocat Data Page
#
#   pre_submit: 	preparing the data for submission
#
#   chk_entry: 		calling entry_test to check input value range and restrictions
#
#   entry_test: 	check input value range and restrictions
#
#    restriction_check: check special restrictions for input
#
#   print_clone_page: 	print comment entry for clone case
#
#   read_range: 	read conditions for values
#
#   read_user_name: 	reading authorized user names
#
#   user_warning: 	warning a user, a user name mistake
#
#   submit_entry: 	check and submitting the modified input values
#
#   read_name: 		read descriptive name of database name
#
#   find_name: 		match database name to descriptive name
#
#   oredit: 		update approved list, updates_list, updates data, and send out email
#
#   oredit_sub:         sub handle actual update of oredit (re-integrated on Aug 09, 2010)
#
#   mod_time_format: 	convert and devide input data format
#
#   lts_date_check:     check ltd_date is in 30 days or not 
#
#   series_rev:         getting mointoring observation things
#
#   series_fwd:         getting monitoring observation things
#
#   find_planned_roll:  get planned roll from mp web page
#
#   rm_from_approved_list:  remove entry from approved list
#
#   send_mail_to_usint:     sending out full support request email to USINT
#
#   mail_out_to_usint:      sending email to USINT
#
#   send_email_to_mp:       sending email to MP if the obs is in an active OR list
#
#   keep_ccd_selection_record: keep ccd selectionin record. -----this is not used anymore 9/27/06
#
#   find_usint:                find an appropriate usint email address for a given obs.
#
#
# ----------------------------------
# data/files needed for this script
# ----------------------------------
#
#  $pass_dir/.htpasswd: 		user/password list.
#
#  $pass_dir/.htgroup:			read user names
#
#  $pass_dir/cxc_user:			cxc user list
#
#  $pass_dir/user_email_list: 		a list of user/usint list
#
#  $pass_dir/usint_users:     		a list of usint persons
#
#  $obs_ss/access_list:			a list of scheduled/unobserved list
#
#  $obs_ss/scheduled_obs_list:		a list of MP scheduled observations 
#
#  $obs_ss/mp_edit_permit		a list of MP scheduled observations, but have a eidt permission
#
#  $obs_ss/sot_ocat.out:		a list of all observations listed on sql database
#
#  $data_dir/ocat_values:		a file contains codtion/restriction for the param
#
#  $data_dir/name_list:			a file contains descritive names for params
#
#  $ocat_dir/approved:			an approved obsid list
#
#  $ocat_dir/updates_table.list		a file contains updated file list
#
#  $ocat_dir/updates/$obsid.*		database to save updated information
#
#  $ocat_dir/cdo_warning_list		a file containings a list of obsid/version of large coordinate shifts
#
#  $temp_dir:				a dirctory where a temporary files are saved
#  
###############################################################################

###############################################################################
#---- before running this script, make sure the following settings are correct.
###############################################################################

#
#--- set  " " <blank> value 
#
$blank  = '&lt;Blank&gt;';
$blank2 = '<Blank>';

#
#---- if this is usint version, set the following param to 'yes', otherwise 'no'
#

$usint_on = 'yes';			##### USINT Version
#$usint_on = 'no';			##### USER Version
#$usint_on = 'test_yes';			##### Test Version USINT
#$usint_on = 'test_no';			##### Test Version USER

#
#---- set a name and email address of a test person
#

$test_user  = 'isobe';
$test_email = 'isobe@head.cfa.harvard.edu';

#$test_user  = 'mta';
#$test_email = 'isobe@head.cfa.harvard.edu';

#$test_user  = 'brad';
#$test_email = 'brad@head.cfa.harvard.edu';

#$test_user  = 'swolk';
#$test_email = 'swolk@head.cfa.harvard.edu';

#
#--- sot contact email address
#

$sot_contact = 'swolk@head.cfa.harvard.edu';

#
#---- if CDO assist needed, send email to the following address
#

####$cdo_email = 'wink@head.cfa.harvard.edu';


#
#--- $mtaobs is a super observer and s/he can access to all GTO/GO observations as an observer
#--- (useful for testing none-usint user version of ocat data page)
#

$mtaobs     = 'mtadude';

#
#--- cus email address
#

$cus_email  = 'cus@head.cfa.harvard.edu';

#
#---- set directory paths : updated to read from a file (02/25/2011)
#

#open(IN, '/data/udoc1/ocat/Info_save/dir_list');
#open(IN, './ocat/Info_save/dir_list');
#open(IN, '/proj/web-cxc-dmz/htdocs/mta/CUS/Usint/ocat/Info_save/dir_list');
open(IN, '/data/mta4/CUS/www/Usint/ocat/Info_save/dir_list');

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
	}elsif($atemp[0]  =~ /data_dir/){
		$data_dir = $atemp[1];
	}elsif($atemp[0]  =~ /ocat_dir/){
		$real_dir = $atemp[1];
	}elsif($atemp[0]  =~ /test_dir/){
		$test_dir = $atemp[1];
	}
}
close(IN);

				
#
#--- if this is a test case, use the first directory, otherwise use the real one
#

if($usint_on =~ /test/i){
	$ocat_dir = $test_dir;
}else{
	$ocat_dir = $real_dir;
}

#
#--- set html pages
#

$usint_http   = 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/';	#--- web site for usint users
#$usint_http   = 'https://cxc.cfa.harvard.edu/cus/index.html';	#--- web site for usint users
$obs_ss_http  = 'https://cxc.cfa.harvard.edu/cgi-bin/obs_ss/';	#--- web site for none usint users (GO Expert etc)
$test_http    = 'http://asc.harvard.edu/cgi-gen/mta/Obscat/';	#--- web site for test

$mp_http      = 'http://asc.harvard.edu/';			#--- web site for mission planning related
$chandra_http = 'http://cxc..harvard.edu/';			#--- chandra main web site
$cdo_http     = 'http://icxc.cfa.harvard.edu/cgi-bin/cdo/';	#--- CDO web site

############################
#----- end of settings
############################

#------------------------------------------------------------------------
#--- find obsid requested if there are group id, it may append a new name
#------------------------------------------------------------------------

$temp  = $ARGV[0];
chomp $temp;

#
#--- removing potentially harmful caharacters
#

@atemp = split(//, $temp);
$tline = '';
foreach $ent (@atemp){
	if($ent =~ /\w/ || $ent =~ /\./){
		$tline = "$tline"."$ent";
	}
}

@atemp = split(/\./, $tline);	
$obsid = $atemp[0];		
@otemp = split(//, $obsid);

if($otemp[0] eq '0'){
	shift @otemp;
	$line = '';
	foreach $ent (@otemp){
		$line = "$line"."$ent";
	}
	$obsid = $line;
}

#----------------------------------------------------------------
#--- a parameters to pass on: an access password and a user name
#--- these are appended only when the script wants to open up
#--- another obsid ocat page (e.g., group observations)
#----------------------------------------------------------------

$pass      = $atemp[1];
$submitter = $atemp[2];
$user      = $atemp[2];

#-------------------------------------------------------------------
#---- read approved list, and check whether this obsid is listed.
#---- if it does, send warning.
#-------------------------------------------------------------------

open(FH, "$ocat_dir/approved");
$prev_app = 0;

#--------------------------------------------------------------------
#----- here are non CXC GTOs who have an access to data modification.
#--------------------------------------------------------------------

$no_sp_user    = 2;				#--- number of special users

@special_user  = ("$test_user",  'mta');
@special_email = ("$test_email", "$test_email");

if($usint_on =~ /yes/){
	open(FH, "$pass_dir/usint_users");
	while(<FH>){
		chomp $_;
		@atemp = split(//,$_);
		if($atemp[0] ne '#'){
			@btemp = split(/\s+/,$_);
			push(@special_user,  $btemp[0]);
			push(@special_email, $btemp[1]);
		}
	}
}

#-------------------------------
#---- read a user-password list
#-------------------------------

open(FH, "<$pass_dir/.htpasswd");

%pwd_list = ();                         	# save the user-password list
while(<FH>) {
        chomp $_;
        @passwd = split(/:/,$_);
        $pwd_list{"$passwd[0]"} = $passwd[1];
        push(@user_name_list, $passwd[0]);
}
close(FH);

#---------------------------------------------------
#---- read cookies for a user name and the password
#---------------------------------------------------

#-----------------------------------------
#--- treat special charactors for cookies
#-----------------------------------------

@Cookie_Encode_Chars = ('\%', '\+', '\;', '\,', '\=', '\&', '\:\:', '\s');

%Cookie_Encode_Chars = ('\%',   '%25',
                        '\+',   '%2B',
                        '\;',   '%3B',
                        '\,',   '%2C',
                        '\=',   '%3D',
                        '\&',   '%26',
                        '\:\:', '%3A%3A',
                        '\s',   '+');

@Cookie_Decode_Chars = ('\+', '\%3A\%3A', '\%26', '\%3D', '\%2C', '\%3B', '\%2B', '\%25');

%Cookie_Decode_Chars = ('\+',       ' ',
                        '\%3A\%3A', '::',
                        '\%26',     '&',
                        '\%3D',     '=',
                        '\%2C',     ',',
                        '\%3B',     ';',
                        '\%2B',     '+',
                        '\%25',     '%');

#----------------
#--- read cookies
#----------------

$submitter = cookie('submitter');
$pass_word = cookie('pass_word');

#-------------------
#--- de code cookies
#-------------------
foreach $char (@Cookie_Decode_Chars) {
        $submitter  =~ s/$char/$Cookie_Decode_Chars{$char}/g;
        $pass_word  =~ s/$char/$Cookie_Decode_Chars{$char}/g;
}

#-----------------------------------------------
#---- find out whether there are param passed on
#-----------------------------------------------

$submitter = param('submitter') || $submitter;
$pass_word = param('password')  || $pass_word;

#-------------------
#--- refresh cookies
#-------------------

$en_submitter = $submitter;
$en_pass_word = $pass_word;

foreach $char (@Cookie_Encode_Chars) {
        $en_submitter   =~ s/$char/$Cookie_Encode_Chars{$char}/g;
        $en_pass_word   =~ s/$char/$Cookie_Encode_Chars{$char}/g;
}

$user_cookie = cookie(-name    => 'submitter',
                      -value   => "$en_submitter",
                      -path    => '/',
                      -expires => '+8h');
$pass_cookie = cookie(-name    => 'pass_word',
                      -value   => "$en_pass_word",
                      -path    => '/',
                      -expires => '+8h');

#-------------------------
#---- new cookies worte in
#-------------------------

print header(-cookie=>[$user_cookie, $pass_cookie], -type => 'text/html');

print start_html(-bgcolor=>"white", -title=>"Ocat Data Page");     # this says that we are starting a html page

#-----------------------------------------------------------------
##----- descriptions of each entry is presented in JavaScript area.
#-----------------------------------------------------------------

print <<ENDOFHTML;

<script language="JavaScript">
<!-- hide me

var seq_nbr = '<font color=blue><b>Sequence Number</b></font><br>'
		+ '<font color=#008080>seq_nbr (target)</font><br>'
		+ 'Sequence # of the particular observation<br>'
	        + 'This is a bookkeeping value and rarely changed<br>';

var status  = '<font color=blue><b>Status</b></font><br>'
		+ '<font color=#008080>status (target)</font><br>'
		+ ' Status of observation<br>'
	        + 'This is a bookkeeping value and rarely changed<br>';

var obsid   = '<font color=blue><b>ObsID#</b></font></br>'
		 + '<font color=#008080>obsid (target)</font><br>'
		 + 'ID # used in ObsCat database and on-board Chandra<br>'
		 + 'A one to one map with individual observations<br>';

var proposal_number = '<font color=blue><b>Proposal Number</b></font><br>'
		 + '<font color=#008080>prop_num (prop_info)</font><br>'
		 + 'Proposal Number. The proposal from which this<br>'
		 + 'and related observations stemmed<br>';

var proposal_title = '<font color=blue><b>Proposal Title</b></font><br>'
		 + '<font color=#008080>title (prop_info)</font><br>'
		 + 'Title of proposal<br>';

var group_id = '<font color=blue><b>Group ID</b></font><br>' 
		 + '<font color=#008080>group_id (target)</font><br>'
		 + 'Group ID of the observation<br>'
		 + 'Bookkeeping tool only used for linked observations<br>';

var obs_ao_str = '<font color=blue><b>Obs AO Status</b></font><br>'
		 + '<font color=#008080>obs_ao_str (target)</font><br>'
		 + 'AO status of the observation. What AO the observation is assigned to.<br>';

var targname = '<font color=blue><b>Target Name</b></font><br>'
		 + '<font color=#008080>targname (target)</font><br>'
		 + 'Normal name for the target. Taken from prposal.<br>';

var si_mode = '<font color=blue><b>SI Mode</b></font><br>'
		 + '<font color=#008080>si_mode (target)</font><br>'
		 + 'This code is used by the CXC in command generation<br>'
		 + 'to select the appropriate instrument configuration<br>'
		 + 'commands from the controlled Operations Data Base in<br>'
		 + 'order to configure the observation as is specified.<br>'
		 + 'Observers do not use this parameter.<br>';

var aca_mode = '<font color=blue><b>ACA Mode</b></font><br>'
		 + '<font color=#008080>si_mode (target)</font><br>'
		 + 'This code is used by the CXC in command generation<br>'
		 + 'to select the appropriate instrument configuration<br>'
		 + 'commands from the controlled Operations Data Base in<br>'
		 + 'order to configure the observation as is specified.<br>'
		 + 'Observers do not use this parameter.<br>';

var instrument = '<font color=blue><b>Instrument</b></font><br>'
		 + '<font color=#008080>instrument (target)</font><br>'
		 + 'Specifies which detector will be on the optical axis during the observation.<br>'
		 + '<font color=red> If an instruement change (ACIS<--->HRC) is required, CDO approval is needed</font><br>'
		 + '<font color=green> Value Range: ACIS-S, ACIS-I, HRC-S HRC-I</font><br>';
		
var grating = '<font color=blue><b>Grating</b></font><br>'
		 + ' <font color=#008080>grating (target)</font><br>'
		 + 'Specifies which grating to use. The default is NONE which specifies no grating (direct imaging)<br>'
		 + '<font color=red>All changes require CDO approval.<br>'
		 + 'Adding a grating requires count rate, and 1st Order Rate</font><br>'
		 + '<font color=green> Value Range: NONE, HETG, LETG</font><br>';
		
var type = '<font color=blue><b>Type</b></font><br>'
		 + '<font color=#008080>type (target)</font><br>'
		 + 'Type of Observation.<br>'
	 	 + '<font color=green>Value Range: GO, TOO, GTO, CAL, DDT, CAL_ER, ARCHIVE, CDFS</font><br>';

var PI_name = '<font color=blue><b>PI Name</b></font><br>'
		 + '<font color=#008080>person_short (prop_info)</font><br>'
		 + 'Last name of Principal Investigator<br>';

var coi_contact = '<font color=blue><b>Observer</b></font><br>'
		  + '<font color=#008080>coi_contact (prop_info)</font><br>'
		  + 'Last name of Observer if it is different from that of PI<br>'
	          + 'It is the OBSERVER, not the PI who is responsible for the observtion setup<br>';

var approved_exposure_time = '<font color=blue><b>Exposure Time</b></font><br>'
		 + '<font color=#008080>approved_exposure_time (target)</font><br>'
		 + ' Exposure time for the Obsid. If your total time is higher than this, <br>';
		 + 'it may have been split due to orbital constraints. <font color=red>If the User wants to <br>'
		 + 'to split the observation, this must be done through a separate CDO request</font><br>';

var rem_exp_time ='<font color=blue><b>Remaining Exposure Time</b></font><br>'
		 + '<font color=#008080>rem_exp_time (target)</font><br>'
		 + 'The remaining time which still must be scheduled on this <br>'
		 + 'target to give the observer the approved_exposure.<br>' 
		 + 'It is computed dynamically based on the mission planning and <br>'
		 + 'data analysis processes.<br>'
	         + 'If it is less than 20% of the approved time, additional obserations<br>'
		 + 'will not be performed<br>';

var joint = '<font color=blue><b>Joint Proposal</b></font><br>'
		 + '<font color=#008080>joint (prop_info)</font><br>'
	   	 + 'A flag for whether this observation is coordinated with another observatory.<br>'
		 + 'This is only for proposed and approved coordination. For post facto<br>'
		 + 'coordination, use the "Coordinated"<br>'
		 + 'field in the "Other Constraints" section or the "REMARLS" area<br>';

var prop_hst = '<font color=blue><b>HST Approved Time</b></font><br>'
		 + '<font color=#008080>hst_approved_time (prop_info)</font><br>'
		 + 'TAC approved HST time<br>';

var prop_noao = '<font color=blue><b>NOAO Approved Time</b></font><br>'
		 + '<font color=#008080>noao_approved_time (prop_info)</font><br>'
		 + 'TAC approved NOAO time<br>';

var prop_xmm = 'XMM Approved Time</b></font><br>'
		 + '<font color=#008080>xmm_approved_time (prop_info)</font><br>'
		 + 'TAC approved XMM time<br>';

var prop_rxte = '<font color=blue><b>RXTE Approved Time</b></font><br>'
		 + '<font color=#008080>rxte_approved_time (prop_info)</font><br>'
		 + 'TAC approved RXTE time<br>';

var prop_vla = '<font color=blue><b>VLA Approved Time</b></font><br>'
		 + '<font color=#008080>vla_approved_time (prop_info)</font><br>'
		 + 'TAC approved VLA time<br>';

var prop_vlba = '<font color=blue><b> VLBA Approved Time</b></font><br>'
		 + '<font color=#008080>vlba_approved_time (prop_info)</font><br>'
		 + 'TAC approved VLBA time<br>';

var soe_st_sched_date = '<font color=blue><b>Schedule Date</b></font><br>'
		 + '<font color=#008080>soe_st_sched_date (target)</font><br>'
		 + 'Observation schedule date<br>'
		 + 'This is the date the observation will take place.<br>'
		 + 'This date is not known until the detailed scheduling has begun<br>'
		 + 'Usually less than 10 days before the observation.<br>'
		 + 'Once this date is konwn it is virtually impossible to change<br>'
		 + 'any setting. CXC director and CXO flight director approval would<br>'
		 + 'be needed<br>';

var lts_lt_plan  = '<font color=blue><b>LTS Date</b></font><br>'
		 + '<font color=#008080>lts_lt_plan (target)</font><br>'
		 + 'LTS planed date<br>'
		 + 'Week of the observation for planning purposes.  This date<br>'
		 + 'may change, especially if the target is considered a pool target.<br>'
		 + 'Typically, 15 observations are moved each week.<br>'
		 + 'See the bottom of the long term schedule for recent changes.<br>';

var ra = '<font color=blue><b>RA(HMS)</b></font><br>'
		 + '<font color=#008080>ra (target)</font><br>'
		 + 'The Right Ascension of the source in mandatory J2000 coordinate system.<br>'
		 + 'The standard format is HH MM SS.S - hours, minutes, seconds,<br>'
		 + ' separated by spaces. For usint reading, a decimal degree format is required <br>.'
                 + '<font color=red>If RA + DEC change is larger than 8 arc minutes, CDO<br>'
                 + ' approval is required and cannot be made from this interface.</font><br>';
		
var dec = '<font color=blue><b>DEC(HMS)</b></font><br>'
		 + '<font color=#008080>dec (target)</font><br>'
		 + 'The declination of the source in mandatory J2000 coordinate<br>'
		 + 'system. The standard format is +/-DD MM SS.S - sign, degrees,arcminutes,<br>'
		 + 'arcseconds, separated by spaces For usint reading, decimal degree format is required.<br>'
                 + '<font color=red>If RA + DEC change is larger than 8 arc minutes, CDO<br>'
                 + ' approval is required and cannot be made from this interface.</font><br>';

var planned_roll = '<font color=blue><b>Planned Roll</b></font><br>'
		 + '<font color=#008080>N/A</font><br>'
	 	 + 'This is the MP planned roll. This is not an editable field.<br>'
		 + 'See http://hea-www.harvard.edu/asclocal/mp/lts/lts-current.html';

var roll_obsr = '<font color=blue><b>Roll Observed</b></font><br>'
		 + '<font color=#008080>soe_roll (soe)</font><br>'
	 	 + 'This is the observed roll. This is not an editable field.<br>'
		 + 'See Roll Constraints if you need to constrain the roll<br>';

var dra='<font color=blue><b>RA</b></font><br>'
		 + 'RA in degrees. This is the RA in decimal coordinates.<br>';
		 + 'This is the system used by the mission planners. The spacecraft<br>'
		 + 'will point here. The MHS version is soloely for convenience<br>'
		 + '<font color=red>If RA + DEC change is rather than 8 arc minutes,<br>'
		 + ' CDO approval is required.</font><br>';

var ddec = '<font color=blue><b>DEC</b></font><br>'
		 + 'DEC in degrees. This is the DEC in decimal coordinates.<br>'
		 + 'This is the system used by the mission planners. The spacecraft<br>'
		 + 'will point here. The MHS version is soloely for convenience<br>'
		+ '<font color=red>If RA + DEC change is rather than 8 arc minutes,<br>'
		+ ' CDO approval is required.</font><br>';

var y_det_offset = '<font color=blue><b>Offset Y</b></font><br>'
		 + '<font color=#008080>y_det_offset (target)</font><br>'
		 + 'This motion moves the target position away from the aimpoint<br>'
		 + '(and thus away from the best focus position) by yawing the spacecraft<br>'
		 + 'away from the target. Sense: negative Y offset moves the target<br>'
		 + 'aways from the aimpoint in the direction of S4 on ACIS-S<br>'
		 + '(ie further onto the S3 chip). Refer to Figure 6.1 in the Proposers Guide<br>'
		 + 'Recommendations: ACIS-S imagin observations Y-offset -0.33 arcmins<br>'
		 + '<font color=green> Value Range: -120.0 to +120.0</font><br>';

var z_det_offset = '<font color=blue><b>Offset Z</b></font><br>'
		 + '<font color=#008080>z_det_offset (target)</font><br>'
		 + 'This motion moves the target position away from the aimpoint<br>'
		 + '(and thus away from the best focus position) by pitching the spacecraft<br>'
		 + 'away from the target. Sense: positive offset moves the traget<br>'
		 + 'towards the readouts in ACIS-S (ie away form ACIS-I). Refer to Figure 6.1<br>'
		 + 'in the Proposers Guide. Value is angle in arcmin measured from the aimpoint<br>'
		 + '<font color=green> Value Range: -120.0 to +120.0</font><br>';
		
var trans_offset = '<font color=blue><b>Z-Sim</b></font><br>'
		 + '<font color=#008080>trans_offset (sim)</font><br>'
                 + 'This is a motion of the SIM and thus the aimpoint away from<br>'
                 + 'the default position on the detector along the z-axis<br>'
                 + '(the SIM Translation direction.<br>'
                 + 'Sense: a negative motion moves the aimpoint (and the<br>'
		 + ' target) towards the readouts on ACIS-S (ie. away from ACIS-I)<br>'
		 + '<br>'
                 + 'Units: mm (scale 2.93mm/arcmin)<br>'
 		 + 'Recommendations<br>'
		 + '<pre>'
 		 + 'Configuration   Mode    SIM z (mm)'
		 + '</pre><br><pre>'
 		 + 'HETG+ACIS-S     TE      -3'
		 + '</pre><br><pre>'
 		 + 'HETG+ACIS-S     CC      -4'
		 + '</pre><br><pre>'
 		 + 'LETG+ACIS-S     TE      -8'
		 + '</pre><br><pre>'
 		 + 'LETG+ACIS-S     CC      -8'
		 + '</pre>'
		 + '<font color=green> Value Range: NULL, -190.5 to 126.621.</font><br>';
		
var focus_offset = '<font color=blue><b>Sim-Focus</b></font><br>'
		 + '<font color=#008080>focus_offset (sim)</font><br>'
		 + 'Focus offset on the SIM, in mm.<br>';
		
var defocus = '<font color=blue><b>Focus</b></font><br>'
		 + '<font color=#008080>defocus (target)</font><br>'
		 + 'A number determining how far in mm the focal plane will <br>'
		 + 'be moved toward or away from the mirrors.<br>';

var raster_scan = '<font color=blue><b>Raster Scan</b></font><br>'
		 + '<font color=#008080>raster_scan (target)</font><br>'
		 + 'A flag indicating whether the observation will be a raster scan<br>'
		 + '<font color=green>Value Ranges: NULL, Y, N </font><br>';
		
var dither_flag = '<font color=blue><b>Dither</b></font><br>'
		 + '<font color=#008080>dither_flag (target)</font><br>'
		 + 'A flag indicating whether a dither is required for the observation.<br>'
		 + 'The default "NULL" means dither is preset to the standard dither<br>'
		 + 'pattern. <I>It does not mean no dither.</I> "Y" means that you are<br>'
		 + 'using your own dither parameters, these may be rejected on final<br>'
		 + 'review, so contact CDO ahead of time for review. "N"means no dither<br>'
		 + 'again this may be rejected by the SI team during final review so<br>'
		 + 'contact CDO to avoid surprises<br>'
		 + 'The dither parameters must not violate the requirement on peak<br>'
		 + ' dither rate:<br>'
 		 + 'sqrt((y_ampl*2*PI/y_period)2 + (z_ampl*2*PI/z_period)2) < 0.22 arcsec/sec<br>'
 		 + 'This peak dither rate can be used to evaluate the effect of image<br>'
		 + ' blurring during an ACIS frame integration.<br><br>'
                 + 'The dither parameters must not violate the requirement'
                 + 'on peak dither rate:<br><br><b>'
                 + 'sqrt((y_ampl*2*PI/y_period)2 + (z_ampl*2*PI/z_period)2) < 0.22 arcsec/sec'
                 + '</b> <BR><BR>'
                 + 'This peak dither rate can be used to evaluate the effect of'
                 + 'image blurring during an ACIS frame integration.'
                 + '<br>'
		 + '<table border= 1>'
		 + '<tr><th>Parameter</th>    <th> ACIS Default</th>    <th> HRC Default</th></tr>'
		 + '<tr><th>y_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" =0.0056 deg</td></tr>'
		 + '<tr><th>y_frequency</th>  <td>1296"/sec<br>=0.36 deg/sec</td><td>1191"/sec<br>=0.331 deg/sec</td></tr>'
		 + '<tr><th>y_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '<tr><th>z_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" = 0.0056 deg</td></tr>'
		 + '<tr><th>z_frequency</th>  <td>1832"/sec<br>=0.509 deg/sec</td><td>1648"/sec<br>= 0.468 deg/sec</td></tr>'
		 + '<tr><th>z_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '</table> <br>'

		 + '<font color=green> Value Range: Y, N, NULL</font><br>';

var y_amp  = '<font color=blue><b>Y Amplitude</b></font><br>'
		 + '<font color=#008080>y_amp (dither)</font><br>'
		 + 'Dither Y amplitude in arcsec<br>'
		 + 'The value is also displayed in degree'
                 + '<br><br>The dither parameters must not violate the requirement'
                 + 'on peak dither rate:<br><br><b>'
                 + 'sqrt((y_ampl*2*PI/y_period)2 + (z_ampl*2*PI/z_period)2) < 0.22 arcsec/sec'
                 + '</b> <BR><BR>'
                 + 'This peak dither rate can be used to evaluate the effect of'
                 + 'image blurring during an ACIS frame integration.'
                 + '<br>'
		 + '<table border= 1>'
		 + '<tr><th>Parameter</th>    <th> ACIS Default</th>    <th> HRC Default</th></tr>'
		 + '<tr><th>y_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" =0.0056 deg</td></tr>'
		 + '<tr><th>y_frequency</th>  <td>1296"/sec<br>=0.36 deg/sec</td><td>1191"/sec<br>=0.331 deg/sec</td></tr>'
		 + '<tr><th>y_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '<tr><th>z_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" = 0.0056 deg</td></tr>'
		 + '<tr><th>z_frequency</th>  <td>1832"/sec<br>=0.509 deg/sec</td><td>1648"/sec<br>= 0.468 deg/sec</td></tr>'
		 + '<tr><th>z_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '</table> <br>';


var y_freq  = '<font color=blue><b>Y Frequency</b></font><br>'
		 + '<font color=#008080>y_freq (dither)</font><br>'
		 + 'Dither Y frequency in arcsec/sec<br>'
                 + '<br><br>The dither parameters must not violate the requirement'
                 + 'on peak dither rate:<br><br><b>'
                 + 'sqrt((y_ampl*2*PI/y_period)2 + (z_ampl*2*PI/z_period)2) < 0.22 arcsec/sec'
                 + '</b> <BR><BR>'
                 + 'This peak dither rate can be used to evaluate the effect of'
                 + 'image blurring during an ACIS frame integration.'
                 + '<br>'
		 + '<table border= 1>'
		 + '<tr><th>Parameter</th>    <th> ACIS Default</th>    <th> HRC Default</th></tr>'
		 + '<tr><th>y_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" =0.0056 deg</td></tr>'
		 + '<tr><th>y_frequency</th>  <td>1296"/sec<br>=0.36 deg/sec</td><td>1191"/sec<br>=0.331 deg/sec</td></tr>'
		 + '<tr><th>y_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '<tr><th>z_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" = 0.0056 deg</td></tr>'
		 + '<tr><th>z_frequency</th>  <td>1832"/sec<br>=0.509 deg/sec</td><td>1648"/sec<br>= 0.468 deg/sec</td></tr>'
		 + '<tr><th>z_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '</table> <br>';

		
var y_phase = '<font color=blue><b>Y Phase</b></font><br>'
		 + '<font color=#008080>y_phase (dither)</font><br>'
		 + 'Dither Y phase in degrees<br>'
                 + '<br><br>The dither parameters must not violate the requirement'
                 + 'on peak dither rate:<br><br><b>'
                 + 'sqrt((y_ampl*2*PI/y_period)2 + (z_ampl*2*PI/z_period)2) < 0.22 arcsec/sec'
                 + '</b> <BR><BR>'
                 + 'This peak dither rate can be used to evaluate the effect of'
                 + 'image blurring during an ACIS frame integration.'
                 + '<br>'
		 + '<table border= 1>'
		 + '<tr><th>Parameter</th>    <th> ACIS Default</th>    <th> HRC Default</th></tr>'
		 + '<tr><th>y_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" =0.0056 deg</td></tr>'
		 + '<tr><th>y_frequency</th>  <td>1296"/sec<br>=0.36 deg/sec</td><td>1191"/sec<br>=0.331 deg/sec</td></tr>'
		 + '<tr><th>y_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '<tr><th>z_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" = 0.0056 deg</td></tr>'
		 + '<tr><th>z_frequency</th>  <td>1832"/sec<br>=0.509 deg/sec</td><td>1648"/sec<br>= 0.468 deg/sec</td></tr>'
		 + '<tr><th>z_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '</table> <br>';

		
var z_amp = '<font color=blue><b>Z Amplitude</b></font><br>'
		 + '<font color=#008080>z_amp (dither)</font><br>'
		 + 'Dither Z amplitude in arcsec<br>'
		 + 'The value is also displayed in degree'
                 + '<br><br>The dither parameters must not violate the requirement'
                 + 'on peak dither rate:<br><br><b>'
                 + 'sqrt((y_ampl*2*PI/y_period)2 + (z_ampl*2*PI/z_period)2) < 0.22 arcsec/sec'
                 + '</b> <BR><BR>'
                 + 'This peak dither rate can be used to evaluate the effect of'
                 + 'image blurring during an ACIS frame integration.'
                 + '<br>'
		 + '<table border= 1>'
		 + '<tr><th>Parameter</th>    <th> ACIS Default</th>    <th> HRC Default</th></tr>'
		 + '<tr><th>y_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" =0.0056 deg</td></tr>'
		 + '<tr><th>y_frequency</th>  <td>1296"/sec<br>=0.36 deg/sec</td><td>1191"/sec<br>=0.331 deg/sec</td></tr>'
		 + '<tr><th>y_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '<tr><th>z_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" = 0.0056 deg</td></tr>'
		 + '<tr><th>z_frequency</th>  <td>1832"/sec<br>=0.509 deg/sec</td><td>1648"/sec<br>= 0.468 deg/sec</td></tr>'
		 + '<tr><th>z_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '</table> <br>';

		
var z_freq = '<font color=blue><b>Z Frequency</b></font><br>'
		 + '<font color=#008080>z_freq (dither)</font><br>'
		 + 'Dither Z frequency in arcsec/sec<br>'
                 + '<br><br>The dither parameters must not violate the requirement'
                 + 'on peak dither rate:<br><br><b>'
                 + 'sqrt((y_ampl*2*PI/y_period)2 + (z_ampl*2*PI/z_period)2) < 0.22 arcsec/sec'
                 + '</b> <BR><BR>'
                 + 'This peak dither rate can be used to evaluate the effect of'
                 + 'image blurring during an ACIS frame integration.'
                 + '<br>'
		 + '<table border= 1>'
		 + '<tr><th>Parameter</th>    <th> ACIS Default</th>    <th> HRC Default</th></tr>'
		 + '<tr><th>y_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" =0.0056 deg</td></tr>'
		 + '<tr><th>y_frequency</th>  <td>1296"/sec<br>=0.36 deg/sec</td><td>1191"/sec<br>=0.331 deg/sec</td></tr>'
		 + '<tr><th>y_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '<tr><th>z_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" = 0.0056 deg</td></tr>'
		 + '<tr><th>z_frequency</th>  <td>1832"/sec<br>=0.509 deg/sec</td><td>1648"/sec<br>= 0.468 deg/sec</td></tr>'
		 + '<tr><th>z_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '</table> <br>';

		
var z_phase = '<font color=blue><b>Z Phase</b></font><br>'
		 + '<font color=#008080>z_phase (dither)</font><br>'
		 + 'Dither Z phase in degrees<br>'
                 + '<br><br>The dither parameters must not violate the requirement'
                 + 'on peak dither rate:<br><br><b>'
                 + 'sqrt((y_ampl*2*PI/y_period)2 + (z_ampl*2*PI/z_period)2) < 0.22 arcsec/sec'
                 + '</b> <BR><BR>'
                 + 'This peak dither rate can be used to evaluate the effect of'
                 + 'image blurring during an ACIS frame integration.'
                 + '<br>'
		 + '<table border= 1>'
		 + '<tr><th>Parameter</th>    <th> ACIS Default</th>    <th> HRC Default</th></tr>'
		 + '<tr><th>y_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" =0.0056 deg</td></tr>'
		 + '<tr><th>y_frequency</th>  <td>1296"/sec<br>=0.36 deg/sec</td><td>1191"/sec<br>=0.331 deg/sec</td></tr>'
		 + '<tr><th>y_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '<tr><th>z_amp</th>        <td>8" = 0.002222 deg</td>         <td>20" = 0.0056 deg</td></tr>'
		 + '<tr><th>z_frequency</th>  <td>1832"/sec<br>=0.509 deg/sec</td><td>1648"/sec<br>= 0.468 deg/sec</td></tr>'
		 + '<tr><th>z_phase</th>      <td>0</td>                         <td></td>&#160</td></tr>'
		 + '</table> <br>';

		
var uninterrupt = '<font color=blue><b>Uninterrupted Obs</b></font><br>'
		 + '<font color=#008080>uninterrupt (target)</font><br>'
		 + 'A flag for whether the observation can be interrupted.<br>'
		 + '<font color=red>CDO approval required to change this to Y or P</font><br>'
		 + 'This indicates a preference this will be noted by<br>'
		 + 'mission planning, but is not included by V&V when<br>'
		 + 'evaluating the success for the observation.<br>'
		 + '<font color=green> Value Range: Y, P, N, NULL</font><br>';

extended_src = '<font color=blue><b>Extended SRC</b></font><br>'
		 + 'RPS form from the proposal submission.<br>'
		 + '<font color=green> Value Range: Y,  N</font><br>';
		
var obj_flag = '<font color=blue><b>Solar System Object</b></font><br>'
		 + '<font color=#008080>obj_flag (target)</font><br>'
		 + 'A flag for a solar system observation.<br>'
		 + 'This field is used to allow the ground system to automatically<br>'
		 + 'calculate the position of the ss object or moving target for you <br>'
		 + 'It has not been used in flight. We recommend working with CDO to<br>'
		 + 'calculate the exact position<br>'
		 + '<font color=green> Value Range: NO, MT, or SS</font><br>';
		
var object = '<font color=blue><b>Object</b></font><br>'
		 + '<font color=#008080>object (target)</font><br>'
		 + 'Solar system objects.<br>'
		 + 'If you are so bold as to let the ground system calculate the <br>'
		 + 'pointing for you, this is where you input the object name<br>'
		 + '<font color=green> Value Range:  NONE, NEW, COMET, EARTH, JUPITER,<br>'
		 + 'MARS, MOON, NEPTUNE, PLUTO, SATURN, URANUS, or VENUS</font><br>';
		
var photometry_flag = '<font color=blue><b>Photometry</b></font><br>'
		 + '<font color=#008080>photometry_flag (target)</font><br>'
		 + 'a flag for photometry which indicates whether observer<br>'
		 + 'will use one of the 5 star tracking slots for traget <br>'
		 + 'photometry. See the POG section Section 5.9.3.1 for details<br>'
		 + '<font color=green> Value Range: NULL, Y, N</font><br>';
		
var vmagnitude = '<font color=blue><b>V Mag</b></font><br>'
		 + '<font color=#008080>vmagnitude (target)</font><br>'
		 + 'V Magnitude of the target if optical monitor data is selected<br>'
		 + '<font color=green> Value Range: NULL, -15 to 20.</font><br>';
		
var est_cnt_rate = '<font color=blue><b>Count Rate</b></font><br>'
		 + '<font color=#008080>est_cnt_rate (target)</font><br>'
		 + 'Estimated count rate for the observation counts/sec.<br>'
		 + 'A vlue is required, if a grating is requested.<br>'
		 + '<font color=green> Value Range: NULL, 0 to 100,000.</font><br>';

var forder_cnt_rate = '<font color=blue><b>1st Order Rate</b></font><br>'
		 + '<font color=#008080>forder_cnt_rate (target)</font><br>'
		 + 'First order count rate in counts/sec for ACIS-S+grating <br>'
		 + 'and HRC-S+grating observations. A vlue is required, if a grating is requested.<br>'
		 + '<font color=green> Value Range: NULL, 0 to 100,000.</font><br>';
		
var window_flag = '<font color=blue><b>Window Flag</font><br>'
		 + '<font color=#008080>window_flag (taget)</font><br>'
		 + 'This can only be set to "Y" if this is a TAC or CDO<br>';
		 + 'approved constraint.  Set to "P" if you have a preference<br>'
		 + 'and we will do the best we can to accommodate your entries<br>'
		 + '<font color=green> Value Range: NULL, N, Y, P</font><br>';

var time_ordr = '<font color=blue><b>Rank</b></font><br>'
		 + '<font color=#008080>ordr(timereq)</font><br>'
		 + 'You can have multiple time constraints on a given target<br>'
		 + 'Increase this number to prodcue multiple window. If you change<br>'
		 + 'this value, numbers of input windows for tstart, tstop change accordingly<br>';

var window_constraint = '<font color=blue><b>Window Constraint</b></font><br>'
		 + '<font color=#008080>window_constraint (timereq)</font><br>'
		 + 'A flag indicating whether a time window is required for the observation.<br>'
		 + '<font color=red>"Y" is only allowed if TAC or CDO approved</font><br>'
		 + '<font color=green> Value Range:  NULL, N, Y, P</font><br>';

var tstart = '<font color=blue><b>Start</b></font><br>'
		 + '<font color=#008080>tstart (timereq) </font><br>'
		 + 'Date and time to start time critical observation. Time must<br>'
		 + 'be 24 hr system in hh:mm:ss format.<br>'
		 + '<I> Time is in UT</I><br>';
		
var tstop = 'Stop</b></font><br>'
		 + '<font color=#008080>tstop (timereq) </font><br>'
		 + 'Date and time to start time critical observation. <br>'
		 + 'Time must be 24 hr system in hh:mm:ss format.<br>'
		 + '<I> Time is in UT</I><br>';
		
var roll_flag = '<font color=blue><b>Roll Flag</font><br>'
		 + '<font color=#008080>roll_flag (taget)</font><br>'
		 + 'This can only be set to "Y" if this is a TAC or CDO approved constraint<br>'
		 + 'Set to "P" if you have a preference and we will do the best we can to <br>'
		 + 'accommodate your entries<br>'
		 + '<font color=green> Value Range: NULL, N, Y, P</font><br>';

var roll_ordr = '<font color=blue><b>Rank</b></font><br>'
		 + '<font color=#008080>ordr (rollreq)</font><br>'
		 + 'Order for the roll constraint. If you change this value,<br>'
		 + 'numbers of roll constraint, roll180, roll, and roll tolerance change accordingly <br>';

var roll_constraint = '<font color=blue><b>Roll Constraint</b></font><br>'
		 + '<font color=#008080>roll_constraint (rollreq)</font><br>'
		 + 'A flag indicating whether a roll constraint is required for the observation. <br>'
		 + 'This can only be set to "Y" if this is a TAC or CDO approved constraint.<br>'
		 + 'Set to "P" if you have a preference and we will do the best we can to <br>'
		 + 'accommodate your entries<br>'
		 + '<font color=green> Value Range: NULL, N, Y, P</font><br>';
		
var roll_180 = 'Roll180?</b></font><br>'
		 + '<font color=#008080>roll_180(rollreq)</font><br>'
		 + 'A flag indicating whether 180 degree flip in the roll is acceptable for the observation<br>'
		 + '<font color=green> Value Range:  NULL, N,  Y</font><br>';
		
var roll = '<font color=blue><b>Roll</b></font><br>'
		 + '<font color=#008080>roll(rollreq)</font><br>'
		 + 'The spacecraft roll angle is the angle between celestial north <br>'
		 + 'and the spacecraft +Z axis projected on the sky.  Measured in degrees.<br>'
		 + '<font color=green> Value Range: NULL, 0 to 360.</font><br>';
		

var roll_tolerance = '<font color=blue><b>Roll Angle Tolerance</b></font><br>'
		 + '<font color=#008080>roll_tolerance (rollreq)</font><br>'
		 + 'Tolerance on the Roll Angle.<br>'
		 + '<font color=green> Value Range: NULL,0 to 360</font><br>';
		
var constr_in_remarks = '<font color=blue><b>Constraints in Remarks?</b></font><br>'
		 + '<font color=#008080>constr_in_remarks (target)</font><br>'
                 + 'A flag indicating whether there is a description<br>'
                 + 'of any constraints in a remark<br>'
                 + 'section.  Note that the Constraint in Remarks section<br>'
                 + '<i> cannot be used to add in<br>'
		 + 'constraints that were not approved through peer review,</i> but rather<br>'
		 + 'to explain existing constraints and preferences.<br>'
		 + '<font color=green> Value Range: NULL, Y, P,  N </font><br>';
		
var phase_constraint_flag = '<font color=blue><b>Phase Constraint</b></font><br>'
		 + '<font color=#008080>phase_constraint_flag (target)</font><br>'
		 + 'A flag indicating whether the observation is targeted at a particular<br>'
		 + 'orbital phase. If so, additional data is required. If this is set for Y<br>'
		 + 'or P, values for the Epoch of phase 0 , the Period of the phenomena, <br>'
		 + 'Phase Start, Phase Start Margin, Phase Min, Phase Min Margin are required<br>'
		 + '<font color=green> Value Range: NULL, N, Y, P</font><br>';
			
var phase_epoch = '<font color=blue><b>Phase Epoch</b></font><br>'
		 + '<font color=#008080>phase_epoch (phasereq)</font><br>'
		 + 'For Phase Dependent observations, the reference date (MJD). <br>'
		 + 'The observations will be made at an integral number of Periods from this date.<br>'
		 + '<font color=green>Value Ranges: > 46066.0</font><br>';
		
var phase_period = '<font color=blue><b>Phase Period</b></font><br>'
		 + '<font color=#008080>phase_period (phasereq)</font><br>'
		 + 'Period in days between phase dependent observations<br>';

var phase_start =  '<font color=blue><b>Phase Start</b></font><br>'
		 + '<font color=#008080>phase_start (phasereq)</font><br>'
		 + 'The earliest phase for the observation<br>'
		 + '<font color=green>Value Ranges:  0 to 1</font><br>';
		
var phase_start_margin = '<font color=blue><b>Phase Start Margin</b></font><br>'
		 + '<font color=#008080>phase_start_margin (phasereq)</font><br>'
	 	 + 'The allowable error for mission planning on the previous entry. <br>'
		 + 'Remeber to include the observation duration when thinking about this<br>'
		 + '<font color=green>Value Ranges: 0 to 0.5</font><br>';
		
var phase_end = '<font color=blue><b>Phase End</b></font><br>'
		 + '<font color=#008080>phase_end (phasereq)</font><br>'
		 + 'Maximum orbital phase to be observed.  <br>'
		 + '<font color=green>Value Ranges:  0 to 1</font><br>';
		
var phase_end_margin = '<font color=blue><b>Phase End Margin</b></font><br>'
		 + '<font color=#008080>phase_end_margin (phasereq)</font><br>'
		 + 'Error on the maximum orbital phase. Include the observation<br>'
		 + 'duration when thinking about this value<br>'
		 + '<font color=green>Value Ranges: 0 to 0.5</font><br>';

var monitor_flag = '<font color=blue><b>Monitoring Observation</b></font><br>'
                + 'The following 3 fields are used for monitoring<br>'
                + 'observations.  While the full pattern of observations<br>'
                + 'can be complicated, here you concern yourself with a<br>'
                + 'previous observation in the group and the time (in<br>'
                + 'days) between that observation and this one.<br>'
                + 'The start time for a monitoring observation is<br>'
                + 'determined by the time the previous observation ENDED,<br>'
                + 'and only has to BEGIN between Min Int and Max Int,<br>'
                + 'it does not need to fall fully within these boundaries. <br><br>'
                + '<b>Notes:</B> It is possible to have monitoring<br>'
                + 'observations where<br>'
                + 'each obsid is linked to the first in the series<br>'
                + '(ie. you want to space them from the initial obsid by<br>'
                + 'some number of days and do not want that to be impacted<br>'
                + 'by the tolerance on the previous one).  In this case,<br>'
                + 'Follows ObsID# should be the first in the sequence.<br>'
                + 'It is also possible for the first observation in a<br>'
                + 'monitoring series to be time constrained or otherwise<br>'
                + 'constrained as specified by the observer, though it<br>'
                + 'does not become a time constrained observation simply<br>'
                + 'because it is the 1st observation in a monitoring series.<br>'
		+ '<b>If group_id has a value, monitoring observation<br>'
		+ 'must be null<br>';
		
var pre_id = '<font color=blue><b>Follows ObsID#</b></font><br>'
		 + '<font color=#008080>pre_id (target)</font><br>'
		 + 'Gives the ObsId # in which this observation follows. There cannot be any time constraints.<br>';

var pre_min_lead = '<font color=blue><b>Min Int</b></font><br>'
		 + '<font color=#008080>pre_min_lead (target)</font><br>'
		 + 'Monitoring Observation: The minimum interval between monitoring observations.  Units are days<br>'
		 + '<font color=green>Value Ranges: NULL, 0 to 364</font><br>';
		
var pre_max_lead = '<font color=blue><b>Max Int</b></font><br>'
		 + '<font color=#008080>pre_max_lead (target)</font><br>'
		 + 'Monitoring Observation: The maximum interval between monitoring observations.  Units are days.<br>'
		 + '<font color=green>Value Ranges: NULL, 0.01 to 365</font><br>';
		
var multitelescope = '<font color=blue><b>Coordinated Observation</b></font><br>'
		 + '<font color=#008080>multitelescope (target)</font><br>'
		 + 'A flag indicating whether this is coodinated observation.<br>'
		 + 'This differs from a joint proposal in that the telescope time involved comes<br>'
		 + 'from multiple TACs. It CAN be listed as a preference if telescope time has been<br>'
		 + 'obtained after the TAC approval of this observation.<br>'
		 + '<font color=red>CDO approval is required to change the value to "Y".</font><br>'
		 + '<font color=green>Value Ranges: Y,P, N</font><br>';
		
var observatories = '<font color=blue><b>Observatories</b></font><br>'
		 + '<font color=#008080>observatories (target)</font><br>'
		 + 'Names of coordinated observatories.</br> '
		 + '<font color=red>CDO approval is required to change the value.</font><br>'
		 + 'if the "Coordinated Observation" flag is set to "Y"<br>';

var multitelescope_interval = '<font color=blue><b>Max Coordination Offset</b></font><br>'
		 + '<font color=#008080>multitelescope_interval (target)</font><br>'
		 + 'The maximum time interval for coordination with ground-based observatories</br>'
		 + 'The units are days (floating point)</br>'
		 + '<font color=red>CDO approval is required to change the value.</font><br>'
		 + 'if the "Coordinated Observation" flag is set to "Y"<br>';
		 
var hrc_timing_mode = '<font color=blue><b>HRC Timing Mode</b></font><br>'
		 + '<font color=#008080>timing_mode (hrcparam)</font><br>'
		 + 'This timing mode consists of using the HRC-S in the imaging mode <br>';
		 + 'Only the center segment is active. The overall detector background is about 50 cnt/sec<br>';
		 + 'Sources with rates up to the telemetry limit can be observed  with no lost events<br>';
		 + '<font color=green>Value Ranges: "Y", "N"</font><br>';

var hrc_zero_block =  '<font color=blue><b>Zero Block</b></font><br>'
		 + '<font color=#008080>zero_block (hrcparam)</font><br>'
		 + 'Logical value indicating zero-order blocking. the defalut is "N"<br>'
		 + 'The spectrum zero order may be blocked if desired.<br>'
		 + 'Using zero-block moves a shutter-blade vignettes much of the <br>'
		 + 'central plate of the HRC-S or a large portion of the center of the<br>'
		 + 'HRC-I.  The impact on the HRC-S can be seen here.<br>'
		 + '<font color=green>Value Ranges: "NULL", "Y", "N"<br>';

var hrc_si_mode = '<font color=blue><b>HRC SI Mode</b></font><br>'
		+ '<font color=#008080>si_mode (hrcparam)</font><br>'
	        + 'A link to a listing of current and default HRCMODEs is available.<br>'
		+ 'If a user wishes to request the use of one of these ofr have a custom<br>'
		+ 'one built the request should be put into the comment area<br>';
		
var exp_mode = '<font color=blue><b>ACIS Exposure Mode</b></font><br>'
		 + '<font color=#008080>exp_mode (acisparam)</font><br>'
		 + 'The exposure mode for ACIS.<br>'
		 + 'See POG section 6.12 for details<br>'
		 + '<font color=green>Value Ranges: TE (Timed Exposure), CC (Continuous Clocking)</font><br>';
		
var bep_pack =  '<font color=blue><b>Event TM Format</b></font><br>'
		 + '<font color=#008080>bep_pack (acisparam)</font><br>'
		 + 'Event Telemetry Format: Event Telemetry Format controls the<br>'
		 + 'packing of the data into the telemetry stream. This must be N, if frame_time has a value.<br>'
		 + 'See POG section 6.13.2 for details<br>'
		 + '<font color=green>Value Ranges:  Faint (TE,CC), Very Faint(TE), Faint+Bias(TE), Graded(TE,CC)</font><br>';

var frame_time = '<font color=blue><b>Frame Time</b></font><br>'
		 + '<font color=#008080>frame_time (acisparam)</font><br>'
                 + 'User specified frame time (in seconds) to use.<br>'
                 + 'ACIS can accommodate frametimes from 0.1 to 10.0 s,<br>'
                 + 'however, frametimes less than 0.4s will introduce a deadtime.  One<br>'
                 + 'CCD can be readout with a 128 row subarray in 0.4s with no deadtime.<br>'
                 + 'Any faster than that and there will be deadtime.<br>'
		 + 'Most Efficient must be N if  frame_time has a value.<br>'
		 + '<font color=green>Value Ranges:  NULL, 0 to 10</font><br>';

var most_efficient = '<font color=blue><b>Most Efficient</b></font><br>'
		 + '<font color=#008080>most_efficient (acisparam)</font><br>'
		 + 'A flag indicating whether the observation requires the most efficient setting.<br>'
		 + 'This must be N, if frame_time has a value<br>'
		 + '<font color=green>Value Ranges: NULL, Y, N</font><br>';
		
var standard_chips = '<font color=blue><b>Standard Chips</b></font><br>'
		 + '<font color=#008080>standard_chips (acisparam)</font><br>'
		 + 'Logical value indicating that the standard ACIS chips should be used. The default in N.<br>'
		 + 'A "Y" answer will activate the 6 standard ACIS chips. If N is<br>'
		 + 'selected, usint needs to select ccd chips from: I0, I1, I2, I3, S0, S1, S2, S3, S4, S5<br>' 
		 + '<font color=green>Value Ranges: NULL, Y, N</font><br>';
		
var fep = '<font color=blue><b>FEP</b></font><br>'
		 + '<font color=#008080>fep (acisparam)</font><br>'
		 + 'FEP <br>'
		 + '<font color=green>Value Ranges:NULL, I0, I1, I2, I3, S0, S1, S2, S3, S4, S5</font><br>';
		
var dropped_chip_count = '<font color=blue><b>Dropped Chip Count</b></font><br>'
		 + '<font color=#008080>dropped_chip_count(acisparam)</font><br>'
		 + 'This tells you # of optional chips dropped. <br>'
		 + '<font color=green>Value Ranges:NULL, 0 to 5</font><br>';
		
var ccdi0_on = '<font color=blue><b>I0</b></font><br>'
		 + '<font color=#008080>ccdi0_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip I0 on? <br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var ccdi1_on = '<font color=blue><b>I1</b></font><br>'
		 + '<font color=#008080>ccdi1_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip I1 on?<br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var ccdi2_on = '<font color=blue><b>I2</b></font><br>'
		 + '<font color=#008080>ccdi2_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip I2 on?<br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var ccdi3_on = '<font color=blue><b>I3</b></font><br>'
		 + '<font color=#008080>ccdi3_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip I3 on?<br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var ccds0_on = '<font color=blue><b>S0</b></font><br>'
		 + '<font color=#008080>ccds0_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip S0 on?<br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var ccds1_on = '<font color=blue><b>S1</b></font><br>'
		 + '<font color=#008080>ccds1_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip S1 on?<br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var ccds2_on = '<font color=blue><b>S2</b></font><br>'
		 + '<font color=#008080>ccds2_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip S2 on?<br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var ccds3_on = '<font color=blue><b>S3</b></font><br>'
		 + '<font color=#008080>ccds3_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip S3 on?<br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var ccds4_on = '<font color=blue><b>S4</b></font><br>'
		 + '<font color=#008080>ccds4_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip S4 on?<br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var ccds5_on = '<font color=blue><b>S5</b></font><br>'
		 + '<font color=#008080>ccds5_on (acisparam)</font><br>'
		 + 'Do you want ACIS chip S5 on?<br>'
		 + 'There is a limit of 6 chips on, and options of dropping CCDs if needed<br>'
		 + 'OPT1 will be dropped first, and OPT5 will be the last.<br>'
		 + '<font color=green>Value Ranges:Y, O1, O2, O3, O4, O5, N, NULL</font><br>';

var subarray = '<font color=blue><b>Use Subarray</b></font><br>'
		 + '<font color=#008080>subarray (acisparam)</font><br>'
		 + 'A subarray is a reduced region of the CCDs (all of the CCDs that<br>'
		 + 'are turned on) that will be read.  A reduced region may also help<br>'
	 	 + 'to reduce the effects of pulse pile-up.  The first box indicates<br>'
		 + 'whether  the proposer intends to use the subarray capability.<br>'
		 + '  The default is "NO".<br>'
		 + 'If "YES" is selected, the Start, Rows must be filled.<br>'
		 + '<br>The old default subarrays are:<br>'
		 + '<table cellpadding=2><tr>'
		 + '<th>subarray:</th><th colspan=2>1/8</th><th colspan=2>1/4</th><th colspan=2>1/2</th>'
		 + '</tr><tr>'
		 + '<th>aimpoint:</th><td>start</td><td>rows</td><td>start</td><td>rows</td><td>start</td><td>rows</td>'
		 + '</tr><tr>'
		 + '<th>ACIS-I  :</th><td>897</td><td>128</td><td>768</td><td>256</td><td>513</td><td>512</td>'
		 + '</tr><tr>'
		 + '<th>ACIS-S  :</th><td>449</td><td>128</td><td>385</td><td>256</td><td>257</td><td>512</td>'
		 + '</tr></table>'
		 + '<br>'
		 + '<font color=green>Value Ranges: N (NO) and CUSTOM (YES)</font><br>';

var subarray_start_row = '<font color=blue><b>Start</b></font><br>'
		 + '<font color=#008080>subarray_start_row (acisparam)</font><br>'
		 + 'Subarray: The starting row that will be read for processing custom subarrays.<br>'
		 + 'If it is not NULL, Use Subarray must be YES, and Rows must be filled.<br>'
		 + 'See section 6.2.13 of the POG<br>'
		 + '<font color=green>Value Ranges: NULL, 1 to 925 </font><br>';
		
var subarray_row_count = '<font color=blue><b>Rows</b></font><br>'
		 + '<font color=#008080>subarray_row_count (acisparam)</font><br>'
		 + 'Subarray: The number of rows that will be read for processing <br>'
		 + 'custom subarrays.  If it is not NULL, Use Subarray must be YES, and Start must be filled.<br>'
		 + 'See section 6.2.13 of the POG for details<br>'
		 + '<font color=green>Value Ranges: NULL, 100 to 1024 </font><br>' ;

var subarray_frame_time = '<font color=blue><b>Frame Time</b></font><br>'
		 + '<font color=#008080>subarray_frame_time (acisparam)</font><br>'
		 + 'Subarray - Frame Time: The Frame Time is the fundamental <br>'
		 + 'unit of exposure for ACIS. The higher time resolution is achieved<br>'
		 + ' by reading fewer rows of the CCD.  <br>'
		 + 'The minimum frame time of 0.2 sec corresponds to reading<br>'
		 + ' a subarray of 128 rows.  The maximum time of 3.2 sec corresponds to reading all 1024 rows.  <br>'
		 + 'Any value from 0.2 to 3.2 sec is possible by adjusting the number<br>'
		 + ' of rows to be read AND by accepting a deadtime for frametimes less than 0.4s<br>'
		 + ' The number of rows to be read and the Subarray<br>'
		 + 'Frame Time should be equivalent; the two values will be compared to see that they are.  <br>'
		 + 'The equation for calculating the Frame Time from the number of<br>'
		 + ' rows to be read is included in the Proposers Guide.<br>'
		 + '<font color=green>Value Ranges: NULL, 0 to 10 </font><br>' ;
		
var duty_cycle = '<font color=blue><b>Duty Cycle</b></font><br>'
		 + '<font color=#008080>duty_cycle (acisparam)</font><br>'
		 + 'Alternating Exposure Readout: Logical value indicating use of <br>'
		 + 'alternating exposure readout.  The default is "N".  Alternating <br>'
		 + 'Exposure Readout observation sets the number of SECONDARY<br>'
		 + 'exposures that will follow each primary exposure.  A deadtime<br>'
		 + 'will result from the short exposure since the electronics still<br>'
		 + 'require 3.2 sec to process full frame.  Therefore, to minimize<br>'
		 + 'the deadtime, the number of short exposures should be kept to a minimum.<br>'
		 + 'If Y is selected, Tprimary must be filled.<br>'
		 + '<font color=green>Value Ranges: NULL, Y, N </font><br>' ;
		
var secondary_exp_count = '<font color=blue><b>Number</b></font><br>'
		 + '<font color=#008080>secondary_exp_count (acisparam)</font><br>'
		 + 'Alternating Exposure Readout: The number of secondary<br>'
		 + ' exposures that will follow each primary exposure<br>'
		 + 'If n = 0, only primary exposures are used.<br>'
		 + 'Read the ACIS chapter of the Proposers Guide for an estimate of the efficiency.<br>'
		 + 'The recommended value is 2.<br>'
		 + '<font color=green>Value Ranges: 0 to 15</font><br>';
		
var primary_exp_time = '<font color=blue><b>Tprimary</b></font><br>'
		 + '<font color=#008080>primary_exp_time (acisparam)</font><br>'
		 + 'Alternating Exposure Readout: Exposure Time for Primary Cycle: <br>'
		 + 'The primary exposure time in tenths of seconds.  The recommended time for <br>'
		 + 'a non-zero number of secondary exposures is 0.3.<br>'
		 + '<font color=green>Value Ranges: NULL, 0 to 10 </font><br>';
		
var secondary_exp_time = '<font color=blue><b>Tsecondary</b></font><br>'
		 + '<font color=#008080>secondary_exp_time (acisparam)</font><br>'
		 + 'Alternating Exposure Readout : Exposure Time for Secondary Cycle: <br>'
		 + 'The secondary exposure time in tenths of seconds.  The recommended time for<br>'
	  	 + 'a non-zero number of secondary exposures is 3.2<br>';

var onchip_sum = '<font color=blue><b>Onchip Summing</b></font><br>'
		 + '<font color=#008080>onchip_sum (acisparam)</font><br>'
		 + 'Logical value indicating on-chip summation. The default value <br>'
		 + 'is "N".  On-chip summation can be used to reduce the number of<br>'
		 + ' items per CCD readout.  The spatial resolution is degraded as <br>'
		 + 'is the event splitting information. Currently, only 2x summation<br>'
		 + 'is supported. You can optionally fill Rows and Column<br>'
	         + 'If this is other than 2, expect to be contract by CDO<br>'
		 + '<font color=green>Value Ranges: NULL, N, Y</font><br>';

var onchip_row_count = '<font color=blue><b>Rows</b></font><br>'
		 + '<font color=#008080>onchip_row_count (acisparam)</font><br>'
		 + '# of rows for On-Chip Summing.<br> '
		 + '<font color=green>Value Ranges: 1 to 512</font><br>';
		
var onchip_column_count = '<font color=blue><b>Columns</b></font><br>'
		 + '<font color=#008080>onchip_column_count (acisparam)</font><br>'
		 + '# of columns for On-Chip Summing.<br>'
		 + '<font color=green>Value Ranges: 1 to 512</font><br>';
		
var eventfilter = '<font color=blue><b>Energy Filter</b></font><br>'
		 + '<font color=#008080>eventfilter (acisparam)</font><br>'
		 + 'This logical value indicates that the user wishes to filter every <br>'
		 + 'candidate event before packing into the telemetry stream. <br>'
		 + ' The filter applies to all of the active CCDs.  The use of an<br>'
		 + 'event filter does NOT affect pulse pileup, but only reduces<br>'
		 + 'the telemetry. If Y is selected, Lowest Energy and Energy Range must be filled.<br>'
		 + '<font color=green>Value Ranges: NULL, Y, N </font><br>';
		

var multiple_spectral_lines = '<font color=blue><b>Multiple Spectral Line</b></font><br>'
		 + '<font color=#008080>multiple_spectral_lines (acisparam)</font><br>'
		 + 'Logical value indicating whether or not more than 2 resolved spectral lines <br>'
		 + 'are expected in the brightest spectrum to be analyzed from this observation. <br>'
		 + '"Y" or "N" is required  for any ACIS-I non-grating observation. Both the two <br>'
		 + 'questions above are asked to trigger assessment of the sensitivity <br>'
		 + 'of ACIS-I imaging observations to gain calibration. Science from high S/N ACIS-I <br>'
		 + 'imaging spectroscopy (no gratings) with rich spectra may be affected by <br>'
		 + 'thermally-induced gain drifts.<br>'
		 + '<font color=green>Value Ranges: NULL, N, Y</font><br>';

var spectra_max_count = '<font color=blue><b>Spectra Max Count</b></font><br>'
		 + '<font color=#008080>spectra_max_count (acisparam)</font><br>'
		 + 'Total maximum expected number of counts for any spectrum to be scientifically <br>'
		 + 'analyzed from this observation. Input is required for any ACIS-I non-grating <br>'
		 + 'observation. <br>'
		 + '<font color=green>Value Ranges: NULL, 1 to  100000</font><br>';

var eventfilter_lower = '<font color=blue><b>Energy Lower</b></font><br>'
		 + '<font color=#008080>eventfilter_lower (acisparam)</font><br>'
		 + 'Energy Filter: Lower Event Threshold: <br>'
		 + 'The value of the threshold that will be applied.  Units are keV. <br>'
		 + 'If it is not NULL, Event filter must be Y.<br>'
		 + '<font color=green>Value Ranges: NULL, 0.0 to 15.0 </font><br>';
		
var eventfilter_higher = '<font color=blue><b>Range</b></font><br>'
		 + '<font color=#008080>eventfilter_higher (acisparam)</font><br>'
                 + 'The range of the events above the lower threshold which will not be <br>'
		 + 'filtered (in keV). (Example: to set an Energy filter from<br>'
                 + '0.1- 13 keV as suggested for VF mode.  Set Lower= 0.1 and range=12.9)<br>'
		 + '<font color=red>In many configurations, an Energy Range above 13 keV will risk telemetry saturation.</font><br>'
		 + 'If it is not NULL, Event filter must be Y.<br>'
		 + '<font color=green>Value Ranges: 0.0 to 15.0 </font><br>';
		
var spwindow = '<font color=blue><b>Window Filter</b></font><br>'
		 + '<font color=#008080>spwindow_flag (target)</font><br>'
   		 + 'By setting this field to "Y", the user can specify one or more spatial<br>'
   		 + 'window filters -- rectangular regions on specific chips -- within which<br>'
   		 + 'event candidates can be rejected according to their energy or to their<br>'
   		 + 'frequency of occurrence. The use of spatial windows does <i>not</i> affect<br>'
   		 + 'the way the CCD is read out, so there will be no impact on event pile-up.<br>'
   		 + 'Spatial windows will reduce the telemetry volume by removing event <br>'
		 + 'candidates.<br><br>'
   		 + 'As many as six spatial windows may be specified for each chip. If windows<br>'
   		 + 'overlap, the order in which they are defined in the RPS form is important:<br>'
   		 + 'for each event candidate centered at (CHIPX=<i>x</i>, CHIPY=<i>y</i>), the<br>'
   		 + 'on-board software examines all spatial windows defined for that chip,<br>'
   		 + '<i>in the order specified in the RPS form, lowest index first</i>, and<br>'
   		 + 'decides whether to reject the event based on the parameters in the <br>'
		 + '<i>first</i> window that contains that (<i>x,y</i>). <br>'
		 + 'If the event lies outside all windows, it will not be rejected <br>'
		 + 'by the window filter.<br>'
		 + 'If Y is selected, additional fields (Chip, Photon Inclusion, Start Row,<br>'
		 + ' Start Column, Height, Width, Lowest Energy, Energy Range, Sample Rate,<br>'
		 + ' Bias, Bias Frequency, Bias After) are valid<br><br>'
		 + '<font color=green>Value Ranges: NULL, Y, N </font><br>';






		
var ordr = '<font color=blue><b>Rank</b></font><br>'
		 + '<font color=#008080>ordr (aciswin)</font><br>'
                 + 'It is possible to have multiple windows.  With<br>'
                 + 'this keyword you can create addition windows or change<br>'
                 + 'the order among existing windows.  If you increase this value,<br>'
                 + 'numbers of input windows for<br>'
		 + 'Chip, Photon Inclusion, Start Row, Start Column, Height, Width,<br>'
		 + 'Lowest Energy, Energy Range, Sample Rate, Bias, Bias Frequency, Bias After<br>'
		 + 'are also increased<br>'
		 + '<font color=green>Value Ranges: > 1</font><br>';
		
var chip = '<font color=blue><b>Chip</b></font><br>'
		 + '<font color=#008080>chip (asicswin)</font><br></font><br>'
		 + 'Spatial Window. A chip name affected by this acis winodow constraint.<br>'
		 + '<font color=green>Value Ranges: NULL, I0, I1, I2, I3, S0, S1, S2, S3, S4, S5</font><br>';

var include_flag = '<font color=blue><b>Photon Inclusion</b></font><br>'
		 + '<font color=#008080>include_flag (asicswin)</font><br></font><br>'
		 + ' Spatial Window. A flag indicating whether the area defined below is included (I), or excluded (E). <br>'
		 + '<font color=green>Value Ranges: NULL, I, E/Exclude only after AO9</font><br>';
		
var spwindow_start_row = '<font color=blue><b>Start Row</b></font><br>'
		 + '<font color=#008080>start_row (asicswin)</font> <br>'
		 + ' Spatial Window. Starting row: The starting row that will be read.<br>'
		 + '<font color=green>Value Ranges: 0 to 895</font><br>';
		
var spwindow_start_column = '<font color=blue><b>Start Column</b></font><br>'
		 + '<font color=#008080>start_column (asicswin)</font> <br>'
		 + ' Spatial Window: Starting column: The starting column that will be read.<br>'
		 + '<font color=green>Value Ranges:  0 to 895</font><br>';
		
var spwindow_height = '<font color=blue><b>Height</b></font><br>'
		 + '<font color=#008080>height (asicswin)</font> <br>'
		 + ' Spatial Window: Height of Window: The number of rows of the window that will be read.<br>'
		 + '<font color=green>Value Ranges: 128 to  1023</font><br>';
		
var spwindow_width = '<font color=blue><b>Width</b></font><br>'
		 + '<font color=#008080>width (asicswin)</font> <br>'
		 + ' Spatial Window: Width of Window: The number of columns of the window that will be read.<br> '
		 + '<font color=green>Value Ranges: 128 to 1023</font><br>';
		
var spwindow_lower_threshold = '<font color=blue><b>Lowest Energy</b></font><br>'
		 + '<font color=#008080>lower_threshold (asicswin)</font> <br>'
                 + 'The value for the lower discrimination threshold.<br>'
                 + 'Units are keV. <b>This keyword only has meaning<br>'
                 + 'within th context of a spatial filter,<br>'
                 + 'otherwise use the ENERGY FILTER<br>'
		 + '<font color=green>Value Ranges: 0.0 to 15.0</font><br>';
		
var spwindow_pha_range = '<font color=blue><b>Energy Range</b></font><br>'
		 + '<font color=#008080>pha_range (asicswin) </font> <br>'
 		 + 'Energy Range for Window: The value for the energy range.<br>'
                 + 'Units are keV.  <b>This keyword only has meaning<br>'
                 + 'within the context of a spatial filter,<br>'
		 + '<font color=red>In many configurations, an Energy Range above 13 keV will risk telemetry saturation.</font><br>'
                 + 'otherwise use the ENERGY FILTER.<br>'
		 + '<font color=green>Value Ranges: 0.0 to 15.0</font><br>';
		
var spwindow_sample = '<font color=blue><b>Sample Rate</b></font><br>'
		 + '<font color=#008080>sample (asicswin)</font> <br>'
		 + ' Spatial Window: Sampling Rate: The value for the window readout rate.<br>'
		 + 'A value of "1" indicates that every event will be read.  A value of<br>'
		 + '"2"  means that every 2nd event will be read, etc.<br>'
		 + '<font color=green>Value Ranges: 1 to 512</font><br>';
		
var bias_request = '<font color=blue><b>Bias</b></font><br>'
		 + '<font color=#008080>bias_request (acisparam)</font><br>'
		 + 'Spatial Window: To request a bias different from normal.<br>'
		 + '<font color=green>Value Ranges:  N (after AO9) </font><br>';
		
var frequency = '<font color=blue><b>Bias Frequency</b></font><br>'
		 + '<font color=#008080>frequency(acisparam)</font><br>'
		 + 'Spatial Window: Designates how often to check the bias.<br>'
		 + '<font color=green>Value Ranges: NULL, 0 to 1</font><br>';
		
var bias_after = 'Bias After</b></font><br>'
		 + '<font color=#008080>bias_after(acisparam)</font><br>'
		 + 'Spatial Window: The algorithm used for checking the bias.<br>'
		 + '<font color=green>Value Ranges: NULL, Y, N</font><br>';
		
var too_id = '<font color=blue><b>TOO ID</b></font><br>'
		 + '<font color=#008080>too_id (too)</font><br>'
		 + 'TOO observation ID<br>';

var too_trig = '<font color=blue><b>TOO Trigger</b></font><br>'
		 + '<font color=#008080>too_trig (too)</font><br>'
		 + 'Conditions what trigger this TOO observation<br>';

var too_type = '<font color=blue><b>TOO Type</b></font><br>'
		 + '<font color=#008080>too_type (too)</font><br>'
                 + 'TOO Type describes the general lag interval<br>'
                 + 'in which the observation can be done after submission<br>'
                 + '(categories: 0-4days, 4-12days, 12-30days, >30days) -<br>'
		 + 'before AO 4 the options were just "fast" or "slow".<br>'


var too_start = '<font color=blue><b>Start</b></font><br>'
		 + '<font color=#008080>too_start (too)</font><br>'
		 + 'A TOO observation start time<br>';

var too_stop = '<font color=blue><b>Stop</b></font><br>'
		 + '<font color=#008080>too_stop (too)</font><br>'
		 + 'A TOO observation stop time<br>';

var too_followup =  '<font color=blue><b># of Follow-up Observations</b></font><br>'
		 + '<font color=#008080>too_followup (too)</font><br>'
		 + 'Numbers of follow up observation for this TOO event<br>';

var too_remarks = '<font color=blue><b>TOO Remarks</b></font><br>'
		 + '<font color=#008080>too_remarks (too)</font><br>'
		 + 'A remarks for this TOO observation<br>';

var remarks = '<font color=blue><b>Remarks</b></font><br>'
		 + '<font color=#008080>remarks (target)</font><br>'
		 + 'The remark area is  reservered  for constraints with when<br>'
		 + 'Constraints in Remarks? is Y, or  actions/considerations that<br>'
		 + 'apply to the observation. All other remarks should be written in comment area.<br>';

var comments = '<font color=blue><b>Comments</b></font><br>'
		 + '<font color=#008080>comments (target)</font><br>'
		 + 'This area is kept as a record of why a change was made. Comments here are <br>'
		 + 'read by Ocat staff. But if the comment impact the observation, contact<br>'
		 + 'CDO for follow through.'
		 + '<font color=red> Request for CDO approval must be written in here.</font><br>';


function WindowOpen(name){

        var new_window =
                window.open("","name","height=480,width=400,scrollbars=yes,resizable=yes","true");

        new_window.document.writeln('<html><head><title>Description</title></head><body>');
        new_window.document.write(name);
        new_window.document.writeln('</body></html>');
	new_window.document.close();
        new_window.focus();

}

//show me  -->
</script>

ENDOFHTML

#---------------------------------------
#------ read database to get the values
#---------------------------------------

read_databases();			

#
#---- check which ones are not canceled, discarded, observed, or achived
#
@schdulable_list = ();
open(SIN, "$obs_ss/sot_ocat.out");
while(<SIN>){
      	chomp $_;
      	if($_ =~ /scheduled/ || $_ =~ /unobserved/){
              	@atemp = split(/\^/, $_);
            	$atemp[1] =~ s/\s+//g;
		push(@schdulable_list, $atemp[1]);
       	}
}
close(SIN);


#------------------------------------------
#------ read MP scheduled observation list
#------------------------------------------

@mp_scheduled_list = ();
open(FH, "$obs_ss/scheduled_obs_list");

while(<FH>){
	chomp $_;
	@atemp = split(/\s+/, $_);
	push(@mp_scheduled_list, $atemp[0]);
}
close(FH);

#-------------------------------------------------------------------------------------
#----- read a list of observations which are in MP scheduled list, but have a special
#----- permission to edit.
#-------------------------------------------------------------------------------------

#@mp_edit_permit = ();
#open(FH, "$obs_ss/mp_edit_permit");
#
#while(<FH>){
#	chomp $_;
#	push(@mp_edit_permit, $_);
#}
#close(FH);

#----------------------------------------------------------
#--- check whether the observation is in an active OR list
#----------------------------------------------------------

$mp_check = 0;
CHK_OUT:
foreach $check (@mp_scheduled_list){
	if($check =~ /$obsid/){
#		foreach $comp (@mp_edit_permit){
#			if($comp =~  /$obsid/){
#				last CHK_OUT;
#			}
#		}
		$mp_check = 1;
		last;
	}
}

#----------------------------------------------------------------------------------
#------- start printing a html page here.
#------- there are three distinct html page. one is Ocat Data Page (data_input_page),
#------- second is Submit page (prep_submit), and the lastly, Oredit page (oredit).
#----------------------------------------------------------------------------------

$no_access  = 0;					# this indicator used for special user previledge
$send_email = 'yes';

print start_html(-bgcolor=>"white",-title=>"Ocat Data Page");	# this says that we are starting a html page

print start_form();

$time_ordr_special = 'no';
$roll_ordr_special = 'no';
$ordr_special      = 'no';
$check             = param("Check");			# a param which indicates which page to be displayed 

print hidden(-name=>'send_email', -value=>"$send_email");

#-------------------------------------------------
#--------- checking password!
#-------------------------------------------------

if($check eq ''){
	$chg_user_ind = param('chg_user_ind');
	match_user();                           	# sub to check inputed user and password

#---------------------------------------------------------------
#--------- if a user and a password do not match ask to re-type
#---------------------------------------------------------------

	if($chg_user_ind eq 'yes'){
		password_check();
#	}elsif(($usint_on ne 'yes' && $usint_on ne 'test_yes') && ($pass eq '' || $pass eq 'no')){
	}elsif($pass eq '' || $pass eq 'no'){
        	if(($pass eq 'no') && ($submitter  ne ''|| $pass_word ne '')){

                	print "<h3><font color='red'>Name and/or Password are not valid.</h3>";

        	}

        	password_check();       			# this one create password input page

#	}elsif($usint_on =~ /yes/ || $pass eq 'yes'){         	# ok a user and a password matched
	}elsif($pass eq 'yes'){ 		        	# ok a user and a password matched

#-------------------------------------------
#------ check whether s/he is a special user
#-------------------------------------------

        	$sp_user = 'no';

		if($usint_on =~ /yes/){
			$sp_user   = 'yes';
			$access_ok = 'yes';
###		}else{
        		special_user();			# sub to check whether s/he is a special user
###                	pi_check();			# sub to check whether the pi has an access

			print hidden(-name=>'send_email', -value=>"$send_email");
		}

$sp_user = 'yes';				#----- this is a temporary measure to let people in Oct 1, 2013
		if($sp_user eq 'yes'){
                        if($prev_app == 0){
                                data_input_page();      # sub to display data for edit
                        }else{
                                data_close_page();
                        }

        	}elsif($access_ok eq 'yes' && $sp_user eq 'no'){

#-------------------------------------------------------------------
#------ if s/he has an access to the data, check a few more things
#-------------------------------------------------------------------

                	if($access_ok eq 'yes'){        	# yes s/he has an access
				$access_ok = 'yes';
				print hidden(-name=>'access_ok',   -value=>'yes');
				print hidden(-name=>'pass_status', -value=>'match');

				if($status =~ /^OBSERVED/i || $status =~ /^ARCHIVED/i 
				      || $status =~ /^CANCELED/i || $status =~ /^DISCARDED/i){

					data_close_page();	# sub to display data (not editable)
				}else{
                        		data_input_page();	# sub to display data for edit
				}
                	}else{                      	        # no s/he does not have one
				$no_access = 1;		        # telling no access
                        	data_close_page();
                	}
        	}else{
			print hidden(-name=>'access_ok', -value=>'no');
			$no_access = 1;				# telling no access
			print '<h2 style="color:red">You are using a wrong user name. Plese try another one (HEAD user name). </h2>';
                        data_close_page();
		}
	}else{
        	print 'Something wrong. Exit<br>';
        	exit(1);
	}
}

#----------------------------------
#--- password check finished.
#----------------------------------

pass_param();			# sub to pass parameters between submitting data

#-------------------------------------------------------------------------
#--- only if a user can access to the observation data, s/he can go futher
#-------------------------------------------------------------------------

if($access_ok eq 'yes'){	

#----------------------------------------------------------------------------
#------- first for the case that the observation is already done and closed.
#----------------------------------------------------------------------------

	if($sp_user eq 'no' 
		&& ($status =~ /^OBSERVED/i || $status =~ /^ARCHIVED/i || $status =~ /^CANCELED/i || $status =~ /^DISCARDED/i)){

		if($check eq 'Clone' || $check eq 'PREVIOUS PAGE'){
	
			pass_param();
			print_clone_page();			# sub to  print comment entry for clone case

#        	}elsif($check eq 'REMOVE' && $prev_app > 0){
#
#                	print start_form();
#                	pass_param();
#                	rm_from_approved_list();
#                	$prev_app = 0;
#                	data_input_page();
#
		}elsif($check eq 'Submit Clone'){

			pass_param();
			read_name();
			prep_submit();				# sub to prepare the data for submission
	
			if($usr_ind == 0){
				user_warning();			# sub to warn a user, a user name mistake 
			}else{
				chk_entry();			# sub to check entries are in given ranges
				if($cdo_w_cnt > 0){
					$cout_name = "$obsid".'_cdo_warning';
					open(OUT, ">$temp_dir/$cout_name");
					foreach $ent (@cdo_warning){
						print OUT "$ent\n";
					}
					close(OUT);
#					system("chmod 777 $temp_dir/*cdo_warning");
				}
			}

		}elsif($check eq 'FINALIZE'){

			pass_param();

#
#---once USINT  can be submited OPT# selection for CCDs, comment out the next sub
#
#---- COMMENTED OUT THIS PART ON 09/27/06
###			keep_ccd_selection_record();

#
#--- if this is an ARCOPS check and approve request, add the obsid to the list
#

			if($asis =~ /ARCOPS/i){
				$date = `date '+%D'`;
				chomp $date;
			
				open(OUT, ">>$ocat_dir/arcops_list");
				print OUT "$obsid\t$date\t$submitter\t$targname\t$instrument\t$grating\n";
				close(OUT);
#				system("chmod 777 $ocat_dir/arcops_list");
			}

			oredit();				# sub to finalize and  send out email

		}else{

			data_close_page();
		}

#-------------------------------------------------------------------------
#--- if time, roll, and window constraints may need input page update...
#-------------------------------------------------------------------------

	}elsif($check eq '     Add Time Rank     '){

        	$time_ordr         = param("TIME_ORDR");
        	$roll_ordr         = param("ROLL_ORDR");
        	$aciswin_no        = param("ACISWIN_NO");
        	$time_ordr_special = 'yes';
        	$roll_ordr_special = 'no';
        	$ordr_special      = 'no';
        	$time_ordr++;

        	pass_param();                           # a sub which passes all parameters between pages
        	data_input_page();                      # a sub to  print ocat data page

	}elsif($check eq '     Add Roll Rank     '){

        	$time_ordr         = param("TIME_ORDR");
        	$roll_ordr         = param("ROLL_ORDR");
        	$aciswin_no        = param("ACISWIN_NO");
        	$time_ordr_special = 'no';
        	$roll_ordr_special = 'yes';
        	$ordr_special      = 'no';
        	$roll_ordr++;

        	pass_param();                           
        	data_input_page();                      

	}elsif($check eq '     Add New Window Entry     '){

        	$time_ordr         = param("TIME_ORDR");
        	$roll_ordr         = param("ROLL_ORDR");
        	$aciswin_no        = param("ACISWIN_NO");
        	$time_ordr_special = 'no';
        	$roll_ordr_special = 'no';
        	$ordr_special      = 'yes';

        	$aciswin_no++;
	
		$add_window_rank   = 1;			# need this to check whether ADD button is selected 
	
        	pass_param();                           
        	data_input_page();                      

#------------------------------------------------
#--- or just s/he wants to update the main page.
#------------------------------------------------

	}elsif($check eq '     Update     '){
	
		pass_param();				
		data_input_page();			

#-------------------------------------------------------------------------------------------
#-------- change submitted to see no errors in the changes, and then display the information
#-------------------------------------------------------------------------------------------

	}elsif($check eq 'Submit'){
	
		pass_param();				# sub to read passed parameters
		read_name();				# sub to read descriptive name of database name
	
		prep_submit();				# sub to  print a modification check page
	
		if($usr_ind == 0){
			user_warning();			# sub to warn a user, a user name mistake 

#-----------------------------------------------------------------------------------
#---- ASIS and REMOVE cases, directly go to final submission. otherwise check errors.
#-----------------------------------------------------------------------------------

		}elsif($asis eq 'ASIS' || $asis eq 'REMOVE'){

			submit_entry();			# check and submitting the modified input values
		}elsif($asis eq 'SEND_MAIL'){

			send_mail_to_usint();		# sending a request of a full support to USINT

		}else{
			chk_entry();			# check entries are in given ranges

			if($cdo_w_cnt > 0){
				$cout_name = "$obsid".'_cdo_warning';
				open(OUT, ">$temp_dir/$cout_name");
				foreach $ent (@cdo_warning){
					print OUT "$ent\n";
				}
				close(OUT);
#				system("chmod 777 $temp_dir/*cdo_warning");
			}
		}

#-----------------------------------------
#---- submit the change and send out email
#-----------------------------------------

	}elsif($check eq 'FINALIZE'){

		pass_param();


#
#--- only when the observations is already on an active list, and there is actually
#--- changes, send a warning email to MP
#
		if($mp_check > 0 && $cnt_modified > 0){
			send_email_to_mp();		# sending warning email to MP
		}

#
#---once USINT  can be submited OPT# selection for CCDs, comment out the next sub
#
#---- COMMENTED OUT THIS PART ON 09/27/06
###		keep_ccd_selection_record();

#
#--- if this is an ARCOPS check and approve request, add the obsid to the list
#

		if($asis =~ /ARCOPS/i){
        		$date = `date '+%D'`;
        		chomp $date;

        		open(OUT, ">>$ocat_dir/arcops_list");
        		print OUT "$obsid\t$date\t$submitter\t$targname\t$instrument\t$grating\n";
        		close(OUT);
#        		system("chmod 777 $ocat_dir/arcops_list");
		}


		oredit();				#  a sub to print a mail out page

#------------------------------
#----- back to data entry page
#------------------------------

	}elsif($check eq 'PREVIOUS PAGE'){		# this prints ocat data page without losing
							# input data typed in after moved to submitting page
		system("rm -f $temp_dir/*.$sf");
		pass_param();
		data_input_page();

#	}elsif($check eq 'REMOVE' && $prev_app > 0){
#
#        	print start_form();
#        	pass_param();
#        	rm_from_approved_list();
#        	$prev_app = 0;
#        	data_input_page();
#

#----------------------------------------------------------------------------------------------------
#--- if no action is taken yet, it comes here; you see this page first (after a user/a password page)
#----------------------------------------------------------------------------------------------------

	}else{
        	if($prev_app == 0){
                	data_input_page();              # just print ocat data page
#        	}else{
#                	data_close_page();
        	}
	}
}							#---- the end of access_ok loop

print end_html();					# closing html page

#################################################################################################
#---- the main script finishes here. sub-scripts start here.
#################################################################################################



#########################################################################
### password_check: open a user - a password input page               ###
#########################################################################

sub password_check{
	print '<h3>Please type your user name and password<h3>';
        print '<table><tr><th>Name</th><td>';
        print textfield(-name=>'submitter', -value=>'', -size=>20);
        print '</td></tr><tr><th>Password</th><td>';
        print password_field( -name=>'password', -value=>'', -size=>20);
        print '</td></tr></table><br>';

	print hidden(-name=>'Check', -override=>'', -value=>'');
        print '<input type="submit" name="Check" value="Submit">';
}

#########################################################################
### match_user: check a user and a password matches                   ###
#########################################################################

sub match_user{
	if($submitter eq ''){
        	$submitter = param('submitter');
        	$submitter =~s/^\s+//g;
        	$pass_word = param('password');
        	$pass_word =~s/^\s+//g;
	}
	
	$sp_status = 'no';
	if($usint_on =~ /yes/){
		$sp_status = 'yes';
#		$pass      = 'yes';
	}
	if($pass eq 'yes'){
		$pass_status = 'match';
	}else{
        	OUTER:
        	foreach $test_name (@user_name_list){
                	$ppwd  = $pwd_list{"$submitter"};
                	$ptest = crypt("$pass_word","$ppwd");
	
                	if(($submitter =~ /$test_name/i) && ($ptest  eq $ppwd)){
                        	$pass_status = 'match';
                        	last OUTER;
                	}
        	}
	}

	if(($usint_on =~ /yes/) && ($sp_status eq 'yes') && ($pass_status eq 'match')){
		$pass = 'yes';
		print hidden(-name=>'pass', -override=>"$pass", -value=>"$pass");
        }elsif(($usint_on =~ /no/) && ($pass_status eq 'match')){
                $pass = 'yes';
		print hidden(-name=>'pass', -override=>"$pass", -value=>"$pass");
        }else{
                $pass = 'no';
        }
}

#########################################################################
### special_user: check whether the user is a special user            ###
#########################################################################

sub special_user{

        $sp_user = 'no';
	$user    = lc($submitter);
        OUTER:
        foreach $comp (@special_user){
                if($user eq $comp){
                        $sp_user = 'yes';
                        last OUTER;
                }
        }
}

###################################################################################
### pi_check: check whether the observer has an access to the data              ###
###################################################################################

sub pi_check{
#
#---- read the list of scheduled/unobserved observations
#
	open(FH, "$obs_ss/access_list");
	@access_obsid     = ();
	@access_status    = ();
	@access_pi_name   = ();
	@access_pi_first  = ();
	@access_observer  = ();
	@access_obs_first = ();
	$access_cnt       = 0;
	while(<FH>){
		chomp $_;
		@atemp = split(/\s+/, $_);
		push(@access_obsid,     $atemp[0]);
		push(@access_status,    $atemp[1]);
		push(@access_type,      $atemp[2]);

		@btemp = split(/:/,     $atemp[3]);
		push(@access_pi_name,   $btemp[0]);
		push(@access_pi_first,  $btemp[1]);

		@btemp = split(/:/,     $atemp[4]);
		push(@access_observer,  $btemp[0]);
		push(@access_obs_first, $btemp[1]);
		$access_cnt++;
	}
	close(FH);
#
#----- read everyone's email addresses
#
	open(FH, "$pass_dir/user_email_list");
	@usr_last_name     = ();
	@usr_first_name    = ();
	@usr_mail_name     = ();
	@usr_email_address = ();
	$email_no = 0;
	while(<FH>){
		chomp $_;
		@atemp = split(/\t+/, $_);
		push(@usr_last_name,     $atemp[0]);
		push(@usr_first_name,    $atemp[1]);
		push(@usr_mail_name,     $atemp[2]);
		push(@usr_email_address, $atemp[3]);
		$email_no++;
	}
	close(FH);
#
#----- check who from cxc proposed observations
#
#	open(FH, "$pass_dir/cxc_user");
#	@cxc_user_list = ();
#	while(<FH>){
#		chomp $_;
#		$person = lc ($_);
#		push(@cxc_user_list, $person);
#	}
#	close(FH);
#
#
#
#----- check who from experts are proposed observations
#
#	open(FH, "$pass_dir/exp_user");
#	@exp_user_list = ();
#	while(<FH>){
#		chomp $_;
#		$person = lc ($_);
#		push(@exp_user_list, $person);
#	}
#	close(FH);

#
#----- check who is from general user list
#
	open(FH, "$pass_dir/gen_user");
	@gen_user_list = ();
	while(<FH>){
		chomp $_;
		$person = lc ($_);
		push(@gen_user_list, $person);
	}
	close(FH);

	$ent_no = 0;
	OUTER:
	foreach $comp (@access_obsid){
		if($obsid == $comp){
			last OUTER;
		}
		$ent_no++;
	}

	$access_ok        = 'no';
	$cxc_usr_chk      = 'no';
	$gto_ok           = 'no';
	$send_email       = 'yes';
	$pi_of_obs        = lc ($access_pi_name[$ent_no]);
	$pi_first_of_obs  = lc ($access_pi_first[$ent_no]);
	$obs_of_obs       = lc ($access_observer[$ent_no]);
	$obs_first_of_obs = lc ($access_obs_first[$ent_no]);
	$pi_mail_name     = '';
	$pi_mail_address  = '';
	$obs_mail_name    = '';
	$obs_mail_address = '';

	$pi_short         =  $pi_of_obs;
	$pi_short         =~ s/\s+//g;
	$pi_f_short       =  $pi_first_of_obs;
	$pi_f_short       =~ s/\s+//g;
	$obs_short        =  $obs_of_obs;
	$obs_short        =~ s/\s+//g;
	$obs_f_short      =  $obs_first_of_obs;
	$obs_f_short      =~ s/\s+//g;

	for($k = 0; $k < $email_no; $k++){
		$comp1 =  $usr_last_name[$k];
		$comp1 =~ s/\s+//g;
		$comp2 =  $usr_first_name[$k];
		$comp2 =~ s/\s+//g;
		if($pi_short eq $comp1 && $pi_f_short eq $comp2){	# PI name and email address
			$pi_mail_name     = $usr_mail_name[$k];
			$pi_mail_address  = $usr_email_address[$k];
			$email_address    = $usr_email_address[$k];
		}
		if($obs_short eq $comp1 && $obs_f_short eq $comp2){	# Observer name and email address
			$obs_mail_name    = $usr_mail_name[$k];
			$obs_mail_address = $usr_email_address[$k];
			$email_address    = $usr_email_address[$k];
		}
	}
		
	if($sp_user eq 'yes'){
		$access_ok     = 'yes';
		$email_address = "$user".'@head.cfa.harvard.edu';
	}elsif($usint_on =~ /no/){
#
#--- "$mtaobs" and 'special' are special: they are a super observers who can assess all GTO observation as a user
#
		if(($user eq "$mtaobs"|| $user eq 'special')  
				&& ($access_type[$ent_no] =~ /GTO/i || $access_type[$ent_no] =~ /GO/i) ){
			$access_ok     = 'yes';
			$gto_ok        = 'yes';
			$email_address = "$test_email";			# email is sent to only to a tester
			if($user eq 'special'){
				$send_email = 'no';
			}
		}elsif($user eq $pi_mail_name || $user eq $obs_mail_name){
			foreach $chk_usr (@gen_user_list){
				if($user eq $chk_usr){
					$access_ok   = 'yes';
					$cxc_usr_chk = 'yes';
				}
			}
#			foreach $cxc_usr (@cxc_user_list){
#				if($user eq $cxc_usr){
#					$access_ok   = 'yes';
#					$cxc_usr_chk = 'yes';
#				}
#			}
#			foreach $exp_usr (@exp_user_list){
#				if($user eq $exp_usr){
#					$access_ok   = 'yes';
#					$cxc_usr_chk = 'yes';
#				}
#			}
#			if($access_type[$ent_no] =~ /GTO/i){
#				$access_ok = 'yes';
#				$gto_ok    = 'yes';
#			}	
			if($user eq $pi_mail_name){
				$email_address = $pi_mail_address;
			}else{
				$email_address = $obs_mail_address;
			}
		}
	}

#--------------------------------------------------------------------------------------
#---- if scheduled obs date is less than 30 days from today; GTO cannot edit the field
#--------------------------------------------------------------------------------------

	if($sp_user eq 'no' && $cxc_usr_chk eq 'no'){
		lts_date_check();			# check ltd_date is in 30 days or not
		if($lts_more30 eq 'no'){
			$access_ok = 'no';
		}
	}
	print hidden(-name=>'access_ok', -value=>"$access_ok");
	print hidden(-name=>'pass', -value=>"$pass");
	print hidden(-name=>'email_address', -value=>"$email_address");
}

################################################################################
### pass_param: passing cgi parameter values to the next window              ###
################################################################################

sub pass_param {

#### this sub receives parameter passed from the previous cgi page (form, pop-up window, hidden param etc),
#### converts them to variables which are usable for the new cgi page.
#### the most of the param were changed using @paramarray, but special cases (which allows multiple and
#### possibly undefind # of order), such as time constraint, roll constraint, and acis window constaint are
#### handled indivisually.
#### there are also a section which handles  different display names than database names.

#-------------------------------------------
#------- password check	and submiiter (user)
#-------------------------------------------

	$sp_user       = param('sp_user');
	$access_ok     = param('access_ok');
	$pass          = param('pass');
	$submitter     = param('submitter');
	$email_address = param('email_address');
	$si_mode       = param('SI_MODE');
	$send_email    = param('send_email');
	
#----------------------------
#------- other special cases
#----------------------------

	$awc_cnt       = param('awc_cnt');			# ACIS Window Constraints Counter 
	$awc_ind       = param('awc_ind');			# ACIS Window Constraints Indicator
	if($add_window_rank != 1){
		$aciswin_no    = param('ACISWIN_NO');		# ACIS Window Constraints Rank Counter
	}

#---------------------
#------- house keeping
#---------------------

	$sf            = param('tmp_suf');			# suffix for temp file written in $temp_dir
								# this avoids to over write other user's file
								# see "submit_entry"
#
#--- tell you how many parameters are modified
#
	$cnt_modified  = param('cnt_modified');

#----------------------
#------- general cases
#----------------------

	foreach $ent (@paramarray){				# paramarray has all parameter's names
#
#--- time order, roll order, and window space order must be checked
#
                if($time_ordr_special =~ /yes/i){
                        if($ent =~ /TIME_ORDR/i){
                                $time_ordr_special = 'no';
                        }else{
                                $new_entry    = lc ($ent);
                                ${$new_entry} = param("$ent");
                        }
                }elsif($roll_ordr_special =~ /yes/i){
                        if($ent =~ /ROLL_ORDR/i){
                                $roll_ordr_special = 'no';
                        }else{
                                $new_entry    = lc ($ent);
                                ${$new_entry} = param("$ent");
                        }
                }elsif($ordr_special =~ /yes/i){
                        if($ent =~ /ACISWIN_ID/i){
                                $ordr_special = 'no';
                        }else{
                                $new_entry    = lc ($ent);
                                ${$new_entry} = param("$ent");
                        }
#
#--- all other cases
#
                }else{
			$new_entry    = lc ($ent);
			${$new_entry} = param("$ent");
		}
	}

#-------------------------------------------------------------------------------------------------------
#-------- time constarint case: there could be more than 1 order of data sets 
#-------- (also roll and window constraints)
#-------------------------------------------------------------------------------------------------------

	$time_ordr_add = param("TIME_ORDR_ADD");                #--- if window constraint is addred later, this will be 1

	for($j = 1; $j <= $time_ordr; $j++){
#
#---- if window constraint is set to Null, set tstart and stop to Null, too
#
		$name = 'WINDOW_CONSTRAINT'."$j";
		$window_constraint[$j] = param("$name");
		$null_ind = 0;
		if($window_constraint[$j] eq 'NO'
		    || $window_constraint[$j] eq 'NULL'
		    || $window_constraint[$j] eq 'NONE'
		    || $window_constraint[$j] eq ''
		    || $window_constraint[$j] eq 'N'){
			$null_ind = 1;
		}

		foreach $ent ('START_DATE', 'START_MONTH', 'START_YEAR', 'START_TIME',
			       'END_DATE',  'END_MONTH',   'END_YEAR',   'END_TIME',
			       'TSTART',    'TSTOP'){
			$name  = "$ent"."$j";
			$val   = param("$name");
			$lname = lc($ent);

			if($null_ind == 0){
				${$lname}[$j] = $val;
			}else{
				${$lname}[$j] = '';
			}
		}

		$tstart_new[$j] = '';					# recombine tstart and tstop
		if($start_month[$j] ne 'NULL'){
			if($start_month[$j] eq 'Jan'){$start_month[$j] = '01'}
			elsif($start_month[$j] eq 'Feb'){$start_month[$j] = '02'}
			elsif($start_month[$j] eq 'Mar'){$start_month[$j] = '03'}
			elsif($start_month[$j] eq 'Apr'){$start_month[$j] = '04'}
			elsif($start_month[$j] eq 'May'){$start_month[$j] = '05'}
			elsif($start_month[$j] eq 'Jun'){$start_month[$j] = '06'}
			elsif($start_month[$j] eq 'Jul'){$start_month[$j] = '07'}
			elsif($start_month[$j] eq 'Aug'){$start_month[$j] = '08'}
			elsif($start_month[$j] eq 'Sep'){$start_month[$j] = '09'}
			elsif($start_month[$j] eq 'Oct'){$start_month[$j] = '10'}
			elsif($start_month[$j] eq 'Nov'){$start_month[$j] = '11'}
			elsif($start_month[$j] eq 'Dec'){$start_month[$j] = '12'}
		}

		if($start_date[$j] =~ /\d/ && $start_month[$j] =~ /\d/ && $start_year[$j] =~ /\d/ ){
			@ttemp   = split(/:/, $start_time[$j]);
			$tind    = 0;
			$time_ck = 0;

			foreach $tent (@ttemp){
				if($tent =~ /\D/ || $tind eq ''){
					$tind++;
				}else{
					$time_ck = "$time_ck"."$tent";
				}
			}

			if($tind == 0){
				$tstart_new  = "$start_month[$j]:$start_date[$j]:$start_year[$j]:$start_time[$j]";
				$chk_start = -9999;
				if($tstart_new =~ /\s+/ || $tstart_new == ''){
				}else{
					$tstart[$j]    = $tstart_new;
				}
			}
		}
		
		$tstop_new[$j] = '';
		if($end_month[$j] ne 'NULL'){
			if($end_month[$j] eq 'Jan'){$end_month[$j] = '01'}
			elsif($end_month[$j] eq 'Feb'){$end_month[$j] = '02'}
			elsif($end_month[$j] eq 'Mar'){$end_month[$j] = '03'}
			elsif($end_month[$j] eq 'Apr'){$end_month[$j] = '04'}
			elsif($end_month[$j] eq 'May'){$end_month[$j] = '05'}
			elsif($end_month[$j] eq 'Jun'){$end_month[$j] = '06'}
			elsif($end_month[$j] eq 'Jul'){$end_month[$j] = '07'}
			elsif($end_month[$j] eq 'Aug'){$end_month[$j] = '08'}
			elsif($end_month[$j] eq 'Sep'){$end_month[$j] = '09'}
			elsif($end_month[$j] eq 'Oct'){$end_month[$j] = '10'}
			elsif($end_month[$j] eq 'Nov'){$end_month[$j] = '11'}
			elsif($end_month[$j] eq 'Dec'){$end_month[$j] = '12'}
		}
		if($end_date[$j] =~ /\d/ && $end_month[$j] =~ /\d/ && $end_year[$j] =~ /\d/ ){
			@ttemp   = split(/:/, $end_time[$j]);
			$tind    = 0;
			$time_ck = 0;

			foreach $tent (@ttemp){
				if($tent =~ /\D/ || $tind eq ''){
					$tind++;
				}else{
					$time_ck = "$time_ck"."$tent";
				}
			}

			if($tind == 0){
				$tstop_new = "$end_month[$j]:$end_date[$j]:$end_year[$j]:$end_time[$j]";
				$chk_end = -9999;
				if($tstop_new =~ /\s+/ || $tstop_new == ''){
				}else{
					$tstop[$j] = $tstop_new;
				}
			}
		}

		if($window_constraint[$j]    eq 'Y')         {$dwindow_constraint[$j] = 'CONSTRAINT'}
		elsif($window_constraint[$j] eq 'CONSTRAINT'){$dwindow_constraint[$j] = 'CONSTRAINT'}
		elsif($window_constraint[$j] eq 'P')         {$dwindow_constraint[$j] = 'PREFERENCE'}
		elsif($window_constraint[$j] eq 'PREFERENCE'){$dwindow_constraint[$j] = 'PREFERENCE'}
#		elsif($window_constraint[$j] eq 'N')         {$dwindow_constraint[$j] = 'NONE'}
#		elsif($window_constraint[$j] eq 'NONE')      {$dwindow_constraint[$j] = 'NONE'}
#		elsif($window_constraint[$j] eq 'NULL')      {$dwindow_constraint[$j] = 'NULL'}
#		elsif($window_constraint[$j] eq '')          {$dwindow_constraint[$j] = 'NULL'}
	}

#
#--- added 10/19/11
#
	if($check eq 'Remove Null Time Entry '){
		if($time_ordr > 1){
			$new_ordr = $time_ordr;
			TOUT1:
			for($j = 1; $j <= $time_ordr; $j++){
				if($window_constraint[$j] =~ /Y/i || $window_constraint[$j] =~ /CONST/i || $window_constraint[$j] =~ /P/i){
					next TOUT1;
				}
				for($jj = $j+1; $jj <= $time_ordr; $jj++){
					if($window_constraint[$jj] =~ /Y/i || $window_constraint[$jj] =~ /CONST/i || $window_constraint[$jj] =~ /P/i){
						$window_constraint[$j]   = $window_constraint[$jj];
						$dwindow_constraint[$j]  = $dwindow_constraint[$jj];

						$start_month[$j]	 = $start_month[$jj];
						$start_date[$j]	         = $start_date[$jj];
						$start_year[$j]	         = $start_year[$jj];
						$start_time[$j]	         = $start_time[$jj];
						$end_month[$j]	         = $end_month[$jj];
						$end_date[$j]	         = $end_date[$jj];
						$end_year[$j]	         = $end_year[$jj];
						$end_time[$j]	         = $end_time[$jj];

						$tstart[$j]	         = $tstart[$jj];
						$tstop[$j]	         = $tstop[$jj];

#						$window_constraint[$jj]  = 'NULL';
#						$dwindow_constraint[$jj] = 'NULL';
						$start_month[$jj] 	 =  '';
						$start_date[$jj]	 =  '';
						$start_year[$jj]	 =  '';
						$start_time[$jj]	 =  '';
						$end_month[$jj]	         =  '';
						$end_date[$jj]	         =  '';
						$end_year[$jj]	         =  '';
						$end_time[$jj]	         =  '';

						$tstart[$jj]	         =  '';
						$tstop[$jj]	         =  '';

						$new_ordr--;
						next TOUT1;
					}elsif($jj == $time_ordr){

#						$window_constraint[$j]   = 'NULL';
#						$dwindow_constraint[$j]  = 'NULL';
						$start_month[$j]	 =  '';
						$start_date[$j]	         =  '';
						$start_year[$j]	         =  '';
						$start_time[$j]	         =  '';
						$end_month[$j]	         =  '';
						$end_date[$j]	         =  '';
						$end_year[$j]	         =  '';
						$end_time[$j]	         =  '';

						$tstart[$j]	         =  '';
						$tstop[$j]	         =  '';

						$new_ordr--;
						last TOUT1;
					}

				}
			}
			$time_ordr = $new_ordr;
		}
		$check = '';
	}


        if($window_constraint[0] =~ /Y/ || $window_constraint[0] =~ /C/i || $window_constraint[0] =~ /P/i){
                $window_flag = 'Y';
        }

#------------------------------
#-------- roll constraint case
#------------------------------

	$roll_ordr_add = param("ROLL_ORDR_ADD");                #--- if roll constraint add is requested later, this will be 1

	for($j = 1; $j <= $roll_ordr; $j++){
		foreach $ent ('ROLL_CONSTRAINT','ROLL_180','ROLL','ROLL_TOLERANCE'){
			$name         = "$ent"."$j";
			$val          =  param("$name");
			$lname        = lc($ent);
			${$lname}[$j] = $val;
		}
		if($roll_constraint[$j]    eq 'Y')         {$droll_constraint[$j] = 'CONSTRAINT'}
		if($roll_constraint[$j]    eq 'CONSTRAINT'){$droll_constraint[$j] = 'CONSTRAINT'}
		elsif($roll_constraint[$j] eq 'P')         {$droll_constraint[$j] = 'PREFERENCE'}
		elsif($roll_constraint[$j] eq 'PREFERENCE'){$droll_constraint[$j] = 'PREFERENCE'}
#		elsif($roll_constraint[$j] eq 'N')         {$droll_constraint[$j] = 'NONE'}
#		elsif($roll_constraint[$j] eq 'NONE')      {$droll_constraint[$j] = 'NONE'}
#		elsif($roll_constraint[$j] eq 'NULL')      {$droll_constraint[$j] = 'NULL'}
#		elsif($roll_constraint[$j] eq '')          {$droll_constraint[$j] = 'NULL'}

		if($roll_180[$j]    eq 'Y')   {$droll_180[$j] = 'YES'}
		elsif($roll_180[$j] eq 'YES') {$droll_180[$j] = 'YES'}
		elsif($roll_180[$j] eq 'N')   {$droll_180[$j] = 'NO'}
		elsif($roll_180[$j] eq 'NO')  {$droll_180[$j] = 'NO'}
		elsif($roll_180[$j] eq 'NULL'){$droll_180[$j] = 'NULL'}
		elsif($roll_180[$j] eq '')    {$droll_180[$j] = 'NULL'}
	}


#
#--- added 10/20/11
#
	if($check eq 'Remove Null Roll Entry '){
		if($roll_ordr > 1){
			$new_ordr = $roll_ordr;
			TOUT1:
			for($j = 1; $j <= $roll_ordr; $j++){
				if($roll_constraint[$j] =~ /Y/i || $roll_constraint[$j] =~ /CONST/i || $roll_constraint[$j] =~ /P/i){
					next TOUT1;
				}
				for($jj = $j+1; $jj <= $roll_ordr; $jj++){
					if($roll_constraint[$jj] =~ /Y/i || $roll_constraint[$jj] =~ /CONST/i || $roll_constraint[$jj] =~ /P/i){
						$roll_constraint[$j]   = $roll_constraint[$jj];
						$droll_constraint[$j]  = $droll_constraint[$jj];
						$roll_180[$j]	       = $roll_180[$jj];
						$droll_180[$j]	       = $droll_180[$jj];
						$roll[$j]	       = $roll[$jj];
						$roll_tolerance[$j]    = $roll_tolerance[$jj];

						$roll_constraint[$jj]  = 'NULL';
						$droll_constraint[$jj] = 'NULL';
						$roll_180[$jj]	       = 'NULL';
						$droll_180[$jj]	       = 'NULL';
						$roll[$jj]	       = '';
						$roll_tolerance[$jj]   = '';

						$new_ordr--;
						next TOUT1;

					}elsif($jj == $roll_ordr){
						$roll_constraint[$jj]  = 'NULL';
						$droll_constraint[$jj] = 'NULL';
						$roll_180[$jj]	       = 'NULL';
						$droll_180[$jj]	       = 'NULL';
						$roll[$jj]	       = '';
						$roll_tolerance[$jj]   = '';

						$new_ordr--;
						next TOUT1;
					}
				}
			}
			$roll_ordr = $new_ordr;
		}
		$check = '';
	}


#--------------------------
#-------- acis window case
#--------------------------

	if($spwindow =~ /Y/i){
		for($j = 0; $j <  $aciswin_no; $j++){
			foreach $ent ('ACISWIN_ID', 'ORDR', 'CHIP',
#					'INCLUDE_FLAG',
					'START_ROW','START_COLUMN','HEIGHT','WIDTH',
					'LOWER_THRESHOLD','PHA_RANGE','SAMPLE'){
				$name         = "$ent"."$j";
				$val          =  param("$name");
#
#--- added 08/04/11
#
				if($name =~ /LOWER_THRESHOLD/i && $val !~ /\d/){
					$val  = 0.08;
				}elsif($name =~ /PHA_RANGE/i && $val !~ /\d/){
					$val  = 13.0;
				}

				$lname        = lc($ent);
				${$lname}[$j] = $val;
			}
##			if($include_flag[$j]    eq 'I')      {$dinclude_flag[$j] = 'INCLUDE'}
##			elsif($include_flag[$j] eq 'INCLUDE'){$dinclude_flag[$j] = 'INCLUDE'}
##			elsif($include_flag[$j] eq 'E')      {$dinclude_flag[$j] = 'EXCLUDE'}
##			elsif($include_flag[$j] eq 'EXCLUDE'){$dinclude_flag[$j] = 'EXCLUDE'}
##			elsif($include_flag[$j] eq ''){$dinclude_flag[$j] = 'EXCLUDE'; $include_flag[$j] = 'E'}

			$include_flag[$j]  = 'E';
			$dinclude_flag[$j] = 'EXCLUDE';
#			if($orig_chip[$j] =~ /N/i && ($chip[$j] =~ /I/i || $chip[$j] =~ /S/i)){
#                        	$spwindow = 'Y';
#                	}
		}
	}elsif($spwindow =~ /N/i){
#
#---- if window filter is set to Null or No, set everything to a Null setting
#
		$aicswin_id[0]      = '';
		$ordr[0]            = '';
                $chip[0]            = 'NULL';
                $dinclude_flag[0]   = 'INCLUDE';
                $include_flag[0]    = 'I';
                $start_row[0]       = '';
                $start_column[0]    = '';
                $height[0]          = '';
                $width[0]           = '';
                $lower_threshold[0] = '';
                $pha_range[0]       = '';
                $sample[0]          = '';
	}

#----------------
#-------- others
#----------------

	$asis       = param("ASIS");
	$clone      = param("CLONE");
	$submitter  = param("USER");
	$dutysci    = param("USER");
	$si_mode    = param("SI_MODE");
	$acistag    = param("ACISTAG");
#	$aciswintag = param("ACISWINTAG");
	$generaltag = param("GENERALTAG");
	$sitag      = param("SITAG");
	$instrument = param("INSTRUMENT");
 
#---------------------------------------------------------------------------------
#------ here are the cases which database values and display values are different.
#---------------------------------------------------------------------------------

	if($multitelescope eq ''){$multitelescope = 'N'}

	if($proposal_joint eq ''){
		$proposal_joint     = 'N/A';
	}
	if($proposal_hst eq ''){
		$proposal_hst       = 'N/A';
	}
	if($proposal_noao eq ''){
		$proposal_noao      = 'N/A';
	}
	if($proposal_xmm eq ''){
		$proposal_xmm       = 'N/A';
	}
	if($rxte_approved_time eq ''){
		$rxte_approved_time = 'N/A';
	}
	if($vla_approved_time eq ''){
		$vla_approved_time  = 'N/A';
	}
	if($vlba_approved_time eq ''){
		$vlba_approved_time = 'N/A';
	}
	
	if($window_flag    eq 'NULL')      {$dwindow_flag = 'NULL'}
	elsif($window_flag eq '')          {$dwindow_flag = 'NULL'; $window_flag = 'NULL';}
	elsif($window_flag eq 'Y')         {$dwindow_flag = 'YES'}
	elsif($window_flag eq 'YES')       {$dwindow_flag = 'YES'}
	elsif($window_flag eq 'N')         {$dwindow_flag = 'NO'}
	elsif($window_flag eq 'NO')        {$dwindow_flag = 'NO'}
	elsif($window_flag eq 'P')         {$dwindow_flag = 'PREFERENCE'}
	elsif($window_flag eq 'PREFERENCE'){$dwindow_flag = 'PREFERENCE'}

	if($roll_flag    eq 'NULL')        {$droll_flag = 'NULL'}
	elsif($roll_flag eq '')            {$droll_flag = 'NULL'; $roll_flag = 'NULL';}
	elsif($roll_flag eq 'Y')           {$droll_flag = 'YES'}
	elsif($roll_flag eq 'YES')         {$droll_flag = 'YES'}
	elsif($roll_flag eq 'N')           {$droll_flag = 'NO'}
	elsif($roll_flag eq 'NO')          {$droll_flag = 'NO'}
	elsif($roll_flag eq 'P')           {$droll_flag = 'PREFERENCE'}
	elsif($roll_flag eq 'PREFERENCE')  {$droll_flag = 'PREFERENCE'}
	
	if($dither_flag    eq 'NULL')      {$ddither_flag = 'NULL'}
	elsif($dither_flag eq '')          {$ddither_flag = 'NULL'; $dither_flag = 'NULL';}
	elsif($dither_flag eq 'Y')         {$ddither_flag = 'YES'}
	elsif($dither_flag eq 'YES')       {$ddither_flag = 'YES'}
	elsif($dither_flag eq 'N')         {$ddither_flag = 'NO'}
	elsif($dither_flag eq 'NO')        {$ddither_flag = 'NO'}
	
	if($uninterrupt    eq 'NULL')      {$duninterrupt = 'NULL'}
	elsif($uninterrupt eq '')          {$duninterrupt = 'NULL'; $uninterrupt = 'NULL';}
	elsif($uninterrupt eq 'N')         {$duninterrupt = 'NO'}
	elsif($uninterrupt eq 'NO')        {$duninterrupt = 'NO'}
	elsif($uninterrupt eq 'Y')         {$duninterrupt = 'YES'}
	elsif($uninterrupt eq 'YES')       {$duninterrupt = 'YES'}
	elsif($uninterrupt eq 'P')         {$duninterrupt = 'PREFERENCE'}
	elsif($uninterrupt eq 'PREFERENCE'){$duninterrupt = 'PREFERENCE'}

	if($photometry_flag    eq 'NULL')  {$dphotometry_flag = 'NULL'}
	elsif($photometry_flag eq 'Y')     {$dphotometry_flag = 'YES'}
	elsif($photometry_flag eq 'YES')   {$dphotometry_flag = 'YES'}
	elsif($photometry_flag eq 'N')     {$dphotometry_flag = 'NO'}
	elsif($photometry_flag eq 'NO')    {$dphotometry_flag = 'NO'}
	
	if($constr_in_remarks    eq 'N')             {$dconstr_in_remarks = 'NO'}
	elsif($constr_in_remarks eq 'NO')            {$dconstr_in_remarks = 'NO'}
	elsif($constr_in_remarks eq 'Y')             {$dconstr_in_remarks = 'YES'}
	elsif($constr_in_remarks eq 'YES')           {$dconstr_in_remarks = 'YES'}
	elsif($constr_in_remarks eq 'P')             {$dconstr_in_remarks = 'PREFERENCE'}
	elsif($constr_in_remarks eq 'PREFERENCE')    {$dconstr_in_remarks = 'PREFERENCE'}

	if($phase_constraint_flag    eq 'NULL')      {$dphase_constraint_flag = 'NULL'}
	elsif($phase_constraint_flag eq 'N')         {$dphase_constraint_flag = 'NONE'}
	elsif($phase_constraint_flag eq 'NO')        {$dphase_constraint_flag = 'NONE'}
	elsif($phase_constraint_flag eq 'Y')         {$dphase_constraint_flag = 'CONSTRAINT'}
	elsif($phase_constraint_flag eq 'CONSTRAINT'){$dphase_constraint_flag = 'CONSTRAINT'}
	elsif($phase_constraint_flag eq 'P')         {$dphase_constraint_flag = 'PREFERENCE'}
	elsif($phase_constraint_flag eq 'PREFERENCE'){$dphase_constraint_flag = 'PREFERENCE'}

        if($monitor_flag    eq 'NULL')               {$dmonitor_flag = 'NULL'; 
							$monitor_flag = 'N'}
        elsif($monitor_flag eq '')                   {$dmonitor_flag = 'NULL'}
        elsif($monitor_flag eq 'Y')                  {$dmonitor_flag = 'YES'}
        elsif($monitor_flag eq 'YES')                {$dmonitor_flag = 'YES'; 
							$monitor_flag = 'Y'}
        elsif($monitor_flag eq 'N')                  {$dmonitor_flag = 'NO'}
        elsif($monitor_flag eq 'NO')                 {$dmonitor_flag = 'NO'; 
							$monitor_flag = 'N'}

#
#---- if phase constraint flag is set for Null, set all phase constraint params to Null
#

	if($phase_constraint_flag =~ /N/i 
		&& $phase_constraint_flag !~ /CONSTRAINT/i 
		&& $phase_constraint_flag !~ /PREFERENCE/i){
		$phase_epoch        = '';
		$phase_period       = '';
		$phase_start        = '';
		$phase_start_margin = '';
		$phase_end          = '';
		$phase_end_margin   = '';
	}

	if($multitelescope    eq 'Y')         {$dmultitelescope = 'YES'}
	elsif($multitelescope eq 'YES')       {$dmultitelescope = 'YES'}
	elsif($multitelescope eq 'N')         {$dmultitelescope = 'NO'}
	elsif($multitelescope eq 'NO')        {$dmultitelescope = 'NO'}
	elsif($multitelescope eq 'P')         {$dmultitelescope = 'PREFERENCE'}
	elsif($multitelescope eq 'PREFERENCE'){$dmultitelescope = 'PREFERENCE'}

#	if($hrc_config eq ''){$hrc_config = 'NULL'}

	if($hrc_zero_block    eq 'NULL')      {$dhrc_zero_block = 'NULL'}
	elsif($hrc_zero_block eq '')          {$dhrc_zero_block = 'NO'; $hrc_zero_block = 'N';}
	elsif($hrc_zero_block eq 'Y')         {$dhrc_zero_block = 'YES'}
	elsif($hrc_zero_block eq 'YES')       {$dhrc_zero_block = 'YES'}
	elsif($hrc_zero_block eq 'N')         {$dhrc_zero_block = 'NO'}
	elsif($hrc_zero_block eq 'NO')        {$dhrc_zero_block = 'NO'}

	if($most_efficient    eq 'NULL')      {$dmost_efficient = 'NULL'}
	elsif($most_efficient eq '')          {$dmost_efficient = 'NULL'}
	elsif($most_efficient eq 'Y')         {$dmost_efficient = 'YES'}
	elsif($most_efficient eq 'YES')       {$dmost_efficient = 'YES'}
	elsif($most_efficient eq 'N')         {$dmost_efficient = 'NO'}
	elsif($most_efficient eq 'NO')        {$dmost_efficient = 'NO'}

	if($ccdi0_on    eq 'NULL')            {$dccdi0_on = 'NULL'}
	elsif($ccdi0_on eq 'Y')               {$dccdi0_on = 'YES'}
	elsif($ccdi0_on eq 'YES')             {$dccdi0_on = 'YES'}
	elsif($ccdi0_on eq 'N')               {$dccdi0_on = 'NO'}
	elsif($ccdi0_on eq 'NO')              {$dccdi0_on = 'NO'}
	elsif($ccdi0_on eq 'OPT1')             {$dccdi0_on = 'OPT1'}
	elsif($ccdi0_on eq 'OPT2')            {$dccdi0_on = 'OPT2'}
	elsif($ccdi0_on eq 'OPT3')            {$dccdi0_on = 'OPT3'}
	elsif($ccdi0_on eq 'OPT4')            {$dccdi0_on = 'OPT4'}
	elsif($ccdi0_on eq 'OPT5')            {$dccdi0_on = 'OPT5'}
	if($ccdi0_on eq 'OPT1')               {$ccdi0_on  = 'O1'}
	elsif($ccdi0_on eq 'OPT2')            {$ccdi0_on  = 'O2'}
	elsif($ccdi0_on eq 'OPT3')            {$ccdi0_on  = 'O3'}
	elsif($ccdi0_on eq 'OPT4')            {$ccdi0_on  = 'O4'}
	elsif($ccdi0_on eq 'OPT5')            {$ccdi0_on  = 'O5'}
	
	
	if($ccdi1_on    eq 'NULL')            {$dccdi1_on = 'NULL'}
	elsif($ccdi1_on eq 'Y')               {$dccdi1_on = 'YES'}
	elsif($ccdi1_on eq 'YES')             {$dccdi1_on = 'YES'}
	elsif($ccdi1_on eq 'N')               {$dccdi1_on = 'NO'}
	elsif($ccdi1_on eq 'NO')              {$dccdi1_on = 'NO'}
	elsif($ccdi1_on eq 'OPT1')            {$dccdi1_on = 'OPT1'}
	elsif($ccdi1_on eq 'OPT2')            {$dccdi1_on = 'OPT2'}
	elsif($ccdi1_on eq 'OPT3')            {$dccdi1_on = 'OPT3'}
	elsif($ccdi1_on eq 'OPT4')            {$dccdi1_on = 'OPT4'}
	elsif($ccdi1_on eq 'OPT5')            {$dccdi1_on = 'OPT5'}
	if($ccdi1_on eq 'OPT1')               {$ccdi1_on  = 'O1'}
	elsif($ccdi1_on eq 'OPT2')            {$ccdi1_on  = 'O2'}
	elsif($ccdi1_on eq 'OPT3')            {$ccdi1_on  = 'O3'}
	elsif($ccdi1_on eq 'OPT4')            {$ccdi1_on  = 'O4'}
	elsif($ccdi1_on eq 'OPT5')            {$ccdi1_on  = 'O5'}
	
	if($ccdi2_on    eq 'NULL')            {$dccdi2_on = 'NULL'}
	elsif($ccdi2_on eq 'Y')               {$dccdi2_on = 'YES'}
	elsif($ccdi2_on eq 'YES')             {$dccdi2_on = 'YES'}
	elsif($ccdi2_on eq 'N')               {$dccdi2_on = 'NO'}
	elsif($ccdi2_on eq 'NO')              {$dccdi2_on = 'NO'}
	elsif($ccdi2_on eq 'OPT1')            {$dccdi2_on = 'OPT1'}
	elsif($ccdi2_on eq 'OPT2')            {$dccdi2_on = 'OPT2'}
	elsif($ccdi2_on eq 'OPT3')            {$dccdi2_on = 'OPT3'}
	elsif($ccdi2_on eq 'OPT4')            {$dccdi2_on = 'OPT4'}
	elsif($ccdi2_on eq 'OPT5')            {$dccdi2_on = 'OPT5'}
	if($ccdi2_on eq 'OPT1')               {$ccdi2_on  = 'O1'}
	elsif($ccdi2_on eq 'OPT2')            {$ccdi2_on  = 'O2'}
	elsif($ccdi2_on eq 'OPT3')            {$ccdi2_on  = 'O3'}
	elsif($ccdi2_on eq 'OPT4')            {$ccdi2_on  = 'O4'}
	elsif($ccdi2_on eq 'OPT5')            {$ccdi2_on  = 'O5'}
	
	if($ccdi3_on    eq 'NULL')            {$dccdi3_on = 'NULL'}
	elsif($ccdi3_on eq 'Y')               {$dccdi3_on = 'YES'}
	elsif($ccdi3_on eq 'YES')             {$dccdi3_on = 'YES'}
	elsif($ccdi3_on eq 'N')               {$dccdi3_on = 'NO'}
	elsif($ccdi3_on eq 'NO')              {$dccdi3_on = 'NO'}
	elsif($ccdi3_on eq 'OPT1')            {$dccdi3_on = 'OPT1'}
	elsif($ccdi3_on eq 'OPT2')            {$dccdi3_on = 'OPT2'}
	elsif($ccdi3_on eq 'OPT3')            {$dccdi3_on = 'OPT3'}
	elsif($ccdi3_on eq 'OPT4')            {$dccdi3_on = 'OPT4'}
	elsif($ccdi3_on eq 'OPT5')            {$dccdi3_on = 'OPT5'}
	if($ccdi3_on eq 'OPT1')               {$ccdi3_on  = 'O1'}
	elsif($ccdi3_on eq 'OPT2')            {$ccdi3_on  = 'O2'}
	elsif($ccdi3_on eq 'OPT3')            {$ccdi3_on  = 'O3'}
	elsif($ccdi3_on eq 'OPT4')            {$ccdi3_on  = 'O4'}
	elsif($ccdi3_on eq 'OPT5')            {$ccdi3_on  = 'O5'}
	
	if($ccds0_on    eq 'NULL')            {$dccds0_on = 'NULL'}
	elsif($ccds0_on eq 'Y')               {$dccds0_on = 'YES'}
	elsif($ccds0_on eq 'YES')             {$dccds0_on = 'YES'}
	elsif($ccds0_on eq 'N')               {$dccds0_on = 'NO'}
	elsif($ccds0_on eq 'NO')              {$dccds0_on = 'NO'}
	elsif($ccds0_on eq 'OPT1')            {$dccds0_on = 'OPT1'}
	elsif($ccds0_on eq 'OPT2')            {$dccds0_on = 'OPT2'}
	elsif($ccds0_on eq 'OPT3')            {$dccds0_on = 'OPT3'}
	elsif($ccds0_on eq 'OPT4')            {$dccds0_on = 'OPT4'}
	elsif($ccds0_on eq 'OPT5')            {$dccds0_on = 'OPT5'}
	if($ccds0_on eq 'OPT1')               {$ccds0_on  = 'O1'}
	elsif($ccds0_on eq 'OPT2')            {$ccds0_on  = 'O2'}
	elsif($ccds0_on eq 'OPT3')            {$ccds0_on  = 'O3'}
	elsif($ccds0_on eq 'OPT4')            {$ccds0_on  = 'O4'}
	elsif($ccds0_on eq 'OPT5')            {$ccds0_on  = 'O5'}
	
	if($ccds1_on    eq 'NULL')            {$dccds1_on = 'NULL'}
	elsif($ccds1_on eq 'Y')               {$dccds1_on = 'YES'}
	elsif($ccds1_on eq 'YES')             {$dccds1_on = 'YES'}
	elsif($ccds1_on eq 'N')               {$dccds1_on = 'NO'}
	elsif($ccds1_on eq 'NO')              {$dccds1_on = 'NO'}
	elsif($ccds1_on eq 'OPT1')            {$dccds1_on = 'OPT1'}
	elsif($ccds1_on eq 'OPT2')            {$dccds1_on = 'OPT2'}
	elsif($ccds1_on eq 'OPT3')            {$dccds1_on = 'OPT3'}
	elsif($ccds1_on eq 'OPT4')            {$dccds1_on = 'OPT4'}
	elsif($ccds1_on eq 'OPT5')            {$dccds1_on = 'OPT5'}
	if($ccds1_on eq 'OPT1')               {$ccds1_on  = 'O1'}
	elsif($ccds1_on eq 'OPT2')            {$ccds1_on  = 'O2'}
	elsif($ccds1_on eq 'OPT3')            {$ccds1_on  = 'O3'}
	elsif($ccds1_on eq 'OPT4')            {$ccds1_on  = 'O4'}
	elsif($ccds1_on eq 'OPT5')            {$ccds1_on  = 'O5'}
	
	if($ccds2_on    eq 'NULL')            {$dccds2_on = 'NULL'}
	elsif($ccds2_on eq 'Y')               {$dccds2_on = 'YES'}
	elsif($ccds2_on eq 'YES')             {$dccds2_on = 'YES'}
	elsif($ccds2_on eq 'N')               {$dccds2_on = 'NO'}
	elsif($ccds2_on eq 'NO')              {$dccds2_on = 'NO'}
	elsif($ccds2_on eq 'OPT1')            {$dccds2_on = 'OPT1'}
	elsif($ccds2_on eq 'OPT2')            {$dccds2_on = 'OPT2'}
	elsif($ccds2_on eq 'OPT3')            {$dccds2_on = 'OPT3'}
	elsif($ccds2_on eq 'OPT4')            {$dccds2_on = 'OPT4'}
	elsif($ccds2_on eq 'OPT5')            {$dccds2_on = 'OPT5'}
	if($ccds2_on eq 'OPT1')               {$ccds2_on  = 'O1'}
	elsif($ccds2_on eq 'OPT2')            {$ccds2_on  = 'O2'}
	elsif($ccds2_on eq 'OPT3')            {$ccds2_on  = 'O3'}
	elsif($ccds2_on eq 'OPT4')            {$ccds2_on  = 'O4'}
	elsif($ccds2_on eq 'OPT5')            {$ccds2_on  = 'O5'}
	
	if($ccds3_on    eq 'NULL')            {$dccds3_on = 'NULL'}
	elsif($ccds3_on eq 'Y')               {$dccds3_on = 'YES'}
	elsif($ccds3_on eq 'YES')             {$dccds3_on = 'YES'}
	elsif($ccds3_on eq 'N')               {$dccds3_on = 'NO'}
	elsif($ccds3_on eq 'NO')              {$dccds3_on = 'NO'}
	elsif($ccds3_on eq 'OPT1')            {$dccds3_on = 'OPT1'}
	elsif($ccds3_on eq 'OPT2')            {$dccds3_on = 'OPT2'}
	elsif($ccds3_on eq 'OPT3')            {$dccds3_on = 'OPT3'}
	elsif($ccds3_on eq 'OPT4')            {$dccds3_on = 'OPT4'}
	elsif($ccds3_on eq 'OPT5')            {$dccds3_on = 'OPT5'}
	if($ccds3_on eq 'OPT1')               {$ccds3_on  = 'O1'}
	elsif($ccds3_on eq 'OPT2')            {$ccds3_on  = 'O2'}
	elsif($ccds3_on eq 'OPT3')            {$ccds3_on  = 'O3'}
	elsif($ccds3_on eq 'OPT4')            {$ccds3_on  = 'O4'}
	elsif($ccds3_on eq 'OPT5')            {$ccds3_on  = 'O5'}

	if($ccds4_on    eq 'NULL')            {$dccds4_on = 'NULL'}
	elsif($ccds4_on eq 'Y')               {$dccds4_on = 'YES'}
	elsif($ccds4_on eq 'YES')             {$dccds4_on = 'YES'}
	elsif($ccds4_on eq 'N')               {$dccds4_on = 'NO'}
	elsif($ccds4_on eq 'NO')              {$dccds4_on = 'NO'}
	elsif($ccds4_on eq 'OPT1')            {$dccds4_on = 'OPT1'}
	elsif($ccds4_on eq 'OPT2')            {$dccds4_on = 'OPT2'}
	elsif($ccds4_on eq 'OPT3')            {$dccds4_on = 'OPT3'}
	elsif($ccds4_on eq 'OPT4')            {$dccds4_on = 'OPT4'}
	elsif($ccds4_on eq 'OPT5')            {$dccds4_on = 'OPT5'}
	if($ccds4_on eq 'OPT1')               {$ccds4_on  = 'O1'}
	elsif($ccds4_on eq 'OPT2')            {$ccds4_on  = 'O2'}
	elsif($ccds4_on eq 'OPT3')            {$ccds4_on  = 'O3'}
	elsif($ccds4_on eq 'OPT4')            {$ccds4_on  = 'O4'}
	elsif($ccds4_on eq 'OPT5')            {$ccds4_on  = 'O5'}
	
	if($ccds5_on    eq 'NULL')            {$dccds5_on = 'NULL'}
	elsif($ccds5_on eq 'Y')               {$dccds5_on = 'YES'}
	elsif($ccds5_on eq 'YES')             {$dccds5_on = 'YES'}
	elsif($ccds5_on eq 'N')               {$dccds5_on = 'NO'}
	elsif($ccds5_on eq 'NO')              {$dccds5_on = 'NO'}
	elsif($ccds5_on eq 'OPT1')            {$dccds5_on = 'OPT1'}
	elsif($ccds5_on eq 'OPT2')            {$dccds5_on = 'OPT2'}
	elsif($ccds5_on eq 'OPT3')            {$dccds5_on = 'OPT3'}
	elsif($ccds5_on eq 'OPT4')            {$dccds5_on = 'OPT4'}
	elsif($ccds5_on eq 'OPT5')            {$dccds5_on = 'OPT5'}
	if($ccds5_on eq 'OPT1')               {$ccds5_on  = 'O1'}
	elsif($ccds5_on eq 'OPT2')            {$ccds5_on  = 'O2'}
	elsif($ccds5_on eq 'OPT3')            {$ccds5_on  = 'O3'}
	elsif($ccds5_on eq 'OPT4')            {$ccds5_on  = 'O4'}
	elsif($ccds5_on eq 'OPT5')            {$ccds5_on  = 'O5'}
	
	$count_ccd_on = 0;
	if($ccdi0_on =~ /Y/i){$count_ccd_on++} 
	if($ccdi1_on =~ /Y/i){$count_ccd_on++} 
	if($ccdi2_on =~ /Y/i){$count_ccd_on++} 
	if($ccdi3_on =~ /Y/i){$count_ccd_on++} 
	if($ccds0_on =~ /Y/i){$count_ccd_on++} 
	if($ccds1_on =~ /Y/i){$count_ccd_on++} 
	if($ccds2_on =~ /Y/i){$count_ccd_on++} 
	if($ccds3_on =~ /Y/i){$count_ccd_on++} 
	if($ccds4_on =~ /Y/i){$count_ccd_on++} 
	if($ccds5_on =~ /Y/i){$count_ccd_on++} 

	if($ccdi0_on =~ /0/i){$count_ccd_on++} 
	if($ccdi1_on =~ /0/i){$count_ccd_on++} 
	if($ccdi2_on =~ /0/i){$count_ccd_on++} 
	if($ccdi3_on =~ /0/i){$count_ccd_on++} 
	if($ccds0_on =~ /0/i){$count_ccd_on++} 
	if($ccds1_on =~ /0/i){$count_ccd_on++} 
	if($ccds2_on =~ /0/i){$count_ccd_on++} 
	if($ccds3_on =~ /0/i){$count_ccd_on++} 
	if($ccds4_on =~ /0/i){$count_ccd_on++} 
	if($ccds5_on =~ /0/i){$count_ccd_on++} 
	
	if($duty_cycle    eq 'NULL')	{$dduty_cycle = 'NULL'}
	elsif($duty_cycle eq 'Y')	{$dduty_cycle = 'YES'}
	elsif($duty_cycle eq 'YES')	{$dduty_cycle = 'YES'}
	elsif($duty_cycle eq 'N')	{$dduty_cycle = 'NO'}
	elsif($duty_cycle eq 'NO')	{$dduty_cycle = 'NO'}

	if($onchip_sum    eq 'NULL')	{$donchip_sum = 'NULL'}
	elsif($onchip_sum eq 'Y')	{$donchip_sum = 'YES'}
	elsif($onchip_sum eq 'YES')	{$donchip_sum = 'YES'}
	elsif($onchip_sum eq 'N')	{$donchip_sum = 'NO'}
	elsif($onchip_sum eq 'NO')	{$donchip_sum = 'NO'}

	if($eventfilter    eq 'NULL')	{$deventfilter = 'NULL'}
	elsif($eventfilter eq 'Y')	{$deventfilter = 'YES'}
	elsif($eventfilter eq 'YES')	{$deventfilter = 'YES'}
	elsif($eventfilter eq 'N')	{$deventfilter = 'NO'}
	elsif($eventfilter eq 'NO')	{$deventfilter = 'NO'}

#
#--- added 03/29/11
#
	if($multiple_spectral_lines    eq 'NULL')	{$dmultiple_spectral_lines = 'NULL'}
	elsif($multiple_spectral_lines eq 'Y')		{$dmultiple_spectral_lines = 'YES'}
	elsif($multiple_spectral_lines eq 'YES')	{$dmultiple_spectral_lines = 'YES'}
	elsif($multiple_spectral_lines eq 'N')		{$dmultiple_spectral_lines = 'NO'}
	elsif($multiple_spectral_lines eq 'NO')		{$dmultiple_spectral_lines = 'NO'}

	if($spwindow    eq 'NULL')	{$dspwindow = 'NULL'}
	elsif($spwindow eq 'Y')		{$dspwindow = 'YES'}
	elsif($spwindow eq 'YES')	{$dspwindow = 'YES'}
	elsif($spwindow eq 'N')		{$dspwindow = 'NO'}
	elsif($spwindow eq 'NO')	{$dspwindow = 'NO'}

	if($subarray eq 'N')         {$dsubarray = 'NO';
				      $subarray  = 'NONE'}
	elsif($subarray eq 'NO')     {$dsubarray = 'NO';
			              $subarray  = 'NONE'}
	elsif($subarray eq 'NONE')   {$dsubarray = 'NO'}
	elsif($subarray eq 'Y')      {$dsubarray = 'YES'}
	elsif($subarray eq 'YES')    {$dsubarray = 'YES';
				      $subarray  = 'CUSTOM'}
	elsif($subarray eq 'CUSTOM') {$dsubarray = 'YES'}

#
#---- added 08/01/11
#
	if($extended_src  eq 'NO')    {$dextended_src = 'NO'}
	elsif($extended_src eq 'N')   {$dextended_src = 'NO'}
	elsif($extended_src eq 'YES') {$dextended_src = 'YES'}
	elsif($extended_src eq 'Y')   {$dextended_src = 'YES'}

	if($hrc_timing_mode eq 'N'){
			$dhrc_timing_mode = 'NO'
	}elsif($hrc_timing_mode eq 'Y'){
			$dhrc_timing_mode = 'YES'
	}

	if($ra =~ /;/){					# if someone mis-typed ":" for ";"
		if($ra =~ /:/){
			$ra =~ s/;/:/g;
		}else{
			$ra =~ s/;/ /g;
		}
	}
	if($ra =~ /:/){					# if ra is in HH:MM:SS form, change it into dra
		$ra =~s/\s+//g;
		@rtemp = split(/:/,$ra);
		$ra    = 15.0*($rtemp[0] + $rtemp[1]/60 + $rtemp[2]/3600);
		$ra    = sprintf "%3.6f",$ra;
	}else{
		@rtemp = split(/\s+/, $ra);		#if ra is in HH MM SS form, change it into dra
		if($rtemp[0] eq ''){
			$rtemp[0] = $rtemp[1];
			$rtemp[1] = $rtemp[2];
			$rtemp[2] = $rtemp[3];
		}

		if($rtemp[0] =~ /\d/ && $rtemp[1] =~ /\d/ && $rtemp[2] =~ /\d/){
			$ra = 15.0*($rtemp[0] + $rtemp[1]/60 + $rtemp[2]/3600);
			$ra = sprintf "%3.6f",$ra;
		}
	}

	if($dec =~ /;/){				# if someone mis-typed ";" for ":"
		if($dec =~ /:/){
			$dec =~ s/;/:/g;
		}else{
			$dec =~ s/;/ /g;
		}
	}
	if($dec =~ /:/){				# if dec is in DDD:MM:SS form, change it into ddec
		$dec =~ s/\s+//g;
		@dtemp = split(/:/, $dec);
		$zzz   = abs ($dtemp[2]);
		if($zzz =~ /\d/){
			$sign  = 1;
			@etemp = split(//, $dec);
			if($etemp[0] eq '-'){
				$sign = -1;
			}
			$dec = $sign * (abs($dtemp[0]) + $dtemp[1]/60 + $dtemp[2]/3600);
			$dec = sprintf "%3.6f",$dec;
		}
	}else{
		@dtemp = split(/\s+/, $dec);		# if dec is in DDD MM SS form, change it into ddec
		if($dtemp[0] eq ''){
			if($dtemp[1] eq '-' || $dtemp[1] eq '+'){
				$dtemp[0] = "$dtemp[1]$dtemp[2]";
				$dtemp[1] = $dtemp[3];
				$dtemp[2] = $dtemp[4];
			}else{
				$dtemp[0] = $dtemp[1];
				$dtemp[1] = $dtemp[2];
				$dtemp[2] = $dtemp[3];
			}
		}elsif($dtemp[0] eq '-' || $detemp[0] eq '+'){
				$dtemp[0] = "$dtemp[0]$dtemp[1]";
				$dtemp[1] = $dtemp[2];
				$dtemp[2] = $dtemp[3];
		}
			

		if($dtemp[0] =~ /\d/ && $dtemp[1] =~ /\d/ && $dtemp[2] =~ /\d/){
			$zzz = abs ($dtemp[2]);
			if($zzz =~ /\d/){
				$sign  = 1;
#				@etemp = split(//, $dec);
#				if($etemp[0] eq '-'){
				if($dtemp[0] < 0){
					$sign = -1;
				}
				$dec = $sign * (abs($dtemp[0]) + $dtemp[1]/60 + $dtemp[2]/3600);
				$dec = sprintf "%3.6f",$dec;
			}
		}
	}
	$dra  = $ra;
	if($ddec == 0 && $ddec =~ /-/){
		$ddec = 0.000000;
	}
	$ddec = $dec;
#
#----- check whether ACIS Window Constraints Lowest Energy exceeds 0.5 keV limit.
#

	for($j = 0; $j < $aciswin_no; $j++){
		if($chip[$j] =~ /N/i){
			$lower_threshold[$j] = '';
			$pha_range[$j]       = '';
			$sample[$j]          = '';
		}elsif($lower_threshold[$j] > 0.5){
			$awc_l_th = 1;
		}
	}

#
#----- dether params
#
	if($y_amp =~ /\d/ || $y_amp_asec =~ /\d/){
        	$y_amp   = $y_amp_asec/3600;
	}
	if($z_amp =~ /\d/ || $z_amp_asec =~ /\d/){
        	$z_amp   = $z_amp_asec/3600;
	}

	if($y_freq =~ /\d/ || $y_freq_asec =~ /\d/){
        	$y_freq   = $y_freq_asec/3600;
	}
	if($z_freq =~ /\d/ || $z_freq_asec =~ /\d/){
        	$z_freq   = $z_freq_asec/3600;
	}
}


################################################################################
### sub read_databases: read out values from databases                       ###
################################################################################

sub read_databases{

#------------------------------------------------
#-------  database username, password, and server
#------------------------------------------------

	$db_user = "browser";
	$server  = "ocatsqlsrv";

#	$db_user="browser";
#	$server="sqlbeta";

#	$db_user = "browser";
#	$server  = "sqlxtest";


	$db_passwd =`cat $pass_dir/.targpass`;
	chop $db_passwd;

#--------------------------------------
#-------- open connection to sql server
#--------------------------------------

	my $db = "server=$server;database=axafocat";
	$dsn1  = "DBI:Sybase:$db";
	$dbh1  = DBI->connect($dsn1, $db_user, $db_passwd, { PrintError => 0, RaiseError => 1});

#-------------------------------------------
#-----------  get remarks from target table
#-------------------------------------------

	$sqlh1 = $dbh1->prepare(qq(select remarks  from target where obsid=$obsid));
	$sqlh1->execute();
	($remarks) = $sqlh1->fetchrow_array;
	$sqlh1->finish;

#-------------------------------------------
#--------  get preferences from target table
#-------------------------------------------

#	$sqlh1 = $dbh1->prepare(qq(select preferences  from target where obsid=$obsid));
#	$sqlh1->execute();
#	($preferences) = $sqlh1->fetchrow_array;
#	$sqlh1->finish;

#---------------------------------------------
#----------  get mp remarks from target table
#---------------------------------------------

	$sqlh1 = $dbh1->prepare(qq(select mp_remarks  from target where obsid=$obsid));
	$sqlh1->execute();
  	($mp_remarks) = $sqlh1->fetchrow_array;
	$sqlh1->finish;

#----------------------------------
#--------  get preference comments
#----------------------------------

#	$sqlh1 = $dbh1->prepare(qq(select mp_remarks from target where obsid=$obsid));
#	$sqlh1->execute();
#      	($mp_remarks) = $sqlh1->fetchrow_array;
#	$sqlh1->finish; 

#---------------------------------
#---------  get roll_pref comments
#---------------------------------

#	$sqlh1 = $dbh1->prepare(qq(select roll_pref  from target where obsid=$obsid));
#	$sqlh1->execute();
#        ($roll_pref) = $sqlh1->fetchrow_array;
#	$sqlh1->finish;

#--------------------------------
#--------  get date_pref comments
#--------------------------------

#	$sqlh1 = $dbh1->prepare(qq(select date_pref from target where obsid=$obsid));
#	$sqlh1->execute();
#       ($date_pref) = $sqlh1->fetchrow_array;
#	$sqlh1->finish; 

#----------------------------------
#---------  get coord_pref comments
#----------------------------------

#	$sqlh1 = $dbh1->prepare(qq(select coord_pref  from target where obsid=$obsid));
#	$sqlh1->execute();
#        ($coord_pref) = $sqlh1->fetchrow_array;
#	$sqlh1->finish; 

#---------------------------------
#---------  get cont_pref comments
#---------------------------------

#	$sqlh1 = $dbh1->prepare(qq(select cont_pref from target where obsid=$obsid));
#	$sqlh1->execute();
#       ($cont_pref) = $sqlh1->fetchrow_array;
#	$sqlh1->finish;

#------------------------------------------
#-------- combine all remarks to one remark 
#------------------------------------------

#	$remark_cont = '';
#	if($roll_pref =~ /\w/){
#        	unless($roll_pref =~ /N\/A/){
#                	$remark_cont ="$remark_cont".'<I><B>Roll preferences:</B></I><BR>'."$roll_pref".'<BR>';
#        	}
#	}
#	if($date_pref =~ /\w/){
#        	unless($data_pref =~ /N\/A/){
#                	$remark_cont ="$remark_cont".'<I><B>Date preferences:</B></I><BR>'."$date_pref".'<BR>';
#        	}
#	}
#	if($coord_pref =~ /\w/){
#        	unless($coord_pref =~ /N\/A/){
#                	$remark_cont ="$remark_cont".'<I><B>Coord preferences:</B></I><BR>'."$coord_pref".'<BR>';
#        	}
#	}
#	if($cont_pref =~ /\w/){
#        	unless($cont_pref =~ /N\/A/){
#                	$remark_cont ="$remark_cont".'<I><B>Cont preferences:</B></I><BR>'."$cont_pref".'<BR>';
#        	}
#	}
#	if($preferences =~ /\w/){
#        	unless($preferences =~ /N\/A/){
#                	$remark_cont ="$remark_cont".'<I><B>Preferences:</B></I><BR>'."$preferences".'<BR>';
#        	}
#	}

#------------------------------------------------------
#---------------  get stuff from target table, clean up
#------------------------------------------------------

	$sqlh1 = $dbh1->prepare(qq(select 
		obsid,targid,seq_nbr,targname,obj_flag,object,si_mode,photometry_flag, 
		vmagnitude,ra,dec,est_cnt_rate,forder_cnt_rate,y_det_offset,z_det_offset, 
		raster_scan,dither_flag,approved_exposure_time,pre_min_lead,pre_max_lead, 
		pre_id,seg_max_num,aca_mode,phase_constraint_flag,ocat_propid,acisid, 
		hrcid,grating,instrument,rem_exp_time,soe_st_sched_date,type,lts_lt_plan, 
		mpcat_star_fidlight_file,status,data_rights,tooid,description,
		total_fld_cnt_rate, extended_src,uninterrupt, multitelescope,observatories,
		tooid, constr_in_remarks, group_id, obs_ao_str, roll_flag, window_flag, spwindow_flag,
                multitelescope_interval
	from target where obsid=$obsid));
	$sqlh1->execute();
    	@targetdata = $sqlh1->fetchrow_array;
	$sqlh1->finish;

#--------------------------------------------------------------------------
#------- fill values from target table
#------- doing this the long way so I can see what I'm doing and make sure
#------- everything is accounted for
#--------------------------------------------------------------------------

	$targid		 		= $targetdata[1];
	$seq_nbr		 	= $targetdata[2];
	$targname		 	= $targetdata[3];
	$obj_flag		 	= $targetdata[4];
	$object		 		= $targetdata[5];
	$si_mode		 	= $targetdata[6];
	$photometry_flag		= $targetdata[7];
	$vmagnitude		 	= $targetdata[8];
	$ra		 		= $targetdata[9];
	$dec		 		= $targetdata[10];
	$est_cnt_rate		 	= $targetdata[11];
	$forder_cnt_rate		= $targetdata[12];
	$y_det_offset		 	= $targetdata[13];
	$z_det_offset		 	= $targetdata[14];
	$raster_scan		 	= $targetdata[15];
	$dither_flag		 	= $targetdata[16];
	$approved_exposure_time		= $targetdata[17];
	$pre_min_lead		 	= $targetdata[18];
	$pre_max_lead 			= $targetdata[19];
	$pre_id				= $targetdata[20];
	$seg_max_num		 	= $targetdata[21];
	$aca_mode		 	= $targetdata[22];
	$phase_constraint_flag 		= $targetdata[23];
	$proposal_id		 	= $targetdata[24];
	$acisid				= $targetdata[25];
	$hrcid		 		= $targetdata[26];
	$grating		 	= $targetdata[27];
	$instrument		 	= $targetdata[28];
	$rem_exp_time		 	= $targetdata[29];
	$soe_st_sched_date		= $targetdata[30];
	$type				= $targetdata[31];
	$lts_lt_plan		 	= $targetdata[32];
	$mpcat_star_fidlight_file	= $targetdata[33];
	$status		 		= $targetdata[34];
	$data_rights		 	= $targetdata[35];
	$tooid 		 		= $targetdata[36];
	$description 		 	= $targetdata[37];
	$total_fld_cnt_rate		= $targetdata[38];
	$extended_src 		 	= $targetdata[39];
	$uninterrupt 			= $targetdata[40];
	$multitelescope 		= $targetdata[41];
	$observatories 			= $targetdata[42];
	$tooid 				= $targetdata[43];
	$constr_in_remarks		= $targetdata[44];
	$group_id 			= $targetdata[45];
	$obs_ao_str 			= $targetdata[46];
	$roll_flag		 	= $targetdata[47];
	$window_flag 			= $targetdata[48];
	$spwindow			= $targetdata[49];
	$multitelescope_interval	= $targetdata[50];


#------------------------------------------------
#---- check group_id and find out related obsids
#------------------------------------------------

	$group_id     =~ s/\s+//g;
	$pre_id       =~ s/\s+//g;
	$pre_min_lead =~ s/\s+//g;
	$pre_max_lead =~ s/\s+//g;

	$monitor_flag = "N";
	if ($pre_id){
    		$monitor_flag = "Y";
	}

	$sqlh1 = $dbh1->prepare(qq(select distinct pre_id from target where pre_id=$obsid));	
	$sqlh1->execute();
	$pre_id_match = $sqlh1->fetchrow_array;
	$sqlh1->finish;
	if($pre_id_match){
		$monitor_flag = "Y";
	}

	if ($group_id){
   		$monitor_flag = "N";
###   		undef $pre_min_lead;
###    		undef $pre_max_lead;
###  		undef $pre_id;
	
		$sqlh1 = $dbh1->prepare(qq(select
        		obsid
		from target where group_id = \'$group_id\'));
		$sqlh1->execute();

		while(@group_obsid = $sqlh1->fetchrow_array){
        		$group_obsid = join("<td>", @group_obsid);
			if($usint_on =~ /test/){
        			@group       = (@group, "<a href=\"$test_http\/ocatdata2html.cgi\?$group_obsid\">$group_obsid<\/a> ");
			}else{
        			@group       = (@group, "<a href=\"$usint_http\/ocatdata2html.cgi\?$group_obsid\">$group_obsid<\/a> ");
			}
		}

#------  output formatting

   		$group_count = 0;
   		foreach (@group){
       			$group_count ++;
       			if(($group_count % 10) == 0){
	           		@group[$group_count - 1] = "@group[$group_count - 1]<br>";
       			}
   		}
		$group_cnt    = $group_count;
   		$group_count .= " obsids for ";
	}else{
		if($monitor_flag !~ /Y/i){
   			undef $pre_min_lead;
    			undef $pre_max_lead;
  			undef $pre_id;
		}
	}


#------------------------------------------------------------------
#---- if monitoring flag is Y, find which ones are monitoring data
#------------------------------------------------------------------

        if($monitor_flag =~ /Y/i){
                &series_rev($obsid);
                &series_fwd($obsid);
                %seen = ();
                @uniq = ();
                foreach $monitor_elem (@monitor_series) {
                        push(@uniq, $monitor_elem) unless $seen{$monitor_elem}++;
                }
                @monitor_series = sort @uniq;
        }

#-------------------------------------------------
#---- updating AO number for the observation
#---- ao value is different from org and current
#-------------------------------------------------

	$proposal_id =~ s/\s+//g;
        $sqlh1 = $dbh1->prepare(qq(select
                ao_str
        from prop_info where ocat_propid=$proposal_id ));

        $sqlh1->execute();
        @updatedata   = $sqlh1->fetchrow_array;
        $sqlh1->finish;
        $obs_ao_str = $updatedata[0];
        $obs_ao_str =~ s/\s+//g;

#-----------------------------------------------------------------------
#------- roll requirement database
#------- first, get roll_ordr to see how many orders are in the database
#-----------------------------------------------------------------------

	$roll_ordr = '';
	OUTER:
	for($incl= 1; $incl < 30; $incl++){
		$sqlh1 = $dbh1->prepare(qq(select ordr from rollreq where ordr=$incl and obsid=$obsid));
		$sqlh1->execute();
    		@rollreq_data = $sqlh1->fetchrow_array;
		$sqlh1->finish;
		if($rollreq_data[0] eq ''){
			next OUTER;
		}
		$roll_ordr = $rollreq_data[0];
		$roll_ordr =~ s/\s+//g;
	}
	if($roll_ordr =~ /\D/ || $roll_ordr eq ''){
		$roll_ordr = 1;
	}

#-----------------------------------------------------------------
#-------- get the rest of the roll requirement data for each order
#-----------------------------------------------------------------

	for($tordr = 1; $tordr <= $roll_ordr; $tordr++){

		$sqlh1 = $dbh1->prepare(qq(select 
			roll_constraint,roll_180,roll,roll_tolerance 
		from rollreq where ordr = $tordr and obsid=$obsid));
		$sqlh1->execute();
		@rollreq_data = $sqlh1->fetchrow_array;
		$sqlh1->finish;

		$roll_constraint[$tordr] = $rollreq_data[0];
		$roll_180[$tordr]        = $rollreq_data[1];
		$roll[$tordr]            = $rollreq_data[2];
		$roll_tolerance[$tordr]  = $rollreq_data[3];
	}

#-----------------------------------------------------------------------
#------ time requirement database
#------ first, get time_ordr to see how many orders are in the database
#-----------------------------------------------------------------------

	@window_constraint = ();
	@tstart = ();
	@tstop  = ();
	OUTER:
	for($incl= 1; $incl < 30; $incl++){
		$sqlh1 = $dbh1->prepare(qq(select ordr from timereq where ordr=$incl and obsid=$obsid));
		$sqlh1->execute();
		@timereq_data = $sqlh1->fetchrow_array;
		$sqlh1->finish;
		if($timereq_data[0] eq ''){
			next OUTER;
		}
		$time_ordr = $timereq_data[0];				# here is time order
		$time_ordr =~ s/\s+//g;
	}
	if($time_ordr =~ /\D/ || $time_ordr eq ''){
		$time_ordr = 1;
	}

#--------------------------------------------------------------
#----- get the rest of the time requirement data for each order
#--------------------------------------------------------------

	for($tordr = 1; $tordr <= $time_ordr; $tordr++){
		$sqlh1 = $dbh1->prepare(qq(select 
			window_constraint, tstart, tstop  
		from timereq where ordr = $tordr and obsid=$obsid));
		$sqlh1->execute();
		@timereq_data = $sqlh1->fetchrow_array;
		$sqlh1->finish;

		$window_constraint[$tordr] = $timereq_data[0];
		$tstart[$tordr]            = $timereq_data[1];
		$tstop[$tordr]             = $timereq_data[2];
	}

#-----------------------------------------------------------------
#---------- if it's a TOO, get remarks and trigger from TOO table
#-----------------------------------------------------------------

	if ($tooid) {
		$sqlh1 = $dbh1->prepare(qq(select 
			type,trig,start,stop,followup,remarks,tooid 
		from too where tooid=$tooid));
		$sqlh1->execute();
		@toodata = $sqlh1->fetchrow_array;
		$sqlh1->finish;

    		$too_type     = $toodata[0];
    		$too_trig     = $toodata[1];
    		$too_start    = $toodata[2];
    		$too_stop     = $toodata[3];
    		$too_followup = $toodata[4];
    		$too_remarks  = $toodata[5];
    		$too_id       = $toodata[6];
	} else {
    		$too_type     = "NULL";
    		$too_trig     = "NULL";
    		$too_start    = "NULL";
    		$too_stop     = "NULL";
    		$too_followup = "NULL";
    		$too_remarks  = "";
    		$too_id       = "NULL";
	}

#------------------------------------------------------------------------
#------------  if it's an hrc observation, get values from hrcparam table
#------------------------------------------------------------------------

#			hrc_config,hrc_chop_duty_cycle,hrc_chop_fraction, 
#			hrc_chop_duty_no,hrc_zero_block,timing_mode,si_mode 
	if ($hrcid){
		$sqlh1 = $dbh1->prepare(qq(select 
			hrc_zero_block,timing_mode,si_mode 
		from hrcparam where hrcid=$hrcid));
		$sqlh1->execute();
		@hrcdata = $sqlh1->fetchrow_array;
		$sqlh1->finish;
                
    		$hrc_zero_block      = $hrcdata[0];
    		$hrc_timing_mode     = $hrcdata[1];
		$hrc_si_mode         = $hrcdata[2];
	} else {
    		$hrc_zero_block      = "N";
    		$hrc_timing_mode     = "N";
		$hrc_si_mode	     = "NULL";
	}

#--------------------------------------------------------------------------
#-----------  if it's an acis observation, get values from acisparam table
#--------------------------------------------------------------------------

	if ($acisid){
		$sqlh1 = $dbh1->prepare(qq(select 
			exp_mode,
			ccdi0_on, ccdi1_on, ccdi2_on, ccdi3_on,
			ccds0_on, ccds1_on, ccds2_on, ccds3_on, ccds4_on,ccds5_on,
			bep_pack, onchip_sum, onchip_row_count, onchip_column_count, frame_time,
			subarray, subarray_start_row, subarray_row_count, 
			duty_cycle, secondary_exp_count, primary_exp_time,
			eventfilter, eventfilter_lower, eventfilter_higher,
			most_efficient, dropped_chip_count,
 			multiple_spectral_lines,  spectra_max_count


		from acisparam where acisid=$acisid));
		$sqlh1->execute();
		@acisdata = $sqlh1->fetchrow_array;
		$sqlh1->finish;
                
    		$exp_mode 		= $acisdata[0];
    		$ccdi0_on 		= $acisdata[1];
    		$ccdi1_on 		= $acisdata[2];
    		$ccdi2_on 		= $acisdata[3];
    		$ccdi3_on 		= $acisdata[4];

    		$ccds0_on 		= $acisdata[5];
    		$ccds1_on 		= $acisdata[6];
    		$ccds2_on 		= $acisdata[7];
    		$ccds3_on 		= $acisdata[8];
    		$ccds4_on 		= $acisdata[9];
    		$ccds5_on 		= $acisdata[10];

    		$bep_pack 		= $acisdata[11];
    		$onchip_sum          	= $acisdata[12];
    		$onchip_row_count    	= $acisdata[13];
    		$onchip_column_count 	= $acisdata[14];
    		$frame_time          	= $acisdata[15];

    		$subarray            	= $acisdata[16];
    		$subarray_start_row  	= $acisdata[17];
    		$subarray_row_count  	= $acisdata[18];
    		$duty_cycle          	= $acisdata[19];
    		$secondary_exp_count 	= $acisdata[20];

    		$primary_exp_time    	= $acisdata[21];
    		$eventfilter         	= $acisdata[22];
    		$eventfilter_lower   	= $acisdata[23];
    		$eventfilter_higher  	= $acisdata[24];
    		$most_efficient      	= $acisdata[25];

		$dropped_chip_count     = $acisdata[26];

#
#---- added 3/28/11
#
		$multiple_spectral_lines = $acisdata[27];  
		$spectra_max_count       = $acisdata[28];

#    		$bias_after          	= $acisdata[27];

#    		$secondary_exp_time  	= $acisdata[22];
#    		$bias_request        	= $acisdata[25];
#    		$fep                 	= $acisdata[27];
#    		$subarray_frame_time 	= $acisdata[28];
#    		$frequency           	= $acisdata[30];
	} else {
    		$exp_mode 		= "NULL";
    		$ccdi0_on 		= "NULL";
    		$ccdi1_on 		= "NULL";
    		$ccdi2_on 		= "NULL";
    		$ccdi3_on 		= "NULL";
    		$ccds0_on 		= "NULL";
    		$ccds1_on 		= "NULL";
    		$ccds2_on 		= "NULL";
    		$ccds3_on 		= "NULL";
    		$ccds4_on 		= "NULL";
    		$ccds5_on 		= "NULL";
    		$bep_pack 		= "NULL";
    		$onchip_sum          	= "NULL";
    		$onchip_row_count    	= "NULL";
    		$onchip_column_count 	= "NULL";
    		$frame_time          	= "NULL";
    		$subarray            	= "NONE";
    		$subarray_start_row  	= "NULL";
    		$subarray_row_count  	= "NULL";
    		$subarray_frame_time 	= "NULL";
    		$duty_cycle          	= "NULL";
    		$secondary_exp_count 	= "NULL";
    		$primary_exp_time    	= "";
    		$eventfilter         	= "NULL";
    		$eventfilter_lower   	= "NULL";
    		$eventfilter_higher  	= "NULL";
    		$spwindow            	= "NULL";
#    		$bias_request        	= "NULL";
    		$most_efficient      	= "NULL";
#    		$fep                 	= "NULL";
		$dropped_chip_count     = "NULL";
#    		$secondary_exp_time  	= "";
#    		$frequency           	= "NULL";
#  		$bias_after          	= "NULL";

#
#--- added 3/28/11
#
		$multiple_spectral_lines = "NULL";
		$spectra_max_count       = "NULL";
	}

#-------------------------------------------------------------------
#-------  get values from aciswin table
#-------  first, get aciswin_id to see whether there are any aciswin param set
#-------------------------------------------------------------------

	$sqlh1 = $dbh1->prepare(qq(select  aciswin_id  from aciswin where  obsid=$obsid));
	$sqlh1->execute();
	@aciswindata = $sqlh1->fetchrow_array;
	$sqlh1->finish;
	$aciswin_id[0] = $aciswindata[0];
	$aciswin_id[0] =~ s/\s+//g;

	if($aciswin_id[0] =~ /\d/){
		$sqlh1 = $dbh1->prepare(qq(select 
			ordr, start_row, start_column, width, height, lower_threshold, 
			pha_range, sample, chip, include_flag , aciswin_id
		from aciswin where obsid=$obsid));
		$sqlh1->execute();
		$j = 0;
		while(my(@aciswindata) = $sqlh1->fetchrow_array){
			
			$ordr[$j]            = $aciswindata[0];
			$start_row[$j]       = $aciswindata[1];
			$start_column[$j]    = $aciswindata[2];
			$width[$j]           = $aciswindata[3];
			$height[$j]          = $aciswindata[4];
			$lower_threshold[$j] = $aciswindata[5];

			if($lower_threshold[$j] > 0.5){
				$awc_l_th = 1;
			}

			$pha_range[$j]       = $aciswindata[6];
			$sample[$j]          = $aciswindata[7];
			$chip[$j]            = $aciswindata[8];
			$include_flag[$j]    = $aciswindata[9];
			$aciswin_id[$j]      = $aciswindata[10];

			$j++;
		}
		$aciswin_no = $j;

		$sqlh1->finish;

#
#--- reorder the rank with increasing order value sequence (added Jul 14, 2015)
#
        if($aciswin_no > 0){
            @rlist = ();
            for($i = 0; $i <= $aciswin_no; $i++){
                push(@rlist, $ordr[$i]);
            }
            @sorted = sort{$a<=>$b} @rlist;
            @tlist = ();
            foreach $ent (@sorted){
                for($i = 0; $i <= $aciswin_no; $i++){
                    if($ent == $ordr[$i]){
                        push(@tlist, $i);
                    }
                }
            }
        
            @temp0 = ();
            @temp1 = ();
            @temp2 = ();
            @temp3 = ();
            @temp4 = ();
            @temp5 = ();
            @temp6 = ();
            @temp7 = ();
            @temp8 = ();
            @temp9 = ();
            @temp10= ();
        
            for($i = 0; $i <= $aciswin_no; $i++){
                $pos = $tlist[$i];
                if($pos == 0){
                    last;
                }
                $pos--;
        
                push(@temp0 , $ordr[$pos]);
                push(@temp1 , $start_row[$pos]);
                push(@temp2 , $start_column[$pos]);
                push(@temp3 , $width[$pos]);
                push(@temp4 , $height[$pos]);
                push(@temp5 , $lower_threshold[$pos]);
                push(@temp6 , $pha_range[$pos]);
                push(@temp7 , $sample[$pos]);
                push(@temp8 , $chip[$pos]);
                push(@temp9 , $include_flag[$pos]);
                push(@temp10, $aciswin_id[$pos]);
            }
            @ordr            = @temp0;
            @start_row       = @temp1;
            @start_column    = @temp2;
            @width           = @temp3;
            @height          = @temp4;
            @lower_threshold = @temp5;
            @pha_range       = @temp6;
            @sample          = @temp7;
            @chip            = @temp8;
            @include_flag    = @temp9;
            @aciswin_id      = @temp10;
        
        }

#------------------ Jul 14, 2015 update ends -------------------------



#		OUTER:
#		for($aciswin_no = 1; $aciswin_no < 30; $aciswin_no++){
#			$test  = $aciswin_id[0] + $aciswin_no;
#			$sqlh1 = $dbh1->prepare(qq(select aciswin_id from aciswin where aciswin_id = $test  and  obsid=$obsid));
#			$sqlh1->execute();
#			@aciswindata = $sqlh1->fetchrow_array;
#			$sqlh1->finish;
#			if($aciswindata[0] !~ /\d/){
#				$aciswin_no--;
#				last OUTER;
#			}
#			$aciswin_id[$aciswin_no] = $aciswindata[0];
#		}
#----------------------------------------------------------------------
#------- get the rest of acis window requirement data from the database
#----------------------------------------------------------------------
#
#		$awc_l_th = 0;
#		for($j = 0; $j < $aciswin_no; $j++){
#			$sqlh1 = $dbh1->prepare(qq(select 
#				ordr,start_row,start_column,width,height,lower_threshold, 
#				pha_range,sample,chip,include_flag 
#			from aciswin where aciswin_id = $aciswin_id[$j]  and  obsid=$obsid));
#
#			$sqlh1->execute();
#			@aciswindata = $sqlh1->fetchrow_array;
#			$sqlh1->finish;
#	
#			$ordr[$j]            = $aciswindata[0];
#			$start_row[$j]       = $aciswindata[1];
#			$start_column[$j]    = $aciswindata[2];
#			$width[$j]           = $aciswindata[3];
#			$height[$j]          = $aciswindata[4];
#			$lower_threshold[$j] = $aciswindata[5];
#
#			if($lower_threshold[$j] > 0.5){
#				$awc_l_th = 1;
#			}
#
#			$pha_range[$j]       = $aciswindata[6];
#			$sample[$j]          = $aciswindata[7];
#			$chip[$j]            = $aciswindata[8];
#			$include_flag[$j]    = $aciswindata[9];
#		}
	}else{

#--------------------------------------------------------
#----    no acis wind constrain parameters are assigned.
#--------------------------------------------------------

		$aciswin_no = 0;
	}


#---------------------------------
#-------  get values from phasereq
#---------------------------------

	$sqlh1 = $dbh1->prepare(qq(select 
		phase_period,phase_epoch,phase_start,phase_end, 
		phase_start_margin, phase_end_margin 
	from phasereq where obsid=$obsid));
	$sqlh1->execute();
	@phasereqdata = $sqlh1->fetchrow_array;
	$sqlh1->finish;

	$phase_period       = $phasereqdata[0];
	$phase_epoch        = $phasereqdata[1];
	$phase_start        = $phasereqdata[2];
	$phase_end          = $phasereqdata[3];
	$phase_start_margin = $phasereqdata[4];
	$phase_end_margin   = $phasereqdata[5];

#------------------------------
#------  get values from dither
#------------------------------

	$sqlh1 = $dbh1->prepare(qq(select 
		y_amp,y_freq,y_phase,z_amp,z_freq,z_phase 
	from dither where obsid=$obsid));
	$sqlh1->execute();
	@ditherdata = $sqlh1->fetchrow_array;
	$sqlh1->finish;

	$y_amp   = $ditherdata[0];
	$y_freq  = $ditherdata[1];
	$y_phase = $ditherdata[2];
	$z_amp   = $ditherdata[3];
	$z_freq  = $ditherdata[4];
	$z_phase = $ditherdata[5];

#-----------------------------
#--------  get values from sim
#-----------------------------

	$sqlh1 = $dbh1->prepare(qq(select 
		trans_offset,focus_offset 
	from sim where obsid=$obsid));
	$sqlh1->execute();
	@simdata = $sqlh1->fetchrow_array;
	$sqlh1->finish;

	$trans_offset = $simdata[0];
	$focus_offset = $simdata[1];

#---------------------------
#------  get values from soe
#---------------------------

	$sqlh1 = $dbh1->prepare(qq(select soe_roll from soe where obsid=$obsid  and unscheduled='N'));
	$sqlh1->execute();
	@soedata = $sqlh1->fetchrow_array;
	$sqlh1->finish;

	$roll_obsr = $soedata[0];

#------------------------------------
#-------    get values from prop_info
#------------------------------------

	$sqlh1 = $dbh1->prepare(qq(select 
		prop_num,title,joint from prop_info 
	where ocat_propid=$proposal_id));
	$sqlh1->execute();
	@prop_infodata = $sqlh1->fetchrow_array;
	$sqlh1->finish;

	$proposal_number = $prop_infodata[0];
	$proposal_title  = $prop_infodata[1];
	$proposal_joint  = $prop_infodata[2];
	$proposal_hst    = $prop_infodata[3];
	$proposal_noao   = $prop_infodata[4];
	$proposal_xmm    = $prop_infodata[5];
	$proposal_rxte   = $prop_infodata[6];
	$proposal_vla    = $prop_infodata[7];
	$proposal_vlba   = $prop_infodata[8];

#-------------------------------------------------------------
#<<<<<<------>>>>>>  switch to axafusers <<<<<<------>>>>>>>>
#-------------------------------------------------------------

	$db = "server=$server;database=axafusers";
	$dsn1 = "DBI:Sybase:$db";
	$dbh1 = DBI->connect($dsn1, $db_user, $db_passwd, { PrintError => 0, RaiseError => 1});

#--------------------------------
#-----  get proposer's last name
#--------------------------------

	$sqlh1 = $dbh1->prepare(qq(select 
		last from person_short s,axafocat..prop_info p 
	where p.ocat_propid=$proposal_id and s.pers_id=p.piid));
	$sqlh1->execute();
	@namedata = $sqlh1->fetchrow_array;
	$sqlh1->finish;

	$PI_name = $namedata[0];

#---------------------------------------------------------------------------
#------- if there is a co-i who is observer, get them, otherwise it's the pi
#---------------------------------------------------------------------------

	$sqlh1 = $dbh1->prepare(qq(select 
		coi_contact from person_short s,axafocat..prop_info p 
	where p.ocat_propid = $proposal_id));
	$sqlh1->execute();
	($observerdata) = $sqlh1->fetchrow_array;
	$sqlh1->finish;

	if ($observerdata =~/N/){
    		$Observer = $PI_name;
	} else {
		$sqlh1 = $dbh1->prepare(qq(select 
			last from person_short s,axafocat..prop_info p 
		where p.ocat_propid = $proposal_id and p.coin_id = s.pers_id));
		$sqlh1->execute();
		($observerdata) = $sqlh1->fetchrow_array;
		$sqlh1->finish;

    		$Observer=$observerdata;
	}

#-------------------------------------------------
#---- Disconnect from the server
#-------------------------------------------------

	$dbh1->disconnect();


#-----------------------------------------------------------------
#------ these ~100 lines are to remove the whitespace from most of
#------ the obscat dump entries.  
#-----------------------------------------------------------------
	$targid  		=~ s/\s+//g; 
	$seq_nbr 		=~ s/\s+//g; 
	$targname 		=~ s/\s+//g; 
	$obj_flag 		=~ s/\s+//g; 
	if($obj_flag 		=~ /NONE/){
		$obj_flag 	= "NO";
	}
	$object 		=~ s/\s+//g; 
	$si_mode 		=~ s/\s+//g; 
	$photometry_flag 	=~ s/\s+//g; 
	$vmagnitude 		=~ s/\s+//g; 
	$ra 			=~ s/\s+//g; 
	$dec 			=~ s/\s+//g; 
	$est_cnt_rate 		=~ s/\s+//g; 
	$forder_cnt_rate 	=~ s/\s+//g; 
	$y_det_offset 		=~ s/\s+//g; 
	$z_det_offset 		=~ s/\s+//g; 
	$raster_scan 		=~ s/\s+//g; 
	$defocus 		=~ s/\s+//g; 
	$dither_flag 		=~ s/\s+//g; 
	$roll 			=~ s/\s+//g; 
	$roll_tolerance 	=~ s/\s+//g; 
	$approved_exposure_time =~ s/\s+//g; 
	$pre_min_lead 		=~ s/\s+//g; 
	$pre_max_lead 		=~ s/\s+//g; 
	$pre_id 		=~ s/\s+//g; 
	$seg_max_num 		=~ s/\s+//g; 
	$aca_mode 		=~ s/\s+//g; 
	$phase_constraint_flag 	=~ s/\s+//g; 
	$proposal_id 		=~ s/\s+//g; 
	$acisid 		=~ s/\s+//g; 
	$hrcid 			=~ s/\s+//g; 
	$grating 		=~ s/\s+//g; 
	$instrument 		=~ s/\s+//g; 
	$rem_exp_time 		=~ s/\s+//g; 
	#$soe_st_sched_date 	=~ s/\s+//g; 
	$type 			=~ s/\s+//g; 
	#$lts_lt_plan 		=~ s/\s+//g; 
	$mpcat_star_fidlight_file =~ s/\s+//g; 
	$status 		=~ s/\s+//g; 
	$data_rights 		=~ s/\s+//g; 
	$server_name 		=~ s/\s+//g; 
	$hrc_zero_block 	=~ s/\s+//g; 
	$hrc_timing_mode 	=~ s/\s+//g;
	$hrc_si_mode 		=~ s/\s+//g;
	$exp_mode 		=~ s/\s+//g; 
#	$standard_chips 	=~ s/\s+//g; 
	$ccdi0_on 		=~ s/\s+//g; 
	$ccdi1_on 		=~ s/\s+//g; 
	$ccdi2_on 		=~ s/\s+//g; 
	$ccdi3_on 		=~ s/\s+//g; 
	$ccds0_on 		=~ s/\s+//g; 
	$ccds1_on 		=~ s/\s+//g; 
	$ccds2_on 		=~ s/\s+//g; 
	$ccds3_on 		=~ s/\s+//g; 
	$ccds4_on 		=~ s/\s+//g; 
	$ccds5_on 		=~ s/\s+//g; 
	$bep_pack 		=~ s/\s+//g; 
	$onchip_sum 		=~ s/\s+//g; 
	$onchip_row_count 	=~ s/\s+//g; 
	$onchip_column_count 	=~ s/\s+//g; 
	$frame_time 		=~ s/\s+//g; 
	$subarray 		=~ s/\s+//g; 
	$subarray_start_row 	=~ s/\s+//g; 
	$subarray_row_count 	=~ s/\s+//g; 
	$subarray_frame_time 	=~ s/\s+//g; 
	$duty_cycle 		=~ s/\s+//g; 
	$secondary_exp_count 	=~ s/\s+//g; 
	$primary_exp_time 	=~ s/\s+//g; 
	$secondary_exp_time 	=~ s/\s+//g; 
	$eventfilter 		=~ s/\s+//g; 
	$eventfilter_lower 	=~ s/\s+//g; 
	$eventfilter_higher 	=~ s/\s+//g; 
#----- added 3/28/11
        $multiple_spectral_lines =~ s/\s+//g; 
        $spectra_max_count       =~ s/\s+//g; 

	$spwindow 		=~ s/\s+//g; 
	$multitelescope_interval=~s/\s+//g;
	$phase_period 		=~ s/\s+//g; 
	$phase_epoch 		=~ s/\s+//g; 
	$phase_start 		=~ s/\s+//g; 
	$phase_end 		=~ s/\s+//g; 
	$phase_start_margin 	=~ s/\s+//g; 
	$phase_end_margin 	=~ s/\s+//g; 
	$PI_name 		=~ s/\s+//g; 
	$proposal_number 	=~ s/\s+//g; 
	$trans_offset 		=~ s/\s+//g; 
	$focus_offset 		=~ s/\s+//g;
	$tooid 			=~ s/\s+//g;
	$description 		=~ s/\s+//g;
	$total_fld_cnt_rate 	=~ s/\s+//g;
	$extended_src 		=~ s/\s+//g;
	$y_amp 			=~ s/\s+//g;
	$y_freq 		=~ s/\s+//g;
	$y_phase 		=~ s/\s+//g;
	$z_amp 			=~ s/\s+//g;
	$z_freq 		=~ s/\s+//g;
	$z_phase 		=~ s/\s+//g;
	$most_efficient 	=~ s/\s+//g;
	$fep 			=~ s/\s+//g;
	$dropped_chip_count     =~ s/\s+//g;
	$timing_mode 		=~ s/\s+//g;
	$uninterrupt 		=~ s/\s+//g;
	$proposal_joint 	=~ s/\s+//g;
	$proposal_hst 		=~ s/\s+//g;
	$proposal_noao 		=~ s/\s+//g;
	$proposal_xmm 		=~ s/\s+//g;
	$roll_obsr 		=~ s/\s+//g;
	$multitelescope 	=~ s/\s+//g;
	$observatories 		=~ s/\s+//g;
	$too_type 		=~ s/\s+//g;
	$too_start 		=~ s/\s+//g;
	$too_stop 		=~ s/\s+//g;
	$too_followup 		=~ s/\s+//g;
	$roll_flag 		=~ s/\s+//g;
	$window_flag 		=~ s/\s+//g;
	$constr_in_remarks  	=~ s/\s+//g;
	$group_id  		=~ s/\s+//g;
	$obs_ao_str  		=~ s/\s+//g;

#--------------------------------------------------------------------
#----- roll_ordr, time_ordr, and ordr need extra check for each order
#--------------------------------------------------------------------

	for($k = 1; $k <= $roll_ordr; $k++){
		$roll_constraint[$k] =~ s/\s+//g; 
		$roll_180[$k]        =~ s/\s+//g; 
		$roll[$k]            =~ s/\s+//g;
		$roll_tolerance[$k]  =~ s/\s+//g; 
	}

	for($k = 1; $k <= $time_ordr; $k++){
		$window_constraint[$k] =~ s/\s+//g; 
#		$tstart[$k]            =~ s/\s+//g; 
#		$tstop[$k]             =~ s/\s+//g; 
	}

	for($k = 0; $k < $aciswin_no; $k++){
		$aciswin_id[$k]      =~ s/\s+//g;
		$ordr[$k]	     =~ s/\s+//g;
		$chip[$k]            =~ s/\s+//g;
		$include_flag[$k]    =~ s/\s+//g;
		$start_row[$k]       =~ s/\s+//g; 
		$start_column[$k]    =~ s/\s+//g; 
		$width[$k]           =~ s/\s+//g; 
		$height[$k]          =~ s/\s+//g; 
		$lower_threshold[$k] =~ s/\s+//g; 
		$pha_range[$k]       =~ s/\s+//g; 
		$sample[$k]          =~ s/\s+//g; 
	}

#-----------------------------------
#-----------  A FEW EXTRA SETTINGS
#-----------------------------------

	$ra   = sprintf("%3.6f", $ra);		# setting to 6 digit after a dicimal point
	$dec  = sprintf("%3.6f", $dec);
	$dra  = $ra;
	$ddec = $dec;

#---------------------------------------------------------------------------
#------- time need to be devided into year, month, day, and time for display
#---------------------------------------------------------------------------

	for($k = 1; $k <= $time_ordr; $k++){
		if($tstart[$k] ne ''){
			$input_time      = $tstart[$k];
			mod_time_format();		# sub mod_time_format changes time format
			$start_year[$k]  = $year;
			$start_month[$k] = $month;
			$start_date[$k]  = $day;
			$start_time[$k]  = $time;
			$tstart[$k]      = "$month:$day:$year:$time";
		}
		
		if($tstop[$k] ne ''){
			$input_time    = $tstop[$k];
			mod_time_format();
			$end_year[$k]  = $year;
			$end_month[$k] = $month;
			$end_date[$k]  = $day;
			$end_time[$k]  = $time;
			$tstop[$k]     = "$month:$day:$year:$time";
		}
	}

#---------------------------------------------------------------------------------
#------ here are the cases which database values and display values are different.
#---------------------------------------------------------------------------------

	if($multitelescope eq '')    {$multitelescope = 'N'}

	if($proposal_joint eq '')    {$proposal_joint = 'N/A'}

	if($proposal_hst eq '')      {$proposal_hst = 'N/A'}

	if($proposal_noao eq '')     {$proposal_noao = 'N/A'}

	if($proposal_xmm eq '')      {$proposal_xmm = 'N/A'}

	if($rxte_approved_time eq ''){$rxte_approved_time = 'N/A'}

	if($vla_approved_time eq '') {$vla_approved_time = 'N/A'}

	if($vlba_approved_time eq ''){$vlba_approved_time = 'N/A'}

	
	if($roll_flag    eq 'NULL')	{$droll_flag = 'NULL'}
	elsif($roll_flag eq '')		{$droll_flag = 'NULL'; $roll_flag = 'NULL';}
	elsif($roll_flag eq 'Y')	{$droll_flag = 'YES'}
	elsif($roll_flag eq 'N')	{$droll_flag = 'NO'}
	elsif($roll_flag eq 'P')	{$droll_flag = 'PREFERENCE'}
	
	if($window_flag    eq 'NULL')	{$dwindow_flag = 'NULL'}
	elsif($window_flag eq '')	{$dwindow_flag = 'NULL'; $window_flag = 'NULL';}
	elsif($window_flag eq 'Y')	{$dwindow_flag = 'YES'}
	elsif($window_flag eq 'N')	{$dwindow_flag = 'NO'}
	elsif($window_flag eq 'P')	{$dwindow_flag = 'PREFERENCE'}
	
	if($dither_flag    eq 'NULL')	{$ddither_flag = 'NULL'}
	elsif($dither_flag eq '')	{$ddither_flag = 'NULL'; $dither_flag = 'NULL';}
	elsif($dither_flag eq 'Y')	{$ddither_flag = 'YES'}
	elsif($dither_flag eq 'N')	{$ddither_flag = 'NO'}
	
	if($uninterrupt    eq 'NULL')	{$duninterrupt = 'NULL'}
	elsif($uninterrupt eq '')	{$duninterrupt = 'NULL'; $uninterrupt = 'NULL';}
	elsif($uninterrupt eq 'N')	{$duninterrupt = 'NO'}
	elsif($uninterrupt eq 'Y')	{$duninterrupt = 'YES'}
	elsif($uninterrupt eq 'P')	{$duninterrupt = 'PREFERENCE'}

	if($photometry_flag    eq 'NULL')	{$dphotometry_flag = 'NULL'}
	elsif($photometry_flag eq '') 		{$dphotometry_flag = 'NULL'; $photometry_flag = 'NULL'}
	elsif($photometry_flag eq 'Y')		{$dphotometry_flag = 'YES'}
	elsif($photometry_flag eq 'N')		{$dphotometry_flag = 'NO'}
	
	for($k = 1; $k <= $time_ordr; $k++){
		if($window_constraint[$k]    eq 'Y')   {$dwindow_constraint[$k] = 'CONSTRAINT'}
		elsif($window_constraint[$k] eq 'P')   {$dwindow_constraint[$k] = 'PREFERENCE'}
		elsif($window_constraint[$k] eq 'N')   {$dwindow_constraint[$k] = 'NONE'}
		elsif($window_constraint[$k] eq 'NULL'){$dwindow_constraint[$k] = 'NULL'}
		elsif($window_constraint[$k] eq ''){
				$window_constraint[$k]  = 'NULL';
				$dwindow_constraint[$k] = 'NULL';
		}
	}	
	
	for($k = 1; $k <= $roll_ordr; $k++){
		if($roll_constraint[$k]    eq 'Y')   {$droll_constraint[$k] = 'CONSTRAINT'}
		elsif($roll_constraint[$k] eq 'P')   {$droll_constraint[$k] = 'PREFERENCE'}
		elsif($roll_constraint[$k] eq 'N')   {$droll_constraint[$k] = 'NONE'}
		elsif($roll_constraint[$k] eq 'NULL'){$droll_constraint[$k] = 'NULL'}
		elsif($roll_constraint[$k] eq ''){
				$roll_constraint[$k]  = 'NULL';
				$droll_constraint[$k] = 'NULL';
		}

		if($roll_180[$k]    eq 'Y'){$droll_180[$k] = 'YES'}
		elsif($roll_180[$k] eq 'N'){$droll_180[$k] = 'NO'}
		else{$droll_180[$k] = 'NULL'}
	}	

	if($constr_in_remarks eq ''){$dconstr_in_remarks = 'NO'; $constr_in_remarks = 'N'}
	elsif($constr_in_remarks eq 'N'){$dconstr_in_remarks = 'NO'}
	elsif($constr_in_remarks eq 'Y'){$dconstr_in_remarks = 'YES'}
	elsif($constr_in_remarks eq 'P'){$dconstr_in_remarks = 'PREFERENCE'}

	if($phase_constraint_flag eq 'NULL'){$dphase_constraint_flag = 'NULL'}
	elsif($phase_constraint_flag eq '') {$dphase_constraint_flag = 'NONE'; $phase_constraint_flag = 'NULL'}
	elsif($phase_constraint_flag eq 'N'){$dphase_constraint_flag = 'NONE'}
	elsif($phase_constraint_flag eq 'Y'){$dphase_constraint_flag = 'CONSTRAINT'}
	elsif($phase_constraint_flag eq 'P'){$dphase_constraint_flag = 'PREFERENCE'}

	if($monitor_flag eq 'NULL')   {$dmonitor_flag = 'NULL'}
	elsif($monitor_flag eq '')    {$dmonitor_flag = 'NULL'}
	elsif($monitor_flag eq 'Y')   {$dmonitor_flag = 'YES'}
	elsif($monitor_flag eq 'YES') {$dmonitor_flag = 'YES'}
	elsif($monitor_flag eq 'N')   {$dmonitor_flag = 'NONE'}
	elsif($monitor_flag eq 'NONE'){$dmonitor_flag = 'NONE'}
	elsif($monitor_flag eq 'NO')  {$dmonitor_flag = 'NO'}

	if($multitelescope eq 'Y')   {$dmultitelescope = 'YES'}
	elsif($multitelescope eq 'N'){$dmultitelescope = 'NO'}
	elsif($multitelescope eq 'P'){$dmultitelescope = 'PREFERENCE'}

	if($hrc_zero_block eq 'NULL'){$dhrc_zero_block = 'NULL'}
	elsif($hrc_zero_block eq '') {$dhrc_zero_block = 'NO'; $hrc_zero_block = 'N';}
	elsif($hrc_zero_block eq 'Y'){$dhrc_zero_block = 'YES'}
	elsif($hrc_zero_block eq 'N'){$dhrc_zero_block = 'NO'}

	if($hrc_timing_mode eq 'NULL'){$dhrc_timing_mode = 'NULL'}
	elsif($hrc_timing_mode eq '') {$dhrc_timing_mode = 'NO'; $hrc_timing_mode = 'N';}
	elsif($hrc_timing_mode eq 'Y'){$dhrc_timing_mode = 'YES'}
	elsif($hrc_timing_mode eq 'N'){$dhrc_timing_mode = 'NO'}

#	if($ordr =~ /\W/ || $ordr == '') {
#		$ordr = 1;
#	}

	if($most_efficient eq 'NULL'){$dmost_efficient = 'NULL'}
	elsif($most_efficient eq '') {$most_efficient = 'NULL'; $dmost_efficient  = 'NULL'}
	elsif($most_efficient eq 'Y'){$dmost_efficient = 'YES'}
	elsif($most_efficient eq 'N'){$dmost_efficient = 'NO'}

	if($ccdi0_on eq 'NULL') {$dccdi0_on = 'NULL'}
	elsif($ccdi0_on eq '')  {$dccdi0_on = 'NULL'; $ccdi0_on = 'NULL'}
	elsif($ccdi0_on eq 'Y') {$dccdi0_on = 'YES'}
	elsif($ccdi0_on eq 'N') {$dccdi0_on = 'NO'}
	elsif($ccdi0_on eq 'O1'){$dccdi0_on = 'OPT1'}
	elsif($ccdi0_on eq 'O2'){$dccdi0_on = 'OPT2'}
	elsif($ccdi0_on eq 'O3'){$dccdi0_on = 'OPT3'}
	elsif($ccdi0_on eq 'O4'){$dccdi0_on = 'OPT4'}
	elsif($ccdi0_on eq 'O5'){$dccdi0_on = 'OPT5'}
	
	if($ccdi1_on eq 'NULL') {$dccdi1_on = 'NULL'}
	elsif($ccdi1_on eq '')  {$dccdi1_on = 'NULL'; $ccdi1_on = 'NULL'}
	elsif($ccdi1_on eq 'Y') {$dccdi1_on = 'YES'}
	elsif($ccdi1_on eq 'N') {$dccdi1_on = 'NO'}
	elsif($ccdi1_on eq 'O1'){$dccdi1_on = 'OPT1'}
	elsif($ccdi1_on eq 'O2'){$dccdi1_on = 'OPT2'}
	elsif($ccdi1_on eq 'O3'){$dccdi1_on = 'OPT3'}
	elsif($ccdi1_on eq 'O4'){$dccdi1_on = 'OPT4'}
	elsif($ccdi1_on eq 'O5'){$dccdi1_on = 'OPT5'}
	
	if($ccdi2_on eq 'NULL') {$dccdi2_on = 'NULL'}
	elsif($ccdi2_on eq '')  {$dccdi2_on = 'NULL'; $ccdi2_on = 'NULL'}
	elsif($ccdi2_on eq 'Y') {$dccdi2_on = 'YES'}
	elsif($ccdi2_on eq 'N') {$dccdi2_on = 'NO'}
	elsif($ccdi2_on eq 'O1'){$dccdi2_on = 'OPT1'}
	elsif($ccdi2_on eq 'O2'){$dccdi2_on = 'OPT2'}
	elsif($ccdi2_on eq 'O3'){$dccdi2_on = 'OPT3'}
	elsif($ccdi2_on eq 'O4'){$dccdi2_on = 'OPT4'}
	elsif($ccdi2_on eq 'O5'){$dccdi2_on = 'OPT5'}
	
	if($ccdi3_on eq 'NULL') {$dccdi3_on = 'NULL'}
	elsif($ccdi3_on eq '')  {$dccdi3_on = 'NULL'; $ccdi3_on = 'NULL'}
	elsif($ccdi3_on eq 'Y') {$dccdi3_on = 'YES'}
	elsif($ccdi3_on eq 'N') {$dccdi3_on = 'NO'}
	elsif($ccdi3_on eq 'O1'){$dccdi3_on = 'OPT1'}
	elsif($ccdi3_on eq 'O2'){$dccdi3_on = 'OPT2'}
	elsif($ccdi3_on eq 'O3'){$dccdi3_on = 'OPT3'}
	elsif($ccdi3_on eq 'O4'){$dccdi3_on = 'OPT4'}
	elsif($ccdi3_on eq 'O5'){$dccdi3_on = 'OPT5'}
	
	if($ccds0_on eq 'NULL') {$dccds0_on = 'NULL'}
	elsif($ccds0_on eq '')  {$dccds0_on = 'NULL'; $ccds0_on = 'NULL'}
	elsif($ccds0_on eq 'Y') {$dccds0_on = 'YES'}
	elsif($ccds0_on eq 'N') {$dccds0_on = 'NO'}
	elsif($ccds0_on eq 'O1'){$dccds0_on = 'OPT1'}
	elsif($ccds0_on eq 'O2'){$dccds0_on = 'OPT2'}
	elsif($ccds0_on eq 'O3'){$dccds0_on = 'OPT3'}
	elsif($ccds0_on eq 'O4'){$dccds0_on = 'OPT4'}
	elsif($ccds0_on eq 'O5'){$dccds0_on = 'OPT5'}
	
	if($ccds1_on eq 'NULL') {$dccds1_on = 'NULL'}
	elsif($ccds1_on eq '')  {$dccds1_on = 'NULL'; $ccds1_on = 'NULL'}
	elsif($ccds1_on eq 'Y') {$dccds1_on = 'YES'}
	elsif($ccds1_on eq 'N') {$dccds1_on = 'NO'}
	elsif($ccds1_on eq 'O1'){$dccds1_on = 'OPT1'}
	elsif($ccds1_on eq 'O2'){$dccds1_on = 'OPT2'}
	elsif($ccds1_on eq 'O3'){$dccds1_on = 'OPT3'}
	elsif($ccds1_on eq 'O4'){$dccds1_on = 'OPT4'}
	elsif($ccds1_on eq 'O5'){$dccds1_on = 'OPT5'}
	
	if($ccds2_on eq 'NULL') {$dccds2_on = 'NULL'}
	elsif($ccds2_on eq '')  {$dccds2_on = 'NULL'; $ccds2_on = 'NULL'}
	elsif($ccds2_on eq 'Y') {$dccds2_on = 'YES'}
	elsif($ccds2_on eq 'N') {$dccds2_on = 'NO'}
	elsif($ccds2_on eq 'O1'){$dccds2_on = 'OPT1'}
	elsif($ccds2_on eq 'O2'){$dccds2_on = 'OPT2'}
	elsif($ccds2_on eq 'O3'){$dccds2_on = 'OPT3'}
	elsif($ccds2_on eq 'O4'){$dccds2_on = 'OPT4'}
	elsif($ccds2_on eq 'O5'){$dccds2_on = 'OPT5'}
	
	if($ccds3_on eq 'NULL') {$dccds3_on = 'NULL'}
	elsif($ccds3_on eq '')  {$dccds3_on = 'NULL'; $ccds3_on = 'NULL'}
	elsif($ccds3_on eq 'Y') {$dccds3_on = 'YES'}
	elsif($ccds3_on eq 'N') {$dccds3_on = 'NO'}
	elsif($ccds3_on eq 'O1'){$dccds3_on = 'OPT1'}
	elsif($ccds3_on eq 'O2'){$dccds3_on = 'OPT2'}
	elsif($ccds3_on eq 'O3'){$dccds3_on = 'OPT3'}
	elsif($ccds3_on eq 'O4'){$dccds3_on = 'OPT4'}
	elsif($ccds3_on eq 'O5'){$dccds3_on = 'OPT5'}

	if($ccds4_on eq 'NULL') {$dccds4_on = 'NULL'}
	elsif($ccds4_on eq '')  {$dccds4_on = 'NULL'; $ccds4_on = 'NULL'}
	elsif($ccds4_on eq 'Y') {$dccds4_on = 'YES'}
	elsif($ccds4_on eq 'N') {$dccds4_on = 'NO'}
	elsif($ccds4_on eq 'O1'){$dccds4_on = 'OPT1'}
	elsif($ccds4_on eq 'O2'){$dccds4_on = 'OPT2'}
	elsif($ccds4_on eq 'O3'){$dccds4_on = 'OPT3'}
	elsif($ccds4_on eq 'O4'){$dccds4_on = 'OPT4'}
	elsif($ccds4_on eq 'O5'){$dccds4_on = 'OPT5'}

	if($ccds5_on eq 'NULL') {$dccds5_on = 'NULL'}
	elsif($ccds5_on eq '')  {$dccds5_on = 'NULL'; $ccds5_on = 'NULL'}
	elsif($ccds5_on eq 'Y') {$dccds5_on = 'YES'}
	elsif($ccds5_on eq 'N') {$dccds5_on = 'NO'}
	elsif($ccds5_on eq 'O1'){$dccds5_on = 'OPT1'}
	elsif($ccds5_on eq 'O2'){$dccds5_on = 'OPT2'}
	elsif($ccds5_on eq 'O3'){$dccds5_on = 'OPT3'}
	elsif($ccds5_on eq 'O4'){$dccds5_on = 'OPT4'}
	elsif($ccds5_on eq 'O5'){$dccds5_on = 'OPT5'}

#
#---- COMMENTED OUT THIS PART ON 09/27/06
#--- until database can save CCD OPT selections, read the CCD setting from 
#--- $ocat_dir and reset the CCD selections
#
#	open(FH, "$ocat_dir/ccd_settings");
#	$ver = 0;
#	while(<FH>){
#		chomp $_;
#		if($_ !~ /\#/){
#			@atemp = split(/\s+/, $_);
#			if($atemp[0] == $obsid){
#				if($atemp[2] >= $ver){
#					$ccd_settings = $atemp[4];
#					$ver++;
#				}
#			}
#		}
#	}
#	close(FH);
#
#	@ccd_opt_chk = split(/:/, $ccd_settings);
#	if($ccd_opt_chk[0] =~ /OPT/){
#			$ccdi0_on  = $ccd_opt_chk[0];
#			$dccdi0_on = $ccd_opt_chk[0];
#	}
#	if($ccd_opt_chk[1] =~ /OPT/){
#			$ccdi1_on  = $ccd_opt_chk[1];
#			$dccdi1_on = $ccd_opt_chk[1];
#	}
#	if($ccd_opt_chk[2] =~ /OPT/){
#			$ccdi2_on  = $ccd_opt_chk[2];
#			$dccdi2_on = $ccd_opt_chk[2];
#	}
#	if($ccd_opt_chk[3] =~ /OPT/){
#			$ccdi3_on  = $ccd_opt_chk[3];
#			$dccdi3_on = $ccd_opt_chk[3];
#	}
#	if($ccd_opt_chk[4] =~ /OPT/){
#			$ccds0_on  = $ccd_opt_chk[4];
#			$dccds0_on = $ccd_opt_chk[4];
#	}
#	if($ccd_opt_chk[5] =~ /OPT/){
#			$ccds1_on  = $ccd_opt_chk[5];
#			$dccds1_on = $ccd_opt_chk[5];
#	}
#	if($ccd_opt_chk[6] =~ /OPT/){
#			$ccds2_on  = $ccd_opt_chk[6];
#			$dccds2_on = $ccd_opt_chk[6];
#	}
#	if($ccd_opt_chk[7] =~ /OPT/){
#			$ccds3_on  = $ccd_opt_chk[7];
#			$dccds3_on = $ccd_opt_chk[7];
#	}
#	if($ccd_opt_chk[8] =~ /OPT/){
#			$ccds4_on  = $ccd_opt_chk[8];
#			$dccds4_on = $ccd_opt_chk[8];
#	}
#	if($ccd_opt_chk[9] =~ /OPT/){
#			$ccds5_on  = $ccd_opt_chk[9];
#			$dccds5_on = $ccd_opt_chk[9];
#	}
#
#----  the end of the CCD OPT settings			
#

#
#---- ACIS subarray setting
#
	if($subarray eq '')         {$dsubarray = 'NO'}
	elsif($subarray eq 'N')     {$dsubarray = 'NO'}
	elsif($subarray eq 'NONE')  {$dsubarray = 'NO'}
	elsif($subarray eq 'CUSTOM'){$dsubarray = 'YES'}
	elsif($subarray eq 'Y')     {$dsubarray = 'YES'}


	if($duty_cycle eq 'NULL')  {$dduty_cycle = 'NULL'}
	elsif($duty_cycle eq '')   {$dduty_cycle = 'NULL'; $duty_cycle = 'NULL'}
	elsif($duty_cycle eq 'Y')  {$dduty_cycle = 'YES'}
	elsif($duty_cycle eq 'YES'){$dduty_cycle = 'YES'}
	elsif($duty_cycle eq 'N')  {$dduty_cycle = 'NO'}
	elsif($duty_cycle eq 'NO') {$dduty_cycle = 'NO'}

	if($onchip_sum eq 'NULL')  {$donchip_sum = 'NULL'}
	elsif($onchip_sum eq '')   {$donchip_sum = 'NULL'; $onchip_sum = 'NULL'}
	elsif($onchip_sum eq 'Y')  {$donchip_sum = 'YES'}
	elsif($onchip_sum eq 'N')  {$donchip_sum = 'NO'}

	if($eventfilter eq 'NULL') {$deventfilter = 'NULL'}
	elsif($eventfilter eq '')  {$deventfilter = 'NULL'; $eventfilter = 'NULL'}
	elsif($eventfilter eq 'Y') {$deventfilter = 'YES'}
	elsif($eventfilter eq 'N') {$deventfilter = 'NO'}

#
#--- added 03/29/11
#
	if($multiple_spectral_lines eq 'NULL') {$dmultiple_spectral_lines = 'NULL'}
	elsif($multiple_spectral_lines eq '')  {$dmultiple_spectral_lines = 'NULL'; $multiple_spectral_lines = 'NULL'}
	elsif($multiple_spectral_lines eq 'Y') {$dmultiple_spectral_lines = 'YES'}
	elsif($multiple_spectral_lines eq 'N') {$dmultiple_spectral_lines = 'NO'}

	if($spwindow eq 'NULL')    {$dspwindow = 'NULL'}
	elsif($spwindow eq '' )    {$dspwindow = 'NULL'; $spwindow = 'NULL'}
	elsif($spwindow eq 'Y')    {$dspwindow = 'YES'}
	elsif($spwindow eq 'N')    {$dspwindow = 'NO'}

	if($y_amp =~ /\d/){
        	$y_amp_asec  = 3600 * $y_amp;
	}else{
		$y_amp_asec  = $y_amp;
	}
	if($z_amp =~ /\d/){
        	$z_amp_asec  = 3600 * $z_amp;
	}else{
		$z_amp_asec  = $z_amp;
	}

	if($y_freq =~ /\d/){
        	$y_freq_asec = 3600 * $y_freq;
	}else{
		$y_freq_asec = $y_freq;
	}
	if($z_freq =~ /\d/){
        	$z_freq_asec = 3600 * $z_freq;
	}else{
		$z_freq_asec = $z_freq;
	}

	$orig_y_amp_asec  = $y_amp_asec;
	$orig_z_amp_asec  = $z_amp_asec;
	$orig_y_freq_asec = $y_freq_asec;
	$orig_z_freq_asec = $z_freq_asec;

#
#--- added 08/01/11
#
	if($extended_src eq 'NULL') {$dextended_src = 'NO'}
	elsif($extended_src eq '')  {$dextended_src = 'NO'}
	elsif($extended_src eq 'N') {$dextended_src = 'NO'}
	elsif($extended_src eq 'Y') {$dextended_src = 'YES'}


#-------------------------------------------------------------
#----- define several arrays of parameter names for later use
#-------------------------------------------------------------

#-------------------------
#----- all the param names
#-------------------------

		@namearray = (
		SEQ_NBR,STATUS,OBSID,PROPOSAL_NUMBER,PROPOSAL_TITLE,GROUP_ID,OBS_AO_STR,TARGNAME,
		SI_MODE,INSTRUMENT,GRATING,TYPE,PI_NAME,OBSERVER,APPROVED_EXPOSURE_TIME, REM_EXP_TIME,
		PROPOSAL_JOINT,PROPOSAL_HST,PROPOSAL_NOAO,PROPOSAL_XMM,PROPOSAL_RXTE,PROPOSAL_VLA,
		PROPOSAL_VLBA,SOE_ST_SCHED_DATE,LTS_LT_PLAN,
		RA,DEC,ROLL_OBSR,DRA,DDEC,Y_DET_OFFSET,Z_DET_OFFSET,TRANS_OFFSET,FOCUS_OFFSET,DEFOCUS,
		RASTER_SCAN,DITHER_FLAG,Y_AMP, Y_FREQ, Y_PHASE, Z_AMP, Z_FREQ, Z_PHASE,
		UNINTERRUPT,OBJ_FLAG,OBJECT,PHOTOMETRY_FLAG,VMAGNITUDE,EST_CNT_RATE,
		FORDER_CNT_RATE, TIME_ORDR,WINDOW_FLAG, ROLL_ORDR,ROLL_FLAG,
		CONSTR_IN_REMARKS,PHASE_CONSTRAINT_FLAG,PHASE_EPOCH,PHASE_PERIOD,
		PHASE_START,PHASE_START_MARGIN, PHASE_END,PHASE_END_MARGIN,PRE_ID,
		PRE_MIN_LEAD,PRE_MAX_LEAD,MULTITELESCOPE, OBSERVATORIES,
		HRC_ZERO_BLOCK,HRC_TIMING_MODE,HRC_SI_MODE,
		EXP_MODE,BEP_PACK,FRAME_TIME,MOST_EFFICIENT,
		CCDI0_ON, CCDI1_ON, CCDI2_ON, CCDI3_ON, CCDS0_ON, CCDS1_ON, CCDS2_ON, 
		CCDS3_ON,CCDS4_ON, CCDS5_ON,
		SUBARRAY,SUBARRAY_START_ROW,SUBARRAY_ROW_COUNT,
		DUTY_CYCLE,SECONDARY_EXP_COUNT,PRIMARY_EXP_TIME,
		ONCHIP_SUM,ONCHIP_ROW_COUNT,ONCHIP_COLUMN_COUNT,EVENTFILTER,EVENTFILTER_LOWER,
		MULTIPLE_SPECTRAL_LINES, SPECTRA_MAX_COUNT,						#--- added 03/29/11
		EVENTFILTER_HIGHER,SPWINDOW,ACISWIN_ID,ORDR, FEP,DROPPED_CHIP_COUNT, BIAS_RREQUEST,
		TOO_ID,TOO_TRIG,TOO_TYPE,TOO_START,TOO_STOP,TOO_FOLLOWUP,TOO_REMARKS,
		REMARKS,COMMENTS,
		MONITOR_FLAG,				#---- this one is added 3/1/06
		MULTITELESCOPE_INTERVAL,		#---- this one is added 9/2/08
		EXTENDED_SRC,				#---- added 08/01/11
#---removed IDs
#		WINDOW_CONSTRAINT,TSTART,TSTOP,
#		ROLL_CONSTRAINT,ROLL_180,ROLL,ROLL_TOLERANCE,
#		STANDARD_CHIPS,
#		SUBARRAY_FRAME_TIME,
#		SECONDARY_EXP_TIME,
#		CHIP,INCLUDE_FLAG,START_ROW,START_COLUMN,HEIGHT,WIDTH,
#		LOWER_THRESHOLD,PHA_RANGE,SAMPLE,
#		FREQUENCY,BIAS_AFTER,
		);

#--------------------------------------------------
#----- all the param names passed between cgi pages
#--------------------------------------------------

		@paramarray = (
		SI_MODE,
		INSTRUMENT,GRATING,TYPE,PI_NAME,OBSERVER,APPROVED_EXPOSURE_TIME, 
		RA,DEC,ROLL_OBSR,Y_DET_OFFSET,Z_DET_OFFSET,TRANS_OFFSET,FOCUS_OFFSET,DEFOCUS,
		DITHER_FLAG,Y_AMP, Y_FREQ, Y_PHASE, Z_AMP, Z_FREQ, Z_PHASE,Y_AMP_ASEC, Z_AMP_ASEC,
		Y_FREQ_ASEC, Z_FREQ_ASEC, UNINTERRUPT,OBJ_FLAG,OBJECT,PHOTOMETRY_FLAG,
		VMAGNITUDE,EST_CNT_RATE, FORDER_CNT_RATE, TIME_ORDR,WINDOW_FLAG, ROLL_ORDR,ROLL_FLAG,
		CONSTR_IN_REMARKS,PHASE_CONSTRAINT_FLAG,PHASE_EPOCH,PHASE_PERIOD,
		PHASE_START,PHASE_START_MARGIN, PHASE_END,PHASE_END_MARGIN,
		PRE_ID,PRE_MIN_LEAD,PRE_MAX_LEAD,MULTITELESCOPE, OBSERVATORIES,
		MULTITELESCOPE_INTERVAL,
		HRC_CONFIG,HRC_ZERO_BLOCK,HRC_TIMING_MODE,HRC_SI_MODE,
		EXP_MODE,BEP_PACK,FRAME_TIME,MOST_EFFICIENT,
		CCDI0_ON, CCDI1_ON, CCDI2_ON, CCDI3_ON, CCDS0_ON, CCDS1_ON, 
		CCDS2_ON, CCDS3_ON,CCDS4_ON, CCDS5_ON,
		SUBARRAY,SUBARRAY_START_ROW,SUBARRAY_ROW_COUNT,
		DUTY_CYCLE,SECONDARY_EXP_COUNT,PRIMARY_EXP_TIME,
		ONCHIP_SUM,ONCHIP_ROW_COUNT,ONCHIP_COLUMN_COUNT,EVENTFILTER,EVENTFILTER_LOWER,
		MULTIPLE_SPECTRAL_LINES, SPECTRA_MAX_COUNT,						#--- added 03/29/11
#		EVENTFILTER_HIGHER,SPWINDOW,ACISWIN_ID,ORDR, ACISWINTAG
		EVENTFILTER_HIGHER,SPWINDOW,ACISWIN_ID, 
		REMARKS,COMMENTS, ACISTAG,SITAG,GENERALTAG,
		DROPPED_CHIP_COUNT, GROUP_ID, MONITOR_FLAG,
		EXTENDED_SRC,
#---- removed IDs
#		STANDARD_CHIPS,
#		SUBARRAY_FRAME_TIME,
#		SECONDARY_EXP_TIME,
#		FREQUENCY,BIAS_AFTER,
#		WINDOW_CONSTRAINT,TSTART,TSTOP,
#		ROLL_CONSTRAINT,ROLL_180,ROLL,ROLL_TOLERANCE,
#		CHIP,INCLUDE_FLAG,START_ROW,START_COLUMN,HEIGHT,WIDTH,
#		LOWER_THRESHOLD,PHA_RANGE,SAMPLE,
#		BIAS_RREQUEST,FEP,


		);

#---------------------------------------------------------------
#----- all the param names passed not editable in ocat data page
#---------------------------------------------------------------

		@passarray = (
		SEQ_NBR,STATUS,OBSID,PROPOSAL_NUMBER,PROPOSAL_TITLE,GROUP_ID,OBS_AO_STR,TARGNAME,
		REM_EXP_TIME,RASTER_SCAN,ACA_MODE,
		PROPOSAL_JOINT,PROPOSAL_HST,PROPOSAL_NOAO,PROPOSAL_XMM,PROPOSAL_RXTE,PROPOSAL_VLA,
		PROPOSAL_VLBA,SOE_ST_SCHED_DATE,LTS_LT_PLAN,
		TOO_ID,TOO_TRIG,TOO_TYPE,TOO_START,TOO_STOP,TOO_FOLLOWUP,TOO_REMARKS,
		FEP,DROPPED_CHIP_COUNT
#--- removed ID
#		SI_MODE,
		);

#--------------------------------------
#----- all the param names in acis data
#--------------------------------------
	
       	@acisarray=(EXP_MODE,BEP_PACK,MOST_EFFICIENT,FRAME_TIME,
		CCDI0_ON,CCDI1_ON,CCDI2_ON,CCDI3_ON,
		CCDS0_ON,CCDS1_ON,CCDS2_ON,CCDS3_ON,CCDS4_ON,CCDS5_ON,
		SUBARRAY,SUBARRAY_START_ROW,SUBARRAY_ROW_COUNT,
		DUTY_CYCLE,SECONDARY_EXP_COUNT,PRIMARY_EXP_TIME,
		ONCHIP_SUM,
		ONCHIP_ROW_COUNT,ONCHIP_COLUMN_COUNT,EVENTFILTER,EVENTFILTER_LOWER,
		EVENTFILTER_HIGHER,DROPPED_CHIP_COUNT,SPWINDOW,
		MULTIPLE_SPECTRAL_LINES, SPECTRA_MAX_COUNT,	#--- added 03/29/11
#---- removed IDs
#		STANDARD_CHIPS,
#		SUBARRAY_FRAME_TIME,
#		SECONDARY_EXP_TIME,
#		FREQUENCY,BIAS_AFTER,
#		BIAS_REQUEST, FEP,
		);

#---------------------------------------
#----- all the param in acis window data
#---------------------------------------

	@aciswinarray=(START_ROW,START_COLUMN,HEIGHT,WIDTH,LOWER_THRESHOLD,
		       PHA_RANGE,SAMPLE,ACISWIN_ID,ORDR,CHIP,
#			INCLUDE_FLAG
			);

#-------------------------------------------
#----- all the param in general data dispaly
#-------------------------------------------


	@genarray=(REMARKS,INSTRUMENT,GRATING,TYPE,RA,DEC,APPROVED_EXPOSURE_TIME,
			Y_DET_OFFSET,Z_DET_OFFSET,TRANS_OFFSET, FOCUS_OFFSET,DEFOCUS,
			RASTER_SCAN,DITHER_FLAG, Y_AMP, Y_FREQ, Y_PHASE, Z_AMP, Z_FREQ, Z_PHASE,
			UNINTERRUPT,OBJ_FLAG,OBJECT,PHOTOMETRY_FLAG,VMAGNITUDE,
			EST_CNT_RATE,FORDER_CNT_RATE,ROLL,ROLL_TOLERANCE,TSTART,TSTOP,
			PHASE_CONSTRAINT_FLAG,PHASE_EPOCH,PHASE_PERIOD, PHASE_START,
			PHASE_START_MARGIN,PHASE_END,PHASE_END_MARGIN,PRE_MIN_LEAD,
			PRE_MAX_LEAD,PRE_ID,HRC_SI_MODE,HRC_TIMING_MODE,HRC_ZERO_BLOCK,
			TOOID,TARGNAME,DESCRIPTION,SI_MODE,ACA_MODE,EXTENDED_SRC,SEG_MAX_NUM,
			Y_AMP,Y_FREQ,Y_PHASE, Z_AMP,Z_FREQ,Z_PHASE,HRC_CHOP_FRACTION,
			HRC_CHOP_DUTY_CYCLE,HRC_CHOP_DUTY_NO,TIMING_MODE, ROLL_OBSR, 
			MULTITELESCOPE, OBSERVATORIES, MULTITELESCOPE_INTERVAL, ROLL_CONSTRAINT, 
			WINDOW_CONSTRAINT, ROLL_ORDR, TIME_ORDR, ROLL_180,
			CONSTR_IN_REMARKS,ROLL_FLAG,WINDOW_FLAG, MONITOR_FLAG,
		);

#-------------------------------
#------ save the original values
#-------------------------------

	foreach $ent (@namearray){	
		$lname    = lc ($ent);
		$wname    = 'orig_'."$lname";		# for the original value, all variable name start from "orig_"
		${$wname} = ${$lname};
	}

#-------------------------------------
#------------------	special cases
#-------------------------------------

	$orig_ra  = $dra;
	$orig_dec = $ddec;

#----------------------------------------------
#------- special treatment for time constraint
#----------------------------------------------

	$ptime_ordr = $time_ordr + 1;
	for($j = $ptime_ordr; $j < 30; $j++){
		$start_date[$j]  = 'NULL';
		$start_month[$j] = 'NULL';
		$start_year[$j]  = 'NULL';
		$end_date[$j]    = 'NULL';
		$end_month[$j]   = 'NULL';
		$end_year[$j]    = 'NULL';
#		$tstart[$j]      = 'NULL';
#		$tstop[$j]       = 'NULL';
		$tstart[$j]      = '';
		$tstop[$j]       = '';
		$window_constraint[$j] = 'NULL';
	}
	for($j = 1; $j < 30; $j++){
		$orig_start_date[$j]  = $start_date[$j];
		$orig_start_month[$j] = $start_month[$j];
		$orig_start_year[$j]  = $start_year[$j];
		$orig_end_date[$j]    = $end_date[$j];
		$orig_end_month[$j]   = $end_month[$j];
		$orig_end_year[$j]    = $end_year[$j];
		$orig_tstart[$j]      = $tstart[$j];
		$orig_tstop[$j]       = $tstop[$j];
		$orig_window_constraint[$j] = $window_constraint[$j];
	}

	$time_ordr_add = 0;                      # added 09/10/12

#----------------------------------------------
#------ special treatment for roll requirements
#----------------------------------------------

	for($j = 1; $j <= $roll_ordr; $j++){		# make sure that all entries have some values for each order
		if($roll_constraint[$j] eq ''){ $roll_constraint[$j] = 'NULL'}
		if($roll_180[$j] eq ''){$roll_180[$j] = 'NULL'}
	}

	$proll_ordr = $roll_ordr + 1;

	for($j = $proll_ordr; $j < 30; $j++){		# set default values up to order < 30, assuming that
		$roll_constraint[$j] = 'NULL';		# we do not get the order larger than 29
		$roll_180[$j]        = 'NULL';
		$roll[$j]            = '';
		$roll_tolerance[$j]  = '';
	}

	for($j = 1; $j < 30; $j++){			# save them as the original values
		$orig_roll_constraint[$j] = $roll_constraint[$j];
		$orig_roll_180[$j]        = $roll_180[$j];
		$orig_roll[$j]            = $roll[$j];
		$orig_roll_tolerance[$j]  = $roll_tolerance[$j];
	}

	$roll_ordr_add = 0;                      # added 09/10/12

#--------------------------------------------
#----- special treatment for acis window data
#--------------------------------------------

	for($j = 0; $j < $aciswin_no; $j++){
		if($chip[$j] eq '') {$chip[$j] = 'NULL'}
		if($chip[$j] eq 'N'){$chip[$j] = 'NULL'}
		if($include_flag[$j] eq '') {
#			if($spwindow_flag =~ /Y/i){
			if($spwindow =~ /Y/i){
				$dinclude_flag[$j] = 'EXCLUDE'; 
				$include_flag[$j]  = 'E';
			}else{
				$dinclude_flag[$j] = 'INCLUDE'; 
				$include_flag[$j]  = 'I';
			}
		}
		if($include_flag[$j] eq 'I'){$dinclude_flag[$j] = 'INCLUDE'}
		if($include_flag[$j] eq 'E'){$dinclude_flag[$j] = 'EXCLUDE'}
	}

	for($j = $aciswin_no; $j < 30; $j++){
		$aciswin_id[$i]    = '';
		$ordr[$j]          = '';
		$chip[$j]          = 'NULL';
		$include_flag[$j]  = 'E';
		$dinclude_flag[$j] = 'EXCLUDE';
	}

	for($j = 0; $j < 30; $j++){
		$orig_aciswin_id[$j]      = $aciswin_id[$j];
		$orig_ordr[$j]            = $ordr[$j];
		$orig_chip[$j]            = $chip[$j];
		$orig_include_flag[$j]    = $include_flag[$j];
                $orig_start_row[$j]       = $start_row[$j];
                $orig_start_column[$j]    = $start_column[$j];
                $orig_width[$j]           = $width[$j];
                $orig_height[$j]          = $height[$j];
                $orig_lower_threshold[$j] = $lower_threshold[$j];
                $orig_pha_range[$j]       = $pha_range[$j];
                $orig_sample[$j]          = $sample[$j];

	}
#--------------------------------------------
#--- check planned roll
#--------------------------------------------

	find_planned_roll();

	$scheduled_roll  = ${planned_roll.$obsid}{planned_roll}[0];
	$scheduled_range = ${planned_roll.$obsid}{planned_range}[0];

}


########################################################################################
### data_close_page: display data for closed observation                             ###
########################################################################################

sub data_close_page{

#------------------------------------------------------------------------------------------
#----- three cases use this sub.
#-----          1. the observation is close,
#-----          2. the observation is previously approved, and if the user needs to
#-----             modify it, s/he needs to remove it from the approved list.
#-----          3. a special user does not have an access right to the ocat data
#------------------------------------------------------------------------------------------

	if($no_access == 0){
		if($prev_app == 0){
			print '<h1>Obscat Data Page---  <font color=red>This observation is closed</font></h1>';
#                }else{
#                        print '<h1>Obscat Data Page--- </h1>';
#                        print '<h3> <font color=red>This observation has been approved. ';
#                        print 'If you need to modify paramters,';
#                        print ' please remove this from the approved list <br />';
#                        print ' (see at the bottom of the page)</font></H3>';
                }
	}else{
		print '<h1>Obscat Data Page---  <font color=red>You cannot modify this data. </font><font size=-0.8></h1>';
		if($lts_more30 eq 'closed'){
			print '<h2>The observation was done and closed</h2>';
		}elsif ($gto_ok eq 'yes' && $lts_more30 eq 'no'){
			print '<h2>The observation is less than 30 days away</h2>';
#		}elsif($gto_ok eq 'yes' && $prev_app > 0){
#                        print '<h2>This observation has been approved. ';
#                        print 'If you need to modify paramters,';
#                        print ' please contact CXC.</h2>';
		}elsif($cxc_usr_chk eq 'no' && $gto_ok eq 'no'){
			print '<h2>This is not your observation<br />';
                        print '</font></h1>';
                        print '<h2>';
                        print 'If you want to change the user name, push submit:  ';
                        print hidden(-name=>'chg_user_ind', -override=>'', -value=>'yes');
                        print hidden(-name=>'Check', -override=>'', -value=>'');
                        print '<input type="submit" name="Check" value="Submit">';
                        print '</h2>';
		}else{
			print '<h2>This is not your observation<br />';
                        print '</font></h1>';
                        print '<h2>';
                        print 'If you want to change the user name, push submit:  ';
                        print hidden(-name=>'chg_user_ind', -override=>'', -value=>'yes');
                        print hidden(-name=>'Check', -override=>'', -value=>'');
                        print '<input type="submit" name="Check" value="Submit">';
                        print '</h2>';
		}
	}


	if($status !~ /scheduled/i && $status !~ /unobserved/i){
		$cap_status = uc($status);
		print "<h2>This observation was <font color='red'>$cap_status</font>.</h2> ";
	}

	print 'A brief description of the listed parameters is given ';

	if($usint_on =~ /no/){
        	print a({-href=>"$obs_ss_http/user_help.html",-target=>'_blank'},"here");
	}elsif($usint_on =~ /yes/){
        	print a({-href=>"$usint_http/user_help.html" ,-target=>'_blank'},"here");
	}

	@ntest = split(//, $obsid);
	$tcnt  = 0;
	foreach(@ntest){
		$tcnt++;
	}
	if($tcnt < 5){
		$add_zero = '';
		for($mt = $tcnt; $mt < 5; $mt++){
			$add_zero = "$add_zero".'0';
		}
		$tobsid = "$add_zero"."$obsid";
	}else{
		$tobsid = $obsid;
	}

       	$dss_http  = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.'."$tobsid".'.dss.gif';
       	$ros_http  = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.'."$tobsid".'.pspc.gif';
       	$rass_http = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.'."$tobsid".'.rass.gif';

	print '<p align=right>';
        print "<a href = $dss_http  target='blank'><img align=middle src=\"$mp_http/targets/webgifs/dss.gif\"></a>";
        print "<a href = $ros_http  target='blank'><img align=middle src=\"$mp_http/targets/webgifs/ros.gif\"></a>";
        print "<a href = $rass_http target='blank'><img align=middle src=\"$mp_http/targets/webgifs/rass.gif\"></a>";
	print '</p>';

	print '<h2>General Parameters</h2>';

#------------------------------------------------>
#----- General Parameter dispaly starts here----->
#------------------------------------------------>

	print '<table cellspacing="0" cellpadding="5">';
	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(seq_nbr);return false;">Sequence Number</a>:';
	print "</th><td>$seq_nbr</td>";
	print '<th><a href="#" onClick="WindowOpen(status);return false;">Status</a>:';
	print "</th><td>$status</td>";
	print '<th><a href="#" onClick="WindowOpen(obsid);return false;">ObsID #</a>:';
	print "</th><td>$obsid</td>";
	print '<input type="hidden" name="OBSID" value="$obsid">';
	print '<th><a href="#" onClick="WindowOpen(proposal_number);return false;">Proposal Number</a>:</th>';
	print "<td>$proposal_number</td>";
	print '</tr></table>';

	print '<table cellspacing="0" cellpadding="5">';
	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(proposal_title);return false;">Proposal Title</a>:</th>';
	print "<td>$proposal_title</td>";
	print '</tr>';
	print '</table>';
	
	print '<table cellspacing="0" cellpadding="5">';
	print '<tr>';
	print '<td></td>';
	print '<th><a href="#" onClick="WindowOpen(obs_ao_str);return false;">Obs AO Status</a>:';
	print "</th><td>$obs_ao_str</td>";
	print '</tr></table>';

	print '<table cellspacing="3" cellpadding="10">';
	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(targname);return false;">Target Name</a>:';
	print "</th><td>$targname</td>";
	print '<th><a href="#" onClick="WindowOpen(si_mode);return false;">SI Mode</a>:</th>';
	print "<td align=\"LEFT\">$si_mode</td>";
#	print '<td align="LEFT"><input type="text" name="SI_MODE" value="$si_mode" size="12"></td>';
	print '<th><a href="#" onClick="WindowOpen(aca_mode);return false;">ACA Mode</a>:</th>';
	print "<td align=\"LEFT\">$aca_mode</td>";
	print '</tr></table>';

	print '<table cellspacing="3" cellpadding="10">';
	print '<tr><td></td>';

	print '<th><a href="#" onClick="WindowOpen(instrument);return false;">Instrument</a>:</th><td>',"$instrument";
	
	print '</td><th><a href="#" onClick="WindowOpen(grating);return false;">Grating</a>:</th><td>',"$grating";
	
	print '</td><th><a href="#" onClick="WindowOpen(type);return false;">Type</a>:</th><td>',"$type";
	
	print '</td></tr></table>';
	
	print '<table cellspacing="15" cellpadding="5">';
	print '<tr>';
	print '<th><a href="#" onClick="WindowOpen(PI_name);return false;">PI Name</a>:';
	print "</th><td>$PI_name</td>";
	print '<th><a href="#" onClick="WindowOpen(coi_contact);return false;">Observer</a>:';
	print "</th><td> $Observer</td></tr>";
	print '<th><a href="#" onClick="WindowOpen(approved_exposure_time);return false;">Exposure Time</a>:</th>';
	print "<td align=\"LEFT\">$approved_exposure_time ks</td>";
	print '<th><a href="#" onClick="WindowOpen(rem_exp_time);return false;">Remaining Exposure Time</a>:</th>';
	print "<td>$rem_exp_time ks</td>";
	print '</tr></table>';
	
	print '<table cellspacing="3" cellpadding="8">';

	print '<tr><th><a href="#" onClick="WindowOpen(joint);return false;">Joint Proposal</a>:</th>';
	print "<td>$proposal_joint</td></tr>";
	print '<tr><td></td><th><a href="#" onClick="WindowOpen(prop_hst);return false;">HST Approved Time</a>:</th>';
	print "<td>$proposal_hst</td>";
	print '<th><a href="#" onClick="WindowOpen(prop_noao);return false;">NOAO Approved Time</a>:</th>';
	print "<td>$proposal_noao</td>";
	print '</tr><tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(prop_xmm);return false;">XMM Approved Time</a>:';
	print "</th><td>$proposal_xmm</td>";
	print '<th><a href="#" onClick="WindowOpen(prop_rxte);return false;">RXTE Approved Time</a>:';
	print "</th><td>$rxte_approved_time</td>";
	print '</tr><tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(prop_vla);return false;">VLA Approved Time</a>:</th>';
	print "<td>$vla_approved_time</td>";
	print '<th><a href="#" onClick="WindowOpen(prop_vlba);return false;">VLBA Approved Time</a>:</th>';
	print "<td>$vlba_approved_time</td>";
	print '</tr></table>';
	
	
	print '<TABLE CELLSPACING="8" CELLPADDING="10">';
	print '<tr>';
	print '<th><a href="#" onClick="WindowOpen(soe_st_sched_date);return false;">Schedule Date</a>:</th>';
	print "<td>$soe_st_sched_date</td>";
	print '<th><a href="#" onClick="WindowOpen(lts_lt_plan);return false;">LTS Date</a>:';
	print "</th><td>$lts_lt_plan</td>";
	print '</tr></table>';
	
#-----------------------------------------
#-------- Convert $ra from decimal to hms
#-----------------------------------------

	$ra = $dra;
       	$hh = int($ra/15);
       	$mm = 60 * ($ra / 15 - $hh);
       	$ss = 60 * ($mm - int($mm));

       	$tra = sprintf("%02d:%02d:%06.4f", $hh, $mm, $ss);

#-----------------------------------------
#-------- Convert $dec from decimal to dms
#-----------------------------------------

	@dtemp = split(/:/, $dec);
	$dec = $ddec;
       	if ($dec < 0) { 			# set sign
               	$sign = "-";
             	$tdec = -1*$dec;
       	}
       	else {
		$sign = "+";
	 	$tdec = $dec
	}
	
       	$dd = int($tdec);
       	$mm = 60 * ($tdec - $dd);
       	$ss = 60 * ($mm - int($mm));
       	$secrollover = sprintf("%02f", $ss);
       	if ($secrollover == 60) {
               	$ss = abs($ss - 60);
               	$mm = ($mm +1 );
       	}
       	if ($mm == 60) {
               	$mm = ($mm - 60);
         	$hh = ($dd + 1);
       	}
  	$tdec = sprintf("%.1s%02d:%02d:%06.4f", $sign, $dd, $mm, $ss);
	$target_http = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.rollvis.gif';
	if($status =~ /^OBSERVED/i || $status =~ /ARCHIVED/i){
	}else{
		$roll_obsr ='';
	}

	print '<table cellspacing="8" cellpadding="5">';
	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(ra);return false;">RA (HMS)</a>:</th>';
	print "<td align=\"LEFT\">$tra</td>";
	print '<th><a href="#" onClick="WindowOpen(dec);return false;">Dec (DMS)</a>:</th>';
	print "<td align=\"LEFT\">$tdec</td>";
	
#
#--- planned roll has a range
#
        print '<th><a href="#" onClick="WindowOpen(planned_roll);return false;">Planned Roll</a>:';

	if($scheduled_roll eq '' && $scheduled_range eq ""){
            print '<td>NA</td>';
        }elsif($scheduled_roll <= $scheduled_range){
            print '<td>',"$scheduled_roll",' -- ', "$scheduled_range",'</td>';
        }else{
            print '<td>',"$scheduled_range",' -- ', "$scheduled_roll",'</td>';
        }

	print "</th><td>$scheduled_roll";

        print '</td></tr>';

	print '<tr><td></td>';
	print'<th><a href="#" onClick="WindowOpen(dra);return false;">RA</a>:';
	print "</th><td>$dra</td>";
	print '<th><a href="#" onClick="WindowOpen(ddec);return false;">Dec</a>:';
	print "</th><td>$ddec</td>";
	print '<th><a href="#" onClick="WindowOpen(roll_obsr);return false;">Roll Observed</a>:';
	print "</th><td>$roll_obsr</td>";
	print '</tr></table>';
	
	print '<table cellspacing="3" cellpadding="5">';
	print '<tr>';
	print '<th><a href="#" onClick="WindowOpen(y_det_offset);return false;">Offset: Y</a>:</th>';
	print "<td align=\"LEFT\">$y_det_offset</td><td></td>";
	print '<th><a href="#" onClick="WindowOpen(z_det_offset);return false;">Z</a>:</th>';
	print "<td align=\"LEFT\">$z_det_offset arcmin</td>";
	print '</tr><tr>';
	print '<th><a href="#" onClick="WindowOpen(trans_offset);return false;">Z-Sim</a>:</th>';
	print "<td align=\"LEFT\">$trans_offset mm<td>";
	print '<th><a href="#" onClick="WindowOpen(focus_offset);return false;">Sim-Focus</a>:</th>';
	print "<td align=\"LEFT\">$focus_offset mm</td>";
	print '<tr>';

	if($sp_user eq 'yes'){
		print '<th><a href="#" onClick="WindowOpen(defocus);return false;">Focus</a>:</th>';
		print '<td align="LEFT">$defocus</td>';
		print '<td></td>';
	}

	print "<th><a href=\"#\" onClick=\"WindowOpen(raster_scan);return false;\">Raster Scan</a>:</th>";
	print "<td align=\"LEFT\">$raster_scan</td>";
#	print "<td align=\"LEFT\"><input type=\"text\" name=\"RASTER_SCAN\" value=\"$raster_scan\" size=\"12\"></td>";
	print '</tr></table>';

	print '<table cellspacing="3" cellpadding="5">';
	print '<tr><th><a href="#" onClick="WindowOpen(uninterrupt);return false;">Uninterrupted Obs</a>:</th><td>';
	print "$duninterrupt";
	print '</td><td>&#160';
	print '</td><th><a href="#"  onClick="WindowOpen(extended_src);return false;">Extended SRC</a>:</th><td>';
	print "$dextended_src";
	print '<td></td></tr>';


	print '<tr><th><a href="#" onClick="WindowOpen(obj_flag);return false;">Solar System Object</a>:</th><td>';
	print "$obj_flag";
	print '</td><td>';
	print '</td><th><a href="#" onClick="WindowOpen(object);return false;">Object</a>:</th><td>';
	print "$object";
	print '</tr><tr>';
	
	print '</td><th><a href="#" onClick="WindowOpen(photometry_flag);return false;">Photometry</a>:</th><td>';
	print "$dphotometry_flag";
	print '</td>';

	print '<td></td>';
	print '<th><a href="#" onClick="WindowOpen(vmagnitude);return false;">V Mag</a>:</th>';
	print "<td align=\"LEFT\">$vmagnitude</td>";
	
	print "<tr>";
	print "<th><a href=\"#\" onClick=\"WindowOpen(est_cnt_rate);return false;\">Count Rate</a>:</th>";
	print "<td align=\"LEFT\">$est_cnt_rate</td>";
	print '<td></td>';
	print "<th><a href=\"#\" onClick=\"WindowOpen(forder_cnt_rate);return false;\">1st Order Rate</a>:</th>";
	print "<td align=\"LEFT\">$forder_cnt_rate</td>";
	print '</tr></table>';
	print '<hr />';

	print '<h2>Dither</h2>';

	print '<table cellspacing="3" cellpadding="5">';
	print '<tr><th><a href="#" onClick="WindowOpen(dither_flag);return false;">Dither</a>:</th><td>';
	print "$ddither_flag";
	print '</td><td></td><td></td><td></td><td></td></tr>';

	print '<tr><td></td><th><a href="#" onClick="WindowOpen(y_amp);return false;">y_amp</a> (in arcsec):</th>';
	print '<td align="LEFT">',"$y_amp_asec",'</td>';

	print '<th><a href="#" onClick="WindowOpen(y_freq);return false;">y_freq</a> (in arcsec/sec):</th>';
	print '<td align="LEFT">',"$y_freq_asec",'</td>';

	print '<th><a href="#" onClick="WindowOpen(y_phase);return false;">y_phase</a>:</th>';
	print '<td align="LEFT">',"$y_phase",'</td>';
	print '</tr>';
#---
        print '<tr><td></td><th>y_amp(in degrees):</th>';
        print '<td align="LEFT">',"$y_amp",'</td>';

        print '<th>y_freq(in degrees/sec)</th>';
        print '<td align="LEFT">',"$y_freq",'</td>';

        print '<th></th>';
        print '<td align="LEFT"></td>';
        print '</tr>';
#----

	print '<tr><td></td><th><a href="#" onClick="WindowOpen(z_amp);return false;">z_amp</a> (in arcsec):</th>';
	print '<td align="LEFT">',"$z_amp_asec",'</td>';

	print '<th><a href="#" onClick="WindowOpen(z_freq);return false;">z_freq</a> (arcsec/sec):</th>';
	print '<td align="LEFT">',"$z_freq_asec",'</td>';

	print '<th><a href="#" onClick="WindowOpen(z_phase);return false;">z_phase</a>:</th>';
	print '<td align="LEFT">',"$z_phase",'</td>';
	print '</tr>';
#---
        print '<tr><td></td><th>z_amp(in degrees):</th>';
        print '<td align="LEFT">',"$z_amp",'</td>';

        print '<th>z_freq(in degrees/sec)</th>';
        print '<td align="LEFT">',"$z_freq",'</td>';

        print '<th></th>';
        print '<td align="LEFT"></td>';
        print '</tr>';
#----

	print '</table>';
	print '<hr />';


#-------------------------------------
#----- time constraint case start here
#-------------------------------------

	print '<h2>Time Constraints</h2>';

	print '<table><tr><th>';
	print '<a href="#" onClick="WindowOpen(window_flag);return false;">Time Constraint? </th><td>';
	print "$dwindow_flag";
	print '</td></tr></table>';

	print '<table cellspacing="0" cellpadding="5">';
	print '<tr><th><a href="#" onClick="WindowOpen(time_ordr);return false;">Rank</a></th>
		<th><a href="#" onClick="WindowOpen(window_constraint);return false;">Window Constraint</a><th>
		<th>Month</th><th>Date</th><th>Year</th><th>Time (24hr system)</th></tr>';


	for($k = 1; $k <= $time_ordr; $k++){
		if($start_month[$k] =~/\d/){
			if($start_month[$k]    == 1) {$wstart_month = 'Jan'}
			elsif($start_month[$k] == 2) {$wstart_month ='Feb'}
			elsif($start_month[$k] == 3) {$wstart_month ='Mar'}
			elsif($start_month[$k] == 4) {$wstart_month ='Apr'}
			elsif($start_month[$k] == 5) {$wstart_month ='May'}
			elsif($start_month[$k] == 6) {$wstart_month ='Jun'}
			elsif($start_month[$k] == 7) {$wstart_month ='Jul'}
			elsif($start_month[$k] == 8) {$wstart_month ='Aug'}
			elsif($start_month[$k] == 9) {$wstart_month ='Sep'}
			elsif($start_month[$k] == 10){$wstart_month ='Oct'}
			elsif($start_month[$k] == 11){$wstart_month ='Nov'}
			elsif($start_month[$k] == 12){$wstart_month ='Dec'}
			else{$wstart_month = 'NULL'}
			$start_month[$k]   = $wstart_month;
		}
	
		if($end_month[$k] =~ /\d/){
			if($end_month[$k]    == 1) {$wend_month = 'Jan'}
			elsif($end_month[$k] == 2) {$wend_month ='Feb'}
			elsif($end_month[$k] == 3) {$wend_month ='Mar'}
			elsif($end_month[$k] == 4) {$wend_month ='Apr'}
			elsif($end_month[$k] == 5) {$wend_month ='May'}
			elsif($end_month[$k] == 6) {$wend_month ='Jun'}
			elsif($end_month[$k] == 7) {$wend_month ='Jul'}
			elsif($end_month[$k] == 8) {$wend_month ='Aug'}
			elsif($end_month[$k] == 9) {$wend_month ='Sep'}
			elsif($end_month[$k] == 10){$wend_month ='Oct'}
			elsif($end_month[$k] == 11){$wend_month ='Nov'}
			elsif($end_month[$k] == 12){$wend_month ='Dec'}
			else{$wend_month = 'NULL'}
			$end_month[$k]   = $wend_month;
		}

		print '<tr><td align=center><b>';
		print "$k";
		print '</b></td><td>';

		print "$dwindow_constraint[$k]";
		print '</td><th><a href="#" onClick="WindowOpen(tstart);return false;">Start</a></th><td align=center>';

		print "$start_month[$k]";
		print '</td><td align=center>';
		
		print "$start_date[$k]";
		print '</td><td align=center>';

		print "$start_year[$k]";
		print '</td><td align=center>';

		print "$start_time[$k]";

#		print '</td><td>',"$tstart[$k]";
		print '</td></tr><tr><td></td><td></td>';

		print '</td><th><a href="#" onClick="WindowOpen(tstop);return false;">End</a></th><td align=center>';

		print "$end_month[$k]";
		print '</td><td align=center>';

		print "$end_date[$k]";
		print '</td><td align=center>';

		print "$end_year[$k]";
		print '</td><td align=center>';

		print "$end_time[$k]";
#		print '</td><td>',"$tstop[$k]";
		print '</td></tr>';
	}
	print '</table>';
	
	print '<hr />';

#--------------------------------------
#---- Roll Constraint Case starts here
#--------------------------------------

#	print '<h2>Roll Constraints</h2>';
	print '<br />';
	print '<font size=+2><b>Roll Constraints </b></font>';

	print "<br /><br />";

	print '<table><tr><th><a href="#" onClick="WindowOpen(roll_flag);return false;">Roll Constraint? </th><td>';
	print "$droll_flag";
	print '</td></tr></table>';

	print '<table cellspacing="0" cellpadding="5">';
	print '<tr><th><a href="#" onClick="WindowOpen(roll_ordr);return false;">Rank</a></th>
		<th><a href="#" onClick="WindowOpen(roll_constraint);return false;">Type of Constraint</a></th>
		<th><a href="#" onClick="WindowOpen(roll_180);return false;">Roll180?</a></th>
		<th><a href="#" onClick="WindowOpen(roll);return false;">Roll</a></th>
		<th><a href="#" onClick="WindowOpen(roll_tolerance);return false;">Roll Tolerance</a></th></tr>';

	for($k = 1; $k <= $roll_ordr; $k++){
		print '<tr><td align=center><b>';
		print "$k";	
		print '</b></td><td>';
		$troll_constraint = 'ROLL_CONSTRAINT'."$k";
		print "$droll_constraint[$k]";

		print '</td><td align=center>';
		$troll_180 = 'ROLL_180'."$k";
		print "$droll_180[$k]";
		print '</td><td align=center>';
		$troll = 'ROLL'."$k";
		print "$roll[$k]";
		print '</td><td align=center>';
		$troll_tolerance = 'ROLL_TOLERANCE'."$k";
		print "$roll_tolerance[$k]";
		print '</td></tr>';
	}
	print '</table>';

#---------------------------------------
#----- Other Constraint Case starts here
#---------------------------------------

	print '<hr />';
	print '<h2>Other Constraints</h2>';
	print '<table cellspacing="0" cellpadding="5">';
	print '<tr>';
	
	print '<th><a href="#" onClick="WindowOpen(constr_in_remarks);return false;">Constraints in Remarks?</a>:</th><td>';
	print "$dconstr_in_remarks";
	print ' </td></tr>';
	print '</table>';

	print '<table cellspacing="0" cellpadding="5">';
	print '<tr>';
	print '<th><a href="#" onClick="WindowOpen(phase_constraint_flag);return false;">Phase Constraint</a>:</th>
	<td align="LEFT">';
	
	print "$dphase_constraint_flag";

	print '</td></tr></table>';
	
	print '<table cellspacing="10" cellpadding="5">';
	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(phase_epoch);return false;">Phase Epoch</a>:</th>';
	print "<td align=\"LEFT\">$phase_epoch</td>";
	print '<th><a href="#" onClick="WindowOpen(phase_period);return false;">Phase Period</a>:</th>';
	print "<td align=\"LEFT\">$phase_period</td>";
	print '<td></td><td></td></tr>';
	
	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(phase_start);return false;">Phase Start</a>:</th>';
	print "<td align=\"LEFT\">$phase_start</td>";
	print '<th><a href="#" onClick="WindowOpen(phase_start_margin);return false;">Phase Start Margin</a>:</th>';
	print "<td align=\"LEFT\">$phase_start_margin</td>";
	print '</tr><tr>';
	print '<td></td>';
	print '<th><a href="#" onClick="WindowOpen(phase_end);return false;">Phase End</a>:</th>';
	print "<td align=\"LEFT\">$phase_end</td>";
	print '<th><a href="#" onClick="WindowOpen(phase_end_margin);return false;">Phase End Margin</a>:</th>';
	print "<td align=\"LEFT\">$phase_end_margin</td>";
	print '</tr></table>';
	
        if($monitor_flag =~ /Y/i){
                %seen = ();
                @uniq = ();
                foreach $monitor_elem (@monitor_series) {
			$schk = 0;
			OUTER3:
			foreach $echk (@schdulable_list){
				if($monitor_elem =~ /$echk/){
					$schk++;
					last OUTER3;
				}
			}

			if($schk > 0){
                        	push(@uniq, "<a href=\"\.\/ocatdata2html.cgi\?$monitor_elem.$pass.$submitter\">$monitor_elem<\/a> ") unless $seen{$monitor_elem}++;
			}
                }
               @monitor_series_list  = sort @uniq;
        }

	print '<table cellspacing="0" cellpadding="2">';
	print '<tr>';

	print '<th><a href="#" onClick="WindowOpen(group_id);return false;">Group ID</a>:</th>';
	print '<td>';
	
	if($group_id){
		print "$group_id";
	}else{
		print '  No Group ID  ';
	}
	print '</td>';

	print '<th><a href="#" onClick="WindowOpen(monitor_flag);return false;">Monitoring Observation:  </th>';
	print "<td>  $monitor_flag   </td>";
	print '</tr></table>';

        if($group_id){
                print "<br />Observations in the Group: @group<br />";
        }elsif($monitor_flag =~ /Y/i){
                print "<br />Observations in the Monitoring: @monitor_series_list<br />";
        }else{
                print "<br />";
        }
	
	print '<table cellspacing="8" cellpadding="5">';

	print '<th><a href="#" onClick="WindowOpen(pre_id);return false;">Follows ObsID#</a>:</th>';
	print '<td align="LEFT">';
	print "$pre_id</td>";

	print '<th><a href="#" onClick="WindowOpen(pre_min_lead);return false;">Min Int<br />(pre_min_lead)</a>:</th>';
	print '<td align="LEFT">';
	print "$pre_min_lead</td>";

	print '<th><a href="#" onClick="WindowOpen(pre_max_lead);return false;">Max Int<br />(pre_max_lead)</a>:</th>';
	print '<td align="LEFT">';
	print "$pre_max_lead</td>";
	print '</tr></table>';
	
	print '<table cellspacing=6 cellpadding=5>';
	print '<tr>';
	print '<th><a href="#" onClick="WindowOpen(multitelescope);return false;">Coordinated Observation</a>:</th><td>';
	print "$dmultitelescope";
	print '</td>';
	print '<td></td>';
	print '<th><a href="#" onClick="WindowOpen(observatories);return false;">Observatories</a>:</th>';
	print "<td align=\"LEFT\">$observatories</td>";
	print '</tr>';

	print '<tr>';
	print '<th><a href="#" onClick="WindowOpen(multitelescope_interval);return false;">Max Coordination Offset</a>:</th>';
	print "<td align=\"LEFT\">$multitelescope_interval</td>";
	print '</tr> </table>';

	print '<hr />';


#---------------------
#----- HRC Parameters
#---------------------

	if($sp_user =~ /no/ && $instrument =~ /ACIS/i){
	}else{
		print '<h2>HRC Parameters</h2>';
		print '<table cellspacing="0" cellpadding="5">';
		print '<tr><td></td>';
	
		print '<th><a href="#" onClick="WindowOpen(hrc_timing_mode);return false;">HRC Timing Mode</a>:</th><td>';
		print "$dhrc_timing_mode";
		print '</td>';
		
		print '<th><a href="#" onClick="WindowOpen(hrc_zero_block);return false;">Zero Block</a>:</th><td>';
		print "$dhrc_zero_block";
		print '</td><td>';
		print '<th><a href="#" onClick="WindowOpen(hrc_si_mode);return false;">SI Mode</a>:</th>
			<td align="LEFT">';
		print "$hrc_si_mode";
		print '</td></tr>';
		print '</table>';
	
		print '<hr />';
	}

#---------------------
#----- ACIS Parameters
#---------------------
	
	if($sp_user =~ /no/ && $instrument =~ /HRC/i){
	}else{
		print '<h2>ACIS Parameters</h2>';
		print '<table cellspacing="0" cellpadding="5">';
		print '<tr>';
		
		print '<th><a href="#" onClick="WindowOpen(exp_mode);return false;">ACIS Exposure Mode</a>:</th><td>';
		print "$exp_mode";
		
		print '</td><th><a href="#" onClick="WindowOpen(bep_pack);return false;">Event TM Format</a>:</th><td>';
		print "$bep_pack";
		print '</td>';

		print '<th><a href="#" onClick="WindowOpen(frame_time);return false;">Frame Time</a>:</th>';
		print "<td align=\"LEFT\">$frame_time</td></tr>";

		print '<tr>';
		print '<td></td><td></td><td></td><td></td>
			<th><a href="#" onClick="WindowOpen(most_efficient);return false;">Most Efficient</a>:</th><td>';

		print "$dmost_efficient";
		print '</td>';
		print '</tr></table>';
	
		if($sp_user eq 'yes'){
			print '<table cellspacing="0" cellpadding="5">';
			print '<tr><td></td>';

			print '<th><a href="#" onClick="WindowOpen(fep);return false;">FEP</a>:</th><td>';
			print "$fep";
			print '</td>';
			print '</td><td></td><td></td>';
			print '<th><a href="#" onClick="WindowOpen(dropped_chip_count);return false;">Dropped Chip Count</a>:</th><td>';
			print "$dropped_chip_count";
			print '</td>';
			print '</tr></table>';
		}
		print '<table cellspacing="4" cellpadding="6" border ="1">';
		print '<tr><td></td><td></td><td></td><td></td>';
	

		print '<th><a href="#" onClick="WindowOpen(ccdi0_on);return false;">I0</a>:</th> <td>',"$dccdi0_on",'</td>';
		print '<th><a href="#" onClick="WindowOpen(ccdi1_on);return false;">I1</a>:</th> <td>',"$dccdi1_on",'</td>';
	
		print '<td></td><td></td><td></td><td></td>';
		print '<tr><td></td><td></td><td></td><td></td>';
	
		print '<th><a href="#" onClick="WindowOpen(ccdi2_on);return false;">I2</a>:</th> <td>',"$dccdi2_on",'</td>';
		print '<th><a href="#" onClick="WindowOpen(ccdi3_on);return false;">I3</a>:</th> <td>',"$dccdi3_on",'</td>';
	
		print '<td></td><td></td><td></td><td></td></tr>';
	
		print '<tr>';
	
	
		print '<th><a href="#" onClick="WindowOpen(ccds0_on);return false;">S0</a>:</th> <td>',"$dccds0_on",'</td>';
		print '<th><a href="#" onClick="WindowOpen(ccds1_on);return false;">S1</a>:</th> <td>',"$dccds1_on",'</td>';
		print '<th><a href="#" onClick="WindowOpen(ccds2_on);return false;">S2</a>:</th> <td>',"$dccds2_on",'</td>';
		print '<th><a href="#" onClick="WindowOpen(ccds3_on);return false;">S3</a>:</th> <td>',"$dccds3_on",'</td>';
		print '<th><a href="#" onClick="WindowOpen(ccds4_on);return false;">S4</a>:</th> <td>',"$dccds4_on",'</td>';
		print '<th><a href="#" onClick="WindowOpen(ccds5_on);return false;">S5</a>:</th> <td>',"$dccds5_on",'</td>';
		
		print '</tr></table><p>';
	
		print '<table cellspacing="0" cellpadding="5">';
		print '<tr>';
		print '<Th><a href="#" onClick="WindowOpen(subarray);return false;">Use Subarray</a>:</Th>';
		print '<td>';
		print "$dsubarray";

		print '</td><th colspan=4>&#160</th></tr><tr>';
		
		print '<th><a href="#" onClick="WindowOpen(subarray_start_row);return false;">Start</a>:</th>
			<td align="LEFT">',"$subarray_start_row",'</td>';
		
		print '<th><a href="#" onClick="WindowOpen(subarray_row_count);return false;">Rows</a>:</th>
			<td align="LEFT">',"$subarray_row_count",'</td>';
		
#		print '<th><a href="#" onClick="WindowOpen(subarray_frame_time);return false;">Frame Time</a>:</th>
#			<td align="LEFT">',"$subarray_frame_time",'</td>';
	
		print '</td></tr>';
		print '<tr>';

		print '<th><a href="#" onClick="WindowOpen(duty_cycle);return false;">Duty Cycle</a>:</th><td>';
		print "$dduty_cycle";
		print '</td>';
		print '</tr><tr>';

		print '<th><a href="#" onClick="WindowOpen(secondary_exp_count);return false;">Number</a>:</th>';
		print "<td align=\"LEFT\">$secondary_exp_count</td>";
		print '<th><a href="#" onClick="WindowOpen(primary_exp_time);return false;">Tprimary</a>:</th>';
		print "<td align=\"LEFT\">$primary_exp_time</td>";
#		print '<th><a href="#" onClick="WindowOpen(secondary_exp_time);return false;">Tsecondary</a>:</th>';
#		print "<td align=\"LEFT\">$secondary_exp_time</td>";
		print '</tr> <tr>';

		print '<th><a href="#" onClick="WindowOpen(onchip_sum);return false;">Onchip Summing</a>:</th><td>';
		print "$donchip_sum";
		print '</td>';

		print '<th><a href="#" onClick="WindowOpen(onchip_row_count);return false;">Rows</a>:</th>';
		print "<td align=\"LEFT\">$onchip_row_count</td>";
		print '<th><a href="#" onClick="WindowOpen(onchip_column_count);return false;">Columns</a>:</th>';
		print "<td align=\"LEFT\">$onchip_column_count</td>";
		print '</tr><tr>';
		print '<th><a href="#" onClick="WindowOpen(eventfilter);return false;">Energy Filter</a>:</th><td>';
		print "$deventfilter";
		print '</td>';

		print '<th><a href="#" onClick="WindowOpen(eventfilter_lower);return false;">Lowest Energy</a>:</th>';
		print "<td align=\"LEFT\">$eventfilter_lower</td>";
		print '<th><a href="#" onClick="WindowOpen(eventfilter_higher);return false;">Energy Range</a>:</th>';
		print "<td align=\"LEFT\">$eventfilter_higher</td>";
        	if($deventfilter =~ /YES/i){
            		$high_energy = $eventfilter_lower + $eventfilter_higher;
            		print "<td><b> = Highest Energy:</b> $high_energy</td>";
        	}
		print '</tr> ';

#
#--- added 03/28/11
#
		print '<tr>';
		print '<th><a href="#" onClick="WindowOpen(multiple_spectral_lines);return false;">Multiple Spectral Lines</a>:</th>';
		print "<td align=\"LEFT\">$multiple_spectral_lines</td>";
		print '<th><a href="#" onClick="WindowOpen(spectra_max_count);return false;">Spectra Max Count</a>:</th>';
		print "<td align=\"LEFT\">$spectra_max_count</td>";
		print '</tr>';

#		if($sp_user eq 'yes'){
#			print '<tr><th><a href="#" onClick="WindowOpen(bias_request);return false;">Bias</a>:</th><td>';
#			print "$bias_request";
#			print '</td><th><a href="#" onClick="WindowOpen(frequency);return false;">Bias Frequency</a>:</th><td>';
#			print "$frequency";
#			print '</td><th><a href="#" onClick="WindowOpen(bias_after);return false;">Bias After</a>:</th><td>';
#			print "$bias_after";
#	
#			print '</td></tr>';
#		}
		print '</table>';

#------------------------------------------------
#-------- Acis Window Constraint Case starts here
#------------------------------------------------

		print '<hr />';
		print '<h2> ACIS Window Constraints</h2>';
		print '<table><tr><th>';
		print '<a href="#" onClick="WindowOpen(spwindow);return false;">Window Filter</a>:';
		print '</th><td>';
		print "$dspwindow";
		print '</td></tr></table>';
		print '<br />';

		if($dswindow =~ /YES/i){
			print '<table cellspacing="0" cellpadding="3">';
			for($k = 0; $k < $aciswin_no; $k++){
#
#-----this line was removed:	<th><a href="#" onClick="WindowOpen(include_flag);return false;">Photon Inclusion</a></th>
#
				print '<tr><th><a href="#" onClick="WindowOpen(ordr);return false;">Rank</a></th>
					<th><a href="#" onClick="WindowOpen(chip);return false;">Chip</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_start_row);return false;">Start Row</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_start_column);return false;">Start Column</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_height);return false;">Height</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_width);return false;">Width</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_lower_threshold);return false;">Lowest Energy</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_pha_range);return false;">Energy Range</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_sample);return false;">Sample Rate</a></th>
					<th></th>
					</tr>';
				print '<tr><td align=center><b>';
				print "$ordr[$k]";
				print '</b></td><td align=center>';
	
				$taciswin_id      = 'ACISWIN_ID'."$k";
				$tordr            = 'ORDR'."$k";
				$tchip            = 'CHIP'."$k";
#				$tinclude_flag    = 'INCLUDE_FLAG'."$k";
				$tstart_row       = 'START_ROW'."$k";
				$tstart_column    = 'START_COLUMN'."$k";
				$theight          = 'HEIGHT'."$k";
				$twidth           = 'WIDTH'."$k";
				$tlower_threshold = 'LOWER_THRESHOLD'."$k";
				$tpha_range       = 'PHA_RANGE'."$k";
				$tsample          = 'SAMPLE'."$k";
		
				print "$chip[$k]";
				print "</td><td align=center>";
#				print "$dinclude_flag[$k]";
#				print "</td><td align=center>";
				print "$start_row[$k]";
				print "</td><td align=center>";
				print "$start_column[$k]";
				print "</td><td align=center>";
				print "$height[$k]";
				print "</td><td align=center>";
				print "$width[$k]";
				print "$lower_threshold[$k]";
				print "</td><td align=middle>";
				print "$pha_range[$k]";
				print '</td><td align=center>';
				print "$sample[$k]";
				print "</td><td align=center>";
				print '</td></tr>';
			}
			print '</table>';
		}else{
			print "<h3>No ACIS  Window Constraints</h3>";
		}

		print '<hr />';
	}

#------------------------------------
#----- TOO Parameter Case start here
#------------------------------------

	if($usint_on =~ /no/ && $too_id =~ /NULL/){
	}else{
		print '<h2>TOO Parameters</h2>';
	
		print '<table cellspacing=3 cellpadding=5>';
		print '<tr>';
		print '<th valign=top><a href="#" onClick="WindowOpen(too_id);return false;">TOO ID</a>:</th><td>';
		print "$too_id",'</td>';
		print '</tr><tr>';
		print '<th valign=top nowrap><a href="#" onClick="WindowOpen(too_trig);return false;">TOO Trigger</a>:';
		print '</th><td>',"$too_trig",'</td>';
		print '</tr><tr>';
		print '<th><a href="#" onClick="WindowOpen(too_type);return false;">TOO Type</a>:</th><td>';
		print '$too_type</td>';
		print '</tr></table>';
		print '<table cellspacing=3 cellpadding=5>';
		print '<tr>';
		print '<th>Exact response window (days):</th>';
		print '</tr><tr>';
		print '<th><a href="#" onClick="WindowOpen(too_start);return false;">Start</a>:</th><td>';
		print "$too_start";
		print '</td><td></td>';
		print '<th><a href="#" onClick="WindowOpen(too_stop);return false;">Stop</a>:</th><td>';
		print "$too_stop";
		print '</td><tr>';
		print '<th><a href="#" onClick="WindowOpen(too_followup);return false;">';
		print '# of Follow-up Observations</a>:</th><td>';
		print "$too_followup";
		print '</td></tr></table>';
		print '<table cellspacing=0 cellpadding=5>';
		print '<tr><td></td>';
		print '<th valign=top><a href="#" onClick="WindowOpen(too_remarks);return false;">TOO Remarks</a>:';
		print '</th><td>';
		print "$too_remarks";
		print '</td></tr></table>';
	
	}
#---------------------------------->
#---- Comment and Remarks  -------->
#---------------------------------->
	
	print '<hr />';
	print '<h2>Comments and Remarks</h2>';
	print '<b>The remarks area below is reserved for remarks related to constraints, ';
	print 'actions/considerations that apply to the observation. ';
	print 'Please put all other remarks/comments into the comment area below.';
	print '</b><br />';
	print '<tr> ';
	print '<br />';

#--------------------------------------------------------------------------------------
#------- Some remarks and/or comments contains " in the sentences. Since html page has 
#------- a problem with it, replacing " to ' so that html can behave normally.
#--------------------------------------------------------------------------------------

	@rtemp = split(//,$remarks);
	$temp = '';
	foreach $ent (@rtemp){
		if($ent eq "\""){
			$temp = "$temp"."'";
		}else{
			$temp = "$temp"."$ent";
		}
	}
	$remarks = $temp;
	
	@rtemp = split(//,$mp_remarks);
	$temp = '';
	foreach $ent (@rtemp){
		if($ent eq "\""){
			$temp = "$temp"."'";
		}else{
			$temp = "$temp"."$ent";
		}
	}
	$mp_remarks = $temp;
	
	@rtemp = split(//,$comments);
	$temp = '';
	foreach $ent (@rtemp){
		if($ent eq "\""){
			$temp = "$temp"."'";
		}else{
			$temp = "$temp"."$ent";
		}
	}
		
	$comments = $temp;

	print '<table cellspacing="0" cellpadding="5">';
	print '<th valign=top><a href="#" onClick="WindowOpen(remarks);return false;">Remarks</a>:</th>';
	print "<td>$remarks</td></tr>";

	if($remark_cont ne ''){
		print '<tr><th valign=top>Other Remark:</th><td>',"$remark_cont",'</td></tr>',"\n";
	}

	print '<tr><td colspan=3>';
	print '<b> Comments are kept as a record of why a change was made.<br />';
	print '</td></tr>';
	print '<tr>';
	print '<th  valign=top><a href="#" onClick="WindowOpen(comments);return false;"> Comments</a>:';
	print "</th><td> $comments </td></tr>";
	print '</table>';
	print '<hr />';
	
#------------------------------------->
#---- here is submitting options ----->
#------------------------------------->

	if($no_access == 0 && $sp_user eq 'yes'){
        	print '<b>OPTIONS</b>';
        	print '<p>';
        	print '<table><tr><td>';
#        	print '<b>Clone this ObsID </b>';
        	print '<b>Split this ObsID </b>';
        	print '</td> <td>';
        	print '        <font color=fuchsia> If you need to clone this observation, please click the buttom on the right,<br /> ';
		print '	      add an explanation why you need cloning in the comment area.</font><br />';
        	print '</td><td>';

		print '<input type="submit" name="Check" value="Clone">';
                print '</tr>';
                print '<tr><td>';
                print '<b>ObsID no longer ready to go</b>';
                print '</td> <td>';
                print '       <font color=fuchsia> If you need to remove this obsid from the approved list, please c lick the button on the right';
                print '</td><td>';
                print '<input type="submit" name="Check" value="REMOVE">';
                print '</tr>';
		print '</table>';

                print '<input type="hidden" name="OBSID"     value="',"$orig_obsid",'">';
                print '<input type="hidden" name="ACISID"    value="',"$orig_acisid",'">';
                print '<input type="hidden" name="HRCID"     value="',"$orig_hrcid",'">';
                print '<input type="hidden" name="SI_MODE"   value="',"$si_mode",'">';
                print '<input type="hidden" name="access_ok" value="',"yes",'">';
                print '<input type="hidden" name="pass"      value="',"$pass",'">';
                print '<input type="hidden" name="sp_user"   value="',"$sp_user",'">';
                print '<input type="hidden" name="email_address" value="',"$email_address",'">';
		print '<input type="hidden" name="send_email" value="',"$send_email",'">';

                print '<input type="hidden" name="USER"      value="',"$submitter",'">';
                print '<input type="hidden" name="SUBMITTER" value="',"$submitter",'">';
                print '<input type="hidden" name="USER"      value="',"$submitter",'">';
	}
	
	foreach $name (@paramarray){
		$lname = lc ($name);
		$value = ${$lname};
		print '<input type="HIDDEN" name="',"$name",'" value="',"$value",'">';
	}


	if($usint_on =~ /yes/){
		print '<br /><br />';
		print "<a href=\"$cdo_http/review_report/disp_report.cgi?","$proposal_number",'">Link to peer review report and proposal</a>';
		print '<br />';
	}
	
	
	if($usint_on =~ /test/){
	}elsif($usint_on =~ /no/){
		print "Go to the <A HREF=\"$obs_ss_http/search.html\">";
		print 'Chandra User Observation Search Page</A><p> '; 
	}elsif($usint_on =~ /yes/){
		print "Go to the <A HREF=\"$usint_http/search.html\">";
		print 'Chandra User Observation Search Page</A><p> '; 
	}


#----------------------------------------------------
#----- SPECIAL CASE THAT WE WANT TO JUST PASS VALUES
#---------------------------------------------------

        print "<input type=\"hidden\" name=\"OBSID\"  value=\"$orig_obsid\">";
        print "<input type=\"hidden\" name=\"ACISID\" value=\"$orig_acisid\">";
        print "<input type=\"hidden\" name=\"HRCID\"  value=\"$orig_hrcid\">";


	print end_form();
	print "</body>";
	print "</html>";
	exit();
}



########################################################################################
### data_input_page: create data input page--- Ocat Data Page                        ###
########################################################################################

sub data_input_page{

print <<ENDOFhtml;

ENDOFhtml
print '	<h1>Obscat Data Page</h1>';

if($mp_check > 0){
	print "<h2><b><font color='red'>";
#	print "This obsid is in an active OR list. You must get permission from ";
#	print "<a href='mailto:$sot_contact'>SOT</a> ";
#	print "to make your change.";

	print "This observation is currently under review in an active OR list. ";
	print "You must get a permission from MP to modify entries.";
	print "</font></b><br /></h2>";
}

if($status !~ /scheduled/i && $status !~ /unobserved/i){
	$cap_status = uc($status);
	print "<h2>This observation was <font color='red'>$cap_status</font>.</h2> ";
}

print 'A brief description of the listed parameters is given ';

#----------------------------------------------------------------------
#---- if the observation is alrady in an active OR list, print warning
#----------------------------------------------------------------------

if($usint_on =~ /no/){
	print a({-href=>"$obs_ss_http/user_help.html",-target=>'_blank'},"here");
}elsif($usint_on =~ /yes/){
	print a({-href=>"$usint_http/user_help.html",-target=>'_blank'},"here");
}


if($eventfilter_lower > 0.5 || $awc_l_th == 1){
	print '<br /><br />';
        print '<font color=red><b>';
	if($eventfilter_lower > 0.5 && $awc_l_th == 0){
        	print 'Energy Filter Lowest Energy is larger than 0.5 keV. ';
	}elsif($eventfilter_lower > 0.5 && $awc_l_th == 1){
        	print 'Energy Filter Lowest Energy and ACIS Window Costraint Lowest Energy are larger than 0.5 keV. ';
	}elsif($eventfilter_lower <= 0.5 && $awc_l_th == 1){
        	print 'ACIS Window Costraint Lowest Energy is larger than 0.5 keV. ';
	}
        print 'Please check all Spatial Window parameters of each CCD.<br />';
#	print 'If you want to remove all the window constraints, change Lowest Energy ';
#	print 'to less than or equal to 0.5keV, and set Window Filter to No or Null, ';
#	print 'then Submit the change using the "Submit" button at the bottom of the page. ';
	print '</b></font>';
#	print "<a href=\"$usint_http/eventfilter_answer.html\" target='blank'>Why did this happen?</a>";
	print '<br />';
}

if($sp_user eq 'no'){
        print '<br />';
	print '<table><tr><td>Please pay special attentions to the </td>';
	print '<td bgcolor=blue><font color=white>Blue high-lighted</font></td>';
	print '<td>entries</td></tr></table>';
        print '<br />';
}

	@ntest = split(//, $obsid);
	$tcnt  = 0;
	foreach(@ntest){
		$tcnt++;
	}
	if($tcnt < 5){
		$add_zero = '';
		for($mt = $tcnt; $mt < 5; $mt++){
			$add_zero = "$add_zero".'0';
		}
		$tobsid = "$add_zero"."$obsid";
	}else{
		$tobsid = $obsid;
	}

        $dss_http  = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.'."$tobsid".'.dss.gif';
        $ros_http  = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.'."$tobsid".'.pspc.gif';
        $rass_http = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.'."$tobsid".'.rass.gif';

	print '<p align=right>';
        print "<a href = $dss_http target='blank'><img align=middle src=\"$mp_http/targets/webgifs/dss.gif\"></a>";
        print "<a href = $ros_http target='blank'><img align=middle src=\"$mp_http/targets/webgifs/ros.gif\"></a>";
        print "<a href = $rass_http target='blank'><img align=middle src=\"$mp_http/targets/webgifs/rass.gif\"></a>";

	print '</p>';

	print '<h2>General Parameters</h2>';

#------------------------------------------------>
#----- General Parameter dispaly starts here----->
#------------------------------------------------>

	print '<table cellspacing="0" cellpadding="5">';
	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(seq_nbr);return false;">Sequence Number</a>:';
	print "</th><td>$seq_nbr</td>";
	print '<th><a href="#" onClick="WindowOpen(status);return false;">Status</a>:';
	print "</th><td>$status</td>";
	print '<th><a href="#" onClick="WindowOpen(obsid);return false;">ObsID #</a>:';
	print "</th><td>$obsid</td>";
	print '<input type="hidden" name="OBSID" value="$obsid">';
	print '<th><a href="#" onClick="WindowOpen(proposal_number);return false;">Proposal Number</a>:</th>';
	print "<td>$proposal_number</td>";
	print '</tr></table>';

	print '<table cellspacing="0" cellpadding="5">';
	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(proposal_title);return false;">Proposal Title</a>:</th>';
	print "<td>$proposal_title</td>";
	print '</tr>';
	print ' </table>';
	
	print '<table cellspacing="0" cellpadding="5">';
	print '<tr>';
	print '<td></td>';
	print '<th><a href="#" onClick="WindowOpen(obs_ao_str);return false;">Obs AO Status</a>:';
	print "</th><td>$obs_ao_str</td>";
	print '</tr></table>';

	print '<table cellspacing="3" cellpadding="10">';
	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(targname);return false;">Target Name</a>:</th><td>';
	print "$targname",'</td>';
	print '<th><a href="#" onClick="WindowOpen(si_mode);return false;">SI Mode</a>:</th>';

	if($sp_user eq 'no'){
		print '<td align="LEFT">',"$si_mode",'</td>';
	}else{
		print '<td align="LEFT"><input type="text" name="SI_MODE" value="',"$si_mode",'" size="12"></td>';
	}

	print '<th><a href="#" onClick="WindowOpen(aca_mode);return false;">ACA Mode</a>:</th>';
	print '<td align="LEFT">',"$aca_mode",'</td>';
	print '</tr></table>';

	print '<table cellspacing="3" cellpadding="10">';
	print '<tr><td></td>';

	if($sp_user eq 'no'){
		print '<th><a href="#" onClick="WindowOpen(instrument);return false;">Instrument</a>:</th><td>',"$instrument";
		print "<input type=\"hidden\" name=\"INSTRUMENT\" value=\"$instrument\">";	

		print '</td><th><a href="#" onClick="WindowOpen(grating);return false;">Grating</a>:</th><td>',"$grating";
		print "<input type=\"hidden\" name=\"GRATING\" value=\"$grating\">";	
	
		print '</td><th><a href="#" onClick="WindowOpen(type);return false;">Type</a>:</th><td>',"$type";
		print "<input type=\"hidden\" name=\"TYPE\" value=\"$type\">";	
	}else{

		print '<th><a href="#" onClick="WindowOpen(instrument);return false;">Instrument</a>:</th><td>';
		print popup_menu(-name=>'INSTRUMENT', -value=>['ACIS-I','ACIS-S','HRC-I','HRC-S'],
			 	-default=>"$instrument",-override=>100000);
		
		print '</td><th><a href="#" onClick="WindowOpen(grating);return false;">Grating</a>:</th><td>';
		print popup_menu(-name=>'GRATING', -value=>['NONE','HETG','LETG'],
			 	-default=>"$grating",-override=>10000);
		
		print '</td><th><a href="#" onClick="WindowOpen(type);return false;">Type</a>:</th><td>';
		print popup_menu(-name=>'TYPE', -value=>['GO','TOO','GTO','CAL','DDT','CAL_ER', 'ARCHIVE', 'CDFS'],
			 	-default=>"$type",-override=>10000);
	}
	
	print '</td></tr></table>';
	
	print '<table cellspacing="15" cellpadding="5">';
	print '<tr>';
	print '<th><a href="#" onClick="WindowOpen(PI_name);return false;">PI Name</a>:';
	print "</th><td>$PI_name</td>";
	print '<th><a href="#" onClick="WindowOpen(coi_contact);return false;">Observer</a>:';
	print "</th><td> $Observer</td></tr>";

#	if($sp_user eq 'no'){
		print '<th><a href="#" onClick="WindowOpen(approved_exposure_time);return false;">Exposure Time</a>:</th>';
		print "<td>$approved_exposure_time ks</td>";
		print "<input type=\"hidden\" name=\"APPROVED_EXPOSURE_TIME\" value=\"$approved_exposure_time\">";
#	}else{
#		print '<th><a href="#" onClick="WindowOpen(approved_exposure_time);return false;">Exposure Time</a>:</th>';
#		print '<td align="LEFT"><input type="text" name="APPROVED_EXPOSURE_TIME" value="';
#		print "$approved_exposure_time".'" size="8"> ks</td>';
#	}

	print '<th><a href="#" onClick="WindowOpen(rem_exp_time);return false;">Remaining Exposure Time</a>:</th>';
	print "<td>$rem_exp_time ks</td>";
	print '</tr></table>';
	
	print '<table cellspacing="3" cellpadding="8">';

	print '<tr><th><a href="#" onClick="WindowOpen(joint);return false;">Joint Proposal</a>:</th>';
	print "<td>$proposal_joint</td></tr>";
	print '<tr><td></td><th><a href="#" onClick="WindowOpen(prop_hst);return false;">HST Approved Time</a>:</th>';
	print "<td>$proposal_hst</td>";
	print '<th><a href="#" onClick="WindowOpen(prop_noao);return false;">NOAO Approved Time</a>:</th>';
	print "<td>$proposal_noao</td>";
	print '</tr><tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(prop_xmm);return false;">XMM Approved Time</a>:';
	print "</th><td>$proposal_xmm</td>";
	print '<th><a href="#" onClick="WindowOpen(prop_rxte);return false;">RXTE Approved Time</a>:';
	print "</th><td>$rxte_approved_time</td>";
	print '</tr><tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(prop_vla);return false;">VLA Approved Time</a>:</th>';
	print "<td>$vla_approved_time</td>";
	print '<th><a href="#" onClick="WindowOpen(prop_vlba);return false;">VLBA Approved Time</a>:</th>';
	print "<td>$vlba_approved_time</td>";
	print '</tr></table>';
	
	
	print '<TABLE CELLSPACING="8" CELLPADDING="10">';
	print '<tr>';
	print '<th><a href="#" onClick="WindowOpen(soe_st_sched_date);return false;">Schedule Date</a>:</th>';
	print "<td>$soe_st_sched_date</td>";
	print '<th><a href="#" onClick="WindowOpen(lts_lt_plan);return false;">LTS Date</a>:';
	print "</th><td>$lts_lt_plan</td>";
	print '</tr></table>';

#----------------------------------------
#-------- Convert $ra from decimal to hms
#----------------------------------------

	$ra = $dra;
       	$hh = int($ra/15);
       	$mm = 60 * ($ra / 15 - $hh);
       	$ss = 60 * ($mm - int($mm));

       	$tra = sprintf("%02d:%02d:%06.4f", $hh, $mm, $ss);

#-----------------------------------------
#-------- Convert $dec from decimal to dms
#-----------------------------------------

	@dtemp = split(/:/, $dec);
	$dec = $ddec;
       	if ($dec < 0) { 			# set sign
               	$sign = "-";
             	$dec *= -1;
       	}
       	else
       	{$sign = "+"}
	
       	$dd = int($dec);
       	$mm = 60 * ($dec - $dd);
       	$ss = 60 * ($mm - int($mm));
       	$secrollover = sprintf("%02f", $ss);
       	if ($secrollover == 60) {
               	$ss = abs($ss - 60);
               	$mm = ($mm +1 );
       	}
       	if ($mm == 60) {
               	$mm = ($mm - 60);
         	$hh = ($dd + 1);
       	}
  	$tdec = sprintf("%.1s%02d:%02d:%06.4f", $sign, $dd, $mm, $ss);

	print 'You may enter RA and Dec in either HMS/DMS format (separated by colons, e.g. ';
	print '16:22:04.8  -27:43:04.0), or as decimal degrees.  The original OBSCAT decimal ';
	print ' degree values are provided below the update boxes .';

#        $view_http = "$obs_ss_http/PSPC_page/plot_pspc.cgi?"."$obsid";
        $view_http = "$usint_http/PSPC_page/plot_pspc.cgi?"."$obsid";
#	print 'If you want to experiment with viewing orientation, open: ';

# 	print "<a href = $view_http target='blank'BORDER=0 WIDTH=692 HEIGHT=1000>Viewing Orientation Page</a> (it may take several seconds).";
	
	if($sp_user eq 'no'){
		print 'The sum of the differences between new and old RA and/or DEC must be smaller than ';
		print '8 arcmin.<br />';
	}else{
		print '<br />';
	}
	print '<table cellspacing="8" cellpadding="5">';
	print '<tr><td></td>';

	if($sp_user eq 'no'){
		print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ra);return false;"><font color=white>RA (HMS)</font></a>:</th>';
	}else{
		print '<th><a href="#" onClick="WindowOpen(ra);return false;">RA (HMS)</a>:</th>';
	}
	print '<td align="LEFT"><input type="text" name="RA" value="',"$tra",'" size="14"></td>';
	
	if($sp_user eq 'no'){
		print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(dec);return false;"><font color=white>Dec (DMS)</font></a>:</th>';
	}else{
		print '<th><a href="#" onClick="WindowOpen(dec);return false;">Dec (DMS)</a>:</th>';
	}

	print '<td align="LEFT"><input type="text" name="DEC" value="',"$tdec",'" size="14"></td>';
#	$target_http = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.rollvis.gif';
#
#--- planned roll has a range
#
	print '<th><a href="#" onClick="WindowOpen(planned_roll);return false;">Planned Roll</a>:</th>';

	if($scheduled_roll eq '' && $scheduled_range eq ""){
            print '<td>NA</td>';
        }elsif($scheduled_roll <= $scheduled_range){
            print '<td>',"$scheduled_roll",' -- ', "$scheduled_range",'</td>';
        }else{
            print '<td>',"$scheduled_range",' -- ', "$scheduled_roll",'</td>';
        }
	print '</td></tr>';



	print '<tr><td></td>';
	print '<th><a href="#" onClick="WindowOpen(dra);return false;">RA</a>:</th><td>',"$dra",'</td>';
	print '<th><a href="#" onClick="WindowOpen(ddec);return false;">Dec</a>:</th><td>',"$ddec",'</td>';

	if($status =~ /^OBSERVED/i || $status =~ /ARCHIVED/i){
	}else{
		$roll_obsr ='';
	}

#	if($sp_user eq 'no'){
        	print '<th><a href="#" onClick="WindowOpen(roll_obsr);return false;">Roll Observed</a>:</th>';
        	print '<td align="LEFT">',"$roll_obsr",'</td></tr>';
		print "<input type=\"hidden\" name=\"ROLL_OBSR\" value=\"$roll_obsr\">";
#	}else{
#		print '<td><a href="#" onClick="WindowOpen(roll_obsr);return false;">Roll Observed</a>:<td>';
#		print '<td align="LEFT"><input type="text" name="ROLL_OBSR" value="'. "$roll_obsr".'" size="6"></td>';
#	}
	print '</tr></table>';

	print '<table cellspacing="3" cellpadding="5">';
	print '<tr>';

	if($sp_user eq 'no'){
		print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(y_det_offset);return false;"><font color=white>Offset: Y</font></a>:</th>';
	}else{
		print '<th><a href="#" onClick="WindowOpen(y_det_offset);return false;">Offset: Y</a>:</th>';
	}

	print '<td align="LEFT"><input type="text" name="Y_DET_OFFSET" value="';
	print "$y_det_offset";
	print '" size="12"> arcmin</td><td></td>';

	if($sp_user eq 'no'){
		print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(z_det_offset);return false;"><font color=white>Z</font></a>:</th>';
	}else{
		print '<th><a href="#" onClick="WindowOpen(z_det_offset);return false;">Z</a>:</th>';
	}

	print '<td align="LEFT"><input type="text" name="Z_DET_OFFSET" value="';
	print "$z_det_offset";
	print '" size="12"> arcmin</td>';
	print '</tr><tr>';
	print '<th><a href="#" onClick="WindowOpen(trans_offset);return false;">Z-Sim</a>:</th>';
	print '<td align="LEFT"><input type="text" name="TRANS_OFFSET" value="';
	print "$trans_offset";
	print '" size="12"> mm<td>';
	print '<th><a href="#" onClick="WindowOpen(focus_offset);return false;">Sim-Focus</a>:</th>';
	print '<td align="LEFT"><input type="text" name="FOCUS_OFFSET" value="';
	print "$focus_offset";
	print '" size="12"> mm</td>';

	print '<tr>';

	if($sp_user eq 'yes'){
		print '<th><a href="#" onClick="WindowOpen(defocus);return false;">Focus</a>:</th>';
		print '<td align="LEFT"><input type="text" name="DEFOCUS" value="',"$defocus", '" size="12"></td>';
		print '<td></td>';
	}else{
		print "<input type=\"hidden\" name=\"DEFOCUS\" value=\"$defocus\">";
	}

	print '<th><a href="#" onClick="WindowOpen(raster_scan);return false;">Raster Scan</a>:</th>';
	print "<td align=\"LEFT\">$raster_scan</td>";
#	print '<td align="LEFT"><input type="text" name="RASTER_SCAN"';
#	print " value=\"$raster_scan\" size=\"12\"></td>";
	print '</tr></table>';

	print '<table cellspacing="3" cellpadding="5">';
#	if($sp_user eq 'no' && $duninterrupt ne 'YES'){
#		print '<tr><th><a href="#" onClick="WindowOpen(uninterrupt);return false;">Uninterrupted Obs</a>:</th><td>';
#		print popup_menu(-name=>'UNINTERRUPT', -value=>['NULL','NO','PREFERENCE'], 
#			 	-default=>"$duninterrupt",-override=>10000);
	if($sp_user eq 'no'){
		print '<tr><th><a href="#" onClick="WindowOpen(uninterrupt);return false;">Uninterrupted Obs</a>:</th><td>';
		print "$duninterrupt";
		print "<input type=\"hidden\" name=\"UNINTERRUPT\" value=\"$duninterrupt\"\>";
		
	}else{
		print '<tr><th><a href="#" onClick="WindowOpen(uninterrupt);return false;">Uninterrupted Obs</a>:</th><td>';
		print popup_menu(-name=>'UNINTERRUPT', -value=>['NULL','NO','PREFERENCE','YES'], 
			 	-default=>"$duninterrupt",-override=>1000);
	}
#
#--- added 08/01/11
#
	print '</td><td>&#160';
	print '</td><th><a href="#"  onClick="WindowOpen(extended_src);return false;">Extended SRC</a>:</th><td>';
	print popup_menu(-name=>'EXTENDED_SRC', -value=>['NO','YES'], 
		 	-default=>"$dextended_src",-override=>1000);
	print '</td></tr>';



	if($sp_user eq 'no'){
		print '<tr><th><a href="#" onClick="WindowOpen(obj_flag);return false;">Solar System Object</a>:</th><td>';
		print "$obj_flag";
		print '</td><td>';
		print '</td><th><a href="#" onClick="WindowOpen(object);return false;">Object</a>:</th><td>';
		print "$object";
		print "<input type=\"hidden\" name=\"OBJ_FLAG\" value=\"$obj_flag\"\>";
		print "<input type=\"hidden\" name=\"OBJECT\" value=\"$object\"\>";
	}else{
		print '<tr><th><a href="#" onClick="WindowOpen(obj_flag);return false;">Solar System Object</a>:</th><td>';
		print popup_menu(-name=>'OBJ_FLAG',-value=>['NO','MT','SS'],-default=>"$obj_flag", -override=>10000);
		print '</td><td>';
		print '</td><th><a href="#" onClick="WindowOpen(object);return false;">Object</a>:</th><td>';
		print popup_menu(-name=>'OBJECT', 
		 		-value=>['NONE','NEW','COMET','EARTH','JUPITER','MARS','MOON','NEPTUNE',
		          		'PLUTO','SATURN','URANUS','VENUS'],
		 		-default=>"$object", -override=>10000);
	}
	print '</tr><tr>';
	
	print '</td><th><a href="#" onClick="WindowOpen(photometry_flag);return false;">Photometry</a>:</th><td>';
	print popup_menu(-name=>'PHOTOMETRY_FLAG', -value=>['NULL','YES','NO'], 
			 -default=>"$dphotometry_flag", -override=>100000);
	print '</td>';

	print '<td></td>';
	print '<th><a href="#" onClick="WindowOpen(vmagnitude);return false;">V Mag</a>:';
	print "</th><td align=\"LEFT\"><input type=\"text\" name=\"VMAGNITUDE\" value=\"$vmagnitude\" size=\"12\"></td>";
	print '<tr>';
	print '<th><a href="#" onClick="WindowOpen(est_cnt_rate);return false;">Count Rate</a>:</th>';
	print '<td align="LEFT"><input type="text" name="EST_CNT_RATE"';
	print " value=\"$est_cnt_rate\" size=\"12\"></td>";
	print '<td></td>';
	print '<th><a href="#" onClick="WindowOpen(forder_cnt_rate);return false;">1st Order Rate</a>:';
	print '</th><td align="LEFT"><input type="text" name="FORDER_CNT_RATE"';
	print " value=\"$forder_cnt_rate\" size=\"12\"></td>";
	print '</tr></table>';
	print '<hr />';

	print '<h2>Dither</h2>';

	if($sp_user eq 'yes'){
		print '<table cellspacing="3" cellpadding="5">';
		print '<tr><th><a href="#" onClick="WindowOpen(dither_flag);return false;">Dither</a>:</th><td>';
		print popup_menu(-name=>'DITHER_FLAG', -value=>['NULL','YES','NO'], 
			 	-default=>"$ddither_flag", -override=>100000);
		print '</td><td></td><td></td><td></td><td></td></tr>';
	
		print '<tr><td></td><th><a href="#" onClick="WindowOpen(y_amp);return false;">y_amp</a> (in arcsec):</th>';
		print '<td align="LEFT"><input type="text" name="Y_AMP_ASEC" value="',"$y_amp_asec",'" size="8"></td>';
	
		print '<th><a href="#" onClick="WindowOpen(y_freq);return false;">y_freq</a> (in arcsec/sec):</th>';
		print '<td align="LEFT"><input type="text" name="Y_FREQ_ASEC" value="',"$y_freq_asec",'" size="8"></td>';
	
		print '<th><a href="#" onClick="WindowOpen(y_phase);return false;">y_phase</a>:</th>';
		print '<td align="LEFT"><input type="text" name="Y_PHASE" value="',"$y_phase",'" size="8"></td>';
		print '</tr>';
#---
                print '<tr><td></td><th>y_amp (in degrees):</th>';
                print '<td align="LEFT">',"$y_amp",'</td>';

                print '<th>y_freq(in degree/sec)</th>';
                print '<td align="LEFT">',"$y_freq",'</td>';

                print '<th></th>';
                print '<td align="LEFT"></td>';
                print '</tr>';
#----
	
		print '<tr><td></td><th><a href="#" onClick="WindowOpen(z_amp);return false;">z_amp</a> (in arcsec):</th>';
		print '<td align="LEFT"><input type="text" name="Z_AMP_ASEC" value="',"$z_amp_asec",'" size="8"></td>';
	
		print '<th><a href="#" onClick="WindowOpen(z_freq);return false;">z_freq</a> (in arcsec/sec):</th>';
		print '<td align="LEFT"><input type="text" name="Z_FREQ_ASEC" value="',"$z_freq_asec",'" size="8"></td>';
	
		print '<th><a href="#" onClick="WindowOpen(z_phase);return false;">z_phase</a>:</th>';
		print '<td align="LEFT"><input type="text" name="Z_PHASE" value="',"$z_phase",'" size="8"></td>';
		print '</tr>';

#---
                print '<tr><td></td><th>z_amp (in degrees):</th>';
                print '<td align="LEFT">',"$z_amp",'</td>';

                print '<th>z_freq(in degree/sec)</th>';
                print '<td align="LEFT">',"$z_freq",'</td>';

                print '<th></th>';
                print '<td align="LEFT"></td>';
                print '</tr>';
#----
	
		print '</table>';
	}else{
		print '<table cellspacing="3" cellpadding="5">';
		print '<tr><th><a href="#" onClick="WindowOpen(dither_flag);return false;">Dither</a>:</th><td>';
		print "$ddither_flag";
		print '</td><td></td><td></td><td></td><td></td></tr>';
	
		print '<tr><td></td><th><a href="#" onClick="WindowOpen(y_amp);return false;">y_amp</a> (in arcsec):</th>';
		print '<td align="LEFT">',"$y_amp_asec",'</td>';
	
		print '<th><a href="#" onClick="WindowOpen(y_freq);return false;">y_freq</a>(in arcsec):</th>';
		print '<td align="LEFT">',"$y_freq_asec",'</td>';
	
		print '<th><a href="#" onClick="WindowOpen(y_phase);return false;">y_phase</a>:</th>';
		print '<td align="LEFT">',"$y_phase",'</td>';
		print '</tr>';
#---
                print '<tr><td></td><th>y_amp (in degrees):</th>';
                print '<td align="LEFT">',"$y_amp",'</td>';

                print '<th>y_freq(in degree/sec)</th>';
                print '<td align="LEFT">',"$y_freq",'</td>';

                print '<th></th>';
                print '<td align="LEFT"></td>';
                print '</tr>';
#----
	
		print '<tr><td></td><th><a href="#" onClick="WindowOpen(z_amp);return false;">z_amp</a> (in arcsec):</th>';
		print '<td align="LEFT">',"$z_amp_asec",'</td>';
	
		print '<th><a href="#" onClick="WindowOpen(z_freq);return false;">z_freq</a> (in arcsec):</th>';
		print '<td align="LEFT">',"$z_freq_asec",'</td>';
	
		print '<th><a href="#" onClick="WindowOpen(z_phase);return false;">z_phase</a>:</th>';
		print '<td align="LEFT">',"$z_phase",'</td>';
		print '</tr>';
#---
                print '<tr><td></td><th>z_amp (in degrees):</th>';
                print '<td align="LEFT">',"$z_amp",'</td>';

                print '<th>z_freq(in degree/sec)</th>';
                print '<td align="LEFT">',"$z_freq",'</td>';

                print '<th></th>';
                print '<td align="LEFT"></td>';
                print '</tr>';
#----
	
		print '</table>';
		print "<input type=\"hidden\" name=\"DITHER_FLAG\" value=\"$ddither_flag\"\>";
		print "<input type=\"hidden\" name=\"Y_AMP_ASEC\" value=\"$y_amp_asec\"\>";
		print "<input type=\"hidden\" name=\"Y_FREQ_ASEC\" value=\"$y_freq_asec\"\>";
		print "<input type=\"hidden\" name=\"Y_PHASE\" value=\"$y_phase\"\>";
		print "<input type=\"hidden\" name=\"Y_AMP\" value=\"$y_amp\"\>";
		print "<input type=\"hidden\" name=\"Y_FREQ\" value=\"$y_freq\"\>";
		print "<input type=\"hidden\" name=\"Z_AMP_ASEC\" value=\"$z_amp_asec\"\>";
		print "<input type=\"hidden\" name=\"Z_FREQ_ASEC\" value=\"$z_freq_asec\"\>";
		print "<input type=\"hidden\" name=\"Z_PHASE\" value=\"$z_phase\"\>";
		print "<input type=\"hidden\" name=\"Z_AMP\" value=\"$z_amp\"\>";
		print "<input type=\"hidden\" name=\"Z_FREQ\" value=\"$z_freq\"\>";
	}
	print '<hr />';

#-------------------------------------
#----- time constraint case start here
#-------------------------------------

	print '<h2>Time Constraints</h2>';

#	print '<table><tr><th>';
#	print '<a href="#" onClick="WindowOpen(window_flag);return false;">Time Constraint? </th><td>';
#	if($sp_user eq 'no' && $dwindow_flag ne 'YES' ){
#		print popup_menu(-name=>"WINDOW_FLAG", -value=>['NULL','NO','PREFERENCE'],-default=>"$dwindow_flag",-override=>1000);
#	}else{
#		print popup_menu(-name=>"WINDOW_FLAG", -value=>['NULL','YES','NO','PREFERENCE'],-default=>"$dwindow_flag",-override=>100000);
#	}
#	print '</td></tr></table>';

	print "<input type=\"hidden\" name=\"TIME_ORDR\" value=\"$time_ordr\">";

	if($dwindow_flag =~ /NO/i || $dwindow_flag =~ /NULL/i){
                print "<h3 style='padding-bottom:40px'>There Is No Time Constraints. Do You Need To Add? ";
                print popup_menu(-name=>"WINDOW_FLAG", -value=>['NO', 'YES'], -default=>"$dwindow_flag", -override=>100000);
                print '<input type="submit" name="Check" value="Update">';
                print '</h3>';

                print "<input type=\"hidden\" name=\"WINDOW_CONSTRAINT1\" value=\"$dwindow_constraint[1]\">";
                print "<input type=\"hidden\" name=\"START_MONTH1\" value=\"$start_month[1]\">";
                print "<input type=\"hidden\" name=\"START_DATE1\" value=\"$start_date[1]\">";
                print "<input type=\"hidden\" name=\"START_YEAR1\" value=\"$start_year[1]\">";
                print "<input type=\"hidden\" name=\"START_TIME1\" value=\"$start_time[1]\">";

                print "<input type=\"hidden\" name=\"END_MONTH1\" value=\"$end_month[1]\">";
                print "<input type=\"hidden\" name=\"END_DATE1\" value=\"$end_date[1]\">";
                print "<input type=\"hidden\" name=\"END_YEAR1\" value=\"$end_year[1]\">";
                print "<input type=\"hidden\" name=\"END_TIME1\" value=\"$end_time[1]\">";

                print "<input type=\"hidden\" name=\"TIME_ORDR_ADD\" value=\"1\">";

	}else{
		print "<input type=\"hidden\" name=\"WINDOW_FLAG\" value=\"$dwindow_flag\">";
		print "<input type=\"hidden\" name=\"TIME_ORDR_ADD\" value=\"$time_ordr_add\">";

		if($sp_user eq 'yes'){
			if($time_ordr_add == 0){
				print 'If you want to add ranks, press "Add Time Rank." If you want to remove null entries, press "Remove Null Time Entry."';
				print '<br />';
#				print '<spacer type=horizontal size=30>';
				print '<b><a href="#" onClick="WindowOpen(time_ordr);return false;">Rank</a></b>: ';
				print '<spacer type=horizontal size=30>';
#				print textfield(-name=>'TIME_ORDR', -value=>"$time_ordr", -size=>'3');

				print '<spacer type=horizontal size=50>';
				print submit(-name=>'Check',-value=>'     Add Time Rank     ')	;
				print submit(-name=>'Check',-value=>'Remove Null Time Entry ')  ;
			}
		}
	
		print '<table cellspacing="0" cellpadding="5">';
		print '<tr><th><a href="#" onClick="WindowOpen(time_ordr);return false;">Rank</a></th>
			<th><a href="#" onClick="WindowOpen(window_constraint);return false;">Window Constraint</a><th>
			<th>Month</th><th>Date</th><th>Year</th><th>Time (24hr system)</th></tr>';

		for($k = 1; $k <= $time_ordr; $k++){
			if($start_month[$k] =~/\d/){
				if($start_month[$k]    == 1) {$wstart_month = 'Jan'}
				elsif($start_month[$k] == 2) {$wstart_month = 'Feb'}
				elsif($start_month[$k] == 3) {$wstart_month = 'Mar'}
				elsif($start_month[$k] == 4) {$wstart_month = 'Apr'}
				elsif($start_month[$k] == 5) {$wstart_month = 'May'}
				elsif($start_month[$k] == 6) {$wstart_month = 'Jun'}
				elsif($start_month[$k] == 7) {$wstart_month = 'Jul'}
				elsif($start_month[$k] == 8) {$wstart_month = 'Aug'}
				elsif($start_month[$k] == 9) {$wstart_month = 'Sep'}
				elsif($start_month[$k] == 10){$wstart_month = 'Oct'}
				elsif($start_month[$k] == 11){$wstart_month = 'Nov'}
				elsif($start_month[$k] == 12){$wstart_month = 'Dec'}
				else{$wstart_month = 'NULL'}
				$start_month[$k]   = $wstart_month;
			}
		
			if($end_month[$k] =~ /\d/){
				if($end_month[$k]    == 1) {$wend_month = 'Jan'}
				elsif($end_month[$k] == 2) {$wend_month = 'Feb'}
				elsif($end_month[$k] == 3) {$wend_month = 'Mar'}
				elsif($end_month[$k] == 4) {$wend_month = 'Apr'}
				elsif($end_month[$k] == 5) {$wend_month = 'May'}
				elsif($end_month[$k] == 6) {$wend_month = 'Jun'}
				elsif($end_month[$k] == 7) {$wend_month = 'Jul'}
				elsif($end_month[$k] == 8) {$wend_month = 'Aug'}
				elsif($end_month[$k] == 9) {$wend_month = 'Sep'}
				elsif($end_month[$k] == 10){$wend_month = 'Oct'}
				elsif($end_month[$k] == 11){$wend_month = 'Nov'}
				elsif($end_month[$k] == 12){$wend_month = 'Dec'}
				else{$wend_month = 'NULL'}
				$end_month[$k]   = $wend_month;
			}

			if($sp_user eq 'no'){
#
#---- if you are not USINT user, you cannot edit here
#
               			print '<tr><td align=center><b>';
                		print "$k";
                		print '</b></td><td>';

                		print "$dwindow_constraint[$k]";
                		print '</td><th><a href="#" onClick="WindowOpen(tstart);return false;">Start</a></th><td align= center>';

                		print "$start_month[$k]";
                		print '</td><td align=center>';
	
                		print "$start_date[$k]";
                		print '</td><td align=center>';
	
                		print "$start_year[$k]";
                		print '</td><td align=center>';
	
                		print "$start_time[$k]";

#               		print '</td><td>',"$tstart[$k]";
                		print '</td></tr><tr><td></td><td></td>';
	
                		print '</td><th><a href="#" onClick="WindowOpen(tstop);return false;">End</a></th><td align=center>';
	
                		print "$end_month[$k]";
                		print '</td><td align=center>';
	
                		print "$end_date[$k]";
                		print '</td><td align=center>';
	
                		print "$end_year[$k]";
                		print '</td><td align=center>';
	
                		print "$end_time[$k]";
#               		print '</td><td>',"$tstop[$k]";
                		print '</td></tr>';

				$twindow_constraint = 'WINDOW_CONSTRAINT'."$k";
				$tstart_month       = 'START_MONTH'."$k";
				$tstart_date        = 'START_DATE'."$k";
				$tstart_year        = 'START_YEAR'."$k";
				$tstart_time        = 'START_TIME'."$k";
				$tend_month         = 'END_MONTH'."$k";
				$tend_date          = 'END_DATE'."$k";
				$tend_year          = 'END_YEAR'."$k";
				$tend_time          = 'END_TIME'."$k";
	
				print "<input type=\"hidden\" name=\"$twindow_constraint\" value=\"$dwindow_constraint[$k]\">";
				print "<input type=\"hidden\" name=\"$tstart_month\" value=\"$start_month[$k]\">";
				print "<input type=\"hidden\" name=\"$tstart_date\"  value=\"$start_date[$k]\">";
				print "<input type=\"hidden\" name=\"$tstart_year\"  value=\"$start_year[$k]\">";
				print "<input type=\"hidden\" name=\"$tstart_time\"  value=\"$start_time[$k]\">";
				print "<input type=\"hidden\" name=\"$tend_month\"   value=\"$end_month[$k]\">";
				print "<input type=\"hidden\" name=\"$tend_date\"    value=\"$end_date[$k]\">";
				print "<input type=\"hidden\" name=\"$tend_year\"    value=\"$end_year[$k]\">";
				print "<input type=\"hidden\" name=\"$tend_time\"    value=\"$end_time[$k]\">";
			}else{
#
#----- yes the user is USINT 
#
				print '<tr><td align=center><b>';
				print "$k";
				print '</b></td><td>';
	
				$twindow_constraint = 'WINDOW_CONSTRAINT'."$k";
	
				if($sp_user eq'yes' || $dwindow_constraint[$k] =~ /CONSTRAINT/i){
					print popup_menu(-name=>"$twindow_constraint", -value=>['CONSTRAINT','PREFERENCE'],
				 		-default=>"$dwindow_constraint[$k]", -override=>100000);
				}else{
					print popup_menu(-name=>"$twindow_constraint", -value=>['PREFERENCE'],
				 		-default=>"$dwindow_constraint[$k]", -override=>100000);
				}
				print '</td><th><a href="#" onClick="WindowOpen(tstart);return false;">Start</a></th><td>';
	
				$tstart_month = 'START_MONTH'."$k";
	
				print popup_menu(-name=>"$tstart_month",
                 				-value=>['NULL','Jan', 'Feb', 'Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
                 				-default=>"$start_month[$k]",-override=>100000);
				print '</td><td>';
				
				$tstart_date = 'START_DATE'."$k";
	
				print popup_menu(-name=>"$tstart_date",
                 			-value=>['NULL','01','02','03','04','05','06','07','08','09','10',
                                 			'11','12','13','14','15','16','17','18','19','20',
                                 			'21','22','23','24','25','26','27','28','29','30', '31'],
                 			-default=>"$start_date[$k]", -override=>10000);
				print '</td><td>';

				$tstart_year = 'START_YEAR'."$k";
	
				print popup_menu(-name=>"$tstart_year",
                 				-value=>['NULL','1999','2000','2001','2002','2003','2004','2005','2006','2007','2008',
                                 			'2009','2010','2011','2012','2013','2014', '2015', '2016', '2017', '2018', '2019', '2020'],
                 				-default=>"$start_year[$k]",-override=>1000000);
				print '</td><td>';
	
				$tstart_time = 'START_TIME'."$k";
	
				print textfield(-name=>"$tstart_time", -size=>'8', -default =>"$start_time[$k]", -override=>1000000);
	
#				print '</td><td>',"$tstart[$k]";
				print '</td></tr><tr><td></td><td></td>';
		
				print '</td><th><a href="#" onClick="WindowOpen(tstop);return false;">End</a></th><td>';
	
				$tend_month = 'END_MONTH'."$k";
	
				print popup_menu(-name=>"$tend_month",
                 				-value=>['NULL','Jan', 'Feb', 'Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
                 				-default=>"$end_month[$k]",-override=>10000);
				print '</td><td>';
	
				$tend_date = 'END_DATE'."$k";
	
				print popup_menu(-name=>"$tend_date",
                 				-value=>['NULL','01','02','03','04','05','06','07','08','09','10',
                                 				'11','12','13','14','15','16','17','18','19','20',
                                 				'21','22','23','24','25','26','27','28','29','30', '31'],
                 				-default=>"$end_date[$k]",-override=>1000000);
				print '</td><td>';
	
				$tend_year = 'END_YEAR'."$k";
	
				print popup_menu(-name=>"$tend_year",
                 				-value=>['NULL','1999','2000','2001','2002','2003','2004','2005','2006','2007','2008',
                                 			'2009','2010','2011','2012','2013','2014', '2015', '2016', '2017', '2018', '2019', '2020'],
                 				-default=>"$end_year[$k]", -override=>100000);
				print '</td><td>';
	
				$tend_time = 'END_TIME'."$k";
	
				print textfield(-name=>"$tend_time", -size=>'8', -default =>"$end_time[$k]", -override=>1000000);
#				print '</td><td>',"$tstop[$k]";
				print '</td></tr>';
			}
		}
		print '</table>';
	}
	print '<hr />';

#-------------------------------------
#---- Roll Constraint Case starts here
#-------------------------------------

#	print '<h2>Roll Constraints</h2>';
        print '<br />';
        print '<font size=+2><b>Roll Constraints </b></font>';

        $target_http = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.rollvis.gif';

        print "<br /><br />";


#	print '<table><tr><th><a href="#" onClick="WindowOpen(roll_flag);return false;">Roll Constraint? </th><td>';
#	if($sp_user eq 'no' && $droll_flag ne 'YES'){
#		print popup_menu(-name=>"ROLL_FLAG", -value=>['NULL','NO','PREFERENCE'],-default=>"$droll_flag",-override=>1000000);
#	}else{
#		print popup_menu(-name=>"ROLL_FLAG", -value=>['NULL','YES','NO','PREFERENCE'],-default=>"$droll_flag",-override=>10000);
#	}
#	print '</td></tr></table>';

	print "<input type=\"hidden\" name=\"ROLL_ORDR\" value=\"$roll_ordr\">";

	if($droll_flag =~ /NO/i || $droll_flag =~ /NULL/i){
                print '<h3 style="padding-bottom:40px">There Is No Roll Constraint. Do You Need To Add? ';
                print popup_menu(-name=>"ROLL_FLAG", -value=>['NO', 'YES'], -default=>"$droll_flag", -override=>100000);
                print '<input type="submit" name="Check" value="Update">';
                print '</h3>';

                print "<input type=\"hidden\" name=\"ROLL_CONSTRAINT1\" value=\"$droll_constraint[1]\">";
                print "<input type=\"hidden\" name=\"ROLL_1801\" value=\"$droll_180[1]\">";
                print "<input type=\"hidden\" name=\"ROLL_TOLERANCE1\" value=\"$droll_tolerance[1]\">";

                print "<input type=\"hidden\" name=\"ROLL_ORDR_ADD\" value=\"1\">";
        }else{
                print "<input type=\"hidden\" name=\"ROLL_ORDR_ADD\" value=\"$roll_ordr_add\">";
                print "<input type=\"hidden\" name=\"ROLL_FLAG\" value=\"$droll_flag\">";

		if($sp_user eq 'yes'){
			print 'If you want to add a rank, press "Add Roll Rank."';
			print 'If you want to remove null entries, press "Remove Null Roll Entry."';
			print '<br />';
#			print '<spacer type=horizontal size=30>';
			print '<b><a href="#" onClick="WindowOpen(roll_ordr);return false;">Rank</a></b>: ';
			print '<spacer type=horizontal size=30>';
#			print textfield(-name=>'ROLL_ORDR', -value=>"$roll_ordr", -size=>'3');

			print '<spacer type=horizontal size=50>';
			print submit(-name=>'Check',-value=>'     Add Roll Rank     ') ;
			print submit(-name=>'Check',-value=>'Remove Null Roll Entry ') ;
		}
	
		print '<table cellspacing="0" cellpadding="5">';
		print '<tr><th><a href="#" onClick="WindowOpen(roll_ordr);return false;">Rank</a></th>
			<th><a href="#" onClick="WindowOpen(roll_constraint);return false;">Type of Constraint</a></th>
			<th><a href="#" onClick="WindowOpen(roll_180);return false;">Roll180?</a></th>
			<th><a href="#" onClick="WindowOpen(roll);return false;">Roll</a></th>
			<th><a href="#" onClick="WindowOpen(roll_tolerance);return false;">Roll Tolerance</a></th></tr>';

		if($sp_user eq 'no'){
        		for($k = 1; $k <= $roll_ordr; $k++){
                		print '<tr><td align=center><b>';
                		print "$k";
                		print '</b></td><td>';
                		$troll_constraint = 'ROLL_CONSTRAINT'."$k";
                		print "$droll_constraint[$k]";
	
                		print '</td><td align=center>';
                		$troll_180 = 'ROLL_180'."$k";
                		print "$droll_180[$k]";
                		print '</td><td align=center>';
                		$troll = 'ROLL'."$k";
                		print "$roll[$k]";
                		print '</td><td align=center>';
                		$troll_tolerance = 'ROLL_TOLERANCE'."$k";
                		print "$roll_tolerance[$k]";
                		print '</td></tr>';
	
				$troll_constraint = 'ROLL_CONSTRAINT'."$k";
				$troll_180 = 'ROLL_180'."$k";
				$troll = 'ROLL'."$k";
				$troll_tolerance = 'ROLL_TOLERANCE'."$k";
	
				print "<input type=\"hidden\" name=\"$troll_constraint\" value=\"$droll_constraint[$k]\">";
				print "<input type=\"hidden\" name=\"$troll_180\" value=\"$droll_180[$k]\">";
				print "<input type=\"hidden\" name=\"$troll\" value=\"$roll[$k]\">";
				print "<input type=\"hidden\" name=\"$troll_tolerance\" value=\"$roll_tolerance[$k]\">";
        		}
		}else{
                	if($roll_ordr_add == 0){
                        	print 'If you want to add a rank, press "Add Roll Rank".';
                        	print 'If you want to remove null entries, press "Remove Null Roll Entry."';
                        	print '<br /><br />';
	
                        	print '<b>Rank</b>: ';
                        	print '<spacer type=horizontal size=30>';
	
                        	print '<spacer type=horizontal size=50>';
                        	print submit(-name=>'Check',-value=>'     Add Roll Rank     ') ;
                        	print submit(-name=>'Check',-value=>'Remove Null Roll Entry ') ;
                	}
                	print '<table cellspacing="0" cellpadding="5">';
                	print '<tr><th>Rank</th>
                        	<th>Type of Constraint</th>
                        	<th>Roll180?</th>
                        	<th>Roll</th>
                        	<th>Roll Tolerance</th></tr>';

			for($k = 1; $k <= $roll_ordr; $k++){
				print '<tr><td align=center><b>';
				print "$k";	
				print '</b></td><td>';
				$troll_constraint = 'ROLL_CONSTRAINT'."$k";
				if($sp_user eq 'yes' || $droll_constraint[$k] =~ /CONSTRAINT/i){
					print popup_menu(-name=>"$troll_constraint", -value=>['CONSTRAINT','PREFERENCE'],
							-default=>"$droll_constraint[$k]", -override=>100000);
				}else{
					print popup_menu(-name=>"$troll_constraint", -value=>['PREFERENCE'],
							-default=>"$droll_constraint[$k]", -override=>100000);
				}
		
				print '</td><td>';
				$troll_180 = 'ROLL_180'."$k";
				print popup_menu(-name=>"$troll_180", -value=>['NULL','YES','NO'],-default=>"$droll_180[$k]",-override=>100000);
				print '</td><td>';
				$troll = 'ROLL'."$k";
				print textfield(-name=>"$troll", -value=>"$roll[$k]", -size=>'10', -override=>100000);
				print '</td><td>';
				$troll_tolerance = 'ROLL_TOLERANCE'."$k";
				print textfield(-name=>"$troll_tolerance", -value=>"$roll_tolerance[$k]", -size=>'10', -override=>100000);
				print '</td></tr>';
			}
		}
		print '</table>';
	}

#----------------------------------------
#----- Other Constraint Case starts here
#----------------------------------------

	print '<hr />';
	print '<h2>Other Constraints</h2>';
	print '<table cellspacing="0" cellpadding="5">';
	print '<tr>';
	
	if($sp_user eq 'no'){
        	print '<th><a href="#" onClick="WindowOpen(constr_in_remarks);return false;">Constraints in Remarks?</a>:</th><td>';
        	print "$dconstr_in_remarks";
		print "<input type=\"hidden\" name=\"CONSTR_IN_REMARKS\" value=\"$dconstr_in_remarks\"\>";
        	print ' </td></tr>';
        	print '</table>';

        	print '<table cellspacing="0" cellpadding="5">';
        	print '<tr>';
        	print '<th><a href="#" onClick="WindowOpen(phase_constraint_flag);return false;">
				Phase Constraint</a>:</th><td align="LEFT">';

        	print "$dphase_constraint_flag";
		print "<input type=\"hidden\" name=\"PHASE_CONSTRAINT_FLAG\" value=\"$dphase_constraint_flag\"\>";

        	print '</td></tr></table>';

        	print '<table cellspacing="10" cellpadding="5">';
        	print '<tr><td></td>';
        	print '<th><a href="#" onClick="WindowOpen(phase_epoch);return false;">Phase Epoch</a>:</th>';
        	print "<td align=\"LEFT\">$phase_epoch</td>";
        	print '<th><a href="#" onClick="WindowOpen(phase_period);return false;">Phase Period</a>:</th>';
        	print "<td align=\"LEFT\">$phase_period</td>";
        	print '<td></td><td></td></tr>';

        	print '<tr><td></td>';
        	print '<th><a href="#" onClick="WindowOpen(phase_start);return false;">Phase Start</a>:</th>';
        	print "<td align=\"LEFT\">$phase_start</td>";
        	print '<th><a href="#" onClick="WindowOpen(phase_start_margin);return false;">Phase Start Margin</a>:</th>';
        	print "<td align=\"LEFT\">$phase_start_margin</td>";
        	print '</tr><tr>';
        	print '<td></td>';
        	print '<th><a href="#" onClick="WindowOpen(phase_end);return false;">Phase End</a>:</th>';
        	print "<td align=\"LEFT\">$phase_end</td>";
        	print '<th><a href="#" onClick="WindowOpen(phase_end_margin);return false;">Phase End Margin</a>:</th>';
        	print "<td align=\"LEFT\">$phase_end_margin</td>";
        	print '</tr></table>';

		print "<input type=\"hidden\" name=\"PHASE_EPOCH\" value=\"$phase_epoch\">";
		print "<input type=\"hidden\" name=\"PHASE_PERIOD\" value=\"$phase_period\">";

		print "<input type=\"hidden\" name=\"PHASE_START\" value=\"$phase_start\">";
		print "<input type=\"hidden\" name=\"PHASE_START_MARGIN\" value=\"$phase_start_margin\">";

		print "<input type=\"hidden\" name=\"PHASE_END\" value=\"$phase_end\">";
		print "<input type=\"hidden\" name=\"PHASE_END_MARGIN\" value=\"$phase_end_margin\">";

                if($monitor_flag =~ /Y/i){
                        %seen = ();
                        @uniq = ();
                        foreach $monitor_elem (@monitor_series) {
print "$monitor_elem<br />";
				$schk = 0;
				OUTER3:
				foreach $echk (@schdulable_list){
					if($monitor_elem =~ /$echk/){
						$schk++;
						last OUTER3;
					}
				}

				if($schk > 0){
					if($usint_on =~ /test/){
                                		push(@uniq, "<a href=\"$test_http\/ocatdata2html.cgi\?$monitor_elem.$pass.$submitter\"> $monitor_elem<\/a> ") unless $seen{$monitor_elem}++;
					}else{
                                		push(@uniq, "<a href=\"$usint_http\/ocatdata2html.cgi\?$monitor_elem.$pass.$submitter\"> $monitor_elem<\/a> ") unless $seen{$monitor_elem}++;
					}
				}
                        }
                        @monitor_series_list  = sort @uniq;
                }

		print '<table cellspacing="0" cellpadding="2">';
		print '<tr>';

		print '<th><a href="#" onClick="WindowOpen(group_id);return false;">Group ID</a>:</th>';
		print '<td>';

		if($group_id){
			print "$group_id";
			print "<input type='hidden' name='GROUP_ID' value=\"$group_id\">";
		}else{
			print '  No Group ID  ';
		}
		print '</td>';

		print '<th><a href="#" onClick="WindowOpen(monitor_flag);return false;">Monitoring Observation:  </th>';
		print "<td>  $monitor_flag   </td>";
		print '</tr></table>';
		print "<input type='hidden' name='MONITOR_FLAG' value=\"$monitor_flag\">";

		if($group_id){
			print "<br />Observations in the Group: @group<br />";
		}elsif($monitor_flag =~ /Y/i){
			print "<br />Observations in the Monitoring: @monitor_series_list<br />";
		}else{
			print "<br />";
		}
	
		print '<table cellspacing="8" cellpadding="5">';

		print '<th><a href="#" onClick="WindowOpen(pre_id);return false;">Follows ObsID#</a>:</th>';
		print '<td align="LEFT">';
		print "$pre_id</td>";

		print '<th><a href="#" onClick="WindowOpen(pre_min_lead);return false;">Min Int<br />(pre_min_lead)</a>:</th>';
		print '<td align="LEFT">';
		print "$pre_min_lead</td>";

		print '<th><a href="#" onClick="WindowOpen(pre_max_lead);return false;">Max Int<br />(pre_max_lead)</a>:</th>';
		print '<td align="LEFT">';
		print "$pre_max_lead</td>";
		print '</tr></table>';

		print "<input type=\"hidden\" name=\"PRE_ID\" value=\"$pre_id\"\>";
		print "<input type=\"hidden\" name=\"PRE_MIN_LEAD\" value=\"$pre_min_lead\"\>";
		print "<input type=\"hidden\" name=\"PRE_MAX_LEAD\" value=\"$pre_max_lead\"\>";
	
        	print '<table cellspacing=6 cellpadding=5>';
        	print '<tr>';
        	print '<th><a href="#" onClick="WindowOpen(multitelescope);return false;">Coordinated Observation</a>:</th><td>';
        	print "$dmultitelescope";
		print "<input type=\"hidden\" name=\"MULTITELESCOPE\" value=\"$dmultitelescope\"\>";

        	print '</td>';
        	print '<td></td>';
        	print '<th><a href="#" onClick="WindowOpen(observatories);return false;">Observatories</a>:</th>';

        	print "<td align=\"LEFT\">$observatories</td>";
		print "<input type=\"hidden\" name=\"OBSERVATORIES\" value=\"$observatories\">";
        	print '</tr>';

        	print '<tr>';
		print '<th><a href="#" onClick="WindowOpen(multitelescope_interval);return false;">Max Coordination Offset</a>:</th>';
        	print "<td align=\"LEFT\">$multitelescope_interval</td>";
		print "<input type=\"hidden\" name=\"MULTITELESCOPE_INTERVAL\" value=\"$multitelescope_interval\">";

	}else{

#----------------------------
#---  sp user part start here
#----------------------------

		print '<th><a href="#" onClick="WindowOpen(constr_in_remarks);return false;">Constraints in Remarks?</a>:</th><td>';
		print popup_menu(-name=>'CONSTR_IN_REMARKS', -value=>['YES','PREFERENCE','NO'],
			 -default=>"$dconstr_in_remarks", -override=>100000);
		print ' </td></tr>';
		print '</table>';

		print '<table cellspacing="0" cellpadding="5">';
		print '<tr>';
		print '<th><a href="#" onClick="WindowOpen(phase_constraint_flag);return false;">Phase Constraint</a>:</th>
		<td align="LEFT">';
		
		if($sp_user eq 'yes' || $dphase_constraint_flag =~ /CONSTRAINT/i){
			print popup_menu(-name=>'PHASE_CONSTRAINT_FLAG', -value=>['NONE','CONSTRAINT','PREFERENCE','NULL'],
			 	-default=>"$dphase_constraint_flag", -override=>10000);
		}else{
			print popup_menu(-name=>'PHASE_CONSTRAINT_FLAG', -value=>['NONE','PREFERENCE','NULL'],
			 	-default=>"$dphase_constraint_flag", -override=>1000000);
		}
	
		print '</td></tr></table>';
	
		print '<table cellspacing="10" cellpadding="5">';
		print '<tr><td></td>';
		print '<th><a href="#" onClick="WindowOpen(phase_epoch);return false;">Phase Epoch</a>:</th>';
		print '<td align="LEFT"><input type="text" name="PHASE_EPOCH" value=';
		print "\"$phase_epoch\"",' size="12"></td>';
		print '<th><a href="#" onClick="WindowOpen(phase_period);return false;">Phase Period</a>:</th>';
		print '<td align="LEFT"><input type="text" name="PHASE_PERIOD" value=';
		print "\"$phase_period\"", ' size="12"></td>';
		print '<td></td><td></td></tr>';
		
		print '<tr><td></td>';
		print '<th><a href="#" onClick="WindowOpen(phase_start);return false;">Phase Start</a>:</th>';
		print '<td align="LEFT"><input type="text" name="PHASE_START" value=';
		print "\"$phase_start\"",' size="12"></td>';
		print '<th><a href="#" onClick="WindowOpen(phase_start_margin);return false;">Phase Start Margin</a>:</th>';
		print '<td align="LEFT"><input type="text" name="PHASE_START_MARGIN" value=';
		print "\"$phase_start_margin\"",' size="12"></td>';
		print '</tr><tr>';
		print '<td></td>';
		print '<th><a href="#" onClick="WindowOpen(phase_end);return false;">Phase End</a>:</th>';
		print '<td align="LEFT"><input type="text" name="PHASE_END" value=';
		print "\"$phase_end\"",' size="12"></td>';
		print '<th><a href="#" onClick="WindowOpen(phase_end_margin);return false;">Phase End Margin</a>:</th>';
		print '<td align="LEFT"><input type="text" name="PHASE_END_MARGIN" value=';
		print "\"$phase_end_margin\"",' size="12"></td>';
		print '</tr></table>';
	
                if($monitor_flag =~ /Y/i){
                       	%seen = ();
                       	@uniq = ();
                       	foreach $monitor_elem (@monitor_series) {
				$schk = 0;
				OUTER3:
				foreach $echk (@schdulable_list){
					if($monitor_elem =~ /$echk/){
						$schk++;
						last OUTER3;
					}
				}

				if($schk > 0){
					if($usint_on =~ /test/){
                               			push(@uniq, "<a href=\"$test_http/ocatdata2html.cgi\?$monitor_elem.$pass.$submitter\">$monitor_elem<\/a> ") unless $seen{$monitor_elem}++;
					}else{
                               			push(@uniq, "<a href=\"$usint_http/ocatdata2html.cgi\?$monitor_elem.$pass.$submitter\">$monitor_elem<\/a> ") unless $seen{$monitor_elem}++;
					}
				}
                       	}
                       	@monitor_series_list  = sort @uniq;
                }

###---NEW
##
##---- group ID window is now un-editable for all cases. you need CDO approval (2/24/06)
##---- ## indicates line disabled for this purpose
##
##		if($sp_user eq 'yes'){
##			print "If you want to set a group id, please type the id in Group ID field,";
##			print "and leave Monitoring Observation field as NO. If you want to set a ";
##			print "monitoring observation, select YES from the pull down menu, and Group ID ";
##			print "field blank. Then click 'Update' button to activate. If you want to change back, ";
##			print "set either Group ID to blank or Monitoring Observation to NO, and click ";
##			print "'Update' button.";
##			print "<br /><br />";
##		}
##
##		if($group_id && $monitor_flag =~ /Y/i){
##			print '<font color=red><b>You cannot have Group ID and Monitoring Observation';
##			print 'at the same time. Please change one or both of them.</b></font>';
##			print '<br /><br />';
##		}

		print '<table cellspacing="0" cellpadding="2">';
		print '<tr>';

		print '<th><a href="#" onClick="WindowOpen(group_id);return false;">Group ID</a>:</th>';
		print '<td>';

##		if($sp_user eq 'yes' && ($group_id =~ /\w/ || $group_id == '') && $dmonitor_flag ne 'YES'){
##
##			print textfield(-name=>'GROUP_ID', -value=>"$group_id", -size=>10);
##		}elsif($sp_user eq 'yes' && $group_id =~ /\w/ && $dmonitor_flag eq 'YES'){
##			print textfield(-name=>'GROUP_ID', -value=>"$group_id", -size=>10);
		if($group_id){
			print "$group_id";
			print "<input type='hidden' name='GROUP_ID' value=\"$group_id\">";
		}else{
			print '  No Group ID  ';
		}
		print '</td>';

		print '<th><a href="#" onClick="WindowOpen(monitor_flag);return false;">Monitoring Observation:  </th>';
		print '<td>';

		if($sp_user eq 'yes' && ($dmonitor_flag =~ /Y/i || $dmonitor_flag == '') 
				     && ($group_id =~ /\s+/ || $group_id eq '')){
			print popup_menu(-name=>'MONITOR_FLAG', -values=>['NO','YES','NULL'],
                        	-default=>"$dmonitor_flag",-override=>10000);
		}elsif($sp_user eq 'yes' && $dmonitor_flag =~ /Y/i && $group_id =~ /\w/ ){
			print popup_menu(-name=>'MONITOR_FLAG', -values=>['NO','YES','NULL'],
                        	-default=>"$dmonitor_flag",-override=>10000);
		}else{
			print "  $dmonitor_flag   </td>";
			print "<input type='hidden' name='MONITOR_FLAG' value=\"$monitor_flag\">";
		}
		print '</td>';

		print '<td>';
##		print submit(-name=>'Check',-value=>'     Update     ') ;
		print '</td></tr></table>';

		if($group_id){
			print "<br />Observations in the Group: @group<br />";
		}elsif($monitor_flag =~ /Y/i){
			print "<br /> Observations in the Monitoring: @monitor_series_list<br />";
		}else{
			print "<br />";
		}

		if($sp_user eq 'yes'){
	
			if($group_id =~ /No Group ID/ || $group_id !~ /\d/){
				print '<table cellspacing="8" cellpadding="5">';
		
				print '<th><a href="#" onClick="WindowOpen(pre_id);return false;">Follows ObsID#</a>:</th>';
				print '<td align="LEFT"><input type="text" name="PRE_ID" value="',"$pre_id",'" size="8"></td>';
				
				print '<th><a href="#" onClick="WindowOpen(pre_min_lead);return false;">Min Int<br />(pre_min_lead)</a>:</th>';
				print '<td align="LEFT"><input type="text" name="PRE_MIN_LEAD" value="',"$pre_min_lead",'" size="8"></td>';
			
				print '<th><a href="#" onClick="WindowOpen(pre_max_lead);return false;">Max Int<br />(pre_max_lead)</a>:</th>';
				print '<td align="LEFT"><input type="text" name="PRE_MAX_LEAD" value="',"$pre_max_lead",'" size="8"></td>';
				print '</tr></table>';
			}else{
        			print '<table cellspacing="8" cellpadding="5">';
		
        			print '<th><a href="#" onClick="WindowOpen(pre_id);return false;">Follows ObsID#</a>:</th>';
        			print '<td align="LEFT">',"$pre_id",'</td>';
			
        			print '<th><a href="#" onClick="WindowOpen(pre_min_lead);return false;">Min Int</a>:</th>';
        			print '<td align="LEFT">',"$pre_min_lead",'</td>';
			
        			print '<th><a href="#" onClick="WindowOpen(pre_max_lead);return false;">Max Int</a>:</th>';
        			print '<td align="LEFT">',"$pre_max_lead",'</td>';
        			print '</tr></table>';

				print "<input type=\"hidden\" name=\"PRE_ID\" value=\"$pre_id\"\>";
				print "<input type=\"hidden\" name=\"PRE_MIN_LEAD\" value=\"$pre_min_lead\"\>";
				print "<input type=\"hidden\" name=\"PRE_MAX_LEAD\" value=\"$pre_max_lead\"\>";


			}
		}else{
        		print '<table cellspacing="8" cellpadding="5">';
	
        		print '<th><a href="#" onClick="WindowOpen(pre_id);return false;">Follows ObsID#</a>:</th>';
        		print '<td align="LEFT">',"$pre_id",'</td>';
		
        		print '<th><a href="#" onClick="WindowOpen(pre_min_lead);return false;">Min Int<br />(pre_min_lead)</a>:</th>';
        		print '<td align="LEFT">',"$pre_min_lead",'</td>';
		
        		print '<th><a href="#" onClick="WindowOpen(pre_max_lead);return false;">Max Int<br />(pre_max_lead)</a>:</th>';
        		print '<td align="LEFT">',"$pre_max_lead",'</td>';
        		print '</tr></table>';

			print "<input type=\"hidden\" name=\"PRE_ID\" value=\"$pre_id\"\>";
			print "<input type=\"hidden\" name=\"PRE_MIN_LEAD\" value=\"$pre_min_lead\"\>";
			print "<input type=\"hidden\" name=\"PRE_MAX_LEAD\" value=\"$pre_max_lead\"\>";
		}

	
		print '<table cellspacing=6 cellpadding=5>';
		print '<tr>';
		print '<th><a href="#" onClick="WindowOpen(multitelescope);return false;">Coordinated Observation</a>:</th><td>';


		if($sp_user eq 'no' && $dmultitelescope ne 'YES'){
			print popup_menu(-name=>'MULTITELESCOPE', -value=>['NO','PREFERENCE'],
			 		-default=>"$dmultitelescope",-override=>100000);
		}else{
			print popup_menu(-name=>'MULTITELESCOPE', -value=>['NO','YES','PREFERENCE'],
			 		-default=>"$dmultitelescope",-override=>1000000);
		}

		print '</td>';
		print '<td></td>';
		print '<th><a href="#" onClick="WindowOpen(observatories);return false;">Observatories</a>:</th>';
		print '<td align="LEFT"><input type="text" name="OBSERVATORIES" value=';
		print "\"$observatories\"",' size="12"></td>';
                print '</tr>';

                print '<tr>';
		print '<th><a href="#" onClick="WindowOpen(multitelescope_interval);return false;">Max Coordination Offset</a>:</th>';
		print '<td align="LEFT"><input type="text" name="MULTITELESCOPE_INTERVAL" value=';
		print "\"$multitelescope_interval\"",' size="12"></td>';
	}
	print '</tr> </table>';

	print '<hr />';


#--------------------
#----- HRC Parameters
#--------------------

	if($sp_user =~ /no/ && $instrument =~ /ACIS/i){
#		print '<h2>HRC Parameters</h2>';
#		print '<table cellspacing="0" cellpadding="5">';
#		print '<tr><td></td>';
#	
#		print '<th><a href="#" onClick="WindowOpen(hrc_timing_mode);return false;">HRC Timing Mode</a>:</th><td>';
#		print "$dhrc_timing_mode";
#		print '</td>';
#		
#		print '<th><a href="#" onClick="WindowOpen(hrc_zero_block);return false;">Zero Block</a>:</th><td>';
#		print "$dhrc_zero_block";
#		print '</td><td>';
#		print '<th><a href="#" onClick="WindowOpen(hrc_si_mode);return false;">SI Mode</a>:</th>
#			<td align="LEFT">';
#		print "$hrc_si_mode";
#		print '</td></tr>';
#		print '</table>';
#		
		print "<input type=\"hidden\" name=\"HRC_TIMING_MODE\" value=\"$hrc_timing_mode\">";
		print "<input type=\"hidden\" name=\"HRC_ZERO_BLOCK\" value=\"$hrc_zero_block\">";
		print "<input type=\"hidden\" name=\"HRC_SI_MODE\" value=\"$hrc_si_mode\">";
	}else{

		print '<h2>HRC Parameters</h2>';
		print '<table cellspacing="0" cellpadding="5">';
		print '<tr><td></td>';
	
		print '<th><a href="#" onClick="WindowOpen(hrc_timing_mode);return false;">HRC Timing Mode</a>:</th><td>';
		print popup_menu(-name=>'HRC_TIMING_MODE', -value=>['NO','YES'], 
			 	-default=>"$dhrc_timing_mode", -override=>100000);
		print '</td>';
		
		print '<th><a href="#" onClick="WindowOpen(hrc_zero_block);return false;">Zero Block</a>:</th><td>';
		print popup_menu(-name=>'HRC_ZERO_BLOCK', -value=>['NO','YES'], 
			 	-default=>"$dhrc_zero_block", -override=>1000000);
		print '</td><td>';
	
		if($sp_user eq 'no'){
			print '<th><a href="#" onClick="WindowOpen(hrc_si_mode);return false;">SI Mode</a>:</th>
				<td align="LEFT">';
			print "$hrc_si_mode";
			print '</td></tr>';
			print "<input type=\"hidden\" name=\"HRC_SI_MODE\" value=\"$hrc_si_mode\">";
		}else{
			print '<th><a href="#" onClick="WindowOpen(hrc_si_mode);return false;">SI Mode</a>:</th>
				<td align="LEFT"><input type="text" name="HRC_SI_MODE" value="';
			print "$hrc_si_mode";
			print '" size="8"></td></tr>';
		}
	
		print '</table>';
	}
	
	print '<hr />';

#---------------------
#----- ACIS Parameters
#--------------------

	if($sp_user =~ /no/ && $instrument =~ /HRC/i){
#		print '<h2>ACIS Parameters</h2>';
#		print '<table cellspacing="0" cellpadding="5">';
#		print '<tr>';
#		
#		print '<th><a href="#" onClick="WindowOpen(exp_mode);return false;">ACIS Exposure Mode</a>:</th><td>';
#		print "$exp_mode";
#		
#		print '</td><th><a href="#" onClick="WindowOpen(bep_pack);return false;">Event TM Format</a>:</th><td>';
#		print "$bep_pack";
#		print '</td>';
#	
#print <<ENDOFhtml;
#	
#		<th><a href="#" onClick="WindowOpen(frame_time);return false;">Frame Time</a>:</th>
#		<td align="LEFT">$frame_time</td></tr>
#
#ENDOFhtml
#		print '<tr>';
#		print '<td></td><td></td><td></td><td></td>
#			<th><a href="#" onClick="WindowOpen(most_efficient);return false;">Most Efficient</a>:</th><td>';
#	
#		print "$dmost_efficient";
#		print '</td>';
#		print '</tr></table>';
#		
#		if($sp_user eq 'yes'){
#			print '<table cellspacing="0" cellpadding="5">';
#			print '<tr><td></td>';
#
#			print '<th><a href="#" onClick="WindowOpen(standard_chips);return false;">Standard Chips</a>:</th><td>';
#			print "$dstandard_chips";
#			print '</td><td></td><td></td>';
#			print '<th><a href="#" onClick="WindowOpen(fep);return false;">FEP</a>:</th><td>';
#			print "$fep";
#			print '</td>';
#			print '</tr></table>';
#		}
#		print '<table cellspacing="4" cellpadding="6" border ="1">';
##		print '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>';
#		print '<tr><td></td><td></td><td></td><td></td>';
#	
#
#		print '<th><a href="#" onClick="WindowOpen(ccdi0_on);return false;">I0</a>:</th> <td>',"$dccdi0_on",'</td>';
#		print '<th><a href="#" onClick="WindowOpen(ccdi1_on);return false;">I1</a>:</th> <td>',"$dccdi1_on",'</td>';
#	
##		print '<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>';
#		print '<td></td><td></td><td></td><td></td>';
##		print '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>';
#		print '<tr><td></td><td></td><td></td><td></td>';
#	
#		print '<th><a href="#" onClick="WindowOpen(ccdi2_on);return false;">I2</a>:</th> <td>',"$dccdi2_on",'</td>';
#		print '<th><a href="#" onClick="WindowOpen(ccdi3_on);return false;">I3</a>:</th> <td>',"$dccdi3_on",'</td>';
#		
##		print '<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>';
#		print '<td></td><td></td><td></td><td></td></tr>';
#	
#		print '<tr>';
#	
#	
#		print '<th><a href="#" onClick="WindowOpen(ccds0_on);return false;">S0</a>:</th> <td>',"$dccds0_on",'</td>';
#		print '<th><a href="#" onClick="WindowOpen(ccds1_on);return false;">S1</a>:</th> <td>',"$dccds1_on",'</td>';
#		print '<th><a href="#" onClick="WindowOpen(ccds2_on);return false;">S2</a>:</th> <td>',"$dccds2_on",'</td>';
#		print '<th><a href="#" onClick="WindowOpen(ccds3_on);return false;">S3</a>:</th> <td>',"$dccds3_on",'</td>';
#		print '<th><a href="#" onClick="WindowOpen(ccds4_on);return false;">S4</a>:</th> <td>',"$dccds4_on",'</td>';
#		print '<th><a href="#" onClick="WindowOpen(ccds5_on);return false;">S5</a>:</th> <td>',"$dccds5_on",'</td>';
#		
#		print '</tr></table><p>';
#		
#		print '<table cellspacing="0" cellpadding="5">';
#		print '<tr>';
#		print '<Th><a href="#" onClick="WindowOpen(subarray);return false;">Use Subarray</a>:</Th>';
#		print '<td>';
#		print "$dsubarray";
#	
#		print '</td><th colspan=4>&#160</th></tr><tr>';
#		
#		print '<th><a href="#" onClick="WindowOpen(subarray_start_row);return false;">Start</a>:</th>
#			<td align="LEFT">',"$subarray_start_row",'</td>';
#		
#		print '<th><a href="#" onClick="WindowOpen(subarray_row_count);return false;">Rows</a>:</th>
#			<td align="LEFT">',"$subarray_row_count",'</td>';
#	
#		print '<th><a href="#" onClick="WindowOpen(subarray_frame_time);return false;">Frame Time</a>:</th>
#			<td align="LEFT">',"$subarray_frame_time",'</td>';
#		
#		print '</td></tr>';
#		print '<tr>';
#	
#		print '<th><a href="#" onClick="WindowOpen(duty_cycle);return false;">Duty Cycle</a>:</th><td>';
#		print "$dduty_cycle";
#		print '</td>';
#		print '</tr><tr>';
#
#print <<ENDOFhtml;
#	
#		<th><a href="#" onClick="WindowOpen(secondary_exp_count);return false;">Number</a>:</th>
#			<td align="LEFT">$secondary_exp_count</td>
#		<th><a href="#" onClick="WindowOpen(primary_exp_time);return false;">Tprimary</a>:</th>
#			<td align="LEFT">$primary_exp_time</td>
#		<th><a href="#" onClick="WindowOpen(secondary_exp_time);return false;">Tsecondary</a>:</th>
#			<td align="LEFT">$secondary_exp_time</td>
#		</tr> <tr>
#	
#ENDOFhtml
#
#		print '<th><a href="#" onClick="WindowOpen(onchip_sum);return false;">Onchip Summing</a>:</th><td>';
#		print "$donchip_sum";
#		print '</td>';
#
#print <<ENDOFhtml;
#	
#		<th><a href="#" onClick="WindowOpen(onchip_row_count);return false;">Rows</a>:</th>
#		<td align="LEFT">$onchip_row_count</td>
#		<th><a href="#" onClick="WindowOpen(onchip_column_count);return false;">Columns</a>:</th>
#		<td align="LEFT">$onchip_column_count</td>
#		</tr>
#		<tr>
#ENDOFhtml
#		print '<th><a href="#" onClick="WindowOpen(eventfilter);return false;">Energy Filter</a>:</th><td>';
#		print "$deventfilter";
#		print '</td>';
#
#print <<ENDOFhtml;
#	
#		<th><a href="#" onClick="WindowOpen(eventfilter_lower);return false;">Lowest Energy</a>:</th>
#			<td align="LEFT">$eventfilter_lower</td>
#		<th><a href="#" onClick="WindowOpen(eventfilter_higher);return false;">Energy Range</a>:</th>
#			<td align="LEFT">$eventfilter_higher</td>
#		</tr> 
#
#ENDOFhtml
#
#		if($sp_user eq 'yes'){
#			print '<tr><th><a href="#" onClick="WindowOpen(bias_request);return false;">Bias</a>:</th><td>';
#			print "$bias_request";
#			print '</td><th><a href="#" onClick="WindowOpen(frequency);return false;">Bias Frequency</a>:</th><td>';
#			print "$frequency";
#			print '</td><th><a href="#" onClick="WindowOpen(bias_after);return false;">Bias After</a>:</th><td>';
#			print "$bias_after";
#	
#			print '</td></tr>';
#		}
#		print '</table>';
#
		print "<input type=\"hidden\" name=\"EXP_MODE\"   		value=\"$exp_mode\">";
		print "<input type=\"hidden\" name=\"BEP_PACK\"   		value=\"$bep_pack\">";
		print "<input type=\"hidden\" name=\"FRAME_TIME\" 		value=\"$frame_time\">";
		print "<input type=\"hidden\" name=\"MOST_EFFICIENT\" 		value=\"$most_efficient\">";
		print "<input type=\"hidden\" name=\"CCDI0_ON\" 		value=\"$ccdi0_on\">";
		print "<input type=\"hidden\" name=\"CCDI1_ON\" 		value=\"$ccdi1_on\">";
		print "<input type=\"hidden\" name=\"CCDI2_ON\" 		value=\"$ccdi2_on\">";
		print "<input type=\"hidden\" name=\"CCDI3_ON\" 		value=\"$ccdi3_on\">";
		print "<input type=\"hidden\" name=\"CCDS0_ON\" 		value=\"$ccds0_on\">";
		print "<input type=\"hidden\" name=\"CCDS1_ON\" 		value=\"$ccds1_on\">";
		print "<input type=\"hidden\" name=\"CCDS2_ON\" 		value=\"$ccds2_on\">";
		print "<input type=\"hidden\" name=\"CCDS3_ON\" 		value=\"$ccds3_on\">";
		print "<input type=\"hidden\" name=\"CCDS4_ON\" 		value=\"$ccds4_on\">";
		print "<input type=\"hidden\" name=\"CCDS5_ON\" 		value=\"$ccds5_on\">";
		print "<input type=\"hidden\" name=\"SUBARRAY\" 		value=\"$subarray\">";
		print "<input type=\"hidden\" name=\"SUBARRAY_START_ROW\" 	value=\"$subarray_start_row\">";
		print "<input type=\"hidden\" name=\"SUBARRAY_ROW_COUNT\" 	value=\"$subarray_row_count\">";
		print "<input type=\"hidden\" name=\"SUBARRAY_FRAME_TIME\" 	value=\"$subarray_frame_time\">";
		print "<input type=\"hidden\" name=\"DUTY_CYCLE\" 		value=\"$duty_cycle\">";
		print "<input type=\"hidden\" name=\"SECONDARY_EXP_COUNT\" 	value=\"$secondary_exp_count\">";
		print "<input type=\"hidden\" name=\"PRIMARY_EXP_TIME\" 	value=\"$primary_exp_time\">";
		print "<input type=\"hidden\" name=\"SECONDARY_EXP_TIME\" 	value=\"$secondary_exp_time\">";
		print "<input type=\"hidden\" name=\"ONCHIP_SUM\" 		value=\"$onchip_sum\">";
		print "<input type=\"hidden\" name=\"ONCHIP_ROW_COUNT\" 	value=\"$onchip_row_count\">";
		print "<input type=\"hidden\" name=\"ONCHIP_COLUMN_COUNT\" 	value=\"$onchip_column_count\">";
		print "<input type=\"hidden\" name=\"EVENTFILTER\" 		value=\"$eventfilter\">";
		print "<input type=\"hidden\" name=\"EVENTFILTER_LOWER\" 	value=\"$eventfilter_lower\">";
		print "<input type=\"hidden\" name=\"EVENTFILTER_HIGHER\" 	value=\"$eventfilter_higher\">";
#
#-- added 03/29/11
#
		print "<input type=\"hidden\" name=\"MULTIPLE_SPECTRAL_LINES\" 	value=\"$multiple_spectral_lines\">";
		print "<input type=\"hidden\" name=\"SPECTRA_MAX_COUNT\" 	value=\"$spectra_max_count\">";

		print "<input type=\"hidden\" name=\"BIAS_REQUEST\" 		value=\"$bias_request\">";
		print "<input type=\"hidden\" name=\"FREQUENCY\" 		value=\"$frequency\">";
		print "<input type=\"hidden\" name=\"BIAS_AFTER\" 		value=\"$bias_after\">";

	}else{
#---------------------
		print '<h2>ACIS Parameters</h2>';
		print '<table cellspacing="0" cellpadding="5">';
		print '<tr>';
		
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(exp_mode);return false;"><font color=white>ACIS Exposure Mode</font></a>:</th><td>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(exp_mode);return false;">ACIS Exposure Mode</a>:</th><td>';
		}
		print popup_menu(-name=>'EXP_MODE', -value=>['NULL','TE','CC'], -default=>"$exp_mode", -override=>100000);
		
		if($sp_user eq 'no'){
			print '</td><th bgcolor="blue"><a href="#" onClick="WindowOpen(bep_pack);return false;"><font color=white>Event TM Format</font></a>:</th><td>';
		}else{
			print '</td><th><a href="#" onClick="WindowOpen(bep_pack);return false;">Event TM Format</a>:</th><td>';
		}
        if($instrument =~ /ACIS/i){
		    print popup_menu(-name=>'BEP_PACK', -value=>['F','VF','F+B','G'], 
			 	-default=>"$bep_pack", -override=>100000);
        }else{
		    print popup_menu(-name=>'BEP_PACK', -value=>['NULL','F','VF','F+B','G'], 
			 	-default=>"$bep_pack", -override=>100000);
        }
		print '</td>';
	
	
		print '<th><a href="#" onClick="WindowOpen(frame_time);return false;">Frame Time</a>:</th>';
#		print "<td align='LEFT'><input type='text' name='FRAME_TIME' value=\"$frame_time" size=12 </td></tr>";

		print "<td align='LEFT'>";
		print textfield(-name=>'FRAME_TIME', -value=>"$frame_time",-size=>12, -override=>1000);
		print "</td></tr>";

		print '<tr>';
		print '<td></td><td></td><td></td><td></td>
			<th><a href="#" onClick="WindowOpen(most_efficient);return false;">Most Efficient</a>:</th><td>';
	
		print popup_menu(-name=>'MOST_EFFICIENT', -value=>['NULL','YES','NO'],
			 	-default=>"$dmost_efficient", -override=>10000);
		print '</td>';
		print '</tr></table>';
		
		print '<table cellspacing="0" cellpadding="5">';
		print '<tr><td></td>';
	
	
		print '<th><a href="#" onClick="WindowOpen(fep);return false;">FEP</a>:</th><td>';
                       print "$fep";
		print '</td><td></td><td></td>';
		print '<th><a href="#" onClick="WindowOpen(dropped_chip_count);return false;">Dropped Chip Count</a>:</th><td>';
		print "$dropped_chip_count";

		print '</td>';
		print '</tr></table>';

		print "<input type=\"hidden\" name=\"FEP\" value=\"$fep\">";
		print "<input type=\"hidden\" name=\"DROPPED_CHIP_COUNT\" value=\"$dropped_chip_count\">";
	
		print '<table cellspacing="0" cellpadding="1">';
		print '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>';
		
	
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccdi0_on);return false;"><font color=white>I0</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccdi0_on);return false;">I0</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDI0_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccdi0_on",-override=>100000),'</td>';
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccdi1_on);return false;"><font color=white>I1</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccdi1_on);return false;">I1</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDI1_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccdi1_on",-override=>1000000),'</td>';
		
		print '<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>';
		print '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>';
		
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccdi2_on);return false;"><font color=white>I2</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccdi2_on);return false;">I2</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDI2_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccdi2_on",-override=>100000),'</td>';
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccdi3_on);return false;"><font color=white>I3</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccdi3_on);return false;">I3</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDI3_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccdi3_on",-override=>100000),'</td>';
		
		print '<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>';
		
		print '<tr>';
		
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccds0_on);return false;"><font color=white>S0</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccds0_on);return false;">S0</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDS0_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccds0_on",-override=>100000),'</td>';
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccds1_on);return false;"><font color=white>S1</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccds1_on);return false;">S1</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDS1_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccds1_on",-override=>100000),'</td>';
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccds2_on);return false;"><font color=white>S2</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccds2_on);return false;">S2</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDS2_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccds2_on",-override=>10000),'</td>';
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccds3_on);return false;"><font color=white>S3</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccds3_on);return false;">S3</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDS3_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccds3_on",-override=>1000000),'</td>';
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccds4_on);return false;"><font color=white>S4</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccds4_on);return false;">S4</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDS4_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccds4_on",-override=>100000),'</td>';
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(ccds5_on);return false;"><font color=white>S5</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(ccds5_on);return false;">S5</a>:</th>';
		}
		print '<td>',popup_menu(-name=>'CCDS5_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
							-default=>"$dccds5_on",-override=>100000),'</td>';
		
		print '</tr></table><p>';
		
		print '<table cellspacing="0" cellpadding="5">';
		print '<tr>';
		if($sp_user eq 'no'){
			print '<Th bgcolor="blue"><a href="#" onClick="WindowOpen(subarray);return false;"><font color=white>Use Subarray</font></a>:</Th>';
		}else{
			print '<Th><a href="#" onClick="WindowOpen(subarray);return false;">Use Subarray</a>:</Th>';
		}
		print '<td>';
		print popup_menu(-name=>'SUBARRAY', -value=>['NO', 'YES'],
			 	-default=>"$dsubarray", -override=>100000);
	
		print '</td><td colspan=4><b>Please fill the next two entries, if you select YES.<br /> You can find the old default 
			subarrays at <a href="#" onClick="WindowOpen(subarray);return false;">Subarray Setting</a>.</b>
			</td></tr><tr>';
		
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(subarray_start_row);return false;"><font color=white>Start</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(subarray_start_row);return false;">Start</a>:</th>';
		}
		print '<td align="LEFT"><input type="text" name="SUBARRAY_START_ROW" value="',"$subarray_start_row",'" size="12"></td>';
		
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(subarray_row_count);return false;"><font color=white>Rows</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(subarray_row_count);return false;">Rows</a>:</th>';
		}
		print '<td align="LEFT"><input type="text" name="SUBARRAY_ROW_COUNT" value="',"$subarray_row_count",'" size="12"></td>';
		
#		if($sp_user eq 'no'){
#			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(subarray_frame_time);return false;"><font color=white>Frame Time</font></a>:</th>';
#		}else{
#			print '<th><a href="#" onClick="WindowOpen(subarray_frame_time);return false;">Frame Time</a>:</th>';
#		}
#		print '<td align="LEFT"><input type="text" name="SUBARRAY_FRAME_TIME" value="',"$subarray_frame_time",'" size="12"></td>';
		
		print '</td></tr>';
		print '<tr>';
	
		print '<th><a href="#" onClick="WindowOpen(duty_cycle);return false;">Duty Cycle</a>:</th><td>';
		print popup_menu(-name=>'DUTY_CYCLE', -value=>['NULL','YES','NO'], 
			 	-default=>"$dduty_cycle", -override=>100000);
		print '</td>';
		print '<th colspan=4><b>If you selected YES, please fill the next two entries</b></th>';
		print '</tr><tr>';

		print '<th><a href="#" onClick="WindowOpen(secondary_exp_count);return false;">Number</a>:</th>';
		print '<td align="LEFT"><input type="text" name="SECONDARY_EXP_COUNT" value=';
		print "\"$secondary_exp_count\"", ' size="12"></td>';
		print '<th><a href="#" onClick="WindowOpen(primary_exp_time);return false;">Tprimary</a>:</th>';
		print '<td align="LEFT"><input type="text" name="PRIMARY_EXP_TIME" value=';
		print "\"$primary_exp_time\"", ' size="12"></td>';
#		print '<th><a href="#" onClick="WindowOpen(secondary_exp_time);return false;">Tsecondary</a>:</th>';
#		print '<td align="LEFT"><input type="text" name="SECONDARY_EXP_TIME" value=';
#		print "\"$secondary_exp_time\"",' size="12"></td>';
		print '</tr> <tr>';

		print '<th><a href="#" onClick="WindowOpen(onchip_sum);return false;">Onchip Summing</a>:</th><td>';
		print popup_menu(-name=>'ONCHIP_SUM', -value=>['NULL','YES','NO'], 
			 	-default=>"$donchip_sum", -override=>100000);
		print '</td>';

		print '<th><a href="#" onClick="WindowOpen(onchip_row_count);return false;">Rows</a>:';
		print '</th><td align="LEFT"><input type="text" name="ONCHIP_ROW_COUNT" value=';
		print "\"$onchip_row_count\"", ' size="12"></td>';
		print '<th><a href="#" onClick="WindowOpen(onchip_column_count);return false;">Columns</a>:';
		print '</th><td align="LEFT"><input type="text" name="ONCHIP_COLUMN_COUNT" value=';
		print "\"$onchip_column_count\"", ' size="12"></td>';
		print '</tr>';
		print '<tr>';

		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(eventfilter);return false;"><font color=white>Energy Filter</font></a>:</th><td>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(eventfilter);return false;">Energy Filter</a>:</th><td>';
		}
		print popup_menu(-name=>'EVENTFILTER', -value=>['NULL','YES','NO'], 
			 	-default=>"$deventfilter", -override=>100000);
		print '</td>';
	

		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(eventfilter_lower);return false;"><font color=white>Lowest Energy</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(eventfilter_lower);return false;">Lowest Energy</a>:</th>';
		}
		print '<td align="LEFT"><input type="text" name="EVENTFILTER_LOWER" value="';
		print "$eventfilter_lower";
		print '" size="12"></td>';
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(eventfilter_higher);return false;"><font color=white>Energy Range</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(eventfilter_higher);return false;">Energy Range</a>:</th>';
		}
		print '<td align="LEFT"><input type="text" name="EVENTFILTER_HIGHER" value="';
		print "$eventfilter_higher";
		print '" size="12"></td>';
                if($deventfilter =~ /YES/i){
                        $high_energy = $eventfilter_lower + $eventfilter_higher;
                        print "<td><b> = Highest Energy:</b> $high_energy</td>";
                }

		print '</tr><tr> ';

#
#--- added 03/29/11 ##############
#
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(multiple_spectral_lines);return false;"><font color=white>Multiple Spectral Lines</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(multiple_spectral_lines);return false;">Multiple Spectral Lines</a>:</th>';
		}
		print '<td align="LEFT">';
		print popup_menu(-name=>'MULTIPLE_SPECTRAL_LINES', -value=>['NULL','NO','YES'], -default=>"$dmultiple_spectral_lines",-override=>10000);
		print '</td>';
		
		if($sp_user eq 'no'){
			print '<th bgcolor="blue"><a href="#" onClick="WindowOpen(spectra_max_count);return false;"><font color=white>Spectra Max Count</font></a>:</th>';
		}else{
			print '<th><a href="#" onClick="WindowOpen(spectra_max_count);return false;">Spectra Max Count</a>:</th>';
		}
		print '<td align="LEFT"><input type="text" name="SPECTRA_MAX_COUNT" value="';
		print "$spectra_max_count";
		print '" size="12"></td>';
		print '</tr> ';

#################




	

#		if($sp_user eq 'yes'){
#			print '<tr><th><a href="#" onClick="WindowOpen(bias_request);return false;">Bias</a>:</th><td>';
#			print textfield(-name=>"BIAS_REQUEST", -value=>"$bias_request", -size=>'12');
#			print popup_menu(-name=>"BIAS_REQUEST", -value=>['YES', 'NONE','NO'],
#                                -default=>"$bias_request", -override=>100000);
#			print '</td><th><a href="#" onClick="WindowOpen(frequency);return false;">Bias Frequency</a>:</th><td>';
#			print textfield(-name=>"FREQUENCY", -value=>"$frequency", -size=>'12');
#			print '</td><th><a href="#" onClick="WindowOpen(bias_after);return false;">Bias After</a>:</th><td>';
#			print textfield(-name=>"BIAS_AFTER", -value=>"$bias_after", -size=>'12');
#			print '</td></tr>';
#		}
		print '</table>';
	}

#------------------------------------------------
#-------- Acis Window Constraint Case starts here
#------------------------------------------------

	if($sp_user eq 'no' && $instrument =~ /HRC/i){
		print '<hr />';
		print '<h2> ACIS Window Constraints</h2>';
		print '<table><tr><th>';
		print '<a href="#" onClick="WindowOpen(spwindow);return false;">Window Filter</a>:';
		print '</th><td>';
		print "$dspwindow";
		print '</td></tr></table>';
		print '<br />';
	
		if($dspwindow =~ /YES/i){
			print '<table cellspacing="0" cellpadding="3">';
			for($k = 0; $k < $aciswin_no; $k++){
#
#----this line was removed: <th><a href="#" onClick="WindowOpen(include_flag);return false;">Photon Inclusion</a></th>
#
				print '<tr><th><a href="#" onClick="WindowOpen(ordr);return false;">Ordr</a></th>
					<th><a href="#" onClick="WindowOpen(chip);return false;">Chip</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_start_row);return false;">Start Row</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_start_column);return false;">Start Column</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_height);return false;">Height</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_width);return false;">Width</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_lower_threshold);return false;">Lowest Energy</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_pha_range);return false;">Energy Range</a></th>
					<th><a href="#" onClick="WindowOpen(spwindow_sample);return false;">Sample Rate</a></th>
					<th><a href="#" onClick="WindowOpen(multiple_spectral_lines);return false;">Multiple Spectral Lines</a></th>
					<th><a href="#" onClick="WindowOpen(spectra_max_count);return false;">Spectra Max Count</a></th>
					<th></th></tr>';
				print '<tr><td align=center><b>';
				print "$ordr[$k]";
				print '</b></td><td align=center>';
		
				$taciswin_id      = 'ACISWIN_ID'."$k";
				$tordr            = 'ORDR'."$k";
				$tchip            = 'CHIP'."$k";
#				$tinclude_flag    = 'INCLUDE_FLAG'."$k";
				$tstart_row       = 'START_ROW'."$k";
				$tstart_column    = 'START_COLUMN'."$k";
				$theight          = 'HEIGHT'."$k";
				$twidth           = 'WIDTH'."$k";
				$tlower_threshold = 'LOWER_THRESHOLD'."$k";
				$tpha_range       = 'PHA_RANGE'."$k";
				$tsample          = 'SAMPLE'."$k";
	
				print "$chip[$k]";
				print "</td><td align=center>";
#				print "$dinclude_flag[$k]";
#				print "</td><td align=center>";
				print "$start_row[$k]";
				print "</td><td align=center>";
				print "$start_column[$k]";
				print "</td><td align=center>";
				print "$height[$k]";
				print "</td><td align=center>";
				print "$width[$k]";
				print "$lower_threshold[$k]";
				print "</td><td align=middle>";
				print "$pha_range[$k]";
				print '</td><td align=center>';
				print "$sample[$k]";
				print "</td><td align=center>";
		
				print '</td></tr>';

                        	print "<input type=\"hidden\" name=\"$taciswin_id\" value=\"$aciswin_id[$k]\"\>";
                        	print "<input type=\"hidden\" name=\"$tordr\" value=\"$ordr[$k]\"\>";
                        	print "<input type=\"hidden\" name=\"$tchip\" value=\"$chip[$k]\"\>";
                        	print "<input type=\"hidden\" name=\"$tinclude_flag\" value=\"$dinclude_flag[$k]\"\>";
                        	print "<input type=\"hidden\" name=\"$tstart_row\" value=\"$start_row[$k]\"\>";
                        	print "<input type=\"hidden\" name=\"$tstart_column\" value=\"$start_column[$k]\"\>";
                        	print "<input type=\"hidden\" name=\"$theight\" value=\"$height[$k]\"\>";
                        	print "<input type=\"hidden\" name=\"$twidth\" value=\"$width[$k]\"\>";
                        	print "<input type=\"hidden\" name=\"$tpha_range\" value=\"$pha_range[$k]\"\>";
                        	print "<input type=\"hidden\" name=\"$tsample\" value=\"$sample[$k]\"\>";
			}
			print '</table>';

			print "<input type=\"hidden\" name=\"SPWINDOW\" value=\"$spwindow\">";
                	print "<input type=\"hidden\" name=\"ACISWIN_NO\" value=\"$aciswin_no\">";
		}else{
			print "<h3>No ACIS  Window Constraints</h3>";

			for($k = 0; $k < $aciswin_no; $k++){
		
				$taciswin_id      = 'ACISWIN_ID'."$k";
				$tordr            = 'ORDR'."$k";
				$tchip            = 'CHIP'."$k";
#				$tinclude_flag    = 'INCLUDE_FLAG'."$k";
				$tstart_row       = 'START_ROW'."$k";
				$tstart_column    = 'START_COLUMN'."$k";
				$theight          = 'HEIGHT'."$k";
				$twidth           = 'WIDTH'."$k";
				$tlower_threshold = 'LOWER_THRESHOLD'."$k";
				$tpha_range       = 'PHA_RANGE'."$k";
				$tsample          = 'SAMPLE'."$k";
	
                       		print "<input type=\"hidden\" name=\"$taciswin_id\" value=\"$aciswin_id[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tordr\" value=\"$ordr[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tchip\" value=\"$chip[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tinclude_flag\" value=\"$dinclude_flag[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tstart_row\" value=\"$start_row[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tstart_column\" value=\"$start_column[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$theight\" value=\"$height[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$twidth\" value=\"$width[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tpha_range\" value=\"$pha_range[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tsample\" value=\"$sample[$k]\"\>";
			}
                       	print "<input type=\"hidden\" name=\"ACISWIN_NO\" value=\"$aciswin_no\"\>";
		}

	}else{

#################
#----  sp_user is yes etc: you can edit ACIS Window Constrain Section
#################

#
#--- ACIS window Constraints: some values are linked to eventfilter_lower condition
#

                print '<hr />';
                print '<h2> ACIS Window Constraints</h2>';
                print '<table><tr><th>';
                print '<a href="#" onClick="WindowOpen(spwindow);return false;">Window Filter</a>:';
                print '</th><td>';

#
#---awc_l_th: acis window constraint lowest energy indicator: if 1 it is exceeded 0.5 keV
#

		if($aciswin_no eq ''){
			$aciswin_no = 0;
		}

		if($awc_cnt eq ''){
			$awc_cnt = 0;
		}
                if($eventfilter_lower > 0.5 || $awc_l_th == 1){
                                $dspwindow = 'YES';
                }

                print popup_menu(-name=>'SPWINDOW', -value=>['NULL','YES','NO'],-default=>"$dspwindow", -override=>10000);
		print '<input type="submit" name="Check" value="Update">';
                print '</td></tr></table>';

		if($dspwindow =~ /YES/i){

                	print '<br />';

			$chip_chk = 0;			#---- used for eventfilter_lower > 0.5
#
#--- check which CCDs are ON
#
                       	@open_ccd = ();                                 #--- a list of ccd abled
                       	$ocnt     = 0;                                  #--- # of ccd abled
                       	for($m = 0; $m < 4; $m++){
                               	$name = 'ccdi'."$m".'_on';
                               	if(${$name} !~ /N/i && ${$name} !~ /NO/i && ${$name} !~ /NULL/){
                                       	$name2 = 'I'."$m";
                                       	push(@open_ccd, $name2);
                                       	$ocnt++;
                               	}
                       	}
                       	for($m = 0; $m < 6; $m++){
                               	$name = 'ccds'."$m".'_on';
                               	if(${$name} !~ /N/i && ${$name} !~ /NO/i && ${$name} !~ /NULL/){
                                       	$name2 = 'S'."$m";
                                       	push(@open_ccd, $name2);
                                       	$ocnt++;
                               	}
                       	}


#
#--- if lowest energy is > 0.5 keV check # of CCD abled
#
                	OUTER:
                	if($eventfilter_lower > 0.5 || $awc_l_th == 1){
                        	print '<font color=red>';
                        	if($eventfilter_lower > 0.5 && $awc_l_th == 0){
                                	print 'Energy Filter Lowest Energy is larger than 0.5 keV. ';
                        	}elsif($eventfilter_lower > 0.5 && $awc_l_th == 1){
                                	print 'Energy Filter Lowest Energy and ACIS Window Constraint Lowest Energy are larger than 0.5 keV. ';
                        	}elsif($eventfilter_lower <= 0.5 && $awc_l_th == 1){
                                	print 'ACIS Window Constraint Lowest Energy is larger than 0.5 keV. ';
                        	}
                        	print 'Please check all Spatial Window parameters of each CCD.<br />';
                        	print 'If you want to remove all the window constraints, change Lowest Energy ';
                        	print 'to less than 0.5keV, and set Window Filter to No or Null, ';
                        	print 'then Submit the change using the "Submit" button at the bottom of the page.';
                        	print '</b></font>';
                        	print "<a href=\"$usint_http/eventfilter_answer.html\" target='blank'>Why did this happen?</a>";
                        	print '</font>';
                        	print '<br />';

#
#--- check how many ccds match with opened ccds
#

				@un_opened = ();
				OUTER:
				foreach $ent (@open_ccd){
					for($k = 0; $k < $aciswin_no; $k++){
						if($chip[$k] =~ /NULL/i){
							next OUTER;
						}
						if($ent =~ /$chip[$k]/i){
							next OUTER;
						}
					}
					push(@un_opened, $ent);
					$chip_chk++;
				}
                	}
	
                	print '<br />';
                	print 'If you want to modify the number of ranks, change Window Filter above to "YES", ';
                	print 'then change the rank entry below, and press "Add New Window Entry"';
                	print '<br /><br />';
                	print '<b><a href="#" onClick="WindowOpen(ordr);return false;">Rank</a></b>: ';
                	print '<spacer type=horizontal size=30>';
	
                	print '<spacer type=horizontal size=50>';
                	print submit(-name=>'Check',-value=>'     Add New Window Entry     ') ;
                	print '<br /><br />';
                	print 'If you are changing any of following entries, make sure ';
                	print 'Window Filter above is set to "YES".<br />';
                	print 'Otherwise, all changes are automatically nullified ';
                	print 'when you submit the changes.';
                        print "<p style='padding-right:300px;padding-bottom:10px'>";
                        print '<b>NOTE</b>: All windows are now <b>"Exclusion"</b> windows. What were formerly inclusion';
			print 'windows are just exclusion windows with a sample value of 1.';
                        print "<br /><br />";
			print 'For each pixel, the software looks at the specified windows in order';
			print '(starting with 0). When it finds a window which has the pixel within';
			print 'its range, it uses the specification in that window, ignoring later';
			print 'windows in the list.';
                        print "<br /><br />";
			print 'So you want an exclusion window for the 128 x 128 rectangle, with a';
			print 'sample value of 1, followed by an exclusion window for 1024 x 1024,';
			print 'with a sample value of 0.';
                	print '</p>';
	
                	if($eventfilter_lower > 0.5 || $awc_l_th == 1){
                        	print 'If you change one or more CCD from YES to NO or the other way around in ACIS Parameters section, ';
                        	print '<br />';
                        	print 'this action will affect the ranks below. After changing the CCD status, please click "Update" button at the bottom of the page ';
                        	print 'to make the effect to take place.';
                        	print '<br /><br />';
                	}
	
                	print '<table cellspacing="0" cellpadding="3">';

                	$add_extra_line = 0;
                	$reduced_ccd_no = 0;
                	$org_aciswin_no = $aciswin_no;
#
#--- if eventfilter lower <= 0.5 keV and window filter is set to Null, reduce all window constraints to Null state
#

			if($eventfilter_lower > 0.5 || $awc_l_th == 1){ 
				if($chip[$aciswin_no -1]=~ /N/i){
					$awc_cnt        = 0;
					$aciswin_no     = $chip_chk;
					$org_aciswin_no = $aciswin_no;
				}else{
					$awc_cnt        = $aciswin_no;
					$aciswin_no    += $chip_chk;
					$org_aciswin_no = $aciswin_no;
				}

#
#--- if eventfilter_lower > 0.5, lower_threshold must be at least equal to eventfilter_lower 
#
				for($k = 0; $k < $aciswin_no; $k++){
					if($lower_threshold[$k] < $eventfilter_lower){
						$lower_threshold[$k] = $eventfilter_lower;
					}
				}

				for($k = 0; $k < $chip_chk; $k++){
					$j = $awc_cnt + $k;
					$aciswin_id[$j]	     = $aciswin_id[$j-1] +1;
					$ordr[$j]            = $j + 1;
					$chip[$j]            = $un_opened[$k];
					$dinclude_flag[$j]   = 'INCLUDE';
					$start_row[$j]       = 1;
					$start_column[$j]    = 1;
					$height[$j]          = 1024;
					$width[$j]           = 1024;
					$lower_threshold[$j] = $eventfilter_lower;
					$pha_range[$j]       = $eventfilter_higher;
					$sample[$j]          = 1;
					$awc_ind	     = 1;
				}
			}

#
#---- when whidow filter is changed from no to yes, add one empty acis window constraint line
#---- with one of opened CCD (fist in the line)
#
			if($aciswin_no !~ /\d/ || $aciswin_no == 0){
				$aciswin_no = 1;
				$ordr[0] = 1;
				$chip[0] = $open_ccd[0];
			}
#
#--- adding one extra entry (consequence of "Add New Window Entry" pressed)
#

			if($add_window_rank == 1 &&  $ordr[$aciswin_no -1] !~ /\d/){
				$ordr[$aciswin_no -1] = 1;
				$chip[$aciswin_no -1] = $open_ccd[0];
				$add_window_rank = 0;
			}
#
#----this line was removed: <th><a href="#" onClick="WindowOpen(include_flag);return false;">Photon Inclusion</a></th>
#
			print '<tr><th><a href="#" onClick="WindowOpen(ordr);return false;">Ordr</a></th>
			<th><a href="#" onClick="WindowOpen(chip);return false;">Chip</a></th>
			<th><a href="#" onClick="WindowOpen(spwindow_start_row);return false;">Start Row</a></th>
			<th><a href="#" onClick="WindowOpen(spwindow_start_column);return false;">Start Column</a></th>
			<th><a href="#" onClick="WindowOpen(spwindow_height);return false;">Height</a></th>
			<th><a href="#" onClick="WindowOpen(spwindow_width);return false;">Width</a></th>
			<th><a href="#" onClick="WindowOpen(spwindow_lower_threshold);return false;">Lowest Energy</a></th>
			<th><a href="#" onClick="WindowOpen(spwindow_pha_range);return false;">Energy Range</a></th>
			<th><a href="#" onClick="WindowOpen(spwindow_sample);return false;">Sample Rate</a></th>
			<th></th></tr>';

			if($aciswin_no == 0){
				$aciswin_no = 1;
			}

#
#---- if eventfilter_lower > 0.5, you need to keep all CCDs must have acis window constraints entires.
#---- check none of them are accidentally "removed" from the list. If so, put it back with warning.
#
			@chk_list  = ();
			@accd_list = ();
			@dccd_list = ();
			$cn       = 0;
			for($k = 0; $k < $aciswin_no; $k++){
				if($ordr[$k] !~ /\d/){
					push(@chk_list,  $k);
					push(@dccd_list, $chip[$k]);
					$cn++;
				}else{
					push(@accd_list, $chip[$k]);
				}
			}
			if($cn > 0){
				@tccd_list = ();
				@k_list    = ();
				$tn        = 0;
				TOUTER:
				for($k = 0; $k < $cn; $k++){
					foreach $comp (@accd_list){
						if($dccd_list[$k] =~ /$comp/){
							next TOUTER;
						}
					}
					push(@tccd_list, $dccd_list[$k]);
					push(@k_list,    $chk_list[$k]);
					$tn++;
				}

				if($tn > 0){
					for($k = 0; $k < $tn; $k++){
						foreach $comp (@open_ccd){
							if($tccd_list[$k] =~ /$comp/){
								$ordr[$k_list[$k]] = 999;
							}
						}
					}
				}
			}

			$chk_drop = 0;
			OUTER:
			for($k = 0; $k < $aciswin_no; $k++){
#
#---- if the ordr entry is blank, remove the line from the data. 
#
				if($ordr[$k] !~ /\d/){

					if($orig_ordr[$k] =~ /\d/ && $orig_chip[$k] !~ /N/){
#
#--- this is for the case the entry was there in database
#
						print "<input type=\"hidden\" name=\"$tordr\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tchip\" value=\"NULL\">";
						print "<input type=\"hidden\" name=\"$tinclude_flag\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tstart_row\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tstart_column\" value=\" \">";
						print "<input type=\"hidden\" name=\"$theight\" value=\" \">";
						print "<input type=\"hidden\" name=\"$twidth\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tlower_threshold\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tpha_range\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tsample\" value=\" \">";
					}else{
#
#--- this is for the case the entry was not in database (removing an added row during this session)
#
						$chk_drop++;
					}
					next OUTER;
				}

#
#--- if a ccd which is not opened is accidentaly added, or during this session, any of the open ccd is closed
#--- remove that ccd from the acis window constraint entries.
#
				$open_chk = 1;
				OUTER2:
				foreach $comp (@open_ccd){
					if($chip[$k] =~ /$comp/){
						$open_chk = 0;
						last OUTER2;
					}
				}

				if($open_chk == 1){
					if($orig_ordr[$k] =~ /\d/ && $orig_chip[$k] !~ /N/){
						print "<input type=\"hidden\" name=\"$tordr\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tchip\" value=\"NULL\">";
						print "<input type=\"hidden\" name=\"$tinclude_flag\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tstart_row\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tstart_column\" value=\" \">";
						print "<input type=\"hidden\" name=\"$theight\" value=\" \">";
						print "<input type=\"hidden\" name=\"$twidth\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tlower_threshold\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tpha_range\" value=\" \">";
						print "<input type=\"hidden\" name=\"$tsample\" value=\" \">";
					}else{
						$chk_drop++;
					}
					next OUTER;
				}
	
#
#--- readjusting the entry number (for the case any ccd is dropped from the list)
#
				$m = $k - $chk_drop;

				$taciswin_id      = 'ACSIWIN_ID'."$m";
				$tordr            = 'ORDR'."$m";
				$tchip            = 'CHIP'."$m";
#				$tinclude_flag    = 'INCLUDE_FLAG'."$m";
				$tstart_row       = 'START_ROW'."$m";
				$tstart_column    = 'START_COLUMN'."$m";
				$theight          = 'HEIGHT'."$m";
				$twidth           = 'WIDTH'."$m";
				$tlower_threshold = 'LOWER_THRESHOLD'."$m";
				$tpha_range       = 'PHA_RANGE'."$m";
				$tsample          = 'SAMPLE'."$m";


				if($chip[$k] !~ /N/i){
					if($lower_threshold[$k] !~ /\d/){
						$lower_threshold[$k] = $eventfilter_lower;
					}
					if($pha_range[$k] !~ /\d/){
						$pha_range[$k] = $eventfilter_higher;
					}
				}

				if($ordr[$k] == 999){
					print "<tr><td style='background-color:red'>";
				}else{
					print "<tr><td>";
				}
				print textfield(-name=>"$tordr", -value=>"$ordr[$k]", -override=>10000, -size=>'2');
				print " </td><td>";
				print popup_menu(-name=>"$tchip",-value=>['NULL','I0','I1','I2','I3','S0','S1','S2','S3','S4','S5'],
                       				-default=>"$chip[$k]", -override=>10000);
				print "</td><td>";
#				print popup_menu(-name=>"$tinclude_flag",-value=>['INCLUDE','EXCLUDE'],
#                        			-default=>"$dinclude_flag[$k]", -override=>10000);
#				print "</td><td>";
				print textfield(-name=>"$tstart_row", -value=>"$start_row[$k]",-override=>10000, -size=>'8');
				print "</td><td>";
				print textfield(-name=>"$tstart_column", -value=>"$start_column[$k]", -override=>10000, -size=>'8');
				print "</td><td>";
				print textfield(-name=>"$theight", -value=>"$height[$k]",-override=>10000,  -size=>'8');
				print "</td><td>";
				print textfield(-name=>"$twidth", -value=>"$width[$k]",-override=>10000,  -size=>'8');
				print "</td><td>";
				print textfield(-name=>"$tlower_threshold", -value=>"$lower_threshold[$k]",-override=>10000, -size=>'8');
				print "</td><td align=middle>";
				print textfield(-name=>"$tpha_range", -value=>"$pha_range[$k]",-override=>10000, -size=>'8');
				print '</td><td>';
				print textfield(-name=>"$tsample", -value=>"$sample[$k]",-override=>10000, -size=>'8');
				print "</td><td>";
				if($ordr[$k] == 999){
					print "<em style='color:red'>You Cannot Remove This Entry</em>";
				}	
				print '</td></tr>';

				print "<input type=\"hidden\" name=\"$taciswin_id\" value=\"$aciswin_id[$k]\"\>";
			}
			print '</table>';

#
#--- adjust total # of ccds (subtract # of dropped ccds)
#
			$aciswin_no -= $chk_drop;

			print '<p>* If you need to remove any window constraint entries, make "Ordr" a blank, then push: ';
			print '<input type="submit" name="Check" value="Update">';
			print '</p>';


			print "<input type=\"hidden\" name=\"SPWINDOW\" value=\"$spwindow\">";
			print "<input type=\"hidden\" name=\"ACISWIN_NO\" value=\"$aciswin_no\">";
			print "<input type=\"hidden\" name=\"awc_cnt\" value=\"$awc_cnt\">";
			print "<input type=\"hidden\" name=\"awc_ind\" value=\"$awc_ind\">";

		}else{
			print "<h3>No ACIS Window Constraints</h3>";

			for($k = 0; $k < $aciswin_no; $k++){
		
				$taciswin_id      = 'ACISWIN_ID'."$k";
				$tordr            = 'ORDR'."$k";
				$tchip            = 'CHIP'."$k";
#				$tinclude_flag    = 'INCLUDE_FLAG'."$k";
				$tstart_row       = 'START_ROW'."$k";
				$tstart_column    = 'START_COLUMN'."$k";
				$theight          = 'HEIGHT'."$k";
				$twidth           = 'WIDTH'."$k";
				$tlower_threshold = 'LOWER_THRESHOLD'."$k";
				$tpha_range       = 'PHA_RANGE'."$k";

                       		print "<input type=\"hidden\" name=\"$taciswin_id\" value=\"$aciswin_id[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tordr\" value=\"$ordr[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tchip\" value=\"$chip[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tinclude_flag\" value=\"$dinclude_flag[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tstart_row\" value=\"$start_row[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tstart_column\" value=\"$start_column[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$theight\" value=\"$height[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$twidth\" value=\"$width[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tpha_range\" value=\"$pha_range[$k]\"\>";
                       		print "<input type=\"hidden\" name=\"$tsample\" value=\"$sample[$k]\"\>";
			}

                       	print "<input type=\"hidden\" name=\"ACISWIN_NO\" value=\"$aciswin_no\"\>";
		}
	}	

#-----------------------------------
#----- TOO Parameter Case start here
#-----------------------------------

	if($usint_on =~ /no/ && $too_id =~ /NULL/){
	}else{
		print '<hr />';
		print '<h2>TOO Parameters</h2>';
		
		print '<table cellspacing=3 cellpadding=5>';
		print '<tr>';
		print '<th valign=top><a href="#" onClick="WindowOpen(too_id);return false;">TOO ID</a>:';
		print '</th><td>';
		print "$too_id",'</td>';
		print '</tr><tr>';
		print '<th valign=top nowrap><a href="#" onClick="WindowOpen(too_trig);return false;">TOO Trigger</a>:';
		print '</th><td>',"$too_trig",'</td>';
		print '</tr><tr>';
		print '<th><a href="#" onClick="WindowOpen(too_type);return false;">TOO Type</a>:</th><td>';
		print "$too_type";
		print '</td></tr></table>';
		print '<table cellspacing=3 cellpadding=5>';
		print '<tr>';
		print '<th>Exact response window (days):</th>';
		print '</tr><tr>';
		print '<th><a href="#" onClick="WindowOpen(too_start);return false;">Start</a>:</th><td>';
		print "$too_start";
		print '</td><td></td>';
		print '<th><a href="#" onClick="WindowOpen(too_stop);return false;">Stop</a>:</th><td>';
		print "$too_stop";
		print '</td><tr>';
		print '<th><a href="#" onClick="WindowOpen(too_followup);return false;">';
		print '# of Follow-up Observations</a>:</th><td>';
		print "$too_followup";
		print '</td></tr></table>';
		print '<table cellspacing=0 cellpadding=5>';
		print '<tr><td></td>';
		print '<th valign=top><a href="#" onClick="WindowOpen(too_remarks);return false;">';
		print 'TOO Remarks</a>:</th><td>';
		print "$too_remarks";
		print '</td></tr></table>';
	}
	
#---------------------------------->
#---- Comment and Remarks  -------->
#---------------------------------->
	
	print '<hr />';
	print '<h2>Comments and Remarks</h2>';
	print '<b>The remarks area below is reserved for remarks related to constraints, ';
	print 'actions/considerations that apply to the observation. ';
	print 'Please put all other remarks/comments into the comment area below. ';
	print '</b><br />';
	print '<tr> ';
	print '<br />';
	

#---------------------------------------------------------------------------------------
#------- Some remarks and/or comments contains " in the sentences. Since html page has 
#------- a problem with it, replacing " to ' so that html can behave normally.
#---------------------------------------------------------------------------------------

	@rtemp = split(//,$remarks);
	$temp = '';
	foreach $ent (@rtemp){
		if($ent eq "\""){
			$temp = "$temp"."'";
		}else{
			$temp = "$temp"."$ent";
		}
	}
	$remarks = $temp;
	
	@rtemp = split(//,$mp_remarks);
	$temp = '';
	foreach $ent (@rtemp){
		if($ent eq "\""){
			$temp = "$temp"."'";
		}else{
			$temp = "$temp"."$ent";
		}
	}
	$mp_remarks = $temp;
	
	@rtemp = split(//,$comments);
	$temp = '';
	foreach $ent (@rtemp){
		if($ent eq "\""){
			$temp = "$temp"."'";
		}else{
			$temp = "$temp"."$ent";
		}
	}
		
	$comments = $temp;


	print '<table cellspacing="0" cellpadding="5">';
	if($sp_user eq 'no'){
		print '<th valign=top><a href="#" onClick="WindowOpen(remarks);return false;"><font color=blue>Remarks</font></a>:</th>';
		print "<td>$remarks</td></tr>";
		print hidden(-name=>'REMARKS', -value=>"$remarks", -override=>10000);
	}else{
		print '<th valign=top><a href="#" onClick="WindowOpen(remarks);return false;">Remarks</a>:</th>';
		print '<td><textarea name="REMARKS" rows="10" cols="60"  WRAP=virtual >';
		print "$remarks";
		print '</textarea></td></tr>';
#		print '<th valign=top>MP Remarks:</th><td><textarea name="MP_REMARKS" rows="10" cols="60" WRAP=virtual>';
#		print "$mp_remarks";
#		print '</textarea></td></tr>';
	}


	if($remark_cont ne ''){
		print '<tr><th valign=top>Other Remark:</th><td>',"$remark_cont",'</td></tr>',"\n";
	}

	print "<tr><td colspan=3>";
	print "<b> Comments are kept as a record of why a change was made.<br />";
	print "If a CDO approval is required, or if you have a special instruction for ARCOPS, ";
	print "add the comment in this area.<br />";
	print "</td></tr>";
	print "<tr>";
	print "<th  valign=top><a href='#' onClick='WindowOpen(comments);return false;'> Comments</a>:</th><td>";
	print "<textarea name='COMMENTS' rows='3' cols='60' WRAP=virtual>$comments</textarea>";
	print "</td></tr>";

	print "</table>";
	print "<hr />";
	

#------------------------------------->
#---- here is submitting options ----->
#------------------------------------->


	if($mp_check > 0){
		print "<h2><b><font color='red'>";
#		print "This obsid is in an active OR list. You must get permission from ";
#		print "<a href='mailto:$sot_contact'>SOT</a> ";
#		print "to make your change.";

		print "Currently under review in an active OR list.";
		print "</font></b><br /></h2>";
	}

######	if($mp_check == 0){
		if($sp_user eq 'yes'){
			print '<b>OPTIONS</b>';
			print '<p>';
			print '<table><tr><td>';
			print '<b>Normal Change </b> ';
			print '</td><td>';
			print 'Any changes other than APPROVAL status';
			print '</td></tr><tr><td>';
#			print '<b>User Approves this ObsID as is </b>';
			print '<b>Observation is Approved for flight </b>';
			print '</td><td>';
			print 'Adds ObsID to the Approved File - nothing else<br />';
			print '</td></tr><tr><td>';
			print '<b>ObsID no longer ready to go </b> ';
			print '</td><td>';
		 	print 'REMOVES ObsID from the Approved File - nothing else<br />';
			print '</td></tr>';

			print '<tr><td>';
#			print '<b>Clone this ObsID </b> ';
			print '<b>Split this ObsID </b> ';
			print '</td> <td> ';
			print '	 	does NOT add them to the Approved File.<br />';
			print '	<font color=fuchsia> Please add an explanation why you need<br /> to split this observation in the comment area.</font><br />';
			print '</td></tr>';
		}else{
			print '<b>OPTIONS</b>';
			print '<p>';
			print '<table><tr><td>';
#			print '<b>User Approves this ObsID as is </b>';
			print '<b>Observation is Approved for flight</b>';
			print '</td><td>Adds ObsID to the Approved File - nothing else';
			print '</td></tr><td>';
			print '<b>Approve ObsID as Changed</b>';
			print '</td><td>This ObsOD will be approved once ARCOPS has signed it off';
			print '</td></tr><tr><td>';
			print '<b>Request Full USINT Support</b> ';
			print '</td><td>USINT will perform all changes and the approval process';
			print '</td></tr>';
		}

	
		print '</table>';
		print '</p>';
		
		print '<center>';
		print '<p>';
		print '<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="5">';
		print '<tr>';
	
		if($sp_user eq 'yes'){
			if($asis eq 'NORM' || $asis eq ''){
				print '<td><input type="RADIO" name="ASIS" value="NORM" CHECKED><b> Normal Change</b>';
			}else{
				print '<td><input type="RADIO" name="ASIS" value="NORM"><b> Normal Change</b>';
			}
		
			if($asis eq 'ASIS'){
#				print '<td><input type="RADIO" name="ASIS" value="ASIS" CHECKED><b> User Approves this ObsID as is</b>';
				print '<td><input type="RADIO" name="ASIS" value="ASIS" CHECKED><b> Observation is Approved for flight</b>';
			}else{
#				print '<td><input type="RADIO" name="ASIS" value="ASIS"><b> User Approves this ObsID as is</b>';
				print '<td><input type="RADIO" name="ASIS" value="ASIS"><b> Observation is Approved for flight</b>';
			}
		
			if($asis eq 'REMOVE'){
				print '<td><input type="RADIO" name="ASIS" value="REMOVE" CHECKED> <b>ObsID no longer ready to go</b>';
			}else{
				print '<td><input type="RADIO" name="ASIS" value="REMOVE"> <b>ObsID no longer ready to go</b>';
			}
	
			if($asis eq 'CLONE'){
#				print '<td><input type="RADIO" name="ASIS" value="CLONE" CHECKED><b> Clone this ObsID</b>';
				print '<td><input type="RADIO" name="ASIS" value="CLONE" CHECKED><b> Split this ObsID</b>';
			}else{
#				print '<td><input type="RADIO" name="ASIS" value="CLONE"><b> Clone this ObsID.</b>';
				print '<td><input type="RADIO" name="ASIS" value="CLONE"><b> Split this ObsID.</b>';
			}
		}else{
			if($asis eq 'ASIS'){
#				print '<td><input type="RADIO" name="ASIS" value="ASIS" CHECKED><b> User Approves this ObsID as is</b>';
				print '<td><input type="RADIO" name="ASIS" value="ASIS" CHECKED><b> Observation is Approved for flight</b>';
			}else{
#				print '<td><input type="RADIO" name="ASIS" value="ASIS"><b> User Approves this ObsID as is</b>';
				print '<td><input type="RADIO" name="ASIS" value="ASIS"><b> Observation is Approved for flight</b>';
			}
			if($asis eq 'ARCOPS' || $asis eq ''){
				print '<td><input type="RADIO" name="ASIS" value="ARCOPS" CHECKED><b> Approve ObsID as Changed</b>';
			}else{
				print '<td><input type="RADIO" name="ASIS" value="ARCOPS"><b> Approve ObsID as Changed</b>';
			}
			if($asis eq 'SEND_MAIL'){
				print '<td><input type="RADIO" name="ASIS" value="SEND_MAIL" CHECKED><b>Request Full USINT Support</b>';
			}else{
				print '<td><input type="RADIO" name="ASIS" value="SEND_MAIL"><b>Request Full USINT Support</b>';
			}
		}
		
	
		print '</tr></table>';

		print '<input type="hidden" name="OBSID"        '," value=\"$orig_obsid\">";
		print '<input type="hidden" name="ACISID"       '," value=\"$orig_acisid\">";
		print '<input type="hidden" name="HRCID"        '," value=\"$orig_hrcid\">";
		print '<input type="hidden" name="SI_MODE"      '," value=\"$si_mode\">";
		print '<input type="hidden" name="access_ok"    '," value=\"yes\">";
		print '<input type="hidden" name="pass"         '," value=\"$pass\">";
		print '<input type="hidden" name="sp_user"      '," value=\"$sp_user\">";
		print '<input type="hidden" name="email_address"'," value=\"$email_address\">";


		print '<TABLE BORDER="0" CELLSPACING="0" CELLPADDING="5">';
		print '<tr>';

##		if($usint_on =~ /yes/){
##			print '<td><b>Username : </b><input type="text" name="USER" size="12" value="',"$submitter",'" >';
##		}else{
			print '<input type="hidden" name="USER"      value="',"$submitter",'">';
			print '<input type="hidden" name="SUBMITTER" value="',"$submitter",'">';
			print '<input type="hidden" name="USER"      value="',"$submitter",'">';
##		}


		print '<td><input type="submit" name="Check"  value="Submit">';
####		print '<td><input type="reset" value="Reset Form">';
		print '<td><input type="submit" name="Check"   value="     Update     ">';
#####	}
	print '</tr>';
	print '</table>';
	print '<br />';
	print '</center>';
	print '<br />';
	print '</form>';
	print '<p>';

	if($usint_on =~ /test/){
		print "<b>";
		print "If you have multiple entries to approve (as is), you can use: ";
		print "<a href='$test_http/express_signoff.cgi?$obsid'>";
		print "Express Approval Page";
		print "</b>";
	}elsif($usint_on =~ /yes/){
		print "<b>";
		print "If you have multiple entries to approve (as is), you can use: ";
		print "<a href='$usint_http/express_signoff.cgi?$obsid'>";
		print "Express Approval Page";
		print "</b>";
	}else{
		print "<b>";
		print "If you have multiple entries to approve (as is), you can use: ";
		print "<a href='$obs_ss_http/express_signoff.cgi?$obsid'>";
		print "Express Approval Page";
		print "</b>";
	}


	if($usint_on =~ /yes/){
		print '<br /><br />';
		print '<h3>';
		print "<a href=\"$cdo_http/review_report/disp_report.cgi?";
		print "$proposal_number";
		print '">Link to peer review report and proposal</a>';
		print '</h3>';
		print '<br />';
	}

	if($usint_on =~ /test/){
	}elsif($usint_on =~ /no/){
		print "Go to the <A HREF=\"$obs_ss_http/search.html\">";
		print 'Chandra User Observation Search Page</A><p>  ';
	}elsif($usint_on =~ /yes/){
		print "Go to the <A HREF=\"$usint_http/search.html\">";
		print 'Chandra User Observation Search Page</A><p>  ';
	}

#------------------------------------------------>
#------- the end of the html page display ------->
#------------------------------------------------>

	print end_form();
	print "</body>";
	print "</html>";
	exit();
}

################################################################################
### mod_time_format: convert time format to match A4 requirements           ####
### this version is not used:1
################################################################################

sub mod_time_format2{

	@atemp = split(/\W/, "$input_time");		# separate time into pieces
	@atime = ();
	$cnt = 0;
	foreach $ent (@atemp){
		if($ent =~ /\w/){
			$cnt++;
			push(@atime, $ent);
		}
	}
	$cnt--;
	
	if($cnt == 6){					# all hh:mm:ss are avairable with AM/PM attached
		if($atime[6] =~ /^P/i){			# fix AM/PM system to 24 hr sytem
			$mo = 2;
			if($atime < 12){
				$atime[3] += 12;
			}
		}
		if($atime[3] < 10){			# hours, mins, and sec must be 2 digit expression
			$atime[3] = int ($atime[3]);
			$atime[3] = "0$atime[3]";
		}
		if($atime[4] < 10){
			$atime[4] = int ($atime[4]);
			$atime[4] = "0$atime[4]";
		}
		if($atime[5] < 10){
			$atime[5] = int ($atime[5]);
			$atime[5] = "0$atime[5]";
		}
	
		$time = "$atime[3]:$atime[4]:$atime[5]";
	}
	
	if($cnt == 5){				      	# only hh:mm are avaairable with PM/AM attached
		if($atime[5] =~ /^A/i){		    	# or all hh:mm:ss are avairable with 24 hr system
			$mo = 1;
		}elsif($atime[5] =~ /^P/i){		# it is it AM/PA system, fix it
			$mo = 2;
			if($atime < 12){
				$atime[3] += 12;
			}
		}else{
			@ctemp = split(//, $atime[5]);
			$etime = '';
			$mind = '';
			foreach $ent (@ctemp){
				if($ent =~ /\d/){
					$etime = "$etime"."$ent";
				}else{
					$mind = $ent;
					last;
				}
				
			}
			if($mind =~ /A/i){
				$atime[5] = $etime;
			}elsif($mind =~ /P/i){
				$atime[5] = $etime;
				if($atime[3] < 12){
					$atime[3] += 12;
				}
			}else{
				$atime[5] = $etime;
			}
	
			$mo = 0;
		}
		if($mo == 0){
			if($atime[3] < 10){
				$atime[3] = int ($atime[3]);
				$atime[3] = "0$atime[3]";
			}
			if($atime[4] < 10){
				$atime[4] = int ($atime[4]);
				$atime[4] = "0$atime[4]";
			}
			if($atime[5] < 10){
				$atime[5] = int ($atime[5]);
				$atime[5] = "0$atime[5]";
			}
			$time = "$atime[3]:$atime[4]:$atime[5]";
		}else{
			if($atime[3] < 10){
				$atime[3] = "0$atime[3]";
			}
			if($atime[4] < 10){
				$atime[4] = "0$atime[4]";
			}
			$time = "$atime[3]:$atime[4]";
		}
	}
	
	if($cnt == 4){							# only hh available with PM/AM
		if($atime[4] =~ /^A/i){					# or hh:mm with 24 hrs system
			$mo = 1;
		}elsif($atime[4] =~ /^P/i){
			$mo = 2;
			if($atime < 12){
				$atime[3] += 12;
			}
		}else{
			@ctemp = split(//, $atime[4]);
			$etime = '';
			$mind = '';
			foreach $ent (@ctemp){
				if($ent =~ /\d/){
					$etime = "$etime"."$ent";
				}else{
					$mind = $ent;
					last;
				}
			}	
			if($mind =~ /A/i){
				$atime[4] = $etime;
			}elsif($mind =~ /P/i){
				$atime[4] = $etime;
				if($atime[3] < 12){
					$atime[3] += 12;
				}
			}else{
				$atime[4] = $etime;
			}
	
			$mo = 0;
		}
		if($mo == 0){
			if($atime[3] < 10){
				$atime[3] = int ($atime[3]);
				$atime[3] = "0$atime[3]";
			}
			if($atime[4] < 10){
				$atime[4] = int ($atime[4]);
				$atime[4] = "0$atime[4]";
			}
			$time = "$atime[3]:$atime[4]";
		}else{
			if($atime[3] < 10){
				$atime[3] = int ($atime[3]);
				$atime[3] = "0$atime[3]";
			}
			$time = "$atime[3]";
		}
	}
	
	if($cnt == 3){							# only hh avairable with 24 hr system
		@ctemp = split(//, $atime[3]);
		$etime = '';
		$mind = '';
		foreach $ent (@ctemp){
	
			if($ent =~ /\d/){
				$etime = "$etime"."$ent";
			}else{
				$mind = $ent;
				last;
			}
		}
		if($mind =~ /A/i){
		$atime[4] = $etime;
		}elsif($mind =~ /P/i){
			$atime[4] = $etime;
			if($atime[3] < 12){
				$atime[3] += 12;
			}
		}else{
			$atime[4] = $etime;
		}
		$mo  = 0;
	
		if($atime[3] < 10){
			$atime[3] = int ($atime[3]);
			$atime[3] = "0$atime[3]";
		}
		$time = "$atime[3]";
	}
	
	@cychk = split(//, $atime[0]);
	@bychk = split(//, $atime[2]);
	$cmon = 0;
	if($atime[0] =~ /\D/){
		$cmon++;
	}

	$yind = 0;
	$jcnt0 = 0;
	foreach(@cychk){
		$jcnt0++;
	}
	
	$jcnt2 = 0;
	foreach(@bychk){
		$jcnt2++;
	}
	
	if($cmon > 0){
		if($jcnt2 == 2){				# fixing yy system to yyyy system
			if($atime[2] > 32){
				$year = "19$atime[2]";		# here we assume that chandra won't
			}else{					# live beyond 2032....
				$year = "20$atime[2]";		# (at least in the old data system)
			}
		}else{
			$year = $atime[2];
			$yind = 1;
		}
	}elsif($jcnt2 == 4){
		$year = $atime[2];
		$yind = 1;
	}elsif($jcnt0 == 4){
		$year = $atime[0];
	}elsif($jcnt2 == 2 && $jcnt0 ==1){
		if($atime[2] > 32){
			$year = "19$atime[2]";
		}else{
			$year = "20$atime[2]";
		}
		$yind = 1;
	}elsif($jcnt2 == 1 && $jcnt0 == 2){
		if($atime[0] > 32){
			$year = "19$atime[0]";
		}else{
			$year = "20$atime[0]";
		}
	}elsif($jcnt2 == 2 && $jcnt0 == 2){
		if($atime[2] > 32){
			$year = "19$atime[2]";
			$yind = 1;
		}elsif($atime[0]> 32){
			$year = "19$atime[0]";
		}else{
			$year = "20$atime[2]";
			$yind = 1;
		}
	}
	
	if($yind == 1){					# check which one is date, and put it in
		$day = $atime[0];
	}else{
		$day = $atime[2];
	}
	
	if($atime[0] =~ /\d/ && $atime[1] =~ /\d/){	# selecting month and correct them
		$month = $atime[1];
		if($month < 10){
			$month = int ($month);
			$month = "0$month";
		}
	}elsif($atime[0] =~ /\d/ && ($atime[1] =~ /\D/ && $atime[1] =~/\S/)){
		if($atime[1] =~ /Jan/i){
			$month = '01';
		}elsif($atime[1] =~ /Feb/i){
			$month = '02';
		}elsif($atime[1] =~ /Mar/i){
			$month = '03';
		}elsif($atime[1] =~ /Apr/i){
			$month = '04';
		}elsif($atime[1] =~ /May/i){
			$month = '05';
		}elsif($atime[1] =~ /Jun/i){
			$month = '06';
		}elsif($atime[1] =~ /Jul/i){
			$month = '07';
		}elsif($atime[1] =~ /Aug/i){
			$month = '08';
		}elsif($atime[1] =~ /Sep/i){
			$month = '09';
		}elsif($atime[1] =~ /Oct/i){
			$month = '10';
		}elsif($atime[1] =~ /Nov/i){
			$month = '11';
		}elsif($atime[1] =~ /Dec/i){
			$month = '12';
		}
	}elsif($atime[0] =~ /\D/ && $atime[0] =~ /\S/ && $atime[1] =~ /\d/){
		$day = $atime[1];
		if($atime[0] =~ /Jan/i){
			$month = '01';
		}elsif($atime[0] =~ /Feb/i){
			$month = '02';
		}elsif($atime[0] =~ /Mar/i){
			$month = '03';
		}elsif($atime[0] =~ /Apr/i){
			$month = '04';
		}elsif($atime[0] =~ /May/i){
			$month = '05';
		}elsif($atime[0] =~ /Jun/i){
			$month = '06';
		}elsif($atime[0] =~ /Jul/i){
			$month = '07';
		}elsif($atime[0] =~ /Aug/i){
			$month = '08';
		}elsif($atime[0] =~ /Sep/i){
			$month = '09';
		}elsif($atime[0] =~ /Oct/i){
			$month = '10';
		}elsif($atime[0] =~ /Nov/i){
			$month = '11';
		}elsif($atime[0] =~ /Dec/i){
			$month = '12';
		}
	}
	
	if($day < 10){
		$day = int ($day);
		$day = "0$day";
	}
}


##################################################################################
### prep_submit: preparing the data for submission                             ###
##################################################################################

sub prep_submit{

#----------------------
#----- time order cases
#----------------------

	for($j = 1; $j <= $time_ordr; $j++){
		$tstart_new[$j] = '';					# recombine tstart and tstop

		if($start_month[$j] ne 'NULL'){
			if($start_month[$j] eq 'Jan'){$start_month[$j] = '01'}
			elsif($start_month[$j] eq 'Feb'){$start_month[$j] = '02'}
			elsif($start_month[$j] eq 'Mar'){$start_month[$j] = '03'}
			elsif($start_month[$j] eq 'Apr'){$start_month[$j] = '04'}
			elsif($start_month[$j] eq 'May'){$start_month[$j] = '05'}
			elsif($start_month[$j] eq 'Jun'){$start_month[$j] = '06'}
			elsif($start_month[$j] eq 'Jul'){$start_month[$j] = '07'}
			elsif($start_month[$j] eq 'Aug'){$start_month[$j] = '08'}
			elsif($start_month[$j] eq 'Sep'){$start_month[$j] = '09'}
			elsif($start_month[$j] eq 'Oct'){$start_month[$j] = '10'}
			elsif($start_month[$j] eq 'Nov'){$start_month[$j] = '11'}
			elsif($start_month[$j] eq 'Dec'){$start_month[$j] = '12'}
		}

		if($start_date[$j] =~ /\d/ && $start_month[$j] =~ /\d/ && $start_year[$j] =~ /\d/ ){
			@ttemp = split(/:/, $start_time[$j]);
			$tind = 0;
			$time_ck = 0;

			foreach $tent (@ttemp){
				if($tent =~ /\D/ || $tind eq ''){
					$tind++;
				}else{
					$time_ck = "$time_ck"."$tent";
				}
			}

			if($tind == 0){
				$tstart_new  = "$start_month[$j]:$start_date[$j]:$start_year[$j]:$start_time[$j]";
				$chk_start = -9999;
				if($tstart_new =~ /\s+/ || $tstart_new == ''){
				}else{
					$tstart[$j]    = $tstart_new;
					$chk_start = "$start_year[$j]$start_month[$j]$start_date[$j]$time_ck";
				}
			}
		}

		
		$tstop_new[$j] = '';

		if($end_month[$j] ne 'NULL'){
			if($end_month[$j] eq 'Jan'){$end_month[$j] = '01'}
			elsif($end_month[$j] eq 'Feb'){$end_month[$j] = '02'}
			elsif($end_month[$j] eq 'Mar'){$end_month[$j] = '03'}
			elsif($end_month[$j] eq 'Apr'){$end_month[$j] = '04'}
			elsif($end_month[$j] eq 'May'){$end_month[$j] = '05'}
			elsif($end_month[$j] eq 'Jun'){$end_month[$j] = '06'}
			elsif($end_month[$j] eq 'Jul'){$end_month[$j] = '07'}
			elsif($end_month[$j] eq 'Aug'){$end_month[$j] = '08'}
			elsif($end_month[$j] eq 'Sep'){$end_month[$j] = '09'}
			elsif($end_month[$j] eq 'Oct'){$end_month[$j] = '10'}
			elsif($end_month[$j] eq 'Nov'){$end_month[$j] = '11'}
			elsif($end_month[$j] eq 'Dec'){$end_month[$j] = '12'}
		}

		if($end_date[$j] =~ /\d/ && $end_month[$j] =~ /\d/ && $end_year[$j] =~ /\d/ ){
			@ttemp = split(/:/, $end_time[$j]);
			$tind = 0;
			$time_ck = 0;
			foreach $tent (@ttemp){
				if($tent =~ /\D/ || $tind eq ''){
					$tind++;
				}else{
					$time_ck = "$time_ck"."$tent";
				}
			}

			if($tind == 0){
				$tstop_new = "$end_month[$j]:$end_date[$j]:$end_year[$j]:$end_time[$j]";
				$chk_end = -9999;
				if($tstop_new =~ /\s+/ || $tstop_new == ''){
				}else{
					$tstop[$j] = $tstop_new;
					$chk_end ="$end_year[$j]$end_month[$j]$end_date[$j]$time_ck";
				}
			}
		}
		
		$time_ok[$j] = 0;

		if($chk_start != -9999 && $chk_end != -9999){			# check tstop > tstart
			$time_ok[$j] = 1;
			if($chk_end >= $chk_start){
				$time_ok[$j] = 2;
			}
		}

		if($window_constraint[$j]    eq 'NONE')      {$window_constraint[$j] = 'N'}
		elsif($window_constraint[$j] eq 'NULL')      {$window_constraint[$j] = 'NULL'}
		elsif($window_constraint[$j] eq 'CONSTRAINT'){$window_constraint[$j] = 'Y'}
		elsif($window_constraint[$j] eq 'PREFERENCE'){$window_constraint[$j] = 'P'}
	}

#----------------------
#---- roll order cases
#----------------------

	for($j = 1; $j <= $roll_ordr; $j++){

		if($roll_constraint[$j]    eq 'NONE')      {$roll_constraint[$j] = 'N'}
		elsif($roll_constraint[$j] eq 'NULL')      {$roll_constraint[$j] = 'NULL'}
		elsif($roll_constraint[$j] eq 'CONSTRAINT'){$roll_constraint[$j] = 'Y'}
		elsif($roll_constraint[$j] eq 'PREFERENCE'){$roll_constraint[$j] = 'P'}
		elsif($roll_constraint[$j] eq '')          {$roll_constraint[$j] = 'NULL'}

		if($roll_180[$j]    eq 'NULL'){$roll_180[$j] = 'NULL'}
		elsif($roll_180[$j] eq 'NO')  {$roll_180[$j] = 'N'}
		elsif($roll_180[$j] eq 'YES') {$roll_180[$j] = 'Y'}
		elsif($roll_180[$j] eq '')    {$roll_180[$j] = 'NULL'}
	}
#-------------------
#--- aciswin cases
#-------------------

	for($j = 0; $j < $acsiwin_no; $j++){
		if($include_flag[$j] eq 'INCLUDE'){$include_flag[$j] = 'I'}
		elsif($include_flag[$j] eq 'EXCLUDE'){$include_flag[$j] = 'E'}
	}
		
#
#--- reorder the rank with increasing order value sequence (added Jul 14, 2015)
#
        if($aciswin_no > 0){
            @rlist = ();
            for($i = 0; $i <= $aciswin_no; $i++){
                push(@rlist, $ordr[$i]);
            }
            @sorted = sort{$a<=>$b} @rlist;
            @tlist = ();
            foreach $ent (@sorted){
                if($ent == 0){
                    next;
                }
                for($i = 0; $i <= $aciswin_no; $i++){
                    if($ent == $ordr[$i]){
                        push(@tlist, $i);
                    }
                }
            }
        
            @temp0 = ();
            @temp1 = ();
            @temp2 = ();
            @temp3 = ();
            @temp4 = ();
            @temp5 = ();
            @temp6 = ();
            @temp7 = ();
            @temp8 = ();
            @temp9 = ();
            @temp10= ();
        
            for($i = 0; $i <= $aciswin_no; $i++){
                $pos = $tlist[$i];
                push(@temp0 , $ordr[$pos]);
                push(@temp1 , $start_row[$pos]);
                push(@temp2 , $start_column[$pos]);
                push(@temp3 , $width[$pos]);
                push(@temp4 , $height[$pos]);
                push(@temp5 , $lower_threshold[$pos]);
                push(@temp6 , $pha_range[$pos]);
                push(@temp7 , $sample[$pos]);
                push(@temp8 , $chip[$pos]);
                push(@temp9 , $include_flag[$pos]);
                push(@temp10, $aciswin_id[$pos]);
            }
            @ordr            = @temp0;
            @start_row       = @temp1;
            @start_column    = @temp2;
            @width           = @temp3;
            @height          = @temp4;
            @lower_threshold = @temp5;
            @pha_range       = @temp6;
            @sample          = @temp7;
            @chip            = @temp8;
            @include_flag    = @temp9;
            @aciswin_id      = @temp10;
        
        }

#------------------ Jul 14, 2015 update ends -------------------------


#----------------------------------------------------------------
#----------- these have different values shown in Ocat Data Page
#----------- find database values for them
#----------------------------------------------------------------
	
	@dname_list = ('proposal_joint', 'roll_flag', 'window_flag', 'dither_flag', 'uninterrupt', 'photometry_flag', 'multitelescope', 'hrc_zero_block',
        	'hrc_timing_mode', 'most_efficient', 'onchip_sum', 'duty_cycle', 'eventfilter', 'multiple_spectral_lines', 'spwindow', 'extended_src',
        	'phase_constraint_flag', 'window_constrint', 'constr_in_remarks', 'ccdi0_on', 'ccdi1_on', 'ccdi2_on', 'ccdi3_on', 'ccds0_on', 'ccds1_on',
        	'ccds2_on', 'ccds3_on', 'ccds4_on', 'ccds5_on');

	foreach $d_name (@dname_list){
		adjust_o_values();
	}

	read_user_name();					# read registered user name
	
	$usr_ind      = 0;
	$usr_cnt      = 0;
	@list_of_user = @user_name;

	if($usint_on  =~ /yes/){
		@list_of_user = @special_user;
	}

	OUTER:
	foreach $usr_nm (@list_of_user){				# checking the user name 
		$luser = lc ($submitter);
		$luser =~ s/\s+//g;

		if($luser eq $usr_nm){
			$usr_ind++;
			if($usint_on =~ /yes/){
				$email_address = $special_email[$usr_cnt];
			}
			last OUTER;
		}
		$usr_cnt++;
	}
	if($submitter eq 'mtadude'){
		$usr_ind++;
	}
		
}

############################################################################################################
### chk_entry: calling entry_test to check input value range and restrictions                            ###
############################################################################################################

sub chk_entry{

#------------------------------
#----- read condition database
#------------------------------

	read_range();					#sub to read the range database

	$header_chk = 0;
	$range_ind  = 0;
	$error_ind  = 0;
	@out_range  = ();

	@cdo_warning = ();
	$cdo_w_cnt   = 0;

    @pwarning_name_list = ();
    @pwarning_orig_val  = ();
    @pwarning_new_val   = ();
    $pwarning_cnt       = 0;

#-------------------
#----- general cases
#-------------------

	foreach $name (@paramarray){
		if($name =~ /WINDOW_FLAG/i || $name =~ /ROLL_FLAG/i || $name =~ /SPWINDOW/i || $name =~ /MONITOR_FLAG/i
			|| $name =~ /GROUP_ID/i || $name =~ /MONITOR_FLAG/i || $name =~/PRE_MIN_LEAD/i
			|| $name =~ /PRE_MAX_LEAD/i
		){
		}else{

#-----------------------------------------------
#----- check input value range and restrictions
#-----------------------------------------------

			entry_test();
		}
	}

	if($range_ind > 0){
		if($header_chk == 0){
			$header_chk++;
			print "<h2><font color=red> Following values are out of range.</font> </h2>";
			print '<br />';
		}
	
		print '<table border= "1" cellpadding="4" >';
		print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
		foreach $ent (@out_range){
			@atemp = split(/<->/,$ent);
			$db_name = $atemp[0];
			find_name();
			print "<tr><th>$web_name ($atemp[0])</th>";
			print "<td style='text-align:center'><font color=\"red\">$atemp[1]</font></td>";
			print "<td><font color=\"green\">$atemp[2]</font></td></tr>";
		}
		print "</table>";
	}
	$range_ind = 0;
	@out_range = ();

#-----------------------------------------
#---- print a html page about the bad news
#-----------------------------------------

#------------------
#---- ccd cases
#------------------

	if($instrument =~ /ACIS/i){
		if($count_ccd_on > 6){
			$range_ind++;
		}

		if($range_ind > 0){
			$error_ind += $range_ind;
			if($header_chk == 0){
				$header_chk++;
				print "<h2><font color=red> Following values are out of range.</font> </h2>";
				print '<br />';
			}
		
			print '<table border= "1" cellpadding="4" >';
			print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
			foreach $ent (@out_range){
				@atemp = split(/<->/,$ent);
				$db_name = $atemp[0];
				find_name();
				print "<tr><th>$web_name ($atemp[0])</th>";
				print "<td style='text-align:center'><font color=\"red\">$atemp[1]</font></td>";
				print "<td><font color=\"green\">$atemp[2]</font></td></tr>";
			}
	
			if($count_ccd_on > 6){
				print "<tr><th># of CCD On</th>";
				print "<td><font color=\"red\">$count_ccd_on</font></td>";
				print "<td><font color=\"green\">must be less than or equal to 6</font></td></tr>";
			}
			print '</table>';
		}
	
#        	if($standard_chips =~ /Y/i){
#                	if($instrument =~ /ACIS-I/i){
#                        	if($ccdi0_on =~ /Y/i && $ccdi1_on =~ /Y/i && $ccdi2_on =~ /Y/i
#                                	&& $ccdi3_on =~ /Y/i && $ccds2_on =~ /Y/i && $ccds3_on =~ /Y/i
#					&& $ccds0_on =~ /N/i && $ccds1_on =~ /N/i 
#					&& $ccds4_on =~ /N/i && $ccds5_on =~ /N/i){
#					if($usint_on =~ /yes/i){
#                                		$standard_ok = 0;
#					}else{
#						$standard_ok = 1;
#					}
#                        	}else{
#                                	$standard_ok = 1;
#                                	if($sp_user eq 'no'){
#                                        	$standard_ok = 0;
#                                        	$standard_chips = 'N';
#                                	}
#                        	}
#                	}elsif($instrument =~ /ACIS-S/i){
#                        	if($ccds0_on =~ /Y/i && $ccds1_on =~ /Y/i && $ccds2_on =~ /Y/i
#                                	&& $ccds3_on =~ /Y/i && $ccds4_on =~ /Y/i && $ccds5_on =~ /Y/i
#					&& $ccdi0_on =~ /N/i && $ccdi1_on =~ /N/i
#					&& $ccdi2_on =~ /N/i && $ccdi3_on =~ /N/i){
#                                	$standard_ok = 0;
#                        	}else{
#					if($usint_on =~ /yes/i){
#                                		$standard_ok = 1;
#					}else{
#						$standard_ok = 0;
#					}
#                                	if($sp_user eq 'no'){
#                                        	$standard_ok = 0;
#                                        	$standard_chips = 'N';
#                                	}
#                        	}
#                	}
#
#                	if($standard_ok == 1){
#                        	print "<h2><font color=red> Following values are out of range.</font> </h2>";
#                        	print '<br />';
#                        	print '<table border= "1" cellpadding="4" >';
#                        	print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
#                        	print "<tr><th>Standard Chips</th>";
#                        	print "<td><font color=\"red\">$standard_chips</font></td>";
#                        	print "<td><font color=\"green\">should be N (NO)</font></td></tr>";
#                        	print '</table>';
#                	}
#
#        	}elsif($standard_chips =~ /N/i){
#
#                	if($instrument =~ /ACIS-I/i){
#                        	if($ccdi0_on =~ /Y/i && $ccdi1_on =~ /Y/i && $ccdi2_on =~ /Y/i
#                                	&& $ccdi3_on =~ /Y/i && $ccds2_on =~ /Y/i && $ccds3_on =~ /Y/i
#					&& $ccds0_on =~ /N/i && $ccds1_on =~ /N/i 
#					&& $ccds4_on =~ /N/i && $ccds5_on =~ /N/i){
#					if($usint_on =~ /yes/i){
#                                		$standard_ok = 1;
#					}else{
#						$standard_ok = 0;
#					}
#                        	}else{
#                                	$standard_ok = 0;
#                                	if($sp_user eq 'no'){
#                                        	$standard_ok = 0;
#                                        	$standard_chips = 'N';
#                                	}
#                        	}
#                	}elsif($instrument =~ /ACIS-S/i){
#                        	if($ccds0_on =~ /Y/i && $ccds1_on =~ /Y/i && $ccds2_on =~ /Y/i
#                                	&& $ccds3_on =~ /Y/i && $ccds4_on =~ /Y/i && $ccds5_on =~ /Y/i
#					&& $ccdi0_on =~ /N/i && $ccdi1_on =~ /N/i
#					&& $ccdi2_on =~ /N/i && $ccdi3_on =~ /N/i){
#                                	$standard_ok = 1;
#                        	}else{
#                                	$standard_ok = 0;
##                                	if($sp_user eq 'no'){
#                                        	$standard_ok = 0;
#                                        	$standard_chips = 'N';
#                                	}
#                        	}
#                	}
#
#                	if($standard_ok == 1){
#                        	print "<h2><font color=red> Following values are out of range.</font> </h2>";
#                        	print '<br />';
#                        	print '<table border= "1" cellpadding="4" >';
#                        	print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
#                        	print "<tr><th>Standard Chips</th>";
#                        	print "<td><font color=\"red\">$standard_chips</font></td>";
#                        	print "<td><font color=\"green\">should be Y (YES)</font></td></tr>";
#                        	print '</table>';
#                	}
#        	}

#        	if($sp_user eq 'no' && $standard_chips =~ /N/i){
#                	if($instrument =~ /ACIS-I/i){
#                        	if($ccdi0_on =~ /Y/i && $ccdi1_on =~ /Y/i && $ccdi2_on =~ /Y/i
#                                	&& $ccdi3_on =~ /Y/i && $ccds2_on =~ /Y/i && $ccds3_on =~ /Y/i){
#                                	$standard_chips = 'Y';
#                        	}
#                	}elsif($instrument =~ /ACIS-S/i){
#                        	if($ccds0_on =~ /Y/i && $ccds1_on =~ /Y/i && $ccds2_on =~ /Y/i
#                                	&& $ccds3_on =~ /Y/i && $ccds4_on =~ /Y/i && $ccds5_on =~ /Y/i){
#                                	$standard_chips = 'Y';
#                        	}
#                	}
#        	}

		$o_cnt1 = 0;
		$o_cnt2 = 0;
		$o_cnt3 = 0;
		$o_cnt4 = 0;
		$o_cnt5 = 0;
		$o_cnt  = 0;
		$no_yes = 0;
		$no_no  = 0;
		foreach $ent ($ccdi0_on, $ccdi1_on, $ccdi2_on, $ccdi3_on, $ccds0_on, $ccds1_on, $ccds2_on,
					$ccds3_on, $ccds4_on, $ccds5_on){
#			if($ent =~ /OPT1/i){$o_cnt1++};
#			if($ent =~ /OPT2/i){$o_cnt2++};
#			if($ent =~ /OPT3/i){$o_cnt3++};
#			if($ent =~ /OPT4/i){$o_cnt4++};
#			if($ent =~ /OPT5/i){$o_cnt5++};
#			if($ent =~ /OPT/i) {$o_cnt++};
			if($ent =~ /O1/i){$o_cnt1++};
			if($ent =~ /O2/i){$o_cnt2++};
			if($ent =~ /O3/i){$o_cnt3++};
			if($ent =~ /O4/i){$o_cnt4++};
			if($ent =~ /O5/i){$o_cnt5++};
			if($ent =~ /^O/i) {$o_cnt++};
			if($ent =~ /Y/i)   {$no_yes++};
			if($ent =~ /N/i)   {$no_no++};
		}
		$ccd_warning = 0;
		if($o_cnt1 > 1 || $o_cnt2 > 1 || $o_cnt3 > 1 || $o_cnt4 > 1 || $o_cnt5 > 1){
				$line = 'You cannot assign the same OPT# on multiple CCDs. ';
				$ccd_warning = 1;
		}else{
			if($o_cnt5 > 0 && ($o_cnt1 == 0  || $o_cnt2 == 0  || $o_cnt3 == 0  || $o_cnt4 == 0)){
				$line = 'Please do not skip OPT#: Use 1, 2, 3, 4, and 5 in order. ';	
				$ccd_warning = 1;
			}elsif($o_cnt4 > 0 && ($o_cnt1 == 0  || $o_cnt2 == 0  || $o_cnt3 == 0)){
				$line = 'Please do not skip OPT#: Use 1, 2, 3, and  4 in order. ';	
				$ccd_warning = 1;
			}elsif($o_cnt3 > 0 && ($o_cnt1 == 0  || $o_cnt2 == 0)){
				$line = 'Please do not skip OPT#: Use 1, 2, and 3 in order. ';	
				$ccd_warning = 1;
			}elsif($o_cnt2 > 0 && $o_cnt1 == 0 ){
				$line = 'Please do not skip OPT#: Use 1  nd 2 in order. ';	
				$ccd_warning = 1;
			}
		}
	
		if($no_yes == 0){
			$ccd_warning = 1;
			if($line eq ''){
				$line = 'There must be at least one CCD with YES. ';
			}else{	
				$line = "$line<br />".' There must be at least one CCD with YES. ';
			}
		}

        	if($ccd_warning == 1){
			if($header_chk == 0){
                		print "<h2><font color=red> Following values are out of range.</font> </h2>";
                		print '<br />';
			}
                	print '<table border= "1" cellpadding="4" >';
                	print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
                	print "<tr><th>CCD Option Selection</th>";
                	print "<td style='text-align:center'><font color=\"red\">";
			
			$chk = $o_cnt + $no_yes;
			if($chk == 0){
				print "CCD# = NO";
			}else{
				foreach $ent ('ccdi0_on', 'ccdi1_on', 'ccdi2_on', 'ccdi3_on', 'ccds0_on', 'ccds1_on', 'ccds2_on',
					'ccds3_on', 'ccds4_on', 'ccds5_on'){
					$e_val = ${$ent};
#					if($e_val =~ /OPT/i){
					if($e_val =~ /^O/i){
						@atemp = split(/_on/, $ent);
						$ccd_ind = uc ($atemp[0]);
						print "$ccd_ind: $e_val<br />";
					}
				}
			}
			print "</font></td>";
                	print "<td><font color=\"green\">$line</font></td></tr>";
                	print '</table>';
        	}
	}


#-----------------------
#------ time order cases
#-----------------------

	for($j = 1; $j <= $time_ordr; $j++){
		$range_ind = 0;
		@out_range = ();
		foreach $in_name ('TSTART', 'TSTOP', 'WINDOW_CONSTRAINT'){
			$name = "$in_name".'.N';
			$lname = lc ($name);
			$lname2 = lc ($in_name);
			${$lname} = ${$lname2}[$j];

            $oin_name = 'orig_'."$in_name";
            $oname = "$oin_name".'.N';
            $olname = lc ($oname);
            $olname2 = lc ($oin_name);
            ${$olname} = ${$olname2}[$j];
		}

		$time_okn = $time_ok[$j];

		foreach $name ('WINDOW_FLAG', 'TSTART.N', 'TSTOP.N', 'WINDOW_CONSTRAINT.N'){
			entry_test();			#----- check the condition
		}

		if($range_ind > 0){			# write html page about bad news
			$error_ind += $range_ind;
			if($header_chk == 0){
				print "<h2><font color=red> Following values are out of range.</font> </h2>";
			}
			$header_chk++;
			print '<br />';
			print '<b>Time Order: ',"$j",'</b><br />';
			print '<br />';
		
			print '<table border= "1" cellpadding="4" >';
			print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
				foreach $ent (@out_range){
				@atemp = split(/<->/,$ent);
				$db_name = $atemp[0];
				find_name();
				print "<tr><th>$web_name ($atemp[0])</th>";
				print "<td style='text-align:center'><font color=\"red\">$atemp[1]</font></th>";
				print "<td><font color=\"green\">$atemp[2]</font></th></tr>";
			}
			print '</table>';
		}

#
#--- preference/constraints change check
#
        foreach $aname ('WINDOW_FLAG', 'TSTART.N', 'TSTOP.N', 'WINDOW_CONSTRAINT.N'){
            $vname = lc($aname);
            $new_val = ${$vname};
            $orig_name = 'orig_'."$vname";
            $orig_val = ${$orig_name};
    
            compare_to_original_val($vname, $new_val, $orig_val);
        }
	}

#-------------------------
#------- roll order cases
#-------------------------

	for($j = 1; $j <= $roll_ordr; $j++){
		$range_ind = 0;
		@out_range = ();

		$isdigit = 1;
		$rline   = '';
		foreach $in_name ('ROLL_CONSTRAINT','ROLL_180','ROLL','ROLL_TOLERANCE'){
			$name = "$in_name".'.N';
			$lname = lc ($name);
			$lname2 = lc ($in_name);
			${$lname} = ${$lname2}[$j];

            		$oin_name = 'orig_'."$in_name";
            		$oname = "$oin_name".'.N';
            		$olname = lc ($oname);
            		$olname2 = lc ($oin_name);
            		${$olname} = ${$olname2}[$j];
	
			if(($in_name eq 'ROLL') || ($in_name eq 'ROLL_TOLERANCE')){
				@ctemp = split(//, ${$lname});
				foreach $etest (@ctemp){
					if($etest =~ /\d/ || $etest =~ /\./){
						#--- donothing;
					}else{
						$isdigit = 0;
						break;
					}
				}
				if(${$lname} eq ''){
					$isdigit = 1;
				}
				if($isdigit == 0){
					$rline = "$rline".'<table border=1>';
					$rline = "$rline".'<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
					$rline = "$rline"."<tr><th>$in_name</th>";
					$rline = "$rline"."<th style='color:red;text-align:center'>${$lname}</th>";
					$rline = "$rline"."<th style='color:green'>number (digit & '.')</th></tr>";
					$rline = "$rline"."</table><br />";
				}
			}
		}

		foreach $name ('ROLL_FLAG','ROLL_CONSTRAINT.N','ROLL_180.N','ROLL.N','ROLL_TOLERANCE.N'){
			entry_test();			#----- check the condition
		}

		if($range_ind > 0 || $isdigit == 0){			# write html page about bad news
			$error_ind += $range_ind;
			print '<br />';
			print '<b>Roll Order: ',"$j",'</b><br />';
			if($header_chk == 0){
				print "<h2><font color=red> Following values are out of range.</font> </h2>";
				print '<br />';
			}
			$header_chk++;

			if($isdigit == 0){
				print $rline;
			}
			if($range_ind > 0){	
				print '<table border= "1" cellpadding="4" >';
				print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
					foreach $ent (@out_range){
					@atemp = split(/<->/,$ent);
					$db_name = $atemp[0];
					find_name();
					print "<tr><th>$web_name ($atemp[0])</th>";
					print "<td style='text-align:center'><font color=\"red\">$atemp[1]</font></th>";
					print "<td><font color=\"green\">$atemp[2]</font></th></tr>";
				}
				print '</table>';
			}
		}
#
#--- preference/constraints change check
#
        foreach $aname ('ROLL_FLAG','ROLL_CONSTRAINT.N','ROLL_180.N','ROLL.N','ROLL_TOLERANCE.N'){
            $vname = lc($aname);
            $new_val = ${$vname};
            $orig_name = 'orig_'."$vname";
            $orig_val = ${$orig_name};
    
            compare_to_original_val($vname, $new_val, $orig_val);
        }
	}

#-----------------------
#--- acis subarray case 
#-----------------------

#	if($si_mode !~ /\w/ && $subarray =~ /YES/i){
#			$range_ind = 0;
#
#			if($header_chk == 0){
#				print "<h2><font color=red> Following values are out of range.</font> </h2>";
#				print '<br />';
#			}
#
#			$header_chk++;
#			print '<table border= "1" cellpadding="4" >';
#			print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
#			print '<tr><th>Use Subarray(SUBARRAY)</th>';
#			print '<td><font color="red">CUSTOM</font></td>';
#			print '<td><font color="green">A value for <b><i>SI Mode (SI_MODE)</b></i>';
#			print ' is required</td></tr>';
#			print '</table>';
#			$range_ind++;
#			$error_ind += $range_ind;
#	}

#---------------------------------------
#--- acis i<-->s change in ACIS Parameter: added 09/26/11
#---------------------------------------

	if(($orig_instrument !~ /ACIS-I/i && $instrument =~ /ACIS-I/i && $grating =~ /N/i)
		|| ($orig_instrument =~ /ACIS-I/i && $orig_grating !~ /N/ && $instrument =~ /ACIS-I/i && $grating =~ /N/i)) {

		if($multiple_spectral_lines =~ /n/i || $spectra_max_count =~ /n/i || $spectra_max_count eq ''){

			if($header_chk == 0){
				 print "<h2><font color=red> Following values are out of range.</font> </h2>";
				print '<br />';
			}

			$header_chk++;
			print '<table border= "1" cellpadding="4" >';
			print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
			if($multiple_spectral_lines =~ /n/i){
				print '<tr><th>Multiple Spectral Lines</th>';
				print "<td style='text-align:center'><font color='red'>$multiple_spectral_lines</td>";
				print '<td><font color="green">YES</td>';
				print '</tr>';
			}
			if($spectra_max_count =~ /n/i || $spectra_max_count eq ''){
				print '<tr><th>Spectral Max Count</th>';
				print "<td><font color='red'>$spectra_max_count</td>";
				print '<td><font color="green">1-1000000</td>';
				print '</tr>';
			}
			print '<tr>';
			print '<td colspan=3 style="color:red">You can find these requirements in the RPS forms.</td>';
			print '</tr>';
			print '</table>';
		}
	}
				

#-----------------------
#----- acis window cases
#-----------------------

	if($instrument =~ /ACIS/){

		$wcnt = 0;
		for($j = 0; $j < $aciswin_no; $j++){
			$jj = $j + 1;
			$range_ind       = 0;
			$acis_order_head = 0;
			@out_range       = ();

			$chk_pha_range = 0;
			foreach $in_name ('ORDR', 'CHIP','INCDLUDE_FLAG','START_ROW','START_COLUMN','HEIGHT','WIDTH',
						'LOWER_THRESHOLD','PHA_RANGE','SAMPLE'){
				$name     = "$in_name".'.N';
				$lname    = lc ($name);
				$lname2   = lc ($in_name);
				${$lname} = ${$lname2}[$j];

                $oin_name = 'orig_'."$in_name";
                $oname = "$oin_name".'.N';
                $olname = lc ($oname);
                $olname2 = lc ($oin_name);
                ${$olname} = ${$olname2}[$j];

				if($name =~ /PHA_RANGE/i && ${$lname} > 13){
					$chk_pha_range++;
				}

			}
	
			$name      = 'instrument'.'.n';
			${$name}   = $instrument;
			$test_inst = 'aciswin';			# this one will be used if the instrument is changed
#
#---- if the entry is removed from the acis window constrints, skip the test.
#	
			if($lname2 =~ /ordr/i && ${$lname} =~ /\d/){
				foreach $name ('INSTRUMENT.N','SPWINDOW','ORDR.N', 'CHIP.N','INCDLUDE_FLAG.N','START_ROW.N','START_COLUMN.N',
						'HEIGHT.N','WIDTH.N', 'LOWER_THRESHOLD.N','PHA_RANGE.N','SAMPLE.N'){

					entry_test();			#----- check the condition
				}
#
#--- preference/constraints change check
#
				foreach $aname ('INSTRUMENT.N','SPWINDOW','ORDR.N', 'CHIP.N','INCDLUDE_FLAG.N','START_ROW.N','START_COLUMN.N',
						'HEIGHT.N','WIDTH.N', 'LOWER_THRESHOLD.N','PHA_RANGE.N','SAMPLE.N'){
                    $vname = lc($aname);
                    $new_val = ${$vname};
                    $orig_name = 'orig_'."$vname";
                    $orig_val = ${$orig_name};
         
                    compare_to_original_val($vname, $new_val, $orig_val);
                }
			}

#
#--- added 08/04/11
#
			if($chk_pha_range > 0){
				if($wcnt == 0){
					print "<h3><font color=fuchsia > Warning: PHA_RANGE >= 13:</font> <br />";
					print "In many configurations, an Energy Range above 13 keV will risk telemetry saturation.</h3>";
					print "<br />";
					$wcnt++;
				}
			}
					

			if($range_ind > 0){			# write html page about bad news
				$error_ind += $range_ind;
				if($header_chk == 0){
					print "<h2><font color=red> Following values are out of range.</font> </h2>";
					print '<br />';
				}
				$header_chk++;

				print '<br />';
				print '<b>Acis Window Entry: ',"$jj",'</b><br />';
				$acis_order_head++;
			
				print '<table border= "1" cellpadding="4" >';
				print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
				foreach $ent (@out_range){
					@atemp = split(/<->/,$ent);
					$db_name = $atemp[0];
					find_name();
					print "<tr><th>$web_name ($atemp[0])</th>";
					print "<td style='text-align:center'><font color=\"red\">$atemp[1]</font></td>";
					print "<td><font color=\"green\">$atemp[2]</font></td></tr>";
				}
				print '</table>';

                        }elsif($eventfilter_lower  > 0.5 || $awc_l_th == 1){

#------------------------------------------------------------------------------------
#--- this is a special case that ACIS energy fileter lowest energy is set > 0.5 keV.
#--- in this case, you need to fill ACIS window constraints
#------------------------------------------------------------------------------------

                                $ocnt = 0;
                                for($m = 0; $m < 4; $m++){
                                        $name = 'ccdi'."$m".'_on';
                                        if(${$name} =~ /Y/i || ${$name} =~ /OPT/i){
                                                $ocnt++;
                                        }
                                }
                                for($m = 0; $m < 6; $m++){
                                        $name = 'ccds'."$m".'_on';
                                        if(${$name} =~ /Y/i || ${$name} =~ /OPT/i){
                                                $ocnt++;
                                        }
                                }
                                if($ocnt > $aciswin_no){
                                        if($header_chk == 0){
                                                print "<h2><font color=red> Following values are out of range.</font> </h2>";
                                                print '<br />';
                                        }
                                        $header_chk++;

					if($do_not_repeat != 1){
                                        	print '<table border= "1" cellpadding="4" >';
                                        	print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
                                        	print "<tr><th>Energy Filter Lowest Energy</th>";
                                        	print "<td style='text-align:center'><font color=\"red\">\>0.5 keV </td>";
                                        	print "<td><font color=\"green\">Spatial Window param  must be filled";
                                        	print "<br />(just click PREVIOUS PAGE)</td>";
                                        	print '</table>';
						$do_not_repeat = 1;
					}
                                }
                        }

			if($lower_threshold[$j] < $eventfilter_lower && $lower_threshold[$j] ne ''){
				if($header_chk == 0){
					print "<h2><font color=red> Following values are out of range.</font> </h2>";
					print '<br />';
				}
				$header_chk++;

				if($acis_order_head == 0){
					print '<br />';
					print '<b>Acis Window Entry: ',"$jj",'</b><br />';
					$acis_order_head++;
				}

				print '<table border= "1" cellpadding="4" >';
				print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
				print "<tr><th>ACIS Lowest Threshold</th><td style='text-align:center'><font color=\"red\">$lower_threshold[$j]</font></th>";
				print "<td><font color=\"green\">lower_threshold must be larger than or equal to eventfilter_lower ($eventfilter_lower)</tr></tr>";
				print '</table>';
			}
			if($pha_range[$j] > $eventfilter_higher && $pha_range[$j] ne ''){
				if($header_chk == 0){
					print "<h2><font color=red> Following values are out of range.</font> </h2>";
					print '<br />';
				}
				$header_chk++;

				if($acis_order_head == 0){
					print '<br />';
					print '<b>Acis Window Entry: ',"$jj",'</b><br />';
					$acis_order_head++;
				}

				print '<table border= "1" cellpadding="4" >';
				print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
				print "<tr><th>ACIS Energy Range</th><td style='text-align:center'><font color=\"red\">$pha_range[$j]</font></th>";
				print "<td><font color=\"green\">energy_range must be smaller than or equal to eventfilter_higher ($eventfilter_higher)</tr></tr>";
				print '</table>';
			}
		}
	}

#--------------------------------
#--- group_id/monitor_flag case
#--------------------------------

	if($monitor_flag =~ /Y/i){

		if($group_id){
			if($header_chk == 0){
				print "<h2><font color=red> Following values are out of range.</font> </h2>";
				print '<br />';
			}
			$header_chk++;
			print '<table border= "1" cellpadding="4" >';
			print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
			print "<tr><th>Monitor Flag</th><td style='text-align:center'><font color=\"red\">$monitor_flag</font></th>";
			print "<td><font color=\"green\">A monitor_flag must be NULL or change group_id</th></tr>";
			print '</table>';

		}elsif($pre_min_lead eq '' || $pre_max_lead eq ''){
			if($header_chk == 0){
				print "<h2><font color=red> Following values are out of range.</font> </h2>";
				print '<br />';
			}
			$header_chk++;
			print '<table border= "1" cellpadding="4" >';
			print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
			print "<tr><th>Monitor Flag</th><td style='text-align:center'><font color=\"red\">$monitor_flag</font></th>";
			print "<td><font color=\"green\">A monitor_flag must be NULL or add pre_min_lead and pre_max_lead</th></tr>";
			print '</table>';
		}
	}

	if($group_id){

		if($monitor_flag =~ /Y/i){
			if($header_chk == 0){
				print "<h2><font color=red> Following values are out of range.</font> </h2>";
				print '<br />';
			}
			$header_chk++;
			print '<table border= "1" cellpadding="4" >';
			print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
			print "<tr><th>Group ID</th><td style='text-align:center'><font color=\"red\">$group_id</font></th>";
			print "<td><font color=\"green\">A group id must be NULL or change monitor_flag</th></tr>";
			print '</table>';

		}elsif($pre_min_lead eq '' || $pre_max_lead eq ''){
			if($header_chk == 0){
				print "<h2><font color=red> Following values are out of range.</font> </h2>";
				print '<br />';
			}
			$header_chk++;
			print '<table border= "1" cellpadding="4" >';
			print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
			print "<tr><th>Group ID</th><td style='text-align:center'><font color=\"red\">$group_id</font></th>";
			print "<td><font color=\"green\">A group_id must be NULL or add pre_min_lead and pre_max_lead</th></tr>";
			print '</table>';
		}
	}

	if($pre_id == $obsid){

		if($header_chk == 0){
			print "<h2><font color=red> Following values are out of range.</font> </h2>";
		 	print '<br />';
		}
		$header_chk++;
		print '<table border= "1" cellpadding="4" >';
		print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
		print "<tr><th>Follows ObsID#</th><td style='text-align:center'><font color=\"red\">$pre_id</font></th>";
		print "<td><font color=\"green\">pre_id must be different from the ObsID of this observation ($obsid) </th></tr>";
		print '</table>';
	}

	if($pre_min_lead > $pre_max_lead){

		if($header_chk == 0){
			print "<h2><font color=red> Following values are out of range.</font> </h2>";
			print  '<br />';
		}
		$header_chk++;
		print '<table border= "1" cellpadding="4" >';
		print '<tr><th>Parameter</th><th>Requested Value</th><th>Possible Values</th></tr>';
		print "<tr><th>Min Int</th><td style='text-align:center'><font color=\"red\">$pre_min_lead</font></th>";
		print "<td><font color=\"green\">pre_min_lead must be smaller than pre_max_lead ($pre_max_lead)</th></tr>";
		print '</table>';
	}
#
#--- preference/constraints change check
#
	foreach $aname ('CONSTR_IN_REMARKS','PHASE_CONSTRAINT_FLAG', 'PHASE_EPOCH', 'PHASE_PERIOD', 'PHASE_START', 'PHASE_START_MARGIN', 'PHASE_END', 'PHASE_END_MARGIN',
                    'GROUP_ID', 'MONITOR_FLAG', 'PRE_ID', 'PRE_MIN_LEAD', 'PRE_MAX_LEAD', 'MULTITELESCOPE', 'OBSERVATORIES', 'MULTITELESCOPE_INTERVAL'){
        $vname = lc($aname);
        $new_val = ${$vname};
        $orig_name = 'orig_'."$vname";
        $orig_val = ${$orig_name};
         
        compare_to_original_val($vname, $new_val, $orig_val);
    }

#    foreach $name ('DITHER_FLAG', 'Y_AMP', 'Y_FREQ', 'Y_PHASE', 'Z_AMP', 'Z_FREQ', 'Z_PHASE'){
#        $vname = lc($aname);
#        $new_val = ${$vname};
#        $orig_name = 'orig_'."$vname";
#        $orig_val = ${$orig_name};
#         
#        compare_to_original_val($vname, $new_val, $orig_val);
#    }

#
#--- print perference/constraint change warning
#
    if($pwarning_cnt > 0){
        print_pwarning();
    }
  
	print '<br /><br />';

#---------------------------------------------------------------
#----- print all paramter entries so that a user verifies input
#---------------------------------------------------------------

	submit_entry();
}

###########################################################################################################
#### compare_to_original_val: sending a warning if there is preference/costraint changes                ####
############################################################################################################

sub compare_to_original_val{

    my $vname, $new_val, $orig_val;
    ($vname, $new_val, $orig_val) = @_;

    if($vname =~ /\.n/){
        $vname =~ s/\.n//g;
    }

    if($new_val ne '' || $orig_val ne ''){
        if($new_val !~ /$orig_val/i){
            if( $orig_val eq ''){
                $orig_val = "' '";
            }
            push(@pwarning_name_list, $vname);
            push(@pwarning_orig_val,  $orig_val);
            push(@pwarning_new_val,   $new_val);
            $pwarning_cnt++;
        }
    }
}

###########################################################################################################
#### print_pwarning: print out preference/constrain change warning                                      ####
############################################################################################################

sub print_pwarning{
    print '<div style="padding-top:30px;padding-bottom:20px">';
    print '<table border=1 style="width:80%">';

    if($pwarning_cnt > 1){
        print '<tr><th colspan=3  style="color:red">The following changes impact constraints or preferences.<br /> ';
        print 'Verify you have indicated CDO approval in the comments.</th></tr>';
    }else{
        print '<tr><th colspan=3 style="color:red">The following change impacts a constraint or preference.<br /> ';
        print 'Verify you have indicated CDO approval in the comments.</td></tr>';
    }
    print '<tr><th>Parameter</th><th>Original Value</th><th>New Value</th></tr>';
    for($i = 0; $i < $pwarning_cnt; $i++){
        $vname = $pwarning_name_list[$i];
        $o_val = $pwarning_orig_val[$i];
        $n_val = $pwarning_new_val[$i];
     
        $db_name = $vname;
        find_name();
        $uvname = uc($vname);
     
        if($web_name eq ''){
            print "<tr><td style='text-align:center'><b>$uvname</b></td>";
        }else{
            print "<tr><td style='text-align:center'><b>$web_name ($uvname)</b></td>";
        }
	$eo_val = $o_val;
	if($o_val =~ /\'/){
		$eo_val = $blank;
	}
        print "<td style='text-align:center'>$eo_val</td>";
        print "<td style='text-align:center'>$n_val</td></tr>";
    }
    print '</tr></table>';
    print '</div>';
}

###########################################################################################################
### entry_test: check input value range and restrictions                                               ####
###########################################################################################################

sub entry_test{

	$uname = lc ($name);		# $name is a parameter name
	
#---------------------------------------------
#----- check whether the entry is digit or not
#---------------------------------------------

	$digit = 0;

	@ctemp = split(//, ${$uname});			
	OUTER:
	foreach $comp (@ctemp){
		if($comp eq '+' || $comp eq '-' || $comp =~/\d/ || $comp =~ /\./){
			$digit = 1;
		}else{
			$digit = 0;
			last OUTER;
		}
	}

#--------------------------------------------------------------
#----- if there any conditions, procceed to check the condtion
#--------------------------------------------------------------

	unless(${condition.$name}[0]  =~ /OPEN/i){
		$rchk = 0;				# comparing the data to the value range

#--------------------------------------------
#----- for the case that the condition is CDO
#--------------------------------------------

		if(${condition.$name}[0] =~ /CDO/i){
			$original = "orig_$uname";
			if(${$original} ne ${$uname}){
				@{same.$name} = @{condition.$name};
				shift @{condition.$name};
				push(@{condition.$name},'<font color=red>Has CDO approved this change?</font>');
				$rchk++;
#
#--- keep CDO warning
#
				if($original =~ /\s+/ || $original eq ''){
					$wline = "$uname is changed from $blank} to  ${$uname}";
				}else{
					$wline = "$uname is changed from $original} to  ${$uname}";
				}
				push(@cdo_warning, $wline);
				$cdo_w_cnt++;
			}
		}

		OUTER:
		foreach $ent (@{condition.$name}){
#---------------------------------------------
#---- check whether condition is value ranges
#---------------------------------------------

			@atemp = split(/\(/,$ent);	# the range is numbers
			if($ent =~ /NULL/i && (${$uname} eq '' || ${$uname}=~ /\s+/)){
				$rchk = 0;
				last OUTER;
			}			

			if($ent =~ /NULL/i || $ent =~ /CDO/i || $ent =~ /DEFAULT/i){
				if(${$uname} =~ /$ent/){
					$rchk = 0;
					last OUTER;
				}
			}elsif($ent =~  /MUST/i){
				if(${$uname} eq '' || ${$uname} =~ /NULL/i || ${$uname} =~ /\s+/){
					$rchk++;
				}else{
					$rchk =0;
				}
				last OUTER;
			}elsif($atemp[1] eq '+' || $atemp[1] eq '-' || $atemp[1] =~ /\d/){
				@btemp = split(/\)/, $atemp[1]);
				@data  = split(/<>/, $btemp[0]);
				if($digit == 0){
					$digit = 1;
					$rchk++;
					last OUTER;
				}
				if($digit == 1 && (${$uname} <  $data[0] || ${$uname} > $data[1])){
					$rchk++;
					last OUTER;
				}

#--------------------------------------------------
#---- check whether there is a special restriction
#--------------------------------------------------

			}elsif(($ent =~ /REST/i) && ( ${$uname} ne '' || ${$uname} !~/\s/)){		# it has a special restriction
					$rchk = 0;
					last OUTER;
			}else{

#----------------------------------------------
#---- check the case that the condition is word
#----------------------------------------------

				if($digit == 0 && ${$uname} ne '' && ${$uname} !~/\s+/){	# the condition is in words
					$rchk++;
					if(${$uname} eq $ent){
						$rchk = 0;
						last OUTER;
					}
				}
			}
		}
	
#-----------------------------------------------------------------
#------- special case: if tstart and tstop is out of order, say so
#-----------------------------------------------------------------

		if($uname =~/^TSTART/i || $uname =~/^TSTOP/i){
			if($time_okn == 1){
				@{same.$name}      = @{condition.$name};
				@{condition.$name} = ("Out of Order");
				$digit = 0;
				$rchk++;
			}
		}

#--------------------------------------------------------------------
#----- if the value is out of range, start writing it into @out_range
#--------------------------------------------------------------------

		if($rchk > 0){				
			$range_ind++;			
			if($digit == 0){
				$line = "$name<->${$uname}<->@{condition.$name}";
				$sind = 0;
				if(${condition.$name}[0] =~ /MUST/){
					$line = "$name<->${$uname}<-> 'Must Have a Value'";
				}
				@{same.$name}      = @{condition.$name};

#-----------------------------------------------------------------
#---- extra restriction check, if there is violation, add comment
#-----------------------------------------------------------------

				restriction_check();	#----- sub to check an extra restriction

				if($sind > 0){		
					$line = "$line<br />"."$add";
				}
			 	push(@out_range,$line);
				@{condition.$name}= @{same.$name};
			}else{
				@{same.$name}      = @{condition.$name};
				if(${condition.$name}[0] =~ /NULL/i){
					$add = 'NULL '."$data[0]<-->$data[1]";
				}else{
					$add = "$data[0]<---->$data[1]";
				}
				$line = "$name<->${$uname}<->$add";
				$sind = 0;
				restriction_check();
				if($sind >  0){
					$line = "$line<br />"."$add";
				}
			 	push(@out_range,$line);
				@{condition.$name}= @{same.$name};
			}
		}else{					

#--------------------------------------------------------------------
#---- the value is in the range, but still want to check restrictions
#--------------------------------------------------------------------

			if( ${$uname} ne '' && ${$uname} !~/\s+/){
				$sind = 0;			
				restriction_check();		#----- sub to check an extra restriction
				if($sind >  0){
					$range_ind++;
					$line = "$name<->${$uname}<->$add";
					push(@out_range,$line);
					@{condition.$name}= @{same.$name};
				}
			}
		}

#-----------------------------------------------
#-----we need to check hrc<---> acis change here
#-----------------------------------------------

		if($uname =~ /^INSTRUMENT/i){

			@acis_param_need = ();	# these two will be used to check hrc to acis change
			$apram_cnt = 0;
			$inst_change = 0;

#---------------------------------------------
#-------- ACIS <---> HRC INSTRUMENT CHANGE!!!
#---------------------------------------------

#--------------------------------------------------------------------------------
#---acis to hrc change saying changed from acis to hrc set all acis param to null
#--------------------------------------------------------------------------------

			if($orig_instrument =~ /^ACIS/i && $instrument =~ /^HRC/i){
				$inst_change    = 1;				
				$exp_mode       = 'NULL';				
				$bep_pack       = 'NULL';
				$frame_time     = '';
				$most_efficient = 'NULL';
#				$standard_chips = 'NULL';
				$ccdi0_on       = 'NULL';
				$ccdi1_on       = 'NULL';
				$ccdi2_on       = 'NULL';
				$ccdi3_on       = 'NULL';
				$ccds0_on       = 'NULL';
				$ccds1_on       = 'NULL';
				$ccds2_on       = 'NULL';
				$ccds3_on       = 'NULL';
				$ccds4_on       = 'NULL';
				$ccds5_on       = 'NULL';
				$subarray       = 'NO';
				$subarray_start_row  = '';
				$subarray_row_count  = '';
				$subarray_frame_time = '';
				$duty_cycle          = 'NULL';
				$secondary_exp_count = '';
				$primary_exp_time    = '';
				$secondary_exp_time  = '';
				$onchip_sum          = 'NULL';
				$onchip_row_count    = '';
				$onchip_column_count = '';
				$eventfilter         = 'NULL';
				$eventfilter_lower   = '';
				$eventfilter_higher  = '';
#
#--- added 03/29/11
#
				$multiple_spectral_lines = '';
				$spectra_max_count       = '';
				$bias                = '';
				$frequency           = '';
				$bias_after          = '';
				$spwindow            = 'NULL';

				for($n = 0; $n < $aciswin_no; $n++){
					$aciswin_id[$n]      = '';
					$ordr[$n]            = '';
					$chip[$n]            = 'NULL';
					$include_flag[$n]    = 'I';
					$start_row[$n]       = '';
					$start_column[$n]    = '';
					$height[$n]          = '';
					$width[$n]           = '';
					$lower_threshold[$n] = '';
					$pha_range[$n]       = '';
					$sample[$n]          = '';
				}
#---------------------------
#---- set aciswin_no to 0
#---------------------------
				$aciswin_no = '0';
				if($test_inst ne 'aciswin'){
					$warning_line = '';

					if($hrc_si_mode eq '' || $hrc_si_mode =~ /NULL/){
						$warning_line = 'The value for <b>HRC_SI_MODE</b> must be provided';
					}

					@{same.$name} = @{condition.$name};
					@{condition.$name} =("<font color=red>Has CDO approved this instrument change?(all ACIS params are NULLed) <br />$warning_line </font>");
					$line = "$name<->${$uname}<->@{condition.$name}";
					push(@out_range,$line);
					@{condition.$name}= @{same.$name};
#
#--- CDO warning
#
					$wline = "$name<->${$uname}";
					push(@cdo_warning, $wline);
					$cdo_w_cnt++;
				}
				$rchk++;

#-----------------------------------------------------------------------
#----- hrc to acis change:saying hrc to acis change set hrc parm to null
#-----------------------------------------------------------------------

			}elsif($orig_instrument =~ /^HRC/i && $instrument =~ /ACIS/i){
				$inst_change     = 2;				
				$hrc_config      = 'NULL';			
				$hrc_zero_block  = 'N';
				$hrc_si_mode     = '';
				$hrc_timing_mode = 'N';
				$warning_line    = '';

				if($test_inst eq 'aciswin'){

					if($spwindow  eq '' || $spwindow  =~ /NULL/){
						$warning_line = 'The value for <b>ACIS Winodw Filter</b> must be provided<br />';
					}
					$test_inst = '';
				}else{
					foreach $test (EXP_MODE,BEP_PACK,MOST_EFFICIENT,CCDI0_ON,CCDI1_ON,
							CCDI2_ON,CCDI3_ON,CCDS0_ON,CCDS1_ON,CCDS2_ON,CCDS3_ON,CCDS4_ON,
							CCDS5_ON,SUBARRAY,DUTY_CYCLE){
						$ltest = lc($test);

						if(${$ltest} eq '' || ${$ltest} =~ /NULL/){
							$warning_line = "$warning_line"."The value for <b>$test</b> must be provided<br />";
						}
					}
				}

				@{same.$name}      = @{condition.$name};
				@{condition.$name} = ("<font color=red>Has CDO approved this instrument change? (All HRC params are NULLed)<br />$warning_line</font>");
				$line              = "$name<->${$uname}<->@{condition.$name}";
				push(@out_range,$line);
				@{condition.$name}= @{same.$name};
				$rchk++;
#
#---CDO warning
#
				$wline = "$name<->${$uname}";
				push(@cdo_warning, $wline);
				$cdo_w_cnt++;
			}
			if($rchk > 0){
				$range_ind++;
			}
		}

#-----------------------
#----- grating case: CDO
#-----------------------

		if($uname =~ /^GRATING/i){

			if($orig_grating ne $grating){
				@{same.$name}      = @{condition.$name};
				@{condition.$name} = ("<font color=red>CDO approval is required </font>");
				$line              = "$name<->${$uname}<->@{condition.$name}";
				push(@out_range,$line);
				@{condition.$name}= @{same.$name};
				$rchk++;
#
#---CDO warning
#
				$wline = "$name<->${$uname}";
				push(@cdo_warning, $wline);
				$cdo_w_cnt++;
			}
			if($rchk > 0){
				$range_ind++;
			}
		}
#------------------
#---- obj_flag case
#------------------

		if($uname =~ /^OBJ_FLAG/i){

			if($orig_obj_flag ne $obj_flag){
				@{same.$name}      = @{condition.$name};
				@{condition.$name} = ("<font color=red>CDO approval is required </font>");
				$line              = "$name<->${$uname}<->@{condition.$name}";
				push(@out_range,$line);
				@{condition.$name}= @{same.$name};
				$rchk++;
#
#---CDO warning
#
				$wline = "$name<->${$uname}";
				push(@cdo_warning, $wline);
				$cdo_w_cnt++;
			}
			if($rchk > 0){
				$range_ind++;
			}
		}
#---------------------------------------------------------------------
#----ra/dec case:  a new and old positional difference must be in 0.5
#---------------------------------------------------------------------

		if($uname =~ /^DEC/i){
			$rtemp = split(/:/,$ra);

			if($rtemp[1] =~ /\d/){
				$tra   = 15.0 * ( $rtemp[0] + $rtemp[1]/60 + $rtemp[2]/3600);
			}else{
				$tra  = $ra;
			}

			$dtemp = split(/:/,$dec);
			if($dtemp[1] =~ /\d/){
				$frac  = $dtemp[1]/60  + $dtemp[2]/3600;

				if($dtemp[0] < 0 || $dtemp[0] =~ /-/){
					$tdec = $dtemp[0] - $frac;
				}else{	
					$tdec = $dtemp[0] + $frac;
				}
			}else{
				$tdec = $dec;
			}

####			$diff = abs($orig_ra - $tra) + abs($orig_dec - $tdec); 
			$diff_ra  = abs($orig_ra - $tra) * cos(abs(0.5 * ($orig_dec + $tdec)/57.2958));
			$diff_dec = abs($orig_dec - $tdec);
			$diff     = sqrt($diff_ra * $diff_ra + $diff_dec * $diff_dec);


			if($diff > 0.1333){
				@{same.$name} = @{condition.$name};
#				@{condition.$name} =("<font color=red>Positional difference of RA+DEC is large; CDO approval is required </font>");
				$wline = '1) No changes can be requested until the out of range is corrected. ';
				$wline = "$wline".'please use the back button to correct out of range requests.<br />';

				$wline = "$wline".'2) If you desire CDO approval please use the Helpdesk (link) and select ';
				$wline = "$wline".'obscat changes.';

				@{condition.$name} = ("<font color=red>$wline<\/font>");

				$line = "$name<->RA+DEC > 8 arcmin<->@{condition.$name}";
				push(@out_range,$line);
				@{condition.$name}= @{same.$name};
				$rchk++;
#
#---CDO warning
#
				$wline = "$name<->RA+DEC > 8 arcmin";
				push(@cdo_warning, $wline);
				$cdo_w_cnt++;
			}
			if($rchk > 0){
				$range_ind++;
			}
		}

#---------------------------------------------------------------------
#-- y/z det offset: change must be less than equal to 10 arc min  ----
#---------------------------------------------------------------------

        if($uname =~/y_det_offset/i){
            $ydiff = $orig_y_det_offset - $y_det_offset;
            $zdiff = $orig_z_det_offset - $z_det_offset;

            $diff = sqrt($ydiff * $ydiff + $zdiff * $zdiff);


            if($diff >= 10){
                @{same.$name} = @{condition.$name};
                $wline = '1) No changes can be requested until the out of range is corrected. ';
                $wline = "$wline".'please use the back button to correct out of range requests.<br />';

                $wline = "$wline".'2) If you desire CDO approval please use the Helpdesk (link) and select ';
                $wline = "$wline".'obscat changes.';

                @{condition.$name} = ("<span style='olor:red'>$wline<\/span>");

                $line = "y/z_offset<->Y/Z Offset > 10 arcmin<->@{condition.$name}";
                push(@out_range,$line);
                @{condition.$name}= @{same.$name};
                $rchk++;
#
#---CDO warning
#
                $wline = "y/z_offset<->Y/Z Offset >= 10 arcmin";
                push(@cdo_warning, $wline);
                $cdo_w_cnt++;
            }
            if($rchk > 0){
                $range_ind++;
            }
        }

#-------------------------
#----- multitelescope case
#-------------------------

		if($uname =~ /^MULTITELESCOPE/i){

			if($orig_multitelescope ne $multitelescope){
				@{same.$name}      = @{condition.$name};
				@{condition.$name} = ("<font color=red>CDO approval is required </font>");
				$line              = "$name<->${$uname}<->@{condition.$name}";
				push(@out_range,$line);
				@{condition.$name} = @{same.$name};
				$rchk++;
#
#---CDO warnine
#
				$wline = "$name<->${$uname}";
				push(@cdo_warning, $wline);
				$cdo_w_cnt++;
			}
			if($rchk > 0){
				$range_ind++;
			}
		}

#------------------------
#----- observatories case
#------------------------

		if($uname =~ /^OBSERVATORIES/i){

			if($orig_observatories ne $observatories){
				@{same.$name}      = @{condition.$name};
				@{condition.$name} = ("<font color=red>CDO approval is required </font>");
				$line              = "$name<->${$uname}<->@{condition.$name}";
				push(@out_range,$line);
				@{condition.$name}= @{same.$name};
				$rchk++;
#
#---CDO warning
#
				$wline = "$name<->${$uname}";
				push(@cdo_warning, $wline);
				$cdo_w_cnt++;
			}
			if($rchk > 0){
				$range_ind++;
			}
		}
	}
}  

###################################################################
###  restriction_check: check special restrictions for input   ####
###################################################################

sub restriction_check{

	$add = '';
	for($m = 0; $m < ${restcnt.$name}; $m++){       # loop around # of restriction entries
		$chname = lc (${rest.$m.$name});	# name of params which need to be checked

		if($chname ne 'NONE'){			# if it is none, we do not need to worry
			$cnt = 0;
			$rest_ind = 0;
			OUTER:
			foreach $ent (@{condition.$name}){
				@atemp = split(//,$ent);
				if($ent eq 'REST'){
					$rest_ind++;
					last OUTER;

#-------------------------------
#------ digit value range check
#-------------------------------

				}elsif($digit == 1 && ($atemp[1] eq '+' || $atemp[1] eq '-' || $atemp[1] =~ /\d/)){
					@btemp = split(/\(/, $ent);
					@ctemp = split(/\)/, $btemp[1]);
					@dat   = split(/<>/, $ctemp[0]);

					if(${$uname} >= $dat[0] && ${$uname} <= $dat[1]){
						last OUTER;
					}else{
						$cnt++;
					}
				}elsif(${$uname} eq $ent){
					last OUTER;
				}else{
					$cnt++;
				}
			}


			@atemp = split(/\(/, ${restcnd.$m.$name}[$cnt]);
			@btemp = split(/\)/, $atemp[1]);

			$comp_val = ${$chname};
			if(${$chname} eq ''){
				$comp_val ='NULL';
			}
			$db_name   = $chname;
			find_name();
			$web_name1 = $web_name;

#--------------------------
#------ restriction check
#--------------------------

			if($rest_ind > 0){
				if($btemp[0] eq 'MUST'){
					if($comp_val eq 'NULL'){
						$add =  "$add"."A value for <i><b>$web_name1 ($chname)</i></b> is required.<br />";
						$sind++;
					}
				}elsif($btemp[0] eq 'NULL'){
					if($comp_val ne 'NULL'){
						$db_name = $name;
						find_name();
						$add = "$add"."A value for <i><b>$web_name1 ($chname)</i></b> must be ";
						$add = "$add"."<font color=\"magenta\">NULL</font>,<br />";
						$add = "$add"."or change the value for <i><b>$web_name ($name)</i></b><br />";
						$sind++;
					}
				}elsif($btemp[0] =~ /^N/i){
					if($comp_val ne 'N' && $comp_val ne 'NULL' && $comp_val ne 'NONE' && $comp_val ne 'NO'){
						$db_name = $name;
						find_name();
						$add = "$add"."A value for <i><b>$web_name1 ($chname)</i></b> must be ";
						$add = "$add"."<font color=\"magenta\">NULL or NO</font>,<br />";
						$add = "$add"."or change the value for <i><b>$web_name ($name)</i></b><br />";
						$sind++;
					}
				}else{
					if($comp_val ne $btemp[0] && $btemp[0] ne 'OPEN' && $btemp[0] ne ''){
						$db_name = $name;
						find_name();
						$add = "$add"."A value for <i><b>$web_name1 ($chname)</i></b> must be ";
						$add = "$add"."<font color=\"magenta\">$btemp[0]</font>,<br />";
						$add = "$add"."or change the value for <i><b>$web_name ($name)</i></b><br />";
						$sind++;
					}
				}
			}elsif((${restcnd.$m.$name}[$cnt] ne '')  && ($comp_val ne $btemp[0])){
				if(($comp_val eq 'NULL') && ($btemp[0] eq 'OPEN')){
				}else{
					$db_name = ${rest.$m.$name};
					find_name();
					$web_name2 = $web_name;

					if($btemp[0] eq 'OPEN'){
#					       $add = "$add"."<i><b>$web_name2 (${rest.$m.$name})</i></b> must not be set.<br /> ";
					}elsif($btemp[0] eq 'MUST'){
						if($comp_val eq '' || $comp_val eq 'NONE' || $comp_val eq 'NULL'){
							$add = "$add"."A value for <i><b>$web_name2 (${rest.$m.$name})</i></b> ";
							$add = "$add"."is required.<br />";
						$sind++;
						}
					}elsif($btemp[0] =~  /^N/i){
						if($comp_val ne 'N' && $comp_val ne 'NULL' &&  $comp_val ne 'NONE'){
							$db_name = $name;
							find_name();
							$add = "$add"."A value for <i><b>$web_name1 ($chname)</i></b> must be ";
							$add = "$add"."<font color=\"magenta\">NULL or NO</font>,<br />";
							$add = "$add"."or change the value for <i><b>$web_name ($name)</i></b><br />";
							$sind++;
						}
					}else{
						$add = "$add"."A value for <i><b>$web_name2 (${rest.$m.$name})</i></b> ";
						$add = "$add"."must be <font color=\"magenta\">$btemp[0]</font>,<br />";
						$sind++;
					}
#					if($btemp[0] ne 'MUST' && $btemp[0] ne 'OPEN'){
#						$db_name = $name;
#						find_name();
#						$add = "$add"."A value for <i><b>$web_name ($chname)</i></b> must be ";
#						$add = "$add"."<font color=\"magenta\">NULL or NO</font>,<br />";
#						$add = "$add"."or change the value for <i><b>$web_name ($name)</i></b><br />";
#					}
				}
			}
		}
	}
}


###################################################################
### print_clone_page: print comment entry for clone case       ####
###################################################################

sub print_clone_page{

	print '<table>';
        print '<tr><td colspan=3>';
        print '<b> Please write why you want to make a clone of this observation in the comment area.<br /> </td></tr>';
        print '<tr>';
        print '<th  valign=top><a href="#" onClick="WindowOpen(comments);return false;"> Comments</a>:</th><td>';
        print '<textarea name="COMMENTS" rows="3" cols="60" WRAP=virtual>',"$comments",'</textarea>';
        print '</td></tr>';
        print '</table>';

	print '<b>Username : </b><input type="text" name="USER" size="12" value="',"$submitter",'" >';
	print '<input type="submit" name="Check"  value="Submit Clone">';
	print '<input type="submit" name="Check"  value="Previous Page">';

	print '<input type="HIDDEN" name="ASIS" value="CLONE">';
	
	foreach $name (@paramarray){
		$lname = lc ($name);
		$value = ${$lname};
		print '<input type="HIDDEN" name="',"$name",'" value="',"$value",'">';
	}
}




###################################################################
### read_range: read conditions                                ####
###################################################################

sub read_range{

	@name_array = ();

#-------------------------------------------------------------
#---- the conditions/restrictions are in the file "ocat_values
#-------------------------------------------------------------

	open(FH,"$data_dir/ocat_values");
	OUTER:
	while(<FH>){
		chomp $_;
		@atemp = split(/\t+/,$_);
		@btemp = split(//,$_);

		if($btemp[0] eq '#'){		   		# pass comment lines
			next OUTER;
		}
		if($instrument     =~ /HRC/i  && $atemp[0] =~ /A/i){
			next OUTER;
		}elsif($instrument =~ /ACIS/i && $atemp[0] =~ /H/i){
			next OUTER;
		}

		@line = ();
		shift(@atemp);


		foreach $ent (@atemp){		  		# pick up only real entries
				
			$ent = uc ($ent);
			push(@line,$ent);
		}

		push(@name_array, $line[1]);	    		# name of the value

		${cndno.$line[1]} = 0;

		if($line[2] eq 'OPEN'){		 		# value range, if it is Open, just say so
			@{condition.$line[1]} = ('OPEN');
			${cndno.$line[1]}++;

		}elsif($line[2] eq 'REST'){	     		# the case which restriction attached
			@{condition.$line[1]} = ('REST');
			${cndno.$line[1]}++;

		}elsif($line[2] eq 'MUST'){	     		# the case which restriction attached
			@{condition.$line[1]} = ('MUST');
			${cndno.$line[1]}++;

		}else{				  		# check the range of the value
			@{condition.$line[1]} = split(/\,/, $line[2]);
			foreach(@{condition.$line[1]}){
				${cndno.$line[1]}++     	# no of possible condtions
			}
		}

		if($line[3] eq 'NONE'){		 		# restriction checking starts here
			$zero = 0;		      		# here is a no restriction case
			@{rest.$zero.$line[1]} = ('NONE');
			${restcnt.$line[1]} = 1;
		}else{
			@btemp = split(/\;/, $line[3]);
			$ent_cnt = 0;
			foreach(@btemp){
				$ent_cnt++;
			}
			${restcnt.$line[1]} = $ent_cnt;

			for($i = 0; $i < $ent_cnt; $i++){
				@atemp = split(/=/, $btemp[$i]);
				${rest.$i.$line[1]}    = $atemp[0];
				@{restcnd.$i.$line[1]} = split(/\,/, $atemp[1]);
			}
		}
	}
	close(FH);
}

####################################################################################
### read_user_name: reading authorized user names                                ###
####################################################################################

sub read_user_name{
	open(FH, "<$pass_dir/.htgroup");
        while(<FH>){
                chomp $_;
                @user_name = split(/\s/,$_);
        }
        shift(@user_name);
}

###################################################################################
### user_warning: warning a user, a user name mistake                           ###
###################################################################################

sub user_warning {

	print "<br /><br />";
	if($submitter eq ''){
		print "<b>No user name is typed in. </b>";
	}else{
        	print "<b> The user: <font color=magenta>$submitter</font> is not in our database. </b>";
	}
	print "<b> Please go back and enter a correct one (use the Back button on the browser).</b>";
	print "<br /><br />";

        print "</form>";
        print "</body>";
        print "</html>";
}

###################################################################################
### submit_entry: check and submitting the modified input values                ###
###################################################################################

sub submit_entry{

#
#--- counters
#
	$k = 0;						# acisarray counter
	$l = 0; 					# aciswin array counter
	$m = 0;						# generalarray counter

#-----------------------------
#--------- pass the parameters
#-----------------------------

	foreach $ent (@paramarray){
               $new_entry = lc ($ent);
               $new_value = ${$new_entry};

		unless($ent =~ /TSTART/ || $ent =~ /TSTOP/ || $ent =~ /WINDOW_CONSTRAINT/
				|| $ent =~ /ACISTAG/ || $ent =~ /ACISWINTAG/ || $ent =~ /SITAG/ || $ent =~ /GENERALTAG/
			){
			print "<input type=\"hidden\" name=\"$ent\" value=\"$new_value\">";
		}
	}

#-------------------------
#------ hidden values here
#-------------------------

	print "<input type=\"hidden\" name=\"ASIS\" value=\"$asis\">";
	print "<input type=\"hidden\" name=\"CLONE\" value=\"$clone\">";
	print "<input type=\"hidden\" name=\"SUBMITTER\" value=\"$submitter\">";
	print "<input type=\"hidden\" name=\"USER\" value=\"$submitter\">";
	print "<input type=\"hidden\" name=\"SI_MODE\" value=\"$si_mode\">";
	print "<input type=\"hidden\" name=\"email_address\" value=\"$email_address\">";
	print "<input type=\"hidden\" name=\"awc_cnt\" value=\"$awc_cnt\">";
	print "<input type=\"hidden\" name=\"awc_ind\" value=\"$awc_ind\">";

#----------------------------
#------ time constraint cases
#----------------------------

	print "<input type=\"hidden\" name=\"TIME_ORDR\" value=\"$time_ordr\">";

	for($j = 1; $j <= $time_ordr; $j++){
		foreach $ent ('START_DATE', 'START_MONTH', 'START_YEAR', 'START_TIME',
			       'END_DATE',  'END_MONTH',   'END_YEAR',   'END_TIME',
			       'WINDOW_CONSTRAINT'){
			$name  = "$ent"."$j";
			$lname = lc ($ent);
			$val   = ${$lname}[$j];
			print "<input type=\"hidden\" name=\"$name\" value=\"$val\">";
		}
	}

#-----------------------------
#------ roll constraint cases
#-----------------------------

	print "<input type=\"hidden\" name=\"ROLL_ORDR\" value=\"$roll_ordr\">";

	for($j = 1; $j <= $roll_ordr; $j++){
		foreach $ent('ROLL_CONSTRAINT','ROLL_180','ROLL','ROLL_TOLERANCE'){
			$name  = "$ent"."$j";
			$lname = lc ($ent);
			$val   = ${$lname}[$j];
			print "<input type=\"hidden\" name=\"$name\" value=\"$val\">";
		}
	}

#-------------------------
#------- acis window cases
#-------------------------

	print "<input type=\"hidden\" name=\"ACISWIN_NO\" value=\"$aciswin_no\">";

	for($j = 0; $j < $aciswin_no; $j++){
		foreach $ent ('ORDR', 'CHIP',
#				'INCLUDE_FLAG',
				'START_ROW','START_COLUMN','HEIGHT','WIDTH',
				'LOWER_THRESHOLD','PHA_RANGE','SAMPLE'){
			$name  = "$ent"."$j";
			$lname = lc ($ent);
			$val   = ${$lname}[$j];
			print "<input type=\"hidden\" name=\"$name\" value=\"$val\">";
		}
	}

#---------------------------------------------------------------------------------------
#--- to avoid write over other user's entry, generate different a sufix for the temp file
#---------------------------------------------------------------------------------------

	$tnum = rand();
	$sf = int(10000 * $tnum);
	if($tval < 10){
		$sf = '000'."$sf";
	}elsif($sf < 100){
		$sf = '00'."$sf";
	}elsif($sf < 1000){
		$sf = '0'."$sf";
	}

	print "<input type=\"hidden\" name=\"tmp_suf\" value=\"$sf\">";


#-------------------------------------------#
#-------------------------------------------#
#-------- ASIS and REMOVE case starts ------#
#-------------------------------------------#
#-------------------------------------------#

   if ($asis eq "ASIS" || $asis eq "REMOVE"){

#------------------------------------------------------
#---- start writing email to the user about the changes
#------------------------------------------------------

    	open (FILE, ">$temp_dir/$obsid.$sf");		# a temp file which email to a user written in.

    	print FILE "OBSID    = $obsid\n";
    	print FILE "SEQNUM   = $seq_nbr\n";
    	print FILE "TARGET   = $targname\n";
    	print FILE "USER NAME = $submitter\n";
    	if($asis eq "ASIS"){
    		print FILE "VERIFIED OK AS IS\n";
    	}elsif($asis eq "REMOVE") {
        	print FILE "VERIFIED  REMOVED\n";
    	}

    	print FILE "\n------------------------------------------------------------------------------------------\n";
    	print FILE "Below is a full listing of obscat parameter values at the time of submission,\nas well as new";
	print FILE " values submitted from the form.  If there is no value in column 3,\nthen this is an unchangable";
	print FILE " parameter on the form.\nNote that new RA and Dec will be slightly off due to rounding errors in";
	print FILE " double conversion.\n\n";
    	print FILE "PARAM NAME                  ORIGINAL VALUE                REQUESTED VALUE             ";
    	print FILE "\n------------------------------------------------------------------------------------------\n";
	
    	close FILE;
 
	format PARAMLINE =
	@<<<<<<<<<<<<<<<<<<<<<<<<<< @<<<<<<<<<<<<<<<<<<<<<<<<<<<< @<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        	$nameagain $old_value $current_entry
.
   
	open (PARAMLINE, ">>$temp_dir/$obsid.$sf");
	foreach $nameagain (@paramarray){

		$lc_name   = lc ($nameagain);
		$old_name  = 'orig_'."$lc_name";
		$old_value = ${$old_name};

    		unless (($lc_name =~/TARGNAME/i) || ($lc_name =~/TITLE/i)
			||  ($lc_name =~/^WINDOW_CONSTRAINT/i) || ($lc_name =~ /^TSTART/i) || ($lc_name =~/^TSTOP/i) 
			||  ($lc_name =~/^ROLL_CONSTRAINT/i) || ($lc_name =~ /^ROLL_180/i)
			||  ($lc_name =~/^CHIP/i) || ($lc_name =~ /^INCLUDE_FLAG/i) || ($lc_name =~ /^START_ROW/i)
			||  ($lc_name =~/^START_COLUMN/i) || ($lc_name =~/^HEIGHT/i) || ($lc_name =~ /^WIDTH/i)
			||  ($lc_name =~/^LOWER_THRESHOLD/i) || ($lc_name =~ /^PHA_RANGE/i) || ($lc_name =~ /^SAMPLE/i)
			||  ($lc_name =~/^SITAG/i) || ($lc_name =~ /^ACISTAG/i) || ($lc_name =~ /^GENERALTAG/i)
			||  ($lc_name =~/ASIS/i) 
#######			|| ($lc_name =~ /MONITOR_FLAG/i)
			){  

#---------------------
#---- time order case
#---------------------

			if($lc_name =~ /TIME_ORDR/){
				$current_entry = $oring_time_ordr;
				write (PARAMLINE);
				for($j = 1; $j <= $orig_time_ordr; $j++){

					$nameagain     = 'WINDOW_CONSTRAINT'."$j";
					$current_entry = $window_constraint[$j];
					$old_value     = $orig_window_constraint[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'TSTART'."$j";
					$current_entry = $tstart[$j];
					$old_value     = $orig_tstart[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'TSTOP'."$j";
					$current_entry = $tstop[$j];
					$old_value     = $orig_tstop[$j];
					check_blank_entry();
					write (PARAMLINE);
				}

#--------------------
#--- roll order case
#--------------------

			}elsif ($lc_name =~ /ROLL_ORDR/){
				$current_entry = $orig_roll_ordr;
				write(PARAMLINE);
				for($j = 1; $j <= $orig_roll_ordr; $j++){

					$nameagain     = 'ROLL_CONSTRAINT'."$j";
					$current_entry = $roll_constraint[$j];
					$old_value     = $orig_roll_constraint[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'ROLL_180'."$j";
					$current_entry = $roll_180[$j];
					$old_value     = $orig_roll_180[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'ROLL'."$j";
					$current_entry = $roll[$j];
					$old_value     = $orig_roll[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'ROLL_TOLERANCE'."$j";
					$current_entry = $roll_tolerance[$j];
					$old_value     = $orig_roll_tolerance[$j];
					check_blank_entry();
					write (PARAMLINE);
				}

#--------------------------
#--- acis window order case
#--------------------------

			}elsif ($lc_name =~ /ACISWIN_ID/i){

				for($j = 0; $j < $aciswin_no; $j++){
					$jj = $j + 1;
					$nameagain     = 'ORDR'."$jj";
					$current_entry = $ordr[$j];
					write(PARAMLINE);

					$nameagain     = 'CHIP'."$jj";
					$current_entry = $chip[$j];
					write(PARAMLINE);

#					$nameagain     = 'INCLUDE_FLAG'."$jj";
#					$current_entry = $include_flag[$j];
#					write(PARAMLINE);

					$nameagain     = 'START_ROW'."$jj";
					$current_entry = $start_row[$j];
					write(PARAMLINE);

					$nameagain     = 'START_COLUMN'."$jj";
					$current_entry = $start_column[$j];
					write(PARAMLINE);

					$nameagain     = 'HEIGHT'."$jj";
					$current_entry = $height[$j];
					write(PARAMLINE);

					$nameagain     = 'WIDTH'."$jj";
					$current_entry = $width[$j];
					write(PARAMLINE);

					$nameagain     = 'LOWER_THRESHOLD'."$jj";
					$current_entry = $lower_threshold[$j];
					write(PARAMLINE);

					$nameagain     = 'PHA_RANGE'."$jj";
					$current_entry = $pha_range[$j];
					write(PARAMLINE);

					$nameagain     = 'SAMPLE'."$jj";
					$current_entry = $sample[$j];
					write(PARAMLINE);
				}
        		}else{
                		$current_entry = ${$old_name};
        			write (PARAMLINE);
        		}
    		}
	}
	close PARAMLINE;

#-----------------------------------------------------------
#-------  start writing a html page for asis and remvoe case
#-----------------------------------------------------------

    	if($asis eq "ASIS"){
	        $wrong_si = 0;
        	if($si_mode =~ /blank/i || $si_mode =~ /NULL/i || $si_mode eq '' || $si_mode =~ /\s+/){
                	$wrong_si = 9999;
                	print "<b><font color='red'>";
                	print "Warning, an obsid, may not be approved without an SI_mode.";
                	print 'Please contact "acisdude" or and HRC contact as appropriate';
                	print "and request they enter an SI-mode befor proceding.";
                	print "</b></font>";
                	print "<br /><br />";
        	}else{
    			print "<b>You have checked that this obsid ($obsid) is ready for flight.";
			print "  Any parameter changes you made will not be submitted with this request.</b><p>";
		}
    	}elsif($asis eq "REMOVE") {
        	print "<b>You have requested this obsid ($obsid) to be removed from the \"ready to go\" list.";
 		print " Any parameter changes you made will not be submitted with this request.</b><p>";
    	}

    	if($asis eq "ASIS"){
        	print "<input type=\"hidden\" name=\"ASIS\" value=\"ASIS\">";
    	}elsif($asis eq "REMOVE") {
        	print "<input type=\"hidden\" name=\"ASIS\" value=\"REMOVE\">";
    	}

        print "<input type=\"hidden\" name=\"access_ok\" value=\"yes\">";
        print "<input type=\"hidden\" name=\"pass\" value=\"$pass\">";
        print "<input type=\"hidden\" name=\"sp_user\" value=\"$sp_user\">";
	print "<input type=\"hidden\" name=\"email_address\" value=\"$email_address\">";

	print '<br />';
	if($error_ind ==  0 || $usint_on =~ /yes/){
		if($wrong_si == 0){
			print "<input type=\"SUBMIT\" name =\"Check\"  value=\"FINALIZE\">";
		}
	}
	print "<input type=\"SUBMIT\" name =\"Check\"  value=\"PREVIOUS PAGE\">";
    	print "</form></body></html>";
    	exit(0);
   }

#--------------------------------------------#
#--------------------------------------------#
#-------- begin clone stuff  here -----------#
#--------------------------------------------#
#--------------------------------------------#

   if ($asis eq "CLONE"){

#--------------------------------
#-------- print email to the user
#--------------------------------

    	open (FILE, ">$temp_dir/$obsid.$sf");

    	print FILE "OBSID    = $obsid\n";
    	print FILE "SEQNUM   = $orig_seq_nbr\n";
    	print FILE "TARGET   = $orig_tragname\n";
    	print FILE "USER NAME = $submitter\n";
    	print FILE "CLONE\n";
#----------
    	print FILE "PAST COMMENTS = \n $orig_comments\n\n";
    	print FILE "NEW COMMENTS  = \n $comments\n\n";
    	print FILE "PAST REMARKS  = \n $orig_remarks\n\n";
    	print FILE "NEW REMARKS   = \n $remarks\n\n";
#----------

    	print FILE "\n------------------------------------------------------------------------------------------\n";
    	print FILE "Below is a full listing of obscat parameter values at the time of submission,\nas well as new";
	print FILE " values submitted from the form.  If there is no value in column 3,\nthen this is an unchangable";
	print FILE " parameter on the form.\nNote that new RA and Dec will be slightly off due to rounding errors in";
	print FILE " double conversion.\n\n";
    	print FILE "PARAM NAME                  ORIGINAL VALUE                REQUESTED VALUE             ";
    	print FILE "\n------------------------------------------------------------------------------------------\n";
	
    	close FILE;
 
	format PARAMLINE =
	@<<<<<<<<<<<<<<<<<<<<<<<<<< @<<<<<<<<<<<<<<<<<<<<<<<<<<<< @<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        	$nameagain $old_value $current_entry
.
   
	open (PARAMLINE, ">>$temp_dir/$obsid.$sf");
	foreach $nameagain (@paramarray){
		$lc_name = lc ($nameagain);
		$old_name = 'orig_'."$lc_name";
		$old_value = ${$old_name};
    		unless (($lc_name =~/TARGNAME/i) || ($lc_name =~/TITLE/i)
			|| ($lc_name =~ /^WINDOW_CONSTRAINT/i) || ($lc_name =~ /^TSTART/i) || ($lc_name =~/^TSTOP/i) 
			|| ($lc_name =~ /^ROLL_CONSTRAINT/i) || ($lc_name =~ /^ROLL_180/i)
			|| ($lc_name =~/^CHIP/i) || ($lc_name =~ /^INCLUDE_FLAG/i) || ($lc_name =~ /^START_ROW/i)
			|| ($lc_name =~/^START_COLUMN/i) || ($lc_name =~/^HEIGHT/i) || ($lc_name =~ /^WIDTH/i)
			|| ($lc_name =~/^LOWER_THRESHOLD/i) || ($lc_name =~ /^PHA_RANGE/i) || ($lc_name =~ /^SAMPLE/i)
			|| ($lc_name =~/^SITAG/i) || ($lc_name =~ /^ACISTAG/i) || ($lc_name =~ /^GENERALTAG/i)
			|| ($lc_name =~/ASIS/i) 
#####			|| ($lc_name =~ /MONITOR_FLAG/i)
			){

#---------------------
#----- time order case
#---------------------
			if($lc_name =~ /TIME_ORDR/){
				$current_entry = ${$lc_name};
				write (PARAMLINE);
				for($j = 1; $j <= $time_ordr; $j++){
					$nameagain     = 'WINDOW_CONSTRAINT'."$j";
					$current_entry = $window_constraint[$j];
					$old_value     = $orig_window_constraint[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'TSTART'."$j";
					$current_entry = $tstart[$j];
					$old_value     = $orig_tstart[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'TSTOP'."$j";
					$current_entry = $tstop[$j];
					$old_value     = $orig_tstop[$j];
					check_blank_entry();
					write (PARAMLINE);
				}

#--------------------
#---- roll order case
#--------------------

			}elsif ($lc_name =~ /ROLL_ORDR/){
				$current_entry = ${$lc_name};
				write(PARAMLINE);
				for($j = 1; $j <= $roll_ordr; $j++){
					$nameagain     = 'ROLL_CONSTRAINT'."$j";
					$current_entry = $roll_constraint[$j];
					$old_value     = $orig_roll_constraint[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'ROLL_180'."$j";
					$current_entry = $roll_180[$j];
					$old_value     = $orig_roll_180[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'ROLL'."$j";
					$current_entry = $roll[$j];
					$old_value     = $orig_roll[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'ROLL_TOLERANCE'."$j";
					$current_entry = $roll_tolerance[$j];
					$old_value     = $orig_roll_tolerance[$j];
					check_blank_entry();
					write (PARAMLINE);
				}

#---------------------
#--- acis window case
#---------------------

			}elsif ($lc_name eq 'ACISWIN_ID'){
				for($j = 0; $j < $aciswin_no; $j++){
					$jj = $j + 1;
					$nameagain     = 'ORDR'."$jj";
					$current_entry = $ordr[$j];
					write(PARAMLINE);

					$nameagain     = 'CHIP'."$jj";
					$current_entry = $chip[$j];
					write(PARAMLINE);

#					$nameagain     = 'INCLUDE_FLAG'."$jj";
#					$current_entry = $include_flag[$j];
#					write(PARAMLINE);

					$nameagain     = 'START_ROW'."$jj";
					$current_entry = $start_row[$j];
					write(PARAMLINE);

					$nameagain     = 'START_COLUMN'."$jj";
					$current_entry = $start_column[$j];
					write(PARAMLINE);

					$nameagain     = 'HEIGHT'."$jj";
					$current_entry = $height[$j];
					write(PARAMLINE);

					$nameagain     = 'WIDTH'."$jj";
					$current_entry = $width[$j];
					write(PARAMLINE);

					$nameagain     = 'LOWER_THRESHOLD'."$jj";
					$current_entry = $lower_threshold[$j];
					write(PARAMLINE);

					$nameagain     = 'PHA_RANGE'."$jj";
					$current_entry = $pha_range[$j];
					write(PARAMLINE);

					$nameagain     = 'SAMPLE'."$jj";
					$current_entry = $sample[$j];
					write(PARAMLINE);
				}
        		}elsif(${$lc_name} ne ''){
                		$current_entry = ${$lc_name};
        			write (PARAMLINE);
        		}else{
                		$current_entry = ${$old_name};
        			write (PARAMLINE);
        		}
    		}
	}
		close PARAMLINE;

#----------------------------------------
#--------- print html page for clone case
#----------------------------------------

    	print "<html>";
    	print "<HEAD><TITLE>Target info for obsid : $obsid</TITLE></HEAD>";
    	print "<body bgcolor=\"#FFFFFF\">";
    	print "Username = $submitter<p>";
    	print "<b>You have submitted a request for splitting obsid $obsid.  No parameter changes will";
	print "  be submitted with this request.</b><p>";

	if($comments eq $orig_comments){
		print '<b><font color=red>You need to explain why you need to split this observation.';
		print 'Plese go back and add the explanation in the comment area</font></b>';
		print '<br />';
	}else{
		print '<table><tr><th>Reasons for cloning:</th><td> ';
		print "$comments",'</td></tr></table>';
	}
	
	print "<input type=\"hidden\" name=\"CLONE\" value=\"CLONE\">";
	print '<br />';

        print "<input type=\"hidden\" name=\"access_ok\" value=\"yes\">";
        print "<input type=\"hidden\" name=\"pass\" value=\"$pass\">";
        print "<input type=\"hidden\" name=\"sp_user\" value=\"$sp_user\">";
	print "<input type=\"hidden\" name=\"email_address\" value=\"$email_address\">";
	print "<input type=\"hidden\" name=\"asis\" value=\"ARCOPS\">";

	if($error_ind ==  0 || $usint_on =~ /yes/){
		print "<input type=\"SUBMIT\" name =\"Check\"  value=\"FINALIZE\">";
	}
	print "<input type=\"SUBMIT\" name =\"Check\"  value=\"PREVIOUS PAGE\">";
	print "</form></body></html>";
	exit(0);
   }

#------------------------------------------#
#------------------------------------------#
#------ begin general changes here --------#
#------------------------------------------#
#------------------------------------------#

#--------------------------------------------
# acisarray triggers acis box in orupdate.cgi
# genarray triggers general box in orupdate.cgi
#--------------------------------------------

#------------------------------------
#----  perform RA and DEC correction
#------------------------------------

	$racnt     = 0;
	if (($ra =~/:/) && ($dec =~/:/)){
		@dec= split (":", $dec);
		if ($dec[0] =~/-/){
			$sign ="-";
			$dec[0] *= -1;
		} else {$sign = "+"}

		$newdec = ($dec[0] + ($dec[1]/60) + ($dec[2]/3600));
		$dec    = sprintf("%1s%3.6f", $sign, $newdec);
		@ra     = split (":", $ra);
		$newra  = (15 * ($ra[0] + ($ra[1]/60) + ($ra[2]/3600)));
		$ra     = sprintf("%3.6f", $newra);
		$racnt++;
	}else{
		$dec = sprintf("%3.6f", $dec);
		$ra  = sprintf("%3.6f", $ra);
	}

#------------------------------------
#----- print the verification webpage
#------------------------------------

	print "<html>";
	print "<HEAD><TITLE>Target info for obsid : $obsid</TITLE></HEAD>";
	print "<body bgcolor=\"#FFFFFF\">\n";

	print "<b>You have submitted the following values for obsid $obsid: </b>";
	print '<br />';

	if($error_ind == 0 || $usint_on =~ /yes/){
		print "<input type=\"SUBMIT\" name =\"Check\"  value=\"FINALIZE\">";
	}
	print "<input type=\"SUBMIT\" name =\"Check\"  value=\"PREVIOUS PAGE\">";
	print "<p>";
	print "Username = $submitter<p>";

#        print "<b>Note:</b><br />";
        print "<p style='padding-bottom:20px'>";
        print "If you see a <span style='color:red'>&lt;Blank&gt;</span> in the \"Original Value\" Column below, ";
        print "it is because you requested to add a value on a \"Blank\" space. ";
        print "The \"Blank\" space in <em>Ocat Data Page</em> could mean \"empty string\", \"NULL\", or even \"0\" value in the database. ";
        print "If you requested to change any non-\"Blank\" value to a \"Blank\" space, <em>arcops</em> will pass it as a \"NULL\" value.";
        print "</p>";
#
#---- counter of number of changed paramters
#

	print "<table border=1 cellspacing=3>";
	print "<th>Parameter</th><th>Original Value</th><th>Requested</th></tr>";
	$cnt_modified = 0;
	
	foreach $name (@paramarray){
		unless (($name =~/ORIG/) || ($name =~/OBSID/) || ($name =~/USER/)
				|| ($name =~ /^REMARKS/) || ($name =~ /^COMMENTS/) || ($name =~ /^MP_REMARKS/)
				|| ($name =~ /^WINDOW_CONSTRAINT/) || ($name =~ /^TSTART/) || ($name =~ /^TSTOP/)
				|| ($name =~ /^ROLL_CONSTRAINT/) || ($name =~/^ROLL_180/) || ($name =~ /^ROLL_TOLERANCE/)
				|| ($name =~/^CHIP/i) || ($name =~ /^INCLUDE_FLAG/i) || ($name =~ /^START_ROW/i)
				|| ($name =~/^START_COLUMN/i) || ($name =~/^HEIGHT/i) || ($name =~ /^WIDTH/i)
				|| ($name =~/^LOWER_THRESHOLD/i) || ($name =~ /^PHA_RANGE/i) || ($name =~ /^SAMPLE/i)
				|| ($name =~/^SITAG/i) || ($name =~ /^ACISTAG/i) || ($name =~ /^GENERALTAG/i)
#####				|| ($name =~/^MONITOR_FLAG/i)
			){

#------------------------------------------
#------ If it is unchanged print that info
#------------------------------------------

			$new_entry = lc ($name);
			$new_value = ${$new_entry};
			$old_entry = 'orig_'."$new_entry";
			$old_value = ${$old_entry};

#-------------------------------------------------
#----- checking whether the value is digit or not
#-------------------------------------------------

			$chk_digit = 0;
			@dtemp = split(//,$new_value);
			OUTER:
			foreach $comp (@dtemp){
				if($comp =~/\d/ || $comp eq '.' || $comp eq '+' || $comp eq '-'){
					$chk_digit = 1;
				}else{
					$chk_digit = 0;
					last OUTER;
				}
			}
			$match_ok = 0;
			if($new_value eq $old_value){
				$match_ok = 1;
			}elsif($chk_digit > 0 && $new_value == $old_value){
				$match_ok = 1;
			}else{
				$cnt_modified++;
			}
			if($match_ok == 1){

#----------------------------------
#----- checking window order case
#----------------------------------

				if($name =~ /ACISWIN_ID/i){
#					print "rank\/ORDR unchanged, set to $new_value<br />";

					for($j = 0; $j < $aciswin_no; $j++){
						$jj = $j + 1;
						print '<spacer type=horizontal size=5>';
#						print "ORDER $j:<br />";
						$ehead = "ENTRY $jj: ";

						foreach $tent ('ORDR','CHIP',
#								'INCLUDE_FLAG',
								'START_ROW','START_COLUMN',
								'HEIGHT','WIDTH','LOWER_THRESHOLD','PHA_RANGE',
								'SAMPLE'){
							$new_entry = lc ($tent);
							$new_value = ${$new_entry}[$j];
							$old_entry = 'orig_'."$new_entry";
							$old_value = ${$old_entry}[$j];
							$chk_digit = 0;
							@dtemp     = split(//,$new_value);

							OUTER:
							foreach $comp (@dtemp){
								if($comp =~/\d/ || $comp eq '.' || $comp eq '+' || $comp eq '-'){
									$chk_digit = 1;
								}else{
									$chk_digit = 0;
									last OUTER;
								}
							}
							$match_ok = 0;

							if($new_value eq $old_value){
								$match_ok = 1;
							}elsif($chk_digit > 0 && $new_value == $old_value){
								$match_ok = 1;
							}

							if($match_ok == 1){
								$tname = "$ehead $tent";
								print_table_row($tname, 'same', $new_value);
							}else{
								$tname = "$ehead $tent";
								if($old_value =~ /\s+/ || $old_value eq ''){
									print_table_row($tname, $blank, $new_value);
								}else{
									print_table_row($tname, $old_value, $new_value);
								}
								$k++; 		#telling asicwin has modified param!
							}
						}
					}

#-------------------------------
#----- checking time order case
#-------------------------------

				}elsif($name =~ /TIME_ORDR/){
					print_table_row($name, 'same', $new_value);

					for($j = 1; $j <= $time_ordr; $j++){
						#print '<spacer type=horizontal size=5>';
						$ehead =  "ORDER $j: ";

						foreach $tent ('WINDOW_CONSTRAINT', 'TSTART', 'TSTOP'){
							$new_entry = lc ($tent);
							$new_value = ${$new_entry}[$j];
							$old_entry = 'orig_'."$new_entry";
							$old_value = ${$old_entry}[$j];
							$chk_digit = 0;
							@dtemp     = split(//,$new_value);

							OUTER:
							foreach $comp (@dtemp){
								if($comp =~/\d/ || $comp eq '.' || $comp eq '+' || $comp eq '-'){
									$chk_digit = 1;
								}else{
									$chk_digit = 0;
									last OUTER;
								}
							}
							$match_ok = 0;

							if($new_value eq $old_value){
								$match_ok = 1;
							}elsif($chk_digit > 0 && $new_value == $old_value){
								$match_ok = 1;
							}

							if($match_ok == 1){
								$tname = "$ehaad $tent";
								print_table_row($tname, 'same', $new_value);
							}else{
								$tname = "$ehaad $tent";
								if($old_value =~ /\s+/ || $old_value eq ''){
									print_table_row($tname, $blank, $new_value);
								}else{
									print_table_row($tname, $old_value, $new_value);
								}
								$m++;		#telling general change is ON
							}
						}
					}

#------------------------------
#----- checking roll order case
#------------------------------

				}elsif($name =~ /ROLL_ORDR/){
					print_table_row($name, 'same', $new_value);
					for($j = 1; $j <= $roll_ordr; $j++){
						#print '<spacer type=horizontal size=5>';
						$ehead = "ORDER $j: ";

						foreach $tent ('ROLL_CONSTRAINT', 'ROLL_180','ROLL', 'ROLL_TOLERANCE'){
							$new_entry = lc ($tent);
							$new_value = ${$new_entry}[$j];
							$old_entry = 'orig_'."$new_entry";
							$old_value = ${$old_entry}[$j];
							$chk_digit = 0;
							@dtemp     = split(//,$new_value);

							OUTER:
							foreach $comp (@dtemp){
								if($comp =~/\d/ || $comp eq '.' || $comp eq '+' || $comp eq '-'){
									$chk_digit = 1;
								}else{
									$chk_digit = 0;
									last OUTER;
								}
							}
							$match_ok = 0;

							if($new_value eq $old_value){
								$match_ok = 1;
							}elsif($chk_digit > 0 && $new_value == $old_value){
								$match_ok = 1;
							}

							if($match_ok == 1){
								$tname = "$ehead $tent";
								print_table_row($tname, 'same', $new_value);
							}else{
								$tname = "$ehead $tent";
								if($old_value =~ /\s+/ || $old_value eq ''){
									print_table_row($tname, $blank, $new_value);
								}else{
									print_table_row($tname, $old_value, $new_value);
								}
								$m++;		# telling general change is ON
							}
						}
					}

#----------------------
#----- all other cases
#----------------------

				}else{
					print_table_row($name, 'same', $new_value);
				}

#------------------------------------------------
#-------  If it is changed, print from old to new
#------------------------------------------------

			}else{

#-----------------------
#----- window order case
#-----------------------
				if($name eq 'ORDR'){
					if($old_value =~ /\s+/ || $old_value eq ''){
						$rent = 'rank ORDR';
						print_table_row($rent, $blank, $new_value);
					}else{
						$rent = 'rank ORDR';
						print_table_row($rent, $old_value, $new_value);
					}

					for($j = 0; $j < $aciswin_no; $j++){
						$jj = $j + 1;
						print '<spacer type=horizontal size=5>';
						print "$jj:<br />";

						foreach $tent ('ORDR','CHIP',
#								'INCLUDE_FLAG',
								'START_ROW','START_COLUMN',
								'HEIGHT','WIDTH','LOWER_THRESHOLD','PHA_RANGE',
								'SAMPLE'){
							$new_entry = lc ($tent);
							$new_value = ${$new_entry}[$j];
							$old_entry = 'orig_'."$new_entry";
							$old_value = ${$old_entry}[$j];
							$chk_digit = 0;
							@dtemp     = split(//,$new_value);
							OUTER:
							foreach $comp (@dtemp){
								if($comp =~/\d/ || $comp eq '.' || $comp eq '+' || $comp eq '-'){
									$chk_digit = 1;
								}else{
									$chk_digit = 0;
									last OUTER;
								}
							}
							$match_ok = 0;

							if($new_value eq $old_value){
								$match_ok = 1;
							}elsif($chk_digit > 0 && $new_value == $old_value){
								$match_ok = 1;
							}

							if($match_ok == 1){
								print_table_row($tent, 'same', $new_value);
							}else{
								print '<spacer type=horizontal size=15>';
								if($old_value =~ /\s+/ || $old_value eq ''){
									print_table_row($tent, $old_value, $new_value);
								}else{
									print_table_row($tent, $old_value, $new_value);
								}
								$k++;		#telling aciswin param changes
							}
						}
					}

#---------------------
#----- time order case
#---------------------

				}elsif($name =~ /TIME_ORDR/){
					if($old_value =~ /\s+/ || $old_value eq ''){
						print_table_row($name, $blank, $new_value);
					}else{
						print_table_row($name, $old_value, $new_value);
					}

					for($j = 1; $j <= $time_ordr; $j++){
					#print '<spacer type=horizontal size=5>';
					$ehead =  "ORDER $j: ";

						foreach $tent ('WINDOW_CONSTRAINT', 'TSTART', 'TSTOP'){
							$new_entry = lc ($tent);
							$new_value = ${$new_entry}[$j];
							$old_entry = 'orig_'."$new_entry";
							$old_value = ${$old_entry}[$j];
							$chk_digit = 0;
							@dtemp     = split(//,$new_value);

							OUTER:
							foreach $comp (@dtemp){
								if($comp =~/\d/ || $comp eq '.' || $comp eq '+' || $comp eq '-'){
									$chk_digit = 1;
								}else{
									$chk_digit = 0;
									last OUTER;
								}
							}
							$match_ok = 0;

							if($new_value eq $old_value){
								$match_ok = 1;
							}elsif($chk_digit > 0 && $new_value == $old_value){
								$match_ok = 1;
							}

							if($match_ok == 1){
								$tname = "$ehead $tent";
								print_table_row($tname, 'same', $new_value);
							}else{
								$tname = "$ehead $tent";
								if($old_value =~ /\s+/ || $old_value eq ''){
									print_table_row($tname, $blank, $new_value);
								}else{
									print_table_row($tname, $old_value, $new_value);
								}
								$m++; 			# telling general change is ON
							}
						}
					}
#---------------------
#----- roll order case
#---------------------
				}elsif($name =~ /ROLL_ORDR/){
					if($old_value =~ /\s+/ || $old_value eq ''){
						print_table_row($name, $blank, $new_value);
					}else{
						print_table_row($name, $old_value, $new_value);
					}

					for($j = 1; $j <= $roll_ordr; $j++){
					#print '<spacer type=horizontal size=5>';
					$ehead = "ORDER $j: ";

						foreach $tent ('ROLL_CONSTRAINT', 'ROLL_180', 'ROLL','ROLL_TOLERANCE'){
							$new_entry = lc ($tent);
							$new_value = ${$new_entry}[$j];
							$old_entry = 'orig_'."$new_entry";
							$old_value = ${$old_entry}[$j];

							if($new_value eq $old_value){
								$tname = "$ehead $tent";
								print_table_row($tname, 'same', $new_value);
							}else{
								$tname = "$ehead $tent";
								if($old_value =~ /\s+/ || $old_value eq ''){
									print_table_row($tname, $blank, $new_value);
								}else{
									print_table_row($tname, $old_value, $new_value);
								}
								$m++;			# telling general change is ON
							}
						}
					}
#----------------------
#----- all other cases
#----------------------
				}else{
					if((($old_value =~ /OPT/) && ($new_value =~ /Y/))
						|| (($old_value =~ /Y/) && ($new_value =~ /OPT/))){
						if($old_value =~ /\s+/ || $old_value eq ''){
							print_table_row($name, $blank, $new_value, 'lime');
						}else{
							print_table_row($name, $old_value, $new_value, 'lime');
						}
					}else{
						if($old_value =~ /\s+/ || $old_value eq ''){
							print_table_row($name, $blank, $new_value);
						}else{
							print_table_row($name, $old_value, $new_value);
						}
					}
				}

				foreach $param (@acisarray){
					if ($name eq $param){
						$k++;
					}
				}
				foreach $param (@aciswinarray){
					if ($name eq $param){
						$l++;
					}
				}
				foreach $param2 (@genarray){
					if ($name eq $param2){
						$m++;
					}
				}
			}
		}
	}

	print "</table><br />";

#--------------------------------
#----- check remarks and comment
#--------------------------------

	$tremarks      = $remarks;
	$tremarks      =~ s/\n+//g;
	$tremarks      =~ s/\t+//g;
	$tremarks      =~ s/\s+//g;
	$torig_remarks = $orig_remarks;
	$torig_remarks =~ s/\n+//g;
	$torig_remarks =~ s/\t+//g;
	$torig_remarks =~ s/\s+//g;
	
	print "<h3>REAMARKS and COMMENTS Changes</h3>";

	if($tremarks ne $torig_remarks){

		if($torig_remarks ne '' && $tremarks eq ''){
			$remarks = "ALL TEXT FROM THE REMRKS HAS BEEN DELETED";

                        print "<span style='color:#FF0000'>REMARKSM</span> changed from<br /><br />";
                        print "<span style='color:#FF0000'> $orig_remarks</span><br /> to<br />";
                        print "<span style='color:#FF0000'> <b>$remarks</b></span><br /><br />";
		}elsif($torig_remarks eq ''){
                        print "<span style='color:#FF0000'>REMARKS</span> changed from<br /><br />";
                        print "<span style='color:#FF0000'> $blank</span><br /> to<br />";
                        print "<span style='color:#FF0000'> $remarks</span><br /><br />";
		}else{
                        print "<span style='color:#FF0000'>REMARKSM</span> changed from<br /><br />";
                        print "<span style='color:#FF0000'> $orig_remarks</span><br /> to<br />";
                        print "<span style='color:#FF0000'> $remarks</span><br /><br />";
		}
		$m++;			# remark is a part of general change
		$cnt_modified++;
	} else {
                if($tremarks eq ''){
                        print "REMARKS unchanged and there is no remark.<br /><br />";
                }else{
                        print "REMARKS unchanged, set to <br /><br />$remarks<br /><br />";
                }
	}

#	$tmp_remarks       = $mp_remarks;
#	$tmp_remarks       =~ s/\s+//g;
#	$torig_mp_remarks  = $orig_mp_remarks;
#	$torig_mp_remarks  =~ s/\s+//g;
#	
#	if($tmp_remarks ne $torig_mp_remarks){
#		print "<FONT color=\"\#FF0000\">MP_REMARKS changed from<br /> $orig_mp_remarks<br /> to<br /> $mp_remarks</FONT><br /><br />";
#	} else {
#		print "MP_REMARKS unchanged, set to $mp_remarks<br />";
#	}

	$tcomments      = $comments;
	$tcomments      =~ s/\n+//g;
	$tcomments      =~ s/\t+//g;
	$tcomments      =~ s/\s+//g;
	$torig_comments = $orig_comments;
	$torig_comments =~ s/\n+//g;
	$torig_comments =~ s/\t+//g;
	$torig_comments =~ s/\s+//g;

	if ($tcomments ne $torig_comments){
		$cnt_modified++;
		if($torig_comments ne '' && $tcomments eq ''){
			$comments = "ALL TEXT FROM THE COMMENTS HAS BEEN DELETED";

                        print "<span style='color:#FF0000'>COMMENTS</span> changed from<br /><br /> ";
                        print "<span style='color:#FF0000'>$orig_comments</span>";
			print"<br />to<br />";
			print "<span style='color:#FF0000'><b>$comments</b><br /></span>";
		}elsif($torig_comments eq ''){
                        print "<span style='color:#FF0000'>COMMENTS</span> changed from<br /><br />";
                        print "<span style='color:#FF0000'> $blank</span>";
			print"<br />to<br />";
			print "<span style='color:#FF0000'>$comments<br /></span>";
		}else{
                        print "<span style='color:#FF0000'>COMMENTS</span> changed from<br /><br /> ";
                        print "<span style='color:#FF0000'>$orig_comments</span>";
			print"<br />to<br />";
			print "<span style='color:#FF0000'>$comments<br /></span>";
		}
	} else {
                if($tcomments eq ''){
                        print "COMMENTS unchanged and there is no comment.<br />";
                }else{
                        print "COMMENTS unchanged, set to<br /><br /> $comments<br />";
                }
	}

	print "<br />";
	if($wrong_si == 0){
		print "<br /><hr />";
		print "<p style='padding-top:15px;padding-bottom:5px'>";
		print "<strong>If these values are correct, click the FINALIZE button.<br />";
		print "Otherwise, use the previous page button to edit.</strong><br />";
		print "</p>";
	}
	$j = 0;

#----------------------------------------
#----- turn on and off several indicators
#----------------------------------------

	if ($orig_si_mode eq $si_mode){
		$sitag = "OFF";
	} else {
		$sitag = "ON";
	}

	$sitag = 'OFF';
	if($instrument =~ /ACIS/i){
		if($orig_targname ne $targname){
			if(($orig_ra ne $ra) || ($orig_dec ne $dec)){
				$si_mode = 'NULL';
			}
		}
	}

	if($orig_est_cnt_rate    ne $est_cnt_rate)   {$si_mode = 'NULL'}
	if($orig_forder_cnt_rate ne $forder_cnt_rate){$si_mode = 'NULL'}
	if($orig_raster_scan     ne $raster_scan)    {$si_mode = 'NULL'}
	if($orig_grating	 ne $grating)        {$si_mode = 'NULL'}
	if($orig_instrument      ne $instrument)     {$si_mode = 'NULL'}
	if($orig_dither_flag     ne $dither_flag)    {$si_mode = 'NULL'}

	if($orig_si_mode ne $si_mode){ $sitag = 'ON'}
	if($instrument =~ /HRC/i){
		if($orig_hrc_config ne $hrc_config){$sitag = 'ON'}
		if($orig_hrc_zero_block ne $hrc_zero_block){$sitag = 'ON'}
	}


	if ($k > 0){
		$acistag    = "ON";
#    		$si_mode    = "NULL";
	}
#	if ($l > 0){
#		$aciswintag = "ON";
#	}
	if ($m > 0){
		$generaltag = "ON";
	}

	print "<input type=\"hidden\" name=\"ACISTAG\" value=\"$acistag\">";
#	print "<input type=\"hidden\" name=\"ACISWINTAG\" value=\"$aciswintag\">";
	print "<input type=\"hidden\" name=\"SITAG\" value=\"$sitag\">";
	print "<input type=\"hidden\" name=\"GENERALTAG\" value=\"$generaltag\">";

	print "<input type=\"hidden\" name=\"access_ok\" value=\"yes\">";
	print "<input type=\"hidden\" name=\"pass\" value=\"$pass\">";
	print "<input type=\"hidden\" name=\"sp_user\" value=\"$sp_user\">";
	print "<input type=\"hidden\" name=\"email_address\" value=\"$email_address\">";
	print "<input type=\"hidden\" name=\"cnt_modified\" value=\"$cnt_modified\">";

	if($error_ind == 0 || $usint_on =~ /yes/){
		if($wrong_si == 0){
			print "<input type=\"SUBMIT\" name =\"Check\"  value=\"FINALIZE\">";
		}
	}
	print "<input type=\"SUBMIT\" name =\"Check\"  value=\"PREVIOUS PAGE\">";
	print "<div style='padding-bottom:30px'></div>";
	print "</form></body></html>";

#---------------------------------
#--------------- print email form
#---------------------------------

	open (FILE, ">$temp_dir/$obsid.$sf");
	print FILE "OBSID    = $obsid\n";
	print FILE "SEQNUM   = $orig_seq_nbr\n";
	print FILE "TARGET   = $orig_targname\n";
	print FILE "USER NAME = $submitter\n";

	if($asis =~ /\w/){
        	print FILE "VERIFIED AS $asis\n";
		if($asis =~ /ARCOPS/i){
			print FILE "Obsid: $obsid will be approved once ARCOPS signs off this submittion.\n";
		}
	}
	print FILE "PAST COMMENTS =\n $orig_comments\n\n";

	if($tcomments ne $torig_comments){
		print FILE "NEW COMMENTS  =\n $comments\n\n";
	}
	
	print FILE "PAST REMARKS =\n $orig_remarks\n\n";

	if($tremarks ne $torig_remarks){
		print FILE "NEW REMARKS =\n $remarks\n\n";
	}

#	print FILE "PAST MP_REMARKS =\n $orig_mp_remarks\n\n";
#	if($tmp_remarks ne $torig_mp_remarks){
#		print FILE "NEW MP_REMARKS =\n $mp_remarks\n\n";
#	}

#--------------

	@saved_line = ();	

	print FILE "GENERAL CHANGES:\n";

	OUTER:
	foreach $name (@paramarray){
		foreach $comp (@prefarray){
			if($name eq $comp){
				next OUTER;
			}
		}

#-------------------
#---- general cases
#-------------------

		unless (($name =~/ORIG/) || ($name =~/OBSID/) || ($name =~/USER/) || ($name =~/COMMENTS/) || ($name =~/ACISTAG/) 
			|| ($name =~/GENERALTAG/) || ($name =~/SITAG/) || ($name eq "RA") || ($name eq "DEC")
			|| ($name eq 'ASIS') || ($name eq 'REMARKS')){

			$a         = 0;
			$aw        = 0;
			$g         = 0;
			$new_entry = lc($name);
			$new_value = ${$new_entry};
			$old_entry = 'orig_'."$new_entry";
			$old_value = ${$old_entry};
			$test1     = $new_value;
			$test2     = $old_value;
			$test1     =~ s/\n+//g;
			$test1     =~ s/\t+//g;
			$test1     =~ s/\s+//g;
			$test2     =~ s/\n+//g;
			$test2     =~ s/\t+//g;
			$test2     =~ s/\s+//g;

#-------------------------------------
#---if it is acis param, put it aside
#-------------------------------------

			unless ($test1 eq $test2){
				foreach $param3 (@acisarray){
					if ($name eq $param3){
						if($test2 eq ''){
							$aline = "$name changed from $blank2 to $new_value\n";
						}else{
							$aline = "$name changed from $old_value to $new_value\n";
						}
						push(@alines,$aline);
						$a++;
					}
				}
				if ($a == 0){
					if($test2 eq ''){
						print FILE "$name changed from $blank2 to $new_value\n";
					}else{
						print FILE "$name changed from $old_value to $new_value\n";
					}
					$j++;
				}
			}
		}

#---------------------
#------ time order case
#---------------------

		if($name =~ /TIME_ORDR/){
			for($j = 1; $j <= $time_ordr; $j++){
				foreach $tent ('WINDOW_CONSTRAINT', 'TSTART', 'TSTOP'){
					$new_entry = lc ($tent);
					$new_value = ${$new_entry}[$j];
					$old_entry = 'orig_'."$new_entry";
					$old_value = ${$old_entry}[$j];

					if($new_value ne $old_value){
						print FILE  "time_ordr= $j: ";
						if($old_value =~ /\s+/ || $old_value eq ''){
							print FILE  "$tent changed from $blank2 to $new_value\n";
						}else{
							print FILE  "$tent changed from $old_value to $new_value\n";
						}
					}
				}
			}
		}

#---------------------
#----- roll order cae
#---------------------

		if($name =~ /ROLL_ORDR/){
			for($j = 1; $j <= $roll_ordr; $j++){
				foreach $tent ('ROLL_CONSTRAINT', 'ROLL_180','ROLL', 'ROLL_TOLERANCE'){
					$new_entry = lc ($tent);
					$new_value = ${$new_entry}[$j];
					$old_entry = 'orig_'."$new_entry";
					$old_value = ${$old_entry}[$j];

					if($new_value ne $old_value){
						print FILE "roll_ordr= $j: ";
						if($old_value =~ /\s+/ || $old_value eq ''){
							print FILE "$tent changed from $blank2 to $new_value\n";
						}else{
							print FILE "$tent changed from $old_value to $new_value\n";
						}
					}
				}
			}
		}
							
#---------------------
#----RA and DEC cases
#---------------------

		if ($name eq "RA"){
			$ra = sprintf("%3.6f",$ra);
			unless ($ra == $orig_ra){
				$ra      = $dra;
				$orig_ra = "$orig_dra";
				if($orig_ra =~ /\s+/ || $orig_ra eq ''){
					print FILE "$name changed from $blank2 to $ra\n";
				}else{
					print FILE "$name changed from $orig_ra to $ra\n";
				}
			}   
		}
		if ($name eq "DEC"){
			$dec = sprintf("%3.6f",$dec);
			unless ($dec == $orig_dec){
				$dec = "$dec";
				$orig_dec = "$orig_ddec";
				if($orig_dec =~ /\s+/ || $orig_dec eq ''){
					print FILE "$name changed from $blank2 to $dec\n";
				}else{
					print FILE "$name changed from $orig_dec to $dec\n";
				}
			}   
		}
	}

#---------------------
#---- Acis param case
#---------------------

	print FILE "\n\nACIS CHANGES:\n";
	foreach $aline2 (@alines){
		print FILE "$aline2";
	}

#---------------------
#----Acis window cases
#---------------------

	print FILE "\n\nACIS WINDOW CHANGES:\n";
	for($j = 0; $j < $aciswin_no; $j++){
		$jj = $j + 1;
		foreach $tent ('ORDR','CHIP',
#				'INCLUDE_FLAG',
				'START_ROW','START_COLUMN',
				'HEIGHT','WIDTH','LOWER_THRESHOLD','PHA_RANGE',
				'SAMPLE'){
			$new_entry = lc ($tent);
			$new_value = ${$new_entry}[$j];
			$old_entry = 'orig_'."$new_entry";
			$old_value = ${$old_entry}[$j];
			if($new_value ne $old_value){
				print FILE "acis window entry $jj: ";
				if($old_value =~ /\s+/ || $old_value eq ''){
					print FILE "$tent changed from $blank2 to $new_value\n";
				}else{
					print FILE "$tent changed from $old_value to $new_value\n";
				}
			}
		}
	}

    	print FILE "\n------------------------------------------------------------------------------------------\n";
    	print FILE "Below is a full listing of obscat parameter values at the time of submission,\nas well as new";
	print FILE " values submitted from the form.  If there is no value in column 3,\nthen this is an unchangable";
	print FILE " parameter on the form.\nNote that new RA and Dec will be slightly off due to rounding errors in";
	print FILE " double conversion.\n\n";
    	print FILE "PARAM NAME                  ORIGINAL VALUE                REQUESTED VALUE             ";
    	print FILE "\n------------------------------------------------------------------------------------------\n";
	
	close FILE;

#---------------------------------------------------------
#---- we want the log to always be in decimal degrees, so:
#---------------------------------------------------------

	format PARAMLINE =
	@<<<<<<<<<<<<<<<<<<<<<<<<<< @<<<<<<<<<<<<<<<<<<<<<<<<<<<< @<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        	$nameagain $old_value $current_entry
.
   
	open (PARAMLINE, ">>$temp_dir/$obsid.$sf");
	foreach $nameagain (@paramarray){
		$lc_name   = lc ($nameagain);
		$old_name  = 'orig_'."$lc_name";
		$old_value = ${$old_name};

    		unless (($lc_name =~/TARGNAME/i) || ($lc_name =~/TITLE/i)
			|| ($lc_name =~ /^WINDOW_CONSTRAINT/i) || ($lc_name =~ /^TSTART/i) || ($lc_name =~/^TSTOP/i) 
			|| ($lc_name =~ /^ROLL_CONSTRAINT/i) || ($lc_name =~ /^ROLL_180/i)
			|| ($lc_name =~/^CHIP/i) || ($lc_name =~ /^INCLUDE_FLAG/i) || ($lc_name =~ /^START_ROW/i)
			|| ($lc_name =~/^START_COLUMN/i) || ($lc_name =~/^HEIGHT/i) || ($lc_name =~ /^WIDTH/i)
			|| ($lc_name =~/^LOWER_THRESHOLD/i) || ($lc_name =~ /^PHA_RANGE/i) || ($lc_name =~ /^SAMPLE/i)
			|| ($lc_name =~/^SITAG/i) || ($lc_name =~ /^ACISTAG/i) || ($lc_name =~ /^GENERALTAG/i)
######			|| ($lc_name =~/^MONITOR_FLAG/i)
			){

#----------------------
#----- time order case
#----------------------
			if($lc_name =~ /TIME_ORDR/i){
				$current_entry = ${$lc_name};
				write (PARAMLINE);
				for($j = 1; $j <= $time_ordr; $j++){
					$nameagain     = 'WINDOW_CONSTRAINT'."$j";
					$current_entry = $window_constraint[$j];
					$old_value     = $orig_window_constraint[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'TSTART'."$j";
					$current_entry = $tstart[$j];
					$old_value     = $orig_tstart[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'TSTOP'."$j";
					$current_entry = $tstop[$j];
					$old_value     = $orig_tstop[$j];
					check_blank_entry();
					write (PARAMLINE);
				}

#-----------------------
#------- roll order case
#-----------------------

			}elsif ($lc_name =~ /ROLL_ORDR/i){
				$current_entry = ${$lc_name};
				write(PARAMLINE);
				for($j = 1; $j <= $roll_ordr; $j++){
					$nameagain     = 'ROLL_CONSTRAINT'."$j";
					$current_entry = $roll_constraint[$j];
					$old_value     = $orig_roll_constraint[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'ROLL_180'."$j";
					$current_entry = $roll_180[$j];
					$old_value     = $orig_roll_180[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'ROLL'."$j";
					$current_entry = $roll[$j];
					$old_value     = $orig_roll[$j];
					check_blank_entry();
					write (PARAMLINE);

					$nameagain     = 'ROLL_TOLERANCE'."$j";
					$current_entry = $roll_tolerance[$j];
					$old_value     = $orig_roll_tolerance[$j];
					check_blank_entry();
					write (PARAMLINE);
				}

#----------------------
#---- window order case
#----------------------

			}elsif ($lc_name =~/^ACISWIN_ID/i){
				for($j = 0; $j < $aciswin_no; $j++){
					$jj = $j + 1;
					$nameagain     = 'ORDR'."$jj";
					$current_entry = $ordr[$j];
					$old_value     = $orig_ordr[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'CHIP'."$jj";
					$current_entry = $chip[$j];
					$old_value     = $orig_chip[$j];
					check_blank_entry();
					write(PARAMLINE);

#					$nameagain     = 'INCLUDE_FLAG'."$jj";
#					$current_entry = $include_flag[$j];
#					$old_value     = $orig_include_flag[$j];
#					write(PARAMLINE);

					$nameagain     = 'START_ROW'."$jj";
					$current_entry = $start_row[$j];
					$old_value     = $orig_start_row[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'START_COLUMN'."$jj";
					$current_entry = $start_column[$j];
					$old_value     = $orig_start_column[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'HEIGHT'."$jj";
					$current_entry = $height[$j];
					$old_value     = $orig_height[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'WIDTH'."$jj";
					$current_entry = $width[$j];
					$old_value     = $orig_width[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'LOWER_THRESHOLD'."$jj";
					$current_entry = $lower_threshold[$j];
					$old_value     = $orig_lower_threshold[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'PHA_RANGE'."$jj";
					$current_entry = $pha_range[$j];
					$old_value     = $orig_pha_range[$j];
					check_blank_entry();
					write(PARAMLINE);

					$nameagain     = 'SAMPLE'."$jj";
					$current_entry = $sample[$j];
					$old_value     = $orig_sample[$j];
					check_blank_entry();
					write(PARAMLINE);
				}
        		}elsif($lc_name =~ /\w/){
                		$current_entry = ${$lc_name};
				check_blank_entry();
        			write (PARAMLINE);
        		}else{
                		$current_entry = ${$old_name};
				check_blank_entry();
        			write (PARAMLINE);
        		}

#----------------------------------------
#----  devisions between different groups
#----------------------------------------

			if($nameagain eq 'EXTENDED_SRC' || $nameagain eq 'PHASE_END_MARGIN' ||
	   			$nameagain eq 'Z_PHASE' || $nameagain eq 'TIMING_MODE' || 
	   			$nameagain eq 'SPWINDOW'){
				print PARAMLINE "\n----------------------------\n";
			}
    		}
	}
	close PARAMLINE;

#-------------------------------------------------------------------------
#-----  create the "arnold line".  Will not be used later if not required
#------------------------------------------------------------------------

#------------------------------------------------------------------------
#-----  get user, pad to be 8 characters
#-------------------------------------------------------------------------

	$nuser = $submitter;
	@chars = split ("", $nuser);
	$cnt   = $#chars;
	$pad   = 7 - $cnt;
	$y=0;
	if ($cnt < 7){
    		while ($y <= $pad){
			$submitter = "$submitter ";
			$y++;
    		}
	}
	$date =`date '+%Y-%m-%d'`;
	chop $date;
	$chips="$ccdi0_on$ccdi1_on$ccdi2_on$ccdi3_on$ccds0_on$ccds1_on$ccds2_on$ccds3_on$ccds4_on$ccds5_on";
	$subarrayframetime = $subarray_frame_time;
	$secondaryexpcount = $secondary_exp_count;
	$primaryexptime    = $primary_exp_time;
	$secondaryexptime  = $secondary_exp_time;
	$subarraystartrow  = $subarray_start_row;
	$subarrayrowcount  = $subarray_row_count;
	@arnoldarray=($subarrayframetime,$secondaryexpcount,$primaryexptime,$secondaryexptime,$subarraystartrow,$subarrayrowcount);
	$z=0;
	foreach $thing (@arnoldarray){
    		$thing = ($thing +0) unless ($thing =~/NULL/);
    		$thing = $arnoldarray[$z];
    		$z++;
	}
	@spwarray=(SPWINDOW, START_ROW, START_COLUMN, WIDTH, HEIGHT, LOWER_THRESHOLD, PHA_RANGE, SAMPLE);
	foreach $spwparam (@spwarray){
		$new_entry = lc($spwparam);
		$old_entry = 'orig_'."$new_entry";
		$new_value = ${$new_entry};
		$old_value = ${$old_entry};
    		unless ($new_value eq $old_value){
			$spw = 1;
	    	}
	}

	open (ARNOLDFILE, ">$temp_dir/arnold.$sf");
	print ARNOLDFILE "$obsid\t$submitter$date\t$chips\t$exp_mode-$bep_pack\t$arnoldarray[0]\t$arnoldarray[1]\t$arnoldarray[2]\t$arnoldarray[3]\t$arnoldarray[4]\t$arnoldarray[5]\n";
	print ARNOLDFILE "\t\t\t\t\t\tSpatial window, see update page\n" if ($spw);
	close (ARNOLDFILE);
	
####	exit(0);
}


#########################################################################
##########################################################################
##########################################################################

sub print_table_row{
	($t_name, $o_value, $n_value, $color) = @_;

	if ($color eq ''){
		$color= '#FF0000'
	}
	if($o_value eq 'same'){
			print "<tr><th>$t_name</th><td style='text-align:center'>$n_value</td><td style='text-align:center;font-size:70%'>No Change</td></tr>";
	}elsif($o_value eq $blank){
#		print "<tr style='color:$color'><th>$t_name</th><td>&#160;</td><td style='text-align:center'>$n_value</td></tr>";
		print "<tr style='color:$color'><th>$t_name</th><td style='text-align:center'>$blank</td><td style='text-align:center'>$n_value</td></tr>";
	}else{
		print "<tr style='color:$color'><th>$t_name</th><td style='text-align:center'>$o_value</td><td style='color:#FF0000;text-align:center'>$n_value</td></tr>";
	}
}

#########################################################################
##########################################################################
##########################################################################

sub check_blank_entry{
        $ctest1 = $current_entry;
        $ctest1 =~ s/\n+//g;
        $ctest1 =~ s/\t+//g;
        $ctest1 =~ s/\s+//g;
        $ctest2 = $old_entry;
        $ctest2 =~ s/\n+//g;
        $ctest2 =~ s/\t+//g;
        $ctest2 =~ s/\s+//g;

        if($ctest1 ne ''){
                if($ctest2 eq ''){
                        $old_value = $blank2;
                }
        }
}

#########################################################################
### read_name: read descriptive name of database name		     ####
#########################################################################

sub read_name{
	open(FH, "$data_dir/name_list");
	@name_list = ();
	while(<FH>){
		chomp $_;
		@wtemp = split(/\t+/, $_);
		$ent   = "$wtemp[0]:$wtemp[1]";
		push(@name_list, $ent);
	}
	close(FH);
}

#########################################################################
### find_name: match database name to descriptive name		      ###
#########################################################################

sub find_name{
	$web_name = '';
	$comp = uc ($db_name);
	OUTER:
	foreach $fent (@name_list){
		@wtemp  = split(/:/, $fent);
		$upname = uc ($wtemp[1]);
		if($comp eq $upname){
			$web_name = $wtemp[0];
			last OUTER;
		}
	}
}

####################################################################################
### oredit: update approved list, updates_list, updates data, and send out email ###
####################################################################################

sub oredit{

	$date = `date '+%D'`;
	chop $date;
	$on = "ON";

#-------------------------------------------------
#-----  construct mail to dutysci and CUS archive
#-------------------------------------------------

#------------------
# get the contents
#------------------

	open (OSLOG, "<$temp_dir/$obsid.$sf");
	@oslog = <OSLOG>;
	close (OSLOG);

	open (FILE, ">$temp_dir/ormail_$obsid.$sf");

#--------------------------------------------------------------------------------
#-------if the submitter is non-cxc person, use email address given to the person
#--------------------------------------------------------------------------------

	$s_yes = 0;
	$s_cnt = 0;
		
#----------------------------------------------------------------------------------
#------ without printing everything, for the case of asis, remove, and clone cases 
#------ tell the CUS that these asis, remove or clone case. otherwise print all info
#----------------------------------------------------------------------------------

	if($asis =~ /ASIS/){
		print FILE 'Submitted as "AS IS"---Observation'."  $obsid". ' is added to the approved list',"\n";
	}elsif($asis =~/REMOVE/){
		print FILE 'Submitted as "REMOVE"--Observation'."  $obsid". ' is removed from the approved list',"\n";
	}elsif($asis =~ /CLONE/){
		print FILE 'Submitted as "CLONE"-- Clone observation: '."$obsid\n";
		print FILE "\nExplanation: $comments\n";
	}else{
		foreach $ent (@paramarray){
			unless($ent =~ /ACISTAG/ || $ent =~ /ACISWINTAG/ || $ent =~ /SITAG/ || $ent =~ /GENERALTAG/){
				$new_entry = lc ($ent);
				$new_value = ${$new_entry};
				$old_entry = 'orig_'."$new_entry";
				$old_value = ${$old_entry};
				$test1 = $new_value;
				$test2 = $old_value;
				$test1 =~ s/\n+//g;
				$test1 =~ s/\t+//g;
				$test1 =~ s/\s+//g;
				$test2 =~ s/\n+//g;
				$test2 =~ s/\t+//g;
				$test2 =~ s/\s+//g;

				if($test1 ne $test2){
					change_old_value_to_blank();
					print FILE "$ent $old_value\:\:$new_value\n";
				}
			}

#--------------------
#---- time order case
#--------------------

			if($ent =~ /TIME_ORDR/){
				for($j = 1; $j <= $time_ordr; $j++){
					foreach $tent ('WINDOW_CONSTRAINT', 'TSTART', 'TSTOP'){
						$new_entry = lc ($tent);
						$new_value = ${$new_entry}[$j];
						$old_entry = 'orig_'."$new_entry";
						$old_value = ${$old_entry}[$j];

						if($new_value ne $old_value){
							change_old_value_to_blank();
							print FILE "\tTIME_ORDR: $J   $tent $old_value\:\:$new_value\n";
						}
					}
				}
			}

#--------------------
#--- roll order case
#--------------------

			if($ent =~ /ROLL_ORDR/){
				for($j = 1; $j <= $roll_ordr; $j++){
					foreach $tent ('ROLL_CONSTRAINT', 'ROLL_180','ROLL', 'ROLL_TOLERANCE'){
						$new_entry = lc ($tent);
						$new_value = ${$new_entry}[$j];
						$old_entry = 'orig_'."$new_entry";
						$old_value = ${$old_entry}[$j];

						if($new_value ne $old_value){
							change_old_value_to_blank();
							print FILE "\tROLL_ORDER: $j   $tent $old_value\:\:$new_value\n";
						}
					}
				}
			}
	
#---------------------
#--- acis window case
#---------------------

			if($ent eq "ACISWIN_NO"){
				for($j = 0; $j < $aciswin_no; $j++){
					$jj = $j + 1;
					foreach $tent ('ORDR', 'CHIP',
#							'INCLUDE_FLAG',
							'START_ROW','START_COLUMN',
							'HEIGHT','WIDTH','LOWER_THRESHOLD','PHA_RANGE',
							'SAMPLE'){
						$new_entry = lc ($tent);
						$new_value = ${$new_entry}[$j];
						$old_entry = 'orig_'."$new_entry";
						$old_value = ${$old_entry}[$j];

						if($new_value ne $old_value){
							change_old_value_to_blank();
							print FILE "\tEntry $jj   $tent $old_value\:\:$new_value\n";
						}
					}
				}
			}
		}
	}

	print FILE "@oslog";

	close FILE;

#
#--- external sub to complete oredit task; this may reduce the chance that this cgi 
#--- script stack in unresponsive browser
#


	$asis_ind = param('ASIS');

	if($generaltag eq ''){
		$generaltag = 'OFF';
	}
	if($acistag eq ''){
		$acistag    = 'OFF';
	}
	if($sitag eq ''){
		$sitag      = 'OFF';
	}

	if($si_mode eq ''){
		$si_mode = 'na';
	}

#	system("nohup /opt/local/bin/perl ./oredit_sub.perl $usint_on $obsid $sf $asis  $dutysci $seq_nbr $generaltag $acistag $si_mode $sitag $cus_email $test_email $email_address $sp_user $large_coord $asis_ind &");
#	system("/opt/local/bin/perl ./oredit_sub.perl $usint_on $obsid $sf $asis  $dutysci $seq_nbr $generaltag $acistag $si_mode $sitag $cus_email $test_email $email_address $sp_user $large_coord $asis_ind");

	$test = `ls $temp_dir/*`;               #--- testing whether the data actually exits.

	if($test =~ /$obsid.$sf/){
        	oredit_sub();
	}

#----------------------------------------------
#----  if it hasn't died yet, then close nicely
#----------------------------------------------

        print "<b>Thank you.  Your request has been submitted.";
        print "Approvals occur immediately, changes may take 48 hours. </b><p>";


	if($usint_on =~ /test/){
		print "<A HREF=\"$obs_ss_http/search.html\">Go Back to the Search Page</A>";
	}else{
		print "<A HREF=\"https://cxc.cfa.harvard.edu/cgi-bin/target_search/search.html\">Go Back to the Search Page</a>";
	}

	print "</body>";
	print "</html>";
}

#####################################################################################
######################################################################################
######################################################################################

sub change_old_value_to_blank{

        $stest = $old_value;
        $stest =~ s/\n+//g;
        $stest =~ s/\t+//g;
        $stest =~ s/\s+//g;

        if($stest eq ''){
                $old_value = $blank2;
        }
}

#####################################################################################
### mod_time_format: convert and devide input data format                         ###
#####################################################################################

sub mod_time_format{
	@tentry = split(/\W+/, $input_time);
	$ttcnt  = 0;
	foreach (@tentry){
		$ttcnt++;
	}
	
	$hr_add = 0;
	if($tentry[$ttcnt-1] eq 'PM' || $tentry[$ttcnt-1] eq 'pm'){
		$hr_add = 12;
		$ttcnt--;
	}elsif($tentry[$ttcnt-1] eq 'AM' || $tentry[$ttcnt-1] eq'am'){
		$ttcnt--;
	}elsif($tentry[$ttcnt-1] =~/PM/){
		$hr_add           = 12;
		@tatemp           = split(/PM/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}elsif($tentry[$ttcnt-1] =~/pm/){
		$hr_add           = 12;
		@tatemp           = split(/pm/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}elsif($tentry[$ttcnt-1] =~ /AM/){
		@tatemp           = split(/AM/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}elsif($tentry[$ttcnt-1] =~ /am/){
		@tatemp           = split(/AM/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}
	
	$mon_lett = 0;
	if($tentry[0]  =~ /\D/){
		$day   = $tentry[1];
		$month = $tentry[0];
		$year  = $tentry[2];
		$mon_lett = 1;
	}elsif($tentry[1] =~ /\D/){
		$day   = $tentry[0];
		$month = $tentry[1];
		$year  = $tentry[2];
		$mon_lett = 1;
	}elsif($tentry[0] =~ /\d/ && $tentry[1] =~ /\d/){
		$day   = $tentry[0];
		$month = $tentry[1];
		$year  = $tentry[2];
	}	
	
	$day = int($day);
	if($day < 10){
		$day = '0'."$day";
	}
	
	if($mon_lett > 0){
		if($month    =~ /^JAN/i){$month = '01'}
		elsif($month =~ /^FEB/i){$month = '02'}
		elsif($month =~ /^MAR/i){$month = '03'}
		elsif($month =~ /^APR/i){$month = '04'}
		elsif($month =~ /^MAY/i){$month = '05'}
		elsif($month =~ /^JUN/i){$month = '06'}
		elsif($month =~ /^JUL/i){$month = '07'}
		elsif($month =~ /^AUG/i){$month = '08'}
		elsif($month =~ /^SEP/i){$month = '09'}
		elsif($month =~ /^OCT/i){$month = '10'}
		elsif($month =~ /^NOV/i){$month = '11'}
		elsif($month =~ /^DEC/i){$month = '12'}
	}
	
	@btemp = split(//, $year);
	$yttcnt = 0;
	foreach(@btemp){
		$yttcnt++;
	}
	if($yttcnt < 3){
		if($year > 39){
			$year = '19'."$year";
		}else{
			$year = '20'."$year";
		}
	}
		
	if($ttcnt == 4){
		$hr = $tentry[3];
		unless($hr eq '12' && $hr_add == 12){
			if($hr eq '12' && $hr_add == 0){
				$hr = 0;
			}
			$hr  = $hr + $hr_add;
			$hr  = int($hr);
			if($hr < 10){
				$hr = '0'."$hr";
			}
		}
		$min = '00';
		$sec = '00';
	}elsif($ttcnt == 5){
		$hr = $tentry[3];
		unless($hr eq '12' && $hr_add == 12){
			if($hr eq '12' && $hr_add == 0){
				$hr = 0;
			}
			$hr  = $hr + $hr_add;
			$hr  = int($hr);
			if($hr < 10){
				$hr = '0'."$hr";
			}
		}
		$min = $tentry[4];
		$min = int($min);
		if($min < 10){
			$min = '0'."$min";
		}
		$sec = '00';
	}elsif($ttcnt == 6){
		$hr = $tentry[3];
		unless($hr eq '12' && $hr_add == 12){
			if($hr eq '12' && $hr_add == 0){
				$hr = 0;
			}
			$hr = $hr + $hr_add;
			$hr = int($hr);
			if($hr < 10){
				$hr = '0'."$hr";
			}
		}
		$min = $tentry[4];
		$min = int($min);
		if($min < 10){
			$min = '0'."$min";
		}
		$sec = $tentry[5];
		$sec = int($sec);
		if($sec < 10){
			$sec = '0'."$sec";
		}
	}
	
	$time = "$hr".":$min".":$sec";
}

#########################################################################
### lts_date_check:   check ltd_date is in 30 days or not            ####
#########################################################################

sub lts_date_check{

	if( $lts_lt_plan eq ''){
		$lts_more30 = 'yes';
	}else{
		@ttemp = split(/\s+/, $lts_lt_plan);

       		if($ttemp[1]     =~ /Jan/i){
               		$month = '1';
			$add = 0;
        	}elsif($ttemp[0] =~ /Feb/i){
               		$month = '2';
			$add = 31;
        	}elsif($ttemp[0] =~ /Mar/i){
               		$month = '3';
			$add = 59;
        	}elsif($ttemp[0] =~ /Apr/i){
               		$month = '4';
			$add = 90;
        	}elsif($ttemp[0] =~ /May/i){
               		$month = '5';
			$add = 120;
        	}elsif($ttemp[0] =~ /Jun/i){
               		$month = '6';
			$add = 151;
        	}elsif($ttemp[0] =~ /Jul/i){
               		$month = '7';
			$add = 181;
        	}elsif($ttemp[0] =~ /Aug/i){
               		$month = '8';
			$add = 212;
        	}elsif($ttemp[0] =~ /Sep/i){
               		$month = '9';
			$add = 243;
        	}elsif($ttemp[0] =~ /Oct/i){
               		$month = '10';
			$add = 273;
        	}elsif($ttemp[0] =~ /Nov/i){
               		$month = '11';
			$add = 304;
        	}elsif($ttemp[0] =~ /Dec/i){
               		$month = '12';
			$add = 334;
        	}

		$ychk = 4.0 * int(0.25 * $ttemp[2]);		# a leap year check
		if($ttemp[2] == $ychk){
			if($month > 2){
				$add++;
			}
		}

		$comp_date = $ttemp[1] + $add;
		$year = $ttemp[2];

		if($year == 1999){
			$dom = $comp_date - 202;
		}elsif($year >= 2000){
			$dom = $comp_date + 163 + 365*($year - 2000);
			if($year > 2000) {
				$dom++;
			}
			if($year > 2004) {
				$dom++;
			}
			if($year > 2008) {
				$dom++;
			}
			if($year > 2012) {
				$dom++;
			}
			if($year > 2016) {
				$dom++;
			}
			if($year > 2020) {
				$dom++;
			}
		}
	
		($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime(time);
	
		$uyear = 1900 + $year;

		if($uyear == 1999){
			$cdom = $yday - 202;
		}elsif($uyear >= 2000){
			$cdom = $yday + 163 + 365*($uyear - 2000);
			if($uyear > 2000) {
				$cdom++;
			}
			if($uyear > 2004) {
				$cdom++;
			}
			if($uyear > 2008) {
				$cdom++;
			}
			if($uyear > 2012) {
				$cdom++;
			}
			if($uyear > 2016) {
				$cdom++;
			}
			if($uyear > 2020) {
				$cdom++;
			}
		}
	
		$lts_more30 = 'yes';
		$diff = $dom - $cdom;
		if($diff < 0){
			$lts_more30 = 'closed';
		}elsif($diff < 30){
			$lts_more30 = 'no';
		}
	}
}

####################################################################
### series_rev: getting mointoring observation things           ####
####################################################################

sub series_rev{

#--------------------------------------------------------------
#--- this one and the next subs are taken from target_param.cgi
#--- written by Mihoko Yukita.(10/28/2003)
#--------------------------------------------------------------

     	push @monitor_series, $_[0];
     	my @partial_series;
     	$sqlh1 = $dbh1->prepare(qq(select
              	pre_id from target where obsid = $_[0]));
     	$sqlh1->execute();
     	my $row;
	
     	while ($row = $sqlh1->fetchrow){
	  	return if (! $row =~ /\d+/);
          	push @partial_series, $row;
          	$sqlh2 = $dbh1->prepare(qq(select
                   	obsid from target where pre_id = $row));
          	$sqlh2->execute();
          	my $new_row;

          	while ($new_row = $sqlh2->fetchrow){
              		if ($new_row != $_[0]){
                  		&series_fwd($new_row);
              		}
          	}
          	$sqlh2->finish;
     	}
     	$sqlh1->finish;

     	$skip = 0;
     	OUTER:
     	foreach $ent (@monitor_series){
       		foreach $comp (@partial_series){
               		if($ent == $comp){
                       		$skip = 1;
                       		last OUTER;
               		}
       		}
     	}


     	if($skip == 0){
     		foreach $monitor_elem (@partial_series) {
          		&series_rev($monitor_elem);
     		}
     	}
}

####################################################################
### series_fwd: getting monitoring observation things           ####
####################################################################

sub series_fwd{
     	push @monitor_series, $_[0];
     	my @partial_series;
     	$sqlh1 = $dbh1->prepare(qq(select
              	obsid from target where pre_id = $_[0]));
     	$sqlh1->execute();
     	my $row;

     	while ($row = $sqlh1->fetchrow){
          	push @partial_series, $row;
          	$sqlh2 = $dbh1->prepare(qq(select
                   	pre_id from target where obsid = $row));
          	$sqlh2->execute();
          	my $new_row;

          	while ($new_row = $sqlh2->fetchrow){
              		if ($new_row != $_[0]){
                  		&series_rev($new_row);
              		}
          	}
          	$sqlh2->finish;
     	}
     	$sqlh1->finish;

     	$skip = 0;
     	OUTER:
     	foreach $ent (@monitor_series){
        	foreach $comp (@partial_series){
                	if($ent == $comp){
                        	$skip = 1;
                        	last OUTER;
                	}
        	}
     	}

     	if($skip == 0){
        	foreach $monitor_elem (@partial_series) {
                	&series_fwd($monitor_elem);
        	}
     	}
}

######################################################################
### find_planned_roll: get planned roll from mp web page          ####
######################################################################

sub find_planned_roll{

        open(PFH, "$obs_ss/mp_long_term");
        OUTER:
        while(<PFH>){
		chomp $_;
		@ptemp = split(/:/, $_);
                %{planned_roll.$ptemp[0]} = (planned_roll =>["$ptemp[1]"], planned_range =>["$ptemp[2]"]);

        }
        close(PFH);
}

#####################################################################
### rm_from_approved_list: remove entry from approved list        ###
#####################################################################

sub rm_from_approved_list{

        @temp_app = ();

	open(FH, "$ocat_dir/approved");

#---------------------------------------------------------------
#---- read data, store it except the one which we need to remove
#---------------------------------------------------------------

        OUTER:
        while(<FH>){
                chomp $_;
                @atemp = split(/\t/,$_);
                if($atemp[0] =~ /$obsid/){
                        next OUTER;
                }else{
                        push(@temp_app, $_);
                }
        }
        close(FH);

	system("mv $ocat_dir/approved $ocat_dir/approved~");

#-----------------------------------
#--- print out the new approved list
#-----------------------------------

	open(AOUT, ">$ocat_dir/approved");

        foreach $ent (@temp_app){
                print AOUT "$ent\n";
        }
        close(AOUT);
        system("chmod 644 $ocat_dir/approved");
}


######################################################################################
### send_mail_to_usint: sending out full support request email to USINT            ###
######################################################################################

sub send_mail_to_usint{

#
#--- send email to USINT 
#

	mail_out_to_usint();

#
#----  say thank you to submit email to USINT.
#

	print "<br /><br />";
        print "<b>Thank you.  Your request has been submitted.<br /><br />";
	print "If you have any quesitons, please contact: <a href=\"mailto:$usint_mail\">$usint_mail</a>.</b>";
	print "<br /><br />";

        if($usint_on =~ /test/){
                print "<A HREF=\"$obs_ss_http/search.html\">Go Back to the Search Page</A>";
        }else{
                print "<A HREF=\"$chandra_http\">Chandra Observatory Page</a>";
        }
        print "</body>";
        print "</html>";
}

#####################################################################################
### mail_out_to_usint: sending email to USINT                                     ###
#####################################################################################

sub mail_out_to_usint{


	$temp_file = "$temp_dir/cus_request";
	open(ZOUT, ">$temp_file");
	
	print ZOUT "\n\nAn observer: $submitter had requested a full USINT support for ";
	print ZOUT "OBSID: $obsid.\n\n";
	
	print ZOUT "The observer's email address is: $email_address\n\n";
	
	print ZOUT "Its Ocat Data Page is:\n";
	print ZOUT "https://cxc.cfa.harvard.edu/mta/CUS/Usint/ocatdata2html.cgi?$obsid\n\n";
	
#
#--- today's date
#

	($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime(time);
	$uyear = 1900 + $year;
	
	if($mon < 10){
        	$mon = '0'."$mon";
	}
	
	$mon++;
	if($mday < 10){
        	$mday = '0'."$mday";
	}
	
	$date = "$mon/$mday/$uyear";
	
	print ZOUT  "$date\n";
	close(ZOUT);
#
#--- find an appropriate email address
#

	find_usint();
	
	if($usint_on =~ /test/){
		system("cat $temp_file | mailx -s\"Subject: TEST!! USINT assist requested (to $usint_mail)\n\"  $test_email");
	}else{
		system("cat $temp_file | mailx -s\"Subject: USINT assist requested\n\"  $usint_mail");
	}

	system("rm $temp_file");

}


#######################################################################################
###send_email_to_mp: sending email to MP if the obs is in an active OR list         ###
#######################################################################################

sub send_email_to_mp{
#
#--- check revision number for the new entry.
#

	open(UIN, "$ocat_dir/updates_table.list");
	@vsave = ();
	$vcnt  = 0;
	while(<UIN>){
        	chomp $_;
        	if($_ =~ /$obsid/){
                	@utemp = split(/\s+/, $_);
                	@vtemp = split(/\./, $utemp[0]);
                	$i_val = int ($vtemp[1]);
                	push(@vsave, $i_val);
                	$vcnt++;
        	}
	}
	close(UIN);
	
	@vsorted = sort{$a<=>$b} @vsave;
	$rev     = int($vsorted[$ucnt-1]);
	$rev++;

	if ($rev < 10){
        	$rev = "00$rev";
	} elsif (($rev >= 10) && ($rev < 100)){
        	$rev = "0$rev";
	}

#
#---- start printing the email to MP
#

	$temp_file = "$temp_dir/mp_request";
	open(ZOUT, ">$temp_file");
	
	print ZOUT "\n\nA user: $submitter submitted changes of  ";
	print ZOUT "OBSID: $obsid which is in the current OR list.\n\n";
	
	print ZOUT "The contact email_address address is: $email_address\n\n";
	
	print ZOUT "Its Ocat Data Page is:\n";
	print ZOUT "https://cxc.cfa.harvard.edu/mta/CUS/Usint/ocatdata2html.cgi?$obsid\n\n\n";

	print ZOUT "If you like to see what were changed:\n";

	$file_name = "$obsid".'.'."$rev";
	print ZOUT "https://cxc.cfa.harvard.edu/mta/CUS/Usint/chkupdata.cgi?$file_name\n\n\n";

	print ZOUT "If you have any question about this email, please contact ";
	print ZOUT "swolk\@head.cfa.harvard.edu.","\n\n\n";
	
#
#--- today's date
#

	($sec, $min, $hour, $mday, $mon, $year, $wday, $yday, $isdst) = localtime(time);
	$uyear = 1900 + $year;
	
	if($mon < 10){
        	$mon = '0'."$mon";
	}
	
	$mon++;
	if($mday < 10){
        	$mday = '0'."$mday";
	}
	
	$date = "$mon/$mday/$uyear";
	
	print ZOUT  "$date\n";
	close(ZOUT);

#
#--- find out who is the mp contact person for this obsid
#

	open(IN, "$obs_ss/scheduled_obs_list");
	OUTER:
	while(<IN>){
		chomp $_;
		@mtemp = split(/\s+/, $_);
		if($obsid == $mtemp[0]){
			$mp_contact = $mtemp[1];
			last OUTER;
		}
	}
	close(IN);
	
	$mp_email = "$mp_contact".'@head.cfa.harvard.edu';

	if($usint_on =~ /test/){
		system("cat $temp_file | mailx -s\"Subject:TEST!! Change to Obsid $obsid Which Is in Active OR List ($mp_email)\n\"  $test_email");
	}else{
		system("cat $temp_file | mailx -s\"Subject: Change to Obsid $obsid Which Is in Active OR List\n\"  $mp_email cus\@head.cfa.harvard.edu");
	}

	system("rm $temp_file");

}

#####################################################################################################
### keep_ccd_selection_record: keep ccd selectionin record.                                       ###
#####################################################################################################

sub keep_ccd_selection_record{

#
#--- save CCD option  setting 
#

	$ccd_setting = "$ccdi0_on:$ccdi1_on:$ccdi2_on:$ccdi3_on:$ccds0_on:$ccds1_on:$ccds2_on:$ccds3_on:$ccds4_on:$ccds5_on";

	open(IN, "$ocat_dir/ccd_settings");
	$version  = 1;
	while(<IN>){
		chomp $_;
		@ctemp = split(/\t+/, $_);
		if($ctemp[0] == $obsid){
			$version++;
		}
	}
	close(FH);

	if($version < 10){
		$version = '00'."$version";
	}elsif($version < 100){
		$version =  '0'."$version";
	}

        $date = `date '+%D'`;
        chomp $date;

	open(OUT, ">>$ocat_dir/ccd_settings");
	print OUT "$obsid\t$seq_nbr\t$version\t$date\t$ccd_setting\n";
	close(OUT);
#
#---- you may want to remove the next line, once the script is debugged. Removed 02/25/2011
#

#	system("chmod 777 $ocat_dir/ccd_settings");
}

###############################################################################
### find_usint: find an appropriate usint email address for a given obs.    ###
###############################################################################

sub find_usint {
        if($targname    =~ /CAL/i){
                $usint_mail  = 'ldavid@cfa.harvard.edu';
        }elsif($grating =~ /LETG/i){
                $usint_mail  = 'jdrake@cfa.harvard.edu bwargelin@cfa.harvard.edu';
        }elsif($grating =~ /HETG/i){
                $usint_mail  = 'nss@space.mit.edu  hermanm@spce.mit.edu';
        }elsif($inst    =~ /HRC/i){
                $usint_mail  = 'juda@cfa.harvard.edu vkashyap@cfa.harvard.edu';
        }else{
                if($seq_nbr < 290000){
                        $usint_mail = 'swolk@cfa.harvard.edu';
                }elsif($seq_nbr > 300000 && $seq_nbr < 490000){
                        $usint_mail = 'nadams@cfa.harvard.edu';
                }elsif($seq_nbr > 500000 && $seq_nbr < 590000){
                        $usint_mail = 'plucinsk@cfa.harvard.edu';
                }elsif($seq_nbr > 600000 && $seq_nbr < 690000){
                        $usint_mail = 'jdepasquale@cfa.harvard.edu';
                }elsif($seq_nbr > 700000 && $seq_nbr < 790000){
                        $usint_mail = 'emk@cfa.harvard.edu';
                }elsif($seq_nbr > 800000 && $seq_nbr < 890000){
                        $usint_mail = 'maxim@cfa.harvard.edu';
                }elsif($seq_nbr > 900000 && $seq_nbr < 990000){
                        $usint_mail = 'das@cfa.harvard.edu';
                }
        }
}


####################################################################################
### oredit_sub: external part of oredit; a part ocatdata2html.cgi                ###
####################################################################################

sub oredit_sub{

	$date = `date '+%D'`;
	chop $date;
	$on = "ON";

#-------------------------------------------------
#-----  construct mail to dutysci and CUS archive
#-------------------------------------------------

#------------------
# get the contents
#------------------

	open (OSLOG, "<$temp_dir/$obsid.$sf");
	@oslog = <OSLOG>;
	close (OSLOG);

#-----------------------------
#-----  couple temp variables
#-----------------------------

    	$dutysci_status = "NA";

	if ($asis =~ /ASIS/){

#-----------------------------------------------------
#---- asis case; we need to update the approved list
#-----------------------------------------------------

    		$general_status = "NULL";			# these are for the status verification page
    		$acis_status    = "NULL";			# orupdate.cgi
    		$si_mode_status = "NULL";

    		$dutysci_status = "$dutysci $date";

		open(ASIN, "$ocat_dir/approved");

		@temp_data = ();

		while(<ASIN>){
			chomp $_;
			push(@temp_data,$_);
		}
		close(ASIN);

		system("mv $ocat_dir/approved $ocat_dir/approved~");

		open(ASIN,">$ocat_dir/approved");

		NEXT:
		foreach $ent (@temp_data){
			@atemp = split(/\t/,$ent);
			if($atemp[0] eq "$obsid"){
				next NEXT;
			}else{
				print ASIN "$ent\n";
			}
		}

		print ASIN "$obsid\t$seq_nbr\t$dutysci\t$date\n";
		close(ASIN);
		system("chmod 644 $ocat_dir/approved");

	} elsif ($asis =~ /REMOVE/){

#------------------------------------------------------------------
#-----  remove; we need to remove this obs data from approved list
#------------------------------------------------------------------

    		$general_status = "NULL";
    		$acis_status    = "NULL";
    		$si_mode_status = "NULL";
		$dutysci_status = "$dutysci $date";
		@temp_app       = ();

		open(FH, "$ocat_dir/approved");

		OUTER:
		while(<FH>){
			chomp $_;
			@atemp = split(/\t/,$_);
			if($atemp[0] =~ /$obsid/){
				next OUTER;
			}else{
				push(@temp_app, $_);
			}
		}
		close(FH);

		system("mv $ocat_dir/approved $ocat_dir/approved~");

		open(AOUT,">$ocat_dir/approved");

		foreach $ent (@temp_app){
			print AOUT "$ent\n";
		}
		close(AOUT);
		system("chmod 644 $ocat_dir/approved");

	} elsif ($asis =~/CLONE/){

#-----------------------------------------------------
#---- clone case; no need to update the approved list; 
#---  so just set param for the verification page
#-----------------------------------------------------

		$general_status = "NA";
		$acis_status    = "NULL";
		$si_mode_status = "NULL";

	} else {

#-----------------
#---- general case
#-----------------

#------------------------------------------------------
#---- check and update params for the verification page
#------------------------------------------------------

		if ($generaltag =~/ON/){
			$general_status = "NA";
		} else {
			$general_status = "NULL";
		}
		if ($acistag =~/ON/){
			$acis_status    = "NA";
			$si_mode_status = "NA";
		} else {
			$acis_status    = "NULL";

			if ($si_mode =~/NULL/){
				$si_mode_status = "NA";
			} else {

				if ($sitag =~/ON/){
					$si_mode_status = "NA";
				} else {
					$si_mode_status = "NULL";
				}
			}
		}
	}


#------------------------------------------------------
#-----  (scan for updates directory) read updates_table.list
#-----  find the revision number for obsid in question
#------------------------------------------------------

	system("cat $ocat_dir/updates_table.list |grep $obsid > $temp_dir/utemp");
#	open(UIN, "$ocat_dir/updates_table.list");
	open(UIN, "$temp_dir/utemp");
	@usave = ();
	$ucnt  = 0;
	while(<UIN>){
		chomp $_;
		@utemp = split(/\s+/, $_);
		@vtemp = split(/\./, $utemp[0]);
		$i_val = int ($vtemp[1]);
		push(@usave, $i_val);
		$ucnt++;
	}
	close(UIN);
	system("rm  $temp_dir/utemp");
	
	@usorted = sort{$a<=>$b} @usave;
	$rev     = int($usorted[$ucnt-1]);
	$rev++;

	if ($rev < 10){
    		$rev = "00$rev";
	} elsif (($rev >= 10) && ($rev < 100)){
    		$rev = "0$rev";
	}

#-------------------------------------
#----  get master log file for editing
#-------------------------------------

	$lpass = 0;
	$wtest = 0;
	my $efile = "$ocat_dir/updates_table.list";
	OUTER:
	while($lpass == 0){
		open(my $update, '>>', $efile) or die "Locked";
		if($@){
#
#--- wait 2 cpu seconds before attempt to check in another round
#
			print "Database access is not available... wating a permission<br />";

			$diff  = 0;
			$start = (times)[0];
			while($diff < 2){
				$end  = (times)[0];
				$diff = $end - $start;
			}


			$wtest++;
			if($wtest > 5){
				print "Something is wrong in the submission. Terminating the process.<br />";
				exit();
			}
		}else{
			$lpass = 1;
#--------------------------------------------------------------------------------------------------
#----  if it is not being edited, write update updates_table.list---data for the verificaiton page
#--------------------------------------------------------------------------------------------------

			flock($update, LOCK_EX) or die "died while trying to lock the file<br />\n";
			print $update "$obsid.$rev\t$general_status\t$acis_status\t$si_mode_status\t$dutysci_status\t$seq_nbr\t$dutysci\n";
			close $update;

#---------------------
#----  checkin update
#---------------------


			$chk = "$obsid.$rev";
			$in_test = `cat $ocat_dir/updates_table.list`;
			if($in_test =~ /$chk/i){

#-----------------------------------------------------
#----  copy the revision file to the appropriate place
#-----------------------------------------------------

				system("cp $temp_dir/$obsid.$sf  $ocat_dir/updates/$obsid.$rev");

				last OUTER;
			}
		}
	}

#----------------------------------------------
#----  append arnold update file, if necessary
#----------------------------------------------

	if ($acistag =~/ON/){
    		open (ARNOLD, "<$temp_dir/arnold.$sf");
    		@arnold = <ARNOLD>;
    		close (ARNOLD);
    		$arnoldline = shift @arnold;
#
#--- closed 02/25/11: the directry does not exist any more
#
#    		open (ARNOLDUPDATE, ">>/home/arcops/ocatMods/acis");
#    		print ARNOLDUPDATE "$arnoldline";
#    		close (ARNOLDUPDATE);
	}


#---------------------------#
#----  send messages  ------#
#---------------------------#

###########
$send_email = 'yes';
##########

	if($send_email eq 'yes'){

		if($asis_ind =~ /ASIS/i){

			if($sp_user eq 'no'){
				open(ASIS, ">$temp_dir/asis.$sf");
				print ASIS "$obsid is approved for flight. Thank you \n";
				close(ASIS);

				if($usint_on =~ /test/){
					system("cat $temp_dir/asis.$sf |mailx -s\"Subject:TEST!!  $obsid is approved\n\"  $test_email");
				}else{
					system("cat $temp_dir/asis.$sf |mailx -s\"Subject: $obsid is approved\n\" -c$cus_email $email_address");
				}
				system("rm $temp_dir/asis.$sf");
			}else{
				if($usint_on =~ /test/){
					system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject:TEST!! Parameter Changes (Approved) log  $obsid.$rev\n\" $test_email");
				}else{
					system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes (Approved) log  $obsid.$rev\n\" -c$cus_email $email_address");
				}
			}

			if($usint_on ne 'test' && $usint_on ne 'test_no'){ system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes (Approved) log  $obsid.$rev\n\"  $cus_email");
			}
		}else{
			if($sp_user eq 'no'){
				open(USER, ">$temp_dir/user.$sf");
				print USER "Your change request for obsid $obsid have been received.\n";
				print USER "You will be notified when the changes have been made.\n";
				close(USER);

				if($usint_on =~ /test/){
					system("cat $temp_dir/user.$sf |mailx -s\"Subject:TEST!!  Parameter Changes log  $obsid.$rev\n\"   $test_email");
				}else{
					system("cat $temp_dir/user.$sf |mailx -s\"Subject: Parameter Changes log  $obsid.$rev\n\"   -c$cus_email $email_address");
				}
				system("rm $temp_dir/user.$sf");
			}else{
				if($usint_on =~ /test/){
					system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject:TEST!! Parameter Changes log  $obsid.$rev\n\"  $test_email");
				}else{
					system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes log  $obsid.$rev\n\" -c$cus_email  $email_address");
				}
			}

			if($usint_on =~ /test/){
				system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject:TEST!! Parameter Changes log  $obsid.$rev\n\"  $test_email");
			}else{
				system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes log  $obsid.$rev\n\" $cus_email");
			}
		}
	}

#--------------------------------------------------------------------
#---- if CDO requests exist, send out email to an appropriate person
#--------------------------------------------------------------------

	$cdo_file = "$obsid".'_cdo_warning';
	open(CIN, "$temp_dir/$cdo_file");
	@cdo_warning = ();
	$cdo_w_cnt   = 0;
	while(<CIN>){
		chomp $_;
		$ent = $_;
		$ent = s/<->/:  /g;
		push(@cdo_warning, $_);
		$cdo_w_cnt++;
	}
	close(CIN);
	system("rm $temp_dir/$cdo_file");

	if($cdo_w_cnt > 0){
		$large_coord = 0;
		open(COUT, ">$temp_dir/$cdo_file");
		print COUT "The following entries of OBSOD:$obsid  need CDO assistance:\n\n";
		foreach $ent (@cdo_warning){
			if($ent =~ /DEC/i){
				$large_coord++;
			}
			print COUT "$ent\n";
		}
		close(COUT);

		system("rm $temp_dir/$cdo_file");

#
#--- if there is a large coordinate shift, keep the record so that oredit.cgi can read and mark the observations
#		

		if($large_coord > 0){
			open(LOUT, ">>$ocat_dir/cdo_warning_list");
			print LOUT "$obsid.$rev\n";
			close(LOUT);
		}
	}


#--------------------------
#----  get rid of the junk
#--------------------------

	system("rm -f $temp_dir/*.$sf");

##	system("chmod 777 $temp_dir/$obsid.*");

	system("chmod 755 $ocat_dir/updates_table.list*");
}

##################################################################################
### adjust_o_values: adjust output letter values to a correct one              ###
##################################################################################

sub adjust_o_values{

	$orig_name = 'orig_'."$d_name";			#--- original value is kept here

	if(${$d_name} =~ /CONSTRAINT/i){
		${$d_name} = 'Y';
	}elsif(${$d_name} =~ /PREFERENCE/i){
		${$d_name} = 'P';
	}elsif(${$d_name} =~ /INCLUDE/i){
		${$d_name} = 'I';
	}elsif(${$d_name} =~ /EXCLUDE/i){
		${$d_name} = 'E';
	}elsif(${$d_name} =~ /YES/i){
		${$d_name} = 'Y';

	}elsif(${$d_name} =~ /NO/i){
		if(${$orig_name} eq 'NO'){
			${$d_name} = 'NO';
		}elsif(${$orig_name} eq ''){
			${$d_name} = '';
		}else{
			${$d_name} = 'N';
		}


	}elsif(${$d_name} =~ /NULL/i){
		if(${$orig_name} eq 'N'){
			${$d_name} = 'N';
		}elsif(${$orig_name} eq ''){
			${$d_name} = '';
		}

	}elsif(${$d_name} =~ /NONE/i){
		if(${$orig_name} eq 'NO'){
			${$d_name} = 'NO';
		}elsif(${$orig_name} eq 'N'){
			${$d_name} = 'N';
		}elsif(${$orig_name} eq ''){
			${$d_name} = '';
		}
	}
}

