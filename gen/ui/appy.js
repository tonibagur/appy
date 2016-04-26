var wrongTextInput = '#F9EDBE none';
var loadingLink = '<img src="ui/loading.gif"/>';
var loadingButton = '<img align="center" src="ui/loadingBtn.gif"/>';
var loadingZone = '<div align="center"><img src="ui/?.gif"/></div>';
var lsTimeout; // Timout for the live search
var podTimeout; // Timeout for checking status of pod downloads

// Functions related to user authentication
function cookiesAreEnabled() {
  /* Test whether cookies are enabled by attempting to set a cookie and then
     change its value. */
  var c = "areYourCookiesEnabled=0";
  document.cookie = c;
  var dc = document.cookie;
  // Cookie not set? Fail.
  if (dc.indexOf(c) == -1) return 0;
  // Change test cookie
  c = "areYourCookiesEnabled=1";
  document.cookie = c;
  dc = document.cookie;
  // Cookie not changed? Fail.
  if (dc.indexOf(c) == -1) return 0;
  // Delete cookie
  document.cookie = "areYourCookiesEnabled=; expires=Thu, 01-Jan-70 00:00:01 GMT";
  return 1;
}

function setLoginVars() {
  // Indicate if JS is enabled
  document.getElementById('js_enabled').value = 1;
  // Indicate if cookies are enabled
  document.getElementById('cookies_enabled').value = cookiesAreEnabled();
  /* Copy login and password length to alternative vars since current vars will
     be removed from the request by zope's authentication mechanism. */
  var v = document.getElementById('__ac_name').value;
  document.getElementById('login_name').value = v;
  password = document.getElementById('__ac_password');
  emptyPassword = document.getElementById('pwd_empty');
  if (password.value.length==0) emptyPassword.value = '1';
  else emptyPassword.value = '0';
}

function showLoginForm() {
  // Hide the login link
  var loginLink = document.getElementById('loginLink');
  loginLink.style.display = "none";
  // Displays the login form
  var loginFields = document.getElementById('loginFields');
  loginFields.style.display = "inline";
}

function goto(url) { window.location = url }
function len(dict) {
  var res = 0;
  for (var key in dict) res += 1;
  return res;
}

function switchLanguage(select, siteUrl) {
  var language = select.options[select.selectedIndex].value;
  goto(siteUrl + '/config/changeLanguage?language=' + language);
}

function switchResultMode(select, hook) {
  var mode = select.options[select.selectedIndex].value;
  askAjax(hook, null, {'resultMode': mode});
}

var isIe = (navigator.appName == "Microsoft Internet Explorer");

function getElementsHavingName(tag, name) {
  if (!isIe) return document.getElementsByName(name);
  var elems = document.getElementsByTagName(tag);
  var res = new Array();
  for (var i=0; i<elems.length; i++) {
    var nameAttr = elems[i].attributes['name'];
    if (nameAttr && (nameAttr.value == name)) res.push(elems[i]);
  }
  return res;
}

// AJAX machinery
var xhrObjects = new Array(); // An array of XMLHttpRequest objects
function XhrObject() { // Wraps a XmlHttpRequest object
  this.freed = 1; // Is this xhr object already dealing with a request or not?
  this.xhr = false;
  if (window.XMLHttpRequest) this.xhr = new XMLHttpRequest();
  else this.xhr = new ActiveXObject("Microsoft.XMLHTTP");
  this.hook = '';  /* The ID of the HTML element in the page that will be
                      replaced by result of executing the Ajax request. */
  this.onGet = ''; /* The name of a Javascript function to call once we
                      receive the result. */
  this.info = {};  /* An associative array for putting anything else */
}

/* When inserting HTML at some DOM node in a page via Ajax, scripts defined in
   this chunk of HTML are not executed. This function, typically used as "onGet"
   param for the askAjaxChunk function below, will evaluate those scripts. */
function evalInnerScripts(xhrObject, hookElem) {
  var scripts = hookElem.getElementsByTagName('script');
  for (var i=0; i<scripts.length; i++) { eval(scripts[i].innerHTML) }
}

function injectChunk(elem, content, inner, searchTop){
  var res = elem;
  if (!isIe || (elem.tagName != 'TABLE')) {
    if (inner) res.innerHTML = content;
    else {
      // Replace p_elem with a new node filled with p_content and return it
      var id = elem.id;
      if (id && searchTop) id = ':' + id;
      elem.outerHTML = content;
      if (id) res = getNode(id); // Get the new element
    }
  }
  else {
    /* IE doesn't want to replace content of a table. Force it to do so via
       a temporary DOM element. */
    var temp = document.createElement('div');
    temp.innerHTML = content;
    temp.firstChild.id = elem.id;
    elem.parentNode.replaceChild(temp.firstChild, elem);
  }
  return res;
}

function getNode(id, forceTop) {
  /* Gets the DOM node whose ID is p_id. If p_id starts with ':', we search
     the node in the top browser window, not in the current one that can be
     an iframe. If p_forceTop is true, even if p_id does not start with ':',
     if the node is not found, we will search in the top browser window. */
  if (!id) return;
  var container = window.document;
  var startIndex = 0;
  if (id[0] == ':') {
    container = window.top.document;
    startIndex = 1;
  }
  var nodeId = id.slice(startIndex);
  var res = container.getElementById(nodeId);
  if (!res && forceTop) res = window.top.document.getElementById(nodeId);
  return res;
}

function getAjaxChunk(pos) {
  // This function is the callback called by the AJAX machinery (see function
  // askAjaxChunk below) when an Ajax response is available.
  // First, find back the correct XMLHttpRequest object
  var rq = xhrObjects[pos];
  if ( (typeof(rq) != 'undefined') && (rq.freed == 0)) {
    if ((!rq.hook) || (rq.xhr.readyState != 4)) return;
    // We have received the HTML chunk
    var hookElem = getNode(rq.hook);
    if (hookElem) {
      var content = rq.xhr.responseText;
      var searchTop = rq.hook[0] == ':';
      var injected = injectChunk(hookElem, content, false, searchTop);
      // Call a custom Javascript function if required
      if (rq.onGet) rq.onGet(rq, injected);
      // Refresh the whole page if requested
      var goto = rq.xhr.getResponseHeader('Appy-Redirect');
      if (goto) window.top.location = goto;
      // Display the Appy message if present
      var msg = rq.xhr.getResponseHeader('Appy-Message');
      if (msg) showAppyMessage(decodeURIComponent(escape(msg)));
    }
    rq.freed = 1;
  }
}

// Displays the waiting icon when an ajax chunk is asked
function showPreloader(hook, waiting) {
  /* p_hook may be null if the ajax result would be the same as what is
     currently shown, as when inline-editing a rich text field). */
  if (!hook || (waiting == 'none')) return;
  // What waiting icon to show?
  if (!waiting) waiting = 'loadingBig';
  injectChunk(getNode(hook), loadingZone.replace('?', waiting), true);
}

