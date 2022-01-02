<?php

include "config.php";

$query = "SELECT SUM(workingTime) AS todaysWorkingTime from relayjobs_new where date(startDatetime) = CURDATE();";

$result = mysqli_query($con,$query);

while($row = mysqli_fetch_array($result)){
    $todaysWorkingTime = $row['todaysWorkingTime'];

    $return_result = $todaysWorkingTime;
                    // "isactive" => $isactive);
}
if (is_null($return_result)) { 
    echo 0;
 }else{
    echo  $return_result;
 }
// Encoding array in JSON format

?>
