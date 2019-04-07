
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

function filterFunction(filterType,elemId) {
  // Declare variables 
  var input, filter, table, tr, td, i;
  input = document.getElementById(filterType);
  cellIndex = input.parentNode.cellIndex;
  filter = input.value.toUpperCase();
  table = document.getElementById(elemId);
  tr = table.getElementsByTagName("tr");
  var filterIndex = cellIndex-1;
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
function setSelectedValue(object, value) {
  for (var i = 0; i < object.options.length; i++) {
      if (object.options[i].text === value) {
          object.options[i].selected = true;
          //object.onchange();
          return object.options[i].value;
      }
  }
}
function editSchedule(e) {
  var eButton = e;
  var eTd = e.parentNode.parentNode;
  var Cells = eTd.getElementsByTagName("td");
  var scheduleModal = document.getElementById("scheduleModal");

  var coursename = scheduleModal.querySelectorAll('select[id="courseName"]')[0];
  coursename.disabled = true;
  setSelectedValue(coursename,Cells[0].innerText)
  
  var courseSubjectName = scheduleModal.querySelectorAll('select[id="courseSubjectName"]')[0];
  courseSubjectName.disabled = true;
  setSelectedValue(courseSubjectName,Cells[1].innerText)

  var courseChapterName = scheduleModal.querySelectorAll('select[id="courseChapterName"]')[0];
  courseChapterName.disabled = true;
  nameSubId = setSelectedValue(courseChapterName,Cells[2].innerText);
  chapterid = nameSubId.split(':')[2];
  var idHiddenElement = scheduleModal.querySelectorAll('input[id="scheduleChapterId"]')[0];
  idHiddenElement.value = chapterid;

  var startDate = scheduleModal.querySelectorAll('input[id="startDate"]')[0];
  startDate.value = Cells[3].innerText;
 
  var eventDuration = scheduleModal.querySelectorAll('input[id="eventDuration"]')[0];
  eventDuration.value = Cells[5].innerText

  var eventTime = scheduleModal.querySelectorAll('input[id="eventTime"]')[0];
  eventTime.value = Cells[4].innerText

  var eventCount = scheduleModal.querySelectorAll('input[id="eventCount"]')[0];
  eventCount.value = Cells[6].innerText;

  var autoPublish = scheduleModal.querySelectorAll('input[id="autoPublish"]')[0];
  autoPublish.checked = Cells[8].innerText == "True"?1:0;
  
  $('#scheduleModal').modal('toggle');
}
$('#scheduleModal').on('hidden.bs.modal', function (e) {
  var coursename = this.querySelectorAll('select[id="courseName"]')[0];
  coursename.disabled = false;
  var courseSubjectName = this.querySelectorAll('select[id="courseSubjectName"]')[0];
  courseSubjectName.disabled = false;
  var courseChapterName = this.querySelectorAll('select[id="courseChapterName"]')[0];
  courseChapterName.disabled = false;
  // do something...
})

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

