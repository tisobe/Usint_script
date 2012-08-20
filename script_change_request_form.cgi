#!/soft/ascds/DS.release/ots/bin/perl
use CGI qw/:standard :netscape /;

#################################################################################################################################
#																#
#	script_change_request_form.cgi: this is the page which a user can put a request of change/update/bug correction to 	#
#				    T. Isobe for his scripts/software.								#
#																#
#		author: t. isobe (tisobe@cfa.harvard.edu)									#
#																#
#		last update: Feb. 16, 2012											#
#																#
#################################################################################################################################

#
#--- if argument is added, it will read test directory. you can use either "test" or your cfa email address
#--- if you provide your cfa email address, change notification will be sent to that email address, otherwiese
#--- it will be sent to isobe@head.cfa.harvard.edu
#

$version = $ARGV[0];
chomp $version;
$email   = '';

if($version eq ''){
	$version = 'test';	#--- test location
#	$version = 'live';	#--- live location
}elsif($version =~/cfa.harvard.edu/){
	$email   = $version;
	$version = 'test';
}else{
	$version  = 'test';
}

if($version =~ /live/){
	$dir = '/data/mta1/isobe/Records/MTA/Script_list/Script_change_request/';
}else{
	$dir = '/data/mta1/isobe/Records/MTA/Script_list/Script_change_request/Test/';
}


if($email eq ''){
	$email = 'isobe@head.cfa.harvard.edu';
}

#
#--- this is a temp directory for writing
#

$http_temp = '/data/udoc1/ocat/Working_dir/http/';

#
#--- read a list of the request made in the past
#

open(FH, "$dir/request_list");

@name = ();
@file = ();
$tot  = 0;

while(<FH>){
	chomp $_;
	@atemp = split(/<>/, $_);
	push(@name, $atemp[0]);			#---- name of the request
	push(@file, $atemp[1]);			#---- the file location which describes the request
	$tot++;
}
close(FH);

#
#--- here we start html/cgi
#

print header(-type => 'text/html');
print start_html(-bgcolor=>"white", -title=>'A Script Update Request Form');

print  '<body style="background-color:#FAEBD7; font-family:serif, sans-serif;font-size:12pt; color:black;" >';


print '<h2 style="background-color:blue; color:#FAEBD7">A Script Update Request Form</h2>';
print '<div style="text-align:right"><a href="http://asc.harvard.edu/mta/ti_script_list/scrpint_list_table.html"><strong>Back to A List of Software Page</strong></a></div>';


print start_form();

$display = param("display");			#--- this is the param to contorl which pages to show up

if($display =~ /Back to Top Page/ || $display =~ /Cancel/){
	main();					#--- the top page

}elsif($display =~ /Add New Request/){
	add_new();				#--- adding a new request

}elsif($display =~ /Submit/ || $display =~ /Update/){
	update();				#--- update the database and back to the (updated) top page

	open(FH, "$dir/request_list");
	
	@name = ();
	@file = ();
	$tot  = 0;
	
	while(<FH>){
		chomp $_;
		@atemp = split(/<>/, $_);
		push(@name, $atemp[0]);			#---- name of the request
		push(@file, $atemp[1]);			#---- the file location which describes the request
		$tot++;
	}
	close(FH);
	main();

}else{
$display = param('display');
	if($display eq ''){
		main();
	}else{

#
#--- find the file name
#

		$pos = $display;

		print "<input type=\"hidden\" name=\"file_id\" value=\"$pos\">";

		read_file();

		if($d_final =~ /Open/i){
			show_page(); 			#--- show the indivisual request page
		}else{
			show_page_closed();		#--- show closed page so that no one can edit any further
		}
	}
}

print end_form();

print '<hr />';
print "<p style='font-size:80%'><em>";
print 'If you have any questions about this site, please contact: <a href="mailto:isobe@head.cfa.harvard.edu">isobe@head.cfa.harvard.edu</a>';
print "</em></p>";
print "<p style='font-size:80%;text-align:right'><em>";
print 'Last Update: Feb 16, 2012';
print '</em></p>';

