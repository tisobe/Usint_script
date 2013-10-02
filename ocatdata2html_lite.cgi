#!/soft/ascds/DS.release/ots/bin/perl

BEGIN
{
    $ENV{SYBASE} = "/soft/SYBASE_OCS15.5";
}

use DBI;
use DBD::Sybase;
use CGI qw/:standard :netscape /;

use Fcntl qw(:flock SEEK_END); # Import LOCK_* constants

###############################################################################
#
#	ocatdat2html_lite.cgi: smaller version of ocatdata2html.cgi
#			       read descriptions in ocatdata2html.cgi for
#			       more details.
#
#		author: t. isobe (tisobe@cfa.harvard.edu)
#	
#		last update: Sep 24, 2013
#  
###############################################################################

###############################################################################
#---- before running this script, make sure the following settings are correct.
###############################################################################

#
#---- if this is usint version, set the following param to 'yes', otherwise 'no'
#

$usint_on = 'yes';			##### USINT Version
#$usint_on = 'test_yes';			##### Test Version USINT

#
#---- set a name and email address of a test person
#

$test_user  = 'isobe';
$test_email = 'isobe@head.cfa.harvard.edu';

#
#--- sot/cus contact email address
#

$sot_contact = 'swolk@head.cfa.harvard.edu';
$cus_email   = 'cus@head.cfa.harvard.edu';

#
#---- set directory pathes 
#

#open(IN, '/data/udoc1/ocat/Info_save/dir_list');
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

#if($usint_on =~ /test/i){
#	$ocat_dir = $test_dir;
#}else{
#	$ocat_dir = $real_dir;
#}
	$ocat_dir = $real_dir;

#
#--- set html pages
#

$usint_http   = 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/';	#--- web site for usint users
$obs_ss_http  = 'https://cxc.cfa.harvard.edu/cgi-bin/obs_ss/';	#--- web site for none usint users (GO Expert etc)
$test_http    = 'http://asc.harvard.edu/cgi-gen/mta/Obscat/';	#--- web site for test

$mp_http      = 'http://asc.harvard.edu/';			#--- web site for mission planning related
$chandra_http = 'http://cxc.harvard.edu/';			#--- chandra main web site
$cdo_http     = 'http://icxc.cfa.harvard.edu/cgi-bin/cdo/';	#--- CDO web site

############################
#----- end of settings
############################

#------------------------------------------------------------------------
#--- find obsid requested if there are group id, it may append a new name
#------------------------------------------------------------------------

$temp  = $ARGV[0];
chomp $temp;
$temp  =~ s/\s+//g;	
@atemp = split(/\./, $temp);	
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


$no_sp_user    = 2;				#--- number of special users

@special_user  = ("$test_user",  'mta');
@special_email = ("$test_email", "$test_email");

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

#-------------------------------
#---- read a user-password list
#-------------------------------

open(FH, "<$pass_dir/.htpasswd");

%pwd_list = ();             	# save the user-password list
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

print header(-cookie=>[$user_cookie, $pass_cookie], -type => 'text/html;  charset=utf-8');

print "<!DOCTYPE html>";
print "<html>";
print "<head>";
print "<title>Ocat Data Page</title>";
print "<style  type='text/css'>";
print "table{border-style:solid;border-spacing:8px;border-width:2px;border-collapse:separate}";
print "a:link {color:blue;}";
print "a:visited {color:teal;}";
print "</style>";
print "</head>";

print "<body style='color:#000000;background-color:#FFFFE0'>";

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

#----------------------------------------------------------
#--- check whether the observation is in an active OR list
#----------------------------------------------------------

