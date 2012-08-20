<html>
<!-- ********************************************************************************* -->
<!--                                                                                   -->
<!-- this ptp form let a user to submit/remove/update too point of contact information -->
<!--                                                                                   -->
<!-- 		author: t. isobe (tisobe@cfa.harvrd.edu)			       -->
<!--            last update: Nov 25, 2009                                              -->
<!--                                                                                   -->
<!-- ********************************************************************************* -->

<head>
<title>Input a New Contact Information</title>

<style type="text/css">

/* define CSS style sheet		*/

	hr {color:sienna}

	p {margin-left:10px}

	body{   background-color:#FAEBD7;
        	font-family:     serif, sans-serif, Verdana, Helvetica, Arial;
        	font-size:       12pt;
        	margin:          20px;
        	padding:         10px;
	}
	
	table{
		font-size:      95%;
	}
	p.center{
		text-align:     center;
	}
	
	h1{
		text-align:     center;
	}
	h1, h2, h3, h4{
		font-style:     oblique;
	}
	
	h2.center{
		text-align:     center;
	}
	
	em.blue{
		color:		blue;
	}
</style>

</head>
<body>

<h2 class='center' style='background:blue;color:#FAEBD7; margin-right:10em'>Input New Contact Information</h2>

<p> 
<ul style='font-size:90%; margin-right:10em'>
<li>
If you want to <em class='blue'>submit</em> a new contact, please put all information in the fields.
If a certain information, other than name, is not available, use "NA".
Then click "Submit Contact Info" button.
</li>
<li>
If you want to <em class='blue'>replace</em> a part of information, put the contact name, and 
necessary information to appropriate fields, and click "Modify Data" button.
</li> 
<li>
If you want to <em class='blue'>remove</em> a contact, just put the EXTACT name in the name field.
Then click "Remove" button.
</li>
<li>
"Load" button just reloads the contact table below, and "Clear" button clears
the new contact inputs.
</li>
</ul>
</p>


<?php

function sentence_case($string) {
/* 
	function to make the first letter of the each word to upper case
	originally made to make the first letter of a sentense to be upper case
   	but I added ' ' to make the first letter of each word
 */
    $sentences = preg_split('/([ ])/', $string, -1, PREG_SPLIT_NO_EMPTY|PREG_SPLIT_DELIM_CAPTURE);
    $new_string = '';
    foreach ($sentences as $key => $sentence) {
        $new_string .= ($key & 1) == 0?
            ucfirst(strtolower(trim($sentence))) :
            $sentence.' ';
    }
    return trim($new_string);
}


/*  the submission from the last round tells the php what to do next	*/

    $submit = $_POST['submit'];
    if($submit == 'Clear'){
	$name   = '';
	$office = '';
	$cell   = '';
	$home   = '';
	$mail   = '';
    }elseif($submit == 'Load Data'){
	/* do nothing... */
    }else{
    	$name   = $_POST['name'];
    	$office = $_POST['office'];
    	$cell   = $_POST['cell'];
    	$home   = $_POST['home'];
    	$mail   = $_POST['mail'];

	$name   = trim($name);
	$office = trim($office);
	$cell   = trim($cell);
	$home   = trim($home);
	$mail   = trim($mail);

	$name   = sentence_case($name);
	$name   = preg_replace('/\s\s+/', ' ', $name);

	if($office == 'na' || $office == 'n/a' || $office == 'N/A'){
		$office = 'NA';
	}
	if($cell   == 'na' || $cell   == 'n/a' || $cell   == 'N/A'){
		$cell   = 'NA';
	}
	if($home   == 'na' || $home   == 'n/a' || $home   == 'N/A'){
		$home   = 'NA';
	}
	if($mail   == 'na' || $mail   == 'n/a' || $mail   == 'N/A'){
		$mail   = 'NA';
	}else{
		$mail   = strtolower($mail);
	}
   }
?>

<!--  this form telling the self referring type though php  -->

<form action=<?php echo $_SERVER['PHP_SELF']; ?>  method="post">
    <table border=0 cellpadding=4>
    <tr>
    <td>
    <label for='name'><strong>Name</strong></label>
    </td>
    <td>
    <input type='text' name='name' value="<?php echo $name; ?>" /> <br />
    </td>
    </tr>

    <tr>
    <td>
    <label for='office'><strong>Office Phone</strong></label>
    </td>
    <td>
    <input type='text' name='office' value="<?php echo $office; ?>" /> <br />
    </td>
    </tr>

    <tr>
    <td>
    <label for='cell'><strong>Cell Phone<strong></label>
    </td>
    <td>
    <input type='text' name='cell' value="<?php echo $cell; ?>" /> <br />
    </td>
    </tr>

    <tr>
    <td>
    <label for='home'><strong>Home Phone</strong></label>
    </td>
    <td>
    <input type='text' name='home' value="<?php echo $home; ?>"  /> <br />
    </td>
    </tr>

    <tr>
    <td>
    <label for='mail'><strong>Mail Address</strong> </label>
    </td>
    <td>
    <input type='text' name='mail' value="<?php echo $mail; ?>"  /> <br />
    </td>
    </tr>
    </table>

    <br />
    <input type='submit' value='Load'                name='submit' />
    <input type='submit' value='Submit Contact Info' name='submit' />
    <input type='submit' value='Modify Data'         name='submit' />
    <input type='submit' value='Remove'              name='submit' />
    <input type='submit' value='Clear'               name='submit' />
	
    <br />
</form>

<?php