print "</body>";
print "</html>";


###################################################################################################
### main: display top page which displays a list of past/current request names                  ###
###################################################################################################

sub main{
	
#
#--- displaying the past request names
#

	print "<p style='padding-bottom: 30px;padding-top:30px'>";
	print "This page let you make a update/modification/bug correction request to ";
	print "T. Isobe on his scripts/programs. If you add a new request or make modificaiton on ";
	print "the request, this script will automatically notify him the change. ";
	print "</p>";

	print "<h3 style='padding-bottom:20px'>Click <em>File ID</em> to see the content</h3>";

	print "<p>";
	print "<input type=\"submit\" name=\"display\" value=\"Add New Request\")";
	print "</p>";

	print "<table border=2 cellpadding=4 cellspacing=4>";
	print "<tr><th>File ID</th><th>Request Name</th><th>Date Created</th><th>Date Completed</th></tr>";

	for($i = 0; $i < $tot; $i++){

		$pos = $i;
		read_file();

		print "<tr><th>";
		print "<input type=\"submit\" name=\"display\" value=\"$i\">";
#		print submit(-name=>'display',-value=>"$name[$i]",-default=>"$name[$i],-override=>10000"); 
		print "</th>";
		print "<td>$name[$i]</td><td>$d_open</td>";
		if($d_final =~ /Open/i){
			print "<td>&#160</td></tr>";
		}else{
			print "<td>$d_final</td></tr>";
		}

	}

	print "</table>";

	print "<p style='padding-bottom:40px'>";
	print "<input type=\"submit\" name=\"display\" value=\"Add New Request\")";
	print "</p>";
	
}

###################################################################################################
### read_file: read data file                                                                   ###
###################################################################################################

sub read_file{
#
#--- read the content of the file
#

	open(FH, "$file[$pos]");
	$chk = 0;
	$description = '';
	$algorithm   = '';
#
#--- description and algoritm have different format; so handle differently
#
	OUTER:
	while(<FH>){
		if($chk == 1){
			if($_ =~ /p_algorithm/){
				$chk = 2;
				next OUTER;
			}
			$description = "$description"."$_";
		}elsif($chk == 2){
			$algorithm   = "$algorithm"."$_";
		}

		chomp $_;
		if($_ =~ /p_description/i){
			$chk = 1;
			next OUTER;
		}
		if($_ =~ /p_algorithm/i){
			$chk = 2;
			next OUTER;
		}
		if($chk == 0){
			@atemp = split(/<>/, $_);
			if($atemp[0] =~ /proposer/){
				$proposer = $atemp[1];
			}elsif($atemp[0] =~ /others/){
				@ctemp = split(/others<>/, $_);
				$others   = $ctemp[1];
			}elsif($atemp[0] =~ /affected/){
				$affected = $atemp[1];
			}elsif($atemp[0] =~ /prepared/){
				$prepared = $atemp[1];
			}elsif($atemp[0] =~ /category/){
				$category = $atemp[1];
			}elsif($atemp[0] =~ /script/){
				$script   = $atemp[1];
			}elsif($atemp[0] =~ /test_site/){
				$test_site= $atemp[1];
			}elsif($atemp[0] =~ /d_open/){
				$d_open   = $atemp[1];
			}elsif($atemp[0] =~ /d_prop/){
				$d_prop   = $atemp[1];
			}elsif($atemp[0] =~ /d_test/){
				$d_test   = $atemp[1];
			}elsif($atemp[0] =~ /d_final/){
				$d_final  = $atemp[1];
			}
		}
	}
	close(FH);
}

###################################################################################################
### show_page: display a specified request page                                                 ###
###################################################################################################