$mp_check = 0;
CHK_OUT:
foreach $check (@mp_scheduled_list){
	if($check =~ /$obsid/){
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


print start_form();

$time_ordr_special = 'no';
$roll_ordr_special = 'no';
$ordr_special      = 'no';
$check         = param("Check");			# a param which indicates which page to be displayed 

print hidden(-name=>'send_email', -value=>"$send_email");

#-------------------------------------------------
#--------- checking password!
#-------------------------------------------------

if($check eq ''){
	$chg_user_ind = param('chg_user_ind');
	match_user();               	# sub to check inputed user and password

#---------------------------------------------------------------
#--------- if a user and a password do not match ask to re-type
#---------------------------------------------------------------

	if($chg_user_ind eq 'yes'){
		password_check();
	}elsif($pass eq '' || $pass eq 'no'){
    	if(($pass eq 'no') && ($submitter  ne ''|| $pass_word ne '')){

        	print "<h3 style='color:red'>Name and/or Password are not valid.</h3>";

    	}

    	password_check();       			# this one create password input page

	}elsif($pass eq 'yes'){ 		    	# ok a user and a password matched

#-------------------------------------------
#------ check whether s/he is a special user
#-------------------------------------------

		$sp_user   = 'yes';
		$access_ok = 'yes';
       		special_user();			# sub to check whether s/he is a special user
           	pi_check();			# sub to check whether the pi has an access

		print hidden(-name=>'send_email', -value=>"$send_email");

        data_input_page();      # sub to display data for edit

	}else{
    	print 'Something wrong. Exit<br />';
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

#-------------------------------------------------------------------------
#--- if time, roll, and window constraints may need input page update...
#-------------------------------------------------------------------------

	if($check eq '     Add Time Rank     '){

    	$time_ordr     = param("TIME_ORDR");
    	$roll_ordr     = param("ROLL_ORDR");
    	$aciswin_no    = param("ACISWIN_NO");
    	$time_ordr_special = 'yes';
    	$roll_ordr_special = 'no';
    	$ordr_special      = 'no';
    	$time_ordr++;

    	pass_param();               # a sub which passes all parameters between pages
    	data_input_page();              # a sub to  print ocat data page

	}elsif($check eq 'Remove Null Time Entry '){

    	$time_ordr     = param("TIME_ORDR");
    	$roll_ordr     = param("ROLL_ORDR");
    	$aciswin_no    = param("ACISWIN_NO");
    	$time_ordr_special = 'yes';
    	$roll_ordr_special = 'no';
    	$ordr_special      = 'no';

    	pass_param();               # a sub which passes all parameters between pages
    	data_input_page();              # a sub to  print ocat data page

	}elsif($check eq '     Add Roll Rank     '){

    	$time_ordr     = param("TIME_ORDR");
    	$roll_ordr     = param("ROLL_ORDR");
    	$aciswin_no    = param("ACISWIN_NO");
    	$time_ordr_special = 'no';
    	$roll_ordr_special = 'yes';
    	$ordr_special      = 'no';
    	$roll_ordr++;

    	pass_param();               
    	data_input_page();              

	}elsif($check eq 'Remove Null Roll Entry '){

    	$time_ordr     = param("TIME_ORDR");
    	$roll_ordr     = param("ROLL_ORDR");
    	$aciswin_no    = param("ACISWIN_NO");
    	$time_ordr_special = 'no';
    	$roll_ordr_special = 'yes';
    	$ordr_special      = 'no';

    	pass_param();               # a sub which passes all parameters between pages
    	data_input_page();              # a sub to  print ocat data page

	}elsif($check eq '     Add Window Rank     '){

    	$time_ordr     = param("TIME_ORDR");
    	$roll_ordr     = param("ROLL_ORDR");
    	$aciswin_no    = param("ACISWIN_NO");
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
#--- if this is an ARCOPS check and approve request, add the obsid to the list
#

		if($asis =~ /ARCOPS/i){
    		$date = `date '+%D'`;
    		chomp $date;

    		open(OUT, ">>$ocat_dir/arcops_list");
    		print OUT "$obsid\t$date\t$submitter\t$targname\t$instrument\t$grating\n";
    		close(OUT);
#    		system("chmod 777 $ocat_dir/arcops_list");
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

#----------------------------------------------------------------------------------------------------
#--- if no action is taken yet, it comes here; you see this page first (after a user/a password page)
#----------------------------------------------------------------------------------------------------

	}else{
    	if($prev_app == 0){
        	data_input_page();          # just print ocat data page
    	}
	}
}							#---- the end of access_ok loop

#
#--- end of the html document
#
print end_form();
print "</body>";
print "</html>";


#################################################################################################
#---- the main script finishes here. sub-scripts start here.
#################################################################################################



#########################################################################
### password_check: open a user - a password input page           ###
#########################################################################

sub password_check{
	print '<h3>Please type your user name and password</h3>';
    print '<table style="border-width:0px"><tr><th>Name</th><td>';
    print textfield(-name=>'submitter', -value=>'', -size=>20);
    print '</td></tr><tr><th>Password</th><td>';
    print password_field( -name=>'password', -value=>'', -size=>20);
    print '</td></tr></table><br />';

	print hidden(-name=>'Check', -override=>'', -value=>'');
    print '<input type="submit" name="Check" value="Submit">';
}

#########################################################################
### match_user: check a user and a password matches           ###
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
    }else{
        $pass = 'no';
    }
}

#########################################################################
### special_user: check whether the user is a special user        ###
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
### pi_check: check whether the observer has an access to the data          ###
###################################################################################

sub pi_check{
	if($sp_user eq 'yes'){
		$access_ok     = 'yes';
		$email_address = "$user".'@head.cfa.harvard.edu';
	}

	print hidden(-name=>'access_ok', -value=>"$access_ok");
	print hidden(-name=>'pass', -value=>"$pass");
	print hidden(-name=>'email_address', -value=>"$email_address");
}

################################################################################
### pass_param: passing cgi parameter values to the next window          ###
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
	$pass      = param('pass');
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

	$sf        = param('tmp_suf');			# suffix for temp file written in $temp_dir
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
        }elsif($ordr_special =~/yes/i){
            if($ent  =~ /ACISWIN_ID/i){
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

	$time_ordr_add = param("TIME_ORDR_ADD");		#--- if window constraint is addred later, this will be 1

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

		if($window_constraint[$j]    eq 'Y')     {$dwindow_constraint[$j] = 'CONSTRAINT'}
		elsif($window_constraint[$j] eq 'CONSTRAINT'){$dwindow_constraint[$j] = 'CONSTRAINT'}
		elsif($window_constraint[$j] eq 'P')     {$dwindow_constraint[$j] = 'PREFERENCE'}
		elsif($window_constraint[$j] eq 'PREFERENCE'){$dwindow_constraint[$j] = 'PREFERENCE'}
#		elsif($window_constraint[$j] eq 'N')     {$dwindow_constraint[$j] = 'NONE'}
#		elsif($window_constraint[$j] eq 'NONE')      {$dwindow_constraint[$j] = 'NONE'}
#		elsif($window_constraint[$j] eq 'NULL')      {$dwindow_constraint[$j] = 'NULL'}
#		elsif($window_constraint[$j] eq '')      {$dwindow_constraint[$j] = 'NULL'}
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

						$start_month[$j]     = $start_month[$jj];
						$start_date[$j]      = $start_date[$jj];
						$start_year[$j]      = $start_year[$jj];
						$start_time[$j]      = $start_time[$jj];
						$end_month[$j]       = $end_month[$jj];
						$end_date[$j]        = $end_date[$jj];
						$end_year[$j]		 = $end_year[$jj];
						$end_time[$j]        = $end_time[$jj];

						$tstart[$j]          = $tstart[$jj];
						$tstop[$j]           = $tstop[$jj];

#						$window_constraint[$jj]  = 'NULL';
#						$dwindow_constraint[$jj] = 'NULL';
						$start_month[$jj]    =  '';
						$start_date[$jj]     =  '';
						$start_year[$jj]     =  '';
						$start_time[$jj]     =  '';
						$end_month[$jj]      =  '';
						$end_date[$jj]       =  '';
						$end_year[$jj]		 =  '';
						$end_time[$jj]       =  '';

						$tstart[$jj]         =  '';
						$tstop[$jj]          =  '';

						$new_ordr--;
						next TOUT1;
					}elsif($jj == $time_ordr){

#						$window_constraint[$j]   = 'NULL';
#						$dwindow_constraint[$j]  = 'NULL';
						$start_month[$j]     =  '';
						$start_date[$j]      =  '';
						$start_year[$j]      =  '';
						$start_time[$j]      =  '';
						$end_month[$j]       =  '';
						$end_date[$j]        =  '';
						$end_year[$j]		 =  '';
						$end_time[$j]        =  '';

						$tstart[$j]          =  '';
						$tstop[$j]           =  '';

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

	$roll_ordr_add = param("ROLL_ORDR_ADD");		#--- if roll constraint add is requested later, this will be 1

	for($j = 1; $j <= $roll_ordr; $j++){
		foreach $ent ('ROLL_CONSTRAINT','ROLL_180','ROLL','ROLL_TOLERANCE'){
			$name     = "$ent"."$j";
			$val      =  param("$name");
			$lname    = lc($ent);
			${$lname}[$j] = $val;
		}
		if($roll_constraint[$j]    eq 'Y')     {$droll_constraint[$j] = 'CONSTRAINT'}
		if($roll_constraint[$j]    eq 'CONSTRAINT'){$droll_constraint[$j] = 'CONSTRAINT'}
		elsif($roll_constraint[$j] eq 'P')     {$droll_constraint[$j] = 'PREFERENCE'}
		elsif($roll_constraint[$j] eq 'PREFERENCE'){$droll_constraint[$j] = 'PREFERENCE'}
#		elsif($roll_constraint[$j] eq 'N')     {$droll_constraint[$j] = 'NONE'}
#		elsif($roll_constraint[$j] eq 'NONE')      {$droll_constraint[$j] = 'NONE'}
#		elsif($roll_constraint[$j] eq 'NULL')      {$droll_constraint[$j] = 'NULL'}
#		elsif($roll_constraint[$j] eq '')      {$droll_constraint[$j] = 'NULL'}

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
						$roll_180[$j]      = $roll_180[$jj];
						$droll_180[$j]     = $droll_180[$jj];
						$roll[$j]          = $roll[$jj];
						$roll_tolerance[$j]    = $roll_tolerance[$jj];

#						$roll_constraint[$jj]  = 'NULL';
#						$droll_constraint[$jj] = 'NULL';
						$roll_180[$jj]     = 'NULL';
						$droll_180[$jj]    = 'NULL';
						$roll[$jj]         = '';
						$roll_tolerance[$jj]   = '';

						$new_ordr--;
						next TOUT1;

					}elsif($jj == $roll_ordr){
#						$roll_constraint[$jj]  = 'NULL';
#						$droll_constraint[$jj] = 'NULL';
						$roll_180[$jj]     = 'NULL';
						$droll_180[$jj]    = 'NULL';
						$roll[$jj]         = '';
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
		for($j = 0; $j < $aciswin_no; $j++){
			foreach $ent ('ACISWIN_ID', 'ORDR', 'CHIP',
					'START_ROW','START_COLUMN','HEIGHT','WIDTH',
					'LOWER_THRESHOLD','PHA_RANGE','SAMPLE'){
				$name     = "$ent"."$j";
				$val      =  param("$name");
#
#--- added 08/05/11
#
                if($name =~ /LOWER_THRESHOLD/i && $val !~ /\d/){
                    $val  = 0.08;
                }elsif($name =~ /PHA_RANGE/i && $val !~ /\d/){
                    $val  = 13.0;
                }

				$lname    = lc($ent);
				${$lname}[$j] = $val;
			}

			$include_flag[$j]  = 'E';
			$dinclude_flag[$j] = 'EXCLUDE';
		}
	}elsif($spwindow =~ /N/i){
#
#---- if window filter is set to Null or No, set everything to a Null setting
#
		$aicswin_id[0]      = '';
		$ordr[0]        = '';
        $chip[0]        = 'NULL';
        $dinclude_flag[0]   = 'INCLUDE';
        $include_flag[0]    = 'I';
        $start_row[0]       = '';
        $start_column[0]    = '';
        $height[0]      = '';
        $width[0]       = '';
        $lower_threshold[0] = '';
        $pha_range[0]       = '';
        $sample[0]      = '';
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
	elsif($window_flag eq '')      {$dwindow_flag = 'NULL'; $window_flag = 'NULL';}
	elsif($window_flag eq 'Y')     {$dwindow_flag = 'YES'}
	elsif($window_flag eq 'YES')       {$dwindow_flag = 'YES'}
	elsif($window_flag eq 'N')     {$dwindow_flag = 'NO'}
	elsif($window_flag eq 'NO')    {$dwindow_flag = 'NO'}
	elsif($window_flag eq 'P')     {$dwindow_flag = 'PREFERENCE'}
	elsif($window_flag eq 'PREFERENCE'){$dwindow_flag = 'PREFERENCE'}

	if($roll_flag    eq 'NULL')    {$droll_flag = 'NULL'}
	elsif($roll_flag eq '')        {$droll_flag = 'NULL'; $roll_flag = 'NULL';}
	elsif($roll_flag eq 'Y')       {$droll_flag = 'YES'}
	elsif($roll_flag eq 'YES')     {$droll_flag = 'YES'}
	elsif($roll_flag eq 'N')       {$droll_flag = 'NO'}
	elsif($roll_flag eq 'NO')      {$droll_flag = 'NO'}
	elsif($roll_flag eq 'P')       {$droll_flag = 'PREFERENCE'}
	elsif($roll_flag eq 'PREFERENCE')  {$droll_flag = 'PREFERENCE'}
	
	if($dither_flag    eq 'NULL')      {$ddither_flag = 'NULL'}
	elsif($dither_flag eq '')      {$ddither_flag = 'NULL'; $dither_flag = 'NULL';}
	elsif($dither_flag eq 'Y')     {$ddither_flag = 'YES'}
	elsif($dither_flag eq 'YES')       {$ddither_flag = 'YES'}
	elsif($dither_flag eq 'N')     {$ddither_flag = 'NO'}
	elsif($dither_flag eq 'NO')    {$ddither_flag = 'NO'}
	
	if($uninterrupt    eq 'NULL')      {$duninterrupt = 'NULL'}
	elsif($uninterrupt eq '')      {$duninterrupt = 'NULL'; $uninterrupt = 'NULL';}
	elsif($uninterrupt eq 'N')     {$duninterrupt = 'NO'}
	elsif($uninterrupt eq 'NO')    {$duninterrupt = 'NO'}
	elsif($uninterrupt eq 'Y')     {$duninterrupt = 'YES'}
	elsif($uninterrupt eq 'YES')       {$duninterrupt = 'YES'}
	elsif($uninterrupt eq 'P')     {$duninterrupt = 'PREFERENCE'}
	elsif($uninterrupt eq 'PREFERENCE'){$duninterrupt = 'PREFERENCE'}

	if($photometry_flag    eq 'NULL')  {$dphotometry_flag = 'NULL'}
	elsif($photometry_flag eq 'Y')     {$dphotometry_flag = 'YES'}
	elsif($photometry_flag eq 'YES')   {$dphotometry_flag = 'YES'}
	elsif($photometry_flag eq 'N')     {$dphotometry_flag = 'NO'}
	elsif($photometry_flag eq 'NO')    {$dphotometry_flag = 'NO'}
	
	if($constr_in_remarks    eq 'N')         {$dconstr_in_remarks = 'NO'}
	elsif($constr_in_remarks eq 'NO')        {$dconstr_in_remarks = 'NO'}
	elsif($constr_in_remarks eq 'Y')         {$dconstr_in_remarks = 'YES'}
	elsif($constr_in_remarks eq 'YES')       {$dconstr_in_remarks = 'YES'}
	elsif($constr_in_remarks eq 'P')         {$dconstr_in_remarks = 'PREFERENCE'}
	elsif($constr_in_remarks eq 'PREFERENCE')    {$dconstr_in_remarks = 'PREFERENCE'}

	if($phase_constraint_flag    eq 'NULL')      {$dphase_constraint_flag = 'NULL'}
	elsif($phase_constraint_flag eq 'N')     {$dphase_constraint_flag = 'NONE'}
	elsif($phase_constraint_flag eq 'NO')    {$dphase_constraint_flag = 'NONE'}
	elsif($phase_constraint_flag eq 'Y')     {$dphase_constraint_flag = 'CONSTRAINT'}
	elsif($phase_constraint_flag eq 'CONSTRAINT'){$dphase_constraint_flag = 'CONSTRAINT'}
	elsif($phase_constraint_flag eq 'P')     {$dphase_constraint_flag = 'PREFERENCE'}
	elsif($phase_constraint_flag eq 'PREFERENCE'){$dphase_constraint_flag = 'PREFERENCE'}

    if($monitor_flag    eq 'NULL')           {$dmonitor_flag = 'NULL'; 
							$monitor_flag = 'N'}
    elsif($monitor_flag eq '')           {$dmonitor_flag = 'NULL'}
    elsif($monitor_flag eq 'Y')          {$dmonitor_flag = 'YES'}
    elsif($monitor_flag eq 'YES')        {$dmonitor_flag = 'YES'; 
							$monitor_flag = 'Y'}
    elsif($monitor_flag eq 'N')          {$dmonitor_flag = 'NO'}
    elsif($monitor_flag eq 'NO')         {$dmonitor_flag = 'NO'; 
							$monitor_flag = 'N'}

#
#---- if phase constraint flag is set for Null, set all phase constraint params to Null
#

	if($phase_constraint_flag =~ /N/i 
		&& $phase_constraint_flag !~ /CONSTRAINT/i 
		&& $phase_constraint_flag !~ /PREFERENCE/i){
		$phase_epoch    = '';
		$phase_period       = '';
		$phase_start    = '';
		$phase_start_margin = '';
		$phase_end      = '';
		$phase_end_margin   = '';
	}

	if($multitelescope    eq 'Y')     {$dmultitelescope = 'YES'}
	elsif($multitelescope eq 'YES')       {$dmultitelescope = 'YES'}
	elsif($multitelescope eq 'N')     {$dmultitelescope = 'NO'}
	elsif($multitelescope eq 'NO')    {$dmultitelescope = 'NO'}
	elsif($multitelescope eq 'P')     {$dmultitelescope = 'PREFERENCE'}
	elsif($multitelescope eq 'PREFERENCE'){$dmultitelescope = 'PREFERENCE'}


	if($hrc_zero_block    eq 'NULL')      {$dhrc_zero_block = 'NULL'}
	elsif($hrc_zero_block eq '')      {$dhrc_zero_block = 'NO'; $hrc_zero_block = 'N';}
	elsif($hrc_zero_block eq 'Y')     {$dhrc_zero_block = 'YES'}
	elsif($hrc_zero_block eq 'YES')       {$dhrc_zero_block = 'YES'}
	elsif($hrc_zero_block eq 'N')     {$dhrc_zero_block = 'NO'}
	elsif($hrc_zero_block eq 'NO')    {$dhrc_zero_block = 'NO'}

	if($most_efficient    eq 'NULL')      {$dmost_efficient = 'NULL'}
	elsif($most_efficient eq '')      {$dmost_efficient = 'NULL'}
	elsif($most_efficient eq 'Y')     {$dmost_efficient = 'YES'}
	elsif($most_efficient eq 'YES')       {$dmost_efficient = 'YES'}
	elsif($most_efficient eq 'N')     {$dmost_efficient = 'NO'}
	elsif($most_efficient eq 'NO')    {$dmost_efficient = 'NO'}

	if($ccdi0_on    eq 'NULL')        {$dccdi0_on = 'NULL'}
	elsif($ccdi0_on eq 'Y')           {$dccdi0_on = 'YES'}
	elsif($ccdi0_on eq 'YES')         {$dccdi0_on = 'YES'}
	elsif($ccdi0_on eq 'N')           {$dccdi0_on = 'NO'}
	elsif($ccdi0_on eq 'NO')          {$dccdi0_on = 'NO'}
	elsif($ccdi0_on eq 'OPT1')         {$dccdi0_on = 'OPT1'}
	elsif($ccdi0_on eq 'OPT2')        {$dccdi0_on = 'OPT2'}
	elsif($ccdi0_on eq 'OPT3')        {$dccdi0_on = 'OPT3'}
	elsif($ccdi0_on eq 'OPT4')        {$dccdi0_on = 'OPT4'}
	elsif($ccdi0_on eq 'OPT5')        {$dccdi0_on = 'OPT5'}
	if($ccdi0_on eq 'OPT1')           {$ccdi0_on  = 'O1'}
	elsif($ccdi0_on eq 'OPT2')        {$ccdi0_on  = 'O2'}
	elsif($ccdi0_on eq 'OPT3')        {$ccdi0_on  = 'O3'}
	elsif($ccdi0_on eq 'OPT4')        {$ccdi0_on  = 'O4'}
	elsif($ccdi0_on eq 'OPT5')        {$ccdi0_on  = 'O5'}
	
	
	if($ccdi1_on    eq 'NULL')        {$dccdi1_on = 'NULL'}
	elsif($ccdi1_on eq 'Y')           {$dccdi1_on = 'YES'}
	elsif($ccdi1_on eq 'YES')         {$dccdi1_on = 'YES'}
	elsif($ccdi1_on eq 'N')           {$dccdi1_on = 'NO'}
	elsif($ccdi1_on eq 'NO')          {$dccdi1_on = 'NO'}
	elsif($ccdi1_on eq 'OPT1')        {$dccdi1_on = 'OPT1'}
	elsif($ccdi1_on eq 'OPT2')        {$dccdi1_on = 'OPT2'}
	elsif($ccdi1_on eq 'OPT3')        {$dccdi1_on = 'OPT3'}
	elsif($ccdi1_on eq 'OPT4')        {$dccdi1_on = 'OPT4'}
	elsif($ccdi1_on eq 'OPT5')        {$dccdi1_on = 'OPT5'}
	if($ccdi1_on eq 'OPT1')           {$ccdi1_on  = 'O1'}
	elsif($ccdi1_on eq 'OPT2')        {$ccdi1_on  = 'O2'}
	elsif($ccdi1_on eq 'OPT3')        {$ccdi1_on  = 'O3'}
	elsif($ccdi1_on eq 'OPT4')        {$ccdi1_on  = 'O4'}
	elsif($ccdi1_on eq 'OPT5')        {$ccdi1_on  = 'O5'}
	
	if($ccdi2_on    eq 'NULL')        {$dccdi2_on = 'NULL'}
	elsif($ccdi2_on eq 'Y')           {$dccdi2_on = 'YES'}
	elsif($ccdi2_on eq 'YES')         {$dccdi2_on = 'YES'}
	elsif($ccdi2_on eq 'N')           {$dccdi2_on = 'NO'}
	elsif($ccdi2_on eq 'NO')          {$dccdi2_on = 'NO'}
	elsif($ccdi2_on eq 'OPT1')        {$dccdi2_on = 'OPT1'}
	elsif($ccdi2_on eq 'OPT2')        {$dccdi2_on = 'OPT2'}
	elsif($ccdi2_on eq 'OPT3')        {$dccdi2_on = 'OPT3'}
	elsif($ccdi2_on eq 'OPT4')        {$dccdi2_on = 'OPT4'}
	elsif($ccdi2_on eq 'OPT5')        {$dccdi2_on = 'OPT5'}
	if($ccdi2_on eq 'OPT1')           {$ccdi2_on  = 'O1'}
	elsif($ccdi2_on eq 'OPT2')        {$ccdi2_on  = 'O2'}
	elsif($ccdi2_on eq 'OPT3')        {$ccdi2_on  = 'O3'}
	elsif($ccdi2_on eq 'OPT4')        {$ccdi2_on  = 'O4'}
	elsif($ccdi2_on eq 'OPT5')        {$ccdi2_on  = 'O5'}
	
	if($ccdi3_on    eq 'NULL')        {$dccdi3_on = 'NULL'}
	elsif($ccdi3_on eq 'Y')           {$dccdi3_on = 'YES'}
	elsif($ccdi3_on eq 'YES')         {$dccdi3_on = 'YES'}
	elsif($ccdi3_on eq 'N')           {$dccdi3_on = 'NO'}
	elsif($ccdi3_on eq 'NO')          {$dccdi3_on = 'NO'}
	elsif($ccdi3_on eq 'OPT1')        {$dccdi3_on = 'OPT1'}
	elsif($ccdi3_on eq 'OPT2')        {$dccdi3_on = 'OPT2'}
	elsif($ccdi3_on eq 'OPT3')        {$dccdi3_on = 'OPT3'}
	elsif($ccdi3_on eq 'OPT4')        {$dccdi3_on = 'OPT4'}
	elsif($ccdi3_on eq 'OPT5')        {$dccdi3_on = 'OPT5'}
	if($ccdi3_on eq 'OPT1')           {$ccdi3_on  = 'O1'}
	elsif($ccdi3_on eq 'OPT2')        {$ccdi3_on  = 'O2'}
	elsif($ccdi3_on eq 'OPT3')        {$ccdi3_on  = 'O3'}
	elsif($ccdi3_on eq 'OPT4')        {$ccdi3_on  = 'O4'}
	elsif($ccdi3_on eq 'OPT5')        {$ccdi3_on  = 'O5'}
	
	if($ccds0_on    eq 'NULL')        {$dccds0_on = 'NULL'}
	elsif($ccds0_on eq 'Y')           {$dccds0_on = 'YES'}
	elsif($ccds0_on eq 'YES')         {$dccds0_on = 'YES'}
	elsif($ccds0_on eq 'N')           {$dccds0_on = 'NO'}
	elsif($ccds0_on eq 'NO')          {$dccds0_on = 'NO'}
	elsif($ccds0_on eq 'OPT1')        {$dccds0_on = 'OPT1'}
	elsif($ccds0_on eq 'OPT2')        {$dccds0_on = 'OPT2'}
	elsif($ccds0_on eq 'OPT3')        {$dccds0_on = 'OPT3'}
	elsif($ccds0_on eq 'OPT4')        {$dccds0_on = 'OPT4'}
	elsif($ccds0_on eq 'OPT5')        {$dccds0_on = 'OPT5'}
	if($ccds0_on eq 'OPT1')           {$ccds0_on  = 'O1'}
	elsif($ccds0_on eq 'OPT2')        {$ccds0_on  = 'O2'}
	elsif($ccds0_on eq 'OPT3')        {$ccds0_on  = 'O3'}
	elsif($ccds0_on eq 'OPT4')        {$ccds0_on  = 'O4'}
	elsif($ccds0_on eq 'OPT5')        {$ccds0_on  = 'O5'}
	
	if($ccds1_on    eq 'NULL')        {$dccds1_on = 'NULL'}
	elsif($ccds1_on eq 'Y')           {$dccds1_on = 'YES'}
	elsif($ccds1_on eq 'YES')         {$dccds1_on = 'YES'}
	elsif($ccds1_on eq 'N')           {$dccds1_on = 'NO'}
	elsif($ccds1_on eq 'NO')          {$dccds1_on = 'NO'}
	elsif($ccds1_on eq 'OPT1')        {$dccds1_on = 'OPT1'}
	elsif($ccds1_on eq 'OPT2')        {$dccds1_on = 'OPT2'}
	elsif($ccds1_on eq 'OPT3')        {$dccds1_on = 'OPT3'}
	elsif($ccds1_on eq 'OPT4')        {$dccds1_on = 'OPT4'}
	elsif($ccds1_on eq 'OPT5')        {$dccds1_on = 'OPT5'}
	if($ccds1_on eq 'OPT1')           {$ccds1_on  = 'O1'}
	elsif($ccds1_on eq 'OPT2')        {$ccds1_on  = 'O2'}
	elsif($ccds1_on eq 'OPT3')        {$ccds1_on  = 'O3'}
	elsif($ccds1_on eq 'OPT4')        {$ccds1_on  = 'O4'}
	elsif($ccds1_on eq 'OPT5')        {$ccds1_on  = 'O5'}
	
	if($ccds2_on    eq 'NULL')        {$dccds2_on = 'NULL'}
	elsif($ccds2_on eq 'Y')           {$dccds2_on = 'YES'}
	elsif($ccds2_on eq 'YES')         {$dccds2_on = 'YES'}
	elsif($ccds2_on eq 'N')           {$dccds2_on = 'NO'}
	elsif($ccds2_on eq 'NO')          {$dccds2_on = 'NO'}
	elsif($ccds2_on eq 'OPT1')        {$dccds2_on = 'OPT1'}
	elsif($ccds2_on eq 'OPT2')        {$dccds2_on = 'OPT2'}
	elsif($ccds2_on eq 'OPT3')        {$dccds2_on = 'OPT3'}
	elsif($ccds2_on eq 'OPT4')        {$dccds2_on = 'OPT4'}
	elsif($ccds2_on eq 'OPT5')        {$dccds2_on = 'OPT5'}
	if($ccds2_on eq 'OPT1')           {$ccds2_on  = 'O1'}
	elsif($ccds2_on eq 'OPT2')        {$ccds2_on  = 'O2'}
	elsif($ccds2_on eq 'OPT3')        {$ccds2_on  = 'O3'}
	elsif($ccds2_on eq 'OPT4')        {$ccds2_on  = 'O4'}
	elsif($ccds2_on eq 'OPT5')        {$ccds2_on  = 'O5'}
	
	if($ccds3_on    eq 'NULL')        {$dccds3_on = 'NULL'}
	elsif($ccds3_on eq 'Y')           {$dccds3_on = 'YES'}
	elsif($ccds3_on eq 'YES')         {$dccds3_on = 'YES'}
	elsif($ccds3_on eq 'N')           {$dccds3_on = 'NO'}
	elsif($ccds3_on eq 'NO')          {$dccds3_on = 'NO'}
	elsif($ccds3_on eq 'OPT1')        {$dccds3_on = 'OPT1'}
	elsif($ccds3_on eq 'OPT2')        {$dccds3_on = 'OPT2'}
	elsif($ccds3_on eq 'OPT3')        {$dccds3_on = 'OPT3'}
	elsif($ccds3_on eq 'OPT4')        {$dccds3_on = 'OPT4'}
	elsif($ccds3_on eq 'OPT5')        {$dccds3_on = 'OPT5'}
	if($ccds3_on eq 'OPT1')           {$ccds3_on  = 'O1'}
	elsif($ccds3_on eq 'OPT2')        {$ccds3_on  = 'O2'}
	elsif($ccds3_on eq 'OPT3')        {$ccds3_on  = 'O3'}
	elsif($ccds3_on eq 'OPT4')        {$ccds3_on  = 'O4'}
	elsif($ccds3_on eq 'OPT5')        {$ccds3_on  = 'O5'}

	if($ccds4_on    eq 'NULL')        {$dccds4_on = 'NULL'}
	elsif($ccds4_on eq 'Y')           {$dccds4_on = 'YES'}
	elsif($ccds4_on eq 'YES')         {$dccds4_on = 'YES'}
	elsif($ccds4_on eq 'N')           {$dccds4_on = 'NO'}
	elsif($ccds4_on eq 'NO')          {$dccds4_on = 'NO'}
	elsif($ccds4_on eq 'OPT1')        {$dccds4_on = 'OPT1'}
	elsif($ccds4_on eq 'OPT2')        {$dccds4_on = 'OPT2'}
	elsif($ccds4_on eq 'OPT3')        {$dccds4_on = 'OPT3'}
	elsif($ccds4_on eq 'OPT4')        {$dccds4_on = 'OPT4'}
	elsif($ccds4_on eq 'OPT5')        {$dccds4_on = 'OPT5'}
	if($ccds4_on eq 'OPT1')           {$ccds4_on  = 'O1'}
	elsif($ccds4_on eq 'OPT2')        {$ccds4_on  = 'O2'}
	elsif($ccds4_on eq 'OPT3')        {$ccds4_on  = 'O3'}
	elsif($ccds4_on eq 'OPT4')        {$ccds4_on  = 'O4'}
	elsif($ccds4_on eq 'OPT5')        {$ccds4_on  = 'O5'}
	
	if($ccds5_on    eq 'NULL')        {$dccds5_on = 'NULL'}
	elsif($ccds5_on eq 'Y')           {$dccds5_on = 'YES'}
	elsif($ccds5_on eq 'YES')         {$dccds5_on = 'YES'}
	elsif($ccds5_on eq 'N')           {$dccds5_on = 'NO'}
	elsif($ccds5_on eq 'NO')          {$dccds5_on = 'NO'}
	elsif($ccds5_on eq 'OPT1')        {$dccds5_on = 'OPT1'}
	elsif($ccds5_on eq 'OPT2')        {$dccds5_on = 'OPT2'}
	elsif($ccds5_on eq 'OPT3')        {$dccds5_on = 'OPT3'}
	elsif($ccds5_on eq 'OPT4')        {$dccds5_on = 'OPT4'}
	elsif($ccds5_on eq 'OPT5')        {$dccds5_on = 'OPT5'}
	if($ccds5_on eq 'OPT1')           {$ccds5_on  = 'O1'}
	elsif($ccds5_on eq 'OPT2')        {$ccds5_on  = 'O2'}
	elsif($ccds5_on eq 'OPT3')        {$ccds5_on  = 'O3'}
	elsif($ccds5_on eq 'OPT4')        {$ccds5_on  = 'O4'}
	elsif($ccds5_on eq 'OPT5')        {$ccds5_on  = 'O5'}
	
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

    if($multiple_spectral_lines    eq 'NULL')       {$dmultiple_spectral_lines = 'NULL'}
    if($multiple_spectral_lines eq 'Y')         {$dmultiple_spectral_lines = 'YES'}
    elsif($multiple_spectral_lines eq 'YES')    {$dmultiple_spectral_lines = 'YES'}
    elsif($multiple_spectral_lines eq 'N')      {$dmultiple_spectral_lines = 'NO'}
    elsif($multiple_spectral_lines eq 'NO')     {$dmultiple_spectral_lines = 'NO'}

    if($spwindow    eq 'NULL')      {$dspwindow = 'NULL'}
    elsif($spwindow eq 'Y')     {$dspwindow = 'YES'}
    elsif($spwindow eq 'YES')       {$dspwindow = 'YES'}
    elsif($spwindow eq 'N')     {$dspwindow = 'NO'}
    elsif($spwindow eq 'NO')    {$dspwindow = 'NO'}

	if($spwindow    eq 'NULL')	{$dspwindow = 'NULL'}
	elsif($spwindow eq 'Y')		{$dspwindow = 'YES'}
	elsif($spwindow eq 'YES')	{$dspwindow = 'YES'}
	elsif($spwindow eq 'N')		{$dspwindow = 'NO'}
	elsif($spwindow eq 'NO')	{$dspwindow = 'NO'}

	if($subarray eq 'N')     {$dsubarray = 'NO';
				      $subarray  = 'NONE'}
	elsif($subarray eq 'NO')     {$dsubarray = 'NO';
			          $subarray  = 'NONE'}
	elsif($subarray eq 'NONE')   {$dsubarray = 'NO'}
	elsif($subarray eq 'Y')      {$dsubarray = 'YES'}
	elsif($subarray eq 'YES')    {$dsubarray = 'YES';
				      $subarray  = 'CUSTOM'}
	elsif($subarray eq 'CUSTOM') {$dsubarray = 'YES'}


#
#---- added 08/05/11
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
			$sample[$j]      = '';
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
### sub read_databases: read out values from databases               ###
################################################################################

sub read_databases{

#------------------------------------------------
#-------  database username, password, and server
#------------------------------------------------

	$db_user = "browser";
	$server  = "ocatsqlsrv";

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

#---------------------------------------------
#----------  get mp remarks from target table
#---------------------------------------------

	$sqlh1 = $dbh1->prepare(qq(select mp_remarks  from target where obsid=$obsid));
	$sqlh1->execute();
  	($mp_remarks) = $sqlh1->fetchrow_array;
	$sqlh1->finish;

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
	       		@group[$group_count - 1] = "@group[$group_count - 1]<br />";
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
		$roll_180[$tordr]    = $rollreq_data[1];
		$roll[$tordr]        = $rollreq_data[2];
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
		$tstart[$tordr]        = $timereq_data[1];
		$tstop[$tordr]         = $timereq_data[2];
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

	if ($hrcid){
		$sqlh1 = $dbh1->prepare(qq(select 
			hrc_zero_block,timing_mode,si_mode 
		from hrcparam where hrcid=$hrcid));
		$sqlh1->execute();
		@hrcdata = $sqlh1->fetchrow_array;
		$sqlh1->finish;
        
    		$hrc_zero_block      = $hrcdata[0];
    		$hrc_timing_mode     = $hrcdata[1];
		$hrc_si_mode     = $hrcdata[2];
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
    		$onchip_sum      	= $acisdata[12];
    		$onchip_row_count    	= $acisdata[13];
    		$onchip_column_count 	= $acisdata[14];
    		$frame_time      	= $acisdata[15];

    		$subarray        	= $acisdata[16];
    		$subarray_start_row  	= $acisdata[17];
    		$subarray_row_count  	= $acisdata[18];
    		$duty_cycle      	= $acisdata[19];
    		$secondary_exp_count 	= $acisdata[20];

    		$primary_exp_time    	= $acisdata[21];
    		$eventfilter     	= $acisdata[22];
    		$eventfilter_lower   	= $acisdata[23];
    		$eventfilter_higher  	= $acisdata[24];
    		$most_efficient      	= $acisdata[25];

		$dropped_chip_count     = $acisdata[26];
		$multiple_spectral_lines = $acisdata[27];
		$spectra_max_count       = $acisdata[28];

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
    		$onchip_sum      	= "NULL";
    		$onchip_row_count    	= "NULL";
    		$onchip_column_count 	= "NULL";
    		$frame_time      	= "NULL";
    		$subarray        	= "NONE";
    		$subarray_start_row  	= "NULL";
    		$subarray_row_count  	= "NULL";
    		$subarray_frame_time 	= "NULL";
    		$duty_cycle      	= "NULL";
    		$secondary_exp_count 	= "NULL";
    		$primary_exp_time    	= "";
    		$eventfilter     	= "NULL";
    		$eventfilter_lower   	= "NULL";
    		$eventfilter_higher  	= "NULL";
    		$spwindow        	= "NULL";
    		$most_efficient      	= "NULL";
		$dropped_chip_count     = "NULL";
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

			$ordr[$j]	     = $aciswindata[0];
			$start_row[$j]       = $aciswindata[1];
			$start_column[$j]    = $aciswindata[2];
			$width[$j]	     = $aciswindata[3];
			$height[$j]	     = $aciswindata[4];
			$lower_threshold[$j] = $aciswindata[5];

			if($lower_threshold[$j] > 0.5){
				$awc_l_th = 1;
			}

			$pha_range[$j]       = $aciswindata[6];
			$sample[$j]	     = $aciswindata[7];
			$chip[$j]	     = $aciswindata[8];
			$include_flag[$j]    = $aciswindata[9];
			$aciswin_id[$j]      = $aciswindata[10];

			$j++;
		}
		$aciswin_no = $j;

		$sqlh1->finish;

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
#			$ordr[$j]	     = $aciswindata[0];
#			$start_row[$j]       = $aciswindata[1];
#			$start_column[$j]    = $aciswindata[2];
#			$width[$j]	     = $aciswindata[3];
#			$height[$j]	     = $aciswindata[4];
#			$lower_threshold[$j] = $aciswindata[5];
#
#			if($lower_threshold[$j] > 0.5){
#				$awc_l_th = 1;
#			}
#
#			$pha_range[$j]       = $aciswindata[6];
#			$sample[$j]	     = $aciswindata[7];
#			$chip[$j]	     = $aciswindata[8];
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
	$phase_epoch    = $phasereqdata[1];
	$phase_start    = $phasereqdata[2];
	$phase_end      = $phasereqdata[3];
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

	$sqlh1 = $dbh1->prepare(qq(select soe_roll from soe where obsid=$obsid and unscheduled='N'));
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
		$roll_180[$k]    =~ s/\s+//g; 
		$roll[$k]        =~ s/\s+//g;
		$roll_tolerance[$k]  =~ s/\s+//g; 
	}

	for($k = 1; $k <= $time_ordr; $k++){
		$window_constraint[$k] =~ s/\s+//g; 
	}

	for($k = 0; $k < $aciswin_no; $k++){
		$aciswin_id[$k]      =~ s/\s+//g;
		$ordr[$k]        =~ s/\s+//g;
		$chip[$k]        =~ s/\s+//g;
		$include_flag[$k]    =~ s/\s+//g;
		$start_row[$k]       =~ s/\s+//g; 
		$start_column[$k]    =~ s/\s+//g; 
		$width[$k]       =~ s/\s+//g; 
		$height[$k]      =~ s/\s+//g; 
		$lower_threshold[$k] =~ s/\s+//g; 
		$pha_range[$k]       =~ s/\s+//g; 
		$sample[$k]      =~ s/\s+//g; 
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
#		elsif($window_constraint[$k] eq 'N')   {$dwindow_constraint[$k] = 'NONE'}
#		elsif($window_constraint[$k] eq 'NULL'){$dwindow_constraint[$k] = 'NULL'}
#		elsif($window_constraint[$k] eq ''){
#				$window_constraint[$k]  = 'NULL';
#				$dwindow_constraint[$k] = 'NULL';
#		}
	}	
	
	for($k = 1; $k <= $roll_ordr; $k++){
		if($roll_constraint[$k]    eq 'Y')   {$droll_constraint[$k] = 'CONSTRAINT'}
		elsif($roll_constraint[$k] eq 'P')   {$droll_constraint[$k] = 'PREFERENCE'}
		elsif($roll_constraint[$k] eq 'N')   {$droll_constraint[$k] = 'NONE'}
#		elsif($roll_constraint[$k] eq 'NULL'){$droll_constraint[$k] = 'NULL'}
#		elsif($roll_constraint[$k] eq ''){
#				$roll_constraint[$k]  = 'NULL';
#				$droll_constraint[$k] = 'NULL';
#		}

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
#----  the end of the CCD OPT settings			
#

#
#---- ACIS subarray setting
#
	if($subarray eq '')     {$dsubarray = 'NO'}
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

    if($multiple_spectral_lines eq 'NULL') {$dmultiple_spectral_lines = 'NULL'}
    if($multiple_spectral_lines eq '')  {$dmultiple_spectral_lines = 'NULL'; $multiple_spectral_lines = 'NULL'}
    elsif($multiple_spectral_lines eq 'Y') {$dmultiple_spectral_lines = 'YES'}
    elsif($multiple_spectral_lines eq 'N') {$dmultiple_spectral_lines = 'NO'}

    if($spwindow eq 'NULL')    {$dspwindow = 'NULL'}
    elsif($spwindow eq '' )    {$dspwindow = 'NULL'; $spwindow = 'NULL'}
    elsif($spwindow eq 'Y')    {$dspwindow = 'YES'}
    elsif($spwindow eq 'N')    {$dspwindow = 'NO'}

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
#--- added 08/05/11
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
		MULTIPLE_SPECTRAL_LINES, SPECTRA_MAX_COUNT,                         #--- added 03/29/11
		EVENTFILTER_HIGHER,SPWINDOW,ACISWIN_ID,ORDR, FEP,DROPPED_CHIP_COUNT, BIAS_RREQUEST,
		TOO_ID,TOO_TRIG,TOO_TYPE,TOO_START,TOO_STOP,TOO_FOLLOWUP,TOO_REMARKS,
		REMARKS,COMMENTS,
		MONITOR_FLAG,				#---- this one is added 3/1/06
		MULTITELESCOPE_INTERVAL,		#---- this one is added 9/2/08
		EXTENDED_SRC,
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
		MULTIPLE_SPECTRAL_LINES, SPECTRA_MAX_COUNT,                         #--- added 03/29/11
#		EVENTFILTER_HIGHER,SPWINDOW,ACISWIN_ID, ORDR, ACISWINTAG,
		EVENTFILTER_HIGHER,SPWINDOW,ACISWIN_ID, 
		REMARKS,COMMENTS, ACISTAG,SITAG,GENERALTAG,
		DROPPED_CHIP_COUNT, GROUP_ID, MONITOR_FLAG,
		EXTENDED_SRC,


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
		FEP,DROPPED_CHIP_COUNT,
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
		MULTIPLE_SPECTRAL_LINES, SPECTRA_MAX_COUNT,     #--- added 03/29/11
		);

#---------------------------------------
#----- all the param in acis window data
#---------------------------------------

	@aciswinarray=(START_ROW,START_COLUMN,HEIGHT,WIDTH,LOWER_THRESHOLD,
		       PHA_RANGE,SAMPLE,ACISWIN_ID,ORDR,CHIP,
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
			CONSTR_IN_REMARKS,ROLL_FLAG,WINDOW_FLAG, MONITOR_FLAG
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

	$time_ordr_add = 0;			 # added 09/10/12

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
		$roll_180[$j]    = 'NULL';
		$roll[$j]        = '';
		$roll_tolerance[$j]  = '';
	}

	for($j = 1; $j < 30; $j++){			# save them as the original values
		$orig_roll_constraint[$j] = $roll_constraint[$j];
		$orig_roll_180[$j]    = $roll_180[$j];
		$orig_roll[$j]        = $roll[$j];
		$orig_roll_tolerance[$j]  = $roll_tolerance[$j];
	}

	$roll_ordr_add = 0;			 # added 09/10/12

#--------------------------------------------
#----- special treatment for acis window data
#--------------------------------------------

	for($j = 0; $j < $aciswin_no; $j++){
		if($chip[$j] eq '') {$chip[$j] = 'NULL'}
		if($chip[$j] eq 'N'){$chip[$j] = 'NULL'}
		if($include_flag[$j] eq '') {
			if($spwindow_flag =~ /Y/i){
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
		$ordr[$j]      = '';
		$chip[$j] 	   = 'NULL';
		$include_flag[$j]  = 'E';
		$dinclude_flag[$j] = 'EXCLUDE';
	}

	for($j = 0; $j < 30; $j++){
		$orig_aciswin_id[$j]      = $aciswin_id[$j];
		$orig_ordr[$j]        = $ordr[$j];
		$orig_chip[$j]        = $chip[$j];
		$orig_include_flag[$j]    = $include_flag[$j];
        $orig_start_row[$j]       = $start_row[$j];
        $orig_start_column[$j]    = $start_column[$j];
        $orig_width[$j]       = $width[$j];
        $orig_height[$j]      = $height[$j];
        $orig_lower_threshold[$j] = $lower_threshold[$j];
        $orig_pha_range[$j]       = $pha_range[$j];
        $orig_sample[$j]      = $sample[$j];

	}
#--------------------------------------------
#--- check planned roll
#--------------------------------------------

	find_planned_roll();

	$scheduled_roll = ${planned_roll.$obsid}{planned_roll}[0];

}


########################################################################################
### data_input_page: create data input page--- Ocat Data Page            ###
########################################################################################

sub data_input_page{

print <<endofhtml;

endofhtml

print '	<h1>Obscat Data Page Lite</h1>';

if($mp_check > 0){
	print "<h2><strong style='color:red'>";
	print "This observation is currently under review in an active OR list. ";
	print "You must get a permission from MP to modify entries.";
	print "</strong></h2>";
}

if($status !~ /scheduled/i && $status !~ /unobserved/i){
	$cap_status = uc($status);
	print "<h2>This observation was <span style='color:red'>$cap_status</span>.</h2> ";
}

print ' <p><strong>This version does not support parameter explanations and ';
print ' a few other things may behave differently from the full version. If you like to use ';
print " a full version, please go to <a href='https://cxc.cfa.harvard.edu/mta/CUS/Usint/ocatdata2html_full.cgi?$obsid'>";
print "https://cxc.cfa.harvard.edu/mta/CUS/Usint/ocatdata2html_full.cgi?$obsid</a>. ";
print 'If you like to see explanations of parameters, please click "here" in the line below.</strong> </p>';

print '<p>A brief description of the listed parameters is given ';

#----------------------------------------------------------------------
#---- if the observation is alrady in an active OR list, print warning
#----------------------------------------------------------------------

if($usint_on =~ /no/){
	print a({-href=>"$obs_ss_http/user_help.html",-target=>'_blank'},"here");
}elsif($usint_on =~ /yes/){
	print a({-href=>"$usint_http/user_help.html",-target=>'_blank'},"here");
}
print "</p>";


if($eventfilter_lower > 0.5 || $awc_l_th == 1){
    print '<p style="color:red;padding-top:20px;padding-bottom:10px">';
	print '<strong>';
	if($eventfilter_lower > 0.5 && $awc_l_th == 0){
    	print 'Energy Filter Lowest Energy is larger than 0.5 keV. ';
	}elsif($eventfilter_lower > 0.5 && $awc_l_th == 1){
    	print 'Energy Filter Lowest Energy and ACIS Window Costraint Lowest Energy are larger than 0.5 keV. ';
	}elsif($eventfilter_lower <= 0.5 && $awc_l_th == 1){
    	print 'ACIS Window Costraint Lowest Energy is larger than 0.5 keV. ';
	}
    print 'Please check all Spatial Window parameters of each CCD.';
	print '</strong>';
	print '</p>';
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

	print '<h2>General Parameters</h2>';

#------------------------------------------------>
#----- General Parameter dispaly starts here----->
#------------------------------------------------>

	print '<table style="border-width:0px">';
	print '<tr><td>&#160;</td>';
	print "<th>Sequence Number:";
	print "</th><td><a href='https://cxc.cfa.harvard.edu/cgi-bin/mp/target.cgi?$seq_nbr' target='_blank'>$seq_nbr</a></td>";
	print '<th>Status:';
	print "</th><td>$status</td>";
	print '<th>ObsID #:';
	print "</th><td>$obsid";
	print '<input type="hidden" name="OBSID" value="$obsid">';
	print "</td>";
	print '<th>Proposal Number:</th>';
	print "<td>$proposal_number</td>";
	print '</tr></table>';

	print '<table  style="border-width:0px">';
	print '<tr><td>&#160;</td>';
	print '<th>Proposal Title:</th>';
	print "<td>$proposal_title</td>";
	print '</tr>';
	print ' </table>';
	
	print '<table  style="border-width:0px">';
	print '<tr>';
	print '<td>&#160;</td>';
	print '<th>Obs AO Status:';
	print "</th><td>$obs_ao_str</td>";
	print '</tr></table>';

	print '<table  style="border-width:0px">';
	print '<tr><td>&#160;</td>';
	print '<th>Target Name:</th><td>';
	print "$targname",'</td>';
	print '<th>SI Mode:</th>';

	print '<td style="text-align:left"><input type="text" name="SI_MODE" value="',"$si_mode",'" size="12"></td>';

	print '<th>ACA Mode:</th>';
	print '<td style="text-align:left">',"$aca_mode",'</td>';
	print '</tr></table>';

	print '<table style="border-width:0px">';
	print '<tr><td>&#160;</td>';

	print '<th>Instrument:</th><td>';
	print popup_menu(-name=>'INSTRUMENT', -value=>['ACIS-I','ACIS-S','HRC-I','HRC-S'],
		 	-default=>"$instrument",-override=>100000);
	
	print '</td><th>Grating:</th><td>';
	print popup_menu(-name=>'GRATING', -value=>['NONE','HETG','LETG'],
		 	-default=>"$grating",-override=>10000);
	
	print '</td><th>Type:</th><td>';
	print popup_menu(-name=>'TYPE', -value=>['GO','TOO','GTO','CAL','DDT','CAL_ER', 'ARCHIVE', 'CDFS'],
		 	-default=>"$type",-override=>10000);
	
	print '</td></tr></table>';
	
	print '<table style="border-width:0px">';
	print '<tr>';
	print '<th>PI Name:';
	print "</th><td>$PI_name</td>";
	print '<th>Observer:';
	print "</th><td> $Observer</td></tr>";

	print '<tr><th>Exposure Time:</TH>';
	print '<td style="text-align:left"><input type="text" name="APPROVED_EXPOSURE_TIME" value="';
	print "$approved_exposure_time".'" size="8"> ks</td>';

	print '<th>Remaining Exposure Time:</TH>';
	print "<td>$rem_exp_time ks</td>";
	print '</tr></table>';
	
	print '<table style="border-width:0px">';

	print '<tr><th>Joint Proposal:</th>';
	print "<td>$proposal_joint</td><td>&#160;</td><td>&#160;</td><td>&#160;</td></tr>";

	print "<tr><td>&#160;</td><th>HST Approved Time:</th><td>$proposal_hst</td>";
	print "<th>NOAO Approved Time:</th><td>$proposal_noao</td>";
	print '</tr>';
	print "<tr><td>&#160;</td><th>XMM Approved Time:</th><td>$proposal_xmm</td>";
	print "<th>RXTE Approved Time:</th><td>$rxte_approved_time</td>";
	print '</tr>';
	print "<tr><td>&#160;</td><th>VLA Approved Time:</th><td>$vla_approved_time</td>";
	print "<th>VLBA Approved Time:</th><td>$vlba_approved_time</td>";
	print '</tr>';
	print '</table>';
	
	
	print '<table style="border-width:0px">';
	print '<tr>';
	print '<th>Schedule Date:</TH>';
	print "<td>$soe_st_sched_date</td>";
	print '<th>LTS Date:';
	print "</TH><td>$lts_lt_plan</td>";
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

	print '<p style="padding-bottom:10px">You may enter RA and Dec in either HMS/DMS format (separated by colons, e.g. ';
	print '16:22:04.8  -27:43:04.0), or as decimal degrees.  The original OBSCAT decimal ';
	print ' degree values are provided below the update boxes .';

#    $view_http = "$obs_ss_http/PSPC_page/plot_pspc.cgi?"."$obsid";
    	$view_http = "$$usint_http/PSPC_page/plot_pspc.cgi?"."$obsid";
	print 'If you like to see the current viewing orientation, open: ';

	$test = `ls /data/targets/'."$seq_nbr".'/*.gif`;
	if($test =~ /soe/){
		print "<a href = 'http://cxc.harvard.edu/targets/$seq_nbr/$seq_nbr.$obsid.soe.rass.gif' target='_blank'>RASS</a>, ";
		print "<a href = 'http://cxc.harvard.edu/targets/$seq_nbr/$seq_nbr.$obsid.soe.pspc.gif' target='_blank'>ROSAT</a>, or  ";
		print "<a href = 'http://cxc.harvard.edu/targets/$seq_nbr/$seq_nbr.$obsid.soe.dss.gif'  target='_blank'>DSS</a>. ";
	}else{
		print "<a href = 'http://cxc.harvard.edu/targets/$seq_nbr/$seq_nbr.$obsid.rass.gif' target='_blank'>RASS</a>, ";
		print "<a href = 'http://cxc.harvard.edu/targets/$seq_nbr/$seq_nbr.$obsid.pspc.gif' target='_blank'>ROSAT</a>, or  ";
		print "<a href = 'http://cxc.harvard.edu/targets/$seq_nbr/$seq_nbr.$obsid.dss.gif'  target='_blank'>DSS</a>. ";
	}
	print "(Note: These figures do not always exist.)</p>";

	print '<table style="border-width:0px">';
	print '<tr><td>&#160;</td>';

	print '<th>RA (HMS):</th>';

	print '<td style="text-align:left"><input type="text" name="RA" value="',"$tra",'" size="14"></td>';
	
	print '<th>Dec (DMS):</th>';

	print '<td style="text-align:left"><input type="text" name="DEC" value="',"$tdec",'" size="14"></td>';
	print '<th>Planned Roll:</th><td>',"$scheduled_roll";
	print '</td></tr>';

	print '<tr><td>&#160;</td>';
	print '<th>RA:</TH><td>',"$dra",'</td>';
	print '<th>Dec:</TH><td>',"$ddec",'</td>';

	if($status =~ /^OBSERVED/i || $status =~ /ARCHIVED/i){
	}else{
		$roll_obsr ='';
	}

    print '<th>Roll Observed:</th>';
    print '<td style="text-align:left">',"$roll_obsr";
	print "<input type=\"hidden\" name=\"ROLL_OBSR\" value=\"$roll_obsr\">";
	print '</td>';
	print '</tr></table>';

	print '<table style="border-width:0px">';
	print '<tr>';

	print '<th>Offset: Y:</th>';

	print '<td style="text-align:left"><input type="text" name="Y_DET_OFFSET" value="';
	print "$y_det_offset";
	print '" size="12"> arcmin</td><td></td>';

	print '<th>Z:</th>';

	print '<td style="text-align:left"><input type="text" name="Z_DET_OFFSET" value="';
	print "$z_det_offset";
	print '" size="12"> arcmin</td>';
	print '</tr><tr>';
	print '<th>Z-Sim:</th>';
	print '<td style="text-align:left"><input type="text" name="TRANS_OFFSET" value="';
	print "$trans_offset";
	print '" size="12"> mm<td>';
	print '<th>Sim-Focus:</th>';
	print '<td style="text-align:left"><input type="text" name="FOCUS_OFFSET" value="';
	print "$focus_offset";
	print '" size="12"> mm</td>';

	print '<tr>';

	print '<th>Focus:</th>';
	print '<td style="text-align:left"><input type="text" name="DEFOCUS" value="',"$defocus", '" size="12"></td>';
	print '<td></td>';

	print '<th>Raster Scan:</th>';
	print "<td style='text-align:left'>$raster_scan</td>";
	print '</tr></table>';

	print '<table style="border-width:0px">';

	print '<tr><th>Uninterrupted Obs:</th><td>';
	print popup_menu(-name=>'UNINTERRUPT', -value=>['NULL','NO','PREFERENCE','YES'], 
			 	-default=>"$duninterrupt",-override=>1000);
#
#--- added 08/05/11
#
    print '</td><td>&#160;</td>';
    print '<th>Extended SRC:</th><td>';
    print popup_menu(-name=>'EXTENDED_SRC', -value=>['NO','YES'],
            -default=>"$dextended_src",-override=>1000);
    print '</td></tr>';


	print '<tr><th>Solar System Object:</th><td>';
	print popup_menu(-name=>'OBJ_FLAG',-value=>['NO','MT','SS'],-default=>"$obj_flag", -override=>10000);
	print '</td><td>&#160;';
	print '</td><th>Object:</th><td>';
	print popup_menu(-name=>'OBJECT', 
	 		-value=>['NONE','NEW','COMET','EARTH','JUPITER','MARS','MOON','NEPTUNE',
	      		'PLUTO','SATURN','URANUS','VENUS'],
	 		-default=>"$object", -override=>10000);
	print '</tr><tr>';
	
	print '<th>Photometry:</th><td>';
	print popup_menu(-name=>'PHOTOMETRY_FLAG', -value=>['NULL','YES','NO'], 
			 -default=>"$dphotometry_flag", -override=>100000);
	print '</td>';

	print '<td>&#160;</td>';
	print '<th>V Mag:';
	print "</th><td style='text-align:left'><input type=\"text\" name=\"VMAGNITUDE\" value=\"$vmagnitude\" size=\"12\"></td>";
	print '<tr>';
	print '<th>Count Rate:</th>';
	print '<td style="text-align:left"><input type="text" name="EST_CNT_RATE"';
	print " value=\"$est_cnt_rate\" size=\"12\"></td>";
	print '<td>&#160;</td>';
	print '<th>1st Order Rate:';
	print '</th><td style="text-align:left"><input type="text" name="FORDER_CNT_RATE"';
	print " value=\"$forder_cnt_rate\" size=\"12\"></td>";
	print '</tr></table>';

	print '<hr />';

	print '<h2>Dither</h2>';

	print '<table  style="border-width:0px">';
	print '<tr><th>Dither:</th><td>';
	print popup_menu(-name=>'DITHER_FLAG', -value=>['NULL','YES','NO'], 
		 	-default=>"$ddither_flag", -override=>100000);
	print '</td><td>&#160;</td><td>&#160;</td><td>&#160;</td><td>&#160;</td><td>&#160;</td></tr>';

	print '<tr><td>&#160;</td><th>y_amp (in arcsec):</th>';
	print '<td style="text-align:left"><input type="text" name="Y_AMP_ASEC" value="',"$y_amp_asec",'" size="8"></td>';

	print '<th>y_freq (in arcsec/sec):</th>';
	print '<td style="text-align:left"><input type="text" name="Y_FREQ_ASEC" value="',"$y_freq_asec",'" size="8"></td>';

	print '<th>y_phase:</th>';
	print '<td style="text-align:left"><input type="text" name="Y_PHASE" value="',"$y_phase",'" size="8"></td>';
	print '</tr>';
#---
    print '<tr><td>&#160;</td><th>y_amp (in degrees):</th>';
    print '<td style="text-align:left">',"$y_amp",'</td>';

    print '<th>y_freq(in degree/sec)</th>';
    print '<td style="text-align:left">',"$y_freq",'</td>';

    print '<th>&#160;</th>';
    print '<td style="text-align:left">&#160;</td>';
    print '</tr>';
#----
	
	print '<tr><td>&#160;</td><th>z_amp (in arcsec):</th>';
	print '<td style="text-align:left"><input type="text" name="Z_AMP_ASEC" value="',"$z_amp_asec",'" size="8"></td>';

	print '<th>z_freq (in arcsec/sec):</th>';
	print '<td style="text-align:left"><input type="text" name="Z_FREQ_ASEC" value="',"$z_freq_asec",'" size="8"></td>';

	print '<th>z_phase:</th>';
	print '<td style="text-align:left"><input type="text" name="Z_PHASE" value="',"$z_phase",'" size="8"></td>';
	print '</tr>';

#---
    print '<tr><td>&#160;</td><th>z_amp (in degrees):</th>';
    print '<td style="text-align:left">',"$z_amp",'</td>';
 
    print '<th>z_freq(in degree/sec)</th>';
    print '<td style="text-align:left">',"$z_freq",'</td>';
 
    print '<th>&#160;&#160;</th>';
    print '<td>&#160;</td>';
    print '</tr>';
#----
	
	print '</table>';
	
	print '<hr />';

#-------------------------------------
#----- time constraint case start here
#-------------------------------------

	print '<h2>Time Constraints</h2>';

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

		if($time_ordr_add == 0){
			print '<p style="padding-bottom:20px">';
			print 'If you want to add ranks, press "Add Time Rank." If you want to remove null entries, press "Remove Null Time Entry."';
			print '</p>';
			print '<strong>Rank</strong>: ';
			print '<spacer type=horizontal size=30>';
	
			print '<spacer type=horizontal size=50>';
			print submit(-name=>'Check',-value=>'     Add Time Rank     ')	;
			print submit(-name=>'Check',-value=>'Remove Null Time Entry ')	;
		}

		print '<table style="border-width:0px">';
		print '<tr><th>Rank</th>
			<th>Window Constraint<th>
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
	
			print '<tr><td style="text-align:center"><strong>';
			print "$k";
			print '</strong></td><td>';
	
			$twindow_constraint = 'WINDOW_CONSTRAINT'."$k";
	
			if($sp_user eq'yes' || $dwindow_constraint[$k] =~ /CONSTRAINT/i){
				print popup_menu(-name=>"$twindow_constraint", -value=>['CONSTRAINT','PREFERENCE'],
			 		-default=>"$dwindow_constraint[$k]", -override=>100000);
			}else{
				print popup_menu(-name=>"$twindow_constraint", -value=>['PREFERENCE'],
			 		-default=>"$dwindow_constraint[$k]", -override=>100000);
			}
			print '</td><th>Start</th><td>';
	
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
                   			'2009','2010','2011','2012','2013','2014', '2015', '2016', '2017','2018', '2019', '2020'],
        				-default=>"$start_year[$k]",-override=>1000000);
			print '</td><td>';

			$tstart_time = 'START_TIME'."$k";
	
			print textfield(-name=>"$tstart_time", -size=>'8', -default =>"$start_time[$k]", ,-override=>1000000);
	
			print '</td></tr><tr><td>&#160;</td><td>&#160;</td>';
	
			print '</td><th>End</th><td>';
	
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
                   			'2009','2010','2011','2012','2013','2014', '2015', '2016', '2017','2018', '2019', '2020'],
        				-default=>"$end_year[$k]", -override=>100000);
			print '</td><td>';
	
			$tend_time = 'END_TIME'."$k";
	
			print textfield(-name=>"$tend_time", -size=>'8', -default =>"$end_time[$k]",-override=>1000000);
			print '</td></tr>';
		}
		print '</table>';
	}	
	print '<hr />';

#-------------------------------------
#---- Roll Constraint Case starts here
#-------------------------------------

    print '<h2 style="padding-bottom:20px">Roll Constraints </h2>';

	
    $target_http = "$mp_http/targets/"."$seq_nbr".'/'."$seq_nbr".'.rollvis.gif';
	
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

		if($roll_ordr_add == 0){
			print '<p style="padding-bottom:20px">If you want to add a rank, press "Add Roll Rank".';
			print 'If you want to remove null entries, press "Remove Null Roll Entry."';
			print '</p>';

			print '<strong>Rank</strong>: ';
			print '<spacer type=horizontal size=30>';
	
			print '<spacer type=horizontal size=50>';
			print submit(-name=>'Check',-value=>'     Add Roll Rank     ') ;
			print submit(-name=>'Check',-value=>'Remove Null Roll Entry ') ;
		}

		print '<table style="border-width:0px">';
		print '<tr><th>Rank</th>
			<th>Type of Constraint</th>
			<th>Roll180?</th>
			<th>Roll</th>
			<th>Roll Tolerance</th></tr>';
	
		for($k = 1; $k <= $roll_ordr; $k++){
			print '<tr><td align=center><strong>';
			print "$k";	
			print '</strong></td><td>';
			$troll_constraint = 'ROLL_CONSTRAINT'."$k";
			if($sp_user eq 'yes' || $droll_constraint[$k] =~ /YES/i){
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
		print '</table>';
	}

#----------------------------------------
#----- Other Constraint Case starts here
#----------------------------------------

	print '<hr />';
	print '<h2>Other Constraints</h2>';
	print '<table style="border-width:0px">';
	print '<tr>';
	

	print '<th>Constraints in Remarks?:</th><td>';
	print popup_menu(-name=>'CONSTR_IN_REMARKS', -value=>['YES','PREFERENCE','NO'],
		 -default=>"$dconstr_in_remarks", -override=>100000);
	print ' </td></tr>';
	print '</table>';

	print '<table style="border-width:0px">';
	print '<tr>';
	print '<th>Phase Constraint:</th>
	<td style="text-align:left">';
	
	print " $dphase_constraint_flag";
    print "<input type=\"hidden\" name=\"PHASE_CONSTRAINT_FLAG\" value=\"$dphase_constraint_flag\">";


#	if($sp_user eq 'yes' || $dphase_constraint_flag =~ /CONSTRAINT/i){
#		print popup_menu(-name=>'PHASE_CONSTRAINT_FLAG', -value=>['NONE','CONSTRAINT','PREFERENCE','NULL'],
#		 	-default=>"$dphase_constraint_flag", -override=>10000);
#	}else{
#		print popup_menu(-name=>'PHASE_CONSTRAINT_FLAG', -value=>['NONE','PREFERENCE','NULL'],
#		 	-default=>"$dphase_constraint_flag", -override=>1000000);
#	}

	

	print '</td></tr></table>';

	if($dphase_constraint_flag =~ /NONE/ || $dphase_constraint_flag =~ /NULL/){
			# do nothing
	}else{
		print '<table style="border-width:0px">';
		print '<tr><td>&#160;</td>';
		print '<th>Phase Epoch:</th>';
		print '<td style="text-align:left"><input type="text" name="PHASE_EPOCH" value=';
		print "\"$phase_epoch\"",' size="12"></td>';
		print '<th>Phase Period:</th>';
		print '<td style="text-align:left"><input type="text" name="PHASE_PERIOD" value=';
		print "\"$phase_period\"", ' size="12"></td>';
		print '<td>&#160;</td><td>&#160;</td></tr>';
		
		print '<tr><td>&#160;</td>';
		print '<th>Phase Start:</th>';
		print '<td style="text-align:left"><input type="text" name="PHASE_START" value=';
		print "\"$phase_start\"",' size="12"></td>';
		print '<th>Phase Start Margin:</th>';
		print '<td style="text-align:left"><input type="text" name="PHASE_START_MARGIN" value=';
		print "\"$phase_start_margin\"",' size="12"></td>';
		print '</tr><tr>';
		print '<td>&#160;</td>';
		print '<th>Phase End:</th>';
		print '<td style="text-align:left"><input type="text" name="PHASE_END" value=';
		print "\"$phase_end\"",' size="12"></td>';
		print '<th>Phase End Margin:</th>';
		print '<td style="text-align:left"><input type="text" name="PHASE_END_MARGIN" value=';
		print "\"$phase_end_margin\"",' size="12"></td>';
		print '</tr></table>';
	}

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

	print '<table style="border-width:0px">';
	print '<tr>';

	print '<th>Group ID:</th>';
	print '<td>';

	if($group_id){
		print "$group_id";
		print "<input type='hidden' name='GROUP_ID' value=\"$group_id\">";
	}else{
		print '  No Group ID  ';
	}
	print '</td>';

	print '<th>Monitoring Observation:  </th>';
	print '<td>';

	if($sp_user eq 'yes' && ($dmonitor_flag =~ /Y/i || $dmonitor_flag == '') 
			     && ($group_id =~ /\s+/ || $group_id eq '')){
		print popup_menu(-name=>'MONITOR_FLAG', -values=>['NO','YES','NULL'],
               	-default=>"$dmonitor_flag",-override=>10000);
	}elsif($sp_user eq 'yes' && $dmonitor_flag =~ /Y/i && $group_id =~ /\w/ ){
		print popup_menu(-name=>'MONITOR_FLAG', -values=>['NO','YES','NULL'],
               	-default=>"$dmonitor_flag",-override=>10000);
	}
	print '</td>';

	print '<td>';
	print '</td></tr></table>';

	if($group_id){
		print "<br />Observations in the Group: @group<br />";
	}elsif($monitor_flag =~ /Y/i){
		print "<br /> Observations in the Monitoring: @monitor_series_list<br />";
	}else{
		print "<br />";
	}

	if($group_id =~ /No Group ID/ || $group_id !~ /\d/){
		print '<table style="border-width:0px">';

		print '<tr><th>Follows ObsID#:</th>';
		print '<td style="text-align:left"><input type="text" name="PRE_ID" value="',"$pre_id",'" size="8"></td>';
		
		print '<th>Min Int<br />(pre_min_lead):</th>';
		print '<td style="text-align:left"><input type="text" name="PRE_MIN_LEAD" value="',"$pre_min_lead",'" size="8"></td>';
	
		print '<th>Max Int<br />(pre_max_lead):</th>';
		print '<td style="text-align:left"><input type="text" name="PRE_MAX_LEAD" value="',"$pre_max_lead",'" size="8"></td>';
		print '</tr></table>';
	}else{
      		print '<table style="border-width:0px">';

       		print '<tr><th>Follows ObsID#:</th>';
       		print '<td style="text-align:left">',"$pre_id",'</td>';
	
       		print '<th>Min Int<br />(pre_min_lead):</th>';
       		print '<td style="text-align:left">',"$pre_min_lead",'</td>';
	
       		print '<th>Max Int<br />(pre_max_lead):</th>';
       		print '<td style="text-align:left">',"$pre_max_lead",'</td>';
       		print '</tr></table>';

		print "<input type=\"hidden\" name=\"PRE_ID\" value=\"$pre_id\"\>";
		print "<input type=\"hidden\" name=\"PRE_MIN_LEAD\" value=\"$pre_min_lead\"\>";
		print "<input type=\"hidden\" name=\"PRE_MAX_LEAD\" value=\"$pre_max_lead\"\>";
	}


	print '<table style="border-width:0px">';
	print '<tr>';
	print '<th>Coordinated Observation:</th><td>';
	print popup_menu(-name=>'MULTITELESCOPE', -value=>['NO','YES','PREFERENCE'],
	 		-default=>"$dmultitelescope",-override=>1000000);
	print '</td>';
	print '<td>&#160;</td>';
	print '<th>Observatories:</th>';
	print '<td style="text-align:left"><input type="text" name="OBSERVATORIES" value=';
	print "\"$observatories\"",' size="12"></td>';
    print '</tr>';

    print '<tr>';
	print '<th>Max Coordination Offset:</th>';
	print '<td style="text-align:left"><input type="text" name="MULTITELESCOPE_INTERVAL" value=';
	print "\"$multitelescope_interval\"",' size="12"></td>';
	print "<td>&#160;</td><td>&#160;</td><td>&#160;</td>";

	print '</tr> </table>';

	print '<hr />';


#--------------------
#----- HRC Parameters
#--------------------

	print '<h2>HRC Parameters</h2>';
	print '<table style="border-width:0px">';
	print '<tr><td></td>';

	print '<th>HRC Timing Mode:</th><td>';
	print popup_menu(-name=>'HRC_TIMING_MODE', -value=>['NO','YES'], 
		 	-default=>"$dhrc_timing_mode", -override=>100000);
	print '</td>';
	
	print '<th>Zero Block:</th><td>';
	print popup_menu(-name=>'HRC_ZERO_BLOCK', -value=>['NO','YES'], 
		 	-default=>"$dhrc_zero_block", -override=>1000000);
	print '</td><td>';

	if($sp_user eq 'no'){
		print '<th>SI Mode:</th><td style="text-align:left">';
		print "$hrc_si_mode";
		print "<input type=\"hidden\" name=\"HRC_SI_MODE\" value=\"$hrc_si_mode\">";
		print '</td></tr>';
	}else{
		print '<th>SI Mode:</th>
			<td style="text-align:left"><input type="text" name="HRC_SI_MODE" value="';
		print "$hrc_si_mode";
		print '" size="8"></td></tr>';
	}

	print '</table>';
	
	print '<hr />';

#---------------------
#----- ACIS Parameters
#--------------------

	print '<h2>ACIS Parameters</h2>';
	print '<table style="border-width:0px">';
	print '<tr>';
	
	print '<th>ACIS Exposure Mode:</th><td>';
	
	print popup_menu(-name=>'EXP_MODE', -value=>['NULL','TE','CC'], -default=>"$exp_mode", -override=>100000);
	
	print '</td><th>Event TM Format:</th><td>';
	
	print popup_menu(-name=>'BEP_PACK', -value=>['F','VF','F+B','G'], 
		 	-default=>"$bep_pack", -override=>100000);
	print '</td>';


	print '<th>Frame Time:</th>';

	print "<td style='text-align:left'>";
	print textfield(-name=>'FRAME_TIME', -value=>"$frame_time",-size=>12, -override=>1000);
	print "</td></tr>";

	print '<tr>';
	print '<td>&#160;</td><td>&#160;</td><td>&#160;</td><td>&#160;</td>
		<th>Most Efficient:</th><td>';

	print popup_menu(-name=>'MOST_EFFICIENT', -value=>['NULL','YES','NO'],
		 	-default=>"$dmost_efficient", -override=>10000);
	print '</td>';
	print '</tr></table>';
	
	print '<table style="border-width:0px">';
	print '<tr><td></td>';


	print '<th>FEP:</th><td>';
              print "$fep";
	print '</td><td></td><td></td>';
	print '<th>Dropped Chip Count:</th><td>';
	print "$dropped_chip_count";

	print '</td>';
	print '</tr></table>';

	print "<input type=\"hidden\" name=\"FEP\" value=\"$fep\">";
	print "<input type=\"hidden\" name=\"DROPPED_CHIP_COUNT\" value=\"$dropped_chip_count\">";

	print '<table style="border-width:0px">';
	print '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>';
	

	print '<th>I0:</th>';
	
	print '<td>',popup_menu(-name=>'CCDI0_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
						-default=>"$dccdi0_on",-override=>100000),'</td>';

	print '<th>I1:</th>';
	
	print '<td>',popup_menu(-name=>'CCDI1_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
						-default=>"$dccdi1_on",-override=>1000000),'</td>';
	
	print '<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>';
	print '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>';
	
	print '<th>I2:</th>';
	
	print '<td>',popup_menu(-name=>'CCDI2_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
						-default=>"$dccdi2_on",-override=>100000),'</td>';

	print '<th>I3:</th>';
	
	print '<td>',popup_menu(-name=>'CCDI3_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
						-default=>"$dccdi3_on",-override=>100000),'</td>';
	
	print '<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>';
	
	print '<tr>';
	
	print '<th>S0:</th>';
	
	print '<td>',popup_menu(-name=>'CCDS0_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
						-default=>"$dccds0_on",-override=>100000),'</td>';
	
	print '<th>S1:</th>';

	print '<td>',popup_menu(-name=>'CCDS1_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
					-default=>"$dccds1_on",-override=>100000),'</td>';

	print '<th>S2:</th>';
	
	print '<td>',popup_menu(-name=>'CCDS2_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
						-default=>"$dccds2_on",-override=>10000),'</td>';

	print '<th>S3:</th>';
	
	print '<td>',popup_menu(-name=>'CCDS3_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
						-default=>"$dccds3_on",-override=>1000000),'</td>';

	print '<th>S4:</th>';
	
	print '<td>',popup_menu(-name=>'CCDS4_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
						-default=>"$dccds4_on",-override=>100000),'</td>';

	print '<th>S5:</th>';
	
	print '<td>',popup_menu(-name=>'CCDS5_ON', -value=>['NULL','YES','OPT1','OPT2','OPT3','OPT4','OPT5','NO'],
						-default=>"$dccds5_on",-override=>100000),'</td>';
	
	print '</tr></table><p>';
	
	print '<table style="border-width:0px">';
	print '<tr>';
	print '<Th>Use Subarray:</Th>';
	print '<td>';
	print popup_menu(-name=>'SUBARRAY', -value=>['NO', 'YES'],
		 	-default=>"$dsubarray", -override=>100000);
	print '</td>';
	print '<td colspan=4><strong>Please fill the next two entries, if you select YES.</strong></td>';
	print '</tr>';

	print '<tr>';
	print '<th>Start:</th>';
	print '<td style="text-align:left"><input type="text" name="SUBARRAY_START_ROW" value="',"$subarray_start_row",'" size="12"></td>';
	print '<th>Rows:</th>';
	print '<td style="text-align:left"><input type="text" name="SUBARRAY_ROW_COUNT" value="',"$subarray_row_count",'" size="12"></td>';
	print "<td>&#160;</td><td>&#160;</td>";
	print '</tr>';

	print '<tr>';
	print '<th>Duty Cycle:</th>';
	print '<td>';
	print popup_menu(-name=>'DUTY_CYCLE', -value=>['NULL','YES','NO'], 
		 	-default=>"$dduty_cycle", -override=>100000);
	print '</td>';
	print '<th colspan=4><strong>If you selected YES, please fill the next two entries</strong></th>';
	print '</tr>';

	print '<tr>';
	print '<th>Number:</th>';
	print '<td style="text-align:left"><input type="text" name="SECONDARY_EXP_COUNT" value=';
	print "\"$secondary_exp_count\"", ' size="12"></td>';
	print '<th>Tprimary:</th>';
	print '<td style="text-align:left"><input type="text" name="PRIMARY_EXP_TIME" value=';
	print "\"$primary_exp_time\"", ' size="12"></td>';
	print "<td>&#160;</td><td>&#160;</td>";
	print '</tr>';

	print ' <tr>';
	print '<th>Onchip Summing:</th><td>';
	print popup_menu(-name=>'ONCHIP_SUM', -value=>['NULL','YES','NO'], 
		 	-default=>"$donchip_sum", -override=>100000);
	print '</td>';
	print '<th>Rows:</th>';
	print '<td style="text-align:left"><input type="text" name="ONCHIP_ROW_COUNT" value=';
	print "\"$onchip_row_count\"", ' size="12"></td>';
	print '<th>Columns:</th>';
	print '<td style="text-align:left"><input type="text" name="ONCHIP_COLUMN_COUNT" value=';
	print "\"$onchip_column_count\"", ' size="12"></td>';
	print '</tr>';

	print '<tr>';
	print '<th>Energy Filter:</th><td>';
	print popup_menu(-name=>'EVENTFILTER', -value=>['NULL','YES','NO'], 
		 	-default=>"$deventfilter", -override=>100000);
	print '</td>';
	print '<th>Lowest Energy:</th>';
	print '<td style="text-align:left"><input type="text" name="EVENTFILTER_LOWER" value="';
	print "$eventfilter_lower";
	print '" size="12"></td>';
	print '<th>Energy Range:</th>';
	print '<td style="text-align:left"><input type="text" name="EVENTFILTER_HIGHER" value="';
	print "$eventfilter_higher";
	print '" size="12"></td>';
	print '</tr>';

	print '<tr> ';
	print '<th>Multiple Spectral Lines:</th>';
	print '<td style="text-align:left">';
	print popup_menu(-name=>'MULTIPLE_SPECTRAL_LINES', -value=>['NULL','NO','YES'], -default=>"$dmultiple_spectral_lines",-override=>10000);
	print '</td>';
	print '<th>Spectra Max Count:</th>';
	print '<td style="text-align:left"><input type="text" name="SPECTRA_MAX_COUNT" value="';
	print "$spectra_max_count";
	print '" size="12"></td>';
	print "<td>&#160;</td><td>&#160;</td>";
	print '</tr> ';

	print '</table>';

#------------------------------------------------
#-------- Acis Window Constraint Case starts here
#------------------------------------------------


#------------------------------------------------
#
#--- ACIS window Constraints: some values are linked to eventfilter_lower condition
#

	print '<hr />';
	print '<h2> ACIS Window Constraints</h2>';
	print '<table style="border-width:0px"><tr><th>';
	print 'Window Filter:';
	print '</th><td>';

#
#---awc_l_th: acis window constraint lowest energy indicator: if 1 it is exceeded 0.5 keV
#

	if($aciswin_no eq ''){
		$aciswin_no = 0;
	}

	if($awc_cnt eq ''){
		$awc_cnt = 1;
	}
	if($eventfilter_lower > 0.5 || $awc_l_th == 1){
		$dspwindow = 'YES';
	}

	print popup_menu(-name=>'SPWINDOW', -value=>['NULL','YES','NO'],-default=>"$dspwindow", -override=>10000);
	print '<input type="submit" name="Check" value="Update">';
	print '</td></tr></table>';

	if($dspwindow =~ /YES/i){

		print '<br />';
		$wfill = 0;

#
#--- check which CCDs are ON
#
		@open_ccd = ();				 #--- a list of ccd abled
		$ocnt     = 0;				  #--- # of ccd abled
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
		OTUER:
		if($eventfilter_lower > 0.5 || $awc_l_th == 1){
			print '<p style="color:red"><strong>';
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
			print '</strong><br />';
			print "<a href=\"$usint_http/eventfilter_answer.html\" target='_blank'>Why did this happen?</a>";
			print '</p>';

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

		print '<p style="padding-top:10px;padding-bottom:20px">';
		print 'If you want to modify the number of ranks, change Window Filter above to "YES", ';
		print 'then change the rank entry below, and press "Add Window Rank"';
		print '</p>';
		print '<strong>Rank</strong>: ';
		print '<spacer type=horizontal size=30>';
	
		print '<spacer type=horizontal size=50>';
		print submit(-name=>'Check',-value=>'     Add Window Rank     ') ;
		
		print '<p style="padding-top:20px;padding-bottom:20px">If you are changing any of following entries, make sure ';
			print 'Window Filter above is set to "YES".<br />';
		print 'Otherwise, all changes are automatically nullified ';
		print 'when you submit the changes.';
		print '</p>';
	
		if($eventfilter_lower > 0.5 || $awc_l_th == 1){
			print '<p>If you change one or more CCD from YES to NO or the other way around in ACIS Parameters section, ';
			print '<br />';
			print 'this action will affect the ranks below. After changing the CCD status, please click "Submit" button at the bottom of the page, ';
			print '<br />';
			print ' and then come back to this page ';
			print 'using "PREVIOUS PAGE" button to make the effect to take place.';
			print '</p>';
		}


		$add_extra_line = 0;
		$reduced_ccd_no = 0;
		$org_aciswin_no = $aciswin_no;
#
#--- if eventfilter lower <= 0.5 keV and window filter is set to Null, reduce all window constraints to Null state
#

		if($eventfilter_lower > 0.5 || $awc_l_th == 1){
			if($chip[$aciswin_no -1]=~ /N/i){
				$awc_cnt	= 0;
				$aciswin_no     = $chip_chk;
				$org_aciswin_no = $aciswin_no;
			}else{
				$awc_cnt	= $aciswin_no;
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
				$aciswin_id[$j]      = $aciswin_id[$j-1] +1;
				$ordr[$j]	    = $j + 1;
				$chip[$j]	    = $un_opened[$k];
				$dinclude_flag[$j]   = 'INCLUDE';
				$start_row[$j]       = 1;
				$start_column[$j]    = 1;
				$height[$j]	  = 1024;
				$width[$j]	   = 1024;
				$lower_threshold[$j] = $eventfilter_lower;
				$pha_range[$j]       = $eventfilter_higher;
				$sample[$j]	  = 1;
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
#----this line was removed: <th>Photon Inclusion</th>
#
		print '<table style="border-width:0px">';
		print '<tr><th>Ordr</th>
		<th>Chip</th>
		<th>Start Row</th>
		<th>Start Column</th>
		<th>Height</th>
		<th>Width</th>
		<th>Lowest Energy</th>
		<th>Energy Range</th>
		<th>Sample Rate</th>
		<th>&#160;</th></tr>';

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
			$tn	= 0;
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
			if($ordr[$k] == 999){
				print "<tr><td style='background-color:red'>";
			}else{
				print "<tr><td>";
			}

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

			$taciswin_id      = 'ACISWIN_ID'."$m";
			$tordr	    = 'ORDR'."$m";
			$tchip	    = 'CHIP'."$m";
			$tinclude_flag    = 'INCLUDE_FLAG'."$m";
			$tstart_row       = 'START_ROW'."$m";
			$tstart_column    = 'START_COLUMN'."$m";
			$theight	  = 'HEIGHT'."$m";
			$twidth	   = 'WIDTH'."$m";
			$tlower_threshold = 'LOWER_THRESHOLD'."$m";
			$tpha_range       = 'PHA_RANGE'."$m";
			$tsample	  = 'SAMPLE'."$m";

			if($chip[$k] !~ /N/i){
				if($lower_threshold[$k] !~ /\d/){
					$lower_threshold[$k] = $eventfilter_lower;
				}
				if($pha_range[$k] !~ /\d/){
					$pha_range[$k] = $eventfilter_higher;
				}
			}

	
			print textfield(-name=>"$tordr", -value=>"$ordr[$k]", -override=>10000, -size=>'2');
			print " </td><td>";
			print popup_menu(-name=>"$tchip",-value=>['NULL','I0','I1','I2','I3','S0','S1','S2','S3','S4','S5'],
					-default=>"$chip[$k]", -override=>10000);
			print "</td><td>";
#		       print popup_menu(-name=>"$tinclude_flag",-value=>['INCLUDE','EXCLUDE'],
#				       -default=>"$dinclude_flag[$k]", -override=>10000);
#		       print "</td><td>";
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
			print "<input type=\"hidden\" name=\"$taciswin_id\" value=\"$aciswin_id[$k]\"\>";

			print '</td></tr>';
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
			$tordr	      = 'ORDR'."$k";
			$tchip	      = 'CHIP'."$k";
#		    $tinclude_flag    = 'INCLUDE_FLAG'."$k";
			$tstart_row       = 'START_ROW'."$k";
			$tstart_column    = 'START_COLUMN'."$k";
			$theight	  = 'HEIGHT'."$k";
			$twidth	      = 'WIDTH'."$k";
			$tlower_threshold = 'LOWER_THRESHOLD'."$k";
			$tpha_range       = 'PHA_RANGE'."$k";
			$tsample	  = 'SAMPLE'."$k";

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

#-----------------------------------
#----- TOO Parameter Case start here
#-----------------------------------

	print '<hr />';
	print '<h2>TOO Parameters</h2>';
	
	print '<table style="border-width:0px">';
	print '<tr>';
	print '<th style="verticla-align:top">TOO ID:';
	print '</th><td>';
	print "$too_id",'</td>';
	print '</tr>';
	
	print '<tr>';
	print '<th style="verticla-align:top;white-space:nowrap">TOO Trigger:';
	print '</th><td>',"$too_trig",'</td>';
	print '</tr><tr>';
	print '<th>TOO Type:</th><td>';
	print "$too_type";
	print '</td></tr></table>';

	print '<table style="border-width:0px">';
	print '<tr>';
	print '<th>Exact response window (days):</th>';
	print '<td>&#160;</td><td>&#160;</td>';
	print '<td>&#160;</td>';
	print '</tr>';

	print '<tr>';
	print '<th>Start:</th><td>';
	print "$too_start";
	print '</td>';
	print '<th>Stop:</th><td>';
	print "$too_stop";
	print '</td>';
	print '</tr>';

	print '<tr>';
	print '<th>';
	print '# of Follow-up Observations:</th><td>';
	print "$too_followup";
	print '</td>';
	print '<td>&#160;</td><td>&#160;</td>';
	print '</tr></table>';

	print '<table style="border-width:0px">';
	print '<tr><td>&#160;</td>';
	print '<th style="vertical-align:top">';
	print 'TOO Remarks:</th><td>';
	print "$too_remarks";
	print '</td></tr></table>';
	
#---------------------------------->
#---- Comment and Remarks  -------->
#---------------------------------->
	
	print '<hr />';
	print '<h2>Comments and Remarks</h2>';
	print '<p style="padding-bottom:20px"><strong>The remarks area below is reserved for remarks related to constraints, ';
	print 'actions/considerations that apply to the observation. ';
	print 'Please put all other remarks/comments into the comment area below. ';
	print '</strong></p>';
	

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


	print '<table style="border-width:0px">';

	print '<tr><th style="vertical-align:top">Remarks:</th>';
#	print '<td><textarea name="REMARKS" ROWS="10" COLS="60"  WRAP=virtual >';
	print '<td><textarea name="REMARKS" ROWS="10" COLS="60">';
	print "$remarks";
	print '</textarea></td><td>&#160;</td></tr>';


	if($remark_cont ne ''){
		print '<tr><th style="vertical-align:top">Other Remark:</th><td>',"$remark_cont",'</td></tr>',"\n";
	}

	print "<tr><td colspan=3>";
	print "<strong> Comments are kept as a record of why a change was made.<br />";
	print "If a CDO approval is required, or if you have a special instruction for ARCOPS, ";
	print "add the comment in this area.</strong>";
	print "</td></tr>";
	print "<tr>";
	print "<th  style='vertical-align:top'>Comments:</th><td>";
#	print "<textarea name='COMMENTS' ROWS='3' COLS='60' WRAP=virtual>$comments</textarea>";
	print "<textarea name='COMMENTS' ROWS='3' COLS='60' >$comments</textarea>";
	print "</td><td>&#160;</td></tr>";

	print "</table>";
	print "<hr />";
	

#------------------------------------->
#---- here is submitting options ----->
#------------------------------------->


	if($mp_check > 0){
		print "<h2><strong style='color:red;padding-bottom:10px'>";

		print "Currently under review in an active OR list.";
		print "</strong></h2>";
	}

		print '<strong>OPTIONS</strong>';
		print '<table style="border-width:0px"><tr><td>';
		print '<strong>Normal Change </strong> ';
		print '</td><td>';
		print 'Any changes other than APPROVAL status';
		print '</td></tr><tr><td>';
		print '<strong>Observation is Approved for flight </strong>';
		print '</td><td>';
		print 'Adds ObsID to the Approved File - nothing else<br />';
		print '</td></tr><tr><td>';
		print '<strong>ObsID no longer ready to go </strong> ';
		print '</td><td>';
	 	print 'REMOVES ObsID from the Approved File - nothing else<br />';
		print '</td></tr>';

		print '<tr><td>';
		print '<strong>Split this ObsID </strong> ';
		print '</td> <td> ';
		print '	 	does NOT add them to the Approved File.<br />';
		print '	<span style="color:fuchsia"> Please add an explanation why you need<br /> to split this observation in the comment area.</span>';
		print '</td></tr>';

	
		print '</table>';
		
		print '<div style="text-align:center;margin-left:auto;margin-right:auto;padding-bottom:20px">';
		print '<table style="border-width:0px">';
		print '<tr>';
	
		if($asis eq 'NORM' || $asis eq ''){
			print '<td><input type="RADIO" name="ASIS" value="NORM" CHECKED><strong> Normal Change</strong>';
		}else{
			print '<td><input type="RADIO" name="ASIS" value="NORM"><strong> Normal Change</strong>';
		}
	
		if($asis eq 'ASIS'){
			print '<td><input type="RADIO" name="ASIS" value="ASIS" CHECKED><strong> Observation is Approved for flight</strong>';
		}else{
			print '<td><input type="RADIO" name="ASIS" value="ASIS"><strong> Observation is Approved for flight</strong>';
		}
	
		if($asis eq 'REMOVE'){
			print '<td><input type="RADIO" name="ASIS" value="REMOVE" CHECKED> <strong>ObsID no longer ready to go</strong>';
		}else{
			print '<td><input type="RADIO" name="ASIS" value="REMOVE"> <strong>ObsID no longer ready to go</strong>';
		}

		if($asis eq 'CLONE'){
			print '<td><input type="RADIO" name="ASIS" value="CLONE" CHECKED><strong> Split this ObsID</strong>';
		}else{
			print '<td><input type="RADIO" name="ASIS" value="CLONE"><strong> Split this ObsID</strong>';
		}
		
	
		print '</tr></table>';

		print '<input type="hidden" name="OBSID"    '," value=\"$orig_obsid\">";
		print '<input type="hidden" name="ACISID"       '," value=\"$orig_acisid\">";
		print '<input type="hidden" name="HRCID"    '," value=\"$orig_hrcid\">";
		print '<input type="hidden" name="SI_MODE"      '," value=\"$si_mode\">";
		print '<input type="hidden" name="access_ok"    '," value=\"yes\">";
		print '<input type="hidden" name="pass"     '," value=\"$pass\">";
		print '<input type="hidden" name="sp_user"      '," value=\"$sp_user\">";
		print '<input type="hidden" name="email_address"'," value=\"$email_address\">";


		print '<input type="hidden" name="USER"      value="',"$submitter",'">';
		print '<input type="hidden" name="SUBMITTER" value="',"$submitter",'">';


		print '<table style="border-width:0px">';
		print '<tr>';

		print '<td><input type="submit" name="Check"  value="Submit">';
		print '<td><input type="submit" name="Check"   value="     Update     ">';

	print '</tr>';
	print '</table>';
	print '</div>';


	print "<p style='padding-bottom:20px'><strong>";
	if($usint_on =~ /test/){
		print "If you have multiple entries to approve (as is), you can use: ";
		print "<a href='$test_http/express_signoff.cgi?$obsid'>";
		print "Express Approval Page</a>";
	}elsif($usint_on =~ /yes/){
		print "If you have multiple entries to approve (as is), you can use: ";
		print "<a href='$usint_http/express_signoff.cgi?$obsid'>";
		print "Express Approval Page</a>";
	}else{
		print "If you have multiple entries to approve (as is), you can use: ";
		print "<a href='$obs_ss_http/express_signoff.cgi?$obsid'>";
		print "Express Approval Page</a>";
	}
	print "</strong></p>";


	print '<h3>';
	print "<a href=\"$cdo_http/review_report/disp_report.cgi?";
	print "$proposal_number";
	print '">Link to peer review report and proposal</a>';
	print '</h3>';

	print "<p style='padding-top:20px'>Go to the <A HREF=\"$usint_http/search.html\">";
	print 'Chandra User Observation Search Page</A><p>  ';
}

##################################################################################
### prep_submit: preparing the data for submission                 ###
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
		elsif($roll_constraint[$j] eq '')      {$roll_constraint[$j] = 'NULL'}

		if($roll_180[$j]    eq 'NULL'){$roll_180[$j] = 'NULL'}
		elsif($roll_180[$j] eq 'NO')  {$roll_180[$j] = 'N'}
		elsif($roll_180[$j] eq 'YES') {$roll_180[$j] = 'Y'}
		elsif($roll_180[$j] eq '')    {$roll_180[$j] = 'NULL'}
	}
#-------------------
#--- aciswin cases
#-------------------

	for($j = 0; $j <= $acsiwin_no; $j++){
		if($include_flag[$j] eq 'INCLUDE'){$include_flag[$j] = 'I'}
		elsif($include_flag[$j] eq 'EXCLUDE'){$include_flag[$j] = 'E'}
	}
		
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

	@list_of_user = @special_user;

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
### chk_entry: calling entry_test to check input value range and restrictions                ###
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
			print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range. </h2>";
		}
	
		print '<table border=1>';
		print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
		foreach $ent (@out_range){
			@atemp = split(/<->/,$ent);
			$db_name = $atemp[0];
			find_name();
			print "<tr><th>$web_name ($atemp[0])</th>";
			print "<td style='color:red'>$atemp[1]</td>";
			print "<td style='color:green'>$atemp[2]</td></tr>";
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
				print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
			}
		
			print '<table border=1>';
			print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
			foreach $ent (@out_range){
				@atemp = split(/<->/,$ent);
				$db_name = $atemp[0];
				find_name();
				print "<tr><th>$web_name ($atemp[0])</th>";
				print "<td style='color:'red'>$atemp[1]</td>";
				print "<td style='green'>$atemp[2]</td></tr>";
			}
	
			if($count_ccd_on > 6){
				print "<tr><th># of CCD On</th>";
				print "<td style='color:red'>$count_ccd_on</td>";
				print "<td style='color:green'>must be less than or equal to 6</td></tr>";
			}
			print '</table>';
		}
	
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
        		print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
			}
        	print '<table border=1>';
        	print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
        	print "<tr><th>CCD Option Selection</th>";
        	print "<td style='color:red'>";
			
			$chk = $o_cnt + $no_yes;
			if($chk == 0){
				print "CCD# = NO";
			}else{
				foreach $ent ('ccdi0_on', 'ccdi1_on', 'ccdi2_on', 'ccdi3_on', 'ccds0_on', 'ccds1_on', 'ccds2_on',
					'ccds3_on', 'ccds4_on', 'ccds5_on'){
					$e_val = ${$ent};
					if($e_val =~ /^O/i){
						@atemp = split(/_on/, $ent);
						$ccd_ind = uc ($atemp[0]);
						print "$ccd_ind: $e_val<br />";
					}
				}
			}
			print "</td>";
        	print "<td style='color:green'>$line</td></tr>";
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
		}

		$time_okn = $time_ok[$j];

		foreach $name ('WINDOW_FLAG', 'TSTART.N', 'TSTOP.N', 'WINDOW_CONSTRAINT.N'){
			entry_test();			#----- check the condition
		}

		if($range_ind > 0){			# write html page about bad news
			$error_ind += $range_ind;
			if($header_chk == 0){
				print "<h2 style='color:red'> Following values are out of range.</h2>";
			}
			$header_chk++;

			print '<strong style="padding-top:10px; padding-bottom:20px">Time Order: ',"$j",'</strong>';
		
			print '<table border=1>';
			print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
				foreach $ent (@out_range){
				@atemp = split(/<->/,$ent);
				$db_name = $atemp[0];
				find_name();
				print "<tr><th>$web_name ($atemp[0])</th>";
				print "<td style='color:red'>$atemp[1]</th>";
				print "<td style='color:green'>$atemp[2]</th></tr>";
			}
			print '</table>';
		}
	}

