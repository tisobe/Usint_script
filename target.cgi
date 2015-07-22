#!/usr/local/bin/perl
#!/proj/cm/DS.ots/Sun-Solaris.v2.6/bin/perl
#
# Purpose:
# ~~~~~~~
# This script generates the Sequence Number
# Summary page:
# http://asc.harvard.edu/cgi-gen/mp/target.cgi?seq#
# where seq# is the target's sequence number.
# When given a sequence number, the script
# reads information about that number from the
# axafocat database.  The output on the sequence 
# number summary page includes the abstract, PI, 
# number of ObsIds for the sequence number and any 
# constraints and/or preferences for these ObsIds. 
#
# Notes:
# ~~~~~~
# 2/19/03 - Updated by J. Hagler to accommodate changes to
#   axafocat made in March, 2003. Specifically, time/window and
#   roll constraints are stored in  separate tables
#   ('timreq' and 'rollreq') to allow for multiple
#   constraints/preferences. -JH
# 8/6/03 - It turns out that mission planning
#   maintains this script (which we no longer
#   even knew existed).  I am updating the
#   server alias because the old one "axafusersrv"
#   is not reliable.  Instead I add in a 
#   check to see if the server works, and if
#   not I use an alternate server.  Also all
#   the webpages have been changed from "asc" 
#   to "cxc".  -MM
# 10/14/03 - Updated so that script will now denote:
#   - Constraints in remakrs
#   - Group observations
#   - Monitoring observations (though not first in series, yet)
#   ~ a la slamassa (SL)
# 10/16/03 - Updated script:
#   - Changed query format from CTlib to DBI
#   - Script now denotes first observation
#     in a monitoring series (woo-hoo! had to change
#     to DBI format for this to work!!!)
#   - Denote uninterrupt constraint (it hadn't before,
#     this must've slipped through the cracks!)
#   ~ a la slamassa (SL)
# 12/9/03 - Updated path to password file
#   - There was a server change so now this script is located
#     in /proj/web-cxc/cgi-gen/mp and the password file
#     in /proj/web-cxc/cgi-gen
#   ~ a la slamassa (SL)
#
#  1/6/03 - Updated script:
#   - Sometimes, "constraints in remarks" field in database is 
#     marked Y when the remarks are blank.
#     Script now checks for this possibility and does not ouput
#     "CONST in REM" if this is the case.
#   ~ a la slamassa (SL)
#

BEGIN { 
    $ENV{'SYBASE'} = "/soft/sybase"; 
}

#use strict;
use Carp;
use CGI qw( :standard );
use DBI;
use DBD::Sybase;

my $user = 'browser';
# server change: path name changes from /proj/ascwww/AXAF/extra/science/
# to  /proj/web-cxc
my $password = `cat /proj/web-cxc/cgi-gen/.targpass`;
chomp $password;

my $seq = $ARGV[0];

#my $MPURL = 'asclocal/mp/SEQNBR';
my $MPURL = 'targets';
#my $MPDIR = '/data/mp1/SEQNBR';
#my $MPDIR = '/data/udoc1/targets';
my $MPDIR = '/data/targets';

my $db  = "server=ocatsqlsrv;database=axafocat";
my $dsn = "DBI:Sybase:$db";

my %CatHash = (
	       '1'  => 'Solar System and Misc.',
	       '2'  => 'Normal Stars and WD',
	       '3'  => 'WD Binaries and CVs',
	       '4'  => 'BH and NS Binaries',
	       '5'  => 'SN, SNR, and isolated NS',
	       '6'  => 'Normal Galaxies',
	       '7'  => 'Active Galaxies and Quasars',
	       '8'  => 'Clusters of Galaxies',
	       '9'  => 'Diffuse Emission and Surveys',
	       );
$seq =~ /(^\d)/;
my $category = $CatHash{$1};

print header,
    "\n\n",
    start_html(-title   => "Summary of sequence number $seq",
	       -BGCOLOR => 'white',
	       -LINK    => "#0000EE",
	       -VLINK   => "#551A8B",
	       -ALINK   => "#FF0000",
	       ),
   "\n\n";

print h3("SUMMARY OF SEQUENCE NUMBER $seq"),p,"\n";


my $dbh = DBI->connect($dsn, $user, $password,{
    PrintError => 0,
    RaiseError => 1});
my $query;

#From Miriam