sub show_page{

#
#--- find the file name
#

	$pos = $display;

	print "<input type=\"hidden\" name=\"file_id\" value=\"$pos\">";

	read_file();

#
#--- start printing the page
#

	print "<p style='text-align:right'>";
	print "<input type=\"submit\" name=\"display\" value=\"Back to Top Page\" style='text-align:right'>";
	print "</p>";

#
#--- name of the request
#
	print "<h3><u>$name[$pos]</u></h3>";

	print "<table border=0 cellpadding=4 cellspacing=4 style='padding-bottom:40px'>";

	print "<tr><th width=18%>&#160</th><th width=18%>&#160</th><th width=18%>Proposal Accepted</th><th width=18%>Tested</th><th width=18%>Final Approval</th></tr>";

	print "<input type=\"hidden\" name=\"name\" value=\"$name[$pos]\">";
#
#--- name of the proposer
#

	print "<tr><th>Requested by</th>";
	@atemp = split(/:/, $proposer);
	print "<td>$atemp[0]</td>";
	print "<td>";
 	print popup_menu(-name=>"prop1", -value=>['No', 'Yes'], -default=>"$atemp[1]",-override=>1000000);
	print "</td><td>";
 	print popup_menu(-name=>"prop2", -value=>['No', 'Yes'], -default=>"$atemp[2]",-override=>1000000);
	print "</td><td>";
 	print popup_menu(-name=>"prop3", -value=>['No', 'Yes'], -default=>"$atemp[3]",-override=>1000000);
	print "</td></tr>";

	print "<input type=\"hidden\" name=\"propsose_name\" value=\"$atemp[0]\">";


	@otemp = split(/<>/, $others);
	$ocnt  = 0;
	foreach(@otemp){
		$ocnt++;
	}
#
#--- name of others
#

#	print "<tr><th>Others</th></tr>";

	print "<input type=\"hidden\" name=\"ocnt\" value=\"$ocnt\">";

	for($i = 0; $i < $ocnt; $i++){
		@atemp = split(/:/, $otemp[$i]);
		$oname  = 'oname'."$i";
		$oname1 = 'oname'."$i".'_1';
		$oname2 = 'oname'."$i".'_2';
		$oname3 = 'oname'."$i".'_3';

		if($i == 0){
			print "<tr><th>Others</th>";
		}else{
			print "<tr><th>&#160</th>";
		}
		print "<td>$atemp[0]</td>";
		print "<td>";
 		print popup_menu(-name=>"$oname1", -value=>['No', 'Yes'], -default=>"$atemp[1]",-override=>1000000);
		print "</td><td>";
 		print popup_menu(-name=>"$oname2", -value=>['No', 'Yes'], -default=>"$atemp[2]",-override=>1000000);
		print "</td><td>";
 		print popup_menu(-name=>"$oname3", -value=>['No', 'Yes'], -default=>"$atemp[3]",-override=>1000000);
		print "</td></tr>";

		print "<input type=\"hidden\" name=\"$oname\" value=\"$atemp[0]\">";
	}

#
#---- affected parties
#	
	print "<tr><th>Affected Parties</th>";
	print "<td>$affected</td></tr>";
	print "<input type=\"hidden\" name=\"affected\" value=\"$affected\">";

#
#----  a person prepared this document
#
	print "<tr><th>Document Prepared by</th>";
	print "<td>$prepared</td></tr>";
	print "<input type=\"hidden\" name=\"prepared\" value=\"$prepared\">";
#
#---- category of this request
#
	print "<tr><th>Category</th>";
	print "<td>$category</td></tr>";
	print "<input type=\"hidden\" name=\"category\" value=\"$category\">";
#
#----  name of the script/ program
#
	print "<tr><th>Script/Program</th>";
	print "<td>$script</td></tr>";
	print "<input type=\"hidden\" name=\"script\" value=\"$script\">";

#
#----  test site
#
	print "<tr><th>Test Site</th>";
	print "<td>";

	print '<textarea name="test_site" rows="8" cols="60"  WRAP=virtual>';
	print "$test_site";
	print "</textarea>";

	print "</td></tr>";

#
#--- date: open date/propsal date/ test date/ final date
#
	print "<tr><th>Date</th></tr>";
	print "<tr><th>Request Open</th><td>$d_open</td></tr>";
	print "<input type=\"hidden\" name=\"d_open\" value=\"$d_open\">";
	print "<tr><th>Proposal Accepted</th><td>";
	print textfield(-name=>'d_prop', -value=>"$d_prop", -size=>'15');
	print " </td></tr>";
	print "<tr><th>Test Version</th><td>"; 
	print textfield(-name=>'d_test', -value=>"$d_test", -size=>'15');
	print "</td></tr>";
	print "<tr><th>Final Approval</th><td>";
	print textfield(-name=>'d_final', -value=>"$d_final", -size=>'15');
	print "</td></tr>";
	print '</table>';

#
#--- description of the request
#

	print '<h3>Short Description</h3>';

	print "<p style='padding-bottom:20px'>";
	print $description;
	print "</p>";
	print "<input type=\"hidden\" name=\"description\" value=\"$description\">";
#
#--- algorithm
#
	print '<h3>Proposed Change/Algorithm</h3>';

	print "<p style='padding-bottom:20px'>";
	print '<textarea name="algorithm" rows="60" cols="100"  wrap=virtual >';
	print "$algorithm";
	print "</textarea>";
	print "</p>";


	print submit(-name=>'display',-value=>'Update') ;


}


