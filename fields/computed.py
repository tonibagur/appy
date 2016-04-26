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
from appy.fields import Field
from appy.px import  Px

# Error messages ---------------------------------------------------------------
UNFREEZABLE = 'This field is unfreezable.'

# ------------------------------------------------------------------------------
class Computed(Field):
    # Some layouts that could apply to computed fields. Standard layouts could
    # not render correctly because the computed field may produce a chunk of
    # HTML implying a subsequent carriage return (as is the case for a 'table',
    # 'div' or 'p' tag for instance).
    gdLayouts = 'f-drvl' # For fields within a grid group, with description
    gdhLayouts = 'f-dhrvl' # Idem, but with a help icon

    WRONG_METHOD = 'Wrong value "%s". Param "method" must contain a method ' \
                   'or a PX.'
    pxView = pxCell = pxEdit = Px('''<x if="field.plainText">:value</x>
      <x if="not field.plainText">::value</x>''')

    pxSearch = Px('''
     <input type="text" name=":'%s*string' % widgetName"
            maxlength=":field.maxChars" size=":field.width"
            value=":field.sdefault"/>''')

    def __init__(self, multiplicity=(0,1), default=None, show=None, page='main',
      group=None, layouts=None, move=0, indexed=False, mustIndex=True,
      searchable=False, specificReadPermission=False,
      specificWritePermission=False, width=None, height=None, maxChars=None,
      colspan=1, method=None, formatMethod=None, plainText=False, master=None,
      masterValue=None, focus=False, historized=False, mapping=None, label=None,
      sdefault='', scolspan=1, swidth=None, sheight=None, context=None,
      view=None, xml=None, unfreezable=False, validable=False):
        # The Python method used for computing the field value, or a PX
        self.method = method
        # A specific method for producing the formatted value of this field.
        # This way, if, for example, the value is a DateTime instance which is
        # indexed, you can specify in m_formatMethod the way to format it in
        # the user interface while m_method computes the value stored in the
        # catalog.
        self.formatMethod = formatMethod
        if isinstance(self.method, basestring):
            # A legacy macro identifier. Raise an exception
            raise Exception(self.WRONG_METHOD % self.method)
        # Does field computation produce plain text or XHTML?
        self.plainText = plainText
        if isinstance(method, Px):
            # When field computation is done with a PX, the result is XHTML
            self.plainText = False
        # Determine default value for "show"
        if show == None:
            # XHTML content in a Computed field generally corresponds to some
            # custom XHTML widget. This is why, by default, we do not render it
            # in the xml layout.
            show = self.plainText and ('view', 'result', 'xml') or \
                                      ('view', 'result')
        # If method is a PX, its context can be given in p_context
        self.context = context
        Field.__init__(self, None, multiplicity, default, show, page, group,
                       layouts, move, indexed, mustIndex, searchable,
                       specificReadPermission, specificWritePermission, width,
                       height, None, colspan, master, masterValue, focus,
                       historized, mapping, label, sdefault, scolspan, swidth,
                       sheight, False, False, view, xml)
        # When a custom widget is built from a computed field, its values are
        # potentially editable an validable, so "validable" must be True.
        self.validable = validable
        # One classic use case for a Computed field is to build a custom widget.
        # In this case, self.method stores a PX or method that produces, on
        # view or edit, the custom widget. Logically, you will need to store a
        # custom data structure on obj.o, in an attribute named according to
        # this field, ie self.name. Typically, you will set or update a value
        # for this attribute in obj.onEdit, by getting, on the obj.request
        # object, values encoded by the user in your custom widget (edit mode).
        # This "custom widget" use case is incompatible with "freezing". Indeed,
        # freezing a Computed field implies storing the computed value at
        # obj.o.[self.name] instead of recomputing it as usual. So if you want
        # to build a custom widget, specify the field as being unfreezable.
        self.unfreezable = unfreezable

    def getValue(self, obj, name=None, forceCompute=False):
        '''Computes the field value on p_obj or get it from the database if it
           has been frozen.'''
        # Is there a database value ?
        if not self.unfreezable and not forceCompute:
            res = obj.__dict__.get(self.name, None)
            if res != None: return res
        # Compute the value
        if not self.method: return
        if isinstance(self.method, Px):
            obj = obj.appy()
            tool = obj.tool
            req = obj.request
            # Get the context of the currently executed PX if present
            try:
                ctx = req.pxContext
            except AttributeError:
                # Create some standard context
                ctx = {'obj': obj, 'zobj': obj.o, 'field': self,
                       'req': req, 'tool': tool, 'ztool': tool.o,
                       '_': tool.translate, 'url': tool.o.getIncludeUrl}
            if self.context: ctx.update(self.context)
            return self.method(ctx)
        else:
            # self.method is a method that will return the field value
            return self.callMethod(obj, self.method, cache=False)

    def getFormattedValue(self, obj, value, layoutType='view',
                          showChanges=False, language=None):
        if self.formatMethod:
            res = self.formatMethod(obj, value)
        else:
            res = value
        if not isinstance(res, basestring): res = str(res)
        return res

    # If you build a custom widget with a Computed field, Appy can't tell if the
    # value in your widget is complete or not. So it returns True by default.
    # It is up to you, in method obj.validate, to perform a complete validation,
    # including verifying if there is a value if your field is required.
    def isCompleteValue(self, obj, value): return True

    def freeze(self, obj, value=None):
        '''Normally, no field value is stored for a Computed field: the value is
           compued on-the-fly by self.method. But if you freeze it, a value is
           stored: either p_value if not None, or the result of calling
           self.method else. Once a Computed field value has been frozen,
           everytime its value will be requested, the frozen value will be
           returned and self.method will not be called anymore. Note that the
           frozen value can be unfrozen (see method below).'''
        if self.unfreezable: raise Exception(UNFREEZABLE)
        obj = obj.o
        # Compute for the last time the field value if p_value is None
        if value == None: value = self.getValue(obj, forceCompute=True)
        # Freeze the given or computed value (if not None) in the database
        if value != None: setattr(obj, self.name, value)

    def unfreeze(self, obj):
        '''Removes the database value that was frozen for this field on p_obj'''
        if self.unfreezable: raise Exception(UNFREEZABLE)
        obj = obj.o
        if hasattr(obj.aq_base, self.name): delattr(obj, self.name)
# ------------------------------------------------------------------------------
