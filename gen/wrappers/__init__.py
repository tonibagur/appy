'''This package contains base classes for wrappers that hide to the Appy
   developer the real classes used by Zope.'''

# ------------------------------------------------------------------------------
import os, os.path, mimetypes
import appy.pod
from appy.gen import Field, Search, Ref, String, WorkflowAnonymous
from appy.gen.indexer import defaultIndexes
from appy.gen.layout import defaultPageLayouts
from appy.gen.utils import createObject
from appy.px import Px
from appy.shared.utils import getOsTempFolder, normalizeString
from appy.shared.xml_parser import XmlMarshaller
from appy.shared.csv_parser import CsvMarshaller

# Basic attributes computed from a Python expression ---------------------------
expressionAttributes = {
  'tool': 'o.getTool().appy()',
  'request': 'o._getRequestObject()',
  'session': 'o.REQUEST.SESSION',
  'typeName': 'self.__class__.__bases__[-1].__name__',
  'id': 'o.id',
  'uid': 'o.id',
  'klass': 'self.__class__.__bases__[-1]',
  'created': 'o.created',
  'creator': 'o.creator',
  'modified': 'o.modified',
  'url': 'o.absolute_url()',
  'state': 'o.State()',
  'stateLabel': 'o.translate(o.getWorkflowLabel())',
  'history': "o.workflow_history['appy']",
  'user': 'o.getTool().getUser()',
  'fields': 'o.getAllAppyTypes()',
  'siteUrl': 'o.getTool().getSiteUrl()',
  'initiator': 'o.getInitiatorInfo(True)',
  'localRoles': "getattr(o.aq_base, '__ac_local_roles__', None)"
}