function askAjaxChunk(hook, mode, url, px, params, beforeSend, onGet, waiting) {
  /* This function will ask to get a chunk of XHTML on the server through a
     XMLHttpRequest. p_mode can be 'GET' or 'POST'. p_url is the URL of a
     given server object. On this object we will call method "ajax" that will
     call a specific p_px with some additional p_params (must be an associative
     array) if required. If p_px is of the form <field name>:<px name>, the PX
     will be found on the field named <field name> instead of being found
     directly on the object at p_url.

     p_hook is the ID of the XHTML element that will be filled with the XHTML
     result from the server. If it starts with ':', we will find the element in
     the top browser window and not in the current one (that can be an iframe).

     p_beforeSend is a Javascript function to call before sending the request.
     This function will get 2 args: the XMLHttpRequest object and the p_params.
     This method can return, in a string, additional parameters to send, ie:
     "&param1=blabla&param2=blabla".

     p_onGet is a Javascript function to call when we will receive the answer.
     This function will get 2 args, too: the XMLHttpRequest object and the
     HTML node element into which the result has been inserted.

     p_waiting is the name of the animated icon that will be shown while waiting
     for the ajax result. If null, it will be loadingBig.gif. Other values can
     be "loading", "loadingBtn" or "loadingPod" (the .gif must be omitted).
     If "none", there will be no icon at all.
  */
  // First, get a non-busy XMLHttpRequest object.
  var pos = -1;
  for (var i=0; i < xhrObjects.length; i++) {
    if (xhrObjects[i].freed == 1) { pos = i; break; }
  }
  if (pos == -1) {
    pos = xhrObjects.length;
    xhrObjects[pos] = new XhrObject();
  }
  xhrObjects[pos].hook = hook;
  xhrObjects[pos].onGet = onGet;
  if (xhrObjects[pos].xhr) {
    var rq = xhrObjects[pos];
    rq.freed = 0;
    // Construct parameters
    var paramsFull = 'px=' + px;
    if (params) {
      for (var paramName in params)
        paramsFull = paramsFull + '&' + paramName + '=' + params[paramName];
    }
    // Call beforeSend if required
    if (beforeSend) {
       var res = beforeSend(rq, params);
       if (res) paramsFull = paramsFull + res;
    }
    // Construct the URL to call
    var urlFull = url + '/ajax';
    if (mode == 'GET') {
      urlFull = urlFull + '?' + paramsFull;
    }
    showPreloader(rq.hook, waiting); // Display the pre-loader
    // Perform the asynchronous HTTP GET or POST
    rq.xhr.open(mode, urlFull, true);
    if (mode == 'POST') {
      // Set the correct HTTP headers
      rq.xhr.setRequestHeader(
        "Content-Type", "application/x-www-form-urlencoded");
      // rq.xhr.setRequestHeader("Content-length", paramsFull.length);
      // rq.xhr.setRequestHeader("Connection", "close");
      rq.xhr.onreadystatechange = function(){ getAjaxChunk(pos); }
      rq.xhr.send(paramsFull);
    }
    else if (mode == 'GET') {
      rq.xhr.onreadystatechange = function() { getAjaxChunk(pos); }
      if (window.XMLHttpRequest) { rq.xhr.send(null); }
      else if (window.ActiveXObject) { rq.xhr.send(); }
    }
  }
}

// Object representing all the data required to perform an Ajax request
function AjaxData(hook, px, params, parentHook, url, mode, beforeSend, onGet) {
  this.hook = hook;
  this.mode = mode;
  if (!mode) this.mode = 'GET';
  this.url = url;
  this.px = px;
  this.params = params;
  this.beforeSend = beforeSend;
  this.onGet = onGet;
  /* If a parentHook is spefified, this AjaxData must be completed with a parent
     AjaxData instance. */
  this.parentHook = parentHook;
  // Inject this AjaxData instance into p_hook
  getNode(hook, true)['ajax'] = this;
}

function askAjax(hook, form, params, waiting) {
  /* Call askAjaxChunk by getting an AjaxData instance from p_hook, a
      potential action from p_form and additional parameters from p_param. */
  var d = getNode(hook)['ajax'];
  // Complete data with a parent data if present
  if (d['parentHook']) {
    var parentHook = d['parentHook'];
    if (hook[0] == ':') parentHook = ':' + parentHook;
    var parent = getNode(parentHook)['ajax'];
    for (var key in parent) {
      if (key == 'params') continue; // Will get a specific treatment herafter
      if (!d[key]) d[key] = parent[key]; // Override if no value on child
    }
    // Merge parameters
    if (parent.params) {
      for (var key in parent.params) {
        if (key in d.params) continue; // Override if not value on child
        d.params[key] = parent.params[key];
      }
    }
  }
  // Resolve dynamic parameter "cbChecked" if present
  if ('cbChecked' in d.params) {
    var cb = getNode(d.params['cbChecked'], true);
    if (cb) d.params['cbChecked'] = cb.checked;
    else delete d.params['cbChecked'];
  }
  // If a p_form id is given, integrate the form submission in the ajax request
  if (form) {
    var f = document.getElementById(form);
    var mode = 'POST';
    // Deduce the action from the form action
    if (f.action != 'none') d.params['action'] = _rsplit(f.action, '/', 2)[1];
    // Get the other params
    var elems = f.elements;
    for (var i=0; i < elems.length; i++) {
      var value = elems[i].value;
      if (elems[i].name == 'popupComment') value = encodeURIComponent(value);
      d.params[elems[i].name] = value;
    }
  }
  else var mode = d.mode;
  // Get p_params if given. Note that they override anything else.
  var px = d.px;
  if (params) {
    if ('mode' in params) { mode = params['mode']; delete params['mode'] };
    if ('px' in params) { px = params['px']; delete params['px'] };
    for (var key in params) d.params[key] = params[key];
  }
  askAjaxChunk(hook, mode, d.url, px, d.params, d.beforeSend, evalInnerScripts,
               waiting);
}

function askBunch(hookId, startNumber, maxPerPage) {
  var params = {'startNumber': startNumber};
  if (maxPerPage) params['maxPerPage'] = maxPerPage;
  askAjax(hookId, null, params);
}

function askBunchSorted(hookId, sortKey, sortOrder) {
  var data = {'startNumber': '0', 'sortKey': sortKey, 'sortOrder': sortOrder};
  askAjax(hookId, null, data);
}

function askBunchFiltered(hookId, filterKey) {
  var filter = document.getElementById(hookId + '_' + filterKey);
  var value = '';
  if (filter.value) {
    // Ensure 3 chars are at least encoded into this field
    value = encodeURIComponent(filter.value.trim());
    if (value.length < 3) {
      filter.style.background = wrongTextInput;
      return;
    }
  }
  var data = {'startNumber': '0', 'filterKey': filterKey, 'filterValue': value};
  askAjax(hookId, null, data);
}

