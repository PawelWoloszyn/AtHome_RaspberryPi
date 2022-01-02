<?php

include "config.php";

$return_arr = array();

$query = "SELECT evtDate, outdoorTmp, ovenTmp FROM temperatures ORDER BY ID DESC LIMIT 10000";

$result = mysqli_query($con,$query);

while($row = mysqli_fetch_array($result)){
    $evtdate = $row['evtDate'];
    $outdoorTmp = $row['outdoorTmp'];
    $ovenTmp = $row['ovenTmp'];

    $return_arr[] = array("evtDate" => $evtdate,
                    "outdoorTmp" => $outdoorTmp,
                    "ovenTmp" => $ovenTmp);
}

// Encoding array in JSON format
echo json_encode($return_arr);
?>
