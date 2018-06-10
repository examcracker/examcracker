
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

$.fn.nextElementInDom = function(selector, options) {
      var defaults = { stopAt : 'body' };
      options = $.extend(defaults, options);

      var parent = $(this).parent();
      var found = parent.find(selector);

      switch(true){
          case (found.length > 0):
              return found;
          case (parent.length === 0 || parent.is(options.stopAt)):
              return $([]);
          default:
              return parent.nextElementInDom(selector);
      }
  };

$("select[name=courseExam]").change(
    function() {
		var val = $(this).find("option:selected").val();
    //var x = document.getElementById("cSubject");
    var x = $(this).nextElementInDom("[name=courseSubject]")[0];
		var set = 0;
		//if (!$("select[id=cSubject]").attr("readonly")) {
    if (!$(x).attr("readonly")) {
		  for(i=0;i<x.options.length;i++)
		  {
			  var optionVal = x.options[i].value.split(":")[0];
			  if (optionVal != val) {
				  x.options[i].hidden=true;
			  }
			  else {
				  x.options[i].hidden=false;
				  set = i;
			  }
		  }
  }
  //$("select[id=cSubject]").val(x.options[set].value);
});