function askBunchMove(hookId, startNumber, uid, move){
  var moveTo = move;
  if (typeof move == 'object'){
    // Get the new index from an input field
    var id = move.id;
    id = id.substr(0, id.length-4) + '_v';
    var input = document.getElementById(id);
    if (isNaN(input.value)) {
      input.style.background = wrongTextInput;
      return;
    }
    moveTo = 'index_' + input.value;
  }
  var data = {'startNumber': startNumber, 'action': 'doChangeOrder',
              'refObjectUid': uid, 'move': moveTo};
  askAjax(hookId, null, data);
}

function askBunchSortRef(hookId, startNumber, sortKey, reverse) {
  var data = {'startNumber': startNumber, 'action': 'sort', 'sortKey': sortKey,
              'reverse': reverse};
  askAjax(hookId, null, data);
}

function clickOn(node) {
  // If node is a form, disable all form buttons
  if (node.tagName == 'FORM') {
    var i = node.elements.length -1;
    while (i >= 0) {
      if (node.elements[i].type == 'button') { clickOn(node.elements[i]); }
      i = i - 1;
    }
    return;
  }
  // Disable any click on p_node to be protected against double-click
  var cn = (node.className)? 'unclickable ' + node.className : 'unclickable';
  node.className = cn;
  /* For a button, show the preloader directly. For a link, show it only after
     a while, if the target page is still not there. */
  if (node.tagName != 'A') injectChunk(node, loadingButton);
  else setTimeout(function(){injectChunk(node, loadingLink)}, 700);
}

function gotoTied(objectUrl, field, numberWidget, total, popup) {
  // Check that the number is correct
  try {
    var number = parseInt(numberWidget.value);
    if (!isNaN(number)) {
      if ((number >= 1) && (number <= total)) {
        goto(objectUrl + '/gotoTied?field=' + field + '&number=' + number +
             '&popup=' + popup);
      }
      else numberWidget.style.background = wrongTextInput; }
    else numberWidget.style.background = wrongTextInput; }
  catch (err) { numberWidget.style.background = wrongTextInput; }
}

function askField(hookId, objectUrl, layoutType, customParams, showChanges,
                  masterValues, requestValue, error, className){
  // Sends an Ajax request for getting the content of any field
  var fieldName = hookId.split('_').pop();
  // layoutType may define a host layout
  var layouts = layoutType.split(':');
  var params = {'layoutType': layouts[0], 'showChanges': showChanges};
  if (layouts.length > 1) params['hostLayout'] = layouts[1];
  if (customParams){for (var key in customParams) params[key]=customParams[key]}
  if (masterValues) params['masterValues'] = masterValues.join('*');
  if (requestValue) params[fieldName] = requestValue;
  if (error) params[fieldName + '_error'] = error;
  var px = fieldName + ':pxRender';
  if (className) px = className + ':' + px;
  askAjaxChunk(hookId, 'GET', objectUrl, px, params, null, evalInnerScripts);
}

function doInlineSave(id, name, url, layout, ask, content, language){
  /* Ajax-saves p_content of field named p_name (or only on part corresponding
     to p_language if the field is multilingual) on object whose id is
     p_id and whose URL is p_url. After saving it, display the field on
     p_layout. Ask a confirmation before doing it if p_ask is true. */
  var doIt = true;
  if (ask) doIt = confirm(save_confirm);
  var params = {'action': 'storeFromAjax', 'layoutType': layout};
  if (language) params['languageOnly'] = language;
  var hook = id + '_' + name;
  if (!doIt) params['cancel'] = 'True';
  else { params['fieldContent'] = encodeURIComponent(content) }
  askAjaxChunk(hook,'POST',url,name+':pxRender',params,null,evalInnerScripts);
}

function prepareForAjaxSave(id, objectId, objectUrl) {
  // Prepare widget whose ID is p_id for ajax-saving its content
  var tag = getNode(id);
  tag.focus();
  tag.select();
  /* Store information on this node. Key "done" is used to avoid saving twice
     (saving is attached to events keydown and blur, see below). */
  tag.obj = {id: objectId, url: objectUrl, done: false};
  tag.addEventListener('keydown', function(event){
    var tag = event.target;
    if ((event.keyCode != 13) || tag.obj.done) return;
    tag.obj.done = true;
    doInlineSave(tag.obj.id, tag.name, tag.obj.url, 'cell', false, tag.value)});
  tag.addEventListener('blur', function(event){
    var tag = event.target;
    if (tag.obj.done) return;
    tag.obj.done = true;
    doInlineSave(tag.obj.id, tag.name, tag.obj.url, 'cell', false, tag.value)});
}

// Used by checkbox widgets for having radio-button-like behaviour.
function toggleCheckbox(visibleCheckbox, hiddenBoolean) {
  vis = document.getElementById(visibleCheckbox);
  hidden = document.getElementById(hiddenBoolean);
  if (vis.checked) hidden.value = 'True';
  else hidden.value = 'False';
}

// Toggle visibility of all elements having p_nodeType within p_node
function toggleVisibility(node, nodeType){
  var elements = node.getElementsByTagName(nodeType);
  for (var i=0; i<elements.length; i++){
    var sNode = elements[i];
    if (sNode.style.visibility == 'hidden') sNode.style.visibility = 'visible';
    else sNode.style.visibility = 'hidden';
  }
}

// JS implementation of Python ''.rsplit
function _rsplit(s, delimiter, limit) {
  var elems = s.split(delimiter);
  var exc = elems.length - limit;
  if (exc <= 0) return elems;
  // Merge back first elements to get p_limit elements
  var head = '';
  var res = [];
  for (var i=0; i < elems.length; i++) {
    if (exc > 0) { head += elems[i] + delimiter; exc -= 1 }
    else { if (exc == 0) { res.push(head + elems[i]); exc -= 1 }
           else res.push(elems[i]) }
  }
  return res;
}

// (Un)checks a checkbox corresponding to a linked object
function toggleCb(checkbox) {
  var name = checkbox.getAttribute('name');
  var elems = _rsplit(name, '_', 3);
  // Get the DOM node corresponding to the Ref field    
  var node = document.getElementById(elems[0] + '_' + elems[1]);
  // Get the array that stores checkbox statuses
  var statuses = node['_appy_' + elems[2] + '_cbs'];
  // Get the array semantics
  var semantics = node['_appy_' + elems[2] + '_sem'];
  var uid = checkbox.value;
  if (semantics == 'unchecked') {
    if (!checkbox.checked) statuses[uid] = null;
    else {if (uid in statuses) delete statuses[uid]};
  }
  else { // semantics is 'checked'
    if (checkbox.checked) statuses[uid] = null;
    else {if (uid in statuses) delete statuses[uid]};
  }
}