#CONNECT: {
#    $SIG{ALRM} = sub { die "timeout" };
#    eval {
#        alarm(5);
#open connection to sql server
#        $dbh = new Sybase::CTlib $USER, $PASSWD, $SERVER;
# use axafocat and clean up
#        $dbh->ct_execute("use axafocat");
#        $dbh->ct_results($restype);

#        alarm(0);
#    };
#}

#if ($@) {
#    if ($@ =~ /timeout/) {
#        $SERVER="sqlocc";
#   Comparing to CDO's program that makes
#   the detailed target pages, this line
#   is extra, so we'll try commenting it
#   out. -MM 8/6/093
##	$dbh->ct_cancel(CS_CANCEL_ALL);
#        goto CONNECT;
#    } else {
#        die;
#    }
#}
#$dbh->ct_cancel(CS_CANCEL_ALL);



#
# get titles and abstracts
#
my ($title, $abstract, $type, $ao);
$query = $dbh->prepare(qq(select title, abstract,
			  type, aoid from
			  target t, prop_info p
			  where t.ocat_propid = 
			  p.ocat_propid and
			  seq_nbr = ?));
$query->execute($seq);
($title, $abstract, $type, $ao) = $query->fetchrow_array;
$query->finish;


#
# two-step process to get the PI and observer (can you believe this mess?)
#
my ($pi, $coicontact, $observer);
$query = $dbh->prepare(qq(select last, coi_contact from target t,
			  prop_info i,axafusers..person_short
			  p where i.piid = p.pers_id and
			  i.ocat_propid = t.ocat_propid
			  and t.seq_nbr = ?));
$query->execute($seq);
($pi, $coicontact) = $query->fetchrow_array;
$query->finish;

$observer = $pi unless $coicontact =~ /Y/;
if($coicontact =~ /Y/){
    $query = $dbh->prepare(qq(select last from target t,
			      prop_info i,axafusers..person_short
			      p where i.coin_id=p.pers_id and
			      t.ocat_propid=i.ocat_propid and 
			      t.seq_nbr = ? ));
    $query->execute($seq);
    $observer = $query->fetchrow_array;
}


#
# get all obsids for a sequence number
#
my $obsid;
my @obsids = ();
$query = $dbh->prepare(qq(select obsid from target where seq_nbr= ?));
$query->execute($seq);
while ($obsid = $query->fetchrow_array){
    push @obsids, $obsid;
}
$query->finish;


# select items which may differ by obsid, by obsid
my (%Vary,@lts,@st, @obsprint);
foreach $obsid (@obsids){
    $query = $dbh->prepare(qq(select targname, ra, dec,
			      si_mode,approved_exposure_time,
			      soe_st_sched_date,lts_lt_plan,
			      instrument,grating,status,lts_lt_plan,
			      soe_st_sched_date
			      from target where obsid = ?));
    $query->execute($obsid);
    my (%Info, @stuff);
    my ($lts, $st);
    push @obsprint, "($obsid)";
    while (@stuff = $query->fetchrow_array) {
	    $stuff[3] = '(none)' unless $stuff[3] =~ /\w+/;

	    $Info{target} = $stuff[0],
	    $Info{ra}     = sprintf "%9.4f",$stuff[1],
	    $Info{dec}    = sprintf "%9.4f",$stuff[2],
	    $Info{simode} = $stuff[3],
	    $Info{time}   = sprintf "%5.1f ks",$stuff[4],
	    $Info{st}     = $stuff[5],
	    $Info{lts}    = $stuff[6],
	    $Info{si}     = $stuff[7],
	    $Info{grat}   = $stuff[8],
	    $Info{status} = $stuff[9],

	    $lts = $stuff[10];
	    $lts =~ s/([A-Za-z]{3}) \s+ ([0-9]{1,2}) \s+ ([0-9]{1,4}).*/$3\-$1\-$2/x; 
	    $lts = "Week of: " . $lts unless $lts =~ /^$/;
	    $st  = $stuff[11];
	    push @lts, "($lts)";
	    push @st, "($st)";
    }
    $query->finish;
    $Vary{$obsid} = { %Info };
}


