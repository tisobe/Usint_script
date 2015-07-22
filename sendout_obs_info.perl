#!/usr/bin/perl

BEGIN { $ENV{'SYBASE'} = "/soft/sybase"; }
use DBI;
use DBD::Sybase;

#########################################################################################################
#													#
#	sendout_obs_info.perl: send out database entries in a plane format of newly submitted		#
#  				observations								#
#													#
#		author: t. isobe (tisobe @cfa.harvard.edu)						#
#													#
#		last update: Jan 23, 2008								#
#													#
#########################################################################################################

#
#---- set directory pathes
#

$obs_ss   = '/proj/web-icxc/cgi-bin/obs_ss/';                   #--- none usint user site
$pass_dir = '/proj/web-icxc/cgi-bin/obs_ss/.Pass_dir/';         #--- a directory contatins user name file etc
$temp_dir = '/data/mta4/www/CUS/Usint/Temp/';                   #--- a temporary file is created in this directory
$ocat_dir = '/data/udoc1/ocat/';
$data_dir = './';

#
#---- find today's date
#

($lsec, $lmin, $lhour, $lmday, $lmon, $lyear, $lwday, $lyday, $lisdst) = localtime(time);

$lyear += 1900;
$lyday += 1;

if($lyday < 10){
	$lyday = '00'."$lyday";
}elsif($lyday < 100){
	$lyday = '0'."$lyday";
}

if($lhour < 10){
	$lhour = '0'."$lhour";
}

if($lmin < 10){
	$lmin = '0'."$lmin";
}

if($lsec < 10){
	$lsec = '0'."$lsec";
}

#
#---- print header
#

open(OUT, '> ztemp');

	print OUT "#Date: $lyear:$lyday:$lhour:$lmin:$lsec\n";
	print OUT "#\n";
	print OUT "#";
	print OUT "obsid\t";
	print OUT "targid\t";
	print OUT "seq_nbr\t";
	print OUT "targname\t";
	print OUT "obj_flag\t";
	print OUT "object\t";
	print OUT "si_mode\t";
	print OUT "photometry_flag\t";
	print OUT "vmagnitude\t";
	print OUT "ra\t";
	print OUT "dec\t";
	print OUT "est_cnt_rate\t";
	print OUT "forder_cnt_rate\t";
	print OUT "y_det_offset\t";
	print OUT "z_det_offset\t";
	print OUT "raster_scan\t";
	print OUT "defocus\t";
	print OUT "dither_flag\t";
	print OUT "roll\t";
	print OUT "roll_tolerance\t";
	print OUT "approved_exposure_time\t";
	print OUT "pre_min_lead\t";
	print OUT "pre_max_lead\t";
	print OUT "pre_id\t";
	print OUT "seg_max_num\t";
	print OUT "aca_mode\t";
	print OUT "phase_constraint_flag\t";
	print OUT "proposal_id\t";
	print OUT "acisid\t";
	print OUT "hrcid\t";
	print OUT "grating\t";
	print OUT "instrument\t";
	print OUT "rem_exp_time\t";
	print OUT "type\t";
	print OUT "mpcat_star_fidlight_file\t";
	print OUT "status\t";
	print OUT "data_rights\t";
	print OUT "server_name\t";
	print OUT "hrc_zero_block\t";
	print OUT "hrc_timing_mode\t";
	print OUT "hrc_si_mode\t";
	print OUT "exp_mode\t";
	print OUT "ccdi0_on\t";
	print OUT "ccdi1_on\t";
	print OUT "ccdi2_on\t";
	print OUT "ccdi3_on\t";
	print OUT "ccds0_on\t";
	print OUT "ccds1_on\t";
	print OUT "ccds2_on\t";
	print OUT "ccds3_on\t";
	print OUT "ccds4_on\t";
	print OUT "ccds5_on\t";
	print OUT "bep_pack\t";
	print OUT "onchip_sum\t";
	print OUT "onchip_row_count\t";
	print OUT "onchip_column_count\t";
	print OUT "frame_time\t";
	print OUT "subarray\t";
	print OUT "subarray_start_row\t";
	print OUT "subarray_row_count\t";
	print OUT "subarray_frame_time\t";
	print OUT "duty_cycle\t";
	print OUT "secondary_exp_count\t";
	print OUT "primary_exp_time\t";
	print OUT "secondary_exp_time\t";
	print OUT "eventfilter\t";
	print OUT "eventfilter_lower\t";
	print OUT "eventfilter_higher\t";
	print OUT "spwindow\t";
	print OUT "phase_period\t";
	print OUT "phase_epoch\t";
	print OUT "phase_start\t";
	print OUT "phase_end\t";
	print OUT "phase_start_margin\t";
	print OUT "phase_end_margin\t";
	print OUT "PI_name\t";
	print OUT "proposal_number\t";
	print OUT "trans_offset\t";
	print OUT "focus_offset\t";
	print OUT "tooid\t";
	print OUT "description\t";
	print OUT "total_fld_cnt_rate\t";
	print OUT "extended_src\t";
	print OUT "y_amp\t";
	print OUT "y_freq\t";
	print OUT "y_phase\t";
	print OUT "z_amp\t";
	print OUT "z_freq\t";
	print OUT "z_phase\t";
	print OUT "most_efficient\t";
	print OUT "fep\t";
	print OUT "dropped_chip_count\t";
	print OUT "timing_mode\t";
	print OUT "uninterrupt\t";
	print OUT "proposal_joint\t";
	print OUT "proposal_hst\t";
	print OUT "proposal_noao\t";
	print OUT "proposal_xmm\t";
	print OUT "roll_obsr\t";
	print OUT "multitelescope\t";
	print OUT "observatories\t";
	print OUT "too_type\t";
	print OUT "too_start\t";
	print OUT "too_stop\t";
	print OUT "too_followup\t";
	print OUT "roll_flag\t";
	print OUT "window_flag\t";
	print OUT "group_id\t";
	print OUT "obs_ao_str\t";

	print OUT "mp_remarks\t";
        print OUT "constr_in_remarks\t";
	print OUT "too_remarks\n";
	print OUT "#\n";
	print OUT "#================================================================================\n";
	print OUT "#\n";