function findNode(node, id) {
  /* When coming back from the iframe popup, we are still in the context of the
     iframe, which can cause problems for finding nodes. We have found that this
     case can be detected by checking node.window. */
  if (node.window) var container = node.window.document;
  else var container = window.parent.document;
  return container.getElementById(id);
}

// Initialise checkboxes of a Ref field or Search
function initCbs(id) {
  var elems = _rsplit(id, '_', 3);
  // Get the DOM node corresponding to the Ref field
  var node = getNode(elems[0] + '_' + elems[1], true);
  // Get the array that stores checkbox statuses
  var statuses = node['_appy_' + elems[2] + '_cbs'];
  // Get the array semantics
  var semantics = node['_appy_' + elems[2] + '_sem'];
  var value = (semantics == 'unchecked')? false: true;
  // Update visible checkboxes
  var checkboxes = getElementsHavingName('input', id);
  for (var i=0; i < checkboxes.length; i++) {
    if (checkboxes[i].value in statuses) checkboxes[i].checked = value;
    else checkboxes[i].checked = !value;
  }
}

// Toggle all checkboxes of a Ref field or Search
function toggleAllCbs(id) {
  var elems = _rsplit(id, '_', 3);
  // Get the DOM node corresponding to the Ref field
  var node = document.getElementById(elems[0] + '_' + elems[1]);
  // Empty the array that stores checkbox statuses
  var statuses = node['_appy_' + elems[2] + '_cbs'];
  for (var key in statuses) delete statuses[key];
  // Switch the array semantics
  var semAttr = '_appy_' + elems[2] + '_sem';
  if (node[semAttr] == 'unchecked') node[semAttr] = 'checked';
  else node[semAttr] = 'unchecked';
  // Update the visible checkboxes
  initCbs(id);
}

// Shows/hides a dropdown menu
function toggleDropdown(dropdownId, forcedValue){
  var dropdown = document.getElementById(dropdownId);
  // Force to p_forcedValue if specified
  if (forcedValue) {dropdown.style.display = forcedValue}
  else {
    var displayValue = dropdown.style.display;
    if (displayValue == 'block') dropdown.style.display = 'none';
    else dropdown.style.display = 'block';
  }
}

// Function that sets a value for showing/hiding sub-titles
function setSubTitles(value, tag) {
  createCookie('showSubTitles', value);
  // Get the sub-titles
  var subTitles = getElementsHavingName(tag, 'subTitle');
  if (subTitles.length == 0) return;
  // Define the display style depending on p_tag
  var displayStyle = 'inline';
  if (tag == 'tr') displayStyle = 'table-row';
  for (var i=0; i < subTitles.length; i++) {
    if (value == 'true') subTitles[i].style.display = displayStyle;
    else subTitles[i].style.display = 'none';
  }
}

// Function that toggles the value for showing/hiding sub-titles
function toggleSubTitles(tag) {
  // Get the current value
  var value = readCookie('showSubTitles');
  if (value == null) value = 'true';
  // Toggle the value
  var newValue = 'true';
  if (value == 'true') newValue = 'false';
  if (!tag) tag = 'div';
  setSubTitles(newValue, tag);
}

// Functions used for master/slave relationships between widgets
function getSlaveInfo(slave, infoType) {
  // Returns the appropriate info about slavery, depending on p_infoType
  var cssClasses = slave.className.split(' ');
  var masterInfo = null;
  // Find the CSS class containing master-related info
  for (var j=0; j < cssClasses.length; j++) {
    if (cssClasses[j].indexOf('slave*') == 0) {
      // Extract, from this CSS class, master name or master values
      masterInfo = cssClasses[j].split('*');
      if (infoType == 'masterName') return masterInfo[1];
      else return masterInfo.slice(2); 
    }
  }
}

function getMasterValues(master) {
  // Returns the list of values that p_master currently has
  var res = null;
  if ((master.tagName == 'INPUT') && (master.type != 'checkbox')) {
    res = master.value;
    if ((res.charAt(0) == '(') || (res.charAt(0) == '[')) {
      // There are multiple values, split it
      values = res.substring(1, res.length-1).split(',');
      res = [];
      var v = null;
      for (var i=0; i < values.length; i++){
        v = values[i].replace(' ', '');
        res.push(v.substring(1, v.length-1));
      }
    }
    else res = [res]; // A single value
  }
  else if (master.type == 'checkbox') {
    res = master.checked + '';
    res = res.charAt(0).toUpperCase() + res.substr(1);
    res = [res];
  }
  else { // SELECT widget
    res = [];
    for (var i=0; i < master.options.length; i++) {
      if (master.options[i].selected) res.push(master.options[i].value);
    }
  }
  return res;
}

function getSlaves(master) {
  // Gets all the slaves of master
  allSlaves = getElementsHavingName('table', 'slave');
  res = [];  
  masterName = master.attributes['name'].value;
  // Remove leading 'w_' if the master is in a search screen
  if (masterName.indexOf('w_') == 0) masterName = masterName.slice(2);
  if (master.type == 'checkbox') {
    masterName = masterName.substr(0, masterName.length-8);
  }
  slavePrefix = 'slave*' + masterName + '*';
  for (var i=0; i < allSlaves.length; i++){
    cssClasses = allSlaves[i].className.split(' ');
    for (var j=0; j < cssClasses.length; j++) {
      if (cssClasses[j].indexOf(slavePrefix) == 0) {
        res.push(allSlaves[i]);
        break;
      }
    }
  }
  return res;
}

function updateSlaves(master, slave, objectUrl, layoutType, requestValues,
                      errors, className){
  /* Given the value(s) in a master field, we must update slave's visibility or
     value(s). If p_slave is given, it updates only this slave. Else, it updates
     all slaves of p_master. */
  var slaves = null;
  if (slave) { slaves = [slave]; }
  else { slaves = getSlaves(master); }
  var masterValues = getMasterValues(master);
  var slaveryValues = null;
  for (var i=0; i < slaves.length; i++) {
    slaveryValues = getSlaveInfo(slaves[i], 'masterValues');
    if (slaveryValues[0] != '+') {
      // Update slaves visibility depending on master values
      var showSlave = false;
      for (var j=0; j < slaveryValues.length; j++) {
        for (var k=0; k< masterValues.length; k++) {
          if (slaveryValues[j] == masterValues[k]) showSlave = true;
        }
      }
      // Is this slave also a master ?
      var subMaster = null;
      if (!slave) {
        var innerId = slaves[i].id.split('_').pop();
        var innerField = document.getElementById(innerId);
        // Inner-field may be absent (ie, in the case of a group)
        if (innerField && (innerField.className == ('master_' + innerId))) {
          subMaster = innerField;
        }
      }
      // Show or hide this slave
      if (showSlave) {
        // Show the slave
        slaves[i].style.display = '';
        if (subMaster) {
          // Recompute its own slave's visibility
          updateSlaves(subMaster, null, objectUrl, layoutType, requestValues,
                       errors, className);
        }
      }
      else {
        // Hide the slave
        slaves[i].style.display = 'none';
        if (subMaster && (subMaster.style.display != 'none')) {
          // Hide its own slaves, too
          var subSlaves = getSlaves(subMaster);
          for (var l=0; l < subSlaves.length; l++) {
            subSlaves[l].style.display = 'none';
          }
        }
      }
    }
    else {
      // Update slaves' values depending on master values
      var slaveId = slaves[i].id;
      var slaveName = slaveId.split('_')[1];
      var reqValue = null;
      if (requestValues && (slaveName in requestValues))
        reqValue = requestValues[slaveName];
      var err = null;
      if (errors && (slaveName in errors))
        err = errors[slaveName];
      askField(slaveId, objectUrl, layoutType, null, false, masterValues,
               reqValue, err, className);
    }
  }
}