#-------------------------
#------- roll order cases
#-------------------------

	for($j = 1; $j <= $roll_ordr; $j++){
		$range_ind = 0;
		@out_range = ();

		foreach $in_name ('ROLL_CONSTRAINT','ROLL_180','ROLL','ROLL_TOLERANCE'){
			$name = "$in_name".'.N';
			$lname = lc ($name);
			$lname2 = lc ($in_name);
			${$lname} = ${$lname2}[$j];
		}

		foreach $name ('ROLL_FLAG','ROLL_CONSTRAINT.N','ROLL_180.N','ROLL.N','ROLL_TOLERANCE.N'){
			entry_test();			#----- check the condition
		}

		if($range_ind > 0){			# write html page about bad news
			$error_ind += $range_ind;
			print '<br />';
			print '<strong>Roll Order: ',"$j",'</strong><br />';
			if($header_chk == 0){
				print "<h2 style='color:red'> Following values are out of range.</h2>";
				print '<br />';
			}
			$header_chk++;
		
			print '<table border=1>';
			print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
				foreach $ent (@out_range){
				@atemp = split(/<->/,$ent);
				$db_name = $atemp[0];
				find_name();
				print "<tr><th>$web_name ($atemp[0])</th>";
				print "<td style='color:red'>$atemp[1]</th>";
				print "<td style='color:green'>$atemp[2]</th></tr>";
			}
			print '</table>';
		}
	}


