#!/usr/bin/env /usr/bin/perl

BEGIN
{
#    $ENV{SYBASE} = "/soft/SYBASE_OCS15.5";
    $ENV{SYBASE} = "/soft/SYBASE15.7";
}

use DBI;
use DBD::Sybase;
use CGI qw/:standard :netscape /;

use Fcntl qw(:flock SEEK_END); # Import LOCK_* constants

#########################################################################################
#											#
# orupdate.cgi: display target paramter update status form page				#
#											#
# R. Kilgard, Jan 30/31 2000								#
# This script generates a dynamic webpage for keeping track of updates to		#
# target parameters.									#
#											#
# T. Isobe (isobe@cfa.harvard.edu) Aug 20, 2003						#
# added password check function. This distinguish normal users and special users 	#
# (who are usually GOT owers). The special users can sign off only their own data	#
#											#
# T. Isobe Mar 23, 2004									#
# added a new email send out for si mode sign off					#
#											#
#											#
# T. Isobe Nov 01. 2004									#
# updated email problem ( http@... was replaced by cus@... etc)				#
#											#
# T. Isobe Nov 18, 2004									#
# changed a temporary writing space to /data/mta4/www/CUs/Usint/Temp			#
#											#
# T. Isobe Jul 27, 2006									#
# cleaning up the script.								#
#											#
# T. Isobe Sep 20, 2006									#
# add comment check 									#
#											#
# T. Isobe Sep 27, 2006									#
# add large coordinate shift warning							#
#											#
#											#
# T. Isobe Feb 27, 2006									#
# change a path to the main CUS page							#
#											#
# T. Isobe Dec 08, 2008									#
# add TOO/DDT notification								#
#											#
# T. Isobe Aug 26, 2009									#
# https://icxc.harvard.edu/mta/CUS/ ---> https://icxc.harvard.edu/cus/index.html 	#
#											#
# T. Isobe Oct 09, 2009									#
#   mailx function input format modified						#
#											#
# T. Isobe Nov 12, 2009									#
#   increased efficiency								#
#											#
# T. Isobe Dec 17, 2009									#
#   added multiple entry indicator etc							#
#											#
# T. Isobe Dec 29, 2009									#
#   added a function to percolate up the user's obsids to the top			#
#											#
# T. Isobe May 26, 2010									#
#    cosmetic change									#
#											#
# T. Isobe Feb 25, 2011									#
#    directories are now read froma file kept in Info					#
#											#
# T. Isobe Aug 31, 2011									#
#     DDT/TOO final sign off request email notification added				#
#											#
# T. Isobe Nov 17, 2011									#
#    sign off problem fixed (line1441)							#
#											#
# T. Isobe Oct 01, 2012									#
#    sccs is replaced by flock								#
#											#
# T. Isobe Nov 06, 2012									#
#    html 5 conformed									#
#											#
# T. Isobe Nov 28, 2012									#
#    flock bug fixed									#
#											#
# T. Isobe Mar 27, 2013									#
#    linux transition and https://icxc ---> https://cxc					#
#                                           #
# T. Isobe Jun 27, 2013                     #
#    mailx's "-r" option removed
#
# T. Isobe Oct  7, 2013									#
#    end_body cgi system function commented out						#
#											#
# T. Isobe Sep 23, 2014									#
#    sybase update (/soft/SYBASE15.7)							#
#
# T. Isobe Apr 24, 2015
# /soft/ascds/DS.release/ots/bin/perl ---> /usr/bin/perl (make accessible from cxc)
#
# T. Isobe Oct 17, 2016
# archive access user changed from borwer to mtaops_internal/public
#											#
#########################################################################################

#print "Content-type: text/html\n\n";	# start html setting

###############################################################################
#---- before running this script, make sure the following settings are correct.
###############################################################################

#
#---- if this is usint version, set the following param to 'yes', otherwise 'no'
#

$usint_on = 'yes';                     ##### USINT Version
#$usint_on = 'no';                      ##### USER Version
#$usint_on = 'test_yes';                 ##### Test Version USINT
#$usint_on = 'test_no';                 ##### Test Version USER

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

if($usint_on =~ /test/i){
        $ocat_dir = $test_dir;
}else{
        $ocat_dir = $real_dir;
}

#
#--- set html pages
#

$usint_http   = 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/';      #--- web site for usint users
#$main_http    = 'https://cxc.cfa.harvard.edu/mta/CUS/';            #--- USINT page
$main_http    = 'https://cxc.cfa.harvard.edu/cus/index.html';      #--- USINT page
$obs_ss_http  = 'https://cxc.cfa.harvard.edu/cgi-bin/obs_ss/';     #--- web site for none usint users (GO Expert etc)
$test_http    = 'http://asc.harvard.edu/cgi-gen/mta/Obscat/';   #--- web site for test

############################
#----- end of settings
############################

#---------------------------------------------------------------------
# ----- here are non CXC GTOs who have an access to data modification.
#---------------------------------------------------------------------

@special_user = ("$test_user", 'mta');
$no_sp_user   = 2;