#
# Deal with constraints/preferences
#
my ($window_flag, $roll_flag, $phase);
my ($preid, $multi, $uninterrupt);
foreach $obsid (@obsids){

    $query = $dbh->prepare(qq(select window_flag, roll_flag,
			      phase_constraint_flag, pre_id,
			      multitelescope, uninterrupt
			      from target t, prop_info p 
			      where t.ocat_propid = p.ocat_propid
			      and obsid = ?));
    $query->execute($obsid);
    ($window_flag,
     $roll_flag,
     $phase,
     $preid,
     $multi,
     $uninterrupt) = $query->fetchrow_array;
    $query->finish;

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# This section updated by J. Hagler 2/19/03 to accommodate changes to
# axafocat made in March, 2003.
# 
# Specifically, time/window and roll constraints are stored in 
# separate tables ('timreq' and 'rollreq') to allow for multiple
# constraints/preferences.
# 
# Note that a single obsid may have constraints *and* preferences for
# time/window and/or roll, for example, 
#
# +----------+-----+----+----------+-------------------+-------------------+
# |          |     |    | window_  |                   |                   |
# |timereq_id|obsid|ordr|constraint|tstart             |tstop              |
# +----------+-----+----+----------+-------------------+-------------------+
# |603       |4418 |1   |Y         |Jan  4 2003 12:00AM|Mar  4 2003 12:23PM|
# |604       |4418 |2   |Y         |Apr  1 2003 12:00AM|Sep  1 2003 12:00AM|
# |605       |4418 |3   |P         |Jul  3 2003 12:00AM|Nov  3 2003 12:00AM|
# |606       |4418 |4   |P         |Dec  3 2003 12:00AM|Dec  3 2003 12:00AM|
# +----------+-----+----+----------+-------------------+-------------------+

#
# fetch time/window constraints from timereq
#
    my $window_constraint;
    my $time_const = 0;
    my $time_pref = 0;
    $query = $dbh->prepare(qq(select window_constraint
			    from timereq where obsid = ?));
    $query->execute($obsid);
    $window_constraint = $query->fetchrow_array;
    if ($window_constraint =~ /Y/){
	$time_const = 1;
    }
    if ($window_constraint =~ /P/){
	$time_pref = 1;
    }
    $query->finish;

#  
# fetch roll constraints from rollreq
#
    my $roll_constraint;
    my $roll_const = 0;
    my $roll_pref = 0;
    $query = $dbh->prepare(qq(select roll_constraint
			     from rollreq where obsid = ?));
    $query->execute($obsid);
    $roll_constraint = $query->fetchrow_array;
    if ($roll_constraint =~ /Y/){
	$roll_const = 1;
    }
    if ($roll_constraint =~ /P/){
	$roll_pref = 1;
    }
    $query->finish;

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This section added by Stephanie LaMassa
# Page currently does not denote whether observation
# has monitoring and grouping constraints
# or whether constraints are specified in remarks

#
# check for constraints in remarks
#
    my $constr_in_remarks;
    my $const_rem  = 0;
    my $const_pref = 0;
    $query = $dbh->prepare(qq(select constr_in_remarks
			      from target where obsid = ? ));
    $query->execute($obsid);
    $constr_in_remarks  = $query->fetchrow_array;
    if ($constr_in_remarks =~ /Y/){
	$const_rem = 1;
    }
    if ($constr_in_remarks =~ /P/){
	$const_pref = 1;
    }
    $query->finish;

#
#  Added: 1/06/04
# Sometimes, contraints in remarks marked yes when
# remarks field is empty: check for this possibility
# and replace 1 with 0 in $const_rem or $const_pref
#
    my $remarks;
    my $rem = 0;
    $query = $dbh->prepare(qq(select remarks from
			      target where obsid = ? ));
    $query->execute($obsid);
    $remarks  = $query->fetchrow_array;
    if ( $remarks !~ /^$/ ) {
	$rem = 1;
    }
    if ( (($const_rem == 1) || ($const_pref == 1))
	           &&
	 ($rem == 0) ) {
	$const_rem  = 0;
	$const_pref = 0;
    }

#
# check for group observations
#
    my $group_id;
    my $group = 0;
    $query = $dbh->prepare(qq(select group_id from
			      target where obsid = ?));
    $query->execute($obsid);
    $group_id = $query->fetchrow_array;
    $group = 1 if $group_id;
    $query->finish;

#  
# check for monitoring observations
#
    my $first_monitor;
    my $monitor = 0;
    # finds monitor observation as long as target is not
    # first observation in a monitoring series
    if ($preid =~ /\w+/ && $group == 0){
	$monitor = 1;
    }else {
	# checks if target is first observation in monitoring series
	# by checking if its obsid is a pre-id for another obsid
	$query = $dbh->prepare(qq(select distinct pre_id 
				  from target where
				  pre_id = ?));
	$query->execute($obsid);
	$first_monitor = $query->fetchrow_array;
	$query->finish;
	if ($first_monitor && $group == 0){
	    $monitor = 1;
	}
    }
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  
#
# keep $roll_flag and $window_flag for backward compatibility
#
    my @constr;
    push @constr, " ROLL"    if ($roll_flag =~ /Y/ or $roll_const eq 1);
    push @constr, " PHASE"   if $phase =~ /Y/;
    push @constr, " WINDOW"  if ($window_flag =~ /Y/ or $time_const eq 1);
    push @constr, " MULTI"   if $multi =~ /Y/;
    push @constr, " MONITOR" if ($monitor == 1);
    push @constr, " GROUP"   if ($group == 1); 
    push @constr, " UNINTERRUPT" if $uninterrupt =~ /Y/;
    push @constr, " CONST in REM" if ($const_rem == 1);
    push @constr, "(none)"   if @constr == 0;
    $Vary{$obsid}{constr} = join ',', @constr;
  
    my @prefs;
    push @prefs, "ROLL"    if ($roll_flag =~ /P/ or $roll_pref eq 1);
    push @prefs, " WINDOW" if ($window_flag =~ /P/ or $time_pref eq 1);
    push @prefs, " MULTI"  if $multi =~ /P/;
    push @prefs, " UNINTERRUPT" if $uninterrupt =~ /P/;
    push @prefs, " CONST in REM" if ($const_pref == 1);
    push @prefs, "(none)"  if @prefs == 0;
    $Vary{$obsid}{prefs} = join ',', @prefs;


}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