#-----------------------
#--- acis i<-->s change in ACIS Paratmer
#-----------------------

	if(($orig_instrument !~ /ACIS-I/i && $instrument =~ /ACIS-I/i && $grating =~ /N/i)
			|| ($orig_instrument =~ /ACIS-I/i && $orig_grating !~ /N/ && $instrument =~ /ACIS-I/i && $grating =~ /N/i)) {


		if($multiple_spectral_lines =~ /n/i || $spectra_max_count =~ /n/i || $spectra_max_count eq ''){

			if($header_chk == 0){
				 print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
			}

			$header_chk++;
			print '<table border=1>';
			print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
			if($multiple_spectral_lines =~ /n/i){
				print '<tr><th>Multiple Spectral Lines</th>';
				print "<td style='color:red'>$multiple_spectral_lines</td>";
				print '<td style="color:green">YES</td>';
				print '</tr>';
			}
			if($spectra_max_count =~ /n/i || $spectra_max_count eq ''){
				print '<tr><th>Spectral Max Count</th>';
				print "<td style='color:red'>$spectra_max_count</td>";
				print '<td style="color:green">1-1000000</td>';
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

		for($j = 0; $j < $aciswin_no; $j++){
			$jj = $j + 1;
			$range_ind       = 0;
			$acis_order_head = 0;
			@out_range       = ();

			$chk_pha_range   = 0;

			foreach $in_name ('ORDR', 'CHIP','INCDLUDE_FLAG','START_ROW','START_COLUMN','HEIGHT','WIDTH',
						'LOWER_THRESHOLD','PHA_RANGE','SAMPLE'){
				$name     = "$in_name".'.N';
				$lname    = lc ($name);
				$lname2   = lc ($in_name);
				${$lname} = ${$lname2}[$j];

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
			}

#
#--- added 08/04/11
#
            if($chk_pha_range > 0){
                print "<h3 style='color:fuchsia;padding-bottom:10px'> Warning: PHA_RANGE > 13:<br />";
                print "In many configurations, an Energy Range above 13 keV will risk telemetry saturation.</h3>";
            }


			if($range_ind > 0){			# write html page about bad news
				$error_ind += $range_ind;
				if($header_chk == 0){
					print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
				}
				$header_chk++;

				print '<strong style="padding-top:10px;padding-bottom:10px">Acis Window Entry: ',"$jj",'</strong>';
				$acis_order_head++;
			
				print '<table border=1>';
				print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
				foreach $ent (@out_range){
					@atemp = split(/<->/,$ent);
					$db_name = $atemp[0];
					find_name();
					print "<tr><th>$web_name ($atemp[0])</th>";
					print "<td style='color:red'>$atemp[1]</td>";
					print "<td style='color:green'>$atemp[2]/td></tr>";
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
                        print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
                    }
                    $header_chk++;

					if($do_not_repeat != 1){
                    	print '<table border=1>';
                    	print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
                    	print "<tr><th>Energy Filter Lowest Energy</th>";
                    	print "<td style='color:red'>0.5 keV </td>";
                    	print "<td style='color:green'>Spatial Window param  must be filled";
                    	print "<br />(just click PREVIOUS PAGE)</td>";
                    	print '</table>';
						$do_not_repeat = 1;
					}
                }
            }

			if(($lower_threshold[$j] < $eventfilter_lower) && ($lower_threshold[$j] ne '')){
				if($header_chk == 0){
					print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
				}
				$header_chk++;

				if($acis_order_head == 0){
					print '<strong style="padding-top:10px;padding-bottom:10px">Acis Window Entry: ',"$jj",'</strong>';
					$acis_order_head++;
				}

				print '<table border=1>';
				print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
				print "<tr><th>ACIS Lowest Threshold</th><td style='color:red'>$lower_threshold[$j]</th>";
				print "<td style='olor:green'>lower_threshold must be larger than or equal to eventfilter_lower ($eventfilter_lower)</td></tr>";
				print '</table>';
			}
			if($pha_range[$j] > $eventfilter_higher && $pha_range[$j] ne ''){
				if($header_chk == 0){
					print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
				}
				$header_chk++;

				if($acis_order_head == 0){
					print '<strong style="padding-top:10px;padding-bottom:10px">Acis Window Entry: ',"$jj",'</strong>';
					$acis_order_head++;
				}

				print '<table border1>';
				print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
				print "<tr><th>ACIS Energy Range</th><td style='color:red'>$pha_range[$j]</th>";
				print "<td style='color:green'>energy_range must be smaller than or equal to eventfilter_higher ($eventfilter_higher)</td></tr>";
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
				print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
			}
			$header_chk++;
			print '<table border=1>';
			print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
			print "<tr><th>Monitor Flag</th><td style='color:red'>$monitor_flag</th>";
			print "<td style='color:green'>A monitor_flag must be NULL or change group_id</td></tr>";
			print '</table>';

		}elsif($pre_min_lead eq '' || $pre_max_lead eq ''){
			if($header_chk == 0){
				print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
			}
			$header_chk++;
			print '<table border=1>';
			print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
			print "<tr><th>Monitor Flag</th><td style='color:red'>$monitor_flag</th>";
			print "<td style='color:green'>A monitor_flag must be NULL or add pre_min_lead and pre_max_lead</td></tr>";
			print '</table>';
		}
	}

	if($group_id){

		if($monitor_flag =~ /Y/i){
			if($header_chk == 0){
				print "<h2 style='color:red;padding-bottom:10px'>Following values are out of range.</h2>";
			}
			$header_chk++;
			print '<table border=1>';
			print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
			print "<tr><th>Group ID</th><td style='color:red'>$group_id</th>";
			print "<td style='color:green'>A group id must be NULL or change monitor_flag</td></tr>";
			print '</table>';

		}elsif($pre_min_lead eq '' || $pre_max_lead eq ''){
			if($header_chk == 0){
				print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
			}
			$header_chk++;
			print '<table border=1>';
			print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
			print "<tr><th>Group ID</th><td style='color:red'>$group_id</th>";
			print "<td style='color:green'>A group_id must be NULL or add pre_min_lead and pre_max_lead</td></tr>";
			print '</table>';
		}
	}

	if($pre_id == $obsid){

		if($header_chk == 0){
			print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
		}
		$header_chk++;
		print '<table border=1>';
		print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
		print "<tr><th>Follows ObsID#</th><td style='color=:red'>$pre_id</th>";
		print "<td style='color:green'>pre_id must be different from the ObsID of this observation ($obsid) </td></tr>";
		print '</table>';
	}

	if($pre_min_lead > $pre_max_lead){

		if($header_chk == 0){
			print "<h2 style='color:red;padding-bottom:10px'> Following values are out of range.</h2>";
		}
		$header_chk++;
		print '<table border=1>';
		print '<tr><th>Parameter</th><th>Value</th><th>Possible Values</th></tr>';
		print "<tr><th>Min Int</th><td style='color:red'>$pre_min_lead</th>";
		print "<td style='color:green'>pre_min_lead must be smaller than pre_max_lead ($pre_max_lead)</td></tr>";
		print '</table>';
	}
	print '<br /><br />';

#---------------------------------------------------------------
#----- print all paramter entries so that a user verifies input
#---------------------------------------------------------------

	submit_entry();
}

