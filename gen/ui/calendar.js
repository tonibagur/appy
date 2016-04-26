// Sends an Ajax request for getting the calendar, at p_month
function askMonth(hookId, month) {askAjax(hookId, null, {'month': month})}

function enableOptions(select, enabled, selectFirst, message){
  /* This function disables, in p_select, all options that are not in p_enabled.
     p_enabled is a string containing a comma-separated list of option names.
     If p_selectFirst is True, the first option from p_enabled will be selected
     by default. p_message will be shown (as "title") for disabled options. */
  // Get p_enabled as a dict
  var l = enabled.split(',');
  var d = {};
  for (var i=0; i < l.length; i++) d[l[i]] = true;
  // Remember if we have already selected the first enabled option
  var isSelected = false;
  var options = select.options;
  // Disable options not being p_enabled
  for (var i=0; i<options.length; i++) {
    options[i].selected = false;
    if (!options[i].value) continue;
    if (options[i].value in d) {
      options[i].disabled = false;
      options[i].title = '';
      // Select it?
      if (selectFirst && !isSelected) {
        options[i].selected = true;
        isSelected = true;
      }
    }
    else {
      options[i].disabled = true;
      options[i].title = message;
    }
  }
}

function openEventPopup(hookId, action, day, timeslot, spansDays,
                        applicableEventTypes, message, freeSlots) {
  /* Opens the popup for creating (or deleting, depending on p_action) a
     calendar event at some p_day. When action is "del", we need to know the
     p_timeslot where the event is assigned and if the event spans more days
     (from p_spansDays), in order to propose a checkbox allowing to delete
     events for those successive days. When action is "new", a possibly
     restricted list of applicable event types for this day is given in
     p_applicableEventTypes; p_message contains an optional message explaining
     why not applicable types are not applicable. When "new", p_freeSlots may
     list the available timeslots at p_day. */
  var popupId = hookId + '_' + action;
  var f = document.getElementById(popupId + 'Form');
  f.day.value = day;
  if (action == 'del') {
    if (f.timeslot) f.timeslot.value = timeslot;
    // Show or hide the checkbox for deleting the event for successive days
    var elem = document.getElementById(hookId + '_DelNextEvent');
    var cb = elem.getElementsByTagName('input');
    cb[0].checked = false;
    cb[1].value = 'False';
    if (spansDays == 'True') elem.style.display = 'block';
    else elem.style.display = 'none';
  }
  else if (action == 'new') {
    // Reinitialise field backgrounds
    f.eventType.style.background = '';
    if (f.eventSpan) f.eventSpan.style.background = '';
    // Disable unapplicable events and non-free timeslots
    enableOptions(f.eventType, applicableEventTypes, false, message);
    if (f.timeslot) enableOptions(f.timeslot, freeSlots, true, 'Not free');
  }
  openPopup(popupId);
}

function triggerCalendarEvent(hookId, action, maxEventLength) {
  /* Sends an Ajax request for triggering a calendar event (create or delete an
     event) and refreshing the view month. */
  var popupId = hookId + '_' + action;
  var formId = popupId + 'Form';
  var f = document.getElementById(formId);
  if (action == 'new') {
    // Check that an event span has been specified
    if (f.eventType.selectedIndex == 0) {
      f.eventType.style.background = wrongTextInput;
      return;
    }
    if (f.eventSpan) {
      // Check that eventSpan is empty or contains a valid number
      var spanNumber = f.eventSpan.value.replace(' ', '');
      if (spanNumber) {
        spanNumber = parseInt(spanNumber);
        if (isNaN(spanNumber) || (spanNumber > maxEventLength)) {
          f.eventSpan.style.background = wrongTextInput;
          return;
        }
      }
    }
  }
  closePopup(popupId);
  askAjax(hookId, formId);
}

// Function that collects the status of all validation checkboxes
function getValidationStatus(hookId) {
  var res = {'validated': [], 'discarded': []};
  var node = document.getElementById(hookId + '_cal');
  var cbs = node.getElementsByTagName('input');
  var key = null;
  for (var i=0; i<cbs.length; i++) {
    if (cbs[i].type != 'checkbox') continue;
    key = (cbs[i].checked)? 'validated': 'discarded';
    res[key].push(cbs[i].id);
  }
  // Convert lists to comma-separated strings
  for (key in res) res[key] = res[key].join();
  return res;
}

// Function for validating and discarding calendar events
function validateEvents(hookId, month) {
  // Collect checkboxes from hookId and identify checked and unchecked ones
  var params = {'action': 'validateEvents', 'mode': 'POST', 'month': month};
  var status = getValidationStatus(hookId);
  for (var key in status) params[key] = status[key];
  askAjax(hookId, null, params);
}

