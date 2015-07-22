#!/usr/bin/perl 

#################################################################################################
#												#
#	find_mismatch.perl: find mis-match entries on updates_table.list and files in updates	#
#			    and notify test_user about the problem.				#
#												#
#		author: t. isobe (tisobe@cfa.harvard.edu)					#
#												#
#		last update: Mar 27, 2013							#
#												#
#################################################################################################

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
#---- set directory paths : updated to read from a file (02/25/2011)
#

open(IN, '/data/mta4/CUS/www/Usint/ocat/Info_save/dir_list');
while(<IN>){
        chomp $_;
        @atemp    = split(/:/, $_);
        $atemp[0] =~ s/\s+//g;
        if($atemp[0] =~ /obs_ss/){
                $obs_ss   = $atemp[1];
        }elsif($atemp[0]  =~ /pass_dir/){
                $pass_dir = $atemp[1];
        }elsif($atemp[0]  =~ /mtemp_dir/){
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
#--- if this is a test case, use the first directory, otherwise use the real one
#

if($usint_on =~ /test/i){
        $ocat_dir = $test_dir;
}else{
        $ocat_dir = $rea_dir;
}


#
#--- select out entries which need to be signed off
#

system("cat $ocat_dir/updates_table.list | grep NA > $temp_dir/ztemp");
open (FILE, "$temp_dir/ztemp");
@revisions = <FILE>;
system("rm $temp_dir/ztemp");
close(FILE);

#
#--- make a list of file entries
#

$compare = `ls $ocat_dir/updates/*`;

@temp_save  = ();
$cnt        = 0;
OUTER:
foreach $ent (@revisions){
        @ctemp = split(/\t+/, $ent);
        if($ctemp[4] !~ /NA/){                  #--- if it is already "verified", skip
                next OUTER;
        }

#
#--- compare two and if there are mis match save it.
#
	if($compare !~ /$ctemp[0]/){
		push(@temp_save, $ctemp[0]);
		$cnt++;
	}
}

#
#--- if there is mis match, send out email notice
#

if($cnt > 0){
	open(OUT, ">$temp_dir/temp_notice");
	if($cnt == 1){
		print OUT "The following entrys does not have an accompanied data file: \n\n";
	}else{
		print OUT "The following entries do not have accompanied data files: \n\n";
	}
	foreach $ent (@temp_save){
		print OUT "\t\t$ent\n";
	}
	close(OUT);

	system("cat $temp_dir/temp_notice | mailx -s\"Subject: Mismatch in updates_table.list\n\"  $test_email");

	system("rm $temp_dir/temp_notice");
}