###########################################################################################################
### entry_test: check input value range and restrictions                           ####
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
		if($comp eq '+' || $comp eq '-' || $comp =~/\d/ || $comp =~ /./){
			$digit = 1;
		}else{
			$digit = 0;
			last OUTER;
		}
	}

#--------------------------------------------------------------
#----- if there any conditions, procceed to check the condtion
#--------------------------------------------------------------

	unless(${condition.$name}[0]  eq 'OPEN' || ${$uname} eq '' || ${$uname} =~/\s/){
		$rchk = 0;				# comparing the data to the value range

#--------------------------------------------
#----- for the case that the condition is CDO
#--------------------------------------------

		if(${condition.$name}[0] eq 'CDO'){
			$original = "orig_$uname";
			if(${$original} ne ${$uname}){
				@{same.$name} = @{condition.$name};
				shift @{condition.$name};
				push(@{condition.$name},'<span style="color:red">Has CDO approved this change?</span>');
				$rchk++;
#
#--- keep CDO warning
#
				$wline = "$uname is changed from $original} to  ${$uname}";
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

			if($ent eq 'NULL' || $ent eq 'CDO' || $ent eq 'DEFAULT'){
				if(${$uname} eq $ent){
					$rchk = 0;
					last OUTER;
				}
			}elsif($atemp[1] eq '+' || $atemp[1] eq '-' || $atemp[1] =~ /\d/){
				@btemp = split(/\)/, $atemp[1]);
				@data  = split(/<>/, $btemp[0]);
				if($digit == 1 && (${$uname} <  $data[0] || ${$uname} > $data[1])){
					$rchk++;
					last OUTER;
				}

#--------------------------------------------------
#---- check whether there is a special restriction
#--------------------------------------------------

			}elsif($ent eq 'REST'){		# it has a special restriction
					$rchk = 0;
			}else{

#----------------------------------------------
#---- check the case that the condition is word
#----------------------------------------------

				if($digit == 0){	# the condition is in words
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
				if(${condition.$name}[0] eq 'NULL'){
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

			$sind = 0;			
			restriction_check();		#----- sub to check an extra restriction
			if($sind >  0){
				$range_ind++;
				$line = "$name<->${$uname}<->$add";
				push(@out_range,$line);
				@{condition.$name}= @{same.$name};
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
				$duty_cycle      = 'NULL';
				$secondary_exp_count = '';
				$primary_exp_time    = '';
				$secondary_exp_time  = '';
				$onchip_sum      = 'NULL';
				$onchip_row_count    = '';
				$onchip_column_count = '';
				$eventfilter     = 'NULL';
				$eventfilter_lower   = '';
				$eventfilter_higher  = '';
				$multiple_spectral_lines = '';
				$spectra_max_count       = '';	
				$bias        = '';
				$frequency       = '';
				$bias_after      = '';
				$spwindow        = 'NULL';

				for($n = 0; $n < $aciswin_no; $n++){
					$aciswin_id[$n]      = '';
					$ordr[$n]        = '';
					$chip[$n]        = 'NULL';
					$include_flag[$n]    = 'I';
					$start_row[$n]       = '';
					$start_column[$n]    = '';
					$height[$n]      = '';
					$width[$n]       = '';
					$lower_threshold[$n] = '';
					$pha_range[$n]       = '';
					$sample[$n]      = '';
				}
#---------------------------
#---- set aciswin_no to 0
#---------------------------
				$aciswin_no = '0';;
				if($test_inst ne 'aciswin'){
					$warning_line = '';

					if($hrc_si_mode eq '' || $hrc_si_mode =~ /NULL/){
						$warning_line = 'The value for <strong>HRC_SI_MODE</strong> must be provided';
					}

					@{same.$name} = @{condition.$name};
					@{condition.$name} =("<span style='color:red'>Has CDO approved this instrument change?(all ACIS params are NULLed) <br />$warning_line </span>");
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
						$warning_line = 'The value for <strong>ACIS Winodw Filter</strong> must be provided<br />';
					}
					$test_inst = '';
				}else{
					foreach $test (EXP_MODE,BEP_PACK,MOST_EFFICIENT,CCDI0_ON,CCDI1_ON,
							CCDI2_ON,CCDI3_ON,CCDS0_ON,CCDS1_ON,CCDS2_ON,CCDS3_ON,CCDS4_ON,
							CCDS5_ON,SUBARRAY,DUTY_CYCLE){
						$ltest = lc($test);

						if(${$ltest} eq '' || ${$ltest} =~ /NULL/){
							$warning_line = "$warning_line"."The value for <strong>$test</strong> must be provided<br />";
						}
					}
				}

				@{same.$name}      = @{condition.$name};
				@{condition.$name} = ("<span style='color:red'>Has CDO approved this instrument change? (All HRC params are NULLed)<br />$warning_line</span>");
				$line          = "$name<->${$uname}<->@{condition.$name}";
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
				@{condition.$name} = ("<span style='color:red'>CDO approval is required </span>");
				$line          = "$name<->${$uname}<->@{condition.$name}";
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
				@{condition.$name} = ("<span style='color:red'>CDO approval is required </span>");
				$line          = "$name<->${$uname}<->@{condition.$name}";
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

			$diff_ra  = abs($orig_ra - $tra) * cos(abs(0.5 * ($orig_dec + $tdec)/57.2958));
			$diff_dec = abs($orig_dec - $tdec);
			$diff     = sqrt($diff_ra * $diff_ra + $diff_dec * $diff_dec);


			if($diff > 0.1333){
				@{same.$name} = @{condition.$name};
				$wline = '1) No changes can be requested until the out of range is corrected. ';
				$wline = "$wline".'please use the back button to correct out of range requests.<br />';

				$wline = "$wline".'2) If you desire CDO approval please use the Helpdesk (link) and select ';
				$wline = "$wline".'obscat changes.';

				@{condition.$name} = ("<span style='olor:red'>$wline<\/span>");

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

#-------------------------
#----- multitelescope case
#-------------------------

		if($uname =~ /^MULTITELESCOPE/i){

			if($orig_multitelescope ne $multitelescope){
				@{same.$name}      = @{condition.$name};
				@{condition.$name} = ("<span style='color:red'>CDO approval is required </span>");
				$line          = "$name<->${$uname}<->@{condition.$name}";
				push(@out_range,$line);
				@{condition.$name} = @{same.$name};
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

#------------------------
#----- observatories case
#------------------------

		if($uname =~ /^OBSERVATORIES/i){

			if($orig_observatories ne $observatories){
				@{same.$name}      = @{condition.$name};
				@{condition.$name} = ("<span style='color:red'>CDO approval is required </span>");
				$line          = "$name<->${$uname}<->@{condition.$name}";
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
						$add =  "$add"."A value for <em><strong>$web_name1 ($chname)</strong></em> is required.<br />";
						$sind++;
					}
				}elsif($btemp[0] eq 'NULL'){
					if($comp_val ne 'NULL'){
						$db_name = $name;
						find_name();
						$add = "$add"."A value for <em><strong>$web_name1 ($chname)</strong></em> must be ";
						$add = "$add"."<span style='color:magenta'>NULL</span>,<br />";
						$add = "$add"."or change the value for <em><strong>$web_name ($name)</strong></em><br />";
						$sind++;
					}
				}elsif($btemp[0] =~ /^N/i){
					if($comp_val ne 'N' && $comp_val ne 'NULL' && $comp_val ne 'NONE' && $comp_val ne 'NO'){
						$db_name = $name;
						find_name();
						$add = "$add"."A value for <em><strong>$web_name1 ($chname)</strong></em> must be ";
						$add = "$add"."<span style='color:magenta'>NULL or NO</span>,<br />";
						$add = "$add"."or change the value for <em><strong>$web_name ($name)</strong></em><br />";
						$sind++;
					}
				}else{
					if($comp_val ne $btemp[0] && $btemp[0] ne 'OPEN' && $btemp[0] ne ''){
						$db_name = $name;
						find_name();
						$add = "$add"."A value for <em><strong>$web_name1 ($chname)</strong></em> must be ";
						$add = "$add"."<span style='color:magenta'>$btemp[0]</span>,<br />";
						$add = "$add"."or change the value for <em><strong>$web_name ($name)</strong></em><br />";
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
					}elsif($btemp[0] eq 'MUST'){
						if($comp_val eq '' || $comp_val eq 'NONE' || $comp_val eq 'NULL'){
							$add = "$add"."A value for <em><strong>$web_name2 (${rest.$m.$name})</strong></em> ";
							$add = "$add"."is required.<br />";
						$sind++;
						}
					}elsif($btemp[0] =~  /^N/i){
						if($comp_val ne 'N' && $comp_val ne 'NULL' &&  $comp_val ne 'NONE'){
							$db_name = $name;
							find_name();
							$add = "$add"."A value for <em><strong>$web_name1 ($chname)</strong></em> must be ";
							$add = "$add"."<span style='color:magenta'>NULL or NO</span>,<br />";
							$add = "$add"."or change the value for <em><strong>$web_name ($name)</strong></em><br />";
							$sind++;
						}
					}else{
						$add = "$add"."A value for <em><strong>$web_name2 (${rest.$m.$name})</strong></em> ";
						$add = "$add"."must be <span style='color:magenta'>$btemp[0]</span>,<br />";
						$sind++;
					}
				}
			}
		}
	}
}


###################################################################
### read_range: read conditions                ####
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
				
			unless($ent =~ /\s/ || $ent eq ''){
				$ent = uc ($ent);
				push(@line,$ent);
			}
		}

		push(@name_array, $line[1]);	    		# name of the value

		${cndno.$line[1]} = 0;

		if($line[2] eq 'OPEN'){		 		# value range, if it is Open, just say so
			@{condition.$line[1]} = ('OPEN');
			${cndno.$line[1]}++;

		}elsif($line[2] eq 'REST'){	     		# the case which restriction attached
			@{condition.$line[1]} = ('REST');
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
### read_user_name: reading authorized user names                ###
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
### user_warning: warning a user, a user name mistake               ###
###################################################################################

sub user_warning {

	print "<div style='padding-top:20px;padding-bottom:20px'>";
	if($submitter eq ''){
		print "<strong>No user name is typed in. </strong>";
	}else{
    	print "<strong> The user: <span style='color:magenta'>$submitter</span> is not in our database. </strong>";
	}
	print "<strong> Please go back and enter a correct one (use the Back button on the browser).</strong>";
	print "</div>";

#    print "</form>";
#    print "</body>";
#    print "</html>";
}

###################################################################################
### submit_entry: check and submitting the modified input values        ###
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
	print "<input type=\"hidden\" name=\"TIME_ORDR_ADD\" value=\"$time_ordr_add\">";

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
	print "<input type=\"hidden\" name=\"ROLL_ORDR_ADD\" value=\"$roll_ordr_add\">";

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
#			      'INCLUDE_FLAG',
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
    	print FILE "USER NAME =  $submitter\n";
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
    	print FILE "PARAM NAME          ORIGINAL VALUE        REQUESTED VALUE         ";
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
					write (PARAMLINE);

					$nameagain     = 'TSTART'."$j";
					$current_entry = $tstart[$j];
					$old_value     = $orig_tstart[$j];
					write (PARAMLINE);

					$nameagain     = 'TSTOP'."$j";
					$current_entry = $tstop[$j];
					$old_value     = $orig_tstop[$j];
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
					write(PARAMLINE);

					$nameagain     = 'ROLL_180'."$j";
					$current_entry = $roll_180[$j];
					$old_value     = $orig_roll_180[$j];
					write (PARAMLINE);

					$nameagain     = 'ROLL'."$j";
					$current_entry = $roll[$j];
					$old_value     = $orig_roll[$j];
					write (PARAMLINE);

					$nameagain     = 'ROLL_TOLERANCE'."$j";
					$current_entry = $roll_tolerance[$j];
					$old_value     = $orig_roll_tolerance[$j];
					write (PARAMLINE);
				}

#--------------------------
#--- acis window order case
#--------------------------

			}elsif ($lc_name eq 'ACISWIN_ID'){
				for($j = 0; $j < $aciswin_no; $j++){
					$jj = $j + 1;
					$nameagain     = 'ORDR'."$jj";
					$current_entry = $ordr[$j];
					write(PARAMLINE);

					$nameagain     = 'CHIP'."$jj";
					$current_entry = $chip[$j];
					write(PARAMLINE);

					$nameagain     = 'INCLUDE_FLAG'."$jj";
					$current_entry = $include_flag[$j];
					write(PARAMLINE);

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
        	print "<p><strong style='color:red;padding-bottom:20px'>";
        	print "Warning, an obsid, may not be approved without an SI_mode.";
        	print 'Please contact "acisdude" or and HRC contact as appropriate';
        	print "and request they enter an SI-mode befor proceding.";
        	print "</strong></p>";
    	}else{
    			print "<p><strong>You have checked that this obsid ($obsid) is ready for flight.";
			print "  Any parameter changes you made will not be submitted with this request.</strong></p>";
		}
    	}elsif($asis eq "REMOVE") {
    	print "<p><strong>You have requested this obsid ($obsid) to be removed from the \"ready to go\" list.";
 		print " Any parameter changes you made will not be submitted with this request.</strong></p>";
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
			print "<input type=\"SUBMIT\"  name = \"Check\"  value=\"FINALIZE\">";
		}
	}
	print "<input type=\"SUBMIT\"  name = \"Check\"  value=\"PREVIOUS PAGE\">";
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
    	print FILE "USER NAME =  $submitter\n";
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
    	print FILE "PARAM NAME          ORIGINAL VALUE        REQUESTED VALUE         ";
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
					write (PARAMLINE);

					$nameagain     = 'TSTART'."$j";
					$current_entry = $tstart[$j];
					$old_value     = $orig_tstart[$j];
					write (PARAMLINE);

					$nameagain     = 'TSTOP'."$j";
					$current_entry = $tstop[$j];
					$old_value     = $orig_tstop[$j];
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
					write(PARAMLINE);

					$nameagain     = 'ROLL_180'."$j";
					$current_entry = $roll_180[$j];
					$old_value     = $orig_roll_180[$j];
					write (PARAMLINE);

					$nameagain     = 'ROLL'."$j";
					$current_entry = $roll[$j];
					$old_value     = $orig_roll[$j];
					write (PARAMLINE);

					$nameagain     = 'ROLL_TOLERANCE'."$j";
					$current_entry = $roll_tolerance[$j];
					$old_value     = $orig_roll_tolerance[$j];
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

					$nameagain     = 'INCLUDE_FLAG'."$jj";
					$current_entry = $include_flag[$j];
					write(PARAMLINE);

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

#    	print "<html>";
#    	print "<head><title>Target info for obsid : $obsid</title></head>";
#    	print "<body bgcolor=\"#FFFFFF\">";
    	print "Username = $submitter<p>";
    	print "<p><strong>You have submitted a a request for splitting obsid $obsid.  No parameter changes will";
	print "  be submitted with this request.</strong></p>";

	if($comments eq $orig_comments){
		print '<p style="padding-bottom:10px"><strong style="color:red">You need to explain why you need to split this observation.';
		print 'Plese go back and add the explanation in the comment area</strong></p>';
	}else{
		print '<table style="border-width:0px"><tr><th>Reasons for cloning:</th><td> ';
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
		print "<input type=\"SUBMIT\"  name = \"Check\"  value=\"FINALIZE\">";
	}
	print "<input type=\"SUBMIT\"  name = \"Check\"  value=\"PREVIOUS PAGE\">";
   }

    if ($asis ne "ASIS" && $asis ne "REMOVE" && $asis ne "CLONE"){

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

#	print "<html>";
#	print "<head><title>Target info for obsid : $obsid</title></head>";
#	print "<body bgcolor=\"#FFFFFF\">\n";

	print "<p style='padding-bottom:10'><strong>You have submitted the following values for obsid $obsid:</strong> </p>";

	if($error_ind == 0 || $usint_on =~ /yes/){
		print "<input type=\"SUBMIT\"  name = \"Check\"  value=\"FINALIZE\">";
	}
	print "<input type=\"SUBMIT\"  name = \"Check\"  value=\"PREVIOUS PAGE\">";
	print "<p>";
	print "Username = $submitter</p>";

#
#---- counter of number of changed paramters
#

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
						print "ENTRY $jj:<br />";

						foreach $tent ('ORDR', 'CHIP',
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
								print '<spacer type=horizontal size=15>';
								print "$tent unchanged, set to $new_value<br />";
							}else{
								print '<spacer type=horizontal size=15>';
								print "<span style='color:#FF0000'>$tent changed from $old_value to $new_value</span><br />";
								$k++; 		#telling asicwin has modified param!
							}
						}
					}