#
# Output HTML
#

print h4("Title: $title\n"),"\n";
print h4("PI: $pi <spacer type=horizontal size=10>Observer: $observer"),"\n";
print h4("Subject Category: $category"),"\n";
print h4("Seq: $seq <spacer type=horizontal size=10> Obsids: @obsprint"),"\n";
print h4("Long-term bin: @lts"),"\n";
print h4("Short-term schedule time: @st"),"\n";
print h4("Cycle: $ao"),"\n";
print h4("ABSTRACT");
print $abstract,p,"\n";

print h4("TARGET SUMMARY"),"\n";


foreach my $obs (@obsids) {
    $Vary{$obs}{anchor_obs}=qq(<a href="http://cxc.harvard.edu/cgi-gen/target_param.cgi?$obs">$obs</a>);
}


print table({-border => 5,
	     -cols   => 11,
	     -cellpadding => 5},
	    Tr({-align=>CENTER,-valign=>CENTER},
	       [
		th(['TARGET NAME','OBSID','RA','DEC','TIME','TYPE','SI',
		    'GRATING','SI-MODE','STATUS','CONSTRAINTS','PREFERENCES',]),

		# thanks to Pete R. for this little hack

		map(td([
			$Vary{$_}{target},
			$Vary{$_}{anchor_obs},
			$Vary{$_}{ra},
			$Vary{$_}{dec},
			$Vary{$_}{time},
			$type,
			$Vary{$_}{si},
			$Vary{$_}{grat},
			$Vary{$_}{simode},
			$Vary{$_}{status},
			$Vary{$_}{constr},
			$Vary{$_}{prefs},
			]),
		    @obsids),
		]
	       )
	    );
print "\n\n";

print p,h4('IMAGES'),"\n";;