# ------------------------------------------------------------------------------
class AbstractWrapper(object):
    '''Any real Appy-managed Zope object has a companion object that is an
       instance of this class.'''

    # Input field for going to element number ...
    pxGotoNumber = Px('''
     <x var2="label=_('goto_number');
              gotoName='%s_%s_goto' % (obj.id, field.name);
              popup=inPopup and '1' or '0'">
      <span class="discreet" style="padding-left: 5px">:label</span>
      <input type="text" size=":(len(str(totalNumber))-1) or 1"
             onclick="this.select()"
             onkeydown=":'if (event.keyCode==13) document.getElementById' \
                         '(%s).click()' % q(gotoName)"/><img
             id=":gotoName" name=":gotoName"
             class="clickable" src=":url('gotoNumber')" title=":label"
             onclick=":'gotoTied(%s,%s,this.previousSibling,%s,%s)' % \
                 (q(sourceUrl), q(field.name), totalNumber, q(popup))"/></x>''')

    pxNavigationStrip = Px('''
     <table width="100%">
      <tr valign="top">
       <!-- Breadcrumb -->
       <td var="sup=zobj.getSupBreadCrumb();
                breadcrumb=zobj.getBreadCrumb(inPopup=inPopup);
                sub=zobj.getSubBreadCrumb()" class="breadcrumb">
        <x if="sup">::sup</x>
        <x for="bc in breadcrumb" var2="nb=loop.bc.nb">
         <img if="nb != 0" src=":url('to')"/>
         <!-- Display only the title of the current object -->
         <span if="nb == len(breadcrumb)-1">::bc.title</span>
         <!-- Display a link for parent objects -->
         <a if="nb != len(breadcrumb)-1" href=":bc.url">:bc.title</a>
        </x>
        <x if="sub">::sub</x>
       </td>
       <!-- Object navigation -->
       <td var="nav=req.get('nav', None)" if="nav"
           var2="self=ztool.getNavigationInfo(nav, inPopup)" align=":dright"
           width="200px">:self.pxNavigate</td>
      </tr>
     </table>
     <!-- Object phases and pages -->
     <x if="zobj.mayNavigate()" var2="phases=zobj.getAppyPhases()">
      <x if="phases">:phases[0].pxAllPhases</x></x>''')

    # The template PX for all pages
    pxTemplate = Px('''
     <html var="ztool=tool.o;                   user=tool.user;
                req=ztool.REQUEST;              resp=req.RESPONSE;
                inPopup=req.get('popup') == '1';
                obj=obj or ztool.getHomeObject(inPopup);
                zobj=obj and obj.o or None;     ajax=False;
                isAnon=user.login=='anon';      app=ztool.getApp();
                appFolder=app.data;             url = ztool.getIncludeUrl;
                appName=ztool.getAppName();     _=ztool.translate;
                dummy=setattr(req, 'pxContext', _ctx_);
                lang=ztool.getUserLanguage();   q=ztool.quote;
                layoutType=ztool.getLayoutType();
                showPortlet=not inPopup and ztool.showPortlet(obj, layoutType);
                dir=ztool.getLanguageDirection(lang);
                cfg=ztool.getProductConfig(True);
                wide=(cfg.skin == 'wide') or inPopup;
                dleft=(dir == 'ltr') and 'left' or 'right';
                dright=(dir == 'ltr') and 'right' or 'left';
                x=resp.setHeader('Content-type', ztool.xhtmlEncoding);
                x=resp.setHeader('Expires', 'Thu, 11 Dec 1975 12:05:00 GMT+2');
                x=resp.setHeader('Content-Language', lang)"
           dir=":ztool.getLanguageDirection(lang)">
     <head>
      <title>:_('app_name')</title>
      <link rel="icon" type="image/x-icon" href="/favicon.ico"/>
      <x for="name in ztool.getGlobalCssJs(dir)">
       <link if="name.endswith('.css')" rel="stylesheet" type="text/css"
             href=":url(name)"/>
       <script if="name.endswith('.js')" src=":url(name)"></script>
      </x>
     </head>
     <body style=":wide and 'margin:0' or ''">
      <!-- Google Analytics stuff, if enabled -->
      <script var="gaCode=ztool.getGoogleAnalyticsCode()" if="gaCode"
              type="text/javascript">:gaCode</script>

      <!-- Popup for confirming an action -->
      <div id="confirmActionPopup" class="popup">
       <form id="confirmActionForm" method="post">
        <div align="center">
         <p id="appyConfirmText"></p>
         <input type="hidden" name="actionType"/>
         <input type="hidden" name="action"/>
         <div id="commentArea" align=":dleft"><br/>
          <span class="discreet">:_('workflow_comment')</span>
          <textarea name="popupComment" cols="30" rows="3"></textarea>
          <br/>
         </div><br/>
         <input type="button" onclick="doConfirm()" value=":_('yes')"/>
         <input type="button" value=":_('no')"
                onclick="closePopup('confirmActionPopup', 'comment')"/>
        </div>
       </form>
      </div>

      <!-- Popup for uploading a file in a pod field -->
      <div id="uploadPopup" class="popup" align="center">
       <form id="uploadForm" name="uploadForm" enctype="multipart/form-data"
             method="post" action=":ztool.absolute_url() + '/doPod'">
        <input type="hidden" name="objectUid"/>
        <input type="hidden" name="fieldName"/>
        <input type="hidden" name="template"/>
        <input type="hidden" name="podFormat"/>
        <input type="hidden" name="action" value="upload"/>
        <input type="file" name="uploadedFile"/><br/><br/>
        <input type="submit" value=":_('object_save')"/>
        <input type="button" onclick="closePopup('uploadPopup')"
               value=":_('object_cancel')"/>
       </form>
      </div>

      <!-- Popup for reinitializing the password -->
      <div id="askPasswordReinitPopup" class="popup"
           if="isAnon and ztool.showForgotPassword()">
       <form id="askPasswordReinitForm" method="post"
             action=":ztool.absolute_url() + '/askPasswordReinit'">
        <div align="center">
         <p>:_('app_login')</p>
         <input type="text" size="35" name="login" id="login" value=""/>
         <br/><br/>
         <input type="button" onclick="doAskPasswordReinit()"
                value=":_('ask_password_reinit')"/>
         <input type="button" onclick="closePopup('askPasswordReinitPopup')"
                value=":_('object_cancel')"/>
        </div>
       </form>
      </div>

      <!-- Popup for displaying an error message (~JS alert()) -->
      <div id="alertPopup" class="popup">
       <img src=":url('warningBig')" align=":dleft" style="margin-right: 10px"/>
       <p id="appyAlertText" style="margin-bottom: 15px"></p>
       <div align="center">
        <input type="button" onclick="closePopup('alertPopup')"
               value=":_('appy_ok')"/>
       </div>
      </div>

      <!-- Popup containing the Appy iframe -->
      <div id="iframePopup" class="popup" if="not inPopup">
       <img align=":dright" src=":url('close')" class="clickable"
            onclick="closePopup('iframePopup')"/>
       <iframe id="appyIFrame" name="appyIFrame" frameborder="0"></iframe>
      </div>

      <div class=":wide and 'mainWide main rel' or 'main rel'">
       <!-- The browser incompatibility message when relevant -->
       <div var="bi=ztool.getBrowserIncompatibility()" if="bi"
            class="wrongBrowser">:bi</div>

       <!-- Top banner -->
       <div class="top" if="not inPopup"
            var2="bannerName=(dir == 'ltr') and 'banner' or 'bannerrtl'"
            style=":url(bannerName, bg=True) + ';background-repeat:no-repeat;\
                   position:relative'">

        <!-- Logo (transparent clickable zone by default) -->
        <div align=":dleft" style="position: absolute">
          <a href=":ztool.getSiteUrl()"><img src=":url('logo')"/></a></div>

        <!-- Top links -->
        <div class="topLinks" align=":dright">
         <!-- Custom links -->
         <x>:tool.pxLinks</x>

         <!-- Top-level pages -->
         <a for="page in tool.pages" class="pageLink"
            href=":page.url">:page.title</a>

         <!-- Connect link if discreet login -->
         <a if="isAnon and cfg.discreetLogin" id="loginLink" name="loginLink"
            onclick="showLoginForm()"
            class="pageLink clickable">:_('app_connect')</a>

         <!-- Language selector -->
         <select if="ztool.showLanguageSelector()" class="pageLink"
                 var2="languages=ztool.getLanguages();
                       defaultLanguage=languages[0]"
                 onchange=":'switchLanguage(this,%s)' % q(ztool.getSiteUrl())">
          <option for="lg in languages" value=":lg"
                  selected=":lang == lg">:ztool.getLanguageName(lg)</option>
         </select>
        </div>
       </div>
       <div height="0">:tool.pxMessage</div> <!-- The message zone -->

       <!-- The user strip -->
       <table if="not inPopup" class="userStrip"
              height=":cfg.discreetLogin and '5px' or '28px'">
        <tr>
         <!-- The user login form for anonymous users -->
         <td align="center"
             if="isAnon and ('/temp_folder/' not in req['ACTUAL_URL'])">
          <form id="loginForm" name="loginForm" method="post" class="login"
                action=":tool.url + '/performLogin'">
           <input type="hidden" name="js_enabled" id="js_enabled" value="0"/>
           <input type="hidden" name="cookies_enabled" id="cookies_enabled"
                  value=""/>
           <input type="hidden" name="login_name" id="login_name" value=""/>
           <input type="hidden" name="pwd_empty" id="pwd_empty" value="0"/>
           <!-- Login fields directly shown or not depending on
                discreetLogin. -->
           <span id="loginFields" name="loginFields"
                 style=":cfg.discreetLogin and 'display:none' or \
                         'display:block'">
            <span class="userStripText">:_('app_login')</span>
            <input type="text" name="__ac_name" id="__ac_name" value=""
                   style="width: 142px"/>&nbsp;
            <span class="userStripText">:_('app_password')</span>
            <input type="password" name="__ac_password" id="__ac_password"
                   style="width: 142px"/>
            <input type="submit" name="submit" onclick="setLoginVars()"
                   var="label=_('app_connect')" value=":label" alt=":label"/>
            <input type="hidden" name="goto" value=":req.get('goto', None)"/>
            <!-- Forgot password? -->
            <a if="ztool.showForgotPassword()"
               href="javascript: openPopup('askPasswordReinitPopup')"
               class="lostPassword">:_('forgot_password')</a>
           </span>
          </form>
         </td>

         <!-- User info and controls for authenticated users -->
         <td if="not isAnon">
          <div class="buttons" align=":dright" width="99%">
           <!-- Config -->
           <a if="tool.allows('write')" href=":tool.url"
              title=":_('%sTool' % appName)">
            <img src=":url('config')"/></a>
           <!-- Additional icons -->
           <x>:tool.pxIcons</x>
           <x>:user.pxUserLink</x>
           <!-- Log out -->
           <a href=":ztool.getLogoutUrl()" title=":_('app_logout')">
            <img src=":url('logout.gif')"/></a>
          </div>
         </td>
        </tr>
       </table>
       <!-- A warning text if we are on a test system -->
       <div height="0" class="test"
            if="not inPopup and cfg.test">:cfg.test</div>
       <div class="payload" var="space=not inPopup and ' footerSpace' or ''">
        <div class="row">
         <!-- The portlet -->
         <div if="showPortlet" class=":'portlet' + space">:tool.pxPortlet</div>
         <div class=":'content' + space">
          <!-- Navigation strip -->
          <div if="zobj and zobj.showNavigationStrip(layoutType, inPopup)"
               height="26px">:obj.pxNavigationStrip</div>
          <!-- Page content -->
          <div>:content</div>
         </div>
        </div>
       </div>
       <!-- Footer -->
       <div if="not inPopup"
          class=":wide and 'footerWide footer' or 'footer'">:tool.pxFooter</div>
      </div>
     </body>
    </html>''', prologue=Px.xhtmlPrologue)

    # --------------------------------------------------------------------------
    # PXs for rendering graphical elements tied to a given object
    # --------------------------------------------------------------------------

    # This PX displays an object's history
    pxHistory = Px('''
     <div var="startNumber=int(req.get('startNumber', 0));
               batchSize=historyMaxPerPage|req.get('maxPerPage', 5);
               batchSize=int(batchSize);
               historyInfo=zobj.getHistory(startNumber, batchSize=batchSize)"
          if="historyInfo.events"
          var2="ajaxHookId='appyHistory';
                objs=historyInfo.events;
                totalNumber=historyInfo.totalNumber;
                batchNumber=len(objs)"
          id=":ajaxHookId">
      <script>:zobj.getHistoryAjaxData(ajaxHookId, startNumber, \
                                       batchSize)</script>
      <!-- Navigate between history pages -->
      <x>:tool.pxNavigate</x>
      <!-- History -->
      <table width="100%" class="history">
       <tr>
        <th align=":dleft">:_('object_action')</th>
        <th align=":dleft">:_('object_author')</th>
        <th align=":dleft">:_('action_date')</th>
        <th align=":dleft">:_('action_comment')</th>
       </tr>
       <tr for="event in objs"
           var2="rhComments=event.get('comments', None);
                 state=event.get('review_state', None);
                 action=event['action'];
                 isDataChange=action.startswith('_data')"
           class=":loop.event.odd and 'even' or 'odd'" valign="top">
        <td if="isDataChange">
         <x>:_('data_%s' % action[5:-1])</x>
         <img if="user.has_role('Manager')" class="clickable"
              src=":url('delete')"
              onclick=":'onDeleteEvent(%s,%s)' % \
                        (q(zobj.id), q(event['time']))"/>
        </td>
        <td if="not isDataChange">:_(zobj.getWorkflowLabel(action))</td>
        <td var="actorId=event.get('actor')">
         <x if="not actorId">?</x>
         <x if="actorId">:ztool.getUserName(actorId)</x>
        </td>
        <td>:ztool.formatDate(event['time'], withHour=True)</td>
        <td if="not isDataChange">
         <x if="rhComments">::zobj.formatText(rhComments)</x>
         <x if="not rhComments">-</x>
        </td>
        <td if="isDataChange">
         <!-- Display the previous values of the fields whose value were
              modified in this change. -->
         <table class="changes" width="100%" if="event.get('changes')">
          <tr>
           <th align=":dleft" width="30%">:_('modified_field')</th>
           <th align=":dleft" width="70%">:_('previous_value')</th>
          </tr>
          <tr for="change in event['changes'].items()" valign="top"
              var2="elems=change[0].split('-');
                    field=zobj.getAppyType(elems[0]);
                    lg=(len(elems) == 2) and elems[1] or ''">
           <td><x>::_(field.labelId)</x>
               <x if="lg">:' (%s)' % ztool.getLanguageName(lg, True)</x></td>
           <td>::change[1][0]</td>
          </tr>
         </table>
         <!-- There may also be a comment, too -->
         <x if="rhComments">::zobj.formatText(rhComments)</x>
        </td>
       </tr>
      </table>
     </div>''')

    pxTransitions = Px('''
     <form var="transitions=targetObj.getTransitions()" if="transitions"
           var2="formId='trigger_%s' % targetObj.id;
                 zobj=targetObj"
           id=":formId" action=":targetObj.absolute_url() + '/onTrigger'"
           style="display: inline" method="post">
      <input type="hidden" name="transition"/>
      <!-- Input field for storing the comment coming from the popup -->
      <textarea id="popupComment" name="popupComment" cols="30" rows="3"
                style="display:none"></textarea>
      <x for="transition in transitions">
       <!-- Render a transition or a group of transitions. -->
       <x if="transition.type == 'transition'">:transition.pxView</x>
       <x if="transition.type == 'group'"
          var2="uiGroup=transition">:uiGroup.px</x>
      </x></form>''')

    # Displays header information about an object: title, workflow-related info,
    # history...
    pxHeader = Px('''
     <div if="not zobj.isTemporary()"
          var2="hasHistory=zobj.hasHistory();
                collapsible=collapsible|True;
                collapse=zobj.getHistoryCollapse();
                creator=zobj.Creator()">
      <table width="100%" class="header" cellpadding="0" cellspacing="0">
       <tr>
        <td colspan="2" class="by">
         <!-- Plus/minus icon for accessing history -->
         <x if="hasHistory and collapsible"><x>:collapse.px</x>
          <x>:_('object_history')</x> &mdash;
         </x>

         <!-- Creator and last modification date -->
         <x>:_('object_created_by')</x> <x>:ztool.getUserName(creator)</x>
         
         <!-- Creation and last modification dates -->
         <x>:_('object_created_on')</x>
         <x var="creationDate=zobj.Created();
                 modificationDate=zobj.Modified()">
          <x>:ztool.formatDate(creationDate, withHour=True)</x>
          <x if="modificationDate != creationDate">&mdash;
           <x>:_('object_modified_on')</x>
           <x>:ztool.formatDate(modificationDate, withHour=True)</x>
          </x>
         </x>

         <!-- State -->
         <x if="zobj.showState()">&mdash;
          <x>:_('workflow_state')</x> : <b>:_(zobj.getWorkflowLabel())</b>
         </x>
        </td>
       </tr>

       <!-- Object history -->
       <tr if="hasHistory">
        <td colspan="2">
         <span id=":collapse.id"
             style=":collapsible and collapse.style or ''"><x>:obj.pxHistory</x>
         </span>
        </td>
       </tr>
      </table>
     </div>''')

    # Shows the range of buttons (next, previous, save,...) and the workflow
    # transitions for a given object.
    pxButtons = Px('''
     <div class="objectButtons"
          var="previousPage=phaseObj.getPreviousPage(page)[0];
               nextPage=phaseObj.getNextPage(page)[0];
               isEdit=layoutType == 'edit';
               mayAct=not isEdit and zobj.mayAct();
               pageInfo=phaseObj.pagesInfo[page]">
      <!-- Refresh -->
      <a if="zobj.isDebug()"
         href=":zobj.getUrl(mode=layoutType, page=page, refresh='yes', \
                            inPopup=inPopup)">
       <img title="Refresh" style="vertical-align:top" src=":url('refresh')"/>
      </a>
      <!-- Previous -->
      <x if="previousPage and pageInfo.showPrevious"
         var2="label=_('page_previous');
               css=ztool.getButtonCss(label, small=False)">
       <!-- Button on the edit page -->
       <x if="isEdit">
        <input type="button" class=":css" value=":label" id="previous"
               onclick="submitAppyForm(this)"
               style=":url('previous', bg=True)"/>
        <input type="hidden" name="previousPage" value=":previousPage"/>
       </x>
       <!-- Button on the view page -->
       <input if="not isEdit" type="button" class=":css" value=":label"
              style=":url('previous', bg=True)" id="previous"
              onclick=":'goto(%s)' % q(zobj.getUrl(page=previousPage, \
                                                   inPopup=inPopup))"/>
      </x>
      <!-- Save -->
      <input if="isEdit and pageInfo.showSave" type="button" id="save"
             var2="label=_('object_save');
                   css=ztool.getButtonCss(label, small=False)"
             class=":css" onclick="submitAppyForm(this)"
             value=":label" style=":url('save', bg=True)" />
      <!-- Cancel -->
      <input if="isEdit and pageInfo.showCancel" type="button" id="cancel"
             var2="label=_('object_cancel');
                   css=ztool.getButtonCss(label, small=False)"
             class=":css" onclick="submitAppyForm(this)" value=":label"
             style=":url('cancel', bg=True)"/>
      <x if="not isEdit"
         var2="locked=zobj.isLocked(user, page);
               editable=pageInfo.showOnEdit and pageInfo.showEdit and \
                        mayAct and zobj.mayEdit()">
       <!-- Edit -->
       <input if="editable and not locked" type="button" id="edit"
              var="label=_('object_edit');
                   css=ztool.getButtonCss(label, small=False)"
              value=":label" class=":css" style=":url('edit', bg=True)"
              onclick=":'goto(%s)' % q(zobj.getUrl(mode='edit', page=page, \
                                                   inPopup=inPopup))"/>
       <!-- Locked -->
       <a if="editable and locked">
        <img class="help"
             var="lockDate=ztool.formatDate(locked[1]);
                  lockMap={'user':ztool.getUserName(locked[0]), \
                           'date':lockDate};
                  lockMsg=_('page_locked', mapping=lockMap)"
             src=":url('lockedBig')" title=":lockMsg"/></a>
       <a if="editable and locked and user.has_role('Manager')">
        <img class="clickable" title=":_('page_unlock')"
             src=":url('unlockBig')"
             onclick=":'onUnlockPage(%s,%s)' % (q(zobj.id), q(page))"/></a>
      </x>
      <!-- Delete -->
      <input if="not isEdit and not inPopup and (page == 'main') and \
                 zobj.mayDelete()" type="button"
             var2="label=_('object_delete');
                   css=ztool.getButtonCss(label, small=False)"
             value=":label" class=":css" style=":url('delete', bg=True)"
             onclick=":'onDeleteObject(%s)' % q(zobj.id)"/>
      <!-- Next -->
      <x if="nextPage and pageInfo.showNext" id="next"
         var2="label=_('page_next');
               css=ztool.getButtonCss(label, small=False)">
       <!-- Button on the edit page -->
       <x if="isEdit">
        <input type="button" class=":css" onclick="submitAppyForm(this)"
               id="next" style=":url('next', bg=True)" value=":label"/>
        <input type="hidden" name="nextPage" value=":nextPage"/>
       </x>
       <!-- Button on the view page -->
       <input if="not isEdit" type="button" class=":css" value=":label"
              style=":url('next', bg=True)" id="next"
              onclick=":'goto(%s)' % q(zobj.getUrl(page=nextPage, \
                                                   inPopup=inPopup))"/>
      </x>
      <!-- Workflow transitions -->
      <x var="targetObj=zobj"
         if="mayAct and (page == 'main') and \
             targetObj.showTransitions(layoutType)">:obj.pxTransitions</x>
      <!-- Fields (actions) defined with layout "buttons" -->
      <x if="layoutType != 'edit'"
         var2="fields=zobj.getAppyTypes('buttons', page, type='Action');
               layoutType='view'">
       <!-- Call pxView and not pxRender to avoid having a table -->
       <x for="field in fields" var2="name=field.name">:field.pxView</x>
      </x>
     </div>''')

    # Display the fields of a given page for a given object
    pxFields = Px('''
     <table width=":layout.width">
      <tr for="field in groupedFields">
       <td if="field.type == 'group'">:field.pxView</td>
       <td if="field.type != 'group'">:field.pxRender</td>
      </tr>
     </table>''')

    pxIndexedContent = Px('''
     <form name="reindexForm" method="post" action=":'%s/onReindex' % obj.url">
      <input type="hidden" name="indexName"/>
      <table var="indexes=obj.getIndexes(asList=True)" class="list compact">
       <!-- 1st line: dump local roles, by the way -->
       <tr>
        <td>Local roles</td>
        <td colspan="2"><x>:obj.localRoles</x></td>
       </tr>
       <tr><th>Index name</th><th>Type</th><th>Content
        <img src=":url('reindex')" class="clickable" title="Reindex all indexes"
             onclick="reindexObject(\'_all_\')"/></th></tr>
       <tr for="info in indexes"
           class=":loop.info.odd and 'odd' or 'even'">
         <td>:info[0]</td><td>:info[1]</td>
         <td><img src=":url('reindex')" class="clickable"
                  title="Reindex this index only"
                  onclick=":'reindexObject(%s)' % q(info[0])"/>
             <x>:ztool.getCatalogValue(zobj, info[0])</x></td>
       </tr>
      </table>
     </form>''')

    # The object, as shown in a list of referred (tied) objects
    pxViewAsTied = Px('''
     <tr valign="top" class=":rowCss"
         var2="tiedUid=tied.o.id;
               objectIndex=field.getIndexOf(zobj, tiedUid)|None;
               mayView=tied.o.mayView();
               cbId='%s_%s' % (ajaxHookId, currentNumber)"
         id=":tiedUid">
      <td if="numbered and not inPickList and not selector">:field.pxNumber</td>
      <td if="checkboxes" class="cbCell">
       <input if="mayView" type="checkbox" name=":ajaxHookId" id=":cbId"
              var2="checked=cbChecked|False" checked=":checked"
              value=":tiedUid" onclick="toggleCb(this)"/>
      </td>
      <td for="column in columns" width=":column.width" align=":column.align"
          var2="refField=column.field">:refField.pxRenderAsTied</td>
      <!-- Store data in this tr node allowing to ajax-refresh it -->
      <script>:field.getAjaxDataRow(tied, ajaxHookId, rowCss=rowCss, \
               currentNumber=currentNumber, cbChecked=cbId)</script>
     </tr>''')

    # When calling pxViewAsTied from Ajax, this surrounding PX is called to
    # define the appropriate variables based on request values.
    pxViewAsTiedFromAjax = Px('''
     <x var="dummy=ztool.updatePxContextFromRequest();
             tied=obj;
             zobj=ztool.getObject(sourceId);
             obj=zobj.appy();
             inMenu=False;
             field=zobj.getAppyType(refFieldName);
             layoutType='view';
             render=field.getRenderMode(layoutType);
             selector=field.getSelector(obj, req);
             linkList=field.link == 'list';
             numberWidth=len(str(totalNumber));
             tiedClassName=ztool.getPortalType(field.klass);
             target=ztool.getLinksTargetInfo(field.klass, zobj.id);
             mayEdit=not field.isBack and zobj.mayEdit(field.writePermission);
             mayEd=not inPickList and mayEdit;
             mayLink=mayEd and field.mayAdd(zobj, mode='link', \
                                            checkMayEdit=False);
             mayUnlink=mayEd and field.getAttribute(zobj, 'unlink');
             gotoNumber=numbered;
             changeOrder=mayEd and field.getAttribute(zobj, 'changeOrder');
             changeNumber=not inPickList and numbered and changeOrder and \
                          (totalNumber &gt; 3);
             columns=ztool.getColumnsSpecifiers(tiedClassName, \
                   field.getAttribute(obj, 'shownInfo'), dir);
             showSubTitles=showSubTitles|True">:obj.pxViewAsTied</x>''')

    # The object, as shown in a list of query results
    pxViewAsResult = Px('''
     <tr var2="obj=zobj.appy(); mayView=zobj.mayView();
               cbId='%s_%s' % (checkboxesId, currentNumber)"
         id=":zobj.id" class=":rowCss" valign="top">
      <!-- A checkbox if required -->
      <td if="checkboxes" class="cbCell" style=":'display:%s' % cbDisplay">
       <input type="checkbox" name=":checkboxesId" checked="checked"
              var2="checked=cbChecked|True" value=":zobj.id"
              onclick="toggleCb(this)" id=":cbId"/>
      </td>
      <td for="column in columns"
          var2="field=column.field" id=":'field_%s' % field.name"
          width=":column.width"
          align=":column.align">:field.pxRenderAsResult</td>
     <!-- Store data in this tr node allowing to ajax-refresh it -->
     <script>:uiSearch.getAjaxDataRow(zobj, ajaxHookId, rowCss=rowCss, \
              currentNumber=currentNumber, cbChecked=cbId)</script>
     </tr>''')

    # When calling pxViewAsResult from Ajax, this surrounding PX is called to
    # define the appropriate variables based on request values.
    pxViewAsResultFromAjax = Px('''
     <x var="ajaxHookId='queryResult';
             dummy=ztool.updatePxContextFromRequest();
             showSubTitles=showSubTitles|True;
             refInfo=ztool.getRefInfo();
             columnLayouts=ztool.getResultColumnsLayouts(className, refInfo);
             columns=ztool.getColumnsSpecifiers(className, columnLayouts, dir);
             target=ztool.getLinksTargetInfo(ztool.getAppyClass(className));
             uiSearch=ztool.getSearch(\
               className, searchName, ui=True)">:obj.pxViewAsResult</x>''')

    pxView = Px('''
     <x var="x=zobj.mayView(raiseError=True);
             errors=req.get('errors', {});
             layout=zobj.getPageLayout(layoutType);
             phaseObj=zobj.getAppyPhases(currentOnly=True, layoutType='view');
             x=not phaseObj and zobj.raiseUnauthorized();
             phase=phaseObj.name;
             cssJs={};
             page=req.get('page', None) or zobj.getDefaultViewPage();
             x=zobj.removeMyLock(user, page);
             groupedFields=zobj.getGroupedFields(layoutType, page,cssJs=cssJs)">
      <x>:tool.pxPagePrologue</x>
      <x if="('indexed' in req) and \
             user.has_role('Manager')">:obj.pxIndexedContent</x>
      <x var="tagId='pageLayout'; tagName=''; tagCss='';
              layoutTarget=obj">:layout.pxRender</x>
      <x var="x=zobj.callOnView()">:tool.pxPageBottom</x>
     </x>''', template=pxTemplate, hook='content')

    pxEdit = Px('''
     <x var="x=zobj.mayEdit(raiseError=True, permOnly=zobj.isTemporary());
             errors=req.get('errors', {});
             layout=zobj.getPageLayout(layoutType);
             cssJs={};
             phaseObj=zobj.getAppyPhases(currentOnly=True, \
                                         layoutType=layoutType);
             x=not phaseObj and zobj.raiseUnauthorized();
             phase=phaseObj.name;
             page=req.get('page', None) or zobj.getDefaultEditPage();
             x=zobj.setLock(user, page);
             confirmMsg=req.get('confirmMsg', None);
             groupedFields=zobj.getGroupedFields(layoutType,page, cssJs=cssJs);
             x=ztool.patchRequestFromTemplate(zobj, req)">
      <x>:tool.pxPagePrologue</x>
      <!-- Warn the user that the form should be left via buttons -->
      <script type="text/javascript">protectAppyForm()</script>
      <form id="appyForm" name="appyForm" method="post"
            enctype="multipart/form-data" action=":zobj.absolute_url()+'/do'">
       <input type="hidden" name="action" value="Update"/>
       <input type="hidden" name="button" value=""/>
       <input type="hidden" name="popup" value=":inPopup and '1' or '0'"/>
       <input type="hidden" name="page" value=":page"/>
       <input type="hidden" name="nav" value=":req.get('nav', None)"/>
       <input type="hidden" name="confirmed" value="False"/>
       <x var="tagId='pageLayout'; tagName=''; tagCss='';
               layoutTarget=obj">:layout.pxRender</x>
      </form>
      <script type="text/javascript"
              if="confirmMsg">::'askConfirm(%s,%s,%s)' % \
             (q('script'), q('postConfirmedEditForm()'), q(confirmMsg))</script>
      <x>:tool.pxPageBottom</x>
     </x>''', template=pxTemplate, hook='content')

    # PX called via asynchronous requests from the browser. Keys "Expires" and
    # "CacheControl" are used to prevent IE to cache returned pages (which is
    # the default IE behaviour with Ajax requests).
    pxAjax = Px('''
     <x var="zobj=obj.o;    ztool=tool.o;    user=tool.user;
             isAnon=user.login == 'anon';    app=ztool.getApp();
             appFolder=app.data;             url = ztool.getIncludeUrl;
             appName=ztool.getAppName();     _=ztool.translate;
             req=ztool.REQUEST;              resp=req.RESPONSE;
             dummy=setattr(req, 'pxContext', _ctx_);
             lang=ztool.getUserLanguage();   q=ztool.quote;
             action=req.get('action', '');   ajax=True;
             inPopup=req.get('popup') == '1';
             px=req['px'].split(':');
             pxt=ztool.getPxTarget(zobj, px);
             className=pxt.className;
             fieldName=pxt.name;
             field=pxt.field;
             dir=ztool.getLanguageDirection(lang);
             dleft=(dir == 'ltr') and 'left' or 'right';
             dright=(dir == 'ltr') and 'right' or 'left';
             x=resp.setHeader('Content-type', ztool.xhtmlEncoding);
             x=resp.setHeader('Expires', 'Thu, 11 Dec 1975 12:05:00 GMT+2');
             x=resp.setHeader('Content-Language', lang);
             x=resp.setHeader('Cache-Control', 'no-cache')">

      <!-- If an action is defined, execute it on p_zobj or on p_field -->
      <x if="action"
         var2="msg=ztool.executeAjaxAction(action, obj, field) or '';
               x=resp.setHeader('Appy-Message', msg)"></x>

      <!-- Consume and return any session message -->
      <x var="msg=ztool.consumeMessages(unlessRedirect=True)" if="msg"
         var2="x=resp.setHeader('Appy-Message', msg)"></x>

      <!-- Then, call the PX on p_obj or on p_field -->
      <x if="not field">:getattr(obj, px[0])</x>
      <x if="field">:getattr(field, px[-1])</x>
     </x>''')

    # PX called for displaying the content of a single field
    pxField = Px('''
     <x var="field=obj.getField(req['name']);
             layoutType=req.get('layoutType', 'view')">
     <div>:field.pxRender</div></x>
    ''', template=pxTemplate, hook='content')

    # --------------------------------------------------------------------------
    # Class methods
    # --------------------------------------------------------------------------
    @classmethod
    def _getParentAttr(klass, attr):
        '''Gets value of p_attr on p_klass base classes (if this attr exists).
           Scan base classes in the reverse order as Python does. Used by
           classmethod m_getWorkflow below. Scanning base classes in reverse
           order allows user-defined elements to override default Appy
           elements.'''
        i = len(klass.__bases__) - 1
        res = None
        while i >= 0:
            res = getattr(klass.__bases__[i], attr, None)
            if res: return res
            i -= 1

    @classmethod
    def getWorkflow(klass):
        '''Returns the workflow tied to p_klass.'''
        res = klass._getParentAttr('workflow')
        # Return a default workflow if no workflow was found.
        if not res: res = WorkflowAnonymous
        return res

    @classmethod
    def getPageLayouts(klass):
        '''Returns the page layouts for p_klass.'''
        res = klass._getParentAttr('layouts')
        # Return the default page layout if no layout was found.
        if not res: res = defaultPageLayouts
        return res

    @classmethod
    def getIndexes(klass, includeDefaults=True, asList=False):
        '''Returns a dict whose keys are the names of the indexes that are
           applicable to instances of this class, and whose values are the
           (Zope) types of those indexes. If p_asList is True, it returns a
           list of tuples insteadof a dict.'''
        # Start with the standard indexes applicable for any Appy class
        if includeDefaults:
            res = defaultIndexes.copy()
        else:
            res = {}
        # Add the indexed fields found on this class
        for field in klass.__fields__:
            if not field.indexed or \
               (field.name in ('title', 'state', 'SearchableText')): continue
            n = field.name
            indexName = 'get%s%s' % (n[0].upper(), n[1:])
            res[indexName] = field.getIndexType()
            # Add the secondary index if present
            if field.hasSortIndex(): res['%s_sort' % indexName] = 'FieldIndex'
        if asList:
            res = res.items()
            res.sort(key=lambda e: e[0])
        return res

    # --------------------------------------------------------------------------
    # Instance methods
    # --------------------------------------------------------------------------
    def __init__(self, o): self.__dict__['o'] = o
    def appy(self): return self

    def __setattr__(self, name, value):
        field = self.o.getAppyType(name)
        if not field:
            raise AttributeError('Attribute "%s" does not exist.' % name)
        field.store(self.o, value)

    def __getattribute__(self, name):
        '''Gets the attribute named p_name'''
        if name in expressionAttributes: 
            o = self.o
            return eval(expressionAttributes[name])
        # Now, let's try to return a real attribute/method
        res = object.__getattribute__(self, name)
        # If we got an Appy field, return its value for this object
        if isinstance(res, Field):
            o = self.o
            if isinstance(res, Ref):
                return res.getValue(o, noListIfSingleObj=True)
            else:
                return res.getValue(o)
        return res

    def __repr__(self):
        return '<%s at %s>' % (self.klass.__name__, id(self))

    def __cmp__(self, other):
        if other: return cmp(self.id, other.id)
        return 1

    def _getCustomMethod(self, methodName):
        '''See docstring of _callCustom below.'''
        if len(self.__class__.__bases__) > 1:
            # There is a custom user class
            custom = self.__class__.__bases__[-1]
            if custom.__dict__.has_key(methodName):
                return custom.__dict__[methodName]

    def _callCustom(self, methodName, *args, **kwargs):
        '''This wrapper implements some methods like "validate" and "onEdit".
           If the user has defined its own wrapper, its methods will not be
           called. So this method allows, from the methods here, to call the
           user versions.'''
        custom = self._getCustomMethod(methodName)
        if custom: return custom(self, *args, **kwargs)

    def getField(self, name): return self.o.getAppyType(name)

    def getValue(self, name, layoutType='view', formatted=False, language=None):
        '''Gets the possibly p_formatted value of field p_name. If this
           formatting implies translating something, it will be done in
           p_language, or in the user language if not specified. If the "shown"
           value is required instead of the "formatted" value (see methods
           getFormattedValue and getShownValue from class appy.fields.Field),
           use p_formatted="shown" instead of p_formatted=True.'''
        field = self.o.getAppyType(name)
        obj = self.o
        val = field.getValue(obj, name)
        if not formatted: return val
        method = (formatted == 'shown') and 'getShownValue' or \
                                            'getFormattedValue'
        return getattr(field, method)(obj, val, layoutType, language=language)

    def getLabel(self, name, type='field'):
        '''Gets the translated label of field named p_name. If p_type is
           "workflow", p_name denotes a workflow state or transition, not a
           field.'''
        o = self.o
        if type == 'field': return o.translate(o.getAppyType(name).labelId)
        elif type == 'workflow': return o.translate(o.getWorkflowLabel(name))

    def isEmpty(self, name):
        '''Returns True if value of field p_name is considered to be empty'''
        obj = self.o
        field = obj.getAppyType(name)
        return field.isEmptyValue(obj, field.getStoredValue(obj, name))

    def isTemp(self):
        '''Is this object a temporary object being created ?'''
        return self.o.isTemporary()

    def link(self, fieldName, obj, noSecurity=True, executeMethods=True):
        '''This method links p_obj (which can be a list of objects) to this one
           through reference field p_fieldName. For understanding the 2 last
           params, check Ref's m_linkObject's doc.'''
        field = self.getField(fieldName) 
        return field.linkObject(self, obj, noSecurity=noSecurity,
                                executeMethods=executeMethods)

    def unlink(self, fieldName, obj, noSecurity=True, executeMethods=True):
        '''This method unlinks p_obj (which can be a list of objects) from this
           one through reference field p_fieldName. For understanding the 2 last
           params, check Ref's m_unlinkObject's doc.'''
        field = self.getField(fieldName) 
        return field.unlinkObject(self, obj, noSecurity=noSecurity,
                                  executeMethods=executeMethods)

    def sort(self, fieldName, sortKey='title', reverse=False):
        '''Sorts referred elements linked to p_self via p_fieldName according
           to a given p_sortKey which can be:
           - an attribute set on referred objects ("title", by default);
           - a method that will be called on every tied object, will receive
             every such object as unique arg and will return a value that will
             represent its order among all tied objects. This return value will
             then be returned by the standard method given to the "key" param of
             the standard list.sort method;
           - None. If None, default sorting will occur, using the method stored
             in field.insert.
        '''
        refs = getattr(self.o, fieldName, None)
        if not refs: return
        tool = self.tool
        # refs is a PersistentList: param "key" is not available for method
        # "sort". So perform the sort on the real list and then indicate that
        # the persistent list has changed (the ZODB way).
        if not sortKey:
            # Sort according to field.insert
            field = self.getField(fieldName)
            insertMethod = field.insert
            if not insertMethod:
                raise Exception('Param "insert" for Ref field %s is None.' % \
                                fieldName)
            if not callable(insertMethod): insertMethod = insertMethod[1]
            keyMethod = lambda uid: insertMethod(self, tool.getObject(uid))
        elif isinstance(sortKey, basestring):
            # Sort according to p_sortKey
            keyMethod = lambda uid: getattr(tool.getObject(uid), sortKey)
        else:
            # Sort according to a custom method
            keyMethod = lambda uid: sortKey(tool.getObject(uid))
        refs.data.sort(key=keyMethod, reverse=reverse)
        refs._p_changed = 1

    def create(self, fieldNameOrClass, noSecurity=False,
               raiseOnWrongAttribute=True, executeMethods=True,
               initialComment='', **kwargs):
        '''This method creates a new instance of a gen-class.

           If p_fieldNameOrClass is the name of a field, the created object will
           be linked to p_self via this field. If p_fieldNameOrClass is a class
           from the gen-application, it must correspond to a root class: the
           created object will be stored in the main application folder (and no
           link will exist between it and p_self).

           p_kwargs allow to specify values for object fields.
           If p_noSecurity is True, security checks will not be performed.

           If p_raiseOnWrongAttribute is True, if a value from p_kwargs does not
           correspond to a field on the created object, an AttributeError will
           be raised. Else, the value will be silently ignored.

           If p_executeMethods is False, the gen-class's onEdit method, if
           present, will not be called; any other defined method will not be
           called neither (ie, Ref.insert, Ref.beforeLink, Ref.afterLink...).

           p_initialComment will be stored as comment in the initial workflow
           transition.
        '''
        isField = isinstance(fieldNameOrClass, basestring)
        tool = self.tool.o
        # Determine the class of the object to create
        if isField:
            fieldName = fieldNameOrClass
            field = self.o.getAppyType(fieldName)
            portalType = tool.getPortalType(field.klass)
        else:
            klass = fieldNameOrClass
            portalType = tool.getPortalType(klass)
        # Determine object id
        if kwargs.has_key('id'):
            objId = kwargs['id']
            del kwargs['id']
        else:
            objId = tool.generateUid(portalType)
        # Where must I create the object?
        if not isField:
            folder = tool.getPath('/data')
        else:
            folder = self.o.getCreateFolder()
            if not noSecurity:
                # Check that the user can edit this field
                field.checkAdd(self.o)
        # Create the object
        zopeObj = createObject(folder, objId, portalType, tool.getAppName(),
                           noSecurity=noSecurity, initialComment=initialComment)
        appyObj = zopeObj.appy()
        # Set object attributes
        for attrName, attrValue in kwargs.iteritems():
            try:
                setattr(appyObj, attrName, attrValue)
            except AttributeError, ae:
                if raiseOnWrongAttribute: raise ae
        # Call custom early initialization
        if executeMethods and hasattr(appyObj, 'onEditEarly'):
            appyObj.onEditEarly()
        if isField:
            # Link the object to this one
            field.linkObject(self, appyObj, executeMethods=executeMethods)
        # Call custom initialization
        if executeMethods and hasattr(appyObj, 'onEdit'): appyObj.onEdit(True)
        zopeObj.reindex()
        return appyObj

    def createFrom(self, fieldNameOrClass, other, noSecurity=False,
                   executeMethods=True, exclude=(), keepBase=False):
        '''Similar to m_create above, excepted that we will use another object
           (p_other) as base for filling in data for the object to create.
           p_exclude can list fields (by their names) that will not be copied on
           p_other. If p_keepBase is True, basic attributes will be kept on the
           new object: creator and dates "created" and "modified". Else, the
           new object's creator will be the logged user.

           Note that this method does not perform a deep copy: objects linked
           via Ref fields from p_self will be referenced by the clone, but not
           themselves copied.'''
        # Get the field values to set from p_other and store it in a dict.
        # p_other may not be of the same class as p_self.
        params = {}
        for field in other.fields:
            # Skip non persistent fields, back references and p_excluded fields
            if not field.persist or (field.name in exclude) or \
               ((field.type == 'Ref') and field.isBack): continue
            params[field.name] = field.getCopyValue(other.o)
        res = self.create(fieldNameOrClass, noSecurity=noSecurity,
                          raiseOnWrongAttribute=False,
                          executeMethods=executeMethods, **params)
        # Propagate base attributes if required
        if keepBase:
            for name in ('creator', 'created', 'modified'):
                setattr(res.o, name, getattr(other.o, name))
        return res

    def freeze(self, name, template=None, format='pdf', noSecurity=True,
               freezeOdtOnError=True, value=None):
        '''This method freezes the content of Pod or Computed field named
           p_name. In the case of a Pod field, a given p_template may be given
           (indeed, several templates can exist in field.template); the "freeze"
           format may be given in p_format ("pdf" by default). If p_value is not
           None, it is frozen as is instead of recomputing the Pod or Computed
           field value.'''
        field = self.getField(name)
        if field.type == 'Pod':
            return field.freeze(self, template, format, noSecurity=noSecurity,
                                freezeOdtOnError=freezeOdtOnError, upload=value)
        elif field.type == 'Computed':
            return field.freeze(self, value=value)
        else:
            raise Exception('Only Pod and Computed fields can be frozen.')

    def unfreeze(self, name, template=None, format='pdf', noSecurity=True):
        '''This method unfreezes a Pod or Computed field'''
        field = self.getField(name)
        if field.type == 'Pod':
            field.unfreeze(self, template, format, noSecurity=noSecurity)
        elif field.type == 'Computed':
            field.unfreeze(self)
        else:
            raise Exception('Only Pod and Computed fields can be unfrozen.')

    def delete(self):
        '''Deletes myself'''
        self.o.delete()

    def translate(self, label, mapping={}, domain=None, language=None,
                  format='html'):
        '''Check documentation of self.o.translate'''
        return self.o.translate(label, mapping, domain, language=language,
                                format=format)

    def do(self, name, comment='', doAction=True, doHistory=True,
           noSecurity=False, data=None):
        '''Programmatically triggers on p_self a transition named p_name. p_data
           can be a dict that will be included into the history event, if one
           wants to add custom data in the history event.'''
        o = self.o
        wf = o.getWorkflow()
        tr = getattr(wf, name, None)
        if not tr or (tr.__class__.__name__ != 'Transition'):
            raise Exception('Transition "%s" not found.' % name)
        return tr.trigger(name, o, wf, comment, doAction=doAction,
                          doHistory=doHistory, doSay=False,
                          noSecurity=noSecurity, data=data)

    def log(self, message, type='info', noUser=False):
        return self.o.log(message, type, noUser)

    def say(self, message, type='info'): return self.o.say(message, type)

    def normalize(self, s, usage='fileName'):
        '''Returns a version of string p_s whose special chars have been
           replaced with normal chars.'''
        return normalizeString(s, usage)

    def search(self, klass, sortBy='', sortOrder='asc', maxResults=None,
               noSecurity=False, **fields):
        '''Searches objects of p_klass. p_sortBy must be the name of an indexed
           field (declared with indexed=True); p_sortOrder can be "asc"
           (ascending, the defaut) or "desc" (descending); every param in
           p_fields must take the name of an indexed field and take a possible
           value of this field. You can optionally specify a maximum number of
           results in p_maxResults. If p_noSecurity is specified, you get all
           objects, even if the logged user does not have the permission to
           view it.'''
        # Find the content type corresponding to p_klass
        tool = self.tool.o
        contentType = tool.getPortalType(klass)
        # Create the Search object
        search = Search('customSearch', sortBy=sortBy, sortOrder=sortOrder,
                        **fields)
        if not maxResults:
            maxResults = 'NO_LIMIT'
            # If I let maxResults=None, only a subset of the results will be
            # returned by method executeResult.
        res = tool.executeQuery(contentType, search=search,
                                maxResults=maxResults, noSecurity=noSecurity)
        return [o.appy() for o in res.objects]

    def search1(self, *args, **kwargs):
        '''Identical to m_search above, but returns a single result (if any).'''
        res = self.search(*args, **kwargs)
        if res: return res[0]

    def count(self, klass, noSecurity=False, **fields):
        '''Identical to m_search above, but returns the number of objects that
           match the search instead of returning the objects themselves. Use
           this method instead of writing len(self.search(...)).'''
        tool = self.tool.o
        contentType = tool.getPortalType(klass)
        search = Search('customSearch', **fields)
        res = tool.executeQuery(contentType, search=search, brainsOnly=True,
                                noSecurity=noSecurity, maxResults='NO_LIMIT')
        if res: return res._len # It is a LazyMap instance
        else: return 0

    def ids(self, fieldName):
        '''Returns the identifiers of the objects linked to this one via field
           name p_fieldName. WARNING: do not modify this list, it is the true
           list that is stored in the database (excepted if empty). Modifying it
           will probably corrupt the database.'''
        return getattr(self.o.aq_base, fieldName, ())

    def countRefs(self, fieldName):
        '''Counts the number of objects linked to this one via Ref field
           p_fieldName.'''
        uids = getattr(self.o.aq_base, fieldName, None)
        if not uids: return 0
        return len(uids)

    def compute(self, klass, sortBy='', context=None, expression=None,
                noSecurity=False, **fields):
        '''This method, like m_search and m_count above, performs a query on
           objects of p_klass. But in this case, instead of returning a list of
           matching objects (like m_search) or counting elements (like p_count),
           it evaluates, on every matching object, a Python p_expression (which
           may be an expression or a statement), and returns, if needed, a
           result. The result may be initialized through parameter p_context.
           p_expression is evaluated with 2 variables in its context: "obj"
           which is the currently walked object, instance of p_klass, and "ctx",
           which is the context as initialized (or not) by p_context. p_context
           may be used as
              (1) a variable or instance that is updated on every call to
                  produce a result;
              (2) an input variable or instance;
              (3) both.

           The method returns p_context, modified or not by evaluation of
           p_expression on every matching object.

           When you need to perform an action or computation on a lot of
           objects, use this method instead of doing things like
           
                    "for obj in self.search(MyClass,...)"
           '''
        tool = self.tool.o
        contentType = tool.getPortalType(klass)
        search = Search('customSearch', sortBy=sortBy, **fields)
        # Initialize the context variable "ctx"
        ctx = context
        for brain in tool.executeQuery(contentType, search=search, \
                 brainsOnly=True, maxResults='NO_LIMIT', noSecurity=noSecurity):
            # Get the Appy object from the brain
            if noSecurity: method = '_unrestrictedGetObject'
            else: method = 'getObject'
            exec 'obj = brain.%s().appy()' % method
            exec expression
        return ctx

    def reindex(self, fields=None, unindex=False):
        '''Asks a direct object reindexing. In most cases you don't have to
           reindex objects "manually" with this method. When an object is
           modified after some user action has been performed, Appy reindexes
           this object automatically. But if your code modifies other objects,
           Appy may not know that they must be reindexed, too. So use this
           method in those cases.
        '''
        if fields:
            # Get names of indexes from field names
            indexes = []
            for name in fields:
                field = self.getField(name)
                if not field:
                    # The index may be a standard Appy index that does not
                    # correspond to a field.
                    indexes.append(name)
                    continue
                if not field.indexed: continue
                # A field may have 2 different indexes
                iName = field.getIndexName(usage='search')
                indexes.append(iName)
                sName = field.getIndexName(usage='sort')
                if sName != iName: indexes.append(sName)
        else:
            indexes = None
        self.o.reindex(indexes=indexes, unindex=unindex)

    def export(self, at='string', format='xml', include=None, exclude=None):
        '''Creates an "exportable" version of this object. p_format is "xml" by
           default, but can also be "csv". If p_format is:
           * "xml", if p_at is "string", this method returns the XML version,
                    without the XML prologue. Else, (a) if not p_at, the XML
                    will be exported on disk, in the OS temp folder, with an
                    ugly name; (b) else, it will be exported at path p_at.
           * "csv", if p_at is "string", this method returns the CSV data as a
                    string. If p_at is an opened file handler, the CSV line will
                    be appended in it.
           If p_include is given, only fields whose names are in it will be
           included. p_exclude, if given, contains names of fields that will
           not be included in the result.
        '''
        if format == 'xml':
            # Todo: take p_include and p_exclude into account.
            # Determine where to put the result
            toDisk = (at != 'string')
            if toDisk and not at:
                at = getOsTempFolder() + '/' + self.o.id + '.xml'
            # Create the XML version of the object
            marshaller = XmlMarshaller(cdata=True, dumpUnicode=True,
                                       dumpXmlPrologue=toDisk,
                                       rootTag=self.klass.__name__)
            xml = marshaller.marshall(self.o, objectType='appy')
            # Produce the desired result
            if toDisk:
                f = file(at, 'w')
                f.write(xml.encode('utf-8'))
                f.close()
                return at
            else:
                return xml
        elif format == 'csv':
            if isinstance(at, basestring):
                marshaller = CsvMarshaller(include=include, exclude=exclude)
                return marshaller.marshall(self)
            else:
                marshaller = CsvMarshaller(at, include=include, exclude=exclude)
                marshaller.marshall(self)

    def historize(self, data):
        '''This method allows to add "manually" a "data-change" event into the
           object's history. Indeed, data changes are "automatically" recorded
           only when an object is edited through the edit form, not when a
           setter is called from the code.

           p_data must be a dictionary whose keys are field names (strings) and
           whose values are the previous field values.'''
        self.o.addDataChange(data)

    def getLastEvent(self, transition, notBefore=None, history=None):
        '''Gets, from the object history (or from p_history if not None), the
           last occurrence of transition named p_transition. p_transition can be
           a list of names: in this case, it returns the most recent occurrence
           of those transitions. If p_notBefore is given, it corresponds to a
           kind of start transition for the search: we will not search in the
           history preceding the last occurrence of this transition. Note that
           p_notBefore can hold a list of transitions.'''
        history = history or self.history
        i = len(history) - 1
        while i >= 0:
            event = history[i]
            if notBefore:
                if isinstance(notBefore, str):
                    condition = event['action'] == notBefore
                else:
                    condition = event['action'] in notBefore
                if condition: return
            if isinstance(transition, str):
                condition = event['action'] == transition
            else:
                condition = event['action'] in transition
            if condition: return event
            i -= 1

    def getEvents(self, action):
        '''Gets a subset of history events, whose action is p_action (if
           p_action is a string) or is within p_action (if p_action is a list
           of actions.'''
        res = []
        single = isinstance(action, str)
        for event in self.history:
            if single:
                condition = event['action'] == action
            else:
                condition = event['action'] in action
            if condition:
                res.append(event)
        return res

    def getHistoryComments(self, transition, xhtml=False):
        '''Gets the concatenation of all comments for all transitions of type
           p_transition in the object history.'''
        res = []
        for event in self.history:
            if event['action'] != transition: continue
            if not event['comments']: continue
            res.append(event['comments'])
        br = xhtml and '<br/>' or '\n'
        return br.join(res)

    def removeEvent(self, event):
        '''Removes p_event from this object's history'''
        res = []
        # Because data change events carry the workflow state, we must ensure
        # that, after having removed p_event, this workflow state is still
        # correct.
        lastState = None
        for e in self.history:
            action = e['action']
            # Ignore this event if it is p_event
            if (action == event['action']) and (e['time'] == event['time']):
                continue
            if action and action.startswith('_data'):
                e['review_state'] = lastState
            res.append(e)
            lastState = e['review_state']
        self.o.workflow_history['appy'] = tuple(res)

    def formatText(self, text, format='html'):
        '''Produces a representation of p_text into the desired p_format, which
           is 'html' by default.'''
        return self.o.formatText(text, format)

    def listStates(self):
        '''Lists the possible states for this object'''
        res = []
        o = self.o
        workflow = o.getWorkflow()
        for name in dir(workflow):
            state = getattr(workflow, name)
            if state.__class__.__name__ != 'State': continue
            # Ignore the state if it is isolated
            if state.isIsolated(workflow): continue
            res.append((name, o.translate(o.getWorkflowLabel(name))))
        return res

    def path(self, name):
        '''Returns the absolute file name of file stored in File field p_named
           p_name.'''
        v = getattr(self, name)
        if v: return v.getFilePath(self)

    def getIndexOf(self, name, obj):
        '''Returns, as an integer starting at 0, the position of p_obj within
           objects linked to p_self via field p_name.'''
        o = self.o
        return o.getAppyType(name).getIndexOf(o, obj.id)

    def allows(self, permission, raiseError=False):
        '''Check doc @Mixin.allows'''
        return self.o.allows(permission, raiseError=raiseError)

    def resetLocalRoles(self, setOwner=True):
        '''Removes all local roles defined on this object, excepted local role
           Owner (if p_setOwner is True), granted to the item creator.'''
        from persistent.mapping import PersistentMapping
        localRoles = PersistentMapping()
        if setOwner: localRoles[self.o.creator] = ['Owner']
        self.o.__ac_local_roles__ = localRoles
        return localRoles

    def addLocalRole(self, login, role, reindex=False):
        '''Grants to some p_login (or several if p_login is a list/tuple) a
           given local p_role (or several if p_role is a list/tuple)

           Do not forget that security information for any object is indexed. So
           if the object being modified (p_self) is not the main object of a ui
           transaction (ie, not triggered within m_onEdit), you should ask to
           reindex the object (set p_reindex to True).
        '''
        if not login or not role: raise Exception('Empty login or role.')
        self.o._checkLocalRoles()
        localRoles = self.o.__ac_local_roles__
        if isinstance(login, str): login = (login,)
        if isinstance(role, str): role = (role,)
        for l in login:
            # Get or create the list of local roles for this login 
            if l not in localRoles:
                roles = []
            else:
                roles = list(localRoles[l])
            for r in role:
                if r not in roles: roles.append(r)
            localRoles[l] = roles
        # Reindex the security-related index if required
        if reindex: self.reindex(fields=('Allowed',))

    def deleteLocalRole(self, login=None, role=None, reindex=False):
        '''Ungrants, for a given p_login, some local p_role.
        
           If p_login is None, is ungrants p_role for every login mentioned in
           local roles. If p_login is a list/tuple, it ungrants p_role to those
           p_logins.

           If p_role is None, it ungrants all previously granted roles to
           p_login. If p_role is a list/tuple, if ungrants those roles to
           p_login.

           For parameter p_reindex, same remark as for m_addLocalRole.
        '''
        if not login and not role: raise Exception('Empty login and role')
        self.o._checkLocalRoles()
        localRoles = self.o.__ac_local_roles__
        if not role:
            # Ungrant to p_login every previously granted role
            if isinstance(login, str): login = (login,)
            for l in login:
                if l in localRoles: del localRoles[l]
        else:
            # To what login(s) must we ungrant p_role(s) ?
            if not login:
                # To anyone having local roles on this object
                login = localRoles.keys()
            # Else: to the login(s) specified in p_login
            elif isinstance(login, str): login = (login,)
            # Ungrant roles
            if isinstance(role, str): role = (role,)
            for l in login:
                if l not in localRoles: continue
                updated = False
                lRoles = localRoles[l]
                for r in role:
                    if r in lRoles:
                        lRoles.remove(r)
                        updated = True
                if updated:
                    # Local roles have been updated for this login.
                    if not lRoles:
                        del localRoles[l]
                    else:
                        localRoles[l] = list(lRoles)
        # Reindex the security-related index if required
        if reindex: self.reindex(fields=('Allowed',))

    def raiseUnauthorized(self, msg=None): return self.o.raiseUnauthorized(msg)

    def sendMailIf(self, privilege, subject, body, attachments=None,
                   privilegeType='permission', excludeExpression='False'):
        '''Sends a mail related to this object to any active user having
           p_privilege on it. If p_privilegeType is:
           - "permission", p_privilege is a (list or tuple of) permission(s);
           - "role",       p_privilege is a (list or tuple of) role(s);
           - "group",      p_privilege is a group login;
           - "user",       p_privilege is a user login.

           p_excludeExpression will be evaluated on every selected user. Users
           for which the expression will produce True will not become mail
           recipients. The expression is evaluated with variable "user" in its
           context.
        '''
        # Determine the set of users to work with
        checkPermissionOrRole = False
        if privilegeType == 'user':
            user = self.search1('User', noSecurity=True, login=privilege)
            if not user:
                raise Exception('user "%s" does not exist.' % privilege)
            users = [user]
        elif privilegeType == 'group':
            # Get the users belonging to this group
            group = self.search1('Group', noSecurity=True, login=privilege)
            if not group:
                raise Exception('group "%s" does not exist.' % privilege)
            users = group.users
        else:
            # Get all users
            users = self.tool.users
            checkPermissionOrRole = True
        # Determine the list of recipients based on active users having
        # p_privilege on p_self.
        recipients = []
        for user in users:
            if (user.state == 'inactive') or eval(excludeExpression): continue
            # Check if the user has p_privilege on this object (only applicable
            # if the privilege does not represent a group).
            if checkPermissionOrRole:
                hasPrivilege = (privilegeType == 'permission') and \
                               user.has_permission or user.has_role
                if isinstance(privilege, str):
                    # Check a single permission or role
                    if not hasPrivilege(privilege, self): continue
                else:
                    # Several permissions or roles are mentioned. Having a
                    # single permission or role is sufficient.
                    hasOne = False
                    for priv in privilege:
                        if hasPrivilege(priv, self):
                            hasOne = True
                            break
                    if not hasOne: continue
            # Get the mail recipient for this user
            recipient = user.getMailRecipient()
            if not recipient: continue
            recipients.append(recipient)
        if recipients:
            self.tool.sendMail(recipients, subject, body, attachments)
        else:
            self.log('no recipient for sending mail about %s with %s %s.' % \
                     (self.id, privilegeType, privilege))
# ------------------------------------------------------------------------------