#-------------------------------
#----- checking time order case
#-------------------------------

				}elsif($name =~ /TIME_ORDR/){
					print "$name unchanged, set to $new_value<br />";

					for($j = 1; $j <= $time_ordr; $j++){
						print '<spacer type=horizontal size=5>';
						print "ORDER $j:<br />";

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
								print '<spacer type=horizontal size=15>';
								print "$tent unchanged, set to $new_value<br />";
							}else{
								print '<spacer type=horizontal size=15>';
								print "<span style='color:#FF0000'>$tent changed from $old_value to $new_value</span><br />";
								$m++;		#telling general change is ON
							}
						}
					}

#------------------------------
#----- checking roll order case
#------------------------------

				}elsif($name =~ /ROLL_ORDR/){
					print "$name unchanged, set to $new_value<br />";

					for($j = 1; $j <= $roll_ordr; $j++){
						print '<spacer type=horizontal size=5>';
						print "ORDER $j:<br />";

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
								print '<spacer type=horizontal size=15>';
								print "$tent unchanged, set to $new_value<br />";
							}else{
								print '<spacer type=horizontal size=15>';
								print "<span style='color:FF0000'>$tent changed from $old_value to $new_value</span><br />";
								$m++;		# telling general change is ON
							}
						}
					}

#----------------------
#----- all other cases
#----------------------

				}else{
					print "$name unchanged, set to $new_value<br />";
				}

