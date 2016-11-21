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

#################################################################################
#										#
#	express_signoff.cgi: This script let a user to sign off multiple obsids	#
#				 at one process.				#
#										#
#	author: t. isobe (tisobe@cfa.harvard.edu)				#
#										#
#	last update: Oct 17, 2016	           				#
#										#
#################################################################################


#-------------------------------------------------------------------------------
#---- if this is usint version, set the following param to 'yes', otherwise 'no'
#-------------------------------------------------------------------------------

############################
#--- a few settings ....
############################

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
#---- set directory paths : updated to read from a file (02/25/2011)
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

$usint_home   = 'https://cxc.cfa.harvard.edu/cus/';                #--- USINT page
$usint_http   = 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/';      #--- web site for usint users
$obs_ss_http  = 'https://cxc.cfa.harvard.edu/cgi-bin/obs_ss/';     #--- web site for none usint users (GO Expert etc)
$test_http    = 'http://asc.harvard.edu/cgi-gen/mta/Obscat/';  #--- web site for test
$test_http    = 'https://cxc.cfa.harvard.edu/mta/CUS/Usint/Linux_test/'; #--- web site for test

$mp_http      = 'http://asc.harvard.edu/';                      #--- web site for mission planning related
$chandra_http = 'http://cxc.harvard.edu/';                      #--- chandra main web site
$cdo_http     = 'https://icxc.cfa.harvard.edu/cgi-bin/cdo/';        #--- CDO web site

############################
#----- end of settings
############################

$org_obsid = $ARGV[0];
chomp $org_obsid;

#-------------------------------------------------------------------
#---- read approved list, and check whether this obsid is listed.
#---- if it does, send warning.
#-------------------------------------------------------------------

open(FH, "$ocat_dir/approved");

@app_obsid = ();
while(<FH>){
        chomp $_;
        @atemp = split(/\s+/, $_);
        push(@app_obsid, $atemp[0]);
}
close(FH);

$prev_app = 0;

#--------------------------------------------------------------------
#----- here are non CXC GTOs who have an access to data modification.
#--------------------------------------------------------------------

@special_user  = ("$test_user",  'mta');
@special_email = ("$test_email", "$test_email");
$no_sp_user    = 2;

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

%pwd_list = ();                                 # save the user-password list
while(<FH>) {
        chomp $_;
        @passwd                 = split(/:/,$_);
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
        $en_submitter =~ s/$char/$Cookie_Encode_Chars{$char}/g;
        $en_pass_word =~ s/$char/$Cookie_Encode_Chars{$char}/g;
}

$user_cookie = cookie(-name    =>'submitter',
                      -value   =>"$en_submitter",
                      -path    =>'/',
                      -expires => '+8h');
$pass_cookie = cookie(-name    =>'pass_word',
                      -value   =>"$en_pass_word",
                      -path    =>'/',
                      -expires => '+8h');

#-------------------------
#---- new cookies wrote in
#-------------------------

print header(-cookie=>[$user_cookie, $pass_cookie], -type => 'text/html;charset=utf-8');


#----------------------------------------------------------------------------------
#------- start printing a html page here.
#------- there are three distinct html page. one is Ocat Data Page (data_input_page),
#------- second is Submit page (prep_submit), and the lastly, Oredit page (oredit).
#----------------------------------------------------------------------------------

print "<!DOCTYPE html>";
print "<html>";
print "<head>";
print "<title>Express Sign Off Page</title>";
print "<style  type='text/css'>";
print "table{text-align:center;margin-left:auto;margin-right:auto;border-style:solid;border-spacing:8px;border-width:2px;border-collapse:separate}";
print "a:link {color:blue;}";
print "a:visited {color:teal;}";
print "</style>";
print "</head>";
print "<body style='color:#000000;background-color:#FFFFE0'>";


print start_form();

$no_access  = 0;                                 # this indicator used for special user previledge
$send_email = 'yes';

if($usint_on =~ /test/){
#	system("chmod 777 $test_dir/ocat/approved");
#	system("chmod 777 $test_dir/ocat/updates_table.list");
#	system("chmod 777 $test_dir/ocat/updates/*");
}

$check   = param("Check");                      # a param which indicates which page to be displayed
$change  = param("Change");
$approve = param("Approve");
$final   = param("Final");
$back    = param("Back");

print hidden(-name=>'send_email', -value=>"$send_email");
print hidden(-name=>'Check', -value=>"$check");

#-------------------------------------------------
#--------- checking password!
#-------------------------------------------------

#######pass_param();                   # sub to pass parameters between submitting data
$pass  = param("pass");
if($submitter !~ /\w/){
        $submitter = param('submitter');
}
$dutysci = $submitter;

if($email_adress !~ /\w/){
	$email_address = param('email_adress');
}

