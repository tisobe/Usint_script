#! /proj/DS.ots/perl-5.10.0.SunOS5.8/bin/perl
BEGIN { $ENV{'SYBASE'} = "/soft/SYBASE_OCS15"; }

use CGI;

use Sybase::DBlib;
use Sybase::CTlib;

###############################################################################
# This is a first-draft script to dynamically create a page based on obsid.  
# It works, as far as I can tell....
# Note:  Currently, this script MUST use the above version of perl and contain
# all the use statements above.
# Ok, that's probably not true - I don't think I'm using DBlib at all.
# It is more complex to use CTlib, but I'm told by the experts that
# DBlib is going to be discontinued.
# -Roy Kilgard, April 2000
###############################################################################

#get the obsid from the CL
$obsid= $ARGV[0];

print "Content-type: text/html\n\n";

# database username, password, and server
$user="browser";
$passwd =`cat /proj/web-cxc/cgi-gen/.targpass`;
chop $passwd;
$server="ocatsqlsrv";

CONNECT: {
    $SIG{ALRM} = sub { die "timeout" };
    eval {
	alarm(5);
#open connection to sql server
	$dbh = new Sybase::CTlib $user, $passwd, $server;
# use axafocat and clean up
	$dbh->ct_execute("use axafocat");
	$dbh->ct_results($restype);
	alarm(0);
    };
}
if ($@) {
    if ($@ =~ /timeout/) {
	$server="sqlocc";
	goto CONNECT;
    } else {
	die;
    }
}