#------------------------------------------------
#-------  If it is changed, print from old to new
#------------------------------------------------

			}else{

#-----------------------
#----- window order case
#-----------------------
				if($name eq 'ACISWIN_ID'){

					for($j = 0; $j < $aciswin_no; $j++){
						$jj = $j + 1;
						print '<spacer type=horizontal size=5>';
						print "ENTRY $jj:<br />";

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
								print '<spacer type=horizontal size=15>';
								print "$tent unchanged, set to $new_value<br />";
							}else{
								print '<spacer type=horizontal size=15>';
								print "<span style='color:#FF0000'>$tent changed from $old_value to $new_value</span><br />";
								$k++;		#telling aciswin param changes
							}
						}
					}

#---------------------
#----- time order case
#---------------------

				}elsif($name =~ /TIME_ORDR/){
					print "<span style='color:#FF0000'>$name changed from $old_value to $new_value</span><br />";

					for($j = 1; $j <= $time_ordr; $j++){
					print '<spacer type=horizontal size=5>';
					print "ORDER $j:<br />";

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
								print '<spacer type=horizontal size=15>';
								print "$tent unchanged, set to $new_value<br />";
							}else{
								print '<spacer type=horizontal size=15>';
								print "<span style='color:#FF0000'>$tent changed from $old_value to $new_value</span><br />";
								$m++; 			# telling general change is ON
							}
						}
					}