/* the request is to remove the information from the data base	*/

    if($submit == "Remove"){
    	$file=fopen("./too_contact_info/personal_list","r");
   		$tot = 1;
    	while (!feof($file))
    	{
		$line = fgets($file);
		$entry = explode("<>", $line);
		if($name != $entry[0] && (!empty($entry[0])) &&  $entry[0] != "\n"){
			$cname[$tot] = $entry[0];
			$save[$tot]  = $line;
			$tot++;
		}
    	}
    	fclose($file);

	$file=fopen("./too_contact_info/personal_list","w");
	for ($i=1; $i<= $tot; $i++)
  	{
		$line = "$save[$i]";
		fwrite($file, $line);
  	}
	fclose($file);

/* the request is to submit a new point of contact information or up date the previous infor */

    }elseif(
	    (($submit == 'Submit Contact Info') 
		&& (!empty($name)) && (!empty($office)) 
		&& (!empty($cell)) && (!empty($home)) 
		&& (!empty($mail))
	    ) || (
	     ($submit == 'Modify Data')
	    )
     	){

/* check whether PC is already in the database 		*/

    	$file=fopen("./too_contact_info/personal_list","r");
   		$tot = 1;
    	while (!feof($file))
    	{
		$line = fgets($file);
		$entry = explode("<>", $line);
		if((!empty($entry[0])) &&  $entry[0] != "\n"){
			$cname[$tot] = $entry[0];
			$save[$tot]  = $line;
			$tot++;
		}
    	}
    	fclose($file);

	$chk = 0;
	$loc = 0;
	for($j = 1; $j <= $tot; $j++){
		if($name == $cname[$j]){
			$chk += 1;
			$loc  = $j;
		}
	}

/* here is the case, we need to do a partial upate  */

	if($chk > 0){
		$test = explode("<>", $save[$loc]);
		if(
			   ( ($office != $test[1]) && (!empty($office)) )
			|| ( ($cell   != $test[2]) && (!empty($cell)) )
		 	|| ( ($home   != $test[3]) && (!empty($home)) )
			|| ( ($mail   != $test[4]) && (!empty($mail)) )
		){
			if($office == ''){
				$office = $test[1];
			}
			if($cell   == ''){
				$cell   = $test[2];
			}
			if($home   == ''){
				$home   = $test[3];
			}
			if($mail   == ''){
				$mail   = $test[4];
			}

			$chk = 0;

/* remove the entry from the database  */

    			$file=fopen("./too_contact_info/personal_list","r");
   			$atot = 1;
    			while (!feof($file))
    			{
				$line = fgets($file);
				$entry = explode("<>", $line);
				if($name != $entry[0] && (!empty($entry[0])) &&  $entry[0] != "\n"){
					$cname[$atot] = $entry[0];
					$tsave[$atot]  = $line;
					$atot++;
				}
    			}
    			fclose($file);
		
/* add back the updated information to the database 	*/

			$file=fopen("./too_contact_info/personal_list","w");
			for ($i=1; $i<= $atot; $i++)
  			{
				$line = "$tsave[$i]";
				fwrite($file, $line);
  			}
			fclose($file);
		}
	}

/* here is totally new PC information update case	*/

	if($chk == 0){
		$file=fopen("./too_contact_info/personal_list","a") or exit("Unable to open file!");

		$input = "$name<>";
		fwrite($file, $input);
	
		$input = "$office<>";
		fwrite($file, $input);
	
		$input = "$cell<>";
		fwrite($file, $input);
	
		$input = "$home<>";
		fwrite($file, $input);
	
		$input = "$mail\n";
		fwrite($file, $input);
	
		fclose($file);
	}
    }
?>

<hr />

<h2>Current Contact Information</h2>

<table border=1 cellpadding=3 cellspacing=3>

<tr>
<th>Contact</th>
<th>Office Phone</th>
<th>Cell Phone</th>
<th>Home Phone</th>
<th>Email</th>
</tr>

<tr>
<?php
$file=fopen("./too_contact_info/personal_list","r");
while (!feof($file))
{
	$line  = fgets($file);
	$entry = explode("<>", $line);
	echo '<tr>';
	if($entry[0] != ''){
		if($entry[0] == $name){
			echo '<td style="background-color:lime;text-align:center">' .$entry[0]. '</td>';
			echo '<td style="background-color:lime;text-align:center">' .$entry[1]. '</td>';
			echo '<td style="background-color:lime">' .$entry[2]. '</td>';
			echo '<td style="background-color:lime">' .$entry[3]. '</td>';
			echo '<td style="background-color:lime">' .$entry[4]. '</td>';
		}
		else
		{
			echo '<td style="text-align:center" >' .$entry[0]. '</td>';
			echo '<td style="text-align:center" >' .$entry[1]. '</td>';
			echo '<td>' .$entry[2]. '</td>';
			echo '<td>' .$entry[3]. '</td>';
			echo '<td>' .$entry[4]. '</td>';
		}
	}
	echo '</tr>';
}
fclose($file);
?>
</table>

<br />
<a href='https://icxc.harvard.edu/mta/CUS/Usint/too_contact_schedule.html'>
<strong><em style='background-color:red;color:yellow;'>Back to USINT TOO Point of Contact</em></strong></a>
<br />

<hr />

<br />
<em style='font-size:90%'>
If you have any questions about this page, please contact: 
<a href='mailto:swolk@head.cfa.harvard.edu'>swolk@head.cfa.harvard.edu</a>.
</em>
<br /><br />
<div style='text-align:right'>
<em style='font-size:85%;'>
<strong>
This PHP Form Was Last Modified on Nov 25, 2009
</strong>
</em>
</div>

</body>
</html>
