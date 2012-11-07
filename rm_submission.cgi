#!/soft/ascds/DS.release/ots/bin/perl
use CGI qw/:standard :netscape /;

use Fcntl qw(:flock SEEK_END); # Import LOCK_* constants

#########################################################################################
#											#
# rm_submission.cgi: remove an accidental submission from database			#
#											#
# 		Author: t. isobe (tisobe@cfa.harvard.edu)				#
#		Last Update: Oct. 31, 2012 						#
# This script removes an obsid from database.    	                            	#
#											#
#########################################################################################

#
#---- if this is usint version, set the following param to 'yes', otherwise 'no'
#

#$usint_on = 'yes';                     ##### USINT Version
#$usint_on = 'no';                      ##### USER Version
$usint_on = 'test_yes';                 ##### Test Version USINT
#$usint_on = 'test_no';                 ##### Test Version USER


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

print header(-type => 'text/html; charset=utf-8');

print "<!DOCTYPE html>";
print "<html>";
print "<head>";
print "<title>Obscat Submission Cancellation  Form</title>";
print "<style  type='text/css'>";
print "table{text-align:center;margin-left:auto;margin-right:auto;border-style:solid;border-spacing:8px;border-width:2px;border-collapse:separate}";
print "a:link {color:blue;}";
print "a:visited {color:teal;}";
print "</style>";
print "</head>";


print "<body style='color:#000000;background-color:#FFFFE0'>";


print start_form();			# starting a form


#---------------------------------------------------------------------
# ----- here are non CXC GTOs who have an access to data modification.
#---------------------------------------------------------------------

@special_user = ('isobe','mta');
$no_sp_user = 2;

#######################
$usint_on = 'yes';
#$usint_on = 'no';
#######################