function initSlaves(objectUrl, layoutType, requestValues, errors) {
  /* When the current page is loaded, we must set the correct state for all
     slave fields. For those that are updated via Ajax requests, their
     p_requestValues and validation p_errors must be carried to those
     requests. */
  slaves = getElementsHavingName('table', 'slave');
  i = slaves.length -1;
  while (i >= 0) {
    masterName = getSlaveInfo(slaves[i], 'masterName');
    master = document.getElementById(masterName);
    // If master is not here, we can't hide its slaves when appropriate
    if (master) {
      updateSlaves(master,slaves[i],objectUrl,layoutType,requestValues,errors);}
    i -= 1;
  }
}

// Function used to submit the appy form on pxEdit
function submitAppyForm(button) {
  var f = document.getElementById('appyForm');
  // On which button has the user clicked ?
  f.button.value = button.id;
  f.submit(); clickOn(button);
}

function submitForm(formId, msg, showComment, back) {
  var f = document.getElementById(formId);
  if (!msg) {
    /* Submit the form and either refresh the entire page (back is null)
       or ajax-refresh a given part only (p_back corresponds to the id of the
       DOM node to be refreshed. */
    if (back) { askAjax(back, formId); }
    else { f.submit(); clickOn(f) }
  }
  else {
    // Ask a confirmation to the user before proceeding
    if (back) {
      var js = "askAjax('"+back+"', '"+formId+"');";
      askConfirm('form-script', formId+'+'+js, msg, showComment); }
    else askConfirm('form', formId, msg, showComment);
  }
}

// Function used for triggering a workflow transition
function triggerTransition(formId, node, msg, back) {
  var f = document.getElementById(formId);
  f.transition.value = node.id;
  submitForm(formId, msg, true, back);
}

function onDeleteObject(uid, back) {
  var f = document.getElementById('deleteForm');
  f.uid.value = uid;
  submitForm('deleteForm', action_confirm, false, back);
}

function onDeleteEvent(objectUid, eventTime) {
  f = document.getElementById('deleteEventForm');
  f.objectUid.value = objectUid;
  f.eventTime.value = eventTime;
  askConfirm('form', 'deleteEventForm', action_confirm);
}

function onLink(action, sourceUid, fieldName, targetUid) {
  f = document.getElementById('linkForm');
  f.linkAction.value = action;
  f.sourceUid.value = sourceUid;
  f.fieldName.value = fieldName;
  f.targetUid.value = targetUid;
  f.submit();
}

function stringFromDictKeys(d){
  // Gets a string containing comma-separated keys from dict p_d
  var res = [];
  for (var key in d) res.push(key);
  return res.join();
}

function onLinkMany(action, id) {
  var elems = _rsplit(id, '_', 3);
  // Get the DOM node corresponding to the Ref field
  var node = document.getElementById(elems[0] + '_' + elems[1]);
  // Get the uids of (un-)checked objects.
  var statuses = node['_appy_' + elems[2] + '_cbs'];
  var uids = stringFromDictKeys(statuses);
  // Get the array semantics
  var semantics = node['_appy_' + elems[2] + '_sem'];
  // Show an error message if no element is selected
  if ((semantics == 'checked') && (len(statuses) == 0)) {
    openPopup('alertPopup', no_elem_selected);
    return;
  }
  // Fill the form and ask for a confirmation
  f = document.getElementById('linkForm');
  f.linkAction.value = action + '_many';
  f.sourceUid.value = elems[0];
  f.fieldName.value = elems[1];
  f.targetUid.value = uids;
  f.semantics.value = semantics;
  askConfirm('form', 'linkForm', action_confirm);
}

function onUnlockPage(objectUid, pageName) {
  f = document.getElementById('unlockForm');
  f.objectUid.value = objectUid;
  f.pageName.value = pageName;
  askConfirm('form', 'unlockForm', action_confirm);
}

function createCookie(name, value, days) {
  if (days) {
    var date = new Date();
    date.setTime(date.getTime()+(days*24*60*60*1000));
    var expires = "; expires="+date.toGMTString();
  } else expires = "";
  document.cookie = name+"="+escape(value)+expires+"; path=/;";
}

function readCookie(name) {
  var nameEQ = name + "=";
  var ca = document.cookie.split(';');
  for (var i=0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0)==' ') { c = c.substring(1,c.length); }
    if (c.indexOf(nameEQ) == 0) {
      return unescape(c.substring(nameEQ.length,c.length));
    }
  }
  return null;
}

function changeImage(img, name) {
  // Changes p_img.src to new image p_name, keeping the same image path
  var path = img.src.split('/');
  path[path.length-1] = name;
  img.src = path.join('/');
  // Return the path to the image
  path.pop();
  return path.join('/');
}

function toggleCookie(cookieId, display, defaultValue) {
  // What is the state of this boolean (expanded/collapsed) cookie?
  var state = readCookie(cookieId);
  if ((state != 'collapsed') && (state != 'expanded')) {
    // No cookie yet, create it
    createCookie(cookieId, defaultValue);
    state = defaultValue;
  }
  var hook = document.getElementById(cookieId); // The hook is the part of
  // the HTML document that needs to be shown or hidden.
  var displayValue = 'none';
  var newState = 'collapsed';
  var image = 'expand.gif';
  if (state == 'collapsed') {
    // Show the HTML zone
    displayValue = display;
    image = 'collapse.gif';
    newState = 'expanded';
  }
  // Update the corresponding HTML element
  hook.style.display = displayValue;
  var img = document.getElementById(cookieId + '_img');
  changeImage(img, image);
  // Inverse the cookie value
  createCookie(cookieId, newState);
}

function podDownloadStatus(node, data) {
  // Checks the status of cookie "podDownload"
  var status = readCookie('podDownload');
  // Stop the timeout if the download is complete
  if (status == 'false') return;
  clearInterval(podTimeout);
  for (var key in data) node.setAttribute(key, data[key]);
}

