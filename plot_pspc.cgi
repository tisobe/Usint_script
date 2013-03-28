#!/soft/ascds/DS.release/ots/bin/perl

#########################################################################################################
#													#
#	plot_pspc.cgi: 	a perl cgi program to plot a viewing direction on an existing ROSAT iamge	#
#													#
#		this script must be in a directory with following codes/links				#
#			target_offset: c program which computes a postion based on given roation	#
#				       and offsets							#
#			MP: symbolic link to /data/mpcrit1/perl/lib/site_perl/5.6.0/sun4-solaris/MP	#
#					MP directory contains MP specific packages			#
#			Astro: symbolic link to /data/mpcrit1/perl/lib/site_perl/5.6.0/Astro		#
#													#
#		this script also needs an output directory:/home/mta/www/CUS/Usint/Temp_pspc_dir	#
#		in which the script deposit a rosat gif file.						#
#													#
#	author: T. Isobe (tisobe@cfa.harvard.edu)							#
#	Last Update: Feb 28. 2011									#
#													#
#########################################################################################################


use CGI qw/:standard :netscape /;

use DBI;
use DBD::Sybase;

use Carp;
use File::Copy;

use FileHandle;
use Getopt::Long;

use PDL;
use PDL::Graphics::PGPLOT;
use PGPLOT;
use CFITSIO;
use WCSTools::LibWCS;

use LWP::UserAgent;
use HTTP::Request::Common qw(GET);

use Astro::Time;

#
#----- MP-Perl 1.0
#
use MP::Datavis;
use MP::MPCAT;
use MP::Signoff;
use MP::LTS;
use MP::FOV;
use MP::SkyView;
use MP::Visibility;

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

#
#---- set values
#

my $ARCSEC_MM   =  20.4;     # plate scale
my $BORESIGHT_Y =  0.019333; # crude Y offset for boresight correction
my $BORESIGHT_Z = -0.015667; # crude Z offset for boresight correction
my $NACISROWS=1024;
my $ACISWEBPATH="http://acis.mit.edu/cgi-bin/get-atbls?tag=";
my @ACISPB=("fepCcdSelect","subarrayStartRow","subarrayRowCount");


my %Month = ('JAN' =>  1, 'FEB' => 2, 'MAR' => 3, 'APR' => 4,
             'MAY' =>  5, 'JUN' => 6, 'JUL' => 7, 'AUG' => 8,
             'SEP' =>  9, 'OCT' =>10, 'NOV' =>11, 'DEC' => 12);

my %Opt = ('update'   => 0,
           'truncate' => 0,
           'notmygifs' => 0);

GetOptions(\%Opt,
           "update|u",
           "truncate|hack=i","notmygifs|n",
           "help|h",\&PrintHelp,
           );

my @acisi = ([1,  23.5, -26.5],
             [1, -26.5, -26.5],
             [1, -26.5,  23.5],
             [1,  23.5,  23.5],
             [1,  23.5, -26.5],
             [0,  -1.5, -26.5],
             [1,  -1.5,  23.5],
             [0,  23.5,  -1.5],
             [1, -26.5,  -1.5], # end I chips
             [0, -81.0,  55.9],
             [1,  69.0,  55.9],
             [1,  69.0,  30.9],
             [1, -81.0,  30.9],
             [1, -81.0,  55.9],
             [0,  44.0,  30.9],
             [1,  44.0,  55.9],
             [0,  19.0,  55.9],
             [1,  19.0,  30.9],
             [0,  -6.0,  30.9],
             [1,  -6.0,  55.9],
             [1, -31.0,  55.9],
             [1, -31.0,  30.9],
             [1, -56.0,  30.9],
             [1, -56.0,  55.9],);

my @aciss = ([1, -81.0,  12.5],
             [1,  69.0,  12.5],
             [1,  69.0 ,-12.5],
             [1, -81.0, -12.5],
             [1, -81.0,  12.5],
             [0,  44.0, -12.5],
             [1,  44.0,  12.5],
             [0,  19.0,  12.5],
             [1,  19.0, -12.5],
             [0,  -6.0, -12.5],
             [1,  -6.0,  12.5],
             [0, -31.0,  12.5],
             [1, -31.0, -12.5],
             [0, -56.0, -12.5],
             [1, -56.0,  12.5], # end S chips
             [0,  23.5, -69.9],
             [1, -26.5, -69.9],
             [1, -26.5, -19.9],
             [1,  23.5, -19.9],
             [1,  23.5, -69.9],
             [0,  -1.5, -69.9],
             [1,  -1.5, -19.9],
             [0,  23.5, -44.9],
             [1, -26.5, -44.9],);

my @hrci = ([1,   0.0, -62.4],
            [1, -62.4,  -0.0],
            [1,   0.0,  62.4],
            [1,  62.4,  -0.0],
            [1,   0.0, -62.4],);

my @hrcs = ([1,  154.0, -10.00],
            [1,  154.0,  10.00],
            [1, -146.0,  10.00],
            [1, -146.0, -10.00],
            [1,  154.0, -10.00],
            [0,   36.7, 10.00],
            [1,   36.7,  5.35],
            [1,  154.0,  5.35],
            [0, -146.0,  5.35],
            [1,  -28.7,  5.35],
            [1,  -28.7, 10.00],
            [0, -146.0,   -4.00],
            [1,  -15.7,   -4.00],
            [1,  -15.7, 10.00],
            [0,  154.0,   -4.00],
            [1,   15.7,   -4.00],
            [1,   15.7, 10.00],);

my @aca = ([1,  123.5, -123.5],
           [1, -123.5, -123.5],
           [1, -123.5,  123.5],
           [1,  123.5,  123.5],
           [1,  123.5, -123.5],);

my @ichiplabs = ([0, -11.5, -11.5],
                 [1,  11.5, -11.5],
                 [2, -11.5,  11.5],
                 [3,  11.5,  11.5],
                 [4, -67.0,  43.4], # start S chips
                 [5, -42.0,  43.4],
                 [6, -17.0,  43.4],
                 [7,   9.0,  43.4],
                 [8,  33.0,  43.4],
                 [9,  58.0,  43.4],);

my @schiplabs = ([4, -67.0,   0.0],
                 [5, -42.0,   0.0],
                 [6, -17.0,   0.0],
                 [7,   9.0,   0.0],
                 [8,  33.0,   0.0],
                 [9,  58.0,   0.0],
                 [0, -11.5, -54.9],
                 [1,  11.5, -54.9],
                 [2, -11.5, -31.9],
                 [3,  11.5, -31.9],);

my %SI = ('ACIS-I' => \@acisi,
          'ACIS-S' => \@aciss,
          'HRC-I'  => \@hrci,
          'HRC-S'  => \@hrcs  );