if($usint_on eq 'yes'){
        open(FH, "$pass_dir/usint_users");
        while(<FH>){
                chomp $_;
                @atemp = split(//,$_);
                if($atemp[0] ne '#'){
                        @btemp = split(/\s+/,$_);
                        push(@special_user, $btemp[0]);
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
        @passwd = split(/:/,$_);
        $pwd_list{"$passwd[0]"} = $passwd[1];
        push(@user_name_list, $passwd[0]);
}
close(FH);


#------------------------------------
#---- check inputed user and password
#------------------------------------

match_user();			# this sub match a user to a password

#--------------------------------------------------------------
#--------- if a user and a password do not match ask to re-type
#--------------------------------------------------------------

if($pass eq '' || $pass eq 'no'){
	if(($pass eq 'no') && ($ac_user  ne ''|| $pass_word ne '')){
		print "<h2 style='color:red;padding-bottom:10px'>Name and/or Password are not valid.";
		print " Please try again.</hr>";
	}
	password_check();	# this one create password input page

}elsif($pass eq 'yes'){		# ok a user and a password matched

	$sp_user = 'no';

#-------------------------------------------
#------ check whether s/he is a special user
#-------------------------------------------

	if($usint_on eq 'yes'){
		$sp_user = 'yes';
	}else{
		special_user();
	}
	
#-------------------------------------------------------
#----- go to the main part to print a verification page
#----- check whether there are any changes, if there are
#----- go into update_info sub to update the table
#-------------------------------------------------------

	$rm_obsrev = '';
	$rm_obsrev = param('Remove');
	if($rm_obsrev){
		update_info();		# this sub update updates_table.list
	}

	remve_submission();		# this sub creates a html page

}else{
	print '<h2 style="color:red">Something wrong. Exiting</h2>';
	exit(1);
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
	print textfield(-name=>'ac_user', -value=>'', -size=>20);
	print '</td></tr><tr><th>Password</th><td>';
	print password_field( -name=>'password', -value=>'', -size=>20);
	print '</td></tr></table><br>';
	
	print '<input type="submit" name="Check" value="Submit">';
}


#########################################################################
### match_user: check a user and a password matches                   ###
#########################################################################

sub match_user{
	$ac_user = param('ac_user');
	$ac_user =~s/^\s+//g; 
	$pass_word = param('password');
	$pass_word =~s/^\s+//g;
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

	open(FH,"$obs_ss/access_list");
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


###############################################################################################
### remve_submission: remove an submitted obsid from database				  #####
###############################################################################################


sub remve_submission{

#-------------------------------------------
#----- a couple of hidden parameters to pass
#-------------------------------------------
#	print start_form();
	print hidden(-name=>'ac_user', -vaule=>"$ac_user");
	print hidden(-name=>'password', -value=>"$password");

#------------------------------------------------------------------------------------------
#----@pass_list will hold all editable entries so that we can pass them as parameters later
#------------------------------------------------------------------------------------------
	@pass_list = ();

	print "<h2 style='text-decoration:underline'>Obs Data Submission Cancellation Page</h2>";

	print "<h3>If you need to remove an accidental submission, please choose the obsid and";
	print " and click a button from \"Remove\" side. If it says \"NO ACCESS\", it means that someone already";
	print " made parameter changes, and cannot remove that submission.</h3>";

	print "<h3 style='color:red;padding-bottom:10px'>If it is once removed, the change is permanent; be careful to select a correct one</h3>";
########
#	print "<B><A HREF=\"https://icxc.harvard.edu/cgi-bin/obs_ss/index.html\">Verification Page ";
#
#	print "Support Observation Search Form</A></B><BR>";
#	print "<B><A HREF=\"http://asc.harvard.edu/~mta/CUS/\">Chandra Uplink Support Organizational Page";
	print '<p>';
	print "<strong><a href=\"https://icxc.harvard.edu/mta/CUS/Usint/orupdate.cgi\">Back to Target Parameter Update Status Form</a></strong>";
	print '</p>';
########

#####
	open (FILE, "< $ocat_dir/updates_table.list");
	@revisions = <FILE>;
	close (FILE);
	print "<form name=\"update\" Method=\"post\" action=\"https://icxc.harvard.edu/mta/CUS/Usint/rm_submission.cgi\">";
#	print "<FORM NAME=\"update\" METHOD=\"post\" ACTION=\"http://asc.harvard.edu/cgi-gen/mta/Obscat/rm_submission.cgi\">";
#	print "<FORM NAME=\"update\" METHOD=\"post\" ACTION=\"https://icxc.harvard.edu/cgi-bin/obs_ss/rm_submission.cgi\">";
#####

	print "<div style='text-align:center;margin-left:auto;margin-right;auto;'>";
	print "<table border=1>";
	print "<tr><th>OBSID.revision</th>";
	print "<th>Remove?</th></tr>";

#---------------------------------------------------------
#----- because log is appended to, rather than added to...
#---------------------------------------------------------

	if($cancelled_line){
    		@values= split ("\t", $cancelled_line);
    		$obsrev = $values[0];
    		@atemp = split(/\./,$obsrev);
    		$obsid = $atemp[0];
    		$general_status = $values[1];
    		$acis_status = $values[2];
    		$si_mode_status = $values[3];
    		$dutysci_status = $values[4];
    		$seqnum = $values[5];
    		$user = $values[6];
    		@atemp = split(/\./,$obsrev);
    		$tempid = $atemp[0];

		print "<td>$obsrev<br />$seqnum<br />$ftime<br />$user</td>";
		print "</td><td style='color:red'>Cancelled</td></tr> ";
	}

	@revisions= reverse(@revisions);
	$today = `date '+%D'`;
	chop $today;

	foreach $line (@revisions){
    		chop $line;
    		@values= split ("\t", $line);
    		$obsrev = $values[0];
    		@atemp = split(/\./,$obsrev);
    		$obsid = $atemp[0];
    		$general_status = $values[1];
    		$acis_status = $values[2];
    		$si_mode_status = $values[3];
    		$dutysci_status = $values[4];
    		$seqnum = $values[5];
    		$user = $values[6];
    		@atemp = split(/\./,$obsrev);
    		$tempid = $atemp[0];

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
					= stat "/data/udoc1/ocat/updates/$obsrev";
#    		($na0,$na1,$na2,$na3,$na4,$na5,$na6,$na7,$na8,$mtime,$na10,$na11,$na12) 
#			= stat "/proj/ascwww/AXAF/extra/science/cgi-gen/mta/Obscat/ocat/updates/$obsrev";

#----------------
#------ get time
#----------------
    		($t0,$t1,$t2,$t3,$t4,$t5,$t6,$t7,$t8) = localtime($mtime);

    		$month = $t4 + 1;
    		$day = $t3;
    		$year = $t5 + 1900;
    		$ftime ="$month/$day/$year";

#----------------------------------------------------------------------------------------------
#---- if dutysci_status is NA (means not signed off yet), print the entry for the verification
#----------------------------------------------------------------------------------------------

    		if ($dutysci_status =~/NA/){
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
				print '<TR bgcolor=yellow>';
			}else{
				print "<TR>";
			}
##########
#			print "<TD><A HREF=\"https://icxc.harvard.edu/cgi-bin/obs_ss/chkupdata.cgi";
			print "<td><a href=\"https://icxc.harvard.edu/mta/CUS/Usint/chkupdata.cgi";
##########
			print "\?$obsrev\">$obsrev</a><br />$seqnum<br />$ftime<br />$user</td>";

			$rm_permission = 'yes';
#--------------------
#----- general obscat 
#--------------------
			if ($general_status ne 'NULL' && $general_status ne 'NA'){
	    			$rm_permission = 'no';
			}
#------------------
#----- acis obscat
#------------------
			if ($acis_status ne 'NULL' && $acis_status ne 'NA'){
	    			$rm_permission = 'no';
			}
#-------------
#----- si mode
#-------------
			if ($si_mode_status ne 'NULL' && $si_mode_status ne 'NA'){
				$rm_permission = 'no';
			}

			if($rm_permission eq 'yes'){
				print "<td><input type=\"submit\" name=\"Remove\" value=\"$obsrev\"></td></tr>";
			}else{
				print "<td style='color:red'>NO ACCESS</td></tr> ";
			}
		}
	}

#-------------------------------
#-----pass the changes as params 
#-------------------------------
	$ap_cnt = 0;
	foreach $ent (@pass_list){
		$name = 'pass_name.'."$ap_cnt";
		print hidden(-name=>"$name", -value=>"$ent");
		$ap_cnt++;
	}
	print hidden(-name=>'ap_cnt', -value=>"$ap_cnt");
	
	print "</table>";
	print "</div>";
}  

###################################################################################
### update_info: will perform updates to table                                 ####
###################################################################################

sub update_info {

	$obsline = $rm_obsrev;
	$rm_obsrev_save = "$rm_obsrev".'~';

#
#--- copy the unwated file, and save just in a case, the user want it back
#
	system("mv $ocat_dir/updates/$rm_obsrev $ocat_dir/updates/$rm_obsrev_save");

#
#--- open the table and read the data in
#
    	$j=0;
	open (INFILE, "< $ocat_dir/updates_table.list");
    	@revcopy = <INFILE>;
    	close (INFILE);
	@newoutput=();
	$last_sign = 0;
	$cancelled_line = '';
	foreach $newline (@revcopy){
               	chop $newline;
               	@newvalues= split ("\t", $newline);
               	$newobsrev = $newvalues[0];
               	$newgeneral_status = $newvalues[1];
               	$newacis_status = $newvalues[2];
               	$newsi_mode_status = $newvalues[3];
               	$newdutysci_status = $newvalues[4];
               	$newseqnum = $newvalues[5];
               	$newuser = $newvalues[6];
#-------------------------------------------
#---- there is obs id match, remove the line
#-------------------------------------------
		if($newobsrev eq $obsline){
    			$j++;
			$cancelled_line = $newline;
#---------------------------------------------
#--- id did not match; so just write the line
#---------------------------------------------
		} else {
    			$newline="$newline\n";
    			push (@newoutput,$newline);
		}
	}
#----------------------------------------------------------------------
#---- start updating the updates_table.list, if there are any changes.
#----------------------------------------------------------------------
    	if ($j == 1){
#-------------------------------------
#----  get master log file for editing
#-------------------------------------

	        $lpass = 0;
	        $wtest = 0;
	        my $efile = "$ocat_dir/updates_table.list";
	        OUTER:
	        while($lpass == 0){
	                open(my $update, '+>', $efile) or die "Locked";
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
    					print "<p><strong><span style='color:#FF0000'>ERROR: The update file is currently being edited by someone else.<br />";
    					print "Please use the back button to return to the previous page, and resubmit.<br /><br />Exiting....</span></strong></p>";

	                                exit(1);
	                        }
	                }else{
	                        $lpass = 1;
#--------------------------------------------------------------------------------------------------
#----  if it is not being edited, write update updates_table.list---data for the verificaiton page
#--------------------------------------------------------------------------------------------------

	                        flock($update, LOCK_EX) or die "died while trying to lock the file<br />\n";

	    			foreach $outline (@newoutput){

					print $update "$outline";
	    			}
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
	}
}