// Function that allows to generate a document from a pod template
function generatePod(node, uid, fieldName, template, podFormat, queryData,
                     customParams, getChecked, mailing) {
  var f = document.getElementById('podForm');
  f.objectUid.value = uid;
  f.fieldName.value = fieldName;
  f.template.value = template;
  f.podFormat.value = podFormat;
  f.queryData.value = queryData;
  if (customParams) { f.customParams.value = customParams; }
  else { f.customParams.value = ''; }
  if (mailing) f.mailing.value = mailing;
  // Transmit value of cookie "showSubTitles"
  f.showSubTitles.value = readCookie('showSubTitles') || 'true';
  f.action.value = 'generate';
  f.checkedUids.value = '';
  f.checkedSem.value = '';
  if (getChecked) {
    // We must collect selected objects from a Ref field
    var cNode = document.getElementById(uid + '_' + getChecked);
    if (cNode && cNode.hasOwnProperty('_appy_objs_cbs')) {
      f.checkedUids.value = stringFromDictKeys(cNode['_appy_objs_cbs']);
      f.checkedSem.value = cNode['_appy_objs_sem'];
    }
  }
  // Submitting the form at the end blocks the animated gifs on FF
  f.submit();
  // If p_node is an image, replace it with a preloader to prevent double-clicks
  if (node.tagName == 'IMG') {
    var data = {'src': node.src, 'class': node.className,
                'onclick': node.attributes.onclick.value};
    node.setAttribute('onclick', '');
    node.className = '';
    var src2 = node.src.replace(podFormat + '.png', 'loadingPod.gif');
    node.setAttribute('src', src2);
    // Initialize the pod download cookie. "false" means: not downloaded yet
    createCookie('podDownload', 'false');
    // Set a timer that will check the cookie value
    podTimeout = window.setInterval(function(){
      podDownloadStatus(node, data)}, 700);
  }
}

// Function that allows to (un-)freeze a document from a pod template
function freezePod(uid, fieldName, template, podFormat, action) {
  var f = document.getElementById('podForm');
  f.objectUid.value = uid;
  f.fieldName.value = fieldName;
  f.template.value = template;
  f.podFormat.value = podFormat;
  f.action.value = action;
  askConfirm('form', 'podForm', action_confirm);
}

// Function that allows to upload a file for freezing it in a pod field
function uploadPod(uid, fieldName, template, podFormat) {
  var f = document.getElementById('uploadForm');
  f.objectUid.value = uid;
  f.fieldName.value = fieldName;
  f.template.value = template;
  f.podFormat.value = podFormat;
  f.uploadedFile.value = null;
  openPopup('uploadPopup');
}

function protectAppyForm() {
  window.onbeforeunload = function(e){
    f = document.getElementById("appyForm");
    if (f.button.value == "") {
      var e = e || window.event;
      if (e) {e.returnValue = warn_leave_form;}
      return warn_leave_form;
    }
  }
}

// Functions for opening and closing a popup
function openPopup(popupId, msg, width, height, back) {
  // Put the message into the popup
  if (msg) {
    var msgHook = (popupId == 'alertPopup')? 'appyAlertText': 'appyConfirmText';
    var confirmElem = document.getElementById(msgHook);
    confirmElem.innerHTML = msg;
  }
  // Open the popup
  var popup = document.getElementById(popupId);
  var frame = popupId == 'iframePopup'; // Is it the "iframe" popup ?
  /* Define height and width. For non-iframe popups, do not set its height: it
     will depend on its content */
  if (!width)  { width =  (frame)? window.innerWidth -200: 350 }
  if (!height) { height = (frame)? window.innerHeight-200: null }
  // Take into account the visible part of the browser window
  var scrollTop = document.documentElement.scrollTop || window.pageYOffset || 0;
  var top = null;
  if (height) { top = scrollTop + ((window.innerHeight - height) / 2)}
  else { top = scrollTop + (window.innerHeight * 0.25) }
  // Set the popup dimensions and position
  popup.style.top = top.toFixed() + 'px';
  popup.style.width = width.toFixed() + 'px';
  if (height) popup.style.height = height.toFixed() + 'px';
  popup.style.left = ((window.innerWidth - width) / 2).toFixed() + 'px';
  if (frame) {
    // Set the enclosed iframe dimensions
    var iframe = document.getElementById('appyIFrame');
    iframe.style.width = (width - 20).toFixed() + 'px';
    iframe.style.height = height.toFixed() + 'px';
    popup['back'] = back;
  }
  popup.style.display = 'block';
}

function closePopup(popupId, clean) {
  // Get the popup
  var container = null;
  if (popupId == 'iframePopup') container = window.parent.document;
  else container = window.document;
  var popup = container.getElementById(popupId);
  // Close the popup
  popup.style.display = 'none';
  popup.style.width = null;
  // Clean field "clean" if specified
  if (clean) {
    var elem = popup.getElementsByTagName('form')[0].elements[clean];
    if (elem) elem.value = '';
  }
  if (popupId == 'iframePopup') {
    // Reinitialise the enclosing iframe
    var iframe = container.getElementById('appyIFrame');
    iframe.style.width = null;
    while (iframe.firstChild) iframe.removeChild(iframe.firstChild);
    // Leave the form silently if we are on an edit page
    iframe.contentWindow.onbeforeunload = null;
  }
  return popup;
}

function backFromPopup() {
  var popup = closePopup('iframePopup');
  if (popup['back']) askAjax(':'+popup['back']);
  else window.parent.location = window.parent.location;
}

function showAppyMessage(message) {
  // Fill the message zone with the message to display
  var messageZone = getNode(':appyMessageContent');
  messageZone.innerHTML = message;
  // Display the message zone
  var messageDiv = getNode(':appyMessage');
  messageDiv.style.display = 'block';
}

// Function triggered when an action needs to be confirmed by the user
function askConfirm(actionType, action, msg, showComment) {
  /* Store the actionType (send a form, call an URL or call a script) and the
     related action, and shows the confirm popup. If the user confirms, we
     will perform the action. If p_showComment is true, an input field allowing
     to enter a comment will be shown in the popup. */
  var confirmForm = document.getElementById('confirmActionForm');
  confirmForm.actionType.value = actionType;
  confirmForm.action.value = action;
  if (!msg) msg = action_confirm;
  var commentArea = document.getElementById('commentArea');
  if (showComment) commentArea.style.display = 'block';
  else commentArea.style.display = 'none';
  openPopup("confirmActionPopup", msg);
}