my %ChipLab = ('ACIS-I', => \@ichiplabs,
               'ACIS-S', => \@schiplabs,);


#J Grimes - chip info


my %acis_chipinfo = (
          'ACIS-I' => [[ [-26.5,-26.5], [-1.5,-1.5] ],
                [ [23.5, -1.5], [-1.5, -26.5] ],
                [ [-26.5,-1.5], [-1.5,23.5] ],
                [ [23.5, 23.5], [-1.5,-1.5] ],
                [ [-81,55.9], [-56, 30.9] ],
                [ [-56,55.9], [-31, 30.9] ],
                [ [-31,55.9], [-6, 30.9] ],
                [ [-6,55.9], [19,30.9] ],
                [ [19,55.9], [44,30.9] ],
                [ [44,55.9], [69,30.9]]],
          'ACIS-S' => [[ [-26.5,-69.9], [-1.5,-44.9] ],
                [ [23.5, -44.9], [-1.5, -69.9] ],
                [ [-26.5,-44.9], [-1.5,-19.9] ],
                [ [23.5, -19.9], [-1.5,-44.9] ],
                [ [-81,12.5], [-56, -12.5] ],
                [ [-56,12.5], [-31, -12.5] ],
                [ [-31,12.5], [-6, -12.5] ],
                [ [-6,12.5], [19, -12.5] ],
                [ [19,12.5], [44, -12.5] ],
                [ [44,12.5], [69, -12.5]]],
                );


our %Units = ('dss'  => 'POSS scaled density',
              'pspc' => 'PSPC cts/s/pixel',
              'rass' => 'RASS counts');

our %StarSize = ('acq' => 20,
                 'gui' => 10,
                 'mon' => 30,);

our %StarColor = ('acq' => 12,
                  'gui' => 8,
                  'mon' => 6,);

our %StarType = ('acq' => 'Acq Star',
                 'gui' => 'Guide Star',
                 'mon' => 'Mon Star'   );

our %DefColor = ('dss'  => 4,
                 'pspc' => 4,
                 'rass' => 4,);

our %Histogram = ('pspc' => 1);

#J Grimes
my $ChipOnColor=13;
my $SubarrayColor=8;
my $TargPtrColor=2;

#my $NEWPOOL = '/data/mp1/CYCLE5-POOL.lst';
my $NEWPOOL = './CYCLE5-POOL.lst';

our $MPDIR   = '/data/mp1/SEQNBR';
$TI_CDODIR = '/data/mta4/www/CUS/Usint/PSPC_page/Temp_pspc_dir';
@SURVEYS = qw(dss pspc rass);

$obsid = $ARGV[0];

@obsidarray = ();

if($obsid =~ /\d/){
#
#--- open sybase
#

      read_database();

#
#--- sub to read a long term schedule roll value
#
	find_planned_roll();
	$roll = ${planned_roll.$obsid}{planned_roll}[0];
	$in_roll = $roll;
	if($roll eq ''){
		$in_roll = $roll_obsr;
		$roll    = $roll_obsr;
	}
	push(@obsidarray,$obsid);
}


###################################################################

#
#----- html page starts here
#

print header(-cookie=>[$user_cookie, $pass_cookie], -type => 'text/html');

print start_html(-bgcolor=>"white");            # this says that we are starting w html page

$check = '';

print start_form();

if($obsid !~ /\d/){
	$obsid      = param("OBSID");
}
if($obsid  =~ /\d/){
	read_database();
	find_planned_roll();
	$roll = ${planned_roll.$obsid}{planned_roll}[0];
	$in_roll = $roll;
	if($roll eq ''){
		$in_roll = $roll_obsr;
		$roll    = $roll_obsr;
	}
}
$test = param("RA");
if($test ne '' || $test eq '00:00:00:00'){
	$tin_ra     = $test;
	$tin_dec    = param("DEC");
	$in_roll    = param("ROLL");
	$in_yoffset = param("YOFFSET");
	$in_zoffset = param("ZOFFSET");
	$check      = param("Check");
}
@ra_ent = split(/:/,$tin_ra);
$in_ra = hms2deg($ra_ent[0], $ra_ent[1], $ra_ent[2]);
@dec_ent = split(/:/, $tin_dec);
$in_dec = dms2deg($dec_ent[0], $dec_ent[1], $dec_end[2]);

