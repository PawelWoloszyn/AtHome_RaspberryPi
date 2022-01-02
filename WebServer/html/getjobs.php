<?php

include "config.php";

$return_arr = array();

$query = "SELECT powerTreshold,startDatetime,stopDatetime FROM relayjobs_new WHERE executed IS NULL AND canceled IS NULL";

$result = mysqli_query($con,$query);

while($row = mysqli_fetch_array($result)){
    $powerTreshold = $row['powerTreshold'];
    $startDatetime = $row['startDatetime'];
    $stopDatetime = $row['stopDatetime'];
    // $isactive = $row['isactive'];

    $return_arr[] = array("powerTreshold" => $powerTreshold,
                    "startDatetime" => $startDatetime,
                    "stopDatetime" => $stopDatetime);
                    // "isactive" => $isactive);
}

// Encoding array in JSON format
echo json_encode($return_arr);
?>
