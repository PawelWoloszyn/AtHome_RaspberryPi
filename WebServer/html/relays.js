var relayjobs;

window.onload = function() {

    getJobs();
    attachEvents();
    refreshPowerReading();
    setCurrentTime();
    getWorkingTime();
};

function setCurrentTime() {
  var now = new Date();
  var hours = now.getHours();
  var minutes = now.getMinutes();
  hours = (hours < 10 ? "0" : "") + hours;
  minutes = (minutes < 10 ? "0" : "") + minutes;
  document.getElementById("startTime").value = hours + ":" + minutes;
  hoursInt= parseInt(hours);
  hours = hoursInt + 2;
 // console.log(hours + ":" + minutes);
  document.getElementById("stopTime").value = hours + ":" + minutes;
}


function refreshPowerReading(){
  var refreshedElement = document.getElementById("inverterImage");
  window.setInterval(function(){
    refreshedElement.src="http://192.168.1.152/gen.screenshot.bmp?"+ new Date().getTime();
    console.log(refreshedElement.src);
  }, 5000);
}

function sendToMysql(startDateTime, stopDateTime, powerValue){
  console.log("sending data to SQL");
  console.log("Trying to insert from JS: " + startDateTime + " "+ stopDateTime + " " +powerValue)

  if(powerValue == undefined)
    powerValue = -1;
  $.ajax({
      type: "POST",
      url: "jobinsert.php",
      data: {
        startDateTime:startDateTime,
        stopDateTime: stopDateTime,
        powerValue:powerValue
    },
      success: function(data) {
         alert("success");
         getJobs();
      }
  });
};

function getJobs(){
  $(document).ready(function(){
      $.ajax({
          url: 'getjobs.php',
          type: 'get',
          dataType: 'JSON',
          success: function(response){
            console.log(response);
            relayjobs = response;
            buildHtmlTable('#excelDataTable');
          }
      });
  });
}

function getWorkingTime(){
  $(document).ready(function(){
      $.ajax({
          url: 'getworkingtime.php',
          type: 'get',
         dataType: 'text',
          success: function(response){
            console.log("response from getworkingtime.php: "+response);
            document.getElementById("todaysWorkingTime").innerHTML = "Dzisiejszy czas grzania: " + response/60 + "minut";
          }
      });
  });
}

// Builds the HTML Table out of relayjobs.
function buildHtmlTable(selector) {
  //reset Table
  document.getElementById("excelDataTable").innerHTML = '';
  var columns = addAllColumnHeaders(relayjobs, selector);

  for (var i = 0; i < relayjobs.length; i++) {
    var row$ = $('<tr/>');
    for (var colIndex = 0; colIndex < columns.length; colIndex++) {
      var cellValue = relayjobs[i][columns[colIndex]];
      if (cellValue == null) cellValue = "";
      row$.append($('<td/>').html(cellValue));
    }
    $(selector).append(row$);
  }
}

// Adds a header row to the table and returns the set of columns.
// Need to do union of keys from all records as some records may not contain
// all records.
function addAllColumnHeaders(relayjobs, selector) {
  var columnSet = [];
  var headerTr$ = $('<tr/>');

  for (var i = 0; i < relayjobs.length; i++) {
    var rowHash = relayjobs[i];
    for (var key in rowHash) {
      if ($.inArray(key, columnSet) == -1) {
        columnSet.push(key);
        headerTr$.append($('<th/>').html(key));
      }
    }
  }
  $(selector).append(headerTr$);

  return columnSet;
}

function attachEvents(){
  document.getElementById('startDate').valueAsDate = new Date();
  document.getElementById('stopDate').valueAsDate = new Date();

  document.getElementById("powerCheckbox").onclick = function() {
      if (this.checked) {
          // alert("Checkbox was checked.");
          document.getElementById("powerDiv").style.display = "block";
      }
      else {
        document.getElementById("powerDiv").style.display = "none";
          // alert("Checkbox wasn't checked.");
      }
    };

    document.getElementById("sendData").onclick = function() {
      //check if start date was entered
      var startDate = document.getElementById("startDate");
      console.log(startDate.value);
      var startTime = document.getElementById("startTime");
      console.log(startTime.value);
      if(!startTime.value || !startDate.value){
        alert("wprowadź dane w pole \"Start\"");
        return;
      }
      //check if stop date was entered
      var stopDate = document.getElementById("stopDate");
      console.log(stopDate.value);
      var stopTime = document.getElementById("stopTime");
      console.log(stopTime.value);
      if(!stopTime.value || !stopDate.value){
        alert("wprowadź dane w pole \"Stop\"");
        return;
      }

      //check if the time difference is correct
      var startDateTime = new Date(startDate.value + " " + startTime.value);
      var stopDateTime = new Date(stopDate.value + " " + stopTime.value);
      var timeDifference = stopDateTime.getTime() - startDateTime.getTime();
      //SPRAWDZ CZY START DATE NIE JEST PRZED OBECNA DATA
      if(stopDateTime < startDateTime){
        alert("stop < start");
        return;
      }
      console.log("time difference in ms is: " + timeDifference);
      //var currentDate = new Date();
      //chceck if the production level was set
      var cb = document.getElementById("powerCheckbox");
      if(cb.checked){
        var powerValue = document.getElementById("powerValue");
        if(powerValue.value <= 0){
          alert("Wprowadź wartość energii");
          return;
        }else{
          sendToMysql(startDateTime.getTime(),stopDateTime.getTime(),powerValue.value);
        }
      }else{
        sendToMysql(startDateTime.getTime(),stopDateTime.getTime(),null);
      }
    };

    //DELETE ALL BUTTON
    var deleteBtn = document.getElementById("deleteAll");
    deleteBtn.onclick = function(){
    if (window.confirm("Na pewno?")) {
      cancelJobs();
      }
    }
}


function cancelJobs(){
  $.ajax({
      type: "POST",
      url: "canceljobs.php",
      success: function(data) {
         alert("success");
         getJobs();
      }
  });
}
