function filterDirectories() {
    var input = document.getElementById("search");
    var filter = input.value.toLowerCase();
    var directoryList = document.getElementById("directory-list");
    var directoryItems = directoryList.getElementsByClassName("directory-item");
    
    for (var i = 0; i < directoryItems.length; i++) {
      var directoryName = directoryItems[i].getElementsByTagName("p")[0];
      
      if (directoryName.innerText.toLowerCase().indexOf(filter) > -1) {
        directoryItems[i].style.display = "";
      } else {
        directoryItems[i].style.display = "none";
      }
    }
  }
  
  document.getElementById("search").addEventListener("keyup", filterDirectories);