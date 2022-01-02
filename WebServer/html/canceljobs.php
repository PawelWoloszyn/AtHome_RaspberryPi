<?php
  include "config.php";
  $querry="UPDATE relayjobs_new set canceled=NOW() WHERE executed IS NULL AND canceled IS NULL";
  $result = mysqli_query($con,$querry);
 ?>