if($change =~ /Change/){
                password_check();
}elsif($approve !~ /Approve/ && $final !~ /Finalize/ 
		&& ($check eq '' || $check =~ /Submit/ || $back =~ /Back to the Previous Page/)){

        $chg_user_ind = param('chg_user_ind');
        match_user();
        if($pass =~ /yes/){

                input_obsid();

        }else{
                print "<h1>Ocat Data Express Approval Page</h1>";
                print "<h3>";
                print "On this page, you can approve more than one observations ";
                print " consequently. To use this page, however,  your name must be registered. ";
                print " If you are not, please contact Dr. Wolk ";
                print ' at <a href="mailto:swolk@head.cfa.harvard.edu">swolk@head.cfa.harvard.edu</a>';
                print "</h3>";

                if(($submitter ne '' || $password ne '') && $pass =~ /no/){
                        print "<p style='color:red;padding-top:20px;padding-bottom:20px'><strong>";
                        print 'Your user name and/or password were entered incorrectly. ';
                        print 'please try again.';
                        print "</p>";
                }

                password_check();
        }

}elsif($final !~ /Finalize/ && ($pass eq '' || $pass =~ /no/)){

        password_check();

}elsif($approve =~ /Approve/){
	$temp = param("obsid_list");
	if($temp =~ /\-/){
		$temp =~ s/\s+//g;
		@atemp = split(/\-/, $temp);
		@obsid_list = ();
		for($ent = $atemp[0]; $ent <= $atemp[1]; $ent++){
			push(@obsid_list, $ent);
		}
	}elsif($temp =~ /\,/){
		$temp =~ s/\s+//g;
		@obsid_list = split(/\,/, $temp);
	}elsif($temp =~ /\;/){
		$temp =~ s/\s+//g;
		@obsid_list = split(/\;/, $temp);
	}elsif($temp =~ /\//){
		$temp =~ s/\s+//g;
		@obsid_list = split(/\//, $temp);
	}else{
		@obsid_list = split(/\s+/, $temp);
	}
#
#--- read which obsids are in the avtive OR list
#
	open(IN, "$obs_ss/scheduled_obs_list");
	@or_list = ();
	while(<IN>){
		chomp $_;
		@mtemp = split(/\s+/, $_);
		push(@or_list, $mtemp[0]);
	}
	close(IN);

	print "<h2 style='padding-top:20px;padding-bottom:10px'>Are you sure to approve the observations of:</h2>";
	print '<table border=1>';
	print '<tr><th>OBSID</th>';
	print '<th>ID</th>';
	print '<th>Seq #</th>';
	print '<th>Title</th>';
	print '<th>Target</th>';
	print '<th>PI</th>';
	print '<th>Note</th></tr>';

	$chk_app  = 0;
	$chk_app2 = 0;
	$chk_app3 = 0;
	$mp_warn_list = '';
	foreach $obsid (@obsid_list){
		OUTER:
		foreach $comp (@app_obsid){
			if($obsid == $comp){
				$chk_app = 1;
				$bgcolor='red';
				last;
			}
		}
		OUTER2:
		foreach $comp (@or_list){
			if($obsid == $comp){
				$chk_app2 = 1;
				$bgcolor2 = 'yellow';
				last;
			}
		}

		read_databases();


		if($si_mode =~ /blank/i || $si_mode =~ /NULL/i || $si_mode eq '' || $si_mode =~ /\s+/){
			$chk_app3 = 1;
			$bgcolor  = 'orange';
		}

		if($usint_on =~ /test/){
			print "<tr><td style='background-color:$bgcolor'><a href=\"$test_http/ocatdata2html.cgi?$obsid\" target='_blank'>$obsid</td>";
		}elsif($usint_on =~ /yes/){
			print "<tr><td style='background-color:$bgcolor'><a href=\"$usint_http/ocatdata2html.cgi?$obsid\" target='_blank'>$obsid</td>";
		}else{
			print "<tr><td style='background-color:$bgcolor'><a href=\"$obs_ss_http/ocatdata2html.cgi?$obsid\" target='_blank'>$obsid</td>";
		}
		print "<td style='background-color:$bgcolor'>$targid</td>";
		print "<td style='background-color:$bgcolor'>$seq_nbr</td>";
		print "<td style='background-color:$bgcolor'>$proposal_title</td>";
		print "<td style='background-color:$bgcolor'>$targname</td>";
		print "<td style='background-color:$bgcolor'>$PI_name</td>";
		if($chk_app  > 0){
			print "<td style='background-color:$bgcolor'>Already Approved </td></tr>";
			$chk_app     = 0;
			$app_warning = 1;
		}elsif($chk_app2 > 0){
			print "<td style='background-color:$bgcolor2'>in Active OR List</td></tr>";
			$mp_warn_list = "$mp_warn_list:"."$obsid";
			$chk_app2     = 0;
		}elsif($chk_app3 > 0){
			print "<td style='background-color:$bgcolor'>SI Mode Is Not Set</td></tr>";
			$chk_app     = 0;
			$app_warning3= 3;
		}else{
			print "<td>&#160;</td></tr>";
		}
		$bgcolor  = 'white';
		$bgcolor2 = 'white';
	}
	print "</table>";
	
	print hidden(-name=>'obsid_list',   -value=>"$temp");
	print hidden(-name=>'mp_warn_list', -value=>"$mp_warn_list");

	print "<div style='padding-bottom:30px;'></div>";

	if($app_warning > 0){
		print "<h3>The observation marked by<span style='color:red'> red </span>is already in the approved list. ";
		print "Please go back and remove it from the list.</h3>";
	}
	if($app_warning3 > 0){
		print "<h3>The observation marked by<span style='color:orange'> orange </span>is missing SI mode. ";
		print "Please go back and remove it from the list.</h3>";
	}
	if($chk_app == 0 && $chk_app2 == 0 && $chk_app3 == 0){	
		print '<input type="submit" name="Final" value="Finalize">';
	}

	print '<br /><br />';
	print '<input type="submit" name="Back" value="Back to the Previous Page">';
	
}elsif($final =~ /Finalize/){
	$temp = param("obsid_list");

	if($temp =~ /\-/){
		$temp =~ s/\s+//g;
		@atemp = split(/\-/, $temp);
		@obsid_list = ();
		for($ent = $atemp[0]; $ent <= $atemp[1]; $ent++){
			push(@obsid_list, $ent);
		}
	}elsif($temp =~ /\,/){
		$temp =~ s/\s+//g;
		@obsid_list = split(/\,/, $temp);
	}elsif($temp =~ /\;/){
		$temp =~ s/\s+//g;
		@obsid_list = split(/\;/, $temp);
	}elsif($temp =~ /\//){
		$temp =~ s/\s+//g;
		@obsid_list = split(/\//, $temp);
	}else{
		@obsid_list = split(/\s+/, $temp);
	}

	print "<br /><h3>Approving.....  (it may take a few minutes)</h3>";

	foreach $obsid(@obsid_list){

		read_databases();

		$asis = 'ASIS';

		read_name();

		prep_submit();                          # sub to  print a modification check page

		print hidden(-name=>'seq_nbr',-override=>"$seq_nbr", -value=>"$seq_nbr");

		submit_entry();

		oredit();
	}

#
#--- if the observation is in an active OR list, send warning to MP
#

	$mp_list      = param('mp_warn_list');
	@atemp        =  split(/:/, $mp_list);
	@mp_warn_list = ();
	$chk          = 0;
	OUTER:
	foreach $obsid (@atemp){
		if($obsid =~ /\d/){
			push(@mp_warn_list, $obsid);
			$chk++;
		}
	}
	if($chk > 0){
		send_email_to_mp();
	}
#
#--- check approved obsids is actually in apporved list and send out email to the user
#
	check_apporved_list();

#
#--- notify the user the task is done and display the ending message.
#
        print "";
        print "<h2 style='padding-bottom:15px'>ALL DONE!!</h2>";
        print "<h3 style='padding-bottom:30px'>You should receive confirmation email shortly.</h3>";

	if($usint_on =~ /test/){

		if($org_obsid =~ /\d/){
			print "<h3>Back to <a href=\"$test_http/ocatdata2html.cgi?$org_obsid\">Ocat Data Page (obsid: $org_obsid)</a>";
		}

        	print "<h3>Back to <a href=\"$test_http/express_signoff.cgi\">Top of Express Approval Page</a></h3>";

	}elsif($usint_on =~ /yes/i){

		if($org_obsid =~ /\d/){
			print "<h3>Back to <a href=\"$usint_http/ocatdata2html.cgi?$org_obsid\">Ocat Data Page (obsid: $org_obsid)</a></h3>";
		}
		print "<h3>Back to <a href=\"$usint_http/express_signoff.cgi\">Top of Express Approval Page</a></h3>";
        	print "<h3>Back to <a href=\"$usint_home/\">USINT Page</a></h3>";

	}else{
		if($org_obsid =~ /\d/){
			print "<h3>Back to <a href=\"$obs_ss_http/ocatdata2html.cgi?$org_obsid\">Ocat Data Page (obsid: $org_obsid)</a></h3>";
		}
		print "<h3>Back to <a href=\"$obs_ss_http/express_signoff.cgi\">Top of Express Approval Page</a></h3>";
        	print "<h3>Back to <a href=\"$obs_ss_http/\">USINT Page</a></h3>";
	}
	exit 1;
}

print end_form();
print "</body>";
print "</html>";


#########################################################################
### password_check: open a user - a password input page               ###
#########################################################################

sub password_check{
        print '<h3>Please type your user name and password</h3>';
        print '<table><tr><th>Name</th><td>';
        print textfield(-name=>'submitter', -value=>'', -size=>20);
        print '</td></tr><tr><th>Password</th><td>';
        print password_field( -name=>'password', -value=>'', -size=>20);
        print '</td></tr></table><br>';

#       print hidden(-name=>'Check', -override=>'', -value=>'');
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
        if($pass_status eq 'match'){
                $pass = 'yes';
                print hidden(-name=>'pass', -override=>"$pass", -value=>"$pass");
        }else{
                $pass = 'no';
        }
}

################################################################################
### input_obsid: a page to write in list of obsids                           ###
################################################################################

sub input_obsid{

        print "<h2 style='padding-bottom:20px'>Welcome to Express Approval Page.</h2>";
        print '<h3>Please type all obsids which you want to approve (separated by ",", ";", "/" or white spaces)</h3>';
	print '<h3>If the entires are sequential without  any breaks, put the first and the last obsids with "-" <br /> ';
	print 'between two obsids. (e.g., 12507-12533). The values are <em>INCLUSIVE</em>.</h3>';

        print textfield(-name=>'obsid_list', -value=>'', -size=>100);

        print "<div style='padding-top:20px;padding-botom:20px'>";
        print '<input type="submit" name="Approve" value="Approve">';
        print '</div>';

        print '<hr />';
        print "<h3 style='padding-top:20px'>If you are not a user  <span style='color:blue'>$submitter</span>, please change a user name: ";
        print '<input type="submit" name="Change" value="Change"> </h3>';

        print hidden(-name=>'submitter',-override=>"$submitter", -value=>"$submitter");
}


################################################################################
### sub read_databases: read out values from databases                       ###
################################################################################

sub read_databases{

        $web = $ENV{'HTTP_REFERER'};
        if($web =~ /icxc/){
            $db_user   = "mtaops_internal_web";
            $db_passwd =`cat $pass_dir/.targpass_internal`;
        }else{
            $db_user = "mtaops_public_web";
            $db_passwd =`cat $pass_dir/.targpass_public`;
        }

        $server  = "ocatsqlsrv";

#       $db_user = "browser";
#       $server  = "sqlbeta";
#       $db_user = "browser";
#       $server  = "sqlxtest";


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

#       $sqlh1 = $dbh1->prepare(qq(select preferences  from target where obsid=$obsid));
#       $sqlh1->execute();
#       ($preferences) = $sqlh1->fetchrow_array;
#       $sqlh1->finish;

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

#       $sqlh1 = $dbh1->prepare(qq(select mp_remarks from target where obsid=$obsid));
#       $sqlh1->execute();
#       ($mp_remarks) = $sqlh1->fetchrow_array;

#---------------------------------
#---------  get roll_pref comments
#---------------------------------

#       $sqlh1 = $dbh1->prepare(qq(select roll_pref  from target where obsid=$obsid));
#       $sqlh1->execute();
#        ($roll_pref) = $sqlh1->fetchrow_array;
#       $sqlh1->finish;

#--------------------------------
#--------  get date_pref comments
#--------------------------------

#       $sqlh1 = $dbh1->prepare(qq(select date_pref from target where obsid=$obsid));
#       $sqlh1->execute();
#       ($date_pref) = $sqlh1->fetchrow_array;
#       $sqlh1->finish;

#----------------------------------
#---------  get coord_pref comments
#----------------------------------

#       $sqlh1 = $dbh1->prepare(qq(select coord_pref  from target where obsid=$obsid));
#       $sqlh1->execute();
#        ($coord_pref) = $sqlh1->fetchrow_array;
#       $sqlh1->finish;

#---------------------------------
#---------  get cont_pref comments
#---------------------------------

#       $sqlh1 = $dbh1->prepare(qq(select cont_pref from target where obsid=$obsid));
#       $sqlh1->execute();
#       ($cont_pref) = $sqlh1->fetchrow_array;
#       $sqlh1->finish;

#------------------------------------------
#-------- combine all remarks to one remark
#------------------------------------------

#       $remark_cont = '';
#       if($roll_pref =~ /\w/){
#               unless($roll_pref =~ /N\/A/){
#                       $remark_cont ="$remark_cont".'<I><B>Roll preferences:</B></I><BR>'."$roll_pref".'<BR>';
#               }
#       }
#       if($date_pref =~ /\w/){
#               unless($data_pref =~ /N\/A/){
#                       $remark_cont ="$remark_cont".'<I><B>Date preferences:</B></I><BR>'."$date_pref".'<BR>';
#               }
#       }
#       if($coord_pref =~ /\w/){
#               unless($coord_pref =~ /N\/A/){
#                       $remark_cont ="$remark_cont".'<I><B>Coord preferences:</B></I><BR>'."$coord_pref".'<BR>';
#               }
#       }
#       if($cont_pref =~ /\w/){
#               unless($cont_pref =~ /N\/A/){
#                       $remark_cont ="$remark_cont".'<I><B>Cont preferences:</B></I><BR>'."$cont_pref".'<BR>';
#               }
#       }
#       if($preferences =~ /\w/){
#               unless($preferences =~ /N\/A/){
#                       $remark_cont ="$remark_cont".'<I><B>Preferences:</B></I><BR>'."$preferences".'<BR>';
#               }
#       }

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

        $targid                         = $targetdata[1];
        $seq_nbr                        = $targetdata[2];
        $targname                       = $targetdata[3];
        $obj_flag                       = $targetdata[4];
        $object                         = $targetdata[5];
        $si_mode                        = $targetdata[6];
        $photometry_flag                = $targetdata[7];
        $vmagnitude                     = $targetdata[8];
        $ra                             = $targetdata[9];
        $dec                            = $targetdata[10];
        $est_cnt_rate                   = $targetdata[11];
        $forder_cnt_rate                = $targetdata[12];
        $y_det_offset                   = $targetdata[13];
        $z_det_offset                   = $targetdata[14];
        $raster_scan                    = $targetdata[15];
        $dither_flag                    = $targetdata[16];
        $approved_exposure_time         = $targetdata[17];
        $pre_min_lead                   = $targetdata[18];
        $pre_max_lead                   = $targetdata[19];
        $pre_id                         = $targetdata[20];
        $seg_max_num                    = $targetdata[21];
        $aca_mode                       = $targetdata[22];
        $phase_constraint_flag          = $targetdata[23];
        $proposal_id                    = $targetdata[24];
        $acisid                         = $targetdata[25];
        $hrcid                          = $targetdata[26];
        $grating                        = $targetdata[27];
        $instrument                     = $targetdata[28];
        $rem_exp_time                   = $targetdata[29];
        $soe_st_sched_date              = $targetdata[30];
        $type                           = $targetdata[31];
        $lts_lt_plan                    = $targetdata[32];
        $mpcat_star_fidlight_file       = $targetdata[33];
        $status                         = $targetdata[34];
        $data_rights                    = $targetdata[35];
        $tooid                          = $targetdata[36];
        $description                    = $targetdata[37];
        $total_fld_cnt_rate             = $targetdata[38];
        $extended_src                   = $targetdata[39];
        $uninterrupt                    = $targetdata[40];
        $multitelescope                 = $targetdata[41];
        $observatories                  = $targetdata[42];
        $tooid                          = $targetdata[43];
        $constr_in_remarks              = $targetdata[44];
        $group_id                       = $targetdata[45];
        $obs_ao_str                     = $targetdata[46];
        $roll_flag                      = $targetdata[47];
        $window_flag                    = $targetdata[48];
        $spwindow                       = $targetdata[49];
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
                undef $pre_min_lead;
                undef $pre_max_lead;
                undef $pre_id;

                $sqlh1 = $dbh1->prepare(qq(select
                        obsid
                from target where group_id = \'$group_id\'));
                $sqlh1->execute();

                while(@group_obsid = $sqlh1->fetchrow_array){
                        $group_obsid = join("<td>", @group_obsid);
                        @group       = (@group, "<a href=\"\.\/ocatdata2html.cgi\?$group_obsid\">$group_obsid<\/a> ");
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
                        last OUTER;
                }
                $roll_ordr = $rollreq_data[0];
                $roll_ordr =~ s/\s+//g;
        }
        if($roll_ordr =~ /\D/ || $roll_ordr eq ''){
                $roll_ordr = 1;
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
                        last OUTER;
                }
                $time_ordr = $timereq_data[0];                          # here is time order
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

#                       hrc_config,hrc_chop_duty_cycle,hrc_chop_fraction,
#                       hrc_chop_duty_no,hrc_zero_block,timing_mode,si_mode
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
                $hrc_si_mode         = "NULL";
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

                $exp_mode               = $acisdata[0];
                $ccdi0_on               = $acisdata[1];
                $ccdi1_on               = $acisdata[2];
                $ccdi2_on               = $acisdata[3];
                $ccdi3_on               = $acisdata[4];

                $ccds0_on               = $acisdata[5];
                $ccds1_on               = $acisdata[6];
                $ccds2_on               = $acisdata[7];
                $ccds3_on               = $acisdata[8];
                $ccds4_on               = $acisdata[9];
                $ccds5_on               = $acisdata[10];

                $bep_pack               = $acisdata[11];
                $onchip_sum             = $acisdata[12];
                $onchip_row_count       = $acisdata[13];
                $onchip_column_count    = $acisdata[14];
                $frame_time             = $acisdata[15];

                $subarray               = $acisdata[16];
                $subarray_start_row     = $acisdata[17];
                $subarray_row_count     = $acisdata[18];
                $duty_cycle             = $acisdata[19];
                $secondary_exp_count    = $acisdata[20];

                $primary_exp_time       = $acisdata[21];
                $eventfilter            = $acisdata[22];
                $eventfilter_lower      = $acisdata[23];
                $eventfilter_higher     = $acisdata[24];
                $most_efficient         = $acisdata[25];

                $dropped_chip_count     = $acisdata[26];
		$multiple_spectral_lines = $acisdata[27];
		$spectra_max_count       = $acisdata[28];


#               $bias_after             = $acisdata[27];

#               $secondary_exp_time     = $acisdata[22];
#               $bias_request           = $acisdata[25];
#               $fep                    = $acisdata[27];
#               $subarray_frame_time    = $acisdata[28];
#               $frequency              = $acisdata[30];
        } else {
                $exp_mode               = "NULL";
                $ccdi0_on               = "NULL";
                $ccdi1_on               = "NULL";
                $ccdi2_on               = "NULL";
                $ccdi3_on               = "NULL";
                $ccds0_on               = "NULL";
                $ccds1_on               = "NULL";
                $ccds2_on               = "NULL";
                $ccds3_on               = "NULL";
                $ccds4_on               = "NULL";
                $ccds5_on               = "NULL";
                $bep_pack               = "NULL";
                $onchip_sum             = "NULL";
                $onchip_row_count       = "NULL";
                $onchip_column_count    = "NULL";
                $frame_time             = "NULL";
                $subarray               = "NONE";
                $subarray_start_row     = "NULL";
                $subarray_row_count     = "NULL";
                $subarray_frame_time    = "NULL";
                $duty_cycle             = "NULL";
                $secondary_exp_count    = "NULL";
                $primary_exp_time       = "";
                $eventfilter            = "NULL";
                $eventfilter_lower      = "NULL";
                $eventfilter_higher     = "NULL";
                $spwindow               = "NULL";
#               $bias_request           = "NULL";
                $most_efficient         = "NULL";
#               $fep                    = "NULL";
                $dropped_chip_count     = "NULL";
#               $secondary_exp_time     = "";
#               $frequency              = "NULL";
#               $bias_after             = "NULL";
		$multiple_spectral_lines = "NULL";
		$spectra_max_count       = "NULL";
        }

#-------------------------------------------------------------------
#-------  get values from aciswin table
#-------  first, get win_ordr to see how many orders in the database
#-------------------------------------------------------------------

        OUTER:
        for($incl= 1; $incl < 30; $incl++){
                $sqlh1 = $dbh1->prepare(qq(select ordr from aciswin where ordr=$incl and  obsid=$obsid));
                $sqlh1->execute();
                @aciswindata = $sqlh1->fetchrow_array;
                $sqlh1->finish;
                if($aciswindata[0] eq ''){
                        last OUTER;
                }
                $ordr  = $aciswindata[0];                       # here is the win_ordr
                $ordr  =~ s/\s+//g;
        }
        if($ordr =~ /\D/ || $ordr eq ''){
                $ordr = 1;
        }
#----------------------------------------------------------------------
#------- get the rest of acis window requirement data from the database
#----------------------------------------------------------------------

        $awc_l_th = 0;
        for($j =1; $j <= $ordr; $j++){
                $sqlh1 = $dbh1->prepare(qq(select
                        start_row,start_column,width,height,lower_threshold,
                        pha_range,sample,chip,include_flag
                from aciswin where ordr = $j and  obsid=$obsid));
                $sqlh1->execute();
                @aciswindata = $sqlh1->fetchrow_array;
                $sqlh1->finish;

                $start_row[$j]       = $aciswindata[0];
                $start_column[$j]    = $aciswindata[1];
                $width[$j]           = $aciswindata[2];
                $height[$j]          = $aciswindata[3];
                $lower_threshold[$j] = $aciswindata[4];
                if($lower_threshold[$j] > 0.5){
                        $awc_l_th = 1;
                }
                $pha_range[$j]       = $aciswindata[5];
                $sample[$j]          = $aciswindata[6];
                $chip[$j]            = $aciswindata[7];
                $include_flag[$j]    = $aciswindata[8];
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

        $sqlh1 = $dbh1->prepare(qq(select soe_roll from soe where obsid=$obsid));
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

        $sqlh1 = $dbh1->prepare(qq(select  
            last  from view_pi where ocat_propid=$proposal_id));
        $sqlh1->execute();
        $PI_name = $sqlh1->fetchrow_array;
        $sqlh1->finish;
    
        $sqlh1 = $dbh1->prepare(qq(select  
            last  from view_coi where ocat_propid=$proposal_id));
        $sqlh1->execute();
        $Observer = $sqlh1->fetchrow_array;
        $sqlh1->finish;
    
        if($Observer eq ""){
            $Observer = $PI_name;
        }

#-------------------------------------------------------------
#<<<<<<------>>>>>>  switch to axafusers <<<<<<------>>>>>>>>
#-------------------------------------------------------------

#        $db = "server=$server;database=axafusers";
#        $dsn1 = "DBI:Sybase:$db";
#        $dbh1 = DBI->connect($dsn1, $db_user, $db_passwd, { PrintError => 0, RaiseError => 1});
#
#--------------------------------
#-----  get proposer's last name
#--------------------------------
#
#        $sqlh1 = $dbh1->prepare(qq(select
#                last from person_short s,axafocat..prop_info p
#        where p.ocat_propid=$proposal_id and s.pers_id=p.piid));
#        $sqlh1->execute();
#        @namedata = $sqlh1->fetchrow_array;
#        $sqlh1->finish;
#
#        $PI_name = $namedata[0];
#
#---------------------------------------------------------------------------
#------- if there is a co-i who is observer, get them, otherwise it's the pi
#---------------------------------------------------------------------------
#
#        $sqlh1 = $dbh1->prepare(qq(select
#                coi_contact from person_short s,axafocat..prop_info p
#        where p.ocat_propid = $proposal_id));
#        $sqlh1->execute();
#        ($observerdata) = $sqlh1->fetchrow_array;
#        $sqlh1->finish;
#
#        if ($observerdata =~/N/){
#                $Observer = $PI_name;
#        } else {
#                $sqlh1 = $dbh1->prepare(qq(select
#                        last from person_short s,axafocat..prop_info p
#                where p.ocat_propid = $proposal_id and p.coin_id = s.pers_id));
#                $sqlh1->execute();
#                ($observerdata) = $sqlh1->fetchrow_array;
#                $sqlh1->finish;
#
#                $Observer=$observerdata;
#        }

#-------------------------------------------------
#---- Disconnect from the server
#-------------------------------------------------

        $dbh1->disconnect();


#-----------------------------------------------------------------
#------ these ~100 lines are to remove the whitespace from most of
#------ the obscat dump entries.
#-----------------------------------------------------------------
        $targid                 =~ s/\s+//g;
        $seq_nbr                =~ s/\s+//g;
        $targname               =~ s/\s+//g;
        $obj_flag               =~ s/\s+//g;
        if($obj_flag            =~ /NONE/){
                $obj_flag       = "NO";
        }
        $object                 =~ s/\s+//g;
        $si_mode                =~ s/\s+//g;
        $photometry_flag        =~ s/\s+//g;
        $vmagnitude             =~ s/\s+//g;
        $ra                     =~ s/\s+//g;
        $dec                    =~ s/\s+//g;
        $est_cnt_rate           =~ s/\s+//g;
        $forder_cnt_rate        =~ s/\s+//g;
        $y_det_offset           =~ s/\s+//g;
        $z_det_offset           =~ s/\s+//g;
        $raster_scan            =~ s/\s+//g;
        $defocus                =~ s/\s+//g;
        $dither_flag            =~ s/\s+//g;
        $roll                   =~ s/\s+//g;
        $roll_tolerance         =~ s/\s+//g;
        $approved_exposure_time =~ s/\s+//g;
        $pre_min_lead           =~ s/\s+//g;
        $pre_max_lead           =~ s/\s+//g;
        $pre_id                 =~ s/\s+//g;
        $seg_max_num            =~ s/\s+//g;
        $aca_mode               =~ s/\s+//g;
        $phase_constraint_flag  =~ s/\s+//g;
        $proposal_id            =~ s/\s+//g;
        $acisid                 =~ s/\s+//g;
        $hrcid                  =~ s/\s+//g;
        $grating                =~ s/\s+//g;
        $instrument             =~ s/\s+//g;
        $rem_exp_time           =~ s/\s+//g;
        #$soe_st_sched_date     =~ s/\s+//g;
        $type                   =~ s/\s+//g;
        #$lts_lt_plan           =~ s/\s+//g;
        $mpcat_star_fidlight_file =~ s/\s+//g;
        $status                 =~ s/\s+//g;
        $data_rights            =~ s/\s+//g;
        $server_name            =~ s/\s+//g;
        $hrc_zero_block         =~ s/\s+//g;
        $hrc_timing_mode        =~ s/\s+//g;
        $hrc_si_mode            =~ s/\s+//g;
        $exp_mode               =~ s/\s+//g;
#       $standard_chips         =~ s/\s+//g;
        $ccdi0_on               =~ s/\s+//g;
        $ccdi1_on               =~ s/\s+//g;
        $ccdi2_on               =~ s/\s+//g;
        $ccdi3_on               =~ s/\s+//g;
        $ccds0_on               =~ s/\s+//g;
        $ccds1_on               =~ s/\s+//g;
        $ccds2_on               =~ s/\s+//g;
        $ccds3_on               =~ s/\s+//g;
        $ccds4_on               =~ s/\s+//g;
        $ccds5_on               =~ s/\s+//g;
        $bep_pack               =~ s/\s+//g;
        $onchip_sum             =~ s/\s+//g;
        $onchip_row_count       =~ s/\s+//g;
        $onchip_column_count    =~ s/\s+//g;
        $frame_time             =~ s/\s+//g;
        $subarray               =~ s/\s+//g;
        $subarray_start_row     =~ s/\s+//g;
        $subarray_row_count     =~ s/\s+//g;
        $subarray_frame_time    =~ s/\s+//g;
        $duty_cycle             =~ s/\s+//g;
        $secondary_exp_count    =~ s/\s+//g;
        $primary_exp_time       =~ s/\s+//g;
        $secondary_exp_time     =~ s/\s+//g;
        $eventfilter            =~ s/\s+//g;
        $eventfilter_lower      =~ s/\s+//g;
        $eventfilter_higher     =~ s/\s+//g;

	$multiple_spectral_lines =~ s/\s+//g;
	$spectra_max_count       =~ s/\s+//g;

        $spwindow               =~ s/\s+//g;
	$multitelescope_interval=~ s/\s+//g;
        $phase_period           =~ s/\s+//g;
        $phase_epoch            =~ s/\s+//g;
        $phase_start            =~ s/\s+//g;
        $phase_end              =~ s/\s+//g;
        $phase_start_margin     =~ s/\s+//g;
        $phase_end_margin       =~ s/\s+//g;
        $PI_name                =~ s/\s+//g;
        $proposal_number        =~ s/\s+//g;
        $trans_offset           =~ s/\s+//g;
        $focus_offset           =~ s/\s+//g;
        $tooid                  =~ s/\s+//g;
        $description            =~ s/\s+//g;
        $total_fld_cnt_rate     =~ s/\s+//g;
        $extended_src           =~ s/\s+//g;
        $y_amp                  =~ s/\s+//g;
        $y_freq                 =~ s/\s+//g;
        $y_phase                =~ s/\s+//g;
        $z_amp                  =~ s/\s+//g;
        $z_freq                 =~ s/\s+//g;
        $z_phase                =~ s/\s+//g;
        $most_efficient         =~ s/\s+//g;
        $fep                    =~ s/\s+//g;
        $dropped_chip_count     =~ s/\s+//g;
        $timing_mode            =~ s/\s+//g;
        $uninterrupt            =~ s/\s+//g;
        $proposal_joint         =~ s/\s+//g;
        $proposal_hst           =~ s/\s+//g;
        $proposal_noao          =~ s/\s+//g;
        $proposal_xmm           =~ s/\s+//g;
        $roll_obsr              =~ s/\s+//g;
        $multitelescope         =~ s/\s+//g;
        $observatories          =~ s/\s+//g;
        $too_type               =~ s/\s+//g;
        $too_start              =~ s/\s+//g;
        $too_stop               =~ s/\s+//g;
        $too_followup           =~ s/\s+//g;
        $roll_flag              =~ s/\s+//g;
        $window_flag            =~ s/\s+//g;
        $constr_in_remarks      =~ s/\s+//g;
        $group_id               =~ s/\s+//g;
        $obs_ao_str             =~ s/\s+//g;

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
#               $tstart[$k]            =~ s/\s+//g;
#               $tstop[$k]             =~ s/\s+//g;
        }

        for($k = 1; $k <= $ordr; $k++){
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

        $ra   = sprintf("%3.6f", $ra);          # setting to 6 digit after a dicimal point
        $dec  = sprintf("%3.6f", $dec);
        $dra  = $ra;
        $ddec = $dec;

#---------------------------------------------------------------------------
#------- time need to be devided into year, month, day, and time for display
#---------------------------------------------------------------------------

        for($k = 1; $k <= $time_ordr; $k++){
                if($tstart[$k] ne ''){
                        $input_time      = $tstart[$k];
                        mod_time_format();              # sub mod_time_format changes time format
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


        if($roll_flag    eq 'NULL')     {$droll_flag = 'NULL'}
        elsif($roll_flag eq '')         {$droll_flag = 'NULL'; $roll_flag = 'NULL';}
        elsif($roll_flag eq 'Y')        {$droll_flag = 'YES'}
        elsif($roll_flag eq 'N')        {$droll_flag = 'NO'}
        elsif($roll_flag eq 'P')        {$droll_flag = 'PREFERENCE'}

        if($window_flag    eq 'NULL')   {$dwindow_flag = 'NULL'}
        elsif($window_flag eq '')       {$dwindow_flag = 'NULL'; $window_flag = 'NULL';}
        elsif($window_flag eq 'Y')      {$dwindow_flag = 'YES'}
        elsif($window_flag eq 'N')      {$dwindow_flag = 'NO'}
        elsif($window_flag eq 'P')      {$dwindow_flag = 'PREFERENCE'}

        if($dither_flag    eq 'NULL')   {$ddither_flag = 'NULL'}
        elsif($dither_flag eq '')       {$ddither_flag = 'NULL'; $dither_flag = 'NULL';}
        elsif($dither_flag eq 'Y')      {$ddither_flag = 'YES'}
        elsif($dither_flag eq 'N')      {$ddither_flag = 'NO'}

        if($uninterrupt    eq 'NULL')   {$duninterrupt = 'NULL'}
        elsif($uninterrupt eq '')       {$duninterrupt = 'NULL'; $uninterrupt = 'NULL';}
        elsif($uninterrupt eq 'N')      {$duninterrupt = 'NO'}
        elsif($uninterrupt eq 'Y')      {$duninterrupt = 'YES'}
        elsif($uninterrupt eq 'P')      {$duninterrupt = 'PREFERENCE'}

        if($photometry_flag    eq 'NULL')       {$dphotometry_flag = 'NULL'}
        elsif($photometry_flag eq '')           {$dphotometry_flag = 'NULL'; $photometry_flag = 'NULL'}
        elsif($photometry_flag eq 'Y')          {$dphotometry_flag = 'YES'}
        elsif($photometry_flag eq 'N')          {$dphotometry_flag = 'NO'}

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

        if($ordr =~ /\W/ || $ordr == '') {
                $ordr = 1;
        }

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
#       open(FH, "$ocat_dir/ccd_settings");
#       $ver = 0;
#       while(<FH>){
#               chomp $_;
#               if($_ !~ /\#/){
#                       @atemp = split(/\s+/, $_);
#                       if($atemp[0] == $obsid){
#                               if($atemp[2] >= $ver){
#                                       $ccd_settings = $atemp[4];
#                                       $ver++;
#                               }
#                       }
#               }
#       }
#       close(FH);
#
#       @ccd_opt_chk = split(/:/, $ccd_settings);
#       if($ccd_opt_chk[0] =~ /OPT/){
#                       $ccdi0_on  = $ccd_opt_chk[0];
#                       $dccdi0_on = $ccd_opt_chk[0];
#       }
#       if($ccd_opt_chk[1] =~ /OPT/){
#                       $ccdi1_on  = $ccd_opt_chk[1];
#                       $dccdi1_on = $ccd_opt_chk[1];
#       }
#       if($ccd_opt_chk[2] =~ /OPT/){
#                       $ccdi2_on  = $ccd_opt_chk[2];
#                       $dccdi2_on = $ccd_opt_chk[2];
#       }
#       if($ccd_opt_chk[3] =~ /OPT/){
#                       $ccdi3_on  = $ccd_opt_chk[3];
#                       $dccdi3_on = $ccd_opt_chk[3];
#       }
#       if($ccd_opt_chk[4] =~ /OPT/){
#                       $ccds0_on  = $ccd_opt_chk[4];
#                       $dccds0_on = $ccd_opt_chk[4];
#       }
#       if($ccd_opt_chk[5] =~ /OPT/){
#                       $ccds1_on  = $ccd_opt_chk[5];
#                       $dccds1_on = $ccd_opt_chk[5];
#       }
#       if($ccd_opt_chk[6] =~ /OPT/){
#                       $ccds2_on  = $ccd_opt_chk[6];
#                       $dccds2_on = $ccd_opt_chk[6];
#       }
#       if($ccd_opt_chk[7] =~ /OPT/){
#                       $ccds3_on  = $ccd_opt_chk[7];
#                       $dccds3_on = $ccd_opt_chk[7];
#       }
#       if($ccd_opt_chk[8] =~ /OPT/){
#                       $ccds4_on  = $ccd_opt_chk[8];
#                       $dccds4_on = $ccd_opt_chk[8];
#       }
#       if($ccd_opt_chk[9] =~ /OPT/){
#                       $ccds5_on  = $ccd_opt_chk[9];
#                       $dccds5_on = $ccd_opt_chk[9];
#       }
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

        if($multiple_spectral_lines eq 'NULL') {$dmultiple_spectral_lines = 'NULL'}
        elsif($multiple_spectral_lines eq '')  {$dmultiple_spectral_lines = 'NULL'; $multiple_spectral_lines = 'NULL'}
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
                UNINTERRUPT,OBJ_FLAG,OBJECT,PHOTOMETRY_FALG,VMAGNITUDE,EST_CNT_RATE,
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
		MULTIPLE_SPECTRAL_LINES, SPECTRA_MAX_COUNT,                                             #--- added 03/29/11
                EVENTFILTER_HIGHER,SPWINDOW,ORDR, FEP,DROPPED_CHIP_COUNT, BIAS_RREQUEST,
                TOO_ID,TOO_TRIG,TOO_TYPE,TOO_START,TOO_STOP,TOO_FOLLOWUP,TOO_REMARKS,
                REMARKS,COMMENTS,
                MONITOR_FLAG,                           #---- this one is added 3/1/06
		MULTITELESCOPE_INTERVAL			#---- this one is added 9/2/08
#---removed IDs
#               WINDOW_CONSTRAINT,TSTART,TSTOP,
#               ROLL_CONSTRAINT,ROLL_180,ROLL,ROLL_TOLERANCE,
#               STANDARD_CHIPS,
#               SUBARRAY_FRAME_TIME,
#               SECONDARY_EXP_TIME,
#               CHIP,INCLUDE_FLAG,START_ROW,START_COLUMN,HEIGHT,WIDTH,
#               LOWER_THRESHOLD,PHA_RANGE,SAMPLE,
#               FREQUENCY,BIAS_AFTER,
                );

#--------------------------------------------------
#----- all the param names passed between cgi pages
#--------------------------------------------------

                @paramarray = (
                SI_MODE,
                INSTRUMENT,GRATING,TYPE,PI_NAME,OBSERVER,APPROVED_EXPOSURE_TIME,
                RA,DEC,ROLL_OBSR,Y_DET_OFFSET,Z_DET_OFFSET,TRANS_OFFSET,FOCUS_OFFSET,DEFOCUS,
                DITHER_FLAG,Y_AMP, Y_FREQ, Y_PHASE, Z_AMP, Z_FREQ, Z_PHASE,Y_AMP_ASEC, Z_AMP_ASEC,
                Y_FREQ_ASEC, Z_FREQ_ASEC, UNINTERRUPT,OBJ_FLAG,OBJECT,PHOTOMETRY_FALG,
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
                EVENTFILTER_HIGHER,SPWINDOW,ORDR,
		MULTIPLE_SPECTRAL_LINES, SPECTRA_MAX_COUNT,                                             #--- added 03/29/11
                REMARKS,COMMENTS, ACISTAG,ACISWINTAG,SITAG,GENERALTAG,
                DROPPED_CHIP_COUNT, GROUP_ID, MONITOR_FLAG
#---- removed IDs
#               STANDARD_CHIPS,
#               SUBARRAY_FRAME_TIME,
#               SECONDARY_EXP_TIME,
#               FREQUENCY,BIAS_AFTER,
#               WINDOW_CONSTRAINT,TSTART,TSTOP,
#               ROLL_CONSTRAINT,ROLL_180,ROLL,ROLL_TOLERANCE,
#               CHIP,INCLUDE_FLAG,START_ROW,START_COLUMN,HEIGHT,WIDTH,
#               LOWER_THRESHOLD,PHA_RANGE,SAMPLE,
#               BIAS_RREQUEST,FEP,


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
#               SI_MODE,
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
		MULTIPLE_SPECTRAL_LINES, SPECTRA_MAX_COUNT     #--- added 03/29/11
#---- removed IDs
#               STANDARD_CHIPS,
#               SUBARRAY_FRAME_TIME,
#               SECONDARY_EXP_TIME,
#               FREQUENCY,BIAS_AFTER,
#               BIAS_REQUEST, FEP,
                );

#---------------------------------------
#----- all the param in acis window data
#---------------------------------------

        @aciswinarray=(START_ROW,START_COLUMN,HEIGHT,WIDTH,LOWER_THRESHOLD,
                       PHA_RANGE,SAMPLE,ORDR,CHIP,
#                       INCLUDE_FLAG
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
                        MULTITELESCOPE, OBSERVATORIES,MULTITELESCOPE_INTERVAL, 
			ROLL_CONSTRAINT, WINDOW_CONSTRAINT,
                        ROLL_ORDR, TIME_ORDR, ROLL_180,CONSTR_IN_REMARKS,ROLL_FLAG,WINDOW_FLAG,
                        MONITOR_FLAG
                );

#-------------------------------
#------ save the original values
#-------------------------------

        foreach $ent (@namearray){
                $lname    = lc ($ent);
                $wname    = 'orig_'."$lname";           # for the original value, all variable name start from "orig_"
                ${$wname} = ${$lname};
        }

#-------------------------------------
#------------------     special cases
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
#               $tstart[$j]      = 'NULL';
#               $tstop[$j]       = 'NULL';
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

#----------------------------------------------
#------ special treatment for roll requirements
#----------------------------------------------

        for($j = 1; $j <= $roll_ordr; $j++){            # make sure that all entries have some values for each order
                if($roll_constraint[$j] eq ''){ $roll_constraint[$j] = 'NULL'}
                if($roll_180[$j] eq ''){$roll_180[$j] = 'NULL'}
        }

        $proll_ordr = $roll_ordr + 1;

        for($j = $proll_ordr; $j < 30; $j++){           # set default values up to order < 30, assuming that
                $roll_constraint[$j] = 'NULL';          # we do not get the order larger than 29
                $roll_180[$j]        = 'NULL';
                $roll[$j]            = '';
                $roll_tolerance[$j]  = '';
        }

        for($j = 1; $j < 30; $j++){                     # save them as the original values
                $orig_roll_constraint[$j] = $roll_constraint[$j];
                $orig_roll_180[$j]        = $roll_180[$j];
                $orig_roll[$j]            = $roll[$j];
                $orig_roll_tolerance[$j]  = $roll_tolerance[$j];
        }

#--------------------------------------------
#----- special treatment for acis window data
#--------------------------------------------

        for($j = 1; $j <= $ordr; $j++){
                if($chip[$j] eq '') {$chip[$j] = 'NULL'}
                if($chip[$j] eq 'N'){$chip[$j] = 'NULL'}
                if($include_flag[$j] eq '') {$dinclude_flag[$j] = 'INCLUDE'; $include_flag[$j] = 'I'}
                if($include_flag[$j] eq 'I'){$dinclude_flag[$j] = 'INCLUDE'}
                if($include_flag[$j] eq 'E'){$dinclude_flag[$j] = 'EXCLUDE'}
        }

        $pordr = $ordr + 1;

        for($j = $pordr; $j < 30; $j++){
                $chip[$j] = 'NULL';
                $include_flag[$j] = 'I';
        }

        for($j = 1; $j < 30; $j++){
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

        $scheduled_roll = ${planned_roll.$obsid}{planned_roll}[0];

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
		if($window_constraint[$j] eq 'NONE'){$window_constraint[$j] = 'N'}
		elsif($window_constraint[$j] eq 'NULL'){$window_constraint[$j] = 'NULL'}
		elsif($window_constraint[$j] eq 'CONSTRAINT'){$window_constraint[$j] = 'Y'}
		elsif($window_constraint[$j] eq 'PREFERENCE'){$window_constraint[$j] = 'P'}
	}

#----------------------
#---- roll order cases
#----------------------

	for($j = 1; $j <= $roll_ordr; $j++){
		if($roll_constraint[$j] eq 'NONE'){$roll_constraint[$j] = 'N'}
		elsif($roll_constraint[$j] eq 'NULL'){$roll_constraint[$j] = 'NULL'}
		elsif($roll_constraint[$j] eq 'CONSTRAINT'){$roll_constraint[$j] = 'Y'}
		elsif($roll_constraint[$j] eq 'PREFERENCE'){$roll_constraint[$j] = 'P'}
		elsif($roll_constraint[$j] eq ''){$roll_constraint[$j] = 'NULL'}

		if($roll_180[$j] eq 'NULL'){$roll_180[$j] = 'NULL'}
		elsif($roll_180[$j] eq 'NO'){$roll_180[$j] = 'N'}
		elsif($roll_180[$j] eq 'YES'){$roll_180[$j] = 'Y'}
		elsif($roll_180[$j] eq ''){$roll_180[$j] = 'NULL'}
	}
#-------------------
#--- aciswin cases
#-------------------

	for($j = 1; $j <= $ordr; $j++){
		if($include_flag[$j] eq 'INCLUDE'){$include_flag[$j] = 'I'}
		elsif($include_flag[$j] eq 'EXCLUDE'){$include_flag[$j] = 'E'}
	}
		
#----------------------------------------------------------------
#----------- these have different values shown in Ocat Data Page
#----------- find database values for them
#----------------------------------------------------------------
	
	if($proposal_joint eq 'NULL'){$proposal_joint = 'NULL'}
	elsif($proposal_joint eq 'YES'){$proposal_joint = 'Y'}
	elsif($proposal_joint eq 'NO'){$proposal_joint = 'N'}
	
	if($roll_flag eq 'NULL'){$roll_flag = 'NULL'}
	elsif($roll_flag eq 'YES'){$roll_flag = 'Y'}
	elsif($roll_flag eq 'NO'){$roll_flag = 'N'}
	elsif($roll_flag eq 'PREFERENCE'){$roll_flag = 'P'}
	
	if($window_flag eq 'NULL'){$window_flag = 'NULL'}
	elsif($window_flag eq 'YES'){$window_flag = 'Y'}
	elsif($window_flag eq 'NO'){$window_flag = 'N'}
	elsif($window_flag eq 'PREFERENCE'){$window_flag = 'P'}
	
	if($dither_flag eq 'NULL'){$dither_flag = 'NULL'}
	elsif($dither_flag eq 'YES'){$dither_flag = 'Y'}
	elsif($dither_flag eq 'NO'){$dither_flag = 'N'}
	
	if($uninterrupt eq 'NULL'){$uninterrupt = 'NULL'}
	elsif($uninterrupt eq 'NO'){$uninterrupt ='N'}
	elsif($uninterrupt eq 'YES'){$uninterrupt ='Y'}
	elsif($uninterrupt eq 'PREFERENCE'){$uninterrupt = 'P'}
	
	if($photometry_flag eq 'NULL'){$photometry_flag = 'NULL'}
	elsif($photometry_flag eq 'YES'){$photometry_flag = 'Y'}
	elsif($photometry_flag eq 'NO'){$photometry_flag = 'N'}

	if($multitelescope eq 'NO'){$multitelescope = 'N'}
	elsif($multitelescope eq 'YES'){$multitelescope = 'Y'}
	elsif($multitelescope eq 'PREFERENCE'){$multitelescope = 'P'}
	
	if($hrc_zero_block eq 'NULL'){$hrc_zero_block = 'NULL'}
	elsif($hrc_zero_block eq 'YES'){$hrc_zero_block = 'Y'}
	elsif($hrc_zero_block eq 'NO'){$hrc_zero_block = 'N'}
	
	if($hrc_timing_mode eq 'NULL'){$hrc_timing_mode = 'NULL'}
	elsif($hrc_timing_mode eq 'YES'){$hrc_timing_mode = 'Y'}
	elsif($hrc_timing_mode eq 'NO'){$hrc_timing_mode = 'N'}
	
	if($most_efficient eq 'NULL'){$most_efficient = 'NULL'}
	elsif($most_efficient eq 'YES'){$most_efficient = 'Y'}
	elsif($most_efficient eq 'NO'){$most_efficient = 'N'}
	
	if($standard_chips eq 'NULL'){$standard_chips = 'NULL'}
	elsif($standard_chips eq 'YES'){$standard_chips = 'Y'}
	elsif($standard_chips eq 'NO'){$standard_chips = 'N'}
	
	if($onchip_sum eq 'NULL'){$onchip_sum = 'NULL'}
	elsif($onchip_sum eq 'YES'){$onchip_sum = 'Y'}
	elsif($onchip_sum eq 'NO'){$onchip_sum = 'N'}
	
	if($duty_cycle eq 'NULL'){$duty_cycle = 'NULL'}
	elsif($duty_cycle eq 'YES'){$duty_cycle = 'Y'}
	elsif($duty_cycle eq 'NO') {$duty_cycle = 'N'}
	
	if($eventfilter eq 'NULL'){$eventfilter = 'NULL'}
	elsif($eventfilter eq 'YES'){$eventfilter = 'Y'}
	elsif($eventfilter eq 'NO'){$eventfilter  = 'N'}

        if($multiple_spectral_lines    eq 'NULL')  {$multiple_spectral_lines = 'NULL'}
        elsif($multiple_spectral_lines eq 'YES')   {$multiple_spectral_lines = 'Y'}
        elsif($multiple_spectral_lines eq 'NO')    {$multiple_spectral_lines = 'N'}
	
	if($spwindow eq 'NULL'){$spwindow = 'NULL'}
	elsif($spwindow eq 'YES'){$spwindow = 'Y'}
	elsif($spwindow eq 'NO'){$spwindow = 'N'}
	
	if($phase_constraint_flag eq 'NULL'){$phase_constraint_flag = 'NULL'}
	elsif($phase_constraint_flag eq 'NONE'){$phase_constraint_flag = 'N'}
	elsif($phase_constraint_flag eq 'CONSTRAINT'){$phase_constraint_flag = 'Y'}
	elsif($phase_constraint_flag eq 'PREFERENCE'){$phase_constraint_flag = 'P'}
	
	if($window_constrint eq 'NONE'){$window_constrint = 'N'}
	elsif($window_constrint eq 'NULL'){$window_constrint = 'NULL'}
	elsif($window_constrint eq 'CONSTRAINT'){$window_constrint = 'Y'}
	elsif($window_constrint eq 'PREFERENCE'){$window_constrint = 'P'}
	
	if($constr_in_remarks eq 'YES'){$constr_in_remarks = 'Y'}
	elsif($constr_in_remarks eq 'PREFERENCE'){$constr_in_remarks = 'P'}
	elsif($constr_in_remarks eq 'NO'){$constr_in_remarks = 'N'}
	
	if($ccdi0_on eq 'NULL'){$ccdi0_on = 'NULL'}
	elsif($ccdi0_on eq 'YES'){$ccdi0_on = 'Y'}
	elsif($ccdi0_on eq 'NO'){$ccdi0_on = 'N'}
	
	if($ccdi1_on eq 'NULL'){$ccdi1_on = 'NULL'}
	elsif($ccdi1_on eq 'YES'){$ccdi1_on = 'Y'}
	elsif($ccdi1_on eq 'NO'){$ccdi1_on = 'N'}
	
	if($ccdi2_on eq 'NULL'){$ccdi2_on = 'NULL'}
	elsif($ccdi2_on eq 'YES'){$ccdi2_on = 'Y'}
	elsif($ccdi2_on eq 'NO'){$ccdi2_on = 'N'}
	
	if($ccdi3_on eq 'NULL'){$ccdi3_on = 'NULL'}
	elsif($ccdi3_on eq 'YES'){$ccdi3_on = 'Y'}
	elsif($ccdi3_on eq 'NO'){$ccdi3_on = 'N'}
	
	if($ccds0_on eq 'NULL'){$ccds0_on = 'NULL'}
	elsif($ccds0_on eq 'YES'){$ccds0_on = 'Y'}
	elsif($ccds0_on eq 'NO'){$ccds0_on = 'N'}
	
	if($ccds1_on eq 'NULL'){$ccds1_on = 'NULL'}
	elsif($ccds1_on eq 'YES'){$ccds1_on = 'Y'}
	elsif($ccds1_on eq 'NO'){$ccds1_on = 'N'}
	
	if($ccds2_on eq 'NULL'){$ccds2_on = 'NULL'}
	elsif($ccds2_on eq 'YES'){$ccds2_on = 'Y'}
	elsif($ccds2_on eq 'NO'){$ccds2_on = 'N'}
	
	if($ccds3_on eq 'NULL'){$ccds3_on = 'NULL'}
	elsif($ccds3_on eq 'YES'){$ccds3_on = 'Y'}
	elsif($ccds3_on eq 'NO'){$ccds3_on = 'N'}
	
	if($ccds4_on eq 'NULL'){$ccds4_on = 'NULL'}
	elsif($ccds4_on eq 'YES'){$ccds4_on = 'Y'}
	elsif($ccds4_on eq 'NO'){$ccds4_on = 'N'}
	
	if($ccds5_on eq 'NULL'){$ccds5_on = 'NULL'}
	elsif($ccds5_on eq 'YES'){$ccds5_on = 'Y'}
	elsif($ccds5_on eq 'NO'){$ccds5_on = 'N'}
	
	read_user_name();					# read registered user name
	
	$usr_ind = 0;
	$usr_cnt = 0;
	@list_of_user = @user_name;
	if($usint_on =~ /yes/){
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

        print "<B> The user: <font color=magenta>$submitter</font> is not in our database </B>";
	print "<b> Please go back and enter a correct one</b>";

        print "</FORM>";
        print "</BODY>";
        print "</HTML>";
}

###################################################################################
### submit_entry: check and submitting the modified input values                ###
###################################################################################

sub submit_entry{


# counters
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
			print "<INPUT TYPE=\"hidden\" NAME=\"$ent\" VALUE=\"$new_value\">";
		}
	}

#-------------------------
#------ hidden values here
#-------------------------

	print "<INPUT TYPE=\"hidden\" NAME=\"ASIS\" VALUE=\"$asis\">";
	print "<INPUT TYPE=\"hidden\" NAME=\"CLONE\" VALUE=\"$clone\">";
	print "<INPUT TYPE=\"hidden\" NAME=\"SUBMITTER\" VALUE=\"$submitter\">";
	print "<INPUT TYPE=\"hidden\" NAME=\"USER\" VALUE=\"$submitter\">";
	print "<INPUT TYPE=\"hidden\" NAME=\"SI_MODE\" VALUE=\"$si_mode\">";
	print "<INPUT TYPE=\"hidden\" NAME=\"email_address\" VALUE=\"$email_address\">";

#----------------------------
#------ time constraint cases
#----------------------------

	print "<INPUT TYPE=\"hidden\" NAME=\"TIME_ORDR\" VALUE=\"$time_ordr\">";
	for($j = 1; $j <= $time_ordr; $j++){
		foreach $ent ('START_DATE', 'START_MONTH', 'START_YEAR', 'START_TIME',
			       'END_DATE',  'END_MONTH',   'END_YEAR',   'END_TIME',
			       'WINDOW_CONSTRAINT'){
			$name = "$ent"."$j";
			$lname = lc ($ent);
			$val  = ${$lname}[$j];
			print "<INPUT TYPE=\"hidden\" NAME=\"$name\" VALUE=\"$val\">";
		}
	}

#-----------------------------
#------ roll constraint cases
#-----------------------------

	print "<INPUT TYPE=\"hidden\" NAME=\"ROLL_ORDR\" VALUE=\"$roll_ordr\">";
	for($j = 1; $j <= $roll_ordr; $j++){
		foreach $ent('ROLL_CONSTRAINT','ROLL_180','ROLL','ROLL_TOLERANCE'){
			$name = "$ent"."$j";
			$lname = lc ($ent);
			$val  = ${$lname}[$j];
			print "<INPUT TYPE=\"hidden\" NAME=\"$name\" VALUE=\"$val\">";
		}
	}

#-------------------------
#------- acis window cases
#-------------------------

	print "<INPUT TYPE=\"hidden\" NAME=\"ORDR\" VALUE=\"$ordr\">";
	for($j = 1; $j <=$ordr; $j++){
		foreach $ent ('CHIP','INCLUDE_FLAG','START_ROW','START_COLUMN','HEIGHT','WIDTH',
				'LOWER_THRESHOLD','PHA_RANGE','SAMPLE'){
			$name = "$ent"."$j";
			$lname = lc ($ent);
			$val  = ${$lname}[$j];
			print "<INPUT TYPE=\"hidden\" NAME=\"$name\" VALUE=\"$val\">";
		}
	}

#-------------------------------------------#
#-------------------------------------------#
#-------- ASIS and REMOVE case starts ------#
#-------------------------------------------#
#-------------------------------------------#

   if ($asis eq "ASIS" || $asis eq "REMOVE"){

#------------------------------------------------------
#---- start writing email to the user about the changes
#------------------------------------------------------

    	open (FILE, ">$temp_dir/$obsid.tmp");		# a temp file which email to a user written in.

    	print FILE "OBSID    = $obsid\n";
    	print FILE "SEQNUM   = $seq_nbr\n";
    	print FILE "TARGET   = $targname\n";
    	print FILE "USERNAME = $submitter\n";
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
   
	open (PARAMLINE, ">>$temp_dir/$obsid.tmp");
	foreach $nameagain (@paramarray){

		$lc_name = lc ($nameagain);
		$old_name = 'orig_'."$lc_name";
		$old_value = ${$old_name};

    		unless (($lc_name =~/TARGNAME/i) || ($lc_name =~/TITLE/i)
			||  ($lc_name =~/^WINDOW_CONSTRAINT/i) || ($lc_name =~ /^TSTART/i) || ($lc_name =~/^TSTOP/i) 
			||  ($lc_name =~/^ROLL_CONSTRAINT/i) || ($lc_name =~ /^ROLL_180/i)
			||  ($lc_name =~/^CHIP/i) || ($lc_name =~ /^INCLUDE_FLAG/i) || ($lc_name =~ /^START_ROW/i)
			||  ($lc_name =~/^START_COLUMN/i) || ($lc_name =~/^HEIGHT/i) || ($lc_name =~ /^WIDTH/i)
			||  ($lc_name =~/^LOWER_THRESHOLD/i) || ($lc_name =~ /^PHA_RANGE/i) || ($lc_name =~ /^SAMPLE/i)
			||  ($lc_name =~/^SITAG/i) || ($lc_name =~ /^ACISTAG/i) || ($lc_name =~ /^GENERALTAG/i)
			||  ($lc_name =~/ASIS/i) || ($lc_name =~ /MONITOR_FLAG/i)
			){  

#---------------------
#---- time order case
#---------------------

			if($lc_name =~ /TIME_ORDR/){
				$current_entry = $oring_time_ordr;
				write (PARAMLINE);
				for($j = 1; $j <= $orig_time_ordr; $j++){
					$nameagain = 'WINDOW_CONSTRAINT'."$j";
					$current_entry = $window_constraint[$j];
					$old_value = $orig_window_constraint[$j];
					write (PARAMLINE);
					$nameagain = 'TSTART'."$j";
					$current_entry = $tstart[$j];
					$old_value = $orig_tstart[$j];
					write (PARAMLINE);
					$nameagain = 'TSTOP'."$j";
					$current_entry = $tstop[$j];
					$old_value = $orig_tstop[$j];
					write (PARAMLINE);
				}

#--------------------
#--- roll order case
#--------------------

			}elsif ($lc_name =~ /ROLL_ORDR/){
				$current_entry = $orig_roll_ordr;
				write(PARAMLINE);
				for($j = 1; $j <= $orig_roll_ordr; $j++){
					$nameagain = 'ROLL_CONSTRAINT'."$j";
					$current_entry = $roll_constraint[$j];
					$old_value = $orig_roll_constraint[$j];
					write(PARAMLINE);
					$nameagain = 'ROLL_180'."$j";
					$current_entry = $roll_180[$j];
					$old_value = $orig_roll_180[$j];
					write (PARAMLINE);

					$nameagain = 'ROLL'."$j";
					$current_entry = $roll[$j];
					$old_value = $orig_roll[$j];
					write (PARAMLINE);
					$nameagain = 'ROLL_TOLERANCE'."$j";
					$current_entry = $roll_tolerance[$j];
					$old_value = $orig_roll_tolerance[$j];
					write (PARAMLINE);
				}

#--------------------------
#--- acis window order case
#--------------------------

			}elsif ($lc_name eq 'ORDR'){
				$current_entry = $orig_ordr;
				write(PARAMLINE);
				for($j = 1; $j <= $orig_ordr; $j++){
					$nameagain = 'CHIP'."$j";
					$current_entry = $chip[$j];
					write(PARAMLINE);
					$nameagain = 'INCLUDE_FLAG'."$j";
					$current_entry = $include_flag[$j];
					write(PARAMLINE);
					$nameagain = 'START_ROW'."$j";
					$current_entry = $start_row[$j];
					write(PARAMLINE);
					$nameagain = 'START_COLUMN'."$j";
					$current_entry = $start_column[$j];
					write(PARAMLINE);
					$nameagain = 'HEIGHT'."$j";
					$current_entry = $height[$j];
					write(PARAMLINE);
					$nameagain = 'WIDTH'."$j";
					$current_entry = $width[$j];
					write(PARAMLINE);
					$nameagain = 'LOWER_THRESHOLD'."$j";
					$current_entry = $lower_threshold[$j];
					write(PARAMLINE);
					$nameagain = 'PHA_RANGE'."$j";
					$current_entry = $pha_range[$j];
					write(PARAMLINE);
					$nameagain = 'SAMPLE'."$j";
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

       	print "<INPUT TYPE=\"hidden\" NAME=\"ASIS\" VALUE=\"ASIS\">";

        print "<INPUT TYPE=\"hidden\" NAME=\"access_ok\" VALUE=\"yes\">";
        print "<INPUT TYPE=\"hidden\" NAME=\"pass\" VALUE=\"$pass\">";
        print "<INPUT TYPE=\"hidden\" NAME=\"sp_user\" VALUE=\"$sp_user\">";
	print "<INPUT TYPE=\"hidden\" NAME=\"email_address\" VALUE=\"$email_address\">";
#	print hidden(-name=>'submitted_obs',-override=>"$ap_list", -value=>"$ap_list");
#	print hidden(-name=>'skipped_obs',-override=>"$sk_list", -value=>"$sk_list");

	$obsid_list = param("obsid_list");
	print "<INPUT TYPE=\"hidden\" NAME=\"obsid_list\" VALUE=\"$obsid_list\">";
	print '<br>';
	print "<INPUT TYPE=\"hidden\" NAME =\"Last_Obsid\"  VALUE=\"$obsid\">";


    	print "</FORM></BODY></HTML>";
   }
}

#########################################################################
### read_name: read descriptive name of database name		     ####
#########################################################################

sub read_name{
	open(FH, "$obs_ss/name_list");
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
	$comp     = uc ($db_name);
	OUTER:
	foreach $fent (@name_list){
		@wtemp = split(/:/, $fent);
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


#------------------------------------------------------
#-----  (scan for updates directory) read updates_table.list
#-----  find the revision number for obsid in question
#------------------------------------------------------

        open(UIN, "$ocat_dir/updates_table.list");
        @usave = ();
        $ucnt  = 0;
        while(<UIN>){
                chomp $_;
                if($_ =~ /$obsid\./){
                        @utemp = split(/\s+/, $_);
                        @vtemp = split(/\./, $utemp[0]);
                        $i_val = int ($vtemp[1]);
                        push(@usave, $i_val);
                        $ucnt++;
                }
        }
        close(UIN);

        @usorted = sort{$a<=>$b} @usave;
        $rev     = int($usorted[$ucnt-1]);
        $rev++;

        if ($rev < 10){
                $rev = "00$rev";
        } elsif (($rev >= 10) && ($rev < 100)){
                $rev = "0$rev";
        }

#-------------------------------------------------
#-----  construct mail to dutysci and CUS archive
#-------------------------------------------------

#------------------
# get the contents
#------------------
	open (OSLOG, "<$temp_dir/$obsid.tmp");
	@oslog = <OSLOG>;
	close (OSLOG);

	open (FILE, ">$temp_dir/ormail_$obsid.tmp");

	$s_yes = 0;
	$s_cnt = 0;
		
	print FILE 'Submitted as "AS IS"---Observation'."  $obsid". ' is added to the approved list',"\n";

	print FILE "@oslog";

	close FILE;


#-----------------------
#-----  get the contents
#-----------------------

	open (OSLOG, "<$temp_dir/$obsid.tmp");
	@oslog = <OSLOG>;
	close (OSLOG);

#-----------------------------
#-----  couple temp variables
#-----------------------------

    	$dutysci_status = "NA";

  	$general_status = "NULL";			# these are for the status verification page
    	$acis_status    = "NULL";			# orupdate.cgi
    	$si_mode_status = "NULL";

	$dutysci_status = "$dutysci $date";
	
	open(ASIN,"$ocat_dir/approved");

	@temp_data = ();
	while(<ASIN>){

		chomp $_;
		push(@temp_data, $_);
	}
	close(ASIN);

	system("mv $ocat_dir/approved $ocat_dir/approved~");

	open(ASIN,">$ocat_dir/approved");

	NEXT:
	foreach $ent (@temp_data){
		@atemp = split(/\t/, $ent);
		if($atemp[0] eq "$obsid"){
			next NEXT;
		}else{
			print ASIN "$ent\n";
		}
	}
	print ASIN "$obsid\t$seq_nbr\t$dutysci\t$date\n";
	close(ASIN);
	system("chmod 644 $ocat_dir/approved");

	if($usint_on =~ /test/){
#		system("chmod 777 $test_dir/approved");
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
                        print $update "$obsid.$rev\tNULL\tNULL\tNULL\t$dutysci_status\t$seq_nbr\t$dutysci\n";
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

                                system("cp  $temp_dir/$obsid.tmp $ocat_dir/updates/$obsid.$rev");

                                last OUTER;
                        }
                }
        }


#----------------------------------------------
#----  append arnold update file, if necessary
#----------------------------------------------

	if ($acistag =~/ON/){
    		open (ARNOLD, "<$temp_dir/arnold.tmp");
    		@arnold = <ARNOLD>;
    		close (ARNOLD);
    		$arnoldline = shift @arnold;
#
#--- closed 02/25/2011; the directory does not exist anymore
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
	$asis_ind = param('ASIS');
	if($send_email eq 'yes'){

		if($sp_user eq 'no'){

			open(ASIS, '>$temp_dir/asis.tmp');
			print ASIS "$obsid is approved for flight. Thank you \n";
			close(ASIS);

			if($unint_on =~ /test/){

#mail#				system("cat $temp_dir/asis.tmp |mailx -s\"Subject: $obsid is approved\n\"  $email_address");

			}else{

#mail#				system("cat $temp_dir/asis.tmp |mailx -s\"Subject: $obsid is approved\n\"  $email_address cus\@head-cfa.harvard.edu");

			}

			system("rm $temp_dir/asis.tmp");

		}else{

			if($unint_on =~ /test/){

#mail#				system("cat $temp_dir/ormail_$obsid.tmp |mailx -s\"Subject: Parameter Changes (Approved) log  $obsid.$rev\n\"  $email_address");
#mail#				system("cat $temp_dir/asis.tmp |mailx -s\"Subject: $obsid is approved\n\"  $email_address");

			}else{

#mail#				system("cat $temp_dir/ormail_$obsid.tmp |mailx -s\"Subject: Parameter Changes (Approved) log  $obsid.$rev\n\"  $email_address  cus\@head.cfa.harvard.edu");

			}
		}
	}


#--------------------------
#----  get rid of the junk
#--------------------------

	system("rm -f $temp_dir/$obsid.tmp");
	system("rm -f $temp_dir/ormail_$obsid.tmp");
	system("rm -f $temp_dir/arnold.tmp");
#	system("chmod 777 $temp_dir/Temp/*");
}

#####################################################################################
### mod_time_format: convert and devide input data format                         ###
#####################################################################################

sub mod_time_format{
	@tentry = split(/\W+/, $input_time);
	$ttcnt = 0;
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
		$hr_add = 12;
		@tatemp = split(/PM/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}elsif($tentry[$ttcnt-1] =~/pm/){
		$hr_add = 12;
		@tatemp = split(/pm/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}elsif($tentry[$ttcnt-1] =~ /AM/){
		@tatemp = split(/AM/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}elsif($tentry[$ttcnt-1] =~ /am/){
		@tatemp = split(/AM/, $tentry[$ttcnt-1]);
		$tentry[$ttcnt-1] = $tatemp[0];
	}
	
	$mon_lett = 0;
	if($tentry[0] =~ /\D/){
		$day  = $tentry[1];
		$month = $tentry[0];
		$year  = $tentry[2];
		$mon_lett = 1;
	}elsif($tentry[1] =~ /\D/){
		$day  = $tentry[0];
		$month = $tentry[1];
		$year  = $tentry[2];
		$mon_lett = 1;
	}elsif($tentry[0] =~ /\d/ && $tentry[1] =~ /\d/){
		$day  = $tentry[0];
		$month = $tentry[1];
		$year  = $tentry[2];
	}	
	
	$day = int($day);
	if($day < 10){
		$day = '0'."$day";
	}
	
	if($mon_lett > 0){
		if($month =~ /^JAN/i){$month = '01'}
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
	
	@btemp = split(//,$year);
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
			$hr = $hr + $hr_add;
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
			$hr = $hr + $hr_add;
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

       	if($ttemp[1] =~ /Jan/i){
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
		if($ttemp[2] == 2000 || $ttemp[2] == 2004 || $ttemp[2] == 2008 || $ttemp[2] == 2012){
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

#
#--- this one and the next subs are taken from target_param.cgi
#--- written by Mihoko Yukita.(10/28/2003)
#
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
        	%{planned_roll.$ptemp[0]} = (planned_roll =>["$ptemp[1]"]);

        }
        close(PFH);
}

#######################################################################################
### send_email_to_mp: sending email to MP if the obs is in an active OR list        ###
#######################################################################################

sub send_email_to_mp{

	open(IN, "$pass_dir/user_email_list");
#
#--- find out submitter's email address
#
	while(<IN>){
		chomp $_;
		@dtemp = split(/\s+/, $_);
		if($submitter eq $dtemp[0]){
			$email_address = $dtemp[3];
			last;
		}
	}
	close(IN);

        $temp_file = "$temp_dir/mp_request";
	$sot_contact = 'swolk@head.cfa.harvard.edu';
        open(ZOUT, ">$temp_file");

        print ZOUT "\n\nA user: $submitter submitted changes/approval of obsid(s):\n\n";
	foreach $ent (@mp_warn_list){
		print ZOUT "$ent\n";
	}

        print ZOUT "\n which is in the current OR list.\n\n";

        print ZOUT "The contact email_address address is: $email_address\n\n";

        print ZOUT "Its Ocat Data Page is:\n";
	foreach $obsid (@mp_warn_list){
        	print ZOUT "$usint_http/ocatdata2html.cgi?$obsid\n\n";
	}
        print ZOUT "\nIf you have any question about this email, please contact $sot_contact.\n\n\n";

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
        	system("cat $temp_file | mailx -s\"Subject: Change to Obsids Which Is in Active OR List ($mp_email)\n\"  $test_email");
	}else{
		system("cat $temp_file | mailx -s\"Subject: Change Obsids Which Is in Active OR List\n\"  $mp_email cus\@head.cfa.harvard.edu");
	}

        system("rm $temp_file");

}


#########################################################################
## check_apporved_list: check approved obsids and notify the user     ###
#########################################################################

sub check_apporved_list{

	open(FIN, "$ocat_dir/approved");

	@approved_list = ();
	while(<FIN>){
		chomp $_;
		push(@approved_list, $_);
	}
	close(FIN);
	@approved_list = reverse(@approved_list);

	@list1 = ();
	@list2 = ();
	$cnt   = 0;
	OUTER:
	foreach $ent (@obsid_list){
		$chk = 0;
		foreach $comp (@approved_list){
			@btemp = split(/\s+/, $comp);
			if($ent == $btemp[0]){
				push(@list1, $comp);
				$chk = 1;
				next OUTER;
			}	
		}
		if($chk == 0){
			push(@list2, $ent);
			$cnt++;
		}
	}

	open(AOUT, ">$temp_dir/alist.tmp");
	print AOUT "\n\nThe following obsids are added on the approved list.\n\n";
	foreach $ent (@list1){
		print AOUT "$ent\n";
	}
	print AOUT "\n\n";
	if($cnt > 0){
		print AOUT "The following obsid(s) were not added to the approved list.\n";
		print AOUT "You may want to try them again.\n";
		foreach $ent (@list2){
			print AOUT "$ent\n";
		}
	}

	if($usint_on =~ /test/i){
		system("cat $temp_dir/alist.tmp |mailx -s\"Subject: Approved Obsids by $email_address \n\"  $test_email");
	}else{
		system("cat $temp_dir/alist.tmp |mailx -s\"Subject: Approved Obsids by $email_address \n\"  $email_address  cus\@head.cfa.harvard.edu");
	}

	system("rm  $temp_dir/alist.tmp");
}