#
#--- when a user gets into the page, s/he sees this part.
#
if($obsid !~ /\d/){
        ($hh,$mm,$ss) = deg2hms($ra);
        $disp_ra  = "$hh:$mm:$ss";
        ($dd,$mm,$ss) = deg2dms($dec);
        $disp_dec = "$dd:$mm:$ss";

        print "<h2>Viewing Orientation Visualizer on a ROSAT Image</h2>";
        print '<h3>Please type in OBSID  and press "Submit." The computation may take several seconds.</h3>';

        print '<table boder=0 cellpadding=5>';
        print '<tr>';
        print '<th>OBSID:</th><td><INPUT TYPE="text" NAME="OBSID" VALUE="',"$obsid",'" SIZE="12"></td>';
        print '</tr><tr>';
        print '<td><INPUT TYPE="submit" NAME="Check"  VALUE="Submit"></td>';
        print '</table>';

	$in_ra      = $ra;
	$in_dec     = $dec;
        $in_roll    = $roll;
        $in_yoffset = $y_det_offset;
        $in_zoffset = $z_det_offset;

}elsif($check ne 'Submit'){
	($hh,$mm,$ss) = deg2hms($ra);
	$disp_ra  = "$hh:$mm:$ss";
	($dd,$mm,$ss) = deg2dms($dec);
	$disp_dec = "$dd:$mm:$ss";

	print "<h2>Viewing Orientation Visualizer on a ROSAT Image</h2>";
	print "<h3>OBSID: $obsid Seq #: $seq_nbr</h3>";
	print '<h3>Please type in new values and press "Submit." The computation may take several seconds.</h3>';
	print '<td><INPUT TYPE="hidden" NAME="OBSID" VALUE="',"$obsid",'"></td>';

	print '<table boder=0 cellpadding=5>';
	print '<tr>';
	print '<th></th>';
	print '<th>RA<br>(HMS)</th>';
	print '<th>Dec<br>(DMS)</th>';
	print '<th>Roll<br>(deg)</th>';
	print '<th>Y Offset<br>(arcmin)</th>';
	print '<th>Z Offset<br>(arcmin)</th>';
	print '</tr>';

	print '<tr>';
	print '<th>Current Values</th>';
	print "<td>$disp_ra</td>";
	print "<td>$disp_dec</td>";
	print "<td>$roll</td>";
	print "<td>$y_det_offset</td>";
	print "<td>$z_det_offset</td>";
	print "<td></td>";
	print '</tr>';

	print '<tr>';
	print '<th>New Values</th>';
	print '<td><INPUT TYPE="text" NAME="RA" VALUE="',"$disp_ra",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="text" NAME="DEC" VALUE="',"$disp_dec",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="text" NAME="ROLL" VALUE="',"$roll",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="text" NAME="YOFFSET" VALUE="',"$y_det_offset",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="text" NAME="ZOFFSET" VALUE="',"$z_det_offset",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="submit" NAME="Check"  VALUE="Submit"></td>';
	print '</tr>';
	print '</table>';

	print "<br>";
	print '<h4>Note: The roll value is from a current MP table, and it could be different from that in the database.</h4>';
	print '<br><br>';
	
	@ra_ent = split(/:/,$disp_ra);
	$in_ra = hms2deg($ra_ent[0], $ra_ent[1], $ra_ent[2]);
	@dec_ent = split(/:/, $disp_dec);
	$in_dec = dms2deg($dec_ent[0], $dec_ent[1], $dec_end[2]);

	$in_roll    = $roll;
	$in_yoffset = $y_det_offset;
	$in_zoffset = $z_det_offset;

	@rollarray = ();
	@obsidarray = ();
	push(@rollarray, $in_roll);
	push(@obsidarray,$obsid);
#
#----- here is the sub script to plot the rosat plot
#
	push(@rollarray, $in_roll);
	mta_ltsoverlay(\@obsidarray,\@rollarray);

	$out_http = 'https://icxc.harvard.edu/mta/CUS/Usint/PSPC_page/Temp_pspc_dir/'."$seq_nbr".'/'."$seq_nbr".'.'."$obsid".'.pspc.gif';
	print '<img src="',"$out_http",'">';

}else{
#
#---- now the script plot the user modified viewing plot
#
#
#---- first remove old plots
#
	system("rm -rf $cus_dir/PSPC_page/Temp_pspc_dir/*");
	($hh,$mm,$ss) = deg2hms($ra);
	$disp_ra  = "$hh:$mm:$ss";
	($dd,$mm,$ss) = deg2dms($dec);
	$disp_dec = "$dd:$mm:$ss";


	print "<h2>Viewing Orientation Visualizer on a ROSAT Image</h2>";
	print "<h3>OBSID: $obsid Seq #: $seq_nbr</h3>";
	print '<h3>Please type in new values and press "Submit." The computation may take several seconds.</h3>';

	print '<td><INPUT TYPE="hidden" NAME="OBSID" VALUE="',"$obsid",'"></td>';

	print '<table boder=0 cellpadding=5>';
	print '<tr>';
	print '<th></th>';
	print '<th>RA<br>(HMS)</th>';
	print '<th>Dec<br>(DMS)</th>';
	print '<th>Roll<br>(deg)</th>';
	print '<th>Y Offset<br>(arcmin)</th>';
	print '<th>Z Offset<br>(arcmin)</th>';
	print '</tr>';

	print '<tr>';
	print '<th>Current Values</th>';
	print "<td>$disp_ra</td>";
	print "<td>$disp_dec</td>";
	print "<td>$roll</td>";
	print "<td>$y_det_offset</td>";
	print "<td>$z_det_offset</td>";
	print "<td></td>";
	print '</tr>';

	if($tin_ra eq '' ){$tin_ra = $disp_ra}
	if($tin_dec eq ''){$tin_dec = $disp_dec}
	if($in_roll eq ''){$in_roll = $roll}
	if($in_yoffset eq ''){$in_yoffset = $y_det_offset}
	if($in_zoffset eq ''){$in_zoffset = $z_det_offset}

	print '<tr>';
	print '<th>New Values</th>';
	print '<td><INPUT TYPE="text" NAME="RA" VALUE="',"$tin_ra",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="text" NAME="DEC" VALUE="',"$tin_dec",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="text" NAME="ROLL" VALUE="',"$in_roll",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="text" NAME="YOFFSET" VALUE="',"$in_yoffset",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="text" NAME="ZOFFSET" VALUE="',"$in_zoffset",'" SIZE="12"></td>';
	print '<td><INPUT TYPE="submit" NAME="Check"  VALUE="Submit"></td>';
	print '</tr>';
	print '</table>';

	print "<br>";
	print '<h4>Note: The roll value is from a current MP table, and it could be different from that in the database.</h4>';
	print '<br><br>';
	
	@ra_ent = split(/:/,$tin_ra);
	$in_ra = hms2deg($ra_ent[0], $ra_ent[1], $ra_ent[2]);
	@dec_ent = split(/:/, $tin_dec);
	$in_dec = dms2deg($dec_ent[0], $dec_ent[1], $dec_end[2]);

#
#----- ploting routine
#
	@rollarray = ();
	@obsidarray = ();
	push(@rollarray, $in_roll);
	push(@obsidarray,$obsid);
	mta_ltsoverlay(\@obsidarray,\@rollarray);

	$out_http = 'https://icxc.harvard.edu/mta/CUS/Usint/PSPC_page/Temp_pspc_dir/'."$seq_nbr".'/'."$seq_nbr".'.'."$obsid".'.pspc.gif';
	print '<img src="',"$out_http",'">';
}

#####################################################################################
### read_databae: reading database                                                ###
#####################################################################################

sub read_database{
#------------------------------------------------
#-------  database username, password, and server
#------------------------------------------------

        $db_user="browser";
        $server="ocatsqlsrv";

#       $db_user="browser";
#       $server="sqlbeta";

        $db_passwd =`cat /proj/web-icxc/cgi-bin/obs_ss/.Pass_dir/.targpass`;
        chop $db_passwd;

#--------------------------------------
#-------- open connection to sql server
#--------------------------------------

        my $db = "server=$server;database=axafocat";
        $dsn1 = "DBI:Sybase:$db";
        $dbh1 = DBI->connect($dsn1, $db_user, $db_passwd, { PrintError => 0, RaiseError => 1
});

        $sqlh1 = $dbh1->prepare(qq(select
                targid, seq_nbr, targname, si_mode,
                ra, dec, y_det_offset, z_det_offset,
                instrument
        from target where obsid=$obsid));
        $sqlh1->execute();
        @targetdata = $sqlh1->fetchrow_array;
        $sqlh1->finish;

        $targetid     = $targetdata[0];
        $seq_nbr      = $targetdata[1];
        $targname     = $targetdata[2];
        $si_mode      = $targetdata[3];
        $ra           = $targetdata[4];
        $dec          = $targetdata[5];
        $y_det_offset = $targetdata[6];
        $z_det_offset = $targetdata[7];
        $instrument   = $targetdata[8];

        if(!$y_det_offset){$y_det_offset = 0};
        if(!$z_det_offset){$z_det_offset = 0};
        $sqlh1 = $dbh1->prepare(qq(select
                trans_offset,focus_offset
        from sim where obsid=$obsid));
        $sqlh1->execute();
        @simdata = $sqlh1->fetchrow_array;
        $sqlh1->finish;

        $trans_offset = $simdata[0];
        $focus_offset = $simdata[1];

        $targetid     =~ s/\s+//g;
        $seq_nbr      =~ s/\s+//g;
        $targname     =~ s/\s+//g;
        $si_mode      =~ s/\s+//g;
        $ra           =~ s/\s+//g;
        $dec          =~ s/\s+//g;
        $y_det_offset =~ s/\s+//g;
        $z_det_offset =~ s/\s+//g;
        $trans_offset =~ s/\s+//g;
        $focus_offset =~ s/\s+//g;


        $sqlh1 = $dbh1->prepare(qq(select soe_roll from soe where obsid=$obsid));
        $sqlh1->execute();
        @soedata = $sqlh1->fetchrow_array;
        $sqlh1->finish;

        $roll_obsr = $soedata[0];

}