#
#---- read the last entry list
#

open(FH, "$obs_ss/past_updates_table");
$last_data = '';
while(<FH>){
	chomp $_;
	$last_data = $_;
}
close(FH);

#
#---- read the current entry list
#

open(FH, "$ocat_dir/updates_table.list");
$chk = 0;
@obsid_list = ();
while(<FH>){
	chomp $_;
	if($_ =~ /$last_data/){
		$chk++;
	}
#
#---- find which ones are new for today
#
	if($chk > 0){
		@atemp = split(/\./, $_);
		push(@obsid_list, $atemp[0]);
	}
}
close(FH);

#
#---- copy the current list 
#

system("mv $obs_ss/past_updates_table $obs_ss/past_updates_table~");
system("cp $ocat_dir/updates_table.list $obs_ss/past_updates_table");

#
#---- read the data for each obsid
#

$count_entry = 0;
foreach $obsid (@obsid_list){

	$count_entry++;
	read_databases();		#---- sub to extract data from the database

	print OUT "'$obsid'\t";
	print OUT "'$targid'\t";
	print OUT "'$seq_nbr'\t";
	print OUT "'$targname'\t";
	print OUT "'$obj_flag'\t";
	print OUT "'$object'\t";
	print OUT "'$si_mode'\t";
	print OUT "'$photometry_flag'\t";
	print OUT "'$vmagnitude'\t";
	print OUT "'$ra'\t";
	print OUT "'$dec'\t";
	print OUT "'$est_cnt_rate'\t";
	print OUT "'$forder_cnt_rate'\t";
	print OUT "'$y_det_offset'\t";
	print OUT "'$z_det_offset'\t";
	print OUT "'$raster_scan'\t";
	print OUT "'$defocus'\t";
	print OUT "'$dither_flag'\t";
	print OUT "'$roll'\t";
	print OUT "'$roll_tolerance'\t";
	print OUT "'$approved_exposure_time'\t";
	print OUT "'$pre_min_lead'\t";
	print OUT "'$pre_max_lead'\t";
	print OUT "'$pre_id'\t";
	print OUT "'$seg_max_num'\t";
	print OUT "'$aca_mode'\t";
	print OUT "'$phase_constraint_flag'\t";
	print OUT "'$proposal_id'\t";
	print OUT "'$acisid'\t";
	print OUT "'$hrcid'\t";
	print OUT "'$grating'\t";
	print OUT "'$instrument'\t";
	print OUT "'$rem_exp_time'\t";
	print OUT "'$type'\t";
	print OUT "'$mpcat_star_fidlight_file'\t";
	print OUT "'$status'\t";
	print OUT "'$data_rights'\t";
	print OUT "'$server_name'\t";
	print OUT "'$hrc_zero_block'\t";
	print OUT "'$hrc_timing_mode'\t";
	print OUT "'$hrc_si_mode'\t";
	print OUT "'$exp_mode'\t";
	print OUT "'$ccdi0_on'\t";
	print OUT "'$ccdi1_on'\t";
	print OUT "'$ccdi2_on'\t";
	print OUT "'$ccdi3_on'\t";
	print OUT "'$ccds0_on'\t";
	print OUT "'$ccds1_on'\t";
	print OUT "'$ccds2_on'\t";
	print OUT "'$ccds3_on'\t";
	print OUT "'$ccds4_on'\t";
	print OUT "'$ccds5_on'\t";
	print OUT "'$bep_pack'\t";
	print OUT "'$onchip_sum'\t";
	print OUT "'$onchip_row_count'\t";
	print OUT "'$onchip_column_count'\t";
	print OUT "'$frame_time'\t";
	print OUT "'$subarray'\t";
	print OUT "'$subarray_start_row'\t";
	print OUT "'$subarray_row_count'\t";
	print OUT "'$subarray_frame_time'\t";
	print OUT "'$duty_cycle'\t";
	print OUT "'$secondary_exp_count'\t";
	print OUT "'$primary_exp_time'\t";
	print OUT "'$secondary_exp_time'\t";
	print OUT "'$eventfilter'\t";
	print OUT "'$eventfilter_lower'\t";
	print OUT "'$eventfilter_higher'\t";
	print OUT "'$spwindow'\t";
	print OUT "'$phase_period'\t";
	print OUT "'$phase_epoch'\t";
	print OUT "'$phase_start'\t";
	print OUT "'$phase_end'\t";
	print OUT "'$phase_start_margin'\t";
	print OUT "'$phase_end_margin'\t";
	print OUT "'$PI_name'\t";
	print OUT "'$proposal_number'\t";
	print OUT "'$trans_offset'\t";
	print OUT "'$focus_offset'\t";
	print OUT "'$tooid'\t";
	print OUT "'$description'\t";
	print OUT "'$total_fld_cnt_rate'\t";
	print OUT "'$extended_src'\t";
	print OUT "'$y_amp'\t";
	print OUT "'$y_freq'\t";
	print OUT "'$y_phase'\t";
	print OUT "'$z_amp'\t";
	print OUT "'$z_freq'\t";
	print OUT "'$z_phase'\t";
	print OUT "'$most_efficient'\t";
	print OUT "'$fep'\t";
	print OUT "'$dropped_chip_count'\t";
	print OUT "'$timing_mode'\t";
	print OUT "'$uninterrupt'\t";
	print OUT "'$proposal_joint'\t";
	print OUT "'$proposal_hst'\t";
	print OUT "'$proposal_noao'\t";
	print OUT "'$proposal_xmm'\t";
	print OUT "'$roll_obsr'\t";
	print OUT "'$multitelescope'\t";
	print OUT "'$observatories'\t";
	print OUT "'$too_type'\t";
	print OUT "'$too_start'\t";
	print OUT "'$too_stop'\t";
	print OUT "'$too_followup'\t";
	print OUT "'$roll_flag'\t";
	print OUT "'$window_flag'\t";
	print OUT "'$group_id'\t";
	print OUT "'$obs_ao_str'\t";

	print OUT "'$mp_remarks'\t";
        print OUT "'$constr_in_remarks'\t";
	print OUT "'$too_remarks'\n";
}