// Function for (un)-checking checkboxes automatically
function onCheckCbCell(cb, hook, totalRows, totalCols) {
  // Is automatic selection on/off?
  var auto = document.getElementById(hook + '_auto');
  if (auto.checked) {
    // Get the current render mode
    var render = document.getElementById(hook)['ajax'].params['render'];
    // Change the state of every successive checkbox
    var timeline = render == 'timeline'; // Else, render is "month"
    // From the checkbox id, extract the date and the remaining part
    var elems = cb.id.split('_');
    if (timeline) {
           var date = elems[2], part = elems[0] + '_' + elems[1] + '_'; }
    else { var date = elems[0], part = '_' + elems[1] + '_' + elems[2]; }
    // Create a Date instance
    var year = parseInt(date.slice(0,4)), month = parseInt(date.slice(4,6))-1,
        day = parseInt(date.slice(6,8));
    var next = new Date(year, month, day);
    // Change the status of successive checkboxes if found
    var checked = cb.checked;
    var nextId = nextCb = null;
    while (true) {
      // Compute the date at the next day
      next.setDate(next.getDate() + 1);
      month = (next.getMonth() + 1).toString();
      if (month.length == 1) month = '0' + month;
      day = next.getDate().toString();
      if (day.length == 1) day = '0' + day;
      date = next.getFullYear().toString() + month + day;
      // Find the next checkbox
      if (timeline) nextId = part + date;
      else          nextId = date + part;
      nextCb = document.getElementById(nextId);
      if (!nextCb) break;
      nextCb.checked = checked;
    }
  }
  // Refresh the total rows if requested
  if (totalRows || totalCols) {
    var params = getValidationStatus(hook);
    params['mode'] = 'POST';
    if (totalRows) {
      params['totalType'] = 'rows';
      askAjax(hook + '_trs', null, params, 'loadingPod');
    }
    if (totalCols) {
      params['totalType'] = 'cols';
      askAjax(hook + '_tcs', null, params, 'loadingPod');
    }
  }
}
 // Switches a layer on/off within a calendar
function switchCalendarLayer(hookId, checkbox) {
  /* Update the ajax data about active layers from p_checkbox, that represents
     the status of some layer */
  var layer = checkbox.id.split('_').pop();
  var d = getNode(hookId)['ajax'];
  var activeLayers = d.params['activeLayers'];
  if (checkbox.checked) {
    // Add the layer to active layers
    activeLayers = (!activeLayers)? layer: activeLayers + ',' + layer;
  }
  else {
    // Remove the layer from active layers
    var res = [];
    var splitted = activeLayers.split(',');
    for (var i=0; i<splitted.length; i++) {
      if (splitted[i] != layer) res.push(splitted[i]);
    }
    activeLayers = res.join();
  }
  askAjax(hookId, null, {'activeLayers': activeLayers});
}

function blinkTd(td, tdId, selectDict, unblinkOnly) {
  // Must the cell be selected or deselected?
  if (td.className && (td.className.indexOf('blinkBg') > -1)) {
    // Stop blinking
    td.className = (td.className == 'blinkBg')? '': td.className.substring(8);
    // Remove entry in the select dict
    if (selectDict) delete selectDict[tdId];
  }
  else if (!unblinkOnly) {
    // Blink
    td.className = (td.className)? 'blinkBg ' + td.className: 'blinkBg';
    // Add entry in the select dict
    if (selectDict) selectDict[tdId] = true;
  }
}

// Called when the user selects a cell in a timeline
function onCell(td, date) {
  // Get the cell ID
  var tr = td.parentNode;
  var cellId = tr.id + '_' + date;
  // Get the data structure where to store selected cells
  var table = tr.parentNode.parentNode;
  var selectDict = table['selected'];
  if (!selectDict) {
    selectDict = {};
    table['selected'] = selectDict;
  }
  // (Un)select the cell
  blinkTd(td, cellId, selectDict, false);
}

// Executes a calendar action
function calendarAction(hookId, actionName, comment) {
  // Get the calendar table: we have stored select cells on it
  var table = document.getElementById(hookId + '_cal');
  var selectDict = table['selected'];
  var selected = (selectDict)? stringFromDictKeys(selectDict):'';
  var params = {'action': 'onExecuteAction', 'actionName': actionName,
                'selected': selected, 'comment': encodeURIComponent(comment)};
  askAjax(hookId, null, params);
}

// Unselect all cells in a calendar
function calendarUnselect(hookId) {
  // Get the table where selected cells are stored
  var table = document.getElementById(hookId + '_cal');
  var selectDict = table['selected'];
  if (!selectDict) return;
  var elems = null;
  for (var key in selectDict) {
    elems = key.split('_'); // (tr id, date)
    // Get the row containing this cell
    var tr = document.getElementById(elems[0]);
    var cells = tr.getElementsByTagName('td');
    for (var i=0; i<cells.length; i++){
      blinkTd(cells[i], null, null, true);
    }
  }
  delete table['selected']; // Delete the whole selectDict
}