###################################################################################################
### show_page_closed: display a specified request page but closed form                          ###
###################################################################################################

sub show_page_closed{

#
#--- find the file name
#

	$pos = $display;

	read_file();

#
#--- start printing the page
#

	print "<p style='text-align:right'>";
	print "<input type=\"submit\" name=\"display\" value=\"Back to Top Page\" style='text-align:right'>";
	print "</p>";

#
#--- name of the request
#
	print "<h3><u>$name[$pos]</u></h3>";
	print "<h3 style='color:red'><em>This Request is Completed and Closed ($d_final)</em></h3>";

	print "<table border=0 cellpadding=4 cellspacing=4 style='padding-bottom:40px'>";

	print "<tr><th width=18%>&#160</th><th width=18%>&#160</th><th width=18%>Proposal Accepted</th><th width=18%>Tested</th><th width=18%>Final Approval</th></tr>";

#
#--- name of the proposer
#

	print "<tr><th>Requested by</th>";
	@atemp = split(/:/, $proposer);
	print "<td>$atemp[0]</td>";
	print "<td>$atemp[1]</td>";
	print "<td>$atemp[2]</td>";
	print "<td>$atemp[3]</td>";
	print "</tr>";


	@otemp = split(/<>/, $others);
	$ocnt  = 0;
	foreach(@otemp){
		$ocnt++;
	}
#
#--- name of others
#

	for($i = 0; $i < $ocnt; $i++){
		@atemp = split(/:/, $otemp[$i]);
		$oname  = 'oname'."$i";
		$oname1 = 'oname'."$i".'_1';
		$oname2 = 'oname'."$i".'_2';
		$oname3 = 'oname'."$i".'_3';

		if($i == 0){
			print "<tr><th>Others</th>";
		}else{
			print "<tr><th>&#160</th>";
		}
		print "<td>$atemp[0]</td>";
		print "<td>$atemp[1]</td>";
		print "<td>$atemp[2]</td>";
		print "<td>$atemp[3]</td>";
		print "</tr>";

	}

#
#---- affected parties
#	
	print "<tr><th>Affected Parties</th>";
	print "<td>$affected</td></tr>";

#
#----  a person prepared this document
#
	print "<tr><th>Document Prepared by</th>";
	print "<td>$prepared</td></tr>";
#
#---- category of this request
#
	print "<tr><th>Category</th>";
	print "<td>$category</td></tr>";
#
#----  name of the script/ program
#
	print "<tr><th>Script/Program</th>";
	print "<td>$script</td></tr>";

#
#----  test site
#
	print "<tr><th>Test Site</th>";
	print "<td>";

	print "$test_site";

	print "</td></tr>";

#
#--- date: open date/propsal date/ test date/ final date
#
	print "<tr><th>Date</th></tr>";
	print "<tr><th>Request Open</th><td>$d_open</td></tr>";
	print "<tr><th>Proposal Accepted</th><td>$d_prop</td></tr>";
	print "<tr><th>Test Version</th><td>$d_test</td></tr>"; 
	print "<tr><th>Final Approval</th><td>$d_final</td></tr>";
	print '</table>';

#
#--- description of the request
#

	print '<h3>Short Description</h3>';

	print "<p style='padding-bottom:20px'>";
	print $description;
	$tout = $description;
	$tout =~ s/\n/<br\/>/g;
	print "$tout";
	print "</p>";

#
#--- algorithm
#
	print '<h3>Proposed Change/Algorithm</h3>';

	print "<p style='padding-bottom:20px;padding-top:10px;margin-left:20px;padding-left:20px;margin-right:60px;background-color:yellow'>";

	$tout = $algorithm;
	$tout =~ s/\n/<br\/>/g;
	print "$tout";

	print "</p>";


	print "<p style='text-align:right'>";
	print "<input type=\"submit\" name=\"display\" value=\"Back to Top Page\" style='text-align:right'>";
	print "</p>";
}