#########################################################################
### offset: a lap script to use c code target_offset                  ###
#########################################################################


sub offset{
        ($ora,$odec,$oroll,$oyoff, $ozoff) = @_;

        $YFLIP = 1.0;
        $ZFLIP = -1.0;
        $TARG_OFFSET = "$cus_dir/PSPC_page/target_offset";

        $off_coords = `$TARG_OFFSET  $ora $odec $oroll $oyoff $ozoff $YFLIP $ZFLIP`;
       chop($off_coords);
        ($off_ra,$off_dec) = split(/\s+/,$off_coords);
        return $off_ra,$off_dec;
}




########################################################
### mta_ltsoverlay: mta version ltsoverlay          ####
########################################################

 sub mta_ltsoverlay {

#
#--- this script is a copy pf mp ltsoverlay
#--- there are several modifications, esp. variable names,
#--- and we also removed many things that mta does not need.
#

    my %Obsids;

     $Obsids{$obsid}{RA}  = sprintf "%9.5f", $in_ra;
     $Obsids{$obsid}{dec} = sprintf "%9.5f", $in_dec;

     my $yoff = 0.0;
     my $zoff = 0.0;
     my $zsim = 0.0;
     my $roll = $in_roll;
     $yoff = $in_yoffset if $in_yoffset;
     $zoff = $in_zoffset if $in_zoffset;
     $zsim = $trans_offset if $trans_offset;

     $Obsids{$obsid}{yoff} = sprintf "%5.2f'", $yoff;
     $Obsids{$obsid}{zoff} = sprintf "%5.2f'", $zoff;
     $Obsids{$obsid}{zsim} = sprintf "%7.3f",  $zsim;
     $Obsids{$obsid}{SeqNbr} = $seq_nbr;
     $Obsids{$obsid}{SI}     = $instrument;
     $Obsids{$obsid}{name}   = $targname if $targname;

     my $seq= $seq_nbr;

     if( abs($yoff) > 0 || abs($zoff) > 0 ){
         # J Grimes added negative to zoff
         ($in_ra,$in_dec) = offset($in_ra,$in_dec,$roll,$yoff/60.0,-1*$zoff/60.0);
     }


     if ($instrument =~m/ACIS/ && $si_mode) {
         $Obsids{$obsid}{SIMode}=$si_mode;
    }


    # create overlays
    # get FITS images from SkyView that had troubles,
    # and try again (this code lifted from weekly.pl)


    my $badfits = mta_make_fov(\%Obsids,"lts");


    my $numbad  = @$badfits;
}


################################################################
### mta_make_fov: mta version of mp make_fov                 ###
################################################################