if($usint_on =~ /yes/){
        open(FH, "$pass_dir/usint_users");
        while(<FH>){
                chomp $_;
                @atemp = split(//, $_);
                if($atemp[0] ne '#'){
                        @btemp = split(/\s+/,$_);
                        push(@special_user,  $btemp[0]);
                        push(@special_email, $btemp[1]);
                }
        }
}

#------------------------------
#---- read a user-password list
#------------------------------

open(FH, "<$pass_dir/.htpasswd");

%pwd_list = ();				# save the user-password list
while(<FH>) {
        chomp $_;
        @passwd                 = split(/:/, $_);
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

$ac_user  = cookie('ac_user');
$password = cookie('password');

#-------------------
#--- de code cookies
#-------------------
foreach $char (@Cookie_Decode_Chars) {
        $ac_user   =~ s/$char/$Cookie_Decode_Chars{$char}/g;
        $password  =~ s/$char/$Cookie_Decode_Chars{$char}/g;
}

#-----------------------------------------------
#---- find out whether there are param passed on
#-----------------------------------------------

$ac_user  = param('ac_user')   || $ac_user;
$password = param('password')  || $pass_word;

#-------------------
#--- refresh cookies
#-------------------

$en_ac_user   = $ac_user;
$en_pass_word = $password;

foreach $char (@Cookie_Encode_Chars) {
        $en_ac_user   =~ s/$char/$Cookie_Encode_Chars{$char}/g;
        $en_pass_word =~ s/$char/$Cookie_Encode_Chars{$char}/g;
}

$user_cookie = cookie(-name    =>'ac_user',
                      -value   =>"$en_ac_user",
                      -path    =>'/',
                      -expires => '+8h');
$pass_cookie = cookie(-name    =>'password',
                      -value   =>"$en_pass_word",
                      -path    =>'/',
                      -expires => '+8h');

#-------------------------
#---- new cookies worte in
#-------------------------

print header(-cookie=>[$user_cookie, $pass_cookie], -type => 'text/html; charset=utf-8');

print "<!DOCTYPE html>";
print "<html>";
print "<head>";
print "<title>Target Parameter Update Status Form</title>";
print "<style  type='text/css'>";
print "table{text-align:center;margin-left:auto;margin-right:auto;border-style:solid;border-spacing:8px;border-width:2px;border-collapse:separate}";
print "a:link {color:blue;}";
print "a:visited {color:teal;}";
print "</style>";


#
#--- descriptions for (Dec 16, 2009 changes)
#

print <<ENDOFHTML;
<script>
<!-- hide me

	var text = '<p style="text-align:justify; padding-right:4em"><b>Changes are separated into <em>General</em> ' 
	 + 'and <em>ACIS categories</em> in the ascii <em>OBSID.revision</em> file.  All changes in each category '
	 + 'should be completed before "signing" the form. 11974.002 is an example of the current format.</b></p> ' 
	 + '<p style="text-align:justify; padding-right:4em"><b>When "signing" a box, it is only necessary to '
	 + 'enter your username. The date is appended automatically.</b></p>'
	 + '<ol style="text-align:justify;margin-left:2em; margin-right:7em;">'
	 + '<li style="padding-bottom:1em"> Different revisions of the same obsid are indicated by the same color marker '
	 + 'on the "OBSID.revision" column.</li>'
	 + '<li style="padding-bottom:1em"> If "<font color=#D2691E>Multiple Revisions Open</font>" is listed in the "Note column" '
	 + '- that particular obsid has multiple revision entries on the table which have not been signed off. Please close '
	 + 'all earlier revisions before closing the latest one.</li>'
	 + '<li style="padding-bottom:1em"> If "<font color=#4B0082>Higher Rev # Was Already Signed Off</font>" is listed '
	 + 'in the "Note column"  - that particular obsid has had a newer entry than entries listed on the table, signed off. '
	 + 'Please close all versions of the obsid on the table, as the newest one (which was already signed off) supersedes '
	 + 'all revisions listed.</li>'
	 + '<li style="padding-bottom:1em"> If you are the owner of the entry - you can sign off all these out-of-date entries '
	 + 'just signing in "Verified by" column, even if general obscat, ACIS obscat, or SI Mode edits columns are not signed '
	 + 'off yet.  Any of the unsigned column entries will be recorded as "N/A" in the database.</li>'
	 + '<li style="padding-bottom:1em"> There is a new button "Regroup by Obsids" on the right top corner of the table. '
	 + 'This rearranges the table so that all entries are regrouped by obsids, and makes it easy to see all open revisions '
	 + 'for an obsid. You can go back to (reversed) time ordered table by clicking "Arranged by Submitted Time" button '
	 + '(when you are on Obsid grouped table). </li>'
	 + '<li style="padding-bottom:1em">If you are a submitter, type your ID in the "Your User ID" box, and click "Submit" '
	 + '(or Regrouping button). It will percolate up all your obsids to the top of the list. </li>'
	 + '</ol>'

function WindowOpen(){

        var new_window =
                window.open("","name","height=600,width=800,scrollbars=yes,resizable=yes","true");

        new_window.document.writeln('<html><head><title>Description</title></head><body>');
        new_window.document.write(text);
        new_window.document.writeln('</body></html>');
        new_window.document.close();
        new_window.focus();

}

//show me  -->
</script>

ENDOFHTML

print "</head>";

print "<body style='color:#000000;background-color:#FFFFE0'>";


#-------------------
#--- starting a form
#-------------------

print start_form();


#------------------------------------
#---- check inputed user and password
#------------------------------------

if($usint_on =~ /yes/){
	$pass = 'yes';
}else{
	match_user();			# this sub match a user to a password
}

#--------------------------------------------------------------
#--------- if a user and a password do not match ask to re-type
#--------------------------------------------------------------

if($pass eq '' || $pass eq 'no'){
	if(($pass eq 'no') && ($ac_user  ne ''|| $pass_word ne '')){
		print "<p style='color:red;padding-bottom:20px'>Name and/or Password are not valid.";
		print " Please try again.</p>";
	}
	password_check();	# this one create password input page

}elsif($pass eq 'yes'){		# ok a user and a password matched

	$sp_user = 'no';

#-------------------------------------------
#------ check whether s/he is a special user
#-------------------------------------------

	if($usint_on =~ /yes/){
		$sp_user = 'yes';
	}else{
		special_user();
	}
	
#-------------------------------------------------------
#----- go to the main part to print a verification page
#----- check whether there are any changes, if there are
#----- go into update_info sub to update the table
#-------------------------------------------------------

	$ap_cnt     = param('ap_cnt');
	@name_list  = ();
	@value_list = ();
	$chk_cnt    = 0;
	for($k = 0; $k < $ap_cnt; $k++){
		$name  = param("pass_name.$k");
		$value = param("$name");
		push(@name_list,  $name);
		push(@value_list, $value);
		if($value =~ /\w/){
			$chk_cnt++;
		}
	}
	if($chk_cnt > 0){
		update_info();		# this sub update updates_table.list
	}

	orupdate_main();		# this sub creates and displays a html page

}else{
	print '<p>Something wrong. Exiting.</p>';
	exit(1);
}

print end_form();
#print end_body();
print end_html();


#########################################################################
### password_check: open a user - a password input page               ###
#########################################################################

sub password_check{
	print '<h3>Please type your user name and password</h3>';
	print '<table style="border-width:0px"><tr><th>Name</th><td>';
	print textfield(-name=>'ac_user', -value=>'', -size=>20);
	print '</td></tr><tr><th>Password</th><td>';
	print password_field( -name=>'password', -value=>'', -size=>20);
	print '</td></tr></table><br />';
	
	print '<input type="submit" name="Check" value="Submit">';
}


#########################################################################
### match_user: check a user and a password matches                   ###
#########################################################################

sub match_user{
	$ac_user   = param('ac_user');
	$ac_user   =~ s/^\s+//g; 
	$pass_word = param('password');
	$pass_word =~ s/^\s+//g;

	OUTER:
	foreach $test_name (@user_name_list){
		$ppwd  = $pwd_list{"$ac_user"};
		$ptest = crypt("$pass_word","$ppwd");

		if(($ac_user eq $test_name) && ($ptest  eq $ppwd)){
			$pass_status = 'match';
			last OUTER;
		}
	}

	if($pass_status eq 'match'){
		$pass = 'yes';
	}else{
		$pass = 'no';
	}
}


#########################################################################
### special_user: check whether the user is a special user            ###
#########################################################################

sub special_user{
	$sp_user = 'no';
	OUTER:
	foreach $comp (@special_user){
		$user = lc ($ac_user);
		if($ac_user eq $comp){
			$sp_user = 'yes';
			last OUTER;
		}
	}
}

#########################################################################
### pi_check: check whether pi has an access to the data              ###
#########################################################################

sub pi_check{
	$user_i = 0;
	$luser  = lc($ac_user);
	$luser  =~ s/\s+//g;

        open(FH, "$pass_dir/user_email_list");
        while(<FH>){
                chomp $_;
                @atemp = split(/\s+/, $_);
		if($luser eq $atemp[2]){
			$usr_last_name     = $atemp[0];
			$usr_first_name    = $atemp[1];
			$usr_email_address = $atemp[3];
		}
        }
        close(FH);

	open(FH, "$obs_ss/access_list");
	@user_data_list = ();
	while(<FH>){
		chomp $_;
		@dtemp = split(/\s+/, $_);
		@etemp = split(/:/,$dtemp[3]);
		@ftemp = split(/:/,$dtemp[4]);

		if(($usr_last_name eq $etemp[0] && $usr_first_name eq $etemp[1])
			 || ($usr_last_name eq $ftemp[0] && $usr_first_name eq $ftemp[1])){
			push(@user_data_list, $dtemp[0]);
		}
	}
	close(FH);
}

#########################################################################
### get_database_values: get a few database values for checking       ###
#########################################################################

sub get_database_values {

#----------------------------------------------------------------------
#----- to access sybase, we need to set user password and a server name
#----------------------------------------------------------------------

#	$db_user   = "browser";
#	$db_passwd =`cat $pass_dir/.targpass`;

    $web = $ENV{'HTTP_REFERER'};
    if($web =~ /icxc/){
        $db_user   = "mtaops_internal_web";
        $db_passwd =`cat $pass_dir/.targpass_internal`;
    }else{
        $db_user = "mtaops_public_web";
        $db_passwd =`cat $pass_dir/.targpass_public`;
    }

	$server    = "ocatsqlsrv";
	chop $db_passwd;

#--------------------------------------
#-------- open connection to sql server
#--------------------------------------

	my $db = "server=$server;database=axafocat";
	$dsn1  = "DBI:Sybase:$db";
	$dbh1  = DBI->connect($dsn1, $db_user, $db_passwd, { PrintError => 0, RaiseError => 1});

#----------------------------------------------
#-----------  get proposal_id from target table
#----------------------------------------------


	$sqlh1 = $dbh1->prepare(qq(select
			type,pre_id  
	from target where obsid=$obsid));
	$sqlh1->execute();
	@targetdata = $sqlh1->fetchrow_array;
	$sqlh1->finish;

	$too_id = $targetdata[0];
	$pre_id = $targetdata[1];
	
	$too_id =~ s/\s+//g;
	$pre_id =~ s/\s+//g;

#--------------------------------------------------------------------
#---- if it is a TOO/DDT observation, mark it for a speical treatment
#--------------------------------------------------------------------

	$too_chk = 0;
	$ddt_chk = 0;
	if($too_id =~ /TOO/i && ($pre_id eq '' || $pre_id !~ /\d/)){
		$too_chk = 1;
	}
	if($too_id =~ /DDT/i && ($pre_id eq '' || $pre_id !~ /\d/)){
		$ddt_chk = 1;
	}
}


###############################################################################################
### orupdate_main: printing a verification page                                             ###
###############################################################################################

##########################################################################
#
#----- this sub is adapted from Kilgard's original orupdate.cgi.
# R. Kilgard, Jan 30/31 2000
# This script generates a dynamic webpage for keeping track of updates to
# target parameters.  
###########################################################################

sub orupdate_main{

#---------------------------------------------------------------------------
#----- this color table will be used to indicated multiple revision entries
#---------------------------------------------------------------------------

@color_table = ('#E6E6FA', '#F5F5DC', '#FFDAB9', '#90EE90', '#BDB76B', '#DDA0DD', '#808000',
		'#FF69B4', '#9ACD32', '#6A5ACD', '#228B22');

$cj      = 0;		#--- counter for the color table 0 - 10.

#-------------------------------------------
#----- a couple of hidden parameters to pass
#-------------------------------------------

	print hidden(-name=>'ac_user',  -value=>"$ac_user");
	print hidden(-name=>'password', -value=>"$password");


#
#--- read CDO warning list--- only large coordinate shift case recorded
#
	open(IN, "$ocat_dir/cdo_warning_list");
	@cdo_warning_list = ();
	while(<IN>){
		chomp $_;
		push(@cdo_warning_list, $_);
	}
	close(IN);
#
#--- reverse the list so that the entry can read the most recently entered item first.
#
	@reversed         = reverse (@cdo_warning_list);
	@cdo_warning_list = @reversed;

#------------------------------------------------------------------------------------------
#----@pass_list will hold all editable entries so that we can pass them as parameters later
#------------------------------------------------------------------------------------------

	@pass_list = ();

	print "<h1>Target Parameter Update Status Form</h1>";

	print "<p style='text-align:justify; padding-right:4em'><strong>";
	print "This form contains all requested updates which have either not been verified or ";
	print "have been verified in the last 24 hours.</strong></p>";


	print '<p><a href="#" onClick="WindowOpen(text);return false;"><strong>More Explanation.</strong></a></p>';


	print "<p style='text-align:justify; padding-right:4em;padding-bottom:20px'><strong>";
	print "If you need to remove an accidental submission, please go to ";

	if($usint_on =~ /test/i){
		print "<a href=\"$test_http/rm_submission.cgi/\">Remove An Accidental Submission Page</a>.";
	}else{
		print "<a href=\"$usint_http/rm_submission.cgi/\">Remove An Accidental Submission Page</a>.";
	}
	print '</strong></p>';
		
###	print " If the row is highlighted with yellow, it is a user input</b><p>";

	print '<table style="border-width:0px">';
	print '<tr>';
	print '<td style="text-align:left;width:40%">';
	if($usint_on =~ /no/){
		print "<strong><a href=\"$obs_ss_http/index.html\">Verification Page</a></strong> ";
	}else{
#		print "Support Observation Search Form</a></b><br />";
		print "<strong><a href=\"$main_http\">Go To Chandra Uplink Support Organizational Page</a></strong>";
	}
	print '</td>';
	print '<td style="text-align:right;width:40%">';

#-------------------------------------------------------------------------------------------------------------
#---- a button to rearrnage the entries. one is by obsid, and the other is by (reversed) submitted time order
#-------------------------------------------------------------------------------------------------------------

	$userid=param('userid');
	print "Your User ID:<input type=\"text\" size='6' name ='userid' value=\"$userid\">";
	print "<input type=\"submit\" value=\"Submit\">"; 

	$reorder = param('reorder');
	$userid  = param('userid');
	if($reorder eq '' || $reorder eq 'Arrange by Submitted Time'){
		print "<input type=\"submit\" name ='reorder' value=\"Regroup by Obsids\">"; 
	}elsif($reorder eq 'Regroup by Obsids'){
		print "<input type=\"submit\" name ='reorder' value=\"Arrange by Submitted Time\">"; 
	}

	print '</td>';
	print '</table>';

	print hidden(-name=>"reorder", -value=>"$reorder");
	print hidden(-name=>"userid", -value=>"$userid");
	print '<div style="padding-bottom:20px"></div>';

#-----------------------------------------------------------------------------
#--- limit the data reading to the only part which has not been signed off yet
#-----------------------------------------------------------------------------

	@revisions = ();
	system("cat $ocat_dir/updates_table.list | grep NA > $temp_dir/ztemp");
	open (FILE, "$temp_dir/ztemp");
	@revisions = <FILE>;
	system("rm $temp_dir/ztemp");
	close(FILE);

#	if($usint_on =~ /test/){
#
#		print "<form name=\"update\" method=\"post\" action=\"$test_http/orupdate_test.cgi\">";
#
#	}elsif($usint_on =~ /no/){
#
#		print "<form name=\"update\" method=\"post\" action=\"$obs_ss_http/orupdate.cgi\">";
#
#	}else{
#		print "<form name=\"update\" method=\"post\" action=\"$usint_http/orupdate.cgi\">";
#
#	}

	print "<table border=1>";
	print "<tr><th>OBSID.revision</th><th>general obscat edits by</th>";
	print "<th>ACIS obscat edits by</th><th>SI MODE edits by</th><th>Verified by";
	print "</th><th>&nbsp;</th><th>Note</th></tr>";

#
#---- save "hidden" value pass till the end of the table
#
	@save_dname     = ();
	@save_lnmae     = ();
	@save_lval      = ();
	@save_too_obsid = ();
	@save_too_val   = ();
	@save_ddt_obsid = ();
	@save_ddt_val   = ();
	@pass_name_save = ();
	@pass_name_val  = ();
	@ap_cnt_save	= ();
	@ap_cnt_val	= ();

#-----------------------------------------------------------------------------------------
#--- keep the record of revision # of each obsid; one is the highest rev # submitted, and 
#--- the other is the highest rev # still open to be signed off.
#-----------------------------------------------------------------------------------------

#---------------------------------------------------------------
#--- first, find rev # of the obsids which need to be signed off
#---------------------------------------------------------------

	@temp_save  = ();
	OUTER3:
	foreach $ent (@revisions){
		@ctemp = split(/\t+/, $ent);
		if($ctemp[4] !~ /NA/){			#--- if it is already "verified", skip
			next OUTER3;
		}
		@dtemp = split(/\./,  $ctemp[0]);
		push(@temp_save, $dtemp[0]);

		$dname = 'data'."$dtemp[0]";
		$rname = 'cnt'."$dtemp[0]";
		if(${$rname} !~ /\d/){
			${$dname} = int($dtemp[1]);
			${$rname} = 1;
		}else{
			${$rname}++;
			if(${$dname} < $dtemp[1]){
				${$dname} = int($dtemp[1]);
			}
		}
	}

#------------------------------------------
#--- make a list of obsids on the open list
#------------------------------------------

	@temp = sort{$a<=>$b}@temp_save;
	$comp = shift(@temp);
	@ob_list = ("$comp");
	OUTER5:
	foreach $ent (@temp){
		foreach $comp (@ob_list){
			if($ent == $comp){
				next OUTER5;
			}
		}
		push(@ob_list, $ent);
	}

#--------------------------------------------------------------------
#--- now find what is the highest rev # opened so far for each obsid
#--------------------------------------------------------------------

	foreach $ent (@ob_list){
		$chk      = "$ocat_dir/updates/$ent".'*';
		$test     = ` ls $chk`;
		$test     =~ s/$ocat_dir\/updates\///g;
		@temp     = split(/\s+/, $test);
		@otemp    = sort{$a<=>$b} @temp;
		$lastone  = pop(@otemp);
		@ltemp    = split(/\./, $lastone);
		$lname    = 'lastrev'."$ent";
		${$lname} = $ltemp[1];

#----------------------------------------------------------------------------
#--- if a rev # which is already "verfied" is higher than the opened rev #'s
#--- mark it so that we can put a notice of the table
#----------------------------------------------------------------------------

		$dname = 'data'."$ent";
		if(${$dname} < $ltemp[1]){
			$ychk = 1;
		}else{
			$ychk = 0;
		}
		$chklist    = 'chk'."$ent";
		${$chklist} = $ychk;

#		print hidden(-name=>"$dname", -value=>"${$dname}", -override=>"${$dname}");
#		print hidden(-name=>"$lname", -value=>"$ychk", -override=>"$ychk");
		push(@save_dname, $dname);
		push(@save_lnmae, $lname);
		push(@save_lval,  $ychk);

#-------------------------------------
#--- assign color code for each obsid
#-------------------------------------

		$color = 'color'."$ent";

		$cname = 'cnt'."$ent";			#--- cname has # of opened revisions of the obsid

		if(${$cname} <= 1){
			${$color} = '#FFFFE0';		#--- if it is the newest, just white background
		}else{
			${$color} = $color_table[$cj];
			$cj++;
			if($cj > 10){
				$cj == 0;
			}
		}
			
	}


#---------------------------------------------------------
#----- because log is appended to, rather than added to...
#---------------------------------------------------------

	if($reorder eq 'Regroup by Obsids'){
		@revisions = sort{$a<=>$b} (@revisions);
	}
	@revisions = reverse(@revisions);

#------------------------------------------------------------------------------
#---- if user id is typed in, percolate all obsids owned by the user to the top
#------------------------------------------------------------------------------

	if($userid =~ /\w/){
		@u_list = ();
		@o_list = ();
		foreach $chk (@revisions){
			@btemp = split(/\t+/, $chk);
			if($btemp[6] =~ /$userid/){
				push(@u_list, $chk);
			}else{
				push(@o_list, $chk);
			}
		}
		@revisions = @u_list;
		foreach $ent (@o_list){
			push(@revisions, $ent);
		}
	}

	$today = `date '+%D'`;
	chop $today;

	ROUTER:
	foreach $line (@revisions){
		chomp $line;
		@values         = split ("\t", $line);

		if($values[4] !~ /NA/){				#--- if it is signed off, removed from our list
			next ROUTER;
		}

		$obsrev         = $values[0];
		@atemp          = split(/\./, $obsrev);
		$obsid          = $atemp[0];
		$general_status = $values[1];
		$acis_status    = $values[2];
		$si_mode_status = $values[3];
		$dutysci_status = $values[4];
		$seqnum         = $values[5];
		$user           = $values[6];
		@atemp          = split(/\./,$obsrev);
		$tempid         = $atemp[0];

#-------------------------------------------------------------------------
#---- checking whether a ac_user has a permission to sign off the case.
#---- $user and $ac_user could be same, but usually different persons.
#-------------------------------------------------------------------------

		$sign_off = 'no';
		if($sp_user eq 'yes'){ 
			$sign_off = 'yes';
		}else{
			pi_check();
			OUTER:
			foreach $comp (@user_data_list){
				if($obsid == $comp){
					$sign_off = 'yes';
					last OUTER;
				}
			}
		}

		($na0,$na1,$na2,$na3,$na4,$na5,$na6,$na7,$na8,$mtime,$na10,$na11,$na12) 
						= stat "$ocat_dir/updates/$obsrev";


#----------------
#------ get time
#----------------

		($t0,$t1,$t2,$t3,$t4,$t5,$t6,$t7,$t8) = localtime($mtime);

		$month = $t4 + 1;
		$day   = $t3;
		$year  = $t5 + 1900;
		$ftime = "$month/$day/$year";

#----------------------------------------------------------------------------------------------
#---- if dutysci_status is NA (means not signed off yet), print the entry for the verification
#----------------------------------------------------------------------------------------------


		if ($dutysci_status =~/NA/){

#-----------------------------------------
#---- get information about TOO/DDT status
#-----------------------------------------

			get_database_values();

			if($too_chk > 0){
				$name = "too_status.$obsid";
#				print hidden(-name=>"$name", -override=>'Y', -value=>'Y');
				push(@save_too_obsid, $name);
				push(@save_too_val,   'Y');
			}elsif($ddt_chk > 0){
				$name = "ddt_status.$obsid";
#				print hidden(-name=>"$name", -override=>'Y', -value=>'Y');
				push(@save_ddt_obsid, $name);
				push(@save_ddt_val,   'Y');
			}else{
				$name = "too_status.$obsid";
				$name = "ddt_status.$obsid";
#				print hidden(-name=>"$name", -override=>'F', -value=>'F');
#				print hidden(-name=>"$name", -override=>'F', -value=>'F');
				push(@save_too_obsid, $name);
				push(@save_too_val,   'F');
				push(@save_ddt_obsid, $name);
				push(@save_ddt_val,   'F');
			}

#--------------------
#---- OBSID & revison
#--------------------
			$usint_user = 'no';
			OUTER:
			foreach $comp (@special_user){
				if($user eq $comp){
					$usint_user = 'yes';
					last OUTER;
				}
			}
			if($usint_user eq 'no'){
###				print '<tr style="background-color:yellow">';
				print '<tr>';
			}else{
				print "<tr>";
			}

#-----------------------------------------
#--- recall info related rev# of the obsid
#-----------------------------------------

			@etemp = split(/\./, $obsrev);
			$rname = 'data'."$etemp[0]";		#-- highest rev # on the open list
			$sname = 'cnt'."$etemp[0]";		#-- # of rev # open for a given obsid
			$lrev  = 'lastrev'."$etemp[0]";		#-- highest rev # so far for a given obsid
			$hirev = 'chk'."$etemp[0]";		#-- a marker whether higher rev # already "verified"


			$color = 'color'."$etemp[0]";
			print "<td style='background-color:${$color}'>";

			if($usint_on =~  /no/){
				print "<a href=\"$obs_ss_http/chkupdata.cgi";
			}else{
				print "<a href=\"$usint_http/chkupdata.cgi";
			}

			print "\?$obsrev\">$obsrev</a><br />$seqnum<br />$ftime<br />$user</td>";
#--------------------
#----- general obscat 
#--------------------
			if ($general_status =~/NULL/){

				print "<td style='text-align:center'>$general_status</td>";

			} elsif ($general_status =~/NA/){

#----------------------------------------------------------------------------
#----- the case a special user hass a permission to sign off the observation
#----------------------------------------------------------------------------

				if($sp_user eq 'yes'){
					print "<td style='text-align:center'><input type=\"text\" name=\"general_status#$obsrev";
					print "\" size=\"12\"></td>";
					push(@pass_list, "general_status#$obsrev");
				}else{
					print "<td style='text-align:center'>---</td>";
				}
			} else {
				print "<td style='text-align:center'>$general_status</td>";
			}
#------------------
#----- acis obscat
#------------------
			if ($acis_status =~/NULL/){
				print "<td style='text-align:center'>$acis_status</td>";
			} elsif ($acis_status =~/NA/){
				if($sp_user eq 'yes'){
					print "<td style='text-align:center'><input type=\"text\" name=\"acis_status#$obsrev";
					print "\" size=\"12\"></td>";
					push(@pass_list, "acis_status#$obsrev");
				}else{
					print "<td style='text-align:center'>---</td>";
				}
			} else {
				print "<td style='text-align:center'>$acis_status</td>";
			}
#-------------
#----- si mode
#-------------
			if ($si_mode_status =~/NULL/){
				print "<td style='text-align:center'>$si_mode_status</td>";
			} elsif ($si_mode_status =~/NA/){
				if($sp_user eq 'yes'){
					print "<td style='text-align:center'><input type=\"text\" name=\"si_mode_status#$obsrev";
					print "\" size=\"12\"></td>";
					push(@pass_list, "si_mode_status#$obsrev");
				}else{
						print "<td style='text-align:center'>---</td>";
				}
			} else {
				print "<td style='text-align:center'>$si_mode_status</td>";
			}

#------------------
#---- Verification
#------------------

			if ($dutysci_status =~ /NA/){
				if($sign_off eq 'yes'){
					if($sp_user eq 'yes'){
						print "<td style='text-align:center'><input type=\"text\" name=\"dutysci_status#$obsrev";
						print "\" size=\"12\"></td><td><input type=\"submit\" value=\"Update\">";
						push(@pass_list, "dutysci_status#$obsrev");
					}elsif($general_status ne 'NA' && $acis_status ne 'NA' && $si_mode_status ne 'NA'){
						print "<td style='text-align:center'><input type=\"text\" name=\"dutysci_status#$obsrev";
						print "\" size=\"12\"></td><td><input type=\"submit\" value=\"Update\">";
						push(@pass_list, "dutysci_status#$obsrev");
					}else{
						print "<td style='text-align:center'><font color='red'>Not Ready for Sign Off</font></td>";
					}
				}else{
					print "<td style='text-align:center'><font color='red'>No Access</font></td>";
					print "<td style='text-align:center'>&#160</td>";
				}
			} else {
				print "<td style='text-align:center'><font color=\"#005C00\">$dutysci_status</font></td>";
				print "<td style='text-align:center'>---</td>";
			}

#---------------------------------------------------------
#---- check whether there is new comment in this obsid/rev
#---------------------------------------------------------

			open(IN, "$ocat_dir/updates/$obsrev");
			$new_comment = 0;
			OUTER:
			while(<IN>){
				chomp $_;
				if($_ =~ /NEW COMMENT/i && ($_ !~ /NA/i || $_!~ /N\/A/i)){
					$new_comment = 1;
					last OUTER;
				}elsif($_ =~ /Below is /){
					last OUTER;
				}
			}
			close(IN);

#----------------------------------------------------------
#--- check whether CDO warning is posted for this obsid/rev
#----------------------------------------------------------

			$large_coord = 0;
			LOUTER:
			foreach $lchk (@cdo_warning_list){
				if($lchk =~ /$obsrev/){
					$large_coord = 1;
					last LOUTER;
				}
			}

#------------------------------------
#--- print a comment in the note area
#------------------------------------

			$bchk = 0;
			if($new_comment == 1 && $large_coord == 0){
				print "<td><span style='color:red'>New Comment</span>";
				$bchk++;
			}elsif($new_comment == 1 && $large_coord == 1){
				print '<td><span style="color:red">New Comment</span><br/>';
				print '<span style="color:blue">Large Coordinates Shift</span>';
				$bchk++;
			}elsif($new_comment == 0 && $large_coord == 1){
				print '<td><span style="color:blue">Large<br/> Coordinates <br/>Shift</span>';
				$bchk++;
			}

#-------------------------------------------------------------------
#---- if there is maltiple resion entries for a given obsid, say so
#-------------------------------------------------------------------

			if(${$sname} > 1){
				if($bchk > 0){
					print '<br><span style="color:#D2691E">Multiple Revisions Open</span>';
				}else{
					print '<td><span style="color:#D2691E">Multiple Revisions Open</span>';
					$bchk++;
				}
			}

#-----------------------------------------------------------------------------------------
#---- if revision newer than any of them listed on the table is already signed off, say so
#-----------------------------------------------------------------------------------------

			if(${$hirev}  > 0){ 
				if($bchk > 0){
					print "<br><span style='color:#4B0082'>Higher Rev # (${$lrev}) Was Already Signed Off</span>";
				}else{
					print "<td><span style='color:#4B0082'>Higher Rev # (${$lrev}) Was Already Signed Off</span>";
					$bchk++;
				}
			}
		}

		if($bchk == 0){
			print '<td>&#160;';
		}

		print "</td>";
		print "</tr>";

	}

#-------------------------------
#-----pass the changes as params 
#-------------------------------
	$ap_cnt = 0;
	foreach $ent (@pass_list){
		$name = 'pass_name.'."$ap_cnt";
#		print hidden(-name=>"$name", -value=>"$ent", -override=>"$ent");
		push(@pass_name_save, $name);
		push(@pass_name_val,  $ent);
		$ap_cnt++;
	}
#	print hidden(-name=>'ap_cnt', -value=>"$ap_cnt", override=>"$ap_cnt");
	push(@ap_cnt_save, 'ap_cnt');
	push(@ap_cnt_val,  $ap_cnt);
	
#------------------------------------------------------------------
#--- adding already signed off entries from the past couple of days
#------------------------------------------------------------------

	$date = `date '+%D'`;
	chop $date;
	@atemp = split(/\//, $date);
	$atemp[1]--;

	if($atemp[1] == 0){
		$atemp[0]--;
		if($atemp[0] == 0){
			$atemp[2]--;
			$atemp[0] = 12;
			$atemp[1] = 31;
			if($atemp[2] < 10){
				$atemp[2] = int($atemp[2]);
				$atemp[2] = '0'."$atemp[2]";
			}
		}elsif($atemp[0] == 1 || $atemp[0] == 3 || $atemp[0] == 5 || $atemp[0] == 7
    			|| $atemp[0] == 8 || $atemp[0] == 10){
			$atemp[1] = 31;
		}elsif($atemp[0] == 2){
			$chk = 4 * int (0.25 * $atemp[2]);
			if($chk == $atemp[2]){
				$atemp[1] = 29;
			}else{
				$atemp[1] = 28;
			}
		}else{
			$atemp[1] = 30;
		}
		if($atemp[0] < 10){
			$atemp[0] = int($atemp[0]);
			$atemp[0] = '0'."$atemp[0]";
		}
	}
	if($atemp[1] < 10){
		$atemp[1] = int($atemp[1]);
		$atemp[1] = '0'."$atemp[1]";
	}
	$yesterday = "$atemp[0]/$atemp[1]/$atemp[2]";

	@recent   = ();
	open (INFILE, "<$ocat_dir/updates_table.list");
	@all_list   = <INFILE>;
	close (INFILE);

	@all_list_reversed = reverse(@all_list);

	$chk = 0;
	$bchk = 0;
	FEND:
	foreach $line (@all_list_reversed){
		if($line !~ /NA/){
			if($line =~ /$date/){
				push(@recent, $line);
			}elsif($line =~ /$yesterday/){
				push(@recent, $line);
			}
		}
		$chk++;
		if($chk > 100){
			last FEND;
		}
	}

	foreach $line (@recent){
		chomp $line;
		@btemp = split(/\t+/, $line);

    		($na0,$na1,$na2,$na3,$na4,$na5,$na6,$na7,$na8,$mtime,$na10,$na11,$na12) 
						= stat "$ocat_dir/updates/$btemp[0]";

    		($t0,$t1,$t2,$t3,$t4,$t5,$t6,$t7,$t8) = localtime($mtime);

    		$month = $t4 + 1;
    		$day   = $t3;
    		$year  = $t5 + 1900;
    		$ftime = "$month/$day/$year";

		print "<tr>";
		print "<td><a href=\"$usint_http/";
		print "chkupdata.cgi\?$btemp[0]\">$btemp[0]</a><br />$btemp[5]<br />$ftime";
		print "<br />$btemp[6]</td><td style='text-align:center'>$btemp[1]</td><td style='text-align:center'>$btemp[2]</td>";
		print "<td style='text-align:center'>$btemp[3]</td><td style='text-align:center;color;#005C00'>";
		print "$btemp[4]</td><td>&nbsp;</td><td>&nbsp;</td></tr>";
	}

	print "</table>";

#
#--- now pass the hidden values to the next round
#
	foreach $dname (@save_dname){
		print hidden(-name=>"$dname", -value=>"${$dname}", -override=>"${$dname}");
	}

	$j = 0;
	foreach $name (@save_too_obsid){
		$val = $save_too_val[$j];
		print hidden(-name=>"$name", -override=>"$val", -value=>"$val");
		$j++;
	}

	$j = 0;
	foreach $name (@save_ddt_obsid){
		$val = $save_ddt_val[$j];
		print hidden(-name=>"$name", -override=>"$val", -value=>"$val");
		$j++;
	}

	$j = 0;
	foreach $name (@pass_name_save){
		$ent = $pass_name_val[$j];
		print hidden(-name=>"$name", -value=>"$ent", -override=>"$ent");
		$j++;
	}

	foreach $ap_cnt (@ap_cnt_val){
		print hidden(-name=>'ap_cnt', -value=>"$ap_cnt", override=>"$ap_cnt");
	}


}  

###################################################################################
### update_info: will perform updates to table                                 ####
###################################################################################

sub update_info {

#--------------------------------------------
#------- foreach parameter entered from table    
#--------------------------------------------

	$incl = 0;
	$date = `date '+%D'`;
	chop $date;

	@newoutput = ();
	$jmod      = 0;

#---------------------------------------------------------------
#--- select out the data line which still needs to be signed off
#---------------------------------------------------------------

	system("cat $ocat_dir/updates_table.list | grep NA > $temp_dir/xtemp");
	open (INFILE, "<$temp_dir/xtemp");
    	@revcopy   = <INFILE>;
    	close (INFILE);
	system("rm $temp_dir/xtemp");

#------------------------------------------------------
#--- name_list contains the signed off cell information
#------------------------------------------------------

	@stat_type = ();
	@obsline   = ();
	@info      = ();
	$ent_cnt   = 0;

	OUTER:
    	foreach $param (@name_list) {

#-----------------------------------------------------------
#------- split it, get the type of update and the obsid line
#-----------------------------------------------------------

		@tmp       = split ("#", $param);
		$stat_type = $tmp[0];
		$obsline   = $tmp[1];
		$info      = $value_list[$incl];
		$incl++;
		if($info eq ''){		#----  only when someone signed off, go to the next step
			next OUTER;
		}

		push(@stat_save, $stat_type);
		push(@obs_save,  $obsline);
		push(@info_save, $info);
		$ent_cnt++;
		${gadd.$obsline} = 0;
		${aadd.$obsline} = 0;
		${madd.$obsline} = 0;
	}

	for($j = 0; $j < $ent_cnt; $j++){
		$stat_type = $stat_save[$j];
		$obsline   = $obs_save[$j];
		$info      = $info_save[$j];
		
#----------------------------------------------------------------
#------- if there really is a change, make the change	
#----------------------------------------------------------------

		${si_sign.$obsline}   = 0;
		${last_sign.$obsline} = 0;

		NOUTER:
		foreach $newline (@revcopy){
                	chomp $newline;
                	@newvalues         = split ("\t", $newline);
                	$newobsrev         = $newvalues[0];
                	$newgeneral_status = $newvalues[1];
                	$newacis_status    = $newvalues[2];
                	$newsi_mode_status = $newvalues[3];
                	$newdutysci_status = $newvalues[4];
                	$newseqnum         = $newvalues[5];
                	$newuser           = $newvalues[6];

#-------------------------------------------
#---- there is obs id match, change the line
#-------------------------------------------

			if($newobsrev !~ /$obsline/){
				next NOUTER;
			}

    			$jmod++;

#-----------------
#---- general case
#-----------------
    			if ($stat_type =~/general/){
				$templine = "$newobsrev\t$info $date\t$newacis_status\t$newsi_mode_status\t$newdutysci_status\t$newseqnum\t$newuser\n";
				push (@newoutput, $templine);
				${gadd.$obsline}++;

#---------------------------------------
#--- if si mode is NA, set email notice
#---------------------------------------

				if($newsi_mode_status =~ /NA/i){
					open(OUT, ">$temp_dir/si_mail.$obsline.tmp");
					print OUT "Please sign off SI Mode for obsid.rev: $newobsrev at: \n";

					if($usint_on =~ /no/){
						print OUT "$obs_ss_http/orupdate.cgi","\n";
					}elsif($usint_on =~ /yes/){
						print OUT "$usint_http/orupdate.cgi","\n";
					}

					print OUT 'This message is generated by a sign-off web page, so no reply is necessary.',"\n";
					close(OUT);
					${si_sign.$obsline} = 1;
				}
					
#-------------
#--- acis case
#-------------
    			} elsif ($stat_type =~/acis/){
				if(${gadd.$obsline} == 0){
					$templine = "$newobsrev\t$newgeneral_status\t$info $date\t$newsi_mode_status\t$newdutysci_status\t$newseqnum\t$newuser\n";
				}else{
					pop(@newoutput);
					$templine = "$newobsrev\t$info $date\t$info $date\t$newsi_mode_status\t$newdutysci_status\t$newseqnum\t$newuser\n";
				}
				push (@newoutput, $templine);
				${aadd.$obsline}++;

#------------------
#---- si mode case
#------------------
    			} elsif ($stat_type =~/mode/){
				if(${gadd.$obsline} == 0 && ${aadd.$obsline} == 0){
					$templine = "$newobsrev\t$newgeneral_status\t$newacis_status\t$info $date\t$newdutysci_status\t$newseqnum\t$newuser\n";
				}elsif(${gadd.$obsline} != 0 && ${aadd.$obsline} == 0){
					pop(@newoutput);
					$templine = "$newobsrev\t$info $date\t$newacis_status\t$info $date\t$newdutysci_status\t$newseqnum\t$newuser\n";
				}elsif(${gadd.$obsline} == 0 && ${aadd.$obsline} != 0){
					pop(@newoutput);
					$templine = "$newobsrev\t$newgeneral_status\t$info $date\t$info $date\t$newdutysci_status\t$newseqnum\t$newuser\n";
				}else{
					pop(@newoutput);
					$templine = "$newobsrev\t$info $date\t$info $date\t$info $date\t$newdutysci_status\t$newseqnum\t$newuser\n";
				}
				push (@newoutput, $templine);
				${madd.$obsline}++;
#----------------------
#---- duty sci sign off
#----------------------
    			} elsif ($stat_type =~/dutysci/){

#---------------------------------------------------------------------------------------------------------
#--- if the owner of the entry wants to 'verifiy' it without any of general, acis or si mode are signed off
#--- s/he can, except the most recent revision.
#---------------------------------------------------------------------------------------------------------

				@rtemp  = split(/\./, $newobsrev);
				$toprev = 'data'."$rtemp[0]";
				$rval   = param("$toprev");		#--- highest rev # currently opened on the table

				$hirev  = 'lastrev'."$rtemp[0]";
				$hval   = param("$hirev");		#--- indicator saying rev # newer than $rval
									#--- is already signed off (assigned 1)
				$rchk = 0;
				if($rval  >  $rtemp[1]){		#--- the current rev # is smaller than $rval
					$rchk++;
				}
				if($hval > 0){
					$rchk++;
				}

				if(($rchk > 0)  && ($info =~ /$newuser/i)){
					if(${gadd.$obsline} == 0 && $newgeneral_status =~ /NA/){
						$newgeneral_status = "N/A";
					}
					if(${aadd.$obsline} == 0 && $newacis_status    =~ /NA/){
						$newacis_status    = "N/A";
					}
					if(${madd.$obsline} == 0 && $newsi_mode_status =~ /NA/){
						$newsi_mode_status = "N/A";
					}


				}else{
					if($newgeneral_status eq 'NA' || $newacis_status eq 'NA' || $newsi_mode_status eq 'NA'){
						next NOUTER;
					}
				}

				if(${gadd.$obsline} == 0 && ${aadd.$obsline} == 0 && ${madd.$obsline} == 0){
					$templine = "$newobsrev\t$newgeneral_status\t$newacis_status\t$newsi_mode_status\t$info $date\t$newseqnum\t$newuser\n";
				}elsif(${gadd.$obsline} != 0 && ${aadd.$obsline} == 0 && ${madd.$obsline} == 0){
					$zzz= pop(@newoutput);
					$templine = "$newobsrev\t$info $date\t$newacis_status\t$newsi_mode_status\t$info $date\t$newseqnum\t$newuser\n";
				}elsif(${gadd.$obsline} == 0 && ${aadd.$obsline} != 0 && ${madd.$obsline} == 0){
					pop(@newoutput);
					$templine = "$newobsrev\t$newgeneral_status\t$info $date\t$newsi_mode_status\t$info $date\t$newseqnum\t$newuser\n";
				}elsif(${gadd.$obsline} == 0 && ${aadd.$obsline} == 0 && ${madd.$obsline} != 0){
					pop(@newoutput);
					$templine = "$newobsrev\t$newgeneral_status\t$newacis_status\t$info $date\t$info $date\t$newseqnum\t$newuser\n";
				}elsif(${gadd.$obsline} != 0 && ${aadd.$obsline} != 0 && ${madd.$obsline} == 0){
					pop(@newoutput);
					$templine = "$newobsrev\t$info $date\t$info $date\t$newsi_mode_status\t$info $date\t$newseqnum\t$newuser\n";
				}elsif(${gadd.$obsline} != 0 && ${aadd.$obsline} == 0 && ${madd.$obsline} != 0){
					pop(@newoutput);
					$templine = "$newobsrev\t$info $date\t$newacis_status\t$info $date\t$info $date\t$newseqnum\t$newuser\n";
				}elsif(${gadd.$obsline} == 0 && ${aadd.$obsline} != 0 && ${madd.$obsline} != 0){
					pop(@newoutput);
					$templine = "$newobsrev\t$newgeneral_status\t$info $date\t$info $date\t$info $date\t$newseqnum\t$newuser\n";
				}
				push (@newoutput,$templine);

				${last_sign.$obsline} = 1;
                                open(OUT, ">$temp_dir/dutysci_mail.$obsline.tmp");
                                print OUT 'All requested edits have been made for the following obsid.rev',"\n";;
                                print OUT "$newobsrev\n";
				if($usint_user eq 'no'){
					print OUT 'This observation will be automatically approved in 24 hrs',"\n";
				}else{
					@etemp = split(/\./,$newobsrev);
					$obsid = $etemp[0];
					print OUT 'Please remember you still need to approve the observation at:',"\n";
#					print OUT "$obs_ss_http/ocatdata2html.cgi?","$obsid\n";
					print OUT "$usint_http/ocatdata2html.cgi?","$obsid\n";
				}
                                print OUT 'This message is generated by a sign-off web page, so no reply is necessary.',"\n";
                                close(OUT);
                                open(FH, "$pass_dir/user_email_list");
                                OUTER:
                                while(<FH>){
                                        chomp $_;
                                        @atemp = split(/\s+/, $_);
                                        if($atemp[0] eq $newuser){
                                                $email_address = $atemp[3];
                                                last OUTER;
                                        }
                                 }
                                 close(FH);

    			}


#--------------------------------------------------------------------------
#--- check whether this is a TOO/DDT, and if so, check any status changed.
#--------------------------------------------------------------------------

			@btemp    = split(/\./, $newobsrev);
			$newobsid = $btemp[0];

#-------------
#--- TOO case
#-------------
			$name = "too_status.$newobsid";
			$too_status = param($name);

			if($too_status =~ /Y/i){
#
#--- GENERAL entries signed off
#

				if($stat_type =~/general/){
					if($newacis_status =~ /NA/){
						
						#--- ask to sign off ACIS
						
#						open(OUT, ">$temp_dir/too_gen_change");
#						print OUT "Editing of General entries of $newobsrev ";
#						print OUT "were finished and signed off. ";
#						print OUT "Please  update ACIS entries, then go to: ";
#						print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
#						print OUT "and sign off ACIS Status.\n";
#
#						if($usint_on =~ /test/){
#							system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu  $test_email");
#						}else{
#							system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu -ccus\@head.cfa.harvard.edu $email_address");
#							system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu $test_email");
#						}
#						system("rm $temp_dir/too_gen_change");

					}else{
						if($newsi_mode_status =~ /NA/){

							#--- ask to sing off SI MODE

							open(OUT, ">$temp_dir/too_gen_change");
							print OUT "Editing of General entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  update SI Mode entries, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off SI Mode Status.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO SI Status Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO SI Status Signed Off Request: OBSID: $newobsid\n\"  -ccus\@head.cfa.harvard.edu acisdude\@head.cfa.harvard.edu");
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO SI Status Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/too_gen_change");

						}else{
							#--- ask to VERIFY the final status

							open(OUT, ">$temp_dir/too_gen_change");
							print OUT "Editing of all entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  verify it, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off 'Verified By' column.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO Verification Signed Off Request: OBSID: $newobsid\n\"  -ccus\@head.cfa.harvard.edu $email_address");
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/too_gen_change");

						}
					}

				}elsif($stat_type =~ /acis/){
#
#--- ACIS entires signed off
#
					if($newgeneral_status =~ /NA/){

						#--- ask to sign off GENERAL

#						open(OUT, ">$temp_dir/too_gen_change");
#						print OUT "Editing of ACIS entries of $newobsrev ";
#						print OUT "were finished and signed off, but General entries are not yet. ";
#						print OUT "Please  update General entries, then go to: ";
#						print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
#						print OUT "and sign off General Status.\n";
#
#						if($usint_on =~ /test/){
#							system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO General Status Signed Off Request: OBSID: $newobsid\n\"   $test_email");
#						}else{
#							system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu -ccus\@head.cfa.harvard.edu $email_address");
#							system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu $test_email");
#						}
#						system("rm $temp_dir/too_gen_change");

					}else{
						if($newsi_mode_status =~ /NA/){

							#--- ask to sing off SI MODE

							open(OUT, ">$temp_dir/too_gen_change");
							print OUT "Editing of ACIS entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  update SI Mode entries, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off SI Mode Status.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO SI Status Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO SI Status Signed Off Request: OBSID: $newobsid\n\" -ccus\@head.cfa.harvard.edu acisdude\@head.cfa.harvard.edu");
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO SI Status Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/too_gen_change");

						}else{
							#--- ask to VERIFY the final status

							open(OUT, ">$temp_dir/too_gen_change");
							print OUT "Editing of all entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  verify it, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off 'Verified By' column.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO Verification Signed Off Request: OBSID: $newobsid\n\"  -ccus\@head.cfa.harvard.edu $email_address");
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/too_gen_change");

						}
					}

				}elsif($stat_type =~ /si_mode/){
#
#--- SI MODE entires signed off
#
					if($newgeneral_status =~ /NA/){

						#--- ask to sign off GENERAL

#						open(OUT, ">$temp_dir/too_gen_change");
#						print OUT "Editing of SI entries of $newobsrev ";
#						print OUT "were finished and signed off, but General entries are not yet. ";
#						print OUT "Please  update General entries, then go to: ";
#						print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
#						print OUT "and sign off General Status.\n";
#
#						if($usint_on =~ /test/){
#							system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu  $test_email");
#						}else{
#							system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu -ccus\@head.cfa.harvard.edu $email_address");
#							system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu $test_email");
#						}
#						system("rm $temp_dir/too_gen_change");

					}else{
						if($newacis_status =~ /NA/){

							#---- ask to sign off ACIS

#							open(OUT, ">$temp_dir/too_gen_change");
#							print OUT "Editing of SI Mode entries of $newobsrev ";
#							print OUT "were finished and signed off, but ACIS entires are not. ";
#							print OUT "Please  update ACIS entries, then go to: ";
#							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
#							print OUT "and sign off ACIS Status.\n";
#	
#							if($usint_on =~ /test/){
#								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu  $test_email");
#							}else{
#								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu -ccus\@head.cfa.harvard.edu $email_address");
#								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu $test_email");
#							}
#							system("rm $temp_dir/too_gen_change");
	
						}else{

							#---- ask to VERIFY the final staus

							open(OUT, ">$temp_dir/too_gen_change");
							print OUT "Editing of all entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  verify it, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off 'Verified By' column.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO Verification Signed Off Request: OBSID: $newobsid\n\" -ccus\@head.cfa.harvard.edu $email_address");
								system("cat $temp_dir/too_gen_change|mailx -s\"Subject: TOO Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/too_gen_change");

						}
					}
				}
				
			}
#-------------
#--- DDT case
#-------------
			$name = "ddt_status.$newobsid";
			$ddt_status = param($name);

			if($ddt_status =~ /Y/i){
#
#--- GENERAL entries signed off
#

				if($stat_type =~/general/){
					if($newacis_status =~ /NA/){
						
						#--- ask to sign off ACIS
						
#						open(OUT, ">$temp_dir/ddt_gen_change");
#						print OUT "Editing of General entries of $newobsrev ";
#						print OUT "were finished and signed off. ";
#						print OUT "Please  update ACIS entries, then go to: ";
#						print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
#						print OUT "and sign off ACIS Status.\n";
#
#						if($usint_on =~ /test/){
#							system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu  $test_email");
#						}else{
#							system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu -ccus\@head.cfa.harvard.edu $email_address");
#							system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu $test_email");
#						}
#						system("rm $temp_dir/ddt_gen_change");

					}else{
						if($newsi_mode_status =~ /NA/){

							#--- ask to sign off SI MODE

							open(OUT, ">$temp_dir/ddt_gen_change");
							print OUT "Editing of General entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  update SI Mode entries, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off SI Mode Status.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT SI Status Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT SI Status Signed Off Request: OBSID: $newobsid\n\"  -ccus\@head.cfa.harvard.edu acisdude\@head.cfa.harvard.edu");
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT SI Status Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/ddt_gen_change");

						}else{
							#--- ask to VERIFY the final status

							open(OUT, ">$temp_dir/ddt_gen_change");
							print OUT "Editing of all entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  verify it, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off 'Verified By' column.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT Verification Signed Off Request: OBSID: $newobsid\n\"  -ccus\@head.cfa.harvard.edu $email_address");
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/ddt_gen_change");

						}
					}

				}elsif($stat_type =~ /acis/){
#
#--- ACIS entires signed off
#
					if($newgeneral_status =~ /NA/){

						#--- ask to sign off GENERAL

#						open(OUT, ">$temp_dir/ddt_gen_change");
#						print OUT "Editing of ACIS entries of $newobsrev ";
#						print OUT "were finished and signed off, but General entries are not yet. ";
#						print OUT "Please  update General entries, then go to: ";
#						print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
#						print OUT "and sign off General Status.\n";
#
#						if($usint_on =~ /test/){
#							system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu  $test_email");
#						}else{
#							system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu -ccus\@head.cfa.harvard.edu $email_address");
#							system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu $test_email");
#						}
#						system("rm $temp_dir/ddt_gen_change");

					}else{
						if($newsi_mode_status =~ /NA/){

							#--- ask to sing off SI MODE

							open(OUT, ">$temp_dir/ddt_gen_change");
							print OUT "Editing of ACIS entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  update SI Mode entries, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off SI Mode Status.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT SI Status Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT SI Status Signed Off Request: OBSID: $newobsid\n\"  -ccus\@head.cfa.harvard.edu acisdude\@head.cfa.harvard.edu");
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT SI Status Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/ddt_gen_change");

						}else{
							#--- ask to VERIFY the final status

							open(OUT, ">$temp_dir/ddt_gen_change");
							print OUT "Editing of all entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  verify it, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off 'Verified By' column.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT Verification Signed Off Request: OBSID: $newobsid\n\"  -ccus\@head.cfa.harvard.edu $email_address");
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/ddt_gen_change");

						}
					}

				}elsif($stat_type =~ /si_mode/){
#
#--- SI MODE entires signed off
#
					if($newgeneral_status =~ /NA/){

						#--- ask to sign off GENERAL

#						open(OUT, ">$temp_dir/ddt_gen_change");
#						print OUT "Editing of SI entries of $newobsrev ";
#						print OUT "were finished and signed off, but General entries are not yet. ";
#						print OUT "Please  update General entries, then go to: ";
#						print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
#						print OUT "and sign off General Status.\n";
#
#						if($usint_on =~ /test/){
#							system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu  $test_email");
#						}else{
#							system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu -ccus\@head.cfa.harvard.edu $email_address");
#							system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT General Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu $test_email");
#						}
#						system("rm $temp_dir/ddt_gen_change");

					}else{
						if($newacis_status =~ /NA/){

							#---- ask to sign off ACIS

#							open(OUT, ">$temp_dir/ddt_gen_change");
#							print OUT "Editing of SI Mode entries of $newobsrev ";
#							print OUT "were finished and signed off, but ACIS entires are not. ";
#							print OUT "Please  update ACIS entries, then go to: ";
#							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
#							print OUT "and sign off ACIS Status.\n";
#	
#							if($usint_on =~ /test/){
#								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu  $test_email");
#							}else{
#								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu -ccus\@head.cfa.harvard.edu $email_address");
#								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT ACIS Status Signed Off Request: OBSID: $newobsid\n\" -rcus\@head.cfa.harvard.edu $test_email");
#							}
#							system("rm $temp_dir/ddt_gen_change");
	
						}else{

							#---- ask to VERIFY the final staus

							open(OUT, ">$temp_dir/ddt_gen_change");
							print OUT "Editing of all entries of $newobsrev ";
							print OUT "were finished and signed off. ";
							print OUT "Please  verify it, then go to: ";
							print OUT 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/orupdate.cgi ';
							print OUT "and sign off 'Verified By' column.\n";
	
							if($usint_on =~ /test/){
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}else{
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT Verification Signed Off Request: OBSID: $newobsid\n\"  -ccus\@head.cfa.harvard.edu $email_address");
								system("cat $temp_dir/ddt_gen_change|mailx -s\"Subject: DDT Verification Signed Off Request: OBSID: $newobsid\n\"  $test_email");
							}
							system("rm $temp_dir/ddt_gen_change");

						}
					}
				}
			}
		}
	}