// Function triggered when an action confirmed by the user must be performed
function doConfirm() {
  // The user confirmed: perform the required action
  closePopup('confirmActionPopup');
  var confirmForm = document.getElementById('confirmActionForm');
  var actionType = confirmForm.actionType.value;
  var action = confirmForm.action.value;
  // Get the entered comment and clean it on the confirm form
  var commentField = confirmForm.popupComment;
  var comment = ((commentField.style.display != 'none') &&
                 (commentField.value))? commentField.value: '';
  commentField.value = '';
  // Tip: for subsequent "eval" statements, "comment" is in the context
  if (actionType == 'form') {
    /* Submit the form whose id is in "action", and transmit him the comment
       from the popup when relevant. */
    var f = document.getElementById(action);
    if (comment) f.popupComment.value = comment;
    f.submit(); clickOn(f);
  }
  else if (actionType == 'url') { goto(action) } // Go to some URL
  else if (actionType == 'script') { eval(action) } // Exec some JS code
  else if (actionType == 'form+script') {
    var elems = action.split('+');
    var f = document.getElementById(elems[0]);
    // Submit the form in elems[0] and execute the JS code in elems[1]
    if (comment) f.popupComment.value = comment;
    f.submit(); clickOn(f);
    eval(elems[1]);
  }
  else if (actionType == 'form-script') {
    /* Similar to form+script, but the form must not be submitted. It will
       probably be used by the JS code, so the comment must be transfered. */
    var elems = action.split('+');
    var f = document.getElementById(elems[0]);
    if (comment) f.popupComment.value = comment;
    eval(elems[1]);
  }
}

// Function triggered when the user asks password reinitialisation
function doAskPasswordReinit() {
  // Check that the user has typed a login
  var f = document.getElementById('askPasswordReinitForm');
  var login = f.login.value.replace(' ', '');
  if (!login) { f.login.style.background = wrongTextInput; }
  else {
    closePopup('askPasswordReinitPopup');
    f.submit();
  }
}

// Function that finally posts the edit form after the user has confirmed that
// she really wants to post it.
function postConfirmedEditForm() {
  var f = document.getElementById('appyForm');
  f.confirmed.value = "True";
  f.button.value = 'save';
  f.submit();
}

// Function that shows or hides a tab. p_action is 'show' or 'hide'.
function manageTab(tabId, action) {
  // Manage the tab content (show it or hide it)
  var content = document.getElementById('tabcontent_' + tabId);
  if (action == 'show')   { content.style.display = 'table-row'; }
  else                    { content.style.display = 'none'; }
  // Manage the tab itself (show as selected or unselected)
  var left = document.getElementById('tab_' + tabId + '_left');
  var tab = document.getElementById('tab_' + tabId);
  var right = document.getElementById('tab_' + tabId + '_right');
  var suffix = (action == 'hide')? 'u': '';
  var path = changeImage(left, 'tabLeft' + suffix + '.png');
  tab.style.backgroundImage = 'url(' + path + '/tabBg' + suffix + '.png)';
  changeImage(right, 'tabRight' + suffix + '.png');
}

// Function used for displaying/hiding content of a tab
function showTab(tabId) {
  // 1st, show the tab to show
  manageTab(tabId, 'show');
  // Compute the number of tabs
  var idParts = tabId.split('_');
  var prefix = idParts[0] + '_';
  // Store the currently selected tab in a cookie
  createCookie('tab_' + idParts[0], tabId);
  var nbOfTabs = idParts[2]*1;
  // Then, hide the other tabs
  for (var i=0; i<nbOfTabs; i++) {
     var idTab = prefix + (i+1) + '_' + nbOfTabs;
     if (idTab != tabId) {
       manageTab(idTab, 'hide');
     }
  }
}

// Function that initializes the state of a tab
function initTab(tabsId, defaultValue) {
  var selectedTabId = readCookie(tabsId);
  if (!selectedTabId) { showTab(defaultValue) }
  else {
    /* Ensure the selected tab exists (it could be absent because of field
       visibility settings) */
    var selectedTab = document.getElementById('tab_' + selectedTabId);
    if (selectedTab) { showTab(selectedTabId) }
    else { showTab(defaultValue) }
  }
}

// List-related Javascript functions
function updateRowNumber(row, rowIndex, action) {
  /* Within p_row, we must find tables representing fields. Every such table has
     an id of the form [objectId]_[field]*[subField]*[i]. Within this table, for
     every occurrence of this string, the "-1" must be replaced with an updated
     index. If p_action is 'set', p_rowIndex is this index. If p_action is
     'add', the index must become [i] + p_rowIndex. */

  // Browse tables representing fields
  var fields = row.getElementsByTagName('table');
  var tagTypes = ['input', 'select', 'img', 'textarea', 'a', 'script'];
  var newIndex = -1;
  for (var i=0; i<fields.length; i++) {
    // Extract, from the table ID, the field identifier
    var id = fields[i].id;
    if ((!id) || (id.indexOf('_') == -1)) continue;
    // Extract info from the field identifier
    var old = id.split('_')[1];
    var elems = old.split('*');
    // Get "old" as a regular expression: we may need multiple replacements
    old = new RegExp(old.replace(/\*/g, '\\*'), 'g');
    // Compute the new index (if not already done) and new field identifier
    if (newIndex == -1) {
      var oldIndex = parseInt(elems[2]);
      newIndex = (action == 'set')? rowIndex: newIndex + oldIndex;
    }
    var neww = elems[0] + '*' + elems[1] + '*' + newIndex;
    // Replace the table ID with its new ID
    fields[i].id = fields[i].id.replace(old, neww);
    // Find sub-elements mentioning "old" and replace it with "neww"
    var val = w = null;
    for (var j=0; j<tagTypes.length; j++) {
      var widgets = fields[i].getElementsByTagName(tagTypes[j]);
      for (var k=0; k<widgets.length; k++) {
        w = widgets[k];
        // Patch id
        val = w.id;
        if (val) w.id = val.replace(old, neww);
        // Patch name
        val = w.name;
        if (val) w.name = val.replace(old, neww);
        // Patch href
        if ((w.nodeName == 'A') && w.href) w.href = w.href.replace(old, neww);
        // Patch (and reeval) script
        if (w.nodeName == 'SCRIPT') {
          w.text = w.text.replace(old, neww);
          eval(w.text);
        }
      }
    }
  }
}

function insertRow(tableId) {
  // This function adds a new row in table with ID p_tableId
  table = document.getElementById(tableId);
  newRow = table.rows[1].cloneNode(true);
  newRow.style.display = 'table-row';
  // Within newRow, incorporate the row number within field names and ids.
  table.tBodies[0].appendChild(newRow);
  updateRowNumber(newRow, table.rows.length-3, 'set');
}

function deleteRow(tableId, deleteImg) {
  row = deleteImg.parentNode.parentNode;
  table = document.getElementById(tableId);
  allRows = table.rows;
  toDeleteIndex = -1; // Will hold the index of the row to delete.
  for (var i=0; i < allRows.length; i++) {
    if (toDeleteIndex == -1) {
      if (row == allRows[i]) toDeleteIndex = i;
    }
    else {
      // Decrement higher row numbers by 1 because of the deletion
      updateRowNumber(allRows[i], -1, 'add');
    }
  }
  table.deleteRow(toDeleteIndex);
}