###################################################################################################
### add_new: adding a new change request                                                        ###
###################################################################################################

sub add_new{
	
	print "<p style='text-align:right'>";
	print "<input type=\"submit\" name=\"display\" value=\"Back to Top Page\" style='text-align:right'>";
	print "</p>";


	print "<h2>New Request Page</h2>";


	print "<table border=0 cellpadding=4 cellspacing=4 style='padding-bottom:40px'>";
#
#---- name of the requested change/update/bug fix
#
	print "<tr><th>Request Name</th><td>";
	print textfield(-name=>'name', -value=>'', -size=>70);
	print "</td></tr>";

	print "<tr><td>&#160</td><td><em>Eample: Adding a new field in Ocat Page</em></td></tr>";
#
#--- name of the person requested
#
	print "<th>Requested by<br /> (name and email address) </th><td>";
	print textfield(-name=>'proposer', -value=>'', -size=>60);
	print "</td></tr>";

	print "<tr><td>&#160</td><td><em>Format: first last (eamil): Example: Takashi Isobe (isobe\@head.cfa.harvard.edu)</em></td></tr>";
#
#--- names of other peeople who involve to this project
#
	print "<tr><th colspan=2 align='left'>Others (The names and email of people who involve in this request)</th></tr>";

	print "<th> name and email address </th><td>";
	print textfield(-name=>'oname1', -value=>'', -size=>60);
	print "</td></tr>";

	print "<th> name and email address </th><td>";
	print textfield(-name=>'oname2', -value=>'', -size=>60);
	print "</td></tr>";

	print "<th> name and email address </th><td>";
	print textfield(-name=>'oname3', -value=>'', -size=>60);
	print "</td></tr>";

	print "<th> name and email address </th><td>";
	print textfield(-name=>'oname4', -value=>'', -size=>60);
	print "</td></tr>";

	print "<th> name and email address </th><td>";
	print textfield(-name=>'oname5', -value=>'', -size=>60);
	print "</td></tr>";

	print "<th> name and email address </th><td>";
	print textfield(-name=>'oname6', -value=>'', -size=>60);
	print "</td></tr>";
#
#---- clients
#
	
	print "<tr><th>Affected Parties</th><td>";
	print textfield(-name=>'affected', -value=>'', -size=>60);
	print "</td></tr>";

	print "<tr><td>&#160</td><td><em>People and/or Group possibly affected by this change</em></td></tr>";
#
#---  person prepared this document
#

	print "<tr><th>Document Prepared by</th><td>";
	print textfield(-name=>'prepared', -value=>'', -size=>60);
	print "</td></tr>";

	print "<tr><td>&#160</td><td><em>Person's name who prepared this page: Example: Takashi Isobe (isobe\@head.cfa.harvard.edu)</em></td></tr>";

#
#---- category of this request
#
	print "<tr><th>Category</th><td>";
	print textfield(-name=>'category', -value=>'', -size=>60);
	print "</td></tr>";

	print "<tr><td>&#160</td><td><em>The category of this script belong to. USINT/POC/MTA/Misc</em></td></tr>";

#
#---- script/program names
#
	print "<tr><th>Script/Program</th><td>";
	print textfield(-name=>'script', -value=>'', -size=>60);
	print "</td></tr>";

	print "<tr><td>&#160</td><td><em>The script name or the web address. Example: ACIS Focal Plane Temperature<br />";
	print "https://icxc.harvard.edu/mta/CUS/Usint/ocatdata2html.cgi</em></td></tr>";
#
#---- test site
#
	print "<tr><th>Test Site</th><td>";
	print '<textarea name="test_site" rows="8" cols="60"  wrap=virtual >';
	print "$test_site";
	print "</textarea>";
	print "</td></tr>";

	print "<tr><td>&#160</td><td><em>Where is the test site and the name of the test script. You can add a short description.</em></td></tr>";

	print '</table>';
#
#--- short description
#

	print '<h3>Short Description</h3>';

	print "<p>Please describe why you need this change and what are expected from this change.</p>";

	print "<p style='padding-bottom:20px'>";

	print '<textarea name="description" rows="20" cols="72"  wrap=virtual >';
	print "$algorithm";
	print "</textarea>";
	print "</p>";
#
#--- algorithm
#

	print '<h3>Proposed Change/Algorithm</h3>';

	print "<p>Please add a step by step description of the change/algorithm.</p>";

	print "<p style='padding-bottom:20px'>";
	print '<textarea name="algorithm" rows="60" cols="72"  wrap=virtual >';
	print "$algorithm";
	print "</textarea>";
	print "</p>";


	print '<input type="submit" name="display" value="Submit">';
	print "<input type=\"submit\" name=\"display\" value=\"Cancel\">";

}