#----------------------------------------------------------------------
#---- start updating the updates_table.list, if there are any changes.
#----------------------------------------------------------------------


	if($jmod >= 0){
	        $lpass = 0;
	        $wtest = 0;
	        my $efile = "$ocat_dir/updates_table.list";

	        OUTER:
	        while($lpass == 0){
	                open(my $update, '+<', $efile) or die "Locked";
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

#------------------------------------------------------
#--- else, if the file is being updated, print an error
#------------------------------------------------------

    					print "<b><font color=\"#FF0000\">ERROR: The update file is currently being edited by someone else.<br />";
    					print "Please use the back button to return to the previous page, and resubmit.</font></b>";
    					print "</body>";
    					print "</html>";

#-----------------------------------------------------------------------
#----- if there is an error, exit now so no mail or file writing happens
#-----------------------------------------------------------------------
    					exit();
	                        }
	                }else{
#--------------------------------------------------------------------------------------------------
#----  if it is not being edited, write update updates_table.list---data for the verificaiton page
#--------------------------------------------------------------------------------------------------

				open (INFILE, "<$efile");
				@all_list   = <INFILE>;
				close (INFILE);
				@all_list_reversed = reverse(@all_list);

	                        $lpass = 1;

	                        flock($update, LOCK_EX) or die "died while trying to lock the file<br />\n";

#
#--- count a modified entries
#
				@temp_head = ();
				$tcnt      = 0;
				foreach $ent (@newoutput){
					@atemp = split(/\s+/, $ent);
					push(@temp_head, $atemp[0]);
					$tcnt++;
				}

				@new_list = ();
				$chk = 0;
				FOUTER:
				foreach $line (@all_list_reversed){

					if($chk < $tcnt){
						for($m = 0; $m < $tcnt; $m++){
							if($line =~ /$temp_head[$m]/){
								push(@new_list, $newoutput[$m]);
								$chk++;
								next  FOUTER;
							}
						}
					}
					push(@new_list, $line);
				}
	
				@new_list_reversed = reverse(@new_list);
				foreach $ent (@new_list_reversed){
					print $update "$ent";
				}

	                        close $update;

#-------------------
#--- sending si mail
#-------------------
				for $e_id (@temp_head){
					if(${si_sign.$e_id} > 0){
						if($usint_on =~ /test/){
######							system("cat $temp_dir/si_mail.$e_id.tmp |mailx -s\"Subject: Signed Off Notice\n\" -rcus\@head.cfa.harvard.edu  $test_email");
#							system("cat $temp_dir/si_mail.$e_id.tmp |mailx -s\"Subject: Signed Off Notice\n\" -rcus\@head.cfa.harvard.edu  isobe\@head.cfa.harvard.edu");
						}else{
							if($acis_status =~ /NULL/){
                                  				system("cat $temp_dir/si_mail.$e_id.tmp |mailx -s\"Subject: Signed Off Notice\n\"  -ccus\@head.cfa.harvard.edu  juda\@head.cfa.harvard.edu");
								}else{
#                                  			system("cat $temp_dir/si_mail.$e_id.tmp |mailx -s\"Subject: Signed Off Notice\n\" -rcus\@head.cfa.harvard.edu -ccus\@head.cfa.harvard.edu  acisdude\@head.cfa.harvard.edu");
							}
						}
						system("rm $temp_dir/si_mail.$e_id.tmp");
					}
#---------------------------
#--- sending  sign off mail
#---------------------------
                        		if(${last_sign.$e_id} > 0 ){
						if($usint_on =~ /test/){
##### 	                                		system("cat $temp_dir/dutysci_mail.$e_id.tmp |mailx -s\"Subject: Signed Off Notice\n\" -rcus\@head.cfa.harvard.edu  $test_email");
                                       			system("cat $temp_dir/dutysci_mail.$e_id.tmp |mailx -s\"Subject: Signed Off Notice\n\"  isobe\@head.cfa.harvard.edu");
						}else{
                                       			system("cat $temp_dir/dutysci_mail.$e_id.tmp |mailx -s\"Subject: Signed Off Notice\n\"  -c  cus\@head.cfa.harvard.edu  $email_address");
                                       			system("cat $temp_dir/dutysci_mail.$e_id.tmp |mailx -s\"Subject: Signed Off Notice\n\" isobe\@head.cfa.harvard.edu");
						}
                                		system("rm $temp_dir/dutysci_mail.$e_id.tmp");
                        		}
				}
			}
    		}
	}
}