#---------------------
#----- roll order case
#---------------------
				}elsif($name =~ /ROLL_ORDR/){
					print "<span style='color:#FF0000'>$name changed from $old_value to $new_value</span><br />";

					for($j = 1; $j <= $roll_ordr; $j++){
					print '<spacer type=horizontal size=5>';
					print "ORDER $j:<br />";

						foreach $tent ('ROLL_CONSTRAINT', 'ROLL_180', 'ROLL','ROLL_TOLERANCE'){
							$new_entry = lc ($tent);
							$new_value = ${$new_entry}[$j];
							$old_entry = 'orig_'."$new_entry";
							$old_value = ${$old_entry}[$j];

							if($new_value eq $old_value){
								print '<spacer type=horizontal size=15>';
								print "$tent unchanged, set to $new_value<br />";
							}else{
								print '<spacer type=horizontal size=15>';
								print "<span style='color:#FF0000'>$tent changed from $old_value to $new_value</span><br />";
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
						
						print "<span style='color:lime'>$name changed from $old_value to $new_value</span><br />";
					}else{
						print "<span style='color:#FF0000'>$name changed from $old_value to $new_value</span><br />";
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

#--------------------------------
#----- check remarks and comment
#--------------------------------

	$tremarks      = $remarks;
	$tremarks      =~ s/\s+//g;
	$torig_remarks = $orig_remarks;
	$torig_remarks =~ s/\s+//g;
	
	if($tremarks ne $torig_remarks){
		print "<span style='color:#FF0000'>REMARKS changed from<br /> $orig_remarks<br /> to<br /> $remarks</sapn><br /><br />";
		$m++;			# remark is a part of general change
		$cnt_modified++;
	} else {
		print "REMARKS unchanged, set to $remarks<br />";
	}

	$tcomments      = $comments;
	$tcomments      =~ s/\s+//g;
	$torig_comments = $orig_comments;
	$torig_comments =~ s/\s+//g;

	if ($tcomments ne $torig_comments){
		$cnt_modified++;

		print "<span style='color:#FF0000'>COMMENTS changed from<br /> $orig_comments";
		print"<br />to<br />";
		print "$comments<br /></span>";
	} else {
		print "COMMENTS unchanged, set to $comments<br />";
	}

	print "<br />";
	if($wrong_si == 0){
		print "<strong>If these values are correct, click the FINALIZE button.<br />";
		print "Otherwise, use the previous page button to edit.</strong><br />";
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
	if($orig_grating	 ne $grating)    {$si_mode = 'NULL'}
	if($orig_instrument      ne $instrument)     {$si_mode = 'NULL'}
	if($orig_dither_flag     ne $dither_flag)    {$si_mode = 'NULL'}

	if($orig_si_mode ne $si_mode){ $sitag = 'ON'}
	if($instrument =~ /HRC/i){
		if($orig_hrc_config ne $hrc_config){$sitag = 'ON'}
		if($orig_hrc_zero_block ne $hrc_zero_block){$sitag = 'ON'}
	}


	if ($k > 0){
		$acistag    = "ON";
	}
	if ($l > 0){
		$aciswintag = "ON";
	}
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

#---------------------------------
#--------------- print email form
#---------------------------------

	open (FILE, ">$temp_dir/$obsid.$sf");
	print FILE "OBSID    = $obsid\n";
	print FILE "SEQNUM   = $orig_seq_nbr\n";
	print FILE "TARGET   = $orig_targname\n";
	print FILE "USER NAME =  $submitter\n";

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
			|| ($name eq 'ASIS')){

			$a     = 0;
			$aw    = 0;
			$g     = 0;
			$new_entry = lc($name);
			$new_value = ${$new_entry};
			$old_entry = 'orig_'."$new_entry";
			$old_value = ${$old_entry};
			$test1     = $new_value;
			$test2     = $old_value;
			$test1     =~ s/\s+//g;
			$test2     =~ s/\s+//g;

#-------------------------------------
#---if it is acis param, put it aside
#-------------------------------------

			unless ($test1 eq $test2){
				foreach $param3 (@acisarray){
					if ($name eq $param3){
						$aline = "$name changed from $old_value to $new_value\n";
						push(@alines,$aline);
						$a++;
					}
				}
				if ($a == 0){
					print FILE "$name changed from $old_value to $new_value\n";
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
						print FILE  "$tent changed from $old_value to $new_value\n";
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
						print FILE "$tent changed from $old_value to $new_value\n";
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
				print FILE "$name changed from $orig_ra to $ra\n";
			}   
		}
		if ($name eq "DEC"){
			$dec = sprintf("%3.6f",$dec);
			unless ($dec == $orig_dec){
				$dec = "$dec";
				$orig_dec = "$orig_ddec";
				print FILE "$name changed from $orig_dec to $dec\n";
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
		foreach $tent ('ORDR', 'CHIP',
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
				print FILE "$tent changed from $old_value to $new_value\n";
			}
		}
	}

    	print FILE "\n------------------------------------------------------------------------------------------\n";
    	print FILE "Below is a full listing of obscat parameter values at the time of submission,\nas well as new";
	print FILE " values submitted from the form.  If there is no value in column 3,\nthen this is an unchangable";
	print FILE " parameter on the form.\nNote that new RA and Dec will be slightly off due to rounding errors in";
	print FILE " double conversion.\n\n";
    	print FILE "PARAM NAME          ORIGINAL VALUE        REQUESTED VALUE         ";
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
					write (PARAMLINE);

					$nameagain     = 'TSTART'."$j";
					$current_entry = $tstart[$j];
					$old_value     = $orig_tstart[$j];
					write (PARAMLINE);

					$nameagain     = 'TSTOP'."$j";
					$current_entry = $tstop[$j];
					$old_value     = $orig_tstop[$j];
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
					write(PARAMLINE);

					$nameagain     = 'ROLL_180'."$j";
					$current_entry = $roll_180[$j];
					$old_value     = $orig_roll_180[$j];
					write (PARAMLINE);

					$nameagain     = 'ROLL'."$j";
					$current_entry = $roll[$j];
					$old_value     = $orig_roll[$j];
					write (PARAMLINE);

					$nameagain     = 'ROLL_TOLERANCE'."$j";
					$current_entry = $roll_tolerance[$j];
					$old_value     = $orig_roll_tolerance[$j];
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
					write(PARAMLINE);

					$nameagain     = 'CHIP'."$jj";
					$current_entry = $chip[$j];
					$old_value     = $orig_chip[$j];
					write(PARAMLINE);

					$nameagain     = 'INCLUDE_FLAG'."$jj";
					$current_entry = $include_flag[$j];
					$old_value     = $orig_include_flag[$j];
					write(PARAMLINE);

					$nameagain     = 'START_ROW'."$jj";
					$current_entry = $start_row[$j];
					$old_value     = $orig_start_row[$j];
					write(PARAMLINE);

					$nameagain     = 'START_COLUMN'."$jj";
					$current_entry = $start_column[$j];
					$old_value     = $orig_start_column[$j];
					write(PARAMLINE);

					$nameagain     = 'HEIGHT'."$jj";
					$current_entry = $height[$j];
					$old_value     = $orig_height[$j];
					write(PARAMLINE);

					$nameagain     = 'WIDTH'."$jj";
					$current_entry = $width[$j];
					$old_value     = $orig_width[$j];
					write(PARAMLINE);

					$nameagain     = 'LOWER_THRESHOLD'."$jj";
					$current_entry = $lower_threshold[$j];
					$old_value     = $orig_lower_threshold[$j];
					write(PARAMLINE);

					$nameagain     = 'PHA_RANGE'."$jj";
					$current_entry = $pha_range[$j];
					$old_value     = $orig_pha_range[$j];
					write(PARAMLINE);

					$nameagain     = 'SAMPLE'."$jj";
					$current_entry = $sample[$j];
					$old_value     = $orig_sample[$j];
					write(PARAMLINE);
				}
    		}elsif($lc_name =~ /\w/){
        		$current_entry = ${$lc_name};
    			write (PARAMLINE);
    		}else{
        		$current_entry = ${$old_name};
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
    }						#------ end of General case
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
				$test1 =~ s/\s+//g;
				$test2 =~ s/\s+//g;

				if($test1 ne $test2){
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
							print FILE "\tEntry  $jj   $tent $old_value\:\:$new_value\n";
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


	$test = `ls $temp_dir/*`;           #--- testing whether the data actually exits.

	if($test =~ /$obsid.$sf/){
    	oredit_sub();
	}

#----------------------------------------------
#----  if it hasn't died yet, then close nicely
#----------------------------------------------

    print "<p><strong>Thank you.  Your request has been submitted.";
    print "Approvals occur immediately, changes may take 48 hours. </strong></p>";


	if($usint_on =~ /test/){
		print "<A HREF=\"$obs_ss_http/search.html\">Go Back to the Search Page</A>";
	}else{
		print "<A HREF=\"https://cxc.cfa.harvard.edu/cgi-bin/target_search/search.html\">Go Back to Search  Page</a>";
	}

#	print "</body>";
#	print "</html>";
}

#####################################################################################
### mod_time_format: convert and devide input data format             ###
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
		$hr_add       = 12;
		@tatemp       = split(/PM/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}elsif($tentry[$ttcnt-1] =~/pm/){
		$hr_add       = 12;
		@tatemp       = split(/pm/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}elsif($tentry[$ttcnt-1] =~ /AM/){
		@tatemp       = split(/AM/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}elsif($tentry[$ttcnt-1] =~ /am/){
		@tatemp       = split(/AM/, $tentry[$ttcnt-1]);
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
### lts_date_check:   check ltd_date is in 30 days or not        ####
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
### series_rev: getting mointoring observation things       ####
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
### series_fwd: getting monitoring observation things       ####
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
### find_planned_roll: get planned roll from mp web page      ####
######################################################################

sub find_planned_roll{

    open(PFH, "$obs_ss/mp_long_term");
    OUTER:
    while(<PFH>){
		chomp $_;
		@ptemp = split(/:/, $_);
    	%{planned_roll.$ptemp[0]} = (planned_roll =>["$ptemp[1]"]);

    }
    close(PFH);
}

#####################################################################
### rm_from_approved_list: remove entry from approved list    ###
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
### send_mail_to_usint: sending out full support request email to USINT        ###
######################################################################################

sub send_mail_to_usint{

#
#--- send email to USINT 
#

	mail_out_to_usint();

#
#----  say thank you to submit email to USINT.
#

    print "<p style='padding-top:20px;padding-bottom:20px'><strong>Thank you.  Your request has been submitted.<br /><br />";
	print "If you have any quesitons, please contact: <a href=\"mailto:$usint_mail\">$usint_mail</a>.</strong></p>";

    if($usint_on =~ /test/){
        print "<A HREF=\"$obs_ss_http/search.html\">Go Back to the Search Page</A>";
    }else{
        print "<A HREF=\"$chandra_http\">Chandra Observatory Page</a>";
    }
#    print "</body>";
#    print "</html>";
}

#####################################################################################
### mail_out_to_usint: sending email to USINT                     ###
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
###send_email_to_mp: sending email to MP if the obs is in an active OR list     ###
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
		system("cat $temp_file | mailx -s\"Subject:TEST!! Change to Obsid $obsid Which Is in Active OR List ($mp_email)\n\" $test_email");
	}else{
		system("cat $temp_file | mailx -s\"Subject: Change to Obsid $obsid Which Is in Active OR List\n\"  $mp_email cus\@head.cfa.harvard.edu");
	}

	system("rm $temp_file");

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
### oredit_sub: external part of oredit; a part ocatdata2html.cgi        ###
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
#---- closed: no directory exists any more 2/28/2011
#
#    		open (ARNOLDUPDATE, ">>/home/arcops/ocatMods/acis");
#    		print ARNOLDUPDATE "$arnoldline";
#    		close (ARNOLDUPDATE);
	}


#---------------------------#
#----  send messages  ------#
#---------------------------#


	if($asis_ind =~ /ASIS/i){

		if($sp_user eq 'no'){
			open(ASIS, ">$temp_dir/asis.$sf");
			print ASIS "$obsid is approved for flight. Thank you \n";
			close(ASIS);

			if($usint_on =~ /test/){
				system("cat $temp_dir/asis.$sf |mailx -s\"Subject:TEST!!  $obsid is approved\n\" $test_email");
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
				system("cat $temp_dir/user.$sf |mailx -s\"Subject:TEST!!  Parameter Changes log  $obsid.$rev\n\"  $test_email");
			}else{
				system("cat $temp_dir/user.$sf |mailx -s\"Subject: Parameter Changes log  $obsid.$rev\n\"  -c$cus_email $email_address");
			}
			system("rm $temp_dir/user.$sf");
		}else{
			if($usint_on =~ /test/){
				system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject:TEST!! Parameter Changes log  $obsid.$rev\n\" $test_email");
			}else{
				system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes log  $obsid.$rev\n\" -c$cus_email  $email_address");
			}
		}

		if($usint_on =~ /test/){
			system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject:TEST!! Parameter Changes log  $obsid.$rev\n\" $test_email");
		}else{
			system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes log  $obsid.$rev\n\" $cus_email");
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

#	system("chmod 777 $temp_dir/*");

    system("chmod 775 $ocat_dir/updates_table.list*");
}


##################################################################################
### adjust_o_values: adjust output letter values to a correct one              ###
##################################################################################

sub adjust_o_values{

    $orig_name = 'orig_'."$d_name";            #--- original value is kept here

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