###################################################################################################
### update: update database                                                                     ###
###################################################################################################

sub update{
	
#
#---- request name
#
	$n_name = param('name');
#
#--- proposer's name
#

	if($display =~ /Update/){
		$propsose_name = param('propsose_name');
		$prop1         = param('prop1');
		$prop2         = param('prop2');
		$prop3         = param('prop3');

		$proposer = "$propsose_name:$prop1:$prop2:$prop3";
	}else{
		$proposer = param('proposer');
	}

#
#--- other people's name. count how many of them are listed
#
	if($display =~ /Update/){
		$ocnt = param('ocnt');

		$i = 0;
               	$oname  = 'oname'."$i";
               	$oname1 = 'oname'."$i".'_1';
               	$oname2 = 'oname'."$i".'_2';
               	$oname3 = 'oname'."$i".'_3';

		$o_name = param("$oname");
		$o_chk1 = param("$oname1");
		$o_chk2 = param("$oname2");
		$o_chk3 = param("$oname3");

		$others = "$o_name:$o_chk1:$o_chk2:$o_chk3";

        	for($i = 1; $i < $ocnt; $i++){
                	$oname  = 'oname'."$i";
                	$oname1 = 'oname'."$i".'_1';
                	$oname2 = 'oname'."$i".'_2';
                	$oname3 = 'oname'."$i".'_3';

			$o_name = param("$oname");
			$o_chk1 = param("$oname1");
			$o_chk2 = param("$oname2");
			$o_chk3 = param("$oname3");

			$aline = "$o_name:$o_chk1:$o_chk2:$o_chk3";
			$others  = "$others<>"."$aline";
		}
	}else{
		$ocnt   = 0;
		$oname1 = param('oname1');
		if($oname1 ne ''){
			$ocnt++;
		}
		$oname2 = param('oname2');
		if($oname2 ne ''){
			$ocnt++;
		}
		$oname3 = param('oname3');
		if($oname3 ne ''){
			$ocnt++;
		}
		$oname4 = param('oname4');
		if($oname4 ne ''){
			$ocnt++;
		}
		$oname5 = param('oname5');
		if($oname5 ne ''){
			$ocnt++;
		}
		$oname6 = param('oname6');
		if($oname6 ne ''){
			$ocnt++;
		}
	}
#
#--- affected party
#
	$affected = param('affected');
#
#--- person prepared this document
#
	$prepared = param('prepared');
#
#--- the category which this request is mande
#
	$category = param('category');
#
#--- script name
#
	$script   = param('script');
#
#--- test script location name
#
	$test_site = param('test_site');
#
#--- find today's date
#

	if($display != /Update/){
		$d_open   = param('d_open');
		$d_prop   = param('d_prop');
		$d_test   = param('d_test');
		$d_final  = param('d_final');
		
	}else{
		$input    = `date`;
		@dtemp    = split(/\s+/, $input);
		$d_open   = "$dtemp[1] $dtemp[2] $dtemp[5]";
		$d_prop   = 'Open';
		$d_test   = 'Open';
		$d_final  = 'Open';
	}
#
#--- description of the request
#
	$description = param('description');
#
#--- algorithm
#
	$algorithm   = param('algorithm');

#
#--- update the current list
#

	if($display =~ /Update/){
		$file_id   = param('file_id');
		$file_name = "$dir/Prop/file_"."$file_id";

		system("chgrp mtagroup $dir/request_list");
		system("chmod 775 $dir/request_list");

#
#--- sending notificaiton email
#
		open(OUT, ">$http_temp/ti_change_temp");
		print OUT "Change Request Content Updated: $file_name\n";
		print OUT "Title: $n_name\n";
		close(OUT);

		system("cat $http_temp/ti_change_temp | mailx -s\"Subject: Change Request Content Updated \n\" -rcus\@head.cfa.harvard.edu $email");
		system("rm $http_temp/ti_change_temp");
		$old = "$file_name".'~';
		system("cp $file_name $old");

	}else{
		push(@name, $n_name);
		$file_name = "$dir/Prop/file_"."$tot";
		push(@file, $file_name);
		$tot++;

		open(OUT, ">$dir/request_list");
		for($i = 0; $i < $tot; $i++){
			print OUT "$name[$i]<>$file[$i]\n";
		}
		close(OUT);

#
#--- sending notificaiton email
#
		system("chgrp mtagroup $dir/request_list");
		system("chmod 775 $dir/request_list");

		open(OUT, ">$http_temp/ti_change_temp");
		print OUT "A new request is addred: $file_name\n";
		print OUT "Title: $n_name\n";
		close(OUT);

		system("cat $http_temp/ti_change_temp | mailx -s\"Subject: A New Change Request Added\n\" -rcus\@head.cfa.harvard.edu $email");
		system("rm $http_temp/ti_change_temp");
	}
#
#--- save the new request in the database
#
	open(OUT, ">$file_name");

	print OUT "name<>","$n_name\n";
	if($display =~ /Update/){
		print OUT "proposer<>","$proposer\n";
		print OUT "others<>","$others\n";

	}else{
		print OUT "proposer<>","$proposer",":Check:Check:Check","\n";

		print OUT "others<>";
		$line = "$oname1:Check;Check:Check";
		for($j = 2; $j <= $ocnt; $j++){
			$aname = 'oname'."$j";
			$aline = "${$aname}:Check;Check:Check";
			$line  = "$line"."<>"."$aline";
		}
		print OUT "$line\n";
	}

	print OUT "affected<>","$affected\n";

	print OUT "prepared<>", "$prepared\n";

	print OUT "category<>", "$category\n";

	print OUT "script<>", "$script\n";

	print OUT "test_site<>", "$test_site\n";

	print OUT "d_open<>", "$d_open\n";

	print OUT "d_prop<>", "$d_prop\n";

	print OUT "d_test<>", "$d_test\n";

	print OUT "d_final<>", "$d_final\n";

	print OUT "p_description\n";

	print OUT "$description\n";

	print OUT "p_algorithm\n";
	
	print OUT "$algorithm\n";

	close(OUT);


	system("chgrp mtagroup $file_name");
	system("chmod 775 $file_name");
}

