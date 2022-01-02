window.onload = function() {
  var refreshedElement = document.getElementById("inverterImage");
  window.setInterval(function(){
    refreshedElement.src="http://192.168.1.152/gen.screenshot.bmp?"+ new Date().getTime();
    console.log(refreshedElement.src);
  }, 5000);
};