close(OUT);

#
#--- cus email address
#

$cus_email  = 'cus@head.cfa.harvard.edu';

#
#--- send out eamil, if there are any new submitted observations
#

if($count_entry > 0){
	system("cat ztemp |mailx -s \"Subject: Newly Submitted Observations\n\" -r  $cus_email -c $cus_email isobe\@head.cfa.harvard.edu emk\@cfa.harvard.edu");
###	system("cat ztemp | mailx -s \"Subject: Newly Submitted Observations\n\"  -r $cus_email  isobe\@head.cfa.harvard.edu");

system("rm ztemp");
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
		tooid, constr_in_remarks, group_id, obs_ao_str, roll_flag, window_flag, spwindow_flag
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
			most_efficient, dropped_chip_count

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
		$ordr  = $aciswindata[0];			# here is the win_ordr
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
	$spwindow 		=~ s/\s+//g; 
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
		EVENTFILTER_HIGHER,SPWINDOW,ORDR, FEP,DROPPED_CHIP_COUNT, BIAS_RREQUEST,
		TOO_ID,TOO_TRIG,TOO_TYPE,TOO_START,TOO_STOP,TOO_FOLLOWUP,TOO_REMARKS,
		REMARKS,COMMENTS,
		MONITOR_FLAG				#---- this one is added 3/1/06
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
		Y_FREQ_ASEC, Z_FREQ_ASEC, UNINTERRUPT,OBJ_FLAG,OBJECT,PHOTOMETRY_FALG,
		VMAGNITUDE,EST_CNT_RATE, FORDER_CNT_RATE, TIME_ORDR,WINDOW_FLAG, ROLL_ORDR,ROLL_FLAG,
		CONSTR_IN_REMARKS,PHASE_CONSTRAINT_FLAG,PHASE_EPOCH,PHASE_PERIOD,
		PHASE_START,PHASE_START_MARGIN, PHASE_END,PHASE_END_MARGIN,
		PRE_ID,PRE_MIN_LEAD,PRE_MAX_LEAD,MULTITELESCOPE, OBSERVATORIES,
		HRC_CONFIG,HRC_ZERO_BLOCK,HRC_TIMING_MODE,HRC_SI_MODE,
		EXP_MODE,BEP_PACK,FRAME_TIME,MOST_EFFICIENT,
		CCDI0_ON, CCDI1_ON, CCDI2_ON, CCDI3_ON, CCDS0_ON, CCDS1_ON, 
		CCDS2_ON, CCDS3_ON,CCDS4_ON, CCDS5_ON,
		SUBARRAY,SUBARRAY_START_ROW,SUBARRAY_ROW_COUNT,
		DUTY_CYCLE,SECONDARY_EXP_COUNT,PRIMARY_EXP_TIME,
		ONCHIP_SUM,ONCHIP_ROW_COUNT,ONCHIP_COLUMN_COUNT,EVENTFILTER,EVENTFILTER_LOWER,
		EVENTFILTER_HIGHER,SPWINDOW,ORDR, 
		REMARKS,COMMENTS, ACISTAG,ACISWINTAG,SITAG,GENERALTAG,
		DROPPED_CHIP_COUNT, GROUP_ID, MONITOR_FLAG
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
		EVENTFILTER_HIGHER,DROPPED_CHIP_COUNT,SPWINDOW
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
		       PHA_RANGE,SAMPLE,ORDR,CHIP,
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
			MULTITELESCOPE, OBSERVATORIES, ROLL_CONSTRAINT, WINDOW_CONSTRAINT, 
			ROLL_ORDR, TIME_ORDR, ROLL_180,CONSTR_IN_REMARKS,ROLL_FLAG,WINDOW_FLAG,
			MONITOR_FLAG
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

