
var droptarget;
function drag(event)
  {
    droptarget = event.target.id;
  }
  function allowDrop(event)
  {
    event.preventDefault();
  }
  function drop(event) {
    event.preventDefault();  
    var drop_target = event.currentTarget;
    var drag_target_id = droptarget;
    var drag_target = document.getElementById(drag_target_id);
    swapNodes(drop_target,drag_target);
}
function swapNodes(a, b) {
    var aparent= a.parentNode;
    var asibling= a.nextSibling===b? a : a.nextSibling;
    b.parentNode.insertBefore(a, b);
    aparent.insertBefore(b, asibling);
}

function filterFunction(filterType) {
  // Declare variables 
  var input, filter, table, tr, td, i;
  input = document.getElementById(filterType);
  filter = input.value.toUpperCase();
  table = document.getElementById("schedulesTable");
  tr = table.getElementsByTagName("tr");
  var filterIndex = 0;
  if (filterType == "filterSubject") {
    filterIndex = 1;
  }  else if (filterType == "filterChapter") {
    filterIndex = 2;
  }
  // Loop through all table rows, and hide those who don't match the search query
  for (i = 2; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[filterIndex];
    if (td) {
      if (td.innerHTML.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    } 
  }
}

function fillSelectByName (me,target,targetNext) {
  var val = $(me).find("option:selected").val();
  //var x = document.getElementById("cSubject");
  var x = document.getElementById(target);
  var set = 0;
  if (!$(x).attr("readonly")) {
    for(i=0;i<x.options.length;i++)
    {
      var larray = x.options[i].value.split(":")
      var optionVal;
      if (larray.length > 2) {
        optionVal  = larray.slice(0,larray.length - 1).join(":");
      }  else{
        optionVal = larray[0];
      }
      if (optionVal != val) {
        x.options[0].selected = false;
        x.options[i].hidden=true;
      }
      else {
        x.options[i].hidden=false;
        set = i;
      }
    }
}

  var isMultiple = x.multiple;
  if (!isMultiple) {
    x.options[set].selected = true;
  }

  if (targetNext != undefined) {
    fillSelectByName(x,targetNext);
  }
}