function onSelectDate(cal) {
  var p = cal.params;
  var update = (cal.dateClicked || p.electric);
  if (update && p.inputField) {
    var fieldName = cal.params.inputField.id;
    // Update day
    var dayValue = cal.date.getDate() + '';
    if (dayValue.length == 1) dayValue = '0' + dayValue;
    var dayField = document.getElementById(fieldName + '_day');
    if (dayField) dayField.value = dayValue;
    // Update month
    var monthValue = (cal.date.getMonth() + 1) + '';
    if (monthValue.length == 1) monthValue = '0' + monthValue;
    document.getElementById(fieldName + '_month').value = monthValue;
    // Update year
    var year = document.getElementById(fieldName + '_year');
    if (!year) {
      // On the search screen, the 'from year' field has a special name.
      var yearId = 'w_' + fieldName.split('_')[0] + '*date';
      year = document.getElementById(yearId);
    }
    year.value = cal.date.getFullYear() + '';
  }
  if (update && p.singleClick && cal.dateClicked) {
    cal.callCloseHandler();
  }
}

function onSelectObjects(popupId, initiatorId, objectUrl, mode,
                         sortKey, sortOrder, filterKey, filterValue){
  /* Objects have been selected in a popup, to be linked via a Ref with
     link='popup'. Get them. */
  var node = document.getElementById(popupId);
  var uids = stringFromDictKeys(node['_appy_objs_cbs']);
  var semantics = node['_appy_objs_sem'];
  // Show an error message if no element is selected
  if ((semantics == 'checked') && (!uids)) {
    openPopup('alertPopup', no_elem_selected);
    return;
  }
  // Close the popup
  closePopup('iframePopup');
  /* When refreshing the Ref field we will need to pass all those parameters,
     for replaying the popup query. */
  var params = {'selected': uids, 'semantics': semantics, 'sortKey': sortKey,
                'sortOrder': sortOrder, 'filterKey': filterKey,
                'filterValue': filterValue};
  if (mode == 'repl') {
    /* Link the selected objects (and unlink the potentially already linked
       ones) and refresh the Ref edit widget. */
    askField(':'+initiatorId, objectUrl, 'edit', params, false);
  }
  else {
    // Link the selected objects and refresh the Ref view widget
    params['action'] = 'onSelectFromPopup';
    askField(':'+initiatorId, objectUrl, 'view', params, false);
  }
}

function onSelectObject(checkboxId, initiatorId, objectUrl) {
  /* In a Ref field with link="popup", a single object has been clicked. If
     multiple objects can be selected, simply update the corresponding checkbox
     status. Else, close the popup and return the selected object. */
  var checkbox = document.getElementById(checkboxId);
  // If the td is visible, simply click the checkbox
  var tdDisplay = checkbox.parentNode.style.display;
  if ((tdDisplay == 'table-cell') || !tdDisplay){ checkbox.click() }
  else {
    /* Close the popup and directly refresh the initiator field with the
       selected object. */
    var uids = checkbox.value;
    closePopup('iframePopup');
    var params = {'selected': uids, 'semantics': 'checked'};
    askField(':'+initiatorId, objectUrl, 'edit', params, false);
  }
}

function onSelectTemplateObject(checkboxId, className) {
  // Get the form for creating instances of p_className
  var addForm = window.parent.document.forms[className + '_add'];
  addForm.template.value = document.getElementById(checkboxId).value;
  closePopup('iframePopup');
  addForm.submit();
}

// Sets the focus on the correct element in some page
function initFocus(pageId){
  var id = pageId + '_title';
  var elem = document.getElementById(id);
  if (elem) elem.focus();
}

function reindexObject(indexName){
  var f = document.forms['reindexForm'];
  f.indexName.value = indexName;
  f.submit();
}

// Live-search-related functions (LS)
function detectEventType(event) {
  /* After p_event occurred on a live search input field, must we trigger a
     search (a new char has been added), move up/down within the search
     results (key up/down has been pressed) or hide the dropdown (escape)? */
  if (event.type == 'focus') return 'search'
  switch (event.keyCode) {
    case 38: return 'up';
    case 40: return 'down';
    case 27: return 'hide'; // escape
    case 13: return 'go'; // cr
    case 37: break; // left
    case 39: break; // right
    default: return 'search';
  }
}
/* Function that selects the search result within the dropdown, after the user
   has pressed the 'up' od 'down' key (p_direction). */
function selectLSResult(dropdown, direction){
  var results = dropdown.children[0].getElementsByTagName('div');
  if (results.length == 0) return;
  var j; // The index of the new element to select
  for (var i=0, len=results.length; i<len; i++) {
    if (results[i].className == 'lsSelected') {
      if (direction == 'up') {
        if (i > 0) j = i-1;
        else j = len-1;
      }
      else {
        if (i < (len-1)) j = i+1;
        else j = 0;
      }
      results[i].className = '';
      results[j].className = 'lsSelected';
      break;
    }
  }
  if (isNaN(j)) results[0].className = 'lsSelected';
}

// Function that allows to go to a selected search result
function gotoLSLink(dropdown) {
  var results = dropdown.children[0].getElementsByTagName('div');
  for (var i=0, len=results.length; i<len; i++) {
    if (results[i].className == 'lsSelected') {
      var a = results[i].children[0];
      if (a.href) window.location = a.href;
      else eval(a.onclick);
    }
  }
}

function hideLSDropdown(dropdown, timeout) {
  if (dropdown.style.display == 'none') return;
  if (!timeout) { dropdown.style.display = 'none'; return; }
  lsTimeout = setTimeout(function(){
    dropdown.style.display = 'none';}, 400);
}

// Function that manages an p_event that occurred on a live search input field
function onLiveSearchEvent(event, klass, action, toolUrl) {
  var dropdown = document.getElementById(klass + '_LSDropdown');
  if (lsTimeout) clearTimeout(lsTimeout);
  // Hide the dropdown if action is forced to 'hide'
  if (action == 'hide') { hideLSDropdown(dropdown, true); return; }
  // Detect if the dropdown must be shown or hidden
  var input = document.getElementById(klass + '_LSinput');
  if (input.value.length > 2) {
    var eventType = detectEventType(event);
    if (!eventType) return;
    if (eventType == 'hide') { hideLSDropdown(dropdown, false); return;}
    if (eventType == 'go') { gotoLSLink(dropdown); return; }
    if (eventType == 'search') {
      // Trigger an Ajax search and refresh the dropdown content
      var formElems = document.getElementById(klass + '_LSForm').elements;
      var params = {};
      for (var i=0, len=formElems.length; i<len; i++) {
        var param = formElems.item(i);
        var paramName = formElems.item(i).name;
        if (param.name == 'action') continue;
        params[param.name] = param.value;
      }
      lsTimeout = setTimeout(function() {
        askAjaxChunk(klass+ '_LSResults', 'GET', toolUrl, 'pxLiveSearchResults',
                     params);
        dropdown.style.display = 'block';}, 400);
      }
    else { selectLSResult(dropdown, eventType);} // Move up/down in results
  }
  else { hideLSDropdown(dropdown, true); }
}