sub mta_make_fov {

#
#---- this is basically same as that of mp version
#---- there are a few variable name changes
#

$ACISWEBPATH="http://acis.mit.edu/cgi-bin/get-atbls?tag=";

#J Grimes-set PGPLOT env values
    $ENV{PGPLOT_FONT}="/data/mpcrit1/pgplot/grfont.dat";
    $ENV{PGPLOT_RGB}="/data/mpcrit1/pgplot/rgb.txt";


    my($Obsids,$datavisType) = @_;

    umask 0002;

    local $| = 1 if $verbose;


    croak "datavis file type $datavisType not recognized...dying\n" unless
        $datavisType =~ /soe|SOE|lts|LTS/;

    my $type; # my $type == "sylvia"
    $type = 'soe.' if $datavisType =~ /soe|SOE/;
    $type = ''     if $datavisType =~ /lts|LTS/;

# J Grimes
# Get ACIS PB Data
    my %acis_data;
    my $ua = LWP::UserAgent->new;
    foreach my $key (keys %$Obsids) {
        next if ($Obsids->{$key}->{SI}!~m/ACIS/ || !$Obsids->{$key}->{SIMode}) ;
        if (!exists $acis_data{$Obsids->{$key}{SIMode}}) {
            print "Retrieving ACIS Parameter Block Info for ",$Obsids->{$key}{SIMode},"\n" if $verbose;
            $acis_data{$Obsids->{$key}{SIMode}}{Get}=
                $ua->request(GET $ACISWEBPATH . $Obsids->{$key}{SIMode});
            foreach my $t (@ACISPB) {
                ($acis_data{$Obsids->{$key}{SIMode}}{$t})=
                    $acis_data{$Obsids->{$key}{SIMode}}{Get}->{_content}=~m/$t\s*=\s*(.+)/;
                (defined $acis_data{$Obsids->{$key}{SIMode}}{$t} &&
                 $acis_data{$Obsids->{$key}{SIMode}}{$t} ne "") or
                     $acis_data{$Obsids->{$key}{SIMode}}{$t}=0;
                $acis_data{$Obsids->{$key}{SIMode}}{"fepCcdSelect"}=~s/(10|\s)//g if $acis_data{$Obsids->{$key}{SIMode}}{"fepCcdSelect"}=~m/\s/;
            }
            if ($Obsids->{$key}{SIMode} =~m/^(CC_|WC)/) {
                $acis_data{$Obsids->{$key}{SIMode}}{$ACISPB[1]}=0;
                $acis_data{$Obsids->{$key}{SIMode}}{$ACISPB[2]}=1023;
            }
        }
    }


    my @bad; # return a hash with the obsids of that CFITSIO choked on

    my $obsid;
    OUTER: foreach $obsid (keys %$Obsids){

        # test $TI_CDODIR for disk space -- if it is
        # too low, abort the overlay creation

        my @df = `/usr/ucb/df $TI_CDODIR/.`;
        for my $line (@df) {
            my @line = split " ", $line;
            next unless @line==6 and $line[1] =~ /^\d+$/;
            my $avail   = $line[3];
            my $percent = $line[4];

            if ( $avail < 350 ) {

                # this is about the maximum size (in kb)
                # of a single FOV GIF

                print "\nWARNING!!\n$TI_CDODIR is out of space; ",
                      "no more GIFs will be created\n\n";
                last OUTER;
            }

            last;
        }


        my $Obs = $Obsids->{$obsid};
        my $seq = $Obs->{SeqNbr};
        my $si  = $Obs->{SI};
	@ctemp = split(//, $obsid);
	$ccnt = 0;
	foreach(@ctemp){
		$ccnt++;
	}
	if($ccnt < 5){
		$iobsid = '0'."$obsid";
	}else{
		$iobsid = $obsid;
	}
        my $datavis = "$MPDIR/$seq/$seq.$iobsid.$type" . "datavis";
#        my ($Coords,$StarFid) = read_datavis($datavis);
#
#        my $tra  = $Coords->{ra};
#        my $tdec = $Coords->{dec};
#        my $roll = $Coords->{roll};

        my $tra  = $in_ra;
        my $tdec = $in_dec;
        my $roll = $in_roll;
        my $name=undef;
        if (exists $Obs->{name}) {
            $name = $Obs->{name};

            # limit the length of the target name
            if (length($name) > 20) {
                $name = substr($name,0,20) . '...';
            }
        }

        my $or_ra=$Obs->{RA};
        my $or_dec=$Obs->{dec};

        #
        # now loop over DSS, PSPC, and RASS images for each target
        #
        my $survey;
        foreach $survey (@SURVEYS){

            carp "$TI_CDODIR/$seq does not exist...creating!\n" unless -d "$TI_CDODIR/$seq";
            mkdir "$TI_CDODIR/$seq" unless -d "$TI_CDODIR/$seq";
#           carp "$MPDIR/$seq does not exist...creating!\n" unless -d "$MPDIR/$seq";
#           mkdir "$MPDIR/$seq" unless -d "$MPDIR/$seq";

            my $fitsfile = "$MPDIR/$seq/$seq.$survey.fits";

            #
            # This is some CFITSIO stuff to get the size of the images
            # and FITS header info for the WCSLIB routines
            #
            my $status = 0;
            my $bitpix = 0;
            my $naxes;
            my $fptr = CFITSIO::open_file($fitsfile, CFITSIO::READONLY(), $status);
            next if check_status($status,$fitsfile,$obsid,$survey,\@bad); # be a good CFITSIO citizen

            $fptr->get_img_parm($bitpix,undef,$naxes,$status);
            next if check_status($status,$fitsfile,$obsid,$survey,\@bad); # be a good CFITSIO citizen

            my($naxis1, $naxis2) = @$naxes;

            my $hdr;
            $fptr->get_image_wcs_keys($hdr,$status);
            next if check_status($status,$fitsfile,$obsid,$survey,\@bad); # be a good CFITSIO citizen

            $fptr->close_file($status);
            next if check_status($status,$fitsfile,$obsid,$survey,\@bad); # be a good CFITSIO citizen

            #
            # now, initialize the WCS object and get target pixels
            #
            my $wcs = WCSTools::LibWCS::wcsinit($hdr);  # WCS object. ick.
            my ($xt,$yt);
            my $offscale = 0;  # not sure what this does
            $wcs->wcs2pix($tra,$tdec,$xt,$yt,$offscale);

            #
            # On the count of three....DRAW!
            #
            my $gif    = "$seq.$obsid." . $type . "$survey.gif";
            my $mpgif  = "$MPDIR/$seq/$gif";
            my $cdogif = "$TI_CDODIR/$seq/$gif";

            print "Creating FOV overlay $gif..." if $verbose;

            my $pgplot = PDL::Graphics::PGPLOT::Window->new({
                Device => "$cdogif/gif",
#               Device => "./$gif/gif",
                Axis   => 'Empty',
                HardLW => 1,
                HardCH => 1,
                AxisColor => 1,
            });
            pgpap(0,1.0);  # preserve 1:1 aspect ratio
            pgsfs(2);
            $pgplot->env(0,$naxis1-1,0,$naxis2-1);

            my $img = rfits $fitsfile;  # PDL::IO::Misc::rfits
            my ($min,$max) = image_stretch($img,$survey);

            my $bad = 0;
            if( $min == $max && $max == 0.0){
                $max += 0.0001;
                $img->set(1,1,$max);
                $bad = 1;
            }

            $pgplot->imag($img, {Min => $min, Max => $max});

            pgsci($DefColor{$survey});
            pgpt(1,[$xt],[$yt],11);  # put a point at the target position
            #actually this is really at the offset position above?
            #think this is the HRMA pointing position really

            #J Grimes #Actually put a cross at the target position
            $wcs->wcs2pix($or_ra,$or_dec,$xt,$yt,$offscale);

            my $lw;
            pgqlw($lw);
            pgsci($TargPtrColor);
            pgsch(2.5);
            pgslw(2*$lw);
            pgpt(1,[$xt],[$yt],5);
            pgsci($DefColor{$survey});
            pgsch(1.0);
            pgslw($lw);



            my $siarray = [ @{ $SI{$si} } ];
            my $point   =  shift @$siarray;

            my $zsim = 0;
            $zsim = $Obs->{zsim} if $Obs->{zsim};
            my $xoff = $point->[1] * $ARCSEC_MM / 3600.0;
            my $yoff = ($point->[2] + $zsim) * $ARCSEC_MM / 3600.0;
            my ($x,$y) = getxy($wcs,$tra,$tdec,$roll,$xoff,$yoff);
            pgmove($x,$y);
            foreach $point (@$siarray){
                $xoff = $point->[1] * $ARCSEC_MM / 3600.0;
                $yoff = ($point->[2] + $zsim) * $ARCSEC_MM / 3600.0;
                ($x,$y) = getxy($wcs,$tra,$tdec,$roll,$xoff,$yoff);
                pgdraw($x,$y) if $point->[0];
                pgmove($x,$y) unless $point->[0];
            }


# J Grimes
            if ($si=~/ACIS/ && $Obsids->{$obsid}{SIMode} &&
                $acis_data{$Obsids->{$obsid}{SIMode}}{"subarrayRowCount"}!=1023) {
                for(my $n=0;$n<length($acis_data{$Obsids->{$obsid}{SIMode}}{"fepCcdSelect"});$n++) {
                    my $chip=substr($acis_data{$Obsids->{$obsid}{SIMode}}{"fepCcdSelect"},$n,1);

                    my $startrow=$acis_data{$Obsids->{$obsid}{SIMode}}{"subarrayStartRow"};
                    my $endrow=$startrow+$acis_data{$Obsids->{$obsid}{SIMode}}{"subarrayRowCount"};


                    my ($xoff,$yoff,$xoff2,$yoff2);
                    if ($chip<4) {
                        $xoff = ($startrow*($acis_chipinfo{$si}[$chip][1][0]-$acis_chipinfo{$si}[$chip][0][0])
                                    /$NACISROWS)+$acis_chipinfo{$si}[$chip][0][0];
                        $yoff = ($acis_chipinfo{$si}[$chip][0][1] + $zsim);
                        $xoff2 = ($endrow*($acis_chipinfo{$si}[$chip][1][0]-$acis_chipinfo{$si}[$chip][0][0])
                                    /$NACISROWS)+$acis_chipinfo{$si}[$chip][0][0];
                        $yoff2 = ($acis_chipinfo{$si}[$chip][1][1] + $zsim);
                    } else {
                        $xoff = $acis_chipinfo{$si}[$chip][0][0];
                        $yoff = ($startrow*($acis_chipinfo{$si}[$chip][1][1]-$acis_chipinfo{$si}[$chip][0][1])
                                 /$NACISROWS + $acis_chipinfo{$si}[$chip][0][1] + $zsim);
                        $xoff2 = $acis_chipinfo{$si}[$chip][1][0];
                        $yoff2 = ($endrow*($acis_chipinfo{$si}[$chip][1][1]-$acis_chipinfo{$si}[$chip][0][1])
                                 /$NACISROWS + $acis_chipinfo{$si}[$chip][0][1] + $zsim);
                    }
                    pgsci($SubarrayColor);
                    my ($x1,$y1) = getxy($wcs,$tra,$tdec,$roll,$xoff*$ARCSEC_MM/3600,$yoff*$ARCSEC_MM/3600);
                    my ($x2,$y2) = getxy($wcs,$tra,$tdec,$roll,$xoff*$ARCSEC_MM/3600,$yoff2*$ARCSEC_MM/3600);
                    my ($x3,$y3) = getxy($wcs,$tra,$tdec,$roll,$xoff2*$ARCSEC_MM/3600,$yoff2*$ARCSEC_MM/3600);
                    my ($x4,$y4) = getxy($wcs,$tra,$tdec,$roll,$xoff2*$ARCSEC_MM/3600,$yoff*$ARCSEC_MM/3600);
#print "($x1,$y1)  ($x2,$y2) ($x3,$y3)  ($x4,$y4)\n";
                    pgmove($x1,$y1);
                    pgdraw($x2,$y2);
                    pgdraw($x3,$y3);
                    pgdraw($x4,$y4);
                    pgdraw($x1,$y1);
                }
            }


            # now chip labels;
            if( $si =~ /ACIS/ ){
                foreach $point (@{ $ChipLab{$si} }){
                    my $chip = $point->[0];

                    # J Grimes
                    if ( $Obsids->{$obsid}{SIMode} && $acis_data{$Obsids->{$obsid}{SIMode}}{"fepCcdSelect"}=~m/$chip/) {
                        pgsci($ChipOnColor);
                        pgsch(1.0);
                    } else {
                        pgsci($DefColor{$survey});
                        pgsch(.7);
                    }

                    $xoff    = $point->[1] * $ARCSEC_MM / 3600.0;
                    $yoff    = ($point->[2] + $zsim) * $ARCSEC_MM / 3600.0;
                    ($x,$y)  = getxy($wcs,$tra,$tdec,$roll,$xoff,$yoff);

                    # J Grimes
                    my $achip= $chip > 3 ? $chip-4 : $chip;
                    pgptxt($x,$y,0,0.5,$achip);
                }
            }
            pgsci($DefColor{$survey});
            pgsch(1.0);


            # for the DSS, plot stars and ACA FOV
            if( $survey eq 'dss' ){
                my @acatmp = @aca;
                ($xoff,$yoff) = @{ shift @acatmp }[1,2];
                $xoff *= $ARCSEC_MM / 3600.0;
                $yoff *= $ARCSEC_MM / 3600.0;  # no zsim offsets for the ACA
                my ($bra,$bdec) = offset($tra,$tdec,$roll,$BORESIGHT_Y,$BORESIGHT_Z);
                ($x,$y) = getxy($wcs,$bra,$bdec,$roll,$xoff,$yoff);
                pgmove($x,$y);

                foreach $point (@acatmp){
                    $xoff = $point->[1] * $ARCSEC_MM / 3600.0;
                    $yoff = $point->[2] * $ARCSEC_MM / 3600.0;
                    ($bra,$bdec) = offset($tra,$tdec,$roll,$BORESIGHT_Y,$BORESIGHT_Z);
                    ($x,$y) = getxy($wcs,$bra,$bdec,$roll,$xoff,$yoff);
                    pgdraw($x,$y);
                }

                # Star and Fid data
                my $star_type;
                foreach $star_type ('acq','gui','mon'){
                    my $id;
                    my $offscale = 0;
                    foreach $id (keys %{$StarFid->{$star_type}}){
                        my $star = $StarFid->{$star_type}{$id};
                        my $ra   = $star->{ra};
                        my $dec  = $star->{dec};
                        $wcs->wcs2pix($ra,$dec,$x,$y,$offscale);
                        pgsci($StarColor{$star_type});
                        pgcirc($x,$y,$StarSize{$star_type}/(1024/$naxis1));
                    }
                }
                my @fidx = ();
                my @fidy = ();
                my $fid;
                foreach $fid (keys %{$StarFid->{'fid'}}){
                    my $ra  = $StarFid->{'fid'}{$fid}{ra};
                    my $dec = $StarFid->{'fid'}{$fid}{dec};
                    $wcs->wcs2pix($ra,$dec,$x,$y,$offscale);
                    push @fidx, $x;
                    push @fidy, $y;
                }
                my $fidnum = @fidx;
                pgsci(2);
                pgsch(0.5);
                pgpt($fidnum,\@fidx,\@fidy,19);
                pgsch(1);
                # label stars and fids
                if( $StarFid ){
                    my $text_y = int($naxis2 / 20);
                    my $text_x = int($naxis1 / 20);
                    my $x_step = $naxis2/4;
                    my $t_off  = 30;
                    foreach $star_type ('gui','acq','mon'){
                        pgsci($StarColor{$star_type});
                        pgcirc($text_x,($text_y + ($StarSize{$star_type}/2)),
                               $StarSize{$star_type}/(1024/$naxis1));
                        pgptxt($text_x + $t_off,$text_y,0,0,$StarType{$star_type});
                        $text_x += $x_step;
                    }
                    pgsci(2);
                    pgsch(0.5);
                    pgpt(1,[$text_x],[$text_y],19);
                    pgsch(1);
                    pgptxt($text_x + $t_off,$text_y,0,0,"Fid Light");
                }
            }

            #
            # Label the RA, dec, and roll using basically the same
            # algorithm as for the stars and fids above
            #
            my $text_y = int( $naxis2 - $naxis2/20 );
            my $text_x = int( $naxis1/20 );
            my $x_step = $naxis2/3;
            $Obs->{RA}   = $tra unless $Obs->{RA};
            $Obs->{dec}  = $tdec unless $Obs->{dec};
            pgsci($DefColor{$survey});
            pgptxt($text_x,$text_y,0,0,"RA = $Obs->{RA}");
            $text_x += $x_step;
            pgptxt($text_x,$text_y,0,0,"DEC = $Obs->{dec}");
            $text_x += $x_step;
            pgptxt($text_x,$text_y,0,0,"ROLL = $roll");

            #
            # Now, label offsets if they're defined;
            #
            $text_x  = int( $naxis1/20 );
            $text_y -= int( $naxis2/20 );
            pgptxt($text_x,$text_y,0,0,"YOFF = $Obs->{yoff}") if $Obs->{yoff};
            $text_x += $x_step;
            pgptxt($text_x,$text_y,0,0,"ZOFF = $Obs->{zoff}") if $Obs->{zoff};
            $text_x += $x_step;
            pgptxt($text_x,$text_y,0,0,"ZSIM = $zsim mm");
            $text_x += $x_step;

            $text_x  = int( $naxis1/20 );
            $text_y -= int( $naxis2/20 );

            pgptxt($text_x,$text_y,0,0,"ACIS PB = $Obs->{SIMode}") if ($datavisType =~ /SOE|soe/ && $Obs->{SIMode});
            pgptxt($text_x,$text_y,0,0,"SI Mode = $Obs->{SIMode}") if ($datavisType =~ /LTS|lts/ && $Obs->{SIMode});

            #
            # if $img contains no useful data ($bad > 0),
            # print a message on the image
            #
            pgptxt(50,20,0,0,
                   "*** The $survey has no data at this pointing ***")
                if $bad;

            #
            # Now, make the nice box with coordinates
            #
            my ($ra1,$dec1,$ra2,$dec2);
            $wcs->pix2wcs(1,1,$ra1,$dec1);
            $wcs->pix2wcs($naxis1,$naxis2,$ra2,$dec2);

            if ( $ra1 < $ra2 ) {
                $ra1 += 360;
            }
            if ( $dec2 < $dec1 ) {
                $dec2 += 180;
            }

            pgsci(11);
            pgsch(.85);
            pgswin($ra1,$ra2,$dec1,$dec2);

            # get nearest minute for beginning RA label
            my ($hh, $mm, $ss) = deg2hms($ra1);
            my $begin_ra = hms2deg($hh,$mm,0);

            # get RA scale so we know how often to label
            # the axis (otherwise labels will overlap at
            # high declinations)
            my $diff = abs( $ra1 - $ra2);
            my $label_int;
            if ( $diff > 10) {
                $label_int = 12;
            } elsif ( $diff >= 7 and $diff < 10) {
                $label_int = 9;
            } elsif ( $diff >= 5 and $diff < 7) {
                $label_int = 6;
            } elsif ( $diff >= 3 and $diff < 5) {
                $label_int = 3;
            } else {
                $label_int = 2;
            }


            # get RAs every minute and draw tickmarks,
            # labelling every $label_int minutes

            pgbox('B',0,0,'',0,0);
            my $radelta = .25;

            my $j = $label_int;
            for ( my $ra = $begin_ra; $ra > $ra2; $ra -= $radelta ) {

                my $frac = abs( ($ra - $ra1) / ($ra2 - $ra1) );
                # this tells PGPLOT where to put the tickmark,
                # in terms of a fraction of the total distance
                # along the axis

                if ( $j == $label_int ) {
                    # label with hms RA every $label_int arcmin.
                    my $ra_tmp = $ra;
                    $ra_tmp -= 360 if $ra_tmp >=360;
                    my ($h,$m,$s) = deg2hms($ra_tmp);
                    my $hms = sprintf "%2.2dh%2.2dm", $h, $m;

                    pgtick($ra1,$dec1,$ra2,$dec1,$frac,0.75,0.0,0.5,0.0,$hms);
                    $j = 0;
                }
                else {
                    # only draw the tickmark
                    pgtick($ra1,$dec1,$ra2,$dec1,$frac,0.25,0.0,0.5,0.0,'');
                }

                $j++;
            }


            # do it again for the top axis, only in degrees
            # (increment by .2 degrees, label every degree,
            # starting with the nearest .2 degree)
            pgbox('C',0,0,'',0,0);

            my $begin_ra2 = sprintf "%.1f", $ra1;
            my $tmp_ra = int($begin_ra2 * 10);
            while ( ($tmp_ra/2) != int($tmp_ra/2) ) {
                $tmp_ra--;
                $tmp_ra = int($tmp_ra);
                if ($tmp_ra < -360) {
                    croak "something went wrong";
                }
            }
            $begin_ra2 = sprintf "%.1f", $tmp_ra/10;

            my $radelta2 = .2;
            for ( my $ra = $begin_ra2; $ra > $ra2; $ra -= $radelta2 ) {

                my $frac = abs( ($ra - $ra1) / ($ra2 - $ra1) );

                $ra = sprintf "%.1f", $ra;
                if ( $ra == int($ra) ) {
                    my $ra_tmp = $ra;
                    $ra_tmp -= 360 if $ra_tmp >=360;
                    $ra_tmp = sprintf "%d", $ra_tmp;
                    pgtick($ra1,$dec2,$ra2,$dec2,
                           $frac,0.0,0.75,-0.5,0.0,$ra_tmp);
                }
                else {
                    pgtick($ra1,$dec2,$ra2,$dec2,
                           $frac,0.0,0.25,-0.5,0.0,'');
                }

            }


            # get nearest 10 arcminutes for beginning Dec label
            my ($dd, $dm, $ds) = deg2dms($dec1);
            $dm = 10 * int($dm/10);
            $dm += 10 if $dec1 < 0;
            if ( $dec1 < 0 and $dec1 > -1 ) {
                $dd = -.000000001;
            }
            my $begin_dec = dms2deg($dd, $dm, 0);

            # get Decs every 10 arcminutes and draw
            # tickmarks, labelling every 20 arcmin.
            pgbox('',0,0,'BC',0,0);

            my $decdelta = (1/6);
            my $k = 0;
            for ( my $dec = $begin_dec; $dec < $dec2; $dec += $decdelta ) {

                my $frac = abs( ($dec - $dec1) / ($dec2 - $dec1) );

                if ( $k == 2 ) {
                    my $dec_tmp = $dec;
                    $dec_tmp -= 180 if $dec_tmp > 90;

                    my ($d,$m,$s) = deg2dms($dec);
                    my $dms;
                    if ($dec < 0 and $dec > -1) {
                        $dms = sprintf "-%2.2d %2.2d'", $d, $m;
                    } else {
                        $dms = sprintf "%2.2d %2.2d'", $d, $m;
                    }

                    pgtick($ra1,$dec1,$ra1,$dec2,
                           $frac,0.0,0.75,-0.5,0.0,$dms);

                    $k = 0;
                }
                else {
                    pgtick($ra1,$dec1,$ra1,$dec2,
                           $frac,0.0,0.25,-0.5,0.0,'');
                }

                $k++;
}


            pgsch(1);



            pgwedg('RG',0.25,3,$min,$img->max,"$Units{$survey}");

            my $sched = '';
            $sched = 'Prelim. Roll' if $datavisType =~ /LTS|lts/;
            $sched = 'ST Scheduled' if $datavisType =~ /soe|SOE/;

            my $title="Seq \# $seq, Obsid $obsid, $sched";
            $title="Name $name, Seq \# $seq, Obsid $obsid, $sched" if defined $name;

            $pgplot->label_axes('RA (J2000)',
                                'Dec (J2000)',
                                $title,
                                {Color => 11});

            pgsci(11);
            pgiden();
            $wcs->free;
            print "done.\n" if $verbose;
        }
    }

#
#  commented out by TI
#
#    # now copy the GIFs over to the MP area (is this still useful?)
#    if ($MPDIR !~ /$TI_CDODIR/) {
#      print "copying gifs to MP area ..." if $verbose;
#      foreach $obsid (keys %$Obsids){
#       my $Obs = $Obsids->{$obsid};
#       my $seq = $Obs->{SeqNbr};
#       my $survey;
#       foreach $survey (@SURVEYS){
#         my $gif = "$seq.$obsid." . $type . "$survey.gif";
#         my $cdogif = "$TI_CDODIR/$seq/$gif";
#         my $mpgif  = "$MPDIR/$seq/$gif";
#         copy $cdogif, $mpgif;
#       }
#      }
#      print "done.\n" if $verbose;
#    } # if ($MPDIR !~ /$TI_CDODIR/) {
#
#    return \@bad;
  }



#################################################################
#################################################################
#################################################################

sub image_stretch {

#################################################################
#
# Return image min and max values, unless $Histogram{$survey}
# is set, in which case do a crude histogram equalization
#
#################################################################

    my ($img,$survey) = @_;

    my $long = $img->copy;
    my $numl = $long->nelem;

    my $hcut;
    if( $Histogram{$survey} ){
        $long = $long->where($long > -1);  # gets rid of those annoying -1's in the PSPC images
        $long = qsort( $long->reshape($numl) );
        my $idx  = int( $numl * 0.999 );
        $hcut = $long->at($idx);
    }

    my $min  = $long->min;
    my $max  = $long->max;

    $max = $hcut if $Histogram{$survey};

    return ($min,$max);
}

#################################################################
#################################################################
#################################################################

sub getxy {
    my ($wcs,$tra,$tdec,$roll,$xoff,$yoff) = @_;

    my ($x,$y,$offscale);

    my ($ra,$dec) = offset($tra,$tdec,$roll,$xoff,$yoff);
    $wcs->wcs2pix($ra,$dec,$x,$y,$offscale);

    return $x,$y;
}

#################################################################
#################################################################
#################################################################

# check CFITSIO status
sub check_status {
    my $s = shift;
    my $f = shift;
    if ($s != 0) {
        my $txt;
      CFITSIO::fits_get_errstatus($s,$txt);
        carp "CFITSIO error ($f): $txt";
        my($obsid,$survey,$bad) = @_;
        push @$bad, [$obsid, $survey];
        return 1;
    }

    return 0;
}

#################################################################
#################################################################
#################################################################

sub deg2hms {

    my $ra = $_[0];

    my $hh = int( $ra/15 );
    my $mm = int( 60 * ($ra/15 - $hh));
    my $ss = 60 * ( 60 * ($ra/15 - $hh) - $mm);

    $ss = 0 if $ss < .00001;
    if ( $ss > 59.999 ) {
        $ss = 0;
        $mm++;
        if ($mm >= 60) {
            $mm -= 60;
            $hh++;
        }
    }

    $ss = sprintf "%4.2f", $ss;
    if($hh < 10){$hh = "0$hh"}
    if($mm < 10){$mm = "0$mm"}
    if($ss < 10){$ss = "0$ss"}

    return ($hh,$mm,$ss);
}

#################################################################
#################################################################
#################################################################

sub deg2dms {

    my $dec = $_[0];

    $dec =~ s/^\+//;
    my $dd = int($dec);
    my $dm = int( 60 * ($dec - $dd) );
    my $ds = 60 * ( 60 * ($dec - $dd) - $dm);

    if ( $dm < 0 ) {
        $dm = -$dm;
    }
    if ( $ds < 0 ) {
        $ds = -$ds;
    }

    $ds = 0 if $ds < .00001;
    if ( $ds > 59.999 ) {
        $ds = 0;
        $dm++;
        if ($dm >= 60) {
            $dm -= 60;
            $dd++;
        }
    }

    $ds = sprintf "%4.2f", $ds;
    $sign = 1;
    if($dd < 0){$sign = -1}
    $dd = abs($dd);
    if($dd < 10){$dd = "0$dd"}
    $dd *= $sign;
    if($mm < 10){$mm = "0$dm"}
    if($ss < 10){$ss = "0$ds"}

    return ($dd,$dm,$ds);

}

#################################################################
#################################################################
#################################################################

sub hms2deg {

    my $hh = $_[0];
    my $mm = $_[1];
    my $ss = $_[2];
    my $ra = 15 * ($hh + $mm/60 + $ss/3600);

    return $ra;
}

#################################################################
#################################################################
#################################################################

sub dms2deg {

    my $dd = $_[0];
    my $dm = $_[1];
    my $ds = $_[2];

    $dd =~ s/^\+//;
    if ( $dd < 0 ) {
        $dd = 0 if ( abs($dd) < .00000001 );
        $dm = -$dm if $dm > 0;
        $ds = -$ds if $ds > 0;
    }

    my $dec = $dd + $dm/60 + $ds/3600;

    return $dec;

}


######################################################################
### find_planned_roll: get planned roll from mp web page          ####
######################################################################

sub find_planned_roll{

#
#---- the table below was created by find_planned_roll.perl in the
#---- same directory. It is run by cron job once a day to update the table.
#
        open(PFH, "$obs_ss/mp_long_term");
        OUTER:
        while(<PFH>){
                chomp $_;
                @ptemp = split(/:/, $_);
                %{planned_roll.$ptemp[0]} = (planned_roll =>["$ptemp[1]"]);

        }
        close(PFH);
}
