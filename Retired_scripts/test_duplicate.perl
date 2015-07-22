#!/usr/bin/perl 

#################################################################################################
#												#
#	test_duplicate.perl: check whether there are any duplicated version # entries in	#
#			     updatas_table.list, and if there are send out warning email	#
#												#
#			author: t. isobe (tisobe@cfa.harvard.edu)				#
#												#
#			last update: Sept 17, 2009						#
#												#
#################################################################################################

#
#--- dirctory where the data exist
#

$dir   = '/data/udoc1/ocat/';

#
#--- who is the charge for the databse?
#

$person = 'isobe';

#
#--- get a list of entries, but just about latest 300 of them
#

$input =  ` ls -rt $dir/updates`;
@list  = split(/\s+/, $input);
@reversed = reverse(@list);
@temp     = ();
for($i = 0; $i < 300; $i++){
	@atemp = split(/\./, $reversed[$i]);
	push(@temp, $atemp[0]);
}

#
#--- get only obsids, not version #
#

@sorted = sort{$a<=>$b} @temp;
$test   = shift(@sorted);
@sample = ($test);
foreach $ent (@sorted){
	if($ent != $test){
		push(@sample, $ent);
		$test = $ent;
	}
}

#
#--- check a temp file exits or not, if it does, remove it
#

$etest = ` ls *`;
if($etest =~ /zwarning/){
	system('rm ./zwarning');
}

#
#--- check whether any duplicated version # for each obsid
#
$p_yes = 0;
foreach $obsid (@sample){

#
#--- sub to check problems
#

	check_duplicated_version();

	if($dcnt > 0){
#
#--- if there are duplicated verion # exist, report here
#
		$line1 = "$obsid has duplicated version: ";
		for($j = 0; $j < $dcnt; $j++){
			$line1 = "$line1"." duplicate[$j]\t";
		}
		open(OUT, ">>./zwarning");
		print OUT "$line1\n";
		close(OUT);
		$p_yes++;
	}
	if($d_indicator > 0){
#
#--- if extra version # in updates_table.list, report here
#
		$line2 = "$obsid is missing database version entries: ";
		for($j = 0; $j < $d_indicator; $j++){
			$line2 = "$line2"."$no_match[$j]\t";
		}
		open(OUT, ">>./zwarning");
		print OUT "$line2\n";
		close(OUT);
		$p_yes++;
	}
	if($d_indicator < 0){
#
#--- if extra version # in updates directory, report here
#
		$line2 = "$obsid is missing table version entries: ";
		$upper = abs($d_indicator);
		for($j = 0; $j < $upper; $j++){
			$line2 = "$line2"."$no_match[$j]\t";
		}
		open(OUT, ">>./zwarning");
		print OUT "$line2\n";
		close(OUT);
		$p_yes++;
	}
}	

if($p_est > 0){
#
#--- send out to a person in charge
#
	system("cat ./zwarning |mailx -s \"Subject: Problem in updates_table.list\n\" -r  mta\@head.cfa.harvard.edu $person\@head.cfa.harvard.edu");
	system("rm ./zwarning");
}





#######################################################################################
#######################################################################################
#######################################################################################

sub check_duplicated_version{


	my(@atemp, @btemp, @version, @version2, $cnt, $cnt2);

#
#--- find obsid entires from udatas_table.list
#

	$name  = "$obsid".'\.';
	$input = `cat $dir/updates_table.list |grep $name`;
	@entry = split(/\s+/, $input);

	@version = ();
	$cnt     = 0;

	foreach $ent (@entry){
		if($ent =~ /$obsid/){
			@btemp = split(/\./, $ent);
			push(@version, $btemp[1]);
			$cnt++;
		}
	}

#
#--- check whether there are duplicated version # for this obsid on the table
#
	
	@order     = ();
	@duplicate = ();
	$ocnt      = 0;
	$dcnt      = 0;
	if($cnt > 0){
		@test = sort{$a<=>$b}@version;
		$out  = shift(@test);
		@order= ($out);
		foreach $ent (@test){
			if($out == $ent){
				push(@duplicate, $ent);
				$dcnt++;
			}else{
				$out = $ent;
				push(@order, $ent);
				$ocnt++;
			}
		}
	}

#
#--- now extract version # from data files kept in updates directory
#

	$name  = "$obsid".'*';
	$input = `ls $dir/updates/$name`;
	@entry = split(/\s+/, $input);
	
	@version2 = ();
	$cnt2     = 0;

	$name  = "$obsid".'\.';
	foreach $ent (@entry){
		@atemp = split(/$name/, $ent);
		push(@version2, $atemp[1]);
		$cnt2++;
	}

#
#--- start checking whether version # entries match 
#

	$d_indicator = 0;
	$chk         = 0;
	@no_match    = ();

	if($cnt == 0 && $cnt2 == 0){
		$d_indicator = 0;
	}elsif($ocnt >= $cnt2){
		@no_match = ();
		$chk = 0;
		OUTER:
		foreach $ent (@order){
			foreach $comp (@version2){
				if($ent == $comp){
					next OUTER;
				}
			}
			push(@no_match, $ent);
			$chk++;
		}
		$d_indicator = $chk;
	}else{
		@no_match = ();
		$chk      = 0;
		OUTER:
		foreach $ent (@version2){
			foreach $comp (@order){
				if($ent == $comp){
					next OUTER;
				}
			}
			push(@no_match, $ent);
			$chk++;
if($chk > 0){
	print "$chk<-->$ent<--->$cnt2<--->$ocnt<--->@version2<--->@order\n";
}
		}
		$d_indicator = -$chk;
	}
}	

	
