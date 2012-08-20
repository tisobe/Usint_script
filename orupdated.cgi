#!/soft/ascds/DS.release/ots/bin/perl
# R. Kilgard, Jan 30/31 2000
# This script generates a dynamic webpage for keeping track of updates to
# target parameters.  
#
# last udpated Mar. 28, 2011 (t. isobe: tisobe@cfa.harvard.edu)
#
#

use CGI;

print "Content-type: text/html\n\n";

read(STDIN,$newinfo,$ENV{'CONTENT_LENGTH'});


print "<HEAD><TITLE>Updated Targets List</TITLE></HEAD>";
print "<BODY BGCOLOR=\"#FFFFFF\">";

print "<H1>Updated Targets List</H1>";
print "<P>This list contains all targets which have been verified as updated.";
print "<P><B><A HREF=\"https://icxc.harvard.edu/cgi-bin/usg/search.html\">Chandra Uplink Support Observation Search Form</A></B><BR>";
print "<B><A HREF=\"https://icxc.harvard.edu/cus/\">Chandra Uplink Support Organizational Page</A></B><P>";
#####
open (FILE, "</data/udoc1/ocat/updates_table.list");
@revisions = <FILE>;
close (FILE);
#####
print "<TABLE BORDER=\"1\" CELLPADDING=\"5\">";
print "<TR><TH>OBSID.revision</TH><TH>general obscat edits by</TH><TH>ACIS obscat edits by</TH><TH>SI MODE edits by</TH><TH>Verified by</TH></TR>";
# because log is appended to, rather than added to...
@revisions= reverse(@revisions);

foreach $line (@revisions){
    chop $line;
    @values= split ("\t", $line);
    $obsrev = $values[0];
    $general_status = $values[1];
    $acis_status = $values[2];
    $si_mode_status = $values[3];
    $dutysci_status = $values[4];
    $seqnum = $values[5];
    $user = $values[6];
    ($na0,$na1,$na2,$na3,$na4,$na5,$na6,$na7,$na8,$mtime,$na10,$na11,$na12) = stat "/data/udoc1/ocat/updates/$obsrev";
    ($t0,$t1,$t2,$t3,$t4,$t5,$t6,$t7,$t8) = localtime($mtime);
    $month = $t4 + 1;
    $day = $t3;
    $year = $t5 + 1900;
    $ftime ="$month/$day/$year";
    unless ($dutysci_status =~/NA/){
	print "<TR>";
	print "<TD><A HREF=\"http://icxc.harvard.edu/uspp/updates/$obsrev\">$obsrev</A><BR>$seqnum<BR>$ftime<BR>$user</TD>";
	print "<TD>$general_status</TD><TD>$acis_status</TD><TD>$si_mode_status</TD><TD><FONT COLOR=\"#005C00\">$dutysci_status</FONT></TD></TR>";

    }
}
print "</TABLE></FORM></BODY></HTML>";
