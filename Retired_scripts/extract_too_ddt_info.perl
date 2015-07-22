#!/soft/ascds/DS.release/ots/bin/perl
use DBI;
use DBD::Sybase;
use CGI qw/:standard :netscape /;

#########################################################################################################################
#															#
#	extract_too_ddt_info.perl: find out approved too and ddt observation and create a list				#
#															#
#			author: t. isobe (tisobe@cfa.harvard.edu)							#
#															#
#			last update: Aug 27, 2012									#
#															#
#########################################################################################################################

#
#---- set directory paths : updated to read from a file (02/25/2011)	 this is user cus version
#

#$test_run  = 0;                                                                # live run
$test_run  = 1;                                                                 # tst run case  

if($test_run == 1){
        $d_path = "/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/";           # test directory list path
}else{  
        $d_path = "/data/udoc1/ocat/Info_save/";                               # live directory list path
}

open(IN, "$d_path/dir_list");

while(<FH>){
    chomp $_;
    @atemp = split(/\s+/, $_);
    $atemp[1] =~ s/://g;
    ${$atemp[0]} = $atemp[1];
}
close(FH);

#$data_dir = '/proj/web-icxc/cgi-bin/obs_ss/Test/too_contact_info';

#
#--- find who is in charge today
#

$person_in_charge       = find_person_in_charge();
$today_person_in_charge = $person_in_charge;


#
#--- read the list of today's approved ddt and too observations (https://icxc.harvard.edu/mp/html/ddttoo.html)
#

read_today_too_ddt_list();

#
#--- read current ddt list, and find a newly added ddt obsids
#

$really_cnt = 0;
@really_new = ();

update_list("ddt");

$rdcnt          = $really_cnt;
@really_new_ddt = @really_new;

#
#--- read current too list, and find a newly added too obsids
#


$really_cnt = 0;
@really_new = ();

update_list("too");

$rtcnt          = $really_cnt;
@really_new_too = @really_new;

#
#--- now update new_obs_list ddt and too
#

update_new_obs_list();


#
#--- sending out reminder email to POC
#

if($rdcnt > 0){
	@really_new = @really_new_ddt;
	send_email("ddt");
}


if($rtcnt > 0){
	@really_new = @really_new_too;
	send_email("too");
}

system("cat $data_dir/new_list_header $data_dir/new_obs_list > $data_dir/new_obs_list.txt");
system("chgrp mtagroup $data_dir/ddt_list $data_dir/too_list $data_dir/new_obs_list  $data_dir/new_obs_list.txt  $data_dir/past_obs_list");


###########################################################################################
###  find_person_in_charge: find person in charge                                       ###
###########################################################################################

sub find_person_in_charge{

	open(FH, "$data_dir/this_week_person_in_charge");

	TOUTER:
	while(<FH>){
        	chomp $_;
        	if($_ =~ /#/){
                	next TOUTER;
        	}else{
                	@atemp     = split(/\,/, $_);
			$poc_email = $atemp[4];
			open(IN, "$data_dir/personal_list");
			while(<IN>){
				chomp $_;
				if($_ =~ /$poc_email/){
					@btemp = split(/<>/, $_);
					@ctemp = split(/\@/, $btemp[4]);
					$person_in_charge = $ctemp[0];

					if($person_in_charge =~ /pzhao/i) {$person_in_charge = 'ping'}
					if($person_in_charge =~ /swolk/i) {$person_in_charge = 'sjw'}
					if($person_in_charge =~ /nadams/i) {$person_in_charge = 'nraw'}
					if($person_in_charge =~ /bwargelin/i) {$person_in_charge = 'bw'}
					last TOUTER;
				}
			}
			close(IN);
			$person_in_charge = 'TBD';
        	}
	}
	close(FH);

	return $person_in_charge;
}


###########################################################################################
###  read_today_too_ddt_list: find approved ddt and too obsids                          ###
###########################################################################################

