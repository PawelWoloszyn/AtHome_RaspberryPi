<?php
    // ini_set("display_errors",1);
    // error_reporting(E_ALL);
    include "config.php";

    //Create variables
    $startDateTime = $_POST['startDateTime'];
    $stopDateTime = $_POST['stopDateTime'];
    $powerValue = $_POST['powerValue'];

    $insertQuery = "INSERT INTO relayjobs_new (addDate, powerTreshold, startDatetime, stopDatetime) VALUES(NOW(), '$powerValue', FROM_UNIXTIME('$startDateTime'/ 1000),FROM_UNIXTIME('$stopDateTime'/ 1000))";
    mysqli_query($con,$insertQuery);

?>