# with ctlib, you must issue the ct_cancel before you can do anything else
# even with a simple sql command like use axafocat
if ($restype == CS_CMD_FAIL){
    print "Unable to access database\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
# get remarks from target table
$dbh->ct_execute("select remarks from target where obsid=$obsid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    $remarks = $dbh->ct_fetch;
# the last is necessary because ct_results will return CS_SUCCEED 
# n+1 times, where n= the number of lines which will be returned by
# ct_execute
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafocat..target\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
# get stuff from target table, clean up
        $dbh->ct_execute("select obsid,targid,seq_nbr,targname,obj_flag,object,si_mode,photometry_flag,vmagnitude,ra,dec,est_cnt_rate,forder_cnt_rate,y_det_offset,z_det_offset,raster_scan,dither_flag,approved_exposure_time,pre_min_lead,pre_max_lead,pre_id,seg_max_num,aca_mode,phase_constraint_flag,ocat_propid,acisid,hrcid,grating,instrument,rem_exp_time,soe_st_sched_date,type,lts_lt_plan,mpcat_star_fidlight_file,status,data_rights,mp_remarks,tooid,multitelescope,observatories,roll_flag,window_flag,uninterrupt,description, group_id,obs_ao_str from target where obsid=$obsid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    @targetdata = $dbh->ct_fetch;
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafocat..target\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
# fill values from target table
# doing this the long way so I can see what I'm doing and make sure
# everything is accounted for
$targid =$targetdata[1];
$seq_nbr =$targetdata[2];
$targname =$targetdata[3];
$obj_flag =$targetdata[4];
$object = $targetdata[5];
$si_mode =$targetdata[6];
$photometry_flag =$targetdata[7];
$vmagnitude =$targetdata[8];
$ra =$targetdata[9];
$dec =$targetdata[10];
$est_cnt_rate =$targetdata[11];
$forder_cnt_rate =$targetdata[12];
$y_det_offset = $targetdata[13];
$z_det_offset = $targetdata[14];
$raster_scan = $targetdata[15];
$dither_flag = $targetdata[16];
$approved_exposure_time = $targetdata[17];
$pre_min_lead = $targetdata[18];
$pre_max_lead = $targetdata[19];
$pre_id = $targetdata[20];
$seg_max_num =$targetdata[21];
$aca_mode = $targetdata[22];
$phase_constraint_flag = $targetdata[23];
$proposal_id = $targetdata[24];
$acisid = $targetdata[25];
$hrcid = $targetdata[26];
$grating =$targetdata[27];
$instrument =$targetdata[28];
$rem_exp_time =$targetdata[29];
$soe_st_sched_date =$targetdata[30];
$type = $targetdata[31];
$lts_lt_plan =$targetdata[32];
$mpcat_star_fidlight_file = $targetdata[33];
$status = $targetdata[34];
$data_rights =$targetdata[35];
$mp_remarks = $targetdata[36];
$tooid = $targetdata[37];
$multitelescope = $targetdata[38];
$observatories = $targetdata[39];
$roll_flag = $targetdata[40];
$window_flag = $targetdata[41];
$uninterrupt_flag = $targetdata[42];
$description = $targetdata[43];
$group_id = $targetdata[44];
$obs_ao_str = $targetdata[45];

$group_id =~ s/\s+//g;  

$monitor_flag ="N";
if ($pre_id){
    $monitor_flag = "Y";
}

#get followed obsids

 $dbh->ct_execute("select distinct pre_id from target where pre_id=$obsid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    $pre_id_match = $dbh->ct_fetch;  
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafocat..target\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}

if ($pre_id_match){
   $monitor_flag = "Y";
}

if ($group_id){   
   $monitor_flag = "N";
   $pre_min_lead_group = $pre_min_lead;
   $pre_max_lead_group = $pre_max_lead;
   $pre_id_group = $pre_id;
   undef $pre_min_lead;
   undef $pre_max_lead;
   undef $pre_id;
  
   $dbh->ct_execute("select obsid from target where group_id = \'$group_id\'");
while($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    while (@group_obsid = $dbh->ct_fetch){
	$group_obsid = join("<td>", @group_obsid);
	@group = (@group, "<a href=\"\.\/target_param.cgi\?$group_obsid\">$group_obsid<\/a> ");

	}
    last;
}

# output formatting

   $group_count = 0;
   foreach (@group){
       $group_count ++;
       if(($group_count % 10) == 0){
	   @group[$group_count - 1] = "@group[$group_count - 1]<br>";
       }
   }
   $group_count .= " obsids for "
}

# get dither info

        $dbh->ct_execute("select y_amp,y_freq,y_phase,z_amp,z_freq,z_phase from dither where obsid=$obsid");
        while ($dbh->ct_results($restype) == CS_SUCCEED){
                next unless $dbh->ct_fetchable($restype);
                @ditherdata = $dbh->ct_fetch;
                last;
        }
        if ($restype == CS_CMD_FAIL){
                print "Unable to query table axafocat..dither\n";
                $dbh->ct_cancel(CS_CANCEL_ALL);
                exit(1);
        } else {
                $dbh->ct_cancel(CS_CANCEL_ALL);
        }
$y_amp = $ditherdata[0];
$y_freq = $ditherdata[1];
$y_phase = $ditherdata[2];
$z_amp = $ditherdata[3];
$z_freq = $ditherdata[4];
$z_phase = $ditherdata[5];


# if it's a too, get remarks and trigger from too table
if ($tooid) {
    $dbh->ct_execute("select type,trig,start,stop,followup,remarks from too where tooid=$tooid");
    while ($dbh->ct_results($restype) == CS_SUCCEED){    
	next unless $dbh->ct_fetchable($restype);
	@toodata = $dbh->ct_fetch;
	last;
    }
    if ($restype == CS_CMD_FAIL){
	print "Unable to query table axafocat...tooparam\n";
	$dbh->ct_cancel(CS_CANCEL_ALL);
	exit(1);
    } else {
	$dbh->ct_cancel(CS_CANCEL_ALL);
    }
    $too_type = $toodata[0];
    $too_trig = $toodata[1];
    $too_start = $toodata[2];
    $too_stop = $toodata[3];
    $too_followup = $toodata[4];
    $too_remarks = $toodata[5];
} else {
    $too_type = "NULL";
    $too_trig = "NULL";
    $too_start = "NULL";
    $too_stop = "NULL";
    $too_followup = "NULL";
    $too_remarks = "NULL";
}


# if it's an hrc observation, get values from hrcparam table
if ($hrcid){
    $dbh->ct_execute("select si_mode,trigger_level,range_switch_level,spect_mode,antico_enable,width_enable,width_threshold,uld_enable,upper_level_disc,blank_enable,u_blank_hi,v_blank_hi,u_blank_lo,v_blank_lo,py_shutter_position,my_shutter_position,hrc_zero_block,timing_mode from hrcparam where hrcid=$hrcid");
    while ($dbh->ct_results($restype) == CS_SUCCEED){    
	next unless $dbh->ct_fetchable($restype);
	@hrcdata = $dbh->ct_fetch;
	last;
    }
    if ($restype == CS_CMD_FAIL){
	print "Unable to query table axafocat..hrcparam\n";
	$dbh->ct_cancel(CS_CANCEL_ALL);
	exit(1);
    } else {
	$dbh->ct_cancel(CS_CANCEL_ALL);
    }
    $si_mode = $hrcdata[0];
    $trigger_level = $hrcdata[1];
    $range_switch_level = $hrcdata[2];
    $spect_mode = $hrcdata[3];
    $antico_enable = $hrcdata[4];
    $width_enable = $hrcdata[5];
    $width_threshold = $hrcdata[6];
    $uld_enable = $hrcdata[7];
    $upper_level_disc = $hrcdata[8];
    $blank_enable = $hrcdata[9];
    $u_blank_hi = $hrcdata[10];
    $v_blank_hi = $hrcdata[11];
    $u_blank_lo = $hrcdata[12];
    $v_blank_lo = $hrcdata[13];
    $py_shutter_position = $hrcdata[14];
    $my_shutter_position = $hrcdata[15];
    $hrc_zero_block = $hrcdata[16];
    $timing_mode = $hrcdata[17];
} else {
    $hrc_si_mode = "NULL";
    $trigger_level = "NULL";
    $range_switch_level = "NULL";
    $spect_mode = "NULL";
    $antico_enable = "NULL";
    $width_enable = "NULL";
    $width_threshold = "NULL";
    $uld_enable = "NULL";
    $upper_level_disc = "NULL";
    $blank_enable = "NULL";
    $u_blank_hi = "NULL";
    $v_blank_hi = "NULL";
    $u_blank_lo = "NULL";
    $v_blank_lo = "NULL";
    $py_shutter_position = "NULL";
    $my_shutter_position = "NULL";
    $hrc_zero_block = "NULL";
    $timing_mode = "NULL";
}



# if it's an acis observation, get values from acisparam table
if ($acisid){
    $dbh->ct_execute("select exp_mode,standard_chips,ccdi0_on,ccdi1_on,ccdi2_on,ccdi3_on,ccds0_on,ccds1_on,ccds2_on,ccds3_on,ccds4_on,ccds5_on,bep_pack,onchip_sum,onchip_row_count,onchip_column_count,frame_time,subarray,subarray_start_row,subarray_row_count,subarray_frame_time,duty_cycle,secondary_exp_count,primary_exp_time,secondary_exp_time,eventfilter,eventfilter_lower,eventfilter_higher,spwindow,bias_request,frequency,bias_after,most_efficient from acisparam where acisid=$acisid");
    while ($dbh->ct_results($restype) == CS_SUCCEED){    
	next unless $dbh->ct_fetchable($restype);
	@acisdata = $dbh->ct_fetch;
	last;
    }
    if ($restype == CS_CMD_FAIL){
	print "Unable to query table axafocat..acisparam\n";
	$dbh->ct_cancel(CS_CANCEL_ALL);
	exit(1);
    } else {
	$dbh->ct_cancel(CS_CANCEL_ALL);
    }
    $exp_mode = $acisdata[0];
    $standard_chips = $acisdata[1];
    $ccdi0_on = $acisdata[2];
    $ccdi1_on = $acisdata[3];
    $ccdi2_on = $acisdata[4];
    $ccdi3_on = $acisdata[5];
    $ccds0_on = $acisdata[6];
    $ccds1_on = $acisdata[7];
    $ccds2_on = $acisdata[8];
    $ccds3_on = $acisdata[9];
    $ccds4_on = $acisdata[10];
    $ccds5_on = $acisdata[11];
    $bep_pack = $acisdata[12];
    $onchip_sum = $acisdata[13];
    $onchip_row_count = $acisdata[14];
    $onchip_column_count = $acisdata[15];
    $frame_time = $acisdata[16];
    $subarray = $acisdata[17];
    $subarray_start_row = $acisdata[18];
    $subarray_row_count = $acisdata[19];
    $subarray_frame_time = $acisdata[20];
    $duty_cycle = $acisdata[21];
    $secondary_exp_count = $acisdata[22];
    $primary_exp_time = $acisdata[23];
    $secondary_exp_time = $acisdata[24];
    $eventfilter = $acisdata[25];
    $eventfilter_lower = $acisdata[26];
    $eventfilter_higher = $acisdata[27];
    $spwindow = $acisdata[28];
    $bias_request = $acisdata[29];
    $frequency = $acisdata[30];
    $bias_after = $acisdata[31];
    $most_efficient = $acisdata[32];
} else {
    $exp_mode = "NULL";
    $standard_chips = "NULL";
    $ccdi0_on = "NULL";
    $ccdi1_on = "NULL";
    $ccdi2_on = "NULL";
    $ccdi3_on = "NULL";
    $ccds0_on = "NULL";
    $ccds1_on = "NULL";
    $ccds2_on = "NULL";
    $ccds3_on = "NULL";
    $ccds4_on = "NULL";
    $ccds5_on = "NULL";
    $bep_pack = "NULL";
    $onchip_sum = "NULL";
    $onchip_row_count = "NULL";
    $onchip_column_count = "NULL";
    $frame_time = "NULL";
    $subarray = "NULL";
    $subarray_start_row = "NULL";
    $subarray_row_count = "NULL";
    $subarray_frame_time = "NULL";
    $duty_cycle = "NULL";
    $secondary_exp_count = "NULL";
    $primary_exp_time = "NULL";
    $secondary_exp_time = "NULL";
    $eventfilter = "NULL";
    $eventfilter_lower = "NULL";
    $eventfilter_higher = "NULL";
    $spwindow = "NULL";
    $bias_request = "NULL";
    $frequency = "NULL";
    $bias_after = "NULL";
    $most_efficient = "NULL"
}



# get values from aciswin table
$dbh->ct_execute("select chip,ordr,include_flag,start_row,start_column,width,height,lower_threshold,pha_range,sample from aciswin where obsid=$obsid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    while (@aciswindata = $dbh->ct_fetch){
	$acis_data =join("<td>",@aciswindata);
	@aciswin = (@aciswin, "<tr ALIGN=\"right\"><td> $acis_data</tr>");
}    
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafocat..aciswin\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
#$start_row = $aciswindata[0];
#$start_column = $aciswindata[1];
#$width = $aciswindata[2];
#$height = $aciswindata[3];
#$lower_threshold = $aciswindata[4];
#$pha_range = $aciswindata[5];
#$sample = $aciswindata[6];
#$order = $aciswindata[7];
#$chip = $aciswindata[8];
#$include_flag = $aciswindata[9];

# get values from phasereq
$dbh->ct_execute("select phase_period,phase_epoch,phase_start,phase_end,phase_start_margin,phase_end_margin from phasereq where obsid=$obsid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    @phasereqdata = $dbh->ct_fetch;
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafocat..phasereq\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
$phase_period = $phasereqdata[0];
$phase_epoch = $phasereqdata[1];
$phase_start = $phasereqdata[2];
$phase_end = $phasereqdata[3];
$phase_start_margin = $phasereqdata[4];
$phase_end_margin = $phasereqdata[5];
# get values from sim
$dbh->ct_execute("select trans_offset,focus_offset from sim where obsid=$obsid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    @simdata = $dbh->ct_fetch;
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafocat..sim\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
$trans_offset=$simdata[0];
$focus_offset=$simdata[1];
# get values from soe
$dbh->ct_execute("select soe_roll from soe where obsid=$obsid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    @soedata = $dbh->ct_fetch;
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafocat..prop_info\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
$roll_obs=$soedata[0];

# get values from rollreq

$dbh->ct_execute("select ordr,roll_constraint,roll,roll_tolerance from rollreq where obsid=$obsid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
  while (@rolldata = $dbh->ct_fetch){ 

      $data = join("<td><td>", @rolldata);
      
	@roll = (@roll,"<tr><td><td> $data</tr>");
   
    }
  }
if ($restype == CS_CMD_FAIL){
    print "Unable to query table rollreq\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}


#get value from timereq
$dbh->ct_execute("select ordr,window_constraint,tstart,tstop from timereq where obsid=$obsid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
  while (@timedata = $dbh->ct_fetch){ 
    $time = join("<td><td>", @timedata);  
    @time = (@time,"<tr><td><td> $time</tr>");
  }
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table timereq\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}







# get values from prop_info
$dbh->ct_execute("select prop_num,title,joint,hst_approved_time,noao_approved_time,xmm_approved_time,rxte_approved_time,vla_approved_time,vlba_approved_time from prop_info where ocat_propid=$proposal_id");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    @prop_infodata = $dbh->ct_fetch;
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafocat..prop_info\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
$proposal_number=$prop_infodata[0];
$proposal_title=$prop_infodata[1];
$proposal_joint=$prop_infodata[2]; 
$proposal_hst=$prop_infodata[3];
$proposal_noao=$prop_infodata[4];
$proposal_xmm_time=$prop_infodata[5];
$proposal_rxte_time=$prop_infodata[6];
$proposal_vla=$prop_infodata[7];
$proposal_vlba=$prop_infodata[8];


if ($proposal_xmm_time){

    $proposal_xmm = "$proposal_xmm_time ks";
}
else{
    $proposal_xmm = "";
}

if ($proposal_rxte_time){

    $proposal_rxte = "$proposal_rxte_time ks";
}
else{
    $proposal_rxte = "";
}










# switch to axafusers
$dbh->ct_execute("use axafusers");
$dbh->ct_results($restype);
if ($restype == CS_CMD_FAIL){
    print "Unable to access database axafusers\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
# get proposer's last name
$dbh->ct_execute("select last from person_short s,axafocat..prop_info p where p.ocat_propid=$proposal_id and s.pers_id=p.piid");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    @namedata = $dbh->ct_fetch;
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafusers..person_short\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
$PI_name=$namedata[0];
# if there is a co-i who is observer, get them, otherwise it's the pi
$dbh->ct_execute("select coi_contact from person_short s,axafocat..prop_info p where p.ocat_propid = $proposal_id");
while ($dbh->ct_results($restype) == CS_SUCCEED){    
    next unless $dbh->ct_fetchable($restype);
    $observerdata = $dbh->ct_fetch;
    last;
}
if ($restype == CS_CMD_FAIL){
    print "Unable to query table axafusers..person_short\n";
    $dbh->ct_cancel(CS_CANCEL_ALL);
    exit(1);
} else {
    $dbh->ct_cancel(CS_CANCEL_ALL);
}
if ($observerdata =~/N/){
    $Observer=$PI_name;
} else {
    $dbh->ct_execute("select last from person_short s,axafocat..prop_info p where p.ocat_propid = $proposal_id and p.coin_id = s.pers_id");
    while ($dbh->ct_results($restype) == CS_SUCCEED){    
	next unless $dbh->ct_fetchable($restype);
	$observerdata = $dbh->ct_fetch;
	last;
    }
    if ($restype == CS_CMD_FAIL){
	print "Unable to query table axafusers..person_short\n";
	$dbh->ct_cancel(CS_CANCEL_ALL);
	exit(1);
    } else {
	$dbh->ct_cancel(CS_CANCEL_ALL);
    }
    $Observer=$observerdata;
}

$dra= "$ra";
$ddec= "$dec";
$dra =~ s/\s+//g; 
$ddec =~ s/\s+//g; 
##### Convert $ra from decimal to hms
$hh = int($ra/15);
$mm = 60 * ($ra / 15 - $hh);
$ss = 60 * ($mm - int($mm));
$secrollover = sprintf("%02f", $ss);
if ($secrollover == 60) {
    $ss = abs($ss - 60);
    $mm = ($mm +1 );
}
if ($mm == 60) {
    $mm = ($mm - 60);
    $hh = ($hh + 1);
}
$ra = sprintf("%02d:%02d:%05.2f", $hh, $mm, $ss);
##### Convert $dec from decimal to dms
if ($dec < 0) { # set sign
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
$dec = sprintf("%.1s%02d:%02d:%05.2f", $sign, $dd, $mm, $ss); 

# these ~100 lines are to remove the whitespace from most of
# the obscat dump entries.  
$targid =~ s/\s+//g; 
$seq_nbr =~ s/\s+//g; 
$targname =~ s/\s+//g; 
$obj_flag =~ s/\s+//g; 
$object =~ s/\s+//g; 
$si_mode =~ s/\s+//g; 
$photometry_flag =~ s/\s+//g; 
$vmagnitude =~ s/\s+//g; 
$ra =~ s/\s+//g; 
$dec =~ s/\s+//g; 
$est_cnt_rate =~ s/\s+//g; 
$forder_cnt_rate =~ s/\s+//g; 
$y_det_offset =~ s/\s+//g; 
$z_det_offset =~ s/\s+//g; 
$raster_scan =~ s/\s+//g; 
$defocus =~ s/\s+//g; 
$dither_flag =~ s/\s+//g; 
$roll =~ s/\s+//g; 
$roll_tolerance =~ s/\s+//g; 
$approved_exposure_time =~ s/\s+//g; 
$pre_min_lead =~ s/\s+//g; 
$pre_max_lead =~ s/\s+//g; 
$pre_id =~ s/\s+//g; 
$seg_max_num =~ s/\s+//g; 
$aca_mode =~ s/\s+//g; 
$phase_constraint_flag =~ s/\s+//g; 
$proposal_id =~ s/\s+//g; 
$acisid =~ s/\s+//g; 
$hrcid =~ s/\s+//g; 
$grating =~ s/\s+//g; 
$instrument =~ s/\s+//g; 
$rem_exp_time =~ s/\s+//g; 
$soe_st_sched_date =~ s/\s\s\s+//g; 
$type =~ s/\s+//g; 
$lts_lt_plan =~ s/\s\s\s+//g; 
#$mpcat_star_fidlight_file =~ s/\s+//g; 
$status =~ s/\s+//g; 
$data_rights =~ s/\s+//g; 
$server_name =~ s/\s+//g; 
$trigger_level =~ s/\s+//g;  
$range_switch_level =~ s/\s+//g;  
$spect_mode =~ s/\s+//g;  
$antico_enable =~ s/\s+//g;  
$width_enable =~ s/\s+//g;  
$width_threshold =~ s/\s+//g;  
$uld_enable =~ s/\s+//g;  
$upper_level_disc =~ s/\s+//g;  
$blank_enable =~ s/\s+//g;  
$u_blank_hi =~ s/\s+//g;  
$v_blank_hi =~ s/\s+//g;  
$u_blank_lo =~ s/\s+//g;  
$v_blank_lo= ~ s/\s+//g; 
$py_shutter_position =~ s/\s+//g;  
$my_shutter_position =~ s/\s+//g;  
$hrc_zero_block =~ s/\s+//g;  
$timing_mode =~ s/\s+//g;  
$exp_mode =~ s/\s+//g; 
$standard_chips =~ s/\s+//g; 
$ccdi0_on =~ s/\s+//g; 
$ccdi1_on =~ s/\s+//g; 
$ccdi2_on =~ s/\s+//g; 
$ccdi3_on =~ s/\s+//g; 
$ccds0_on =~ s/\s+//g; 
$ccds1_on =~ s/\s+//g; 
$ccds2_on =~ s/\s+//g; 
$ccds3_on =~ s/\s+//g; 
$ccds4_on =~ s/\s+//g; 
$ccds5_on =~ s/\s+//g; 
$bep_pack =~ s/\s+//g; 
$onchip_sum =~ s/\s+//g; 
$onchip_row_count =~ s/\s+//g; 
$onchip_column_count =~ s/\s+//g; 
$frame_time =~ s/\s+//g; 
$subarray =~ s/\s+//g; 
$subarray_start_row =~ s/\s+//g; 
$subarray_row_count =~ s/\s+//g; 
$subarray_frame_time =~ s/\s+//g; 
$duty_cycle =~ s/\s+//g; 
$secondary_exp_count =~ s/\s+//g; 
$primary_exp_time =~ s/\s+//g; 
$secondary_exp_time =~ s/\s+//g; 
$eventfilter =~ s/\s+//g; 
$eventfilter_lower =~ s/\s+//g; 
$eventfilter_higher =~ s/\s+//g; 
$spwindow =~ s/\s+//g; 
$start_row =~ s/\s+//g; 
$start_column =~ s/\s+//g; 
$width =~ s/\s+//g; 
$height =~ s/\s+//g; 
$lower_threshold =~ s/\s+//g; 
$pha_range =~ s/\s+//g; 
$sample =~ s/\s+//g; 
$bias_request =~ s/\s+//g; 
$frequency =~ s/\s+//g; 
$bias_after =~ s/\s+//g; 
$most_efficient =~ s/\s+//g; 
$phase_period =~ s/\s+//g; 
$phase_epoch =~ s/\s+//g; 
$phase_start =~ s/\s+//g; 
$phase_end =~ s/\s+//g; 
$phase_start_margin =~ s/\s+//g; 
$phase_end_margin =~ s/\s+//g; 
$PI_name =~ s/\s+//g; 
$proposal_number =~ s/\s+//g; 
$proposal_joint =~ s/\s+//g; 
$proposal_hst =~ s/\s+//g;
$proposal_noao =~ s/\s+//g;
$proposal_xmm =~ s/\s+//g;
$trans_offset =~ s/\s+//g; 
$focus_offset =~ s/\s+//g;
$order =~ s/\s+//g; 
$chip =~ s/\s+//g;
$include_flag =~ s/\s+//g;
$roll_obs =~ s/\s+//g;
$multitelescope =~ s/\s+//g;
$observatories =~ s/\s+//g;
$too_type =~ s/\s+//g;
$too_start =~ s/\s+//g;
$too_stop =~ s/\s+//g;
$too_followup =~ s/\s+//g;
$roll_flag =~ s/\s+//g; 
$window_flag =~ s/\s+//g; 
$uninterrupt_flag =~ s/\s+//g; 
$rollordr =~ s/\s+//g; 
$roll_constraint =~ s/\s+//g; 
$group_id =~ s/\s+//g;
$obs_ao_str =~ s/\s+//g; 
$description =~ s/\s+//g;
$y_amp =~ s/\s+//g; 
$y_freq =~ s/\s+//g; 
$y_phase =~ s/\s+//g; 
$z_amp =~ s/\s+//g;
$z_freq =~ s/\s+//g; 
$z_phase =~ s/\s+//g; 
$proposal_rxte=~ s/\s+//g;
$proposal_vla=~ s/\s+//g;
$proposal_vlba=~ s/\s+//g;



# Truncate the decimals from Roll Observed (it's not that precise)
if ($roll_obs) {
    $roll_obsr = sprintf("%.f", $roll_obs);
    $roll_obsr = "$roll_obsr degrees";
}





print <<ENDOFHTML;
<HTML>
<HEAD>
<TITLE>Obscat Data Page</TITLE>
<BODY BGCOLOR="#FFFFFF">
<h1>Obscat Data Page</h1>

A brief description of the listed parameters is given <a href='https://icxc-test.cfa.harvard.edu/cgi-bin/obs_ss/user_help.html',target='_blank'>here.</a><p>

<h2>General Parameters</h2>
<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Sequence Number:</th><td>$seq_nbr</td><th>Status:</th><td>$status</td><th>ObsID #:</th><td>$obsid</td><th>Proposal Number:</th><td>$proposal_number</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Proposal Title:</th><td>$proposal_title</td></tr></table>


<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Obs AO Status:</th><td>$obs_ao_str</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Target Name:</th><td>$targname</td><th>SI Mode:</th><td>$si_mode</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Instrument:</th><td>$instrument</td><th>Grating:</th><td>$grating</td><th>Type:</th><td>$type</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>PI Name:</th><td>$PI_name</td><th>Observer:</th><td>$Observer</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Exposure Time:</th><td>$approved_exposure_time ks</td><TH>Remaining Exposure Time:</TH><TD>$rem_exp_time ks</TD></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Joint Proposal:</th><td>$proposal_joint</td></tr>
<tr><Td><td><th>HST Approved Time:</th><td>$proposal_hst</td><th>NOAO Approved Time:</th><td>$proposal_noao</td></tr>
<tr><Td><td><th>XMM Approved Time:</th><td>$proposal_xmm </td><th>RXTE Approved Time:<td>$proposal_rxte<td></tr>
<tr><Td><td><th>VLA Approved Time:<td>$proposal_vla<th>VLBA Approved Time:<td>$proposal_vlba</tr>

</table>


<table cellspacing=0 cellpadding=4>
<tr><td></td><th>Schedule Date:<td>$soe_st_sched_date<th>LTS Date:<td>$lts_lt_plan</tr></Table>


<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>RA:</th><td>$ra</td><th>Dec:</th><td>$dec</td><th>Roll Observed:</th><td>$roll_obsr</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>RA:</th><td>$dra</td><th>Dec:</th><td>$ddec</td><td></tr></table>


<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Offset: Y:</th><td>$y_det_offset arcmin</td><th>Z:</th><td>$z_det_offset arcmin</td></tr>
<tr><td><th>Sim-Z:</th><td>$trans_offset mm<td>
<th>Sim-Focus:</th><td>$focus_offset mm</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Focus:</th><td>$defocus</td><th>Raster Scan:</th><td>$raster_scan</td></tr>
</table>

<table cellspacing=0 cellpadding=4><tr><td>
<th>Dither:</th><td>$dither_flag</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td><td><td><th>y_amp:<td>$y_amp<Th>y_freq:<td>$y_freq<th>y_phase:<td>$y_phase</tr>
<tr><td><td><td><th>z_amp:<td>$z_amp<th>z_freq:<td>$z_freq<th>z_phase:<td>$z_phase</tr>
</table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Solar System Object:</th><td>$obj_flag</td><th>Object:</th><td>$object</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td>
<th>Photometry:</th><td>$photometry_flag</td><th>V Mag:</th><td>$vmagnitude</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Count Rate:</th><td>$est_cnt_rate</td><th>1st Order Rate:</th><td>$forder_cnt_rate</td></tr></table>

<hr>

<h2>Time Constraints</h2>

<table cellspacing=0 cellpadding=4>
<tr><td></td><th> Time Constraint:<td>$window_flag</tr></table>
<table cellspacing=0 cellpadding=4>
<tr><td></td><th><u>Order</u><td>
<th><u>Window constraint</u></th><td><th><u>Start</u></th><td></td><th><u>Stop</u></th><td></td></tr><tr><td>@time</table>

<hr>

<h2>Roll Constraints</h2>

<table cellspacing=0 cellpadding=4>
<tr><td></td><th> Roll Constraint:<td>$roll_flag</tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td><th><u>Order</u><td>
<th><u>Roll Angle Constraints</u></th><td><th><u>Roll Angle</u></th><td><th><u>Tolerance</u></th><td></td><td>$rollordr<td></tr><tr>@roll</table>

<hr>

<h2>Other Constraints</h2>

<table cellspacing=0 cellpadding=4>
<tr><td>
<th>Phase Constraint:</th><td>$phase_constraint_flag</td></table>

<table cellspacing=0 cellpadding=4>
<tr><td><td>
<th>Epoch:</th><td>$phase_epoch</td><th>Period:</th><td>$phase_period</td></tr>
<tr><td></td><td>
<th>Min:</th><td>$phase_start</td><th>Min Err:</th><td>$phase_start_margin</td></tr>
<tr><td><td>
<th>Max:</th><td>$phase_end</td><th>Max Err:</th><td>$phase_end_margin</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Monitoring Observation:<td> <td>$monitor_flag</table>

<table cellspacing=0 cellpadding=4>
<tr><td><td></td>
<th>Follows ObsID#:</th><td>$pre_id</td><th>Min Int:</th><td>$pre_min_lead</td><th>Max Int:</th><td>$pre_max_lead</td></tr></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td><td>Note: If Min Int and Max Int are set to 'NULL', this is not a monitoring observation</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Coordinated Observation:</th><td>$multitelescope</td><th>Observatories:</th><td>$observatories</td></td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Uninterrupt: </th><td>$uninterrupt_flag</td></td></td></tr></table>

<hr>
<h2>Group Parameters</h2>
<table cellspacing=0 cellpadding=4>
<tr valign=top><td></td>
<th>Group ID<td>$group_id<th>Follows ObsID#:</th><td>$pre_id_group</td><th>Min Int:</th><td>$pre_min_lead_group</td><th>Max Int:</th><td>$pre_max_lead_group</td></tr></table>
<table cellspacing=0 cellpadding=4>
<tr valign=top><td></td>
<th>$group_count $group_id<td>@group</tr>
</tr></table>

<hr>

<h2>HRC Parameters</h2>
<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Timing Mode:</th><td>$timing_mode</td><th>Zero Block:</th><td>$hrc_zero_block</td><th>SI Mode:<td></tr></table>

<hr>

<h2>ACIS Parameters</h2>
<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>ACIS Exposure Mode:</th><td>$exp_mode</td><th>Event TM Format:</th><td>$bep_pack<th>Frame Time:</th><td>$frame_time</td></tr>
<tr><td><td><td>
</table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Standard Chips:</th><td>$standard_chips</td></tr></table>

<center><table cellspacing=0 cellpadding=4>
<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
<th>I0:</th><td>$ccdi0_on</td><th>I1:</th><td>$ccdi1_on</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>
<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><th>I2:</th><td>$ccdi2_on</td><th>I3:</th><td>$ccdi3_on</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
<tr><th>S0:</th><td>$ccds0_on</td><th>S1:</th><td>$ccds1_on</td><th>S2:</th><td>$ccds2_on</td><th>S3:</th><td>$ccds3_on</td><th>S4:</th><td>$ccds4_on</td><th>S5:</th><td>$ccds5_on</td></tr></table></center><p>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Subarray Type:</th><td>$subarray</td>
</tr>
<tr>
<td></td>
<th>Start:</th><td>$subarray_start_row</td><th>Rows:</th><td>$subarray_row_count<td><th>Frame Time:</th><td>$subarray_frame_time</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Duty Cycle:</th><td>$duty_cycle</td><th>Number:</th><td>$secondary_exp_count</td><th>Tprimary:</th><td>$primary_exp_time</td><th>Tsecondary:</th><td>$secondary_exp_time</td><th>Most Efficient:</th><td>$most_efficient</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Onchip Summing:</th><td>$onchip_sum</td><th>Rows:</th><td>$onchip_row_count</td><th>Columns:</th><td>$onchip_column_count</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Event Filter:</th><td>$eventfilter</td><th>Lower:</th><td>$eventfilter_lower</td><th>Range:</th><td>$eventfilter_higher</td></tr></table>

<table cellspacing=0 cellpadding=4 >
<tr>
<th> &nbsp;Window Filter:</th>

<tr><th><u>Chip</u><th><u>Rank</u><th><u>Type</u><th><u>Start Row</u><th><u>Start Column</u><th><u>Height</u><th><u>Width</u><th><u>Lower Energy</u><th><u>Energy Range</u><th><u>Sample Rate</u></th></tr> <tr>@aciswin
</tr>
</table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th>Bias:</th><td>$bias_request</td><th>Frequency:</th><td>$frequency</td><th>After:</th><td>$bias_after</td></tr></table>

<hr>

<h2>TOO Parameters</h2>



<table cellspacing=0 cellpadding=4>
<tr>
<td><th>TOO_ID:</th><td></td><th>TOO Trigger:</th><td>"$too_trig"</td>
<th>TOO Type:</th><td>$too_type</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td><th>Exact response window (days):</th></tr>
<tr><td><td>
<th>Start:</th><td>$too_start</td><th>Stop:</th><td>$too_stop</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th># of Follow-up Observations:</th><td>$too_followup</td></tr></table>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th valign=top>TOO Remarks:</th><td>"$too_remarks"</td></tr></table>

<hr>

<h2>Additional Remarks</h2>

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th valign=top>Remarks:</th><td>"$remarks"</td></tr></table> 

<table cellspacing=0 cellpadding=4>
<tr><td></td>
<th valign=top>MP Remarks:</th><td>"$mp_remarks"</td></tr></table> 

<P><B><A HREF="https://icxc-test.cfa.harvard.edu/cgi-bin/obs_ss/ocatdata2html.cgi?$obsid">Link to internal parameter update form: INTERNAL ACCESS ONLY</A></B>

ENDOFHTML

print "</BODY>";
print "</HTML>";
exit();



