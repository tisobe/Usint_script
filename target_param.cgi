#!/usr/local/bin/perl

BEGIN { $ENV{'SYBASE'} = "/soft/sybase";} 
use DBI;
use DBD::Sybase;
use CGI;


###############################################################################
# This is a first-draft script to dynamically create a page based on obsid.  
# It works, as far as I can tell....
# Note:  Currently, this script MUST use the above version of perl and contain
# all the use statements above.
# Ok, that's probably not true - I don't think I'm using DBlib at all.
# It is more complex to use CTlib, but I'm told by the experts that
# DBlib is going to be discontinued.
# -Roy Kilgard, April 2000
###########################################################################
#This script is also modified by Mihoko Yukita
# and by Samantha Stevenson (July 2005)
# modified to account for removal of the following:
#    bias_after, frequency, bias_request, fep,  standard_chips , subarray_frame_time
# Oct, 2007 - Tara Gokas
# vla, vlba removed from joint table, nrao added
# 
# NOT ACCOUNTED FOR YET:
# multitelescope_interval added to target
# 
###############################################################################

#get the obsid from the CL
$obsid= $ARGV[0];

print "Content-type: text/html\n\n";



#######################################
#########print html
######################################

print <<ENDOFHTML;
<HTML>
<head>
<TITLE>Obscat Data Page</TITLE>
<link rel="stylesheet" href="/incl/cxcstyle_hfonly.css" type="text/css" media="screen">
</head>
<BODY BGCOLOR="#FFFFFF">

<h1>Obscat Data Page</h1>
<p>This page has been replaced by functionality in <a href="http://cda.harvard.edu/chaser/startViewer.do?menuItem=details&obsid=$obsid">WebChaSeR</a>.
</p>
<p>
<a href="http://cda.harvard.edu/chaser/startViewer.do?menuItem=details&obsid=$obsid">http://cda.harvard.edu/chaser/startViewer.do?menuItem=details&obsid=$obsid</a>
</p>


<hr>
ENDOFHTML

print "</BODY>";
print "</HTML>";
exit();



