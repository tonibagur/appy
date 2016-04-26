# ------------------------------------------------------------------------------
# This file is part of Appy, a framework for building applications in the Python
# language. Copyright (C) 2007 Gaetan Delannay

# Appy is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.

# Appy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with
# Appy. If not, see <http://www.gnu.org/licenses/>.

# ------------------------------------------------------------------------------
from appy.px import Px
from appy.gen import utils as gutils

# Error messages ---------------------------------------------------------------
TABS_COLUMNS_ERROR = 'A tabs-style group must have a single column.'
GRID_COLUMNS_ERROR = 'For a grid-style group, you must specify an even number ' \
  'of columns, in order to produce couples of label/field columns. For every ' \
  'couple, the first columns holds a field label and the second one holds ' \
  'the field content.'

# ------------------------------------------------------------------------------
class Group:
    '''Used for describing a group of fields within a page'''
    def __init__(self, name, columns=None, wide=True, style='section2',
                 hasLabel=True, hasDescr=False, hasHelp=False,
                 hasHeaders=False, group=None, colspan=1, align='center',
                 valign='top', css_class='', labelCss=None, master=None,
                 masterValue=None, cellpadding=1, cellspacing=1,
                 cellgap='0.6em', label=None, translated=None):
        self.name = name
        # In its simpler form, field "columns" below can hold a list or tuple
        # of column widths expressed as strings, that will be given as is in
        # the "width" attributes of the corresponding "td" tags. Instead of
        # strings, within this list or tuple, you may give Column instances
        # (see below).
        self.columns = columns
        self._setColumns(style)
        # If field "wide" below is True, the HTML table corresponding to this
        # group will have width 100%. You can also specify some string value,
        # which will be used for HTML param "width".
        if wide == True:
            self.wide = '100%'
        elif isinstance(wide, basestring):
            self.wide = wide
        else:
            self.wide = ''
        # Groups of various styles can be rendered. If "style" is:
        # - 'sectionX'  (X can be 1, 2, 3...) 
        #               the group will be rendered as a "section": the group
        #               title will be rendered in some style (depending on X)
        #               before the widgets;
        # - 'fieldset'  all widgets within the group will be rendered within an
        #               HTML fieldset;
        # - 'tabs'      the group will be rendered as tabs. One tab will be
        #               rendered for every inner widget. If you want some tab to
        #               contain several widgets, specify a group as sub-group of
        #               the group having style 'tabs';
        # - 'grid'      the widgets will be rendered in some standardized,
        #               tabular way.
        self.style = style
        # If hasLabel is True, the group will have a name and the corresponding
        # i18n label will be generated.
        self.hasLabel = hasLabel
        # If hasDescr is True, the group will have a description and the
        # corresponding i18n label will be generated.
        self.hasDescr = hasDescr
        # If hasHelp is True, the group will have a help text associated and the
        # corresponding i18n label will be generated.
        self.hasHelp = hasHelp
        # If hasheaders is True, group content will begin with a row of headers,
        # and a i18n label will be generated for every header.
        self.hasHeaders = hasHeaders
        self.nbOfHeaders = len(self.columns)
        # If this group is himself contained in another group, the following
        # attribute is filled.
        self.group = Group.get(group)
        # If the group is rendered into another group, we can specify the number
        # of columns that this group will span.
        self.colspan = colspan
        self.align = align
        self.valign = valign
        self.cellpadding = cellpadding
        self.cellspacing = cellspacing
        # Beyond standard cellpadding and cellspacing, cellgap can define an
        # additional horizontal gap between cells in a row. So this value does
        # not add space before the first cell or after the last one.
        self.cellgap = cellgap
        if style == 'tabs':
            # Group content will be rendered as tabs. In this case, some
            # param combinations have no sense.
            self.hasLabel = self.hasDescr = self.hasHelp = False
            # Inner field/group labels will be used as tab labels
        # "css_class", if specified, will be applied to the whole group
        self.css_class = css_class
        # "labelCss" is the CSS class that will be applied to the group label
        self._setLabelCss(labelCss, style)
        self.master = master
        self.masterValue = gutils.initMasterValue(masterValue)
        if master: master.slaves.append(self)
        self.label = label # See similar attr of Type class
        # If a translated name is already given here, we will use it instead of
        # trying to translate the group label.
        self.translated = translated

    def _setColumns(self, style):
        '''Standardizes field "columns" as a list of Column instances. Indeed,
           the initial value for field "columns" may be a list or tuple of
           Column instances or strings.'''
        # Start with a default value, if self.columns is None
        if not self.columns:
            if style == 'grid':
                # One column for the labels, another for the remaining elements
                self.columns = ['150em', '']
            else:
                self.columns = ['100%']
        # Standardize columns as a list of Column instances
        for i in range(len(self.columns)):
            columnData = self.columns[i]
            if not isinstance(columnData, Column):
                self.columns[i] = Column(self.columns[i])
        # Standardize or check columns depending on group style
        if style == 'tabs':
            # There must be a unique column
            if len(self.columns) > 1: raise Exception(TABS_COLUMNS_ERROR)
        elif style == 'grid':   
            # grid has always an even number of columns (couples of label/field
            # columns)
            if len(self.columns)%2: raise Exception(GRID_COLUMNS_ERROR)

    def _setLabelCss(self, labelCss, style):
        '''For "sectionX"-style groups, the applied CSS class is by default the
           p_style itself. For the other styles of groups (tabs, grids,...) it
           is not the case.'''
        if labelCss:
            self.labelCss = labelCss
        else:
            # Set a default value for the label CSS
            if style.startswith('section'):
                self.labelCss = style
            else:
                self.labelCss = 'section3'

    @staticmethod
    def get(groupData):
        '''Produces a Group instance from p_groupData. User-defined p_groupData
           can be a string or a Group instance; this method returns always a
           Group instance.'''
        res = groupData
        if res and isinstance(res, basestring):
            # Group data is given as a string. 2 more possibilities:
            # (a) groupData is simply the name of the group;
            # (b) groupData is of the form <groupName>_<numberOfColumns>.
            groupElems = groupData.rsplit('_', 1)
            if len(groupElems) == 1:
                res = Group(groupElems[0])
            else:
                try:
                    nbOfColumns = int(groupElems[1])
                except ValueError:
                    nbOfColumns = 1
                width = 100.0 / nbOfColumns
                res = Group(groupElems[0], ['%.2f%%' % width] * nbOfColumns)
        return res

    def getMasterData(self):
        '''Gets the master of this group (and masterValue) or, recursively, of
           containing groups when relevant.'''
        if self.master: return self.master, self.masterValue
        if self.group: return self.group.getMasterData()

    def generateLabels(self, messages, classDescr, walkedGroups,
                       content='fields'):
        '''This method allows to generate all the needed i18n labels related to
           this group. p_messages is the list of i18n p_messages (a PoMessages
           instance) that we are currently building; p_classDescr is the
           descriptor of the class where this group is defined. The type of
           content in this group is specified by p_content.'''
        # A part of the group label depends on p_content
        gp = (content == 'searches') and 'searchgroup' or 'group'
        if self.hasLabel:
            msgId = '%s_%s_%s' % (classDescr.name, gp, self.name)
            messages.append(msgId, self.name)
        if self.hasDescr:
            msgId = '%s_%s_%s_descr' % (classDescr.name, gp, self.name)
            messages.append(msgId, ' ', nice=False)
        if self.hasHelp:
            msgId = '%s_%s_%s_help' % (classDescr.name, gp, self.name)
            messages.append(msgId, ' ', nice=False)
        if self.hasHeaders:
            for i in range(self.nbOfHeaders):
                msgId = '%s_%s_%s_col%d' % (classDescr.name, gp, self.name, i+1)
                messages.append(msgId, ' ', nice=False)
        walkedGroups.add(self)
        if self.group and (self.group not in walkedGroups) and \
           not self.group.label:
            # We remember walked groups for avoiding infinite recursion
            self.group.generateLabels(messages, classDescr, walkedGroups,
                                      content=content)

    def insertInto(self, elems, uiGroups, page, className, content='fields'):
        '''Inserts the UiGroup instance corresponding to this Group instance
           into p_elems, the recursive structure used for displaying all
           elements in a given p_page (fields, searches, transitions...) and
           returns this UiGroup instance.'''
        # First, create the corresponding UiGroup if not already in p_uiGroups
        if self.name not in uiGroups:
            uiGroup = uiGroups[self.name] = UiGroup(self, page, className,
                                                    content=content)
            # Insert the group at the higher level (ie, directly in p_elems)
            # if the group is not itself in a group.
            if not self.group:
                elems.append(uiGroup)
            else:
                outerGroup = self.group.insertInto(elems, uiGroups, page,
                                                   className, content=content)
                outerGroup.addElement(uiGroup)
        else:
            uiGroup = uiGroups[self.name]
        return uiGroup

