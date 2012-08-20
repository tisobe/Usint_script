#!/opt/local/bin/perl

#################################################################################################################
#														#
#	oredit_sub.perl: this is a part of ocatdata2html, sub oredit. It was originally a part of it, but	#
#			 it was made to a separate entity to improve computational speed.			#
#														#
#		author: t. isobe (tisobe@cfa.harvard.edu)							#
#														#
#		last update: Oct 13, 2009									#
#														#
#################################################################################################################

#
#--- read data
#

$usint_on	= $ARGV[0];
$obsid		= $ARGV[1];
$sf		= $ARGV[2];
$asis		= $ARGV[3];
$dutysci	= $ARGV[4];
$seq_nbr	= $ARGV[5];
$generaltag	= $ARGV[6];
$acistag	= $ARGV[7];
$si_mode	= $ARGV[8];
$sitag		= $ARGV[9];
$cus_email	= $ARGV[10];
$test_email	= $ARGV[11];
$email_address	= $ARGV[12];
$sp_user	= $ARGV[13];
$large_coord	= $ARGV[14];
$asis_ind	= $ARGV[15];

chomp $usint_on;
chomp $obsid;
chomp $sf;
chomp $asis;
chomp $dutysci;
chomp $seq_nbr;
chomp $generaltag;
chomp $acistag;
chomp $si_mode;
chomp $sitag;
chomp $cus_email;
chomp $test_email;
chomp $email_address;
chomp $sp_user;
chomp $large_coord;
chomp $asis_ind;

#
#--- special treatment for si_mode tag
#

if($si_mode eq 'na'){
	$si_mode = '';
}

#
#---- set directory pathes
#

$obs_ss   = '/proj/web-icxc/cgi-bin/obs_ss/';             #--- none usint user site
$pass_dir = '/proj/web-icxc/cgi-bin/obs_ss/.Pass_dir/';   #--- a directory contatins user name file etc
$temp_dir = '/data/mta4/www/CUS/Usint/Temp/';             #--- a temporary file is created in this d irectory
$data_dir = './';


#
#--- if this is a test case, use the first directory, otherwise use the real one
#

if($usint_on =~ /test/i){
        $ocat_dir = '/proj/web-cxc/cgi-gen/mta/Obscat/ocat/';
}else{
        $ocat_dir = '/data/udoc1/ocat/';
}

#
#--- set html pages
#

$usint_http   = 'https://icxc.harvard.edu/cus/index.html';      #--- web site for usint users
$obs_ss_http  = 'https://icxc.harvard.edu/cgi-bin/obs_ss/';     #--- web site for none usint users (GO Expert etc)
$test_http    = 'http://asc.harvard.edu/cgi-gen/mta/Obscat/';   #--- web site for test

$mp_http      = 'http://asc.harvard.edu/';                      #--- web site for mission planning related
$chandra_http = 'http://cxc.harvard.edu/';                      #--- chandra main web site
$cdo_http     = 'https://icxc.harvard.edu/cgi-bin/cdo/';        #--- CDO web site

############################
#----- end of settings
############################


#
#--- call the main (and only) sub script
#

oredit_sub();


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

#-------------------------------------
#----  get master log file for editing
#-------------------------------------

	chdir "$ocat_dir";
	system("chmod 777 $ocat_dir/SCCS/*");
	$wtest = 0;
	OUTER:
	while($wtest == 0){
		$status = `/usr/ccs/bin/sccs   info $ocat_dir`;


		if ($status =~ /Nothing being edited/ig){
			$checkout = `/usr/ccs/bin/sccs edit $ocat_dir/updates_table.list`;

#--------------------------------------------------------------------------------------------------
#----  if it is not being edited, write update updates_table.list---data for the verificaiton page
#--------------------------------------------------------------------------------------------------

	
			open (UPDATE, ">>$ocat_dir/updates_table.list");

			print UPDATE "$obsid.$rev\t$general_status\t$acis_status\t$si_mode_status\t$dutysci_status\t$seq_nbr\t$dutysci\n";
    			close UPDATE;

#---------------------
#----  checkin update
#---------------------

			$checkin = `/usr/ccs/bin/sccs delget -y $ocat_dir/updates_table.list`;

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
#
#--- wait 5 cpu seconds before attempt to check in another round
#
		$diff  = 0;
		$start = (times)[0];
		while($diff < 5){
			$end  = (times)[0];
			$diff = $end - $start;
		}

		$wtest++;
		if($wtest > 300){
			exit();
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
    		open (ARNOLDUPDATE, ">>/home/arcops/ocatMods/acis");
    		print ARNOLDUPDATE "$arnoldline";
    		close (ARNOLDUPDATE);
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
					system("cat $temp_dir/asis.$sf |mailx -s\"Subject:TEST!!  $obsid is approved\n\" -r$cus_email $test_email");
				}else{
					system("cat $temp_dir/asis.$sf |mailx -s\"Subject: $obsid is approved\n\" -r$cus_email -c$cus_email $email_address");
				}
				system("rm $temp_dir/asis.$sf");
			}else{
				if($usint_on =~ /test/){
					system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject:TEST!! Parameter Changes (Approved) log  $obsid.$rev\n\" -r$cus_email  $test_email");
				}else{
					system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes (Approved) log  $obsid.$rev\n\" -r$cus_email -c$cus_email $email_address");
				}
			}

			if($usint_on ne 'test' && $usint_on ne 'test_no'){ system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes (Approved) log  $obsid.$rev\n\" -r$cus_email  $cus_email");
			}
		}else{
			if($sp_user eq 'no'){
				open(USER, ">$temp_dir/user.$sf");
				print USER "Your change request for obsid $obsid have been received.\n";
				print USER "You will be notified when the changes have been made.\n";
				close(USER);

				if($usint_on =~ /test/){
					system("cat $temp_dir/user.$sf |mailx -s\"Subject:TEST!!  Parameter Changes log  $obsid.$rev\n\"  -r$cus_email $test_email");
				}else{
					system("cat $temp_dir/user.$sf |mailx -s\"Subject: Parameter Changes log  $obsid.$rev\n\"  -r$cus_email -c$cus_email $email_address");
				}
				system("rm $temp_dir/user.$sf");
			}else{
				if($usint_on =~ /test/){
					system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject:TEST!! Parameter Changes log  $obsid.$rev\n\" -r$cus_email  $test_email");
				}else{
					system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes log  $obsid.$rev\n\" -r$cus_email -c$cus_email  $email_address");
				}
			}

			if($usint_on =~ /test/){
				system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject:TEST!! Parameter Changes log  $obsid.$rev\n\" -r$cus_email  $test_email");
			}else{
				system("cat $temp_dir/ormail_$obsid.$sf |mailx -s\"Subject: Parameter Changes log  $obsid.$rev\n\" -r$cus_email $cus_email");
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

	system("rm -f $temp_dir/$obsid.$sf $temp_dir/ormail_$obsid.$sf");
	system("rm -f $temp_dir/ormail_$obsid.$sf");

	system("rm -f $temp_dir/arnold.$sf");
	system("chmod 777 $temp_dir/*");
}

