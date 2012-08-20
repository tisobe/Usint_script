#!/soft/ascds/DS.release/ots/bin/perl
use DBI;
use DBD::Sybase;
use CGI qw/:standard :netscape /;

#########################################################################################################################
#															#
#	find_too_ddt_email.perl: find a newly approved DDT/TOO observation from email, and update the list		#
#															#
#		author: t. isobe (tisobe@cfa.harvard.edu)								#
#															#
#		last update: Arp 27, 2012										#
#															#
#########################################################################################################################

#
#---- set directory paths : updated to read from a file (02/25/2011)     this is user cus version
#

#$test_run  = 0;                                                                # live run
$test_run  = 1;                                                                 # test run case  

if($test_run == 1){
        $d_path = "/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/";           # test directory list path
}else{  
        $d_path = "/data/udoc1/ocat/Info_save/";                               # live directory list path
}

open(IN, "$d_path/dir_list");

while(<IN>){
        chomp $_;
        @atemp    = split(/:/, $_);
        $atemp[0] =~ s/\s+//g;
        if($atemp[0] =~ /obs_ss/){
                $obs_ss   = $atemp[1];
        }elsif($atemp[0]  =~ /pass_dir/){
                $pass_dir = $atemp[1];
        }elsif($atemp[0]  =~ /ctemp_dir/){
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


#------------------------
#--- TEST TEST TEST
#-------------------------

#####$data_dir = './';

#-------------------------
#





#
#---- read too and ddt observations which are already in the lists
#

open(FH, "$data_dir/too_list");

@too_data = ();
@too_obs  = ();
$too_cnt  = 0;

while(<FH>){
	chomp $_;
	push(@too_data, $_);
	@atemp = split(/\s+/, $_);
	push(@too_obs, $atemp[2]);
	$too_cnt++;
}
close(FH);

open(FH, "$data_dir/ddt_list");

@ddt_data = ();
@ddt_obs  = ();
$ddt_cnt  = 0;

while(<FH>){
	chomp $_;
	push(@ddt_data, $_);
	@atemp = split(/\s+/, $_);
	push(@ddt_obs, $atemp[2]);
	$ddt_cnt++;
}
close(FH);

#
#--- find who is in charge today
#

$person_in_charge = find_person_in_charge();


#
#--- read monitor/group observations already in the list
#

open(FH, "$data_dir/monitor_too_ddt");

@group_obsid = ();
@group_poc   = ();
@group_id    = ();
@group_seq   = ();
$group_cnt   = 0;

while(<FH>){
	chomp $_;
	@atemp = split(/\s+/, $_);
	push(@group_obsid, $atemp[0]);
	push(@group_poc,   $atemp[1]);
	push(@group_id,    $atemp[2]);
	push(@group_seq,   $atemp[3]);
	$group_cnt++;
}
close(FH);

$group_cnt_org = $group_cnt;			#---- keep the record so that we can compare later

#
#---- find ddt/too observation seq_nbr from email : outputs are list of seq_nbrs
#

read_ddt_too_from_email();

#
#--- compare the lists found above to the current one and find out whether there are any newly 
#--- approved DDT/TOO observations
#

@too_new = ();

OUTER:
foreach $ent (@too_list){
	foreach $comp (@too_obs){
		if($ent == $comp){
			next OUTER;
		}
	}
	push(@too_new, $ent);
}

@ddt_new = ();
OUTER:
foreach $ent (@ddt_list){
	foreach $comp (@ddt_obs){
		if($ent == $comp){
			next OUTER;
		}
	}
	push(@ddt_new, $ent);
}


#
#--- if nothing new, quietly exit
#

if($too_new[0] !~ /\d/ && $ddt_new[0] !~ /\d/){
	exit 1;
}

#------------------------------------------
#----       update starts here      -------
#------------------------------------------

#
#--- read new_obs_list
#

@nol_type   = ();
@nol_seq    = ();
@nol_obsid  = ();
@nol_status = ();
@nol_poc    = ();
@nol_ao     = ();
@nol_date   = ();
$nol_cnt    = 0;

open(FH, "$data_dir/new_obs_list");
OUTER:
while(<FH>){
	chomp $_;
	@atemp = split(/\t+/, $_);
	push(@nol_type,   $atemp[0]);
	push(@nol_seq,    $atemp[1]);
	push(@nol_obsid,  $atemp[2]);
	push(@nol_status, $atemp[3]);
	push(@nol_poc,    $atemp[4]);
	push(@nol_ao, 	  $atemp[5]);
	push(@nol_date,   $atemp[6]);
	$nol_cnt++;
}
close(FH);

#
#--- a list of totally new ddt/too observations
#

@new_obs_add   = ();
@past_list_add = ();
$pla_chk       = 0;

#
#--- TOO UPDATE:  add new too observation to too_list
#

if($too_new[0] =~ /\d/){

	system("mv $data_dir/too_list $data_dir/too_list~");
	open(OUT, "> $data_dir/too_list");
#
#--- print out the previous list
#

	foreach $ent (@too_data){
		print OUT "$ent\n";
	}

	@really_new  = ();

	SOUTER:
	foreach $obsid (@too_new){

		find_group();			#--- finding other information from the database

		if($status =~ /unobserved/ || $status =~ /scheduled/ || $status =~ /observed/){
			# continue
		}else{
			next SOUTER;
		}

#
#--- find poc for the observation; first check group/monitor affilication
#
		$poc =  '';
		OUTER:
		for($m = 0; $m < $group_cnt; $m++){
			if($obsid == $group_obsid[$m]){
				$poc = $group_poc[$m];
				last OUTER;
			}
		}

		if($poc eq ''){
			$poc = $person_in_charge;

			if($targname =~ /Crab/i){
				$poc = 'ppp';
			}elsif($targname =~ /Jupiter/i || $targname =~ /Saturn/i){
				$poc = 'sjw';
			}elsif($grating =~ /letg/i || $grating =~ /hetg/i){
				$poc = lc($grating);
			}
#
#--- if there are group id related obsids, add to the list
#

		      if($group_cnt > 0){
			      update_monitor_list("group");

		      }elsif($monitor_cnt > 0){
#
#--- if there are monitor related obsids, add to the list
#
			      update_monitor_list("monitor");
		      }
		}

		if($status =~ /observed/ && $status !~ /unobserved/){

			find_obs_date();			#---- finding a starting date

		}else{
			if($soe_st_sched_date ne ''){
				$date = $soe_st_sched_date;
			}elsif($lts_lt_plan ne ''){
				$date = $lts_lt_plan;
			}else{
				$date= 'NA';
			}
		}

		print OUT "too\t$seq_nbr\t$obsid\t$status\t$poc\t$date\n";
		push(@really_new, $obsid);

#
#--- compare the entry to new_obs_list
#
		$chk = 0;
		OUTER2:
		for($k = 0; $k < $nol_cnt; $k++){
			if($obsid == $nol_obsid[$k]){
				if($nol_poc[$k] !~ /\w/ && $nol_poc[$k] =~ /NA/i){
					$nol_poc[$k] = $poc;
				}
				$nol_status[$k] = $status;
				$chk = 1;
				last OUTER2;
			}
		}

		%{poc.$obsid} = (poc =>["$poc"]);
				
#
#---- if the observation is not in new_obs_list, keep it so that we can append it later
#
		if($chk == 0){
			$line = "TOO\t$seq_nbr\t$obsid\t$status\t$poc\t$obs_ao_str\t$date\n";
			push(@new_obs_add,   $line);
			push(@past_list_add, $obsid);
			$pla_chk++;
		}
	}
	close(OUT);

#
#--- sending notification email
#

	send_email('too');
}


#
#--- DDT UPDATE: add new ddt observation to ddt_list
#

if($ddt_new[0] =~ /\d/){

	system("mv $data_dir/ddt_list $data_dir/ddt_list~");
	open(OUT, "> $data_dir/ddt_list");
#
#--- print out the previous list
#
	foreach $ent (@ddt_data){
		print OUT "$ent\n";
	}

	@really_new = ();

	SOUTER:
	foreach $obsid (@ddt_new){

		find_group();			#--- finding other information from the database

		if($status =~ /unobserved/ ||  $status =~ /scheduled/ || $status =~ /observed/){
			# continue
		}else{
			next SOUTER;
		}
#
#--- find poc for the observation
#

		$poc =  '';
		OUTER:
		for($m = 0; $m < $group_cnt; $m++){
			if($obsid == $group_obsid[$m]){
				$poc = $group_poc[$m];
				last OUTER;
			}
		}

		if($poc eq ''){
			$poc = $person_in_charge;

			if($targname =~ /Crab/i){
				$poc = 'ppp';
			}elsif($targname =~ /Jupiter/i || $targname =~ /Saturn/i){
				$poc = 'sjw';
			}elsif($grating =~ /letg/i || $grating =~ /hetg/i){
				$poc = lc($grating);
			}
#
#--- if there are group id related obsids, add to the list
#

		      if($group_cnt > 0){
			      update_monitor_list("group");

		      }elsif($monitor_cnt > 0){
#
#--- if there are monitor related obsids, add to the list
#
			      update_monitor_list("monitor");
		      }
		}

		if($status =~ /observed/ && $status !~ /unobserved/){

			find_obs_date();			#---- finding a starting date

		}else{
			if($soe_st_sched_date ne ''){
				$date = $soe_st_sched_date;
			}elsif($lts_lt_plan ne ''){
				$date = $lts_lt_plan;
			}else{
				$date= 'NA';
			}
		}

		print OUT "ddt\t$seq_nbr\t$obsid\t$status\t$poc\t$date\n";
		push(@really_new, $obsid);
#
#--- compare the entry to new_obs_list
#
		$chk = 0;
		OUTER2:
		for($k = 0; $k < $nol_cnt; $k++){
			if($obsid == $nol_obsid[$k]){
				if($nol_poc[$k] !~ /\w/ && $nol_poc[$k] =~ /NA/i){
					$nol_poc[$k] = $poc;
				}
				$nol_status[$k] = $status;
				$chk = 1;
				last OUTER2;
			}
		}

		%{poc.$obsid} = (poc =>["$poc"]);
				
#
#---- if the observation is not in new_obs_list, keep it so that we can append it later
#

		if($chk == 0){
			$line = "DDT\t$seq_nbr\t$obsid\t$status\t$poc\t$obs_ao_str\t$date\n";
			push(@new_obs_add, $line);
			push(@past_list_add, $obsid);
			$pla_chk++;
		}
	}
	close(OUT);

#
#--- sending notification email
#
	send_email('ddt');
}


#
#--- update new_obs_list
#

system("mv $data_dir/new_obs_list $data_dir/new_obs_list~");

open(OUT, "> $data_dir/new_obs_list");
for($i = 0; $i < $nol_cnt; $i++){
	print OUT "$nol_type[$i]\t";
	print OUT "$nol_seq[$i]\t";
	print OUT "$nol_obsid[$i]\t";
	print OUT "$nol_status[$i]\t";
	print OUT "$nol_poc[$i]\t";
	print OUT "$nol_ao[$i]\t";
	print OUT "$nol_date[$i]\n";
}

foreach $ent (@new_obs_add){
	print OUT "$ent\n";
}
close(OUT);

#
#--- adding the obsid to past_obs_list for extract_too_list.perl use
#

if($pla_chk > 0){
	open(OUT, ">>$data_dir/past_obs_list");
	foreach $ent (@past_list_add){
		print OUT "$ent\n";
	}
	close(OUT);
}

#
#---- update new_obs_list.txt
#

system("cat $data_dir/new_list_header $data_dir/new_obs_list > $data_dir/new_obs_list.txt");

#
#--- update monitor_too_ddt if there are new entries
#

if($group_cnt > $group_cnt_org){
	system("mv $data_dir/monitor_too_ddt $data_dir/monitor_too_ddt~");

	open(OUT, ">$data_dir/monitor_too_ddt");

	for($i = 0; $i < $group_cnt; $i++){
		print OUT "$group_obsid[$i]\t";
		print OUT "$group_poc[$i]\t";
		print OUT "$group_id[$i]\t";
		print OUT "$group_seq[$i]\n";
	}
	close(OUT);
}



################################################################################################## 
### read_ddt_too_from_email: read cus email file and extract recent DDT and TOO approved list  ### 
################################################################################################## 

sub read_ddt_too_from_email{

	open(FH, "/arc/cus/mail_archive");
	@lines = (); 
	$lcnt  = 0;
	while(<FH>){
		chomp $_;
		push(@lines, $_);
		$lcnt++;
	}
	close(FH);
	
	@too_list = ();
	@ddt_list = ();
	
	OUTER:
	for($i = 0; $i < $lcnt; $i++){
		if($lines[$i] =~ /Obsid/ && $lines[$i] =~ /Seq/ && $lines[$i] =~ /is a TOO which has recently/){
				@atemp = split(/Obsid/, $lines[$i]);
				@btemp = split(/\(/, $atemp[1]);
				$oid   = $btemp[0];
				$oid   =~ s/\s+//g;
				push(@too_list, $oid);
				next OUTER;
		}elsif($lines[$i] =~ /Obsid/ && $lines[$i] =~ /Seq/ && $lines[$i] =~ /is a DDT which has recently/){
				@atemp = split(/Obsid/, $lines[$i]);
				@btemp = split(/\(/, $atemp[1]);
				$oid   = $btemp[0];
				$oid   =~ s/\s+//g;
				push(@ddt_list, $oid);
				next OUTER;
		}elsif($lines[$i] =~ /is a TOO/ && $lines[$i] =~ /Obsid/ && $lines[$i] =~ /Prop/ && $lines[$i] =~ /Seq/){
				@atemp = split(/Obsid/, $lines[$i]);
				@btemp = split(/\(/, $atemp[1]);
				$oid   = $btemp[0];
				$oid   =~ s/\s+//g;
				push(@too_list, $oid);
		}elsif($lines[$i] =~ /is a DDT/ && $lines[$i] =~ /Obsid/ && $lines[$i] =~ /Prop/ && $lines[$i] =~ /Seq/){
				@atemp = split(/Obsid/, $lines[$i]);
				@btemp = split(/\(/, $atemp[1]);
				$oid   = $btemp[0];
				$oid   =~ s/\s+//g;
				push(@ddt_list, $oid);
		}

	}
	
#
#--- remove duplicated entries
#

	@temp = sort{@a<=>$b} @too_list;
	@new  = pop(@temp);
	OUTER:
	foreach $ent(@temp){
		foreach $comp(@new){
			if($ent == $comp){
				next OUTER;
			}
		}
		push(@new, $ent);
	}
	
	@too_list = @new;
	
	@temp = sort{@a<=>$b} @ddt_list;
	@new  = pop(@temp);
	OUTER:
	foreach $ent(@temp){
		foreach $comp(@new){
			if($ent == $comp){
				next OUTER;
			}
		}
		push(@new, $ent);
	}
	
	@ddt_list = @new;
}


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
					if($person_in_charge =~ /jdrake/i) {$person_in_charge = 'jd'}
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
### update_monitor_list: update group or monitoring obsids for a given obsid            ###
###########################################################################################

sub update_monitor_list{
	($mhead) = @_;
	if($mhead =~ /group/){
		@test = @group_member;
	}else{
		@test = @monitor_series;
	}

	OUTER:
	foreach $obsid_s (@test){
		push(@group_obsid, $obsid_s);
		push(@group_poc,   $poc);
		push(@group_id,	   $test[0]);
		push(@group_seq,   $seq_nbr);
		$group_cnt++;
	}
}


###########################################################################################
### send_email: send out email when new ddt or too observation is approved              ###
###########################################################################################

sub send_email{
	($head) = @_;
	$uc_head = uc($head);

	foreach $obsid (@really_new){
		$user = ${poc.$obsid}{poc}[0];
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
#######			system("cat $temp_dir/tmp_email |mailx -s\"Subject: New $uc_head Observation \n\" -r cus\@head.cfa.harvard.edu $poc_email  cus\@head.cfa.harvard.edu");
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
        $obsid        =~ s/\s+//g;
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
	system("/opt/local/bin/lynx -source http://acis.mit.edu/cgi-bin/get-obsid\?id=$obsid > $temp_dir/ztemp");
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