class Column:
    '''Used for describing a column within a Group like defined above'''
    def __init__(self, width, align="left"):
        self.width = width
        self.align = align

class UiGroup:
    '''On-the-fly-generated data structure that groups all elements
       (fields, searches, transitions...) sharing the same Group instance, that
       the currently logged user can see.'''

    # Render a help icon for a group
    pxHelp = Px('''<acronym title="obj.translate('help', field=field)"><img
     src=":url('help')"/></acronym>''')

    # Render the group title, description and help
    pxHeader = Px('''
     <!-- Title -->
     <tr><td colspan=":len(field.columnsWidths)" class=":field.labelCss"
             align=":dleft">
       <x>::_(field.labelId)</x><x if="field.hasHelp">:field.pxHelp</x>
      </td>
     </tr>
     <tr if="field.hasDescr">
      <td colspan=":len(field.columnsWidths)"
          class="discreet">::_(field.descrId)</td>
     </tr>''')

    # Render the fields within a group in the most frequent cases:
    # style = "sectionX" or "fieldset". The group is referred as var "field".
    pxFields = Px('''
     <table var="cellgap=field.cellgap" width=":field.wide"
            align=":ztool.flipLanguageDirection(field.align, dir)"
            id=":tagId" name=":tagName" class=":groupCss"
            cellspacing=":field.cellspacing" cellpadding=":field.cellpadding">
      <!-- Title, description and help -->
      <x if="field.showHeader()">:field.pxHeader</x>
      <!-- The column headers -->
      <tr>
       <th for="colNb in range(len(field.columnsWidths))"
           align=":ztool.flipLanguageDirection(field.columnsAligns[colNb], dir)"
           width=":field.columnsWidths[colNb]">::field.hasHeaders and \
            _('%s_col%d' % (field.labelId, (colNb+1))) or ''</th>
      </tr>
      <!-- The rows of widgets -->
      <tr valign=":field.valign" for="row in field.elements">
       <td for="field in row" colspan=":field.colspan|1"
           style=":not loop.field.last and ('padding-right:%s'% cellgap) or ''">
        <x if="field">
         <x if="field.type == 'group'">:field.pxView</x>
         <x if="field.type != 'group'">:field.pxRender</x>
        </x>
       </td>
      </tr>
     </table>''')

    # Render a group with style = 'fieldset'
    pxFieldset = Px('''
     <fieldset>
      <legend if="field.hasLabel">
       <i>::_(field.labelId)></i><x if="field.hasHelp">:field.pxHelp</x>
      </legend>
      <div if="field.hasDescr" class="discreet">::_(field.descrId)</div>
      <x>:field.pxFields</x>
     </fieldset>''')

    # Render a group with style = 'tabs'
    pxTabs = Px('''
     <x var="tabsCount=len(field.elements)">
      <table width=":field.wide" class=":groupCss" id=":tagId" name=":tagName">
       <!-- First row: the tabs -->
       <tr valign="middle"><td style="border-bottom: 1px solid #ff8040">
        <table class="tabs" cellpadding="0" cellspacing="0">
         <tr valign="middle">
          <x for="sub in field.elements"
             var2="nb = loop.sub.nb + 1;
                   suffix='%s_%d_%d' % (field.name, nb, tabsCount);
                   tabId='tab_%s' % suffix">
           <td><img src=":url('tabLeft')" id=":'%s_left' % tabId"/></td>
           <td style=":url('tabBg', bg=True)" class="tab" id=":tabId">
            <a onclick=":'showTab(%s)' % q(suffix)"
               class="clickable">:_(sub.labelId)</a>
           </td>
           <td><img id=":'%s_right' % tabId" src=":url('tabRight')"/></td>
          </x>
         </tr>
        </table>
       </td></tr>

       <!-- Other rows: the fields -->
       <tr for="sub in field.elements"
           var2="nb=loop.sub.nb + 1"
           id=":'tabcontent_%s_%d_%d' % (field.name, nb, tabsCount)"
           style=":(nb == 1) and 'display:table-row' or 'display:none'">
        <td var="field=sub">:field.pxRender</td>
       </tr>
      </table>
      <script type="text/javascript">:'initTab(%s,%s)' % \
       (q('tab_%s' % field.name), q('%s_1_%d' % (field.name, tabsCount)))
      </script>
     </x>''')

    pxGrid = Px('''
     <table cellpadding="0" cellspacing="0" width=":field.wide"
            class=":groupCss" id=":tagId" name=":tagName">
      <!-- Title, description and help -->
      <x if="field.showHeader()">:field.pxHeader</x>
      <tr><th for="col in field.columns" width=":col.width"></th></tr>
      <tr for="row in field.elements" valign="top"
          class=":loop.row.odd and 'odd' or 'even'">
       <x for="sub in row">
        <td id="summaryCell">
         <label if="sub.hasLabel and \
                    (sub.type != 'Action')">::_('label', field=sub)</label></td>
        <td var="field=sub"
            id="summaryCell" class="smaller">:field.pxRender</td>
       </x>
      </tr>
     </table>''')

    # PX that renders a group of fields (the group is referred as var "field")
    pxView = Px('''
     <x var="tagCss=field.master and ('slave*%s*%s' % \
                    (field.masterName, '*'.join(field.masterValue))) or '';
             widgetCss=field.css_class;
             groupCss=tagCss and ('%s %s' % (tagCss, widgetCss)) or widgetCss;
             tagName=field.master and 'slave' or '';
             tagId='%s_%s' % (zobj.id, field.name)">:field.pxFromStyle()</x>''')
    pxRender = pxView

    # PX that renders a group of searches
    pxViewSearches = Px('''
     <x var="collapse=field.getCollapseInfo(field.labelId, req)">
      <!-- Group name, prefixed by the expand/collapse icon -->
      <div class="portletGroup"><x>:collapse.px</x>
       <x if="not field.translated">:_(field.labelId)</x>
       <x if="field.translated">:field.translated</x>
      </div>
      <!-- Group content -->
      <div id=":collapse.id" style=":'padding-left: 10px; %s' % collapse.style">
       <x for="searches in field.elements">
        <x for="elem in searches">
         <!-- An inner group within this group -->
         <x if="elem.type== 'group'" var2="field=elem">:field.pxViewSearches</x>
         <!-- A search -->
         <x if="elem.type!= 'group'" var2="search=elem">:search.pxView</x>
        </x>
       </x>
      </div></x>''')

    # PX that renders a group of transitions
    pxViewTransitions = Px('''
     <!-- Render a group of transitions, as a one-column table -->
     <table>
      <x for="row in uiGroup.elements">
       <x for="transition in row"><tr><td>:transition.pxView</td></tr></x>
      </x>
     </table>''')

    # What PX to use, depending on group content?
    pxByContent = {'fields': pxView, 'searches': pxViewSearches,
                   'transitions': pxViewTransitions}

    def __init__(self, group, page, className, content='fields'):
        '''A UiGroup can group various kinds of elements: fields, searches,
           transitions..., The type of content that one may find in this group
           is given in p_content.
           * p_group      is the Group instance corresponding to this UiGroup;
           * p_page       is the Page instance where the group is rendered (for
                          transitions, it corresponds to a virtual page
                          "workflow");
           * p_className  is the name of the class that holds the elements to
                          group.'''
        self.type = 'group'
        # All p_group attributes become self attributes. This is required
        # because a UiGroup, in some PXs, must behave like a Field (ie, have
        # the same attributes, like "master".
        for name, value in group.__dict__.iteritems():
            if not name.startswith('_'):
                setattr(self, name, value)
        self.group = group
        self.columnsWidths = [col.width for col in group.columns]
        self.columnsAligns = [col.align for col in group.columns]
        # Names of i18n labels for this group
        labelName = self.name
        prefix = className
        if group.label:
            if isinstance(group.label, basestring): prefix = group.label
            else: # It is a tuple (className, name)
                if group.label[1]: labelName = group.label[1]
                if group.label[0]: prefix = group.label[0]
        gp = (content == 'searches') and 'searchgroup' or 'group'
        self.labelId = '%s_%s_%s' % (prefix, gp, labelName)
        self.descrId = self.labelId + '_descr'
        self.helpId  = self.labelId + '_help'
        # The name of the page where the group lies
        self.page = page.name
        # The elements (fields or sub-groups) contained in the group, that the
        # current user may see. They will be inserted by m_addElement below.
        self.flatElements = self.style == 'tabs'
        if self.flatElements:
            # Elements will be stored as a simple list
            self.elements = []
        else:
            # In most cases, "elements" will be a list of lists for rendering
            # them as a table.
            self.elements = [[]]
        # PX to use for rendering this group
        self.px = self.pxByContent[content]

    def addElement(self, element):
        '''Adds p_element into self.elements. We try first to add p_element into
           the last row. If it is not possible, we create a new row.'''
        if self.flatElements:
            self.elements.append(element)
            return
        # Get the last row
        lastRow = self.elements[-1]
        numberOfColumns = len(self.columnsWidths)
        # Grid groups span a single field on 2 columns
        if self.style == 'grid': numberOfColumns = numberOfColumns / 2
        # Compute the number of columns already filled in the last row
        filledColumns = 0
        for rowElem in lastRow: filledColumns += rowElem.colspan
        freeColumns = numberOfColumns - filledColumns
        if freeColumns >= element.colspan:
            # We can add the element in the last row
            lastRow.append(element)
        else:
            if freeColumns:
                # Terminate the current row by appending empty cells
                for i in range(freeColumns): lastRow.append('')
            # Create a new row
            self.elements.append([element])

    def getCollapseInfo(self, id, request):
        '''Returns a Collapsible instance, that determines if this group,
           represented as an expandable menu item, is collapsed or expanded.'''
        return gutils.Collapsible(id, request)

    def pxFromStyle(self):
        '''Get the PX to use for rendering a group, depending on its style'''
        style = self.style
        if style[-1].isdigit(): return self.pxFields # sectionX
        px = 'px%s' % style.capitalize()
        return getattr(self, px)

    def showHeader(self):
        '''The block "title, description, help" must not be rendered even if it
           exists, because it is rendered elsewhere.'''
        if self.style == 'fieldset': return
        parent = self.group.group
        if parent and (parent.style == 'tabs'): return
        return self.hasLabel
# ------------------------------------------------------------------------------