foreach $obsid (@obsids){
    my $fobsid = sprintf "%05d",$obsid;

    my $dss_lts  = "$seq/$seq.mpvis.dss.gif";
    my $pspc_lts = "$seq/$seq.mpvis.pspc.gif";
    my $rass_lts = "$seq/$seq.mpvis.rass.gif";

    my $dss_olts  = "$seq/$seq.$fobsid.dss.gif";
    my $pspc_olts = "$seq/$seq.$fobsid.pspc.gif";
    my $rass_olts = "$seq/$seq.$fobsid.rass.gif";

    $dss_lts  = $dss_olts  if -e "$MPDIR/$dss_olts";
    $pspc_lts = $pspc_olts if -e "$MPDIR/$pspc_olts";
    $rass_lts = $rass_olts if -e "$MPDIR/$rass_olts";
    
    my $dss_soe  = "$seq/$seq.mpvis.soe.dss.gif";
    my $pspc_soe = "$seq/$seq.mpvis.soe.pspc.gif";
    my $rass_soe = "$seq/$seq.mpvis.soe.rass.gif";

    my $dss_osoe  = "$seq/$seq.$fobsid.soe.dss.gif";
    my $pspc_osoe = "$seq/$seq.$fobsid.soe.pspc.gif";
    my $rass_osoe = "$seq/$seq.$fobsid.soe.rass.gif";

    $dss_soe  = $dss_osoe  if -e "$MPDIR/$dss_osoe";
    $pspc_soe = $pspc_osoe if -e "$MPDIR/$pspc_osoe";
    $rass_soe = $rass_osoe if -e "$MPDIR/$rass_osoe";

    my $dss  = $dss_lts;
    my $pspc = $pspc_lts;
    my $rass = $rass_lts;

    #
    # to display SOE gif rather than LTS gif, SOE gif must
    # exist, and be more recent than the LTS gif
    #
    # this works because LTS gifs not yet in the ST schedule get touched
    # but LTS gifs for targets not in the LTS (ie scheduled, observed, or in 
    # weeks currently being scheduled)
    #
    $dss  = $dss_soe  if( -e "$MPDIR/$dss_soe"  &&
			 ( (stat "$MPDIR/$dss_soe")[9] > (stat "$MPDIR/$dss")[9] ) );
    $pspc = $pspc_soe if( -e "$MPDIR/$pspc_soe" &&
			 ( (stat "$MPDIR/$pspc_soe")[9] > (stat "$MPDIR/$pspc")[9] ) );
    $rass = $rass_soe if( -e "$MPDIR/$rass_soe" &&
			 ( (stat "$MPDIR/$rass_soe")[9] > (stat "$MPDIR/$rass")[9] ) );
    
    my $dss_url  = "$MPURL/$dss";
    my $pspc_url = "$MPURL/$pspc";
    my $rass_url = "$MPURL/$rass";

    
    if(   -e "$MPDIR/$dss" 
       || -e "$MPDIR/$pspc"
       || -e "$MPDIR/$rass"
       ){
	my $modstring = '';
	if( $dss =~ /mpvis/ ){
	    $modstring = '-- old FOV';
	} else {
	    $modstring = '-- Approx FOV for nom. roll of LTS bin' unless $dss =~ /soe/;
	    $modstring = '-- ST scheduled FOV' if $dss =~ /soe/;
	    my $epoch = (stat("$MPDIR/$dss"))[9];
	    my $date  = gmtime $epoch;
	    $modstring .= "  (updated $date)";
	}

	print h4("obsid $obsid: ");

	print qq(<a href="http://cxc.harvard.edu/$dss_url"><img align=middle src="http://cxc.harvard.edu/targets/webgifs/dss.gif"></a>);
	print "\n\n";
	
	print qq(<a href="http://cxc.harvard.edu/$pspc_url"><img align=middle src="http://cxc.harvard.edu/targets/webgifs/ros.gif"></a>);
	print "\n\n";
	
	if( -e "$MPDIR/$rass" ){
	    print qq(<a href="http://cxc.harvard.edu/$rass_url"><img align=middle src="http://cxc.harvard.edu/targets/webgifs/rass.gif"></a>);
	}
	
	print qq(<b> <spacer type=horizontal size=5> $modstring </b>),"\n\n";

	print p,"\n";
    } else {
	print qq/ (not available) <p>/;
    }
}


if ( 
     -e "$MPDIR/$seq/$seq.rollvis.bw.gif"
    and
     -e "$MPDIR/$seq/$seq.rollvis.gif"
   ) 
{
    print qq(<B><FONT SIZE="+2"><a href="http://cxc.harvard.edu/targets/$seq/$seq.rollvis.gif">Roll/Pitch/Visibility</a> </FONT></B>);
    print qq(&nbsp;<a href="http://cxc.harvard.edu/targets/$seq/$seq.rollvis.bw.gif">(printable version)</a> );
    print "\n\n";
    print p,"\n";
}
elsif ( -e "$MPDIR/$seq/$seq.rollvis.gif" )
{
    print qq(<B><FONT SIZE="+2"><a href="http://cxc.harvard.edu/targets/$seq/$seq.rollvis.gif">Roll/Visibility</a> </FONT></B>);
    print "\n\n";
    print p,"\n";
} else {
    print qq(<B><FONT SIZE="+2"> Roll/Visibility </FONT></B><p>);
}

print p,h4('PARAMETERS');
foreach $obsid (@obsids){
    print qq(<a href="http://asc.harvard.edu/cgi-gen/target_param.cgi?$obsid">Obscat parameters</a> for obsid $obsid<p>);
}
print "</body> </html>\n";

print p,p;

ENDOFHTML;
$dbh->disconnect;
exit;

