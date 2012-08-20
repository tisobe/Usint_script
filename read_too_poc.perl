#!/usr/bin/perl 

#################################################################################
#										#
#	read_too_poc.perl: read who is too poc for this week, and print out	#
#			   email address to /home/mta/TOO-POC.			#
#										#
#		author: t. isobe (tisobe@cfa.harvard.edu)			#
#										#
#		last update Mar 04, 2011					#
#										#
#################################################################################

#
#---- set directory paths : updated to read from a file (02/25/2011) --- this is user: mta version
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

 
open(FH, "$data_dir/this_week_person_in_charge");

OUTER:
while(<FH>){
	if($_ =~ /#/){
		next OUTER;
	}else{
		chomp $_;
		@atemp = split(/\,/, $_);
		$email = $atemp[4];
		last OUTER;
	}
}
close(FH);

open(OUT, ">/home/mta/TOO-POC");
print OUT "$email\n";
close(OUT);