sub read_today_too_ddt_list{

	@ddt_list = ();
	@too_list = ();
	$dcnt     = 0;
	$tcnt     = 0;
#
#--- https://icxc.harvard.edu/mp/html/ddttoo.html gives the list of approved ddt and too observations
#	
	open(FH, "/proj/web-icxc/htdocs/mp/html/ddttoo.html");
	OUTER:
	while(<FH>){
		chomp $_;
		if($_ =~ /\<h4\>Unobserved\/Pending DDT Observations:/){
			$type = 'ddt';
		}elsif($_ =~ /\<h4\>Unobserved\/Pending TOO Observations:/){
			$type = 'too';
		}elsif($_ =~ /\<\!\-\- ObsID \-\-\>/){
			@atemp = split(/\?/, $_);
			@btemp = split(/\'/, $atemp[1]);
			$obsid = $btemp[0];
			if($obsid !~ /\d/){
				next OUTER;
			}
		}elsif($_ =~ /Approved?/){
			if($_ =~ /Y/){
				$app = 1;
			}else{
				$app = 0;
			}
		}elsif($_ =~ /\<\!\-\- status \-\-\>/){
			if($app == 1){
				if($_ =~ /observed/ || $_ =~ /scheduled/ || $_ =~ /unobserved/){
					if($type =~ /ddt/){
						if($obsid < 100000){
							push(@ddt_list, $obsid);
							$dcnt++;
						}
						$app   = -1;
						$obsid = '';

					}elsif($type =~ /too/){
						if($obsid < 100000){
							push(@too_list, $obsid);
							$tcnt++;
						}
						$app   = -1;
						$obsid = '';
					}
				}
			}
		}
	}
	close(FH);

#
#--- some obsids are read from email and not in ddttoo.html list yet; so add these into the list
#

	open(FH, "$data_dir/ddt_list");
	OUTER:
	while(<FH>){
		chomp $_;
		if($_ =~ /unobserved/ || $_ =~ /scheduled/){
			@atemp = split(/\t+/, $_);
			foreach $comp (ddt_list){
				if($atemp[2] == $comp){
					next OUTER;
				}
			}
			push(@ddt_list, $atemp[2]);
			$dcnt++;
		}
	}
	close(FH);
		

	open(FH, "$data_dir/too_list");
	OUTER:
	while(<FH>){
		chomp $_;
		if($_ =~ /unobserved/ || $_ =~ /scheduled/){
			@atemp = split(/\t+/, $_);
			foreach $comp (too_list){
				if($atemp[2] == $comp){
					next OUTER;
				}
			}
			push(@too_list, $atemp[2]);
			$tcnt++;
		}
	}
	close(FH);
		
}

###########################################################################################
###  update_list: update ddt or too list including it status, approved status etc       ###
###########################################################################################

sub update_list{

	($head) = @_;				#--- $head should be ddt or too
	chomp $head;

	$dat_name  = "$head".'_list';		#--- data file name
	$old_name  = "$dat_name".'~';		#--- copy of the current data file name
	$tmp_name  = "$dat_name".'_tmp';	#--- temporary updated data file name

	@line_save = ();
	@approved  = ();
	@current   = ();
	@c_cnt     = 0;

#
#--- back up the current list
#
	system("cp $data_dir/$dat_name $data_dir/$old_name");
#
#--- read current "$head" data list 
#
	open(FH, "$data_dir/$dat_name");
	while(<FH>){
		chomp $_;
		@atemp = split(/\t+/, $_);
		$obsid = $atemp[2];
		if($obsid !~ /\d/){
			open(IN, "$obs_ss/sot_ocat.out");
			OUTER2:
			while(<IN>){
				chomp $_;
				@btemp = split(/\^/, $_);
				if($btemp[3] == $atemp[1]){
					$obsid = $btemp[10];
					last OUTER2;
				}
			}
			close(IN);
		}

		find_group();			#--- find sq #, status etc for obsid

		if($status =~ /unobserved/ || $status =~ /scheduled/ || $status =~ /observed/){
			push(@current, $obsid);

			if($status =~ /observed/ && $status !~ /unobserved/){
				find_obs_date();
			}else{
				if($soe_st_sched_date ne ''){
					$date = $soe_st_sched_date;
				}elsif($lts_lt_plan ne ''){
					$date = $lts_lt_plan;
				}else{
					$date = 'NA';
				}
			}

			if($targname =~ /Crab/i){
				$pnam = 'ppp';
				%{$head.$obsid} = (poc => ["$pnam"]);
			}elsif($targname =~ /Jupiter/i || $targname =~ /Saturn/i){
				$pnam = 'sjw';
				%{$head.$obsid} = (poc => ["$pnam"]);
			}elsif($grating =~ /letg/i || $grating =~ /hetg/i){
				$pnam = lc($grating);
				%{$head.$obsid} = (poc => ["$pnam"]);
			}else{
				$pnam = $atemp[4];
				%{$head.$obsid} = (poc => ["$atemp[4]"]);
			}

			$line = "$head\t$seq_nbr\t$obsid\t$status\t$pnam\t$date";
			push(@line_save, $line);

			if($_ =~ /unapproved/){
				push(@approved, 0);
			}else{
				push(@approved, 1);
			}
			$c_cnt++;
		}else{
			open(AOUT, ">>$data_dir/old_ddt_too_list");
			($usec, $umin, $uhour, $umday, $umon, $uyear, $uwday, $uyday, $uisdst)= localtime(time);
			$uyear = 1900 + $uyear;
			print AOUT "$_\t$uyear:$uyday\n";
			close(AOUT);
		}
	
	}
	close(FH);

#
#--- compare the last and today's lists and if there anything new, add to the list
#
	@crt_list = ();
	@new_list = ();
	@new_cnt  = 0;
	OUTER:
	foreach $ent (@{$dat_name}){
		foreach $comp (@current){
			if($ent == $comp){
				push(@crt_list, $ent);
				next OUTER;
			}
		}
		push(@new_list, $ent);
		$new_cnt++;
	}

#
#--- print out already known ddt/too approved observations, then
#--- the newly approved obsids are in the current list without "unapproved"
#
	open(OUT, ">$data_dir/$tmp_name");

	OUTER:
	for($i = 0; $i < $c_cnt; $i++){
		foreach $comp (@crt_list){
			if($comp == $current[$i]){
				print OUT "$line_save[$i]\n";
				next OUTER;
			}
		}
	}

#
#--- add new one to the list
#

	if($new_cnt > 0){
		@really_new = ();
		@really_cnt = 0;
		foreach $obsid (@new_list){

			find_group();

			if($status =~ /unobserved/ || $status =~ /scheduled/ || $status =~ /observed/){

				if($status =~ /observed/ && $status !~ /unobserved/){
					find_obs_date();
				}else{
					if($soe_st_sched_date ne ''){
						$date = $soe_st_sched_date;
					}elsif($lts_lt_plan ne ''){
						$date = $lts_lt_plan;
					}else{
						$date = 'NA';
					}
				}
			
				$person_in_charge = $today_person_in_charge;
				if($targname =~ /Crab/i){
					$person_in_charge = 'ppp';
				}elsif($targname =~ /Jupiter/i || $targname =~ /Saturn/i){
					$person_in_charge = 'sjw';
				}elsif($grating =~ /letg/i || $grating =~ /hetg/i){
					$person_in_charge = lc($grating);
				}

				print OUT "$head\t$seq_nbr\t$obsid\t$status\t$person_in_charge\t$date\n";

				push(@current,    $obisd);
				push(@really_new, $obsid);
				$really_cnt++;
				%{$head.$obsid} = (poc => ["$person_in_charge"]);
			}

#
#--- if there are group id related obsids, add to the list
#

##			if($group_cnt > 0){
##				related_obsids("group");
##
##			}elsif($monitor_cnt > 0){
#
#--- if there are monitor related obsids, add to the list
#
##				related_obsids("monitor");
##			}
		}
	}
	close(OUT);

	if($really_cnt > 0){
		@temp  = sort{$a<=>$b} @really_new;
		$first = shift(@temp);
		@selc  = ($first);
		$scnt  = 1;
		OUTER:
		foreach $ent (@temp){
			foreach $comp (@selc){
				if($ent =~ /$comp/){
					next OUTER;
				}
			}
			push(@selc, $ent);
			$scnt++;
		}
		@really_new = @selc;
		$really_cnt = $scnt;
	}

	system("mv $data_dir/$tmp_name $data_dir/$dat_name");
}



###########################################################################################
### related_obsids: find group or monitoring obsids for a given obsid                   ###
###########################################################################################

sub related_obsids{
	($mhead) = @_;
	if($mhead =~ /group/){
		@test = @group_member;
	}else{
		@test = @monitor_series;
	}

	OUTER:
	foreach $obsid (@test){

#
#--- make sure that the obsids in the list are not already printed out
#
		foreach $comp (@{$dat_name}){
			if($obsid == $comp){
				next OUTER;
			}
		}

		foreach $comp (@new_list){
			if($obsid == $comp){
				next OUTER;
			}

			find_group();

			if($status =~ /unobserved/ || $status =~ /scheduled/ || $status =~ /observed/){
			
				$person_in_charge = $today_person_in_charge;
				if($targname =~ /Crab/i){
					$person_in_charge = 'ppp';
				}elsif($targname =~ /Jupiter/i || $targname =~ /Saturn/i){
					$person_in_charge = 'sjw';
				}elsif($grating =~ /letg/i || $grating =~ /hetg/i){
					$person_in_charge = lc($grating);
				}

				print OUT "$head\t$seq_nbr\t$monid\t$status\t$person_in_charge\tunapproved\n";

				push(@current,    $obsid);
				push(@really_new, $obsid);
				$really_cnt++;
				%{$head.$obsid} = (poc =>["$person_in_charge"]);
			}
		}
	}
}


###########################################################################################
### update_new_obs_list: using new ddt/too list jpdate new_obs_list                     ###
###########################################################################################

sub update_new_obs_list{

	($lsec, $lmin, $lhour, $lmday, $lmon, $lyear, $lwday, $lyday, $isdst) = localtime(time);
	$lyear += 1900;
	$chk    = 4.0 * int (0.25 * $lyear);
	$base   = 365;
	if($chk == $lyear){
		$base = 366;
	}
	$end_year = $lyear;
	$end_date = $lyday + 30;
	if($end_date > $base){
		$end_year  = $lyear+1;
		$end_date -= $base;
	}

	open(OUT, ">$data_dir/new_obs_list_temp");
	open(OUT2, "> $data_dir/obs_in_30days");
	
	@ddt_temp = ();
	@too_temp = ();

	open(FH, "$data_dir/new_obs_list");
	OUTER:
	while(<FH>){
		chomp $_;
		if($_ =~ /canceled/i || $_ =~ /discarded/i || $_ =~ /archived/i){
			next OUTER;
		}
		
		if($_ =~ /DDT/i){
			if($_ =~ /scheduled/i || $_ =~ /unobserved/i){
				@atemp = split(/\t+/, $_);
				$poc   = ${ddt.$atemp[2]}{poc}[0];
				if($poc eq '' || $poc !~ /\w/){
					$poc = 'TBD';
				}

				$obsid  = $atemp[2];
				find_group();   
				$status = $atemp[3];
				if($status =~ /observed/ && $status !~ /unobserved/){
					find_obs_date();
				}else{
					if($soe_st_sched_date ne ''){
						$date = $soe_st_sched_date;
					}elsif($lts_lt_plan ne ''){
						$date = $lts_lt_plan;
					}else{
						$date = 'NA';
					}
				}

				print OUT "$atemp[0]\t$atemp[1]\t$atemp[2]\t$atemp[3]\t$poc\t$atemp[5]\t$date\n";
				push(@ddt_temp, $atemp[2]);
				if($date ne "NA" && $date ne ''){
					@dtemp  = split(/\s+/, $date);
					$cmonth = conv_month_chr_to_num($dtemp[0], 0);
					$cdate  = $dtemp[1];
					$cyear  = $dtemp[2];
					$cydate = find_ydate($cyear, $cmonth, $cdate);

					if($cyear <= $end_year){
						if($cyear < $end_year){
							print OUT2 "$atemp[0]\t$atemp[1]\t$atemp[2]\t$atemp[3]\t$poc\t$atemp[5]\t$date\n";
						}elsif($cydate <= $end_date){
							print OUT2 "$atemp[0]\t$atemp[1]\t$atemp[2]\t$atemp[3]\t$poc\t$atemp[5]\t$date\n";
						}
					}
				}
			}else{
				print OUT "$_\n";
				@atemp = split(/\s+/, $_);
				push(@ddt_temp, $atemp[2]);
			}
		}elsif($_ =~ /TOO/i){
			if($_ =~ /scheduled/i || $_ =~ /unobserved/i){
				@atemp = split(/\t+/, $_);
				$poc   = ${too.$atemp[2]}{poc}[0];
				if($poc eq '' || $poc !~ /\w/){
					$poc = 'TBD';
				}

				$obsid  = $atemp[2];
				find_group();   
				$status = $atemp[3];
				if($status =~ /observed/ && $status !~ /unobserved/){
					find_obs_date();
				}else{
					if($soe_st_sched_date ne ''){
						$date = $soe_st_sched_date;
					}elsif($lts_lt_plan ne ''){
						$date = $lts_lt_plan;
					}else{
						$date = 'NA';
					}
				}

				print OUT "$atemp[0]\t$atemp[1]\t$atemp[2]\t$atemp[3]\t$poc\t$atemp[5]\t$date\n";
				push(@too_temp, $atemp[2]);
				if($date ne "NA" && $date ne ''){
					@dtemp  = split(/\s+/, $date);
					$cmonth = conv_month_chr_to_num($dtemp[0], 0);
					$cdate  = $dtemp[1];
					$cyear  = $dtemp[2];
					$cydate = find_ydate($cyear, $cmonth, $cdate);

					if($cyear <= $end_year){
						if($cyear < $end_year){
							print OUT2 "$atemp[0]\t$atemp[1]\t$atemp[2]\t$atemp[3]\t$poc\t$atemp[5]\t$date\n";
						}elsif($cydate <= $end_date){
							print OUT2 "$atemp[0]\t$atemp[1]\t$atemp[2]\t$atemp[3]\t$poc\t$atemp[5]\t$date\n";
						}
					}
				}
			}else{
				print OUT "$_\n";
				@atemp = split(/\t+/, $_);
				push(@too_temp, $atemp[2]);
			}
		}else{
			print OUT "$_\n";
			@atemp = split(/\t+/, $_);
			$date  = $atemp[6];
			if($atemp[3] =~ /scheduled/ || $atemp[3] =~ /unobserved/){
				if($date ne "NA" && $date ne ''){
					@dtemp  = split(/\s+/, $date);
					$cmonth = conv_month_chr_to_num($dtemp[0], 0);
					$cdate  = $dtemp[1];
					$cyear  = $dtemp[2];
					$cydate = find_ydate($cyear, $cmonth, $cdate);
	
					if($cyear <= $end_year){
						if($cyear < $end_year){
							print OUT2 "$atemp[0]\t$atemp[1]\t$atemp[2]\t$atemp[3]\t$atemp[4]\t$atemp[5]\t$date\n";
						}elsif($cydate <= $end_date){
							print OUT2 "$atemp[0]\t$atemp[1]\t$atemp[2]\t$atemp[3]\t$atemp[4]\t$atemp[5]\t$date\n";
						}
					}
				}
			}
		}
	}
	close(FH);
#
#--- just in a case some ddt or too observations which are not observed yet are missing
#
	open(FH, "$data_dir/ddt_list");
	OUTER:
	while(<FH>){
		chomp $_;
		@atemp = split(/\s+/, $_);
		if($atemp[3] =~ /unobserved/ || $atemp[3] =~ /scheduled/){
			foreach $comp (@ddt_temp){
				if($atemp[2] == $comp){
					next OUTER;
				}
			}
			$obsid = $atemp[2];
			find_group();

			if($status =~ /observed/ && $status !~ /unobserved/){
				find_obs_date();
			}else{
				if($soe_st_sched_date ne ''){
					$date = $soe_st_sched_date;
				}elsif($lts_lt_plan ne ''){
					$date = $lts_lt_plan;
				}else{
					$date = 'NA';
				}
			}
	
			$type = uc($atemp[0]);
			print OUT "$type\t$atemp[1]\t$obsid\t$atemp[3]\t$atemp[4]\t$obs_ao_str\t$date\n";
			if($atemp[3] =~ /scheduled/ || $atemp[3] =~ /unobserved/){
				if($date ne "NA" && $date ne ''){
					@dtemp  = split(/\s+/, $date);
					$cmonth = conv_month_chr_to_num($dtemp[0], 0);
					$cdate  = $dtemp[1];
					$cyear  = $dtemp[2];
					$cydate = find_ydate($cyear, $cmonth, $cdate);
	
					if($cyear <= $end_year){
						if($cyear < $end_year){
							print OUT2 "$type\t$atemp[1]\t$obsid\t$atemp[3]\t$atemp[4]\t$obs_ao_str\t$date\n";
						}elsif($cydate <= $end_date){
							print OUT2 "$type\t$atemp[1]\t$obsid\t$atemp[3]\t$atemp[4]\t$obs_ao_str\t$date\n";
						}
					}
				}
			}
		}
	}
	close(FH);
		

	open(FH, "$data_dir/too_list");
	OUTER:
	while(<FH>){
		chomp $_;
		@atemp = split(/\s+/, $_);
		if($atemp[3] =~ /unobserved/ || $atemp[3] =~ /scheduled/){
			foreach $comp (@too_temp){
				if($atemp[2] == $comp){
					next OUTER;
				}
			}
			$obsid = $atemp[2];
			find_group();

			if($status =~ /observed/ && $status !~ /unobserved/){
				find_obs_date();
			}else{
				if($soe_st_sched_date ne ''){
					$date = $soe_st_sched_date;
				}elsif($lts_lt_plan ne ''){
					$date = $lts_lt_plan;
				}else{
					$date = 'NA';
				}
			}
	
			$type = uc($atemp[0]);
			print OUT "$type\t$atemp[1]\t$obsid\t$atemp[3]\t$atemp[4]\t$obs_ao_str\t$date\n";
			if($atemp[3] =~ /scheduled/ || $atemp[3] =~ /unobserved/){
				if($date ne "NA" || $date ne ''){
					@dtemp  = split(/\s+/, $date);
					$cmonth = conv_month_chr_to_num($dtemp[0], 0);
					$cdate  = $dtemp[1];
					$cyear  = $dtemp[2];
					$cydate = find_ydate($cyear, $cmonth, $cdate);
	
					if($cyear <= $end_year){
						if($cyear < $end_year){
							print OUT2 "$type\t$atemp[1]\t$obsid\t$atemp[3]\t$atemp[4]\t$obs_ao_str\t$date\n";
						}elsif($cydate <= $end_date){
							print OUT2 "$type\t$atemp[1]\t$obsid\t$atemp[3]\t$atemp[4]\t$obs_ao_str\t$date\n";
						}
					}
				}
			}
		}
	}
	close(FH);
	close(OUT);
	close(OUT2);

#
#---- removing un-wanted invisible special characters
#

	open(IN, "$data_dir/new_obs_list_temp");
	open(OUT,"$data_dir/new_obs_list_temp2");
	while(<IN>){
		chomp $_;
		$temp = $_;
		$temp =~ s/[^a-zA-Z0-9\s\:\t]*//g;
		print OUT "$temp\n";
	}
	close(OUT);
	close(IN);

	system("rm $data_dir/new_obs_list_temp");

	system("mv $data_dir/new_obs_list_temp2 $data_dir/new_obs_list");
}

###########################################################################################
### send_email: send out email when new ddt or too observation is approved              ###
###########################################################################################

sub send_email{
	($head) = @_;
	$uc_head = uc($head);

	foreach $obsid (@really_new){
		$user = ${$head.$obsid}{poc}[0];
		if($user eq ''){
			$user = $person_in_charge;
		}
		open(FH, "$data_dir/usint_personal");
		OUTER2:
		while(<IN>){
			chomp $_;
			if($_ =~ /$user/i){
				@ctemp = split(/:/, $_);
				$poc_email = $ctemp[5];
				last OUTER2;
			}
		}
		close(IN);

		if($user =~ /hetg/i){
			$poc_email = 'nss@cfa.harvard.edu';
		}elsif($user =~ /letg/i){
			$poc_email = 'bwargelin@cfa.harvard.eedu';
		}

		open(OUT, ">$temp_dir/tmp_email");
		print OUT "A new $uc_head observation (OBSID: $obsid) is assigned to you. Please check: \n";
		print OUT "https://icxc.harvard.edu/mta/CUS/Usint/ocatdata2html.cgi?$obsid \n";
		print OUT "for more information.\n";
		print OUT "If this you are not the final support astronomer for this observations \n";
		print OUT "please reply to isobe@head.cfa.harvard.edu cc:cus@head.cfa.harvard.edu.\n";
		close(OUT);

		system("cat $temp_dir/tmp_email |mailx -s\"Subject: New $uc_head Observation ($user: $poc_email)\n\" -r cus\@head.cfa.harvard.edu isobe\@head.cfa.harvard.edu");
		if($test_run == 0){
			system("cat $temp_dir/tmp_email |mailx -s\"Subject: New $uc_head Observation ($user: $poc_email)\n\" -r cus\@head.cfa.harvard.edu swolk\@head.cfa.harvard.edu");
####			system("cat $temp_dir/tmp_email |mailx -s\"Subject: New $uc_head Observation \n\" -r cus\@head.cfa.harvard.edu $poc_email  cus\@head.cfa.harvard.edu");
		}
		system("rm $temp_dir/tmp_email");
	}
}

###########################################################################################
### find_group: find related obsids                                                     ###
###########################################################################################

sub find_group {

#------------------------------------------------
#-------  database username, password, and server
#------------------------------------------------

        $db_user = "browser";
        $server  = "ocatsqlsrv";

        $db_passwd =`cat $pass_dir/.targpass`;
        chomp $db_passwd;

#--------------------------------------
#-------- open connection to sql server
#--------------------------------------

        my $db = "server=$server;database=axafocat";
        $dsn1  = "DBI:Sybase:$db";
        $dbh1  = DBI->connect($dsn1, $db_user, $db_passwd, { PrintError => 0, RaiseError => 1});


#
#--- find a group_id etc
#

#------------------------------------------------------
#---------------  get stuff from target table, clean up
#------------------------------------------------------

        $sqlh1 = $dbh1->prepare(qq(select
                        group_id,pre_id,pre_min_lead,pre_max_lead,grating,type,instrument,obs_ao_str,status,seq_nbr,ocat_propid,
			soe_st_sched_date,lts_lt_plan,targname
        from target where obsid=$obsid));

        $sqlh1->execute();
        @targetdata   = $sqlh1->fetchrow_array;
        $sqlh1->finish;

        $group_id     = $targetdata[0];
        $pre_id       = $targetdata[1];
        $pre_min_lead = $targetdata[2];
        $pre_max_lead = $targetdata[3];
        $grating      = $targetdata[4];
        $type         = $targetdata[5];
        $instrument   = $targetdata[6];
        $obs_ao_str   = $targetdata[7];
	$status       = $targetdata[8];
	$seq_nbr      = $targetdata[9];
	$ocat_propid  = $targetdata[10];
	$soe_st_sched_date = $targetdata[11];
	$lts_lt_plan  = $targetdata[12];
	$targname     = $targetdata[13];

        $group_id     =~ s/\s+//g;
        $pre_id       =~ s/\s+//g;
        $pre_min_lead =~ s/\s+//g;
        $pre_max_lead =~ s/\s+//g;
        $grating      =~ s/\s+//g;
        $type         =~ s/\s+//g;
        $instrument   =~ s/\s+//g;
        $obs_ao_str   =~ s/\s+//g;
        $status       =~ s/\s+//g;
        $seq_nbr      =~ s/\s+//g;
        $ocat_propid  =~ s/\s+//g;
	$targname     =~ s/\s+//g;

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

		@group_member = ();
		$group_cnt    = 0;
                while(@group_obsid = $sqlh1->fetchrow_array){
			$group_obsid = join(" ", @group_obsid);
			push(@group_member, $group_obsid);
			$group_cnt++;
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

	$monitor_cnt = 0;
	foreach (@monitor_series){
		$monitor_cnt++;
	}

#-------------------------------------------------
#---- updating AO number for the observation
#---- ao value is different from org and current
#-------------------------------------------------

	$sqlh1 = $dbh1->prepare(qq(select
		ao_str
	from prop_info where ocat_propid=$ocat_propid ));

	$sqlh1->execute();
	@updatedata   = $sqlh1->fetchrow_array;
	$sqlh1->finish;
	if($updatedata[0] =~ /\d/){
		$obs_ao_str = $updatedata[0];
		$obs_ao_str =~ s/\s+//g;
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

##############################################################################################
### find_obs_date: extract obs starting date from mit web site                             ###
##############################################################################################

sub find_obs_date{
	system("$op_dir/lynx -source http://acis.mit.edu/cgi-bin/get-obsid\?id=$obsid > $temp_dir/ztemp");
	open(IN, "$temp_dir/ztemp");
	$chk = 0;
	OUTER:
	while(<IN>){
		chomp $_;	
		if($chk > 0){
			@dtemp = split(/\<tt\>/, $_);
			@ftemp = split(/\</, $dtemp[1]);
			$date  = $ftemp[0];
			last OUTER;
		}
		if($_ =~ /Start Date:/){
			$chk = 1;
		}
	}
	close(IN);
	system("rm $temp_dir/ztemp");
	
	@dtemp = split(/\s+/, $date);
	@ftemp = split(/-/,   $dtemp[0]);
	
	if($ftemp[1] == 1){
		$mon = "Jan";
	}elsif($ftemp[1] == 2){
		$mon = "Feb";
	}elsif($ftemp[1] == 3){
		$mon = "Mar";
	}elsif($ftemp[1] == 4){
		$mon = "Apr";
	}elsif($ftemp[1] == 5){
		$mon = "May";
	}elsif($ftemp[1] == 6){
		$mon = "Jun";
	}elsif($ftemp[1] == 7){
		$mon = "Jul";
	}elsif($ftemp[1] == 8){
		$mon = "Aug";
	}elsif($ftemp[1] == 9){
		$mon = "Sep";
	}elsif($ftemp[1] == 10){
		$mon = "Oct";
	}elsif($ftemp[1] == 11){
		$mon = "Nov";
	}elsif($ftemp[1] == 12){
		$mon = "Dec";
	}
	
	@etemp = split(/:/, $dtemp[1]);
	$part = 'AM';
	$time = $etemp[0];
	if($etemp[0] == 0){
		$time = 12;
	}elsif($etemp[0] >= 12){
		$part = 'PM';
		if($etemp[0] > 12){
			$time = $etemp[0] - 12;
		}
	}
	
	$time = "$time:$etemp[1]"."$part";
	
	$date = "$mon $ftemp[2] $ftemp[0] $time";
}

###################################################################
### conv_month_chr_to_num: change month format to e.g. Jan to 1 ###
###################################################################

sub conv_month_chr_to_num{

######################################################################
#       Input   $temp_month: month in letters
#               $add0:  it indicates which format, 1 or 01 is wnated
#                       if it is larger than 0, it is latter
#       Output  $cmonth: month in number
######################################################################

        my ($temp_month, $cmonth, $add0);
        ($temp_month, $add0) = @_;

        if($temp_month =~ /Jan/i){
                $cmonth = 1;
        }elsif($temp_month =~ /Feb/i){
                $cmonth = 2;
        }elsif($temp_month =~ /Mar/i){
                $cmonth = 3;
        }elsif($temp_month =~ /Apr/i){
                $cmonth = 4;
        }elsif($temp_month =~ /May/i){
                $cmonth = 5;
        }elsif($temp_month =~ /Jun/i){
                $cmonth = 6;
        }elsif($temp_month =~ /Jul/i){
                $cmonth = 7;
        }elsif($temp_month =~ /Aug/i){
                $cmonth = 8;
        }elsif($temp_month =~ /Sep/i){
                $cmonth = 9;
        }elsif($temp_month =~ /Oct/i){
                $cmonth = 10;
        }elsif($temp_month =~ /Nov/i){
                $cmonth = 11;
        }elsif($temp_month =~ /Dec/i){
                $cmonth = 12;
        }
        if($add0 > 0 && $cmonth < 10){
                $cmonth = '0'."$cmonth";
        }
        return $cmonth;
}

##################################################
### find_ydate: change month/day to y-date     ###
##################################################

sub find_ydate {

##################################################
#       Input   $tyear: year
#               $tmonth: month
#               $tday:   day of the month
#
#       Output  $ydate: day from Jan 1<--- returned
##################################################

        my($tyear, $tmonth, $tday, $ydate, $chk);
        ($tyear, $tmonth, $tday) = @_;

        if($tmonth == 1){
                $ydate = $tday;
        }elsif($tmonth == 2){
                $ydate = $tday + 31;
        }elsif($tmonth == 3){
                $ydate = $tday + 59;
        }elsif($tmonth == 4){
                $ydate = $tday + 90;
        }elsif($tmonth == 5){
                $ydate = $tday + 120;
        }elsif($tmonth == 6){
                $ydate = $tday + 151;
        }elsif($tmonth == 7){
                $ydate = $tday + 181;
        }elsif($tmonth == 8){
                $ydate = $tday + 212;
        }elsif($tmonth == 9){
                $ydate = $tday + 243;
        }elsif($tmonth == 10){
                $ydate = $tday + 273;
        }elsif($tmonth == 11){
                $ydate = $tday + 304;
        }elsif($tmonth == 12 ){
                $ydate = $tday + 334;
        }
        $chk = 4 * int (0.25 * $tyear);
        if($chk == $tyear && $tmonth > 2){
                $ydate++;
        }
        return $ydate;
}

