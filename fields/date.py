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
import time
from appy.fields import Field
from appy.px import Px

# ------------------------------------------------------------------------------
def getDateFromIndexValue(indexValue):
    '''p_indexValue is the internal representation of a date as stored in the
       zope Date index (see "_convert" method in DateIndex.py in
       Products.pluginIndexes/DateIndex). This function produces a DateTime
       based on it.'''
    # p_indexValue represents a number of minutes
    minutes = indexValue % 60
    indexValue = (indexValue-minutes) / 60 # The remaining part, in hours
    # Get hours
    hours = indexValue % 24
    indexValue = (indexValue-hours) / 24 # The remaining part, in days
    # Get days
    day = indexValue % 31
    if day == 0: day = 31
    indexValue = (indexValue-day) / 31 # The remaining part, in months
    # Get months
    month = indexValue % 12
    if month == 0: month = 12
    year = (indexValue - month) / 12
    from DateTime import DateTime
    utcDate = DateTime('%d/%d/%d %d:%d UTC' % (year,month,day,hours,minutes))
    return utcDate.toZone(utcDate.localZone())

# ------------------------------------------------------------------------------
class Date(Field):

    pxView = pxCell = Px('''<x>:value</x>''')
    pxEdit = Px('''
     <x var="years=field.getSelectableYears()">
      <!-- Day -->
      <select var="days=range(1,32)" if="field.showDay"
              name=":'%s_day' % name" id=":'%s_day' % name">
       <option value="">-</option>
       <option for="day in days"
               var2="zDay=str(day).zfill(2)" value=":zDay"
               selected=":field.isSelected(zobj, 'day', day, \
                                           rawValue)">:zDay</option>
      </select>

      <!-- Month -->
      <select var="months=range(1,13)"
              name=":'%s_month' % name" id=":'%s_month' % name">
       <option value="">-</option>
       <option for="month in months"
               var2="zMonth=str(month).zfill(2)" value=":zMonth"
               selected=":field.isSelected(zobj, 'month', month, \
                                           rawValue)">:zMonth</option>
      </select>

      <!-- Year -->
      <select name=":'%s_year' % name" id=":'%s_year' % name">
       <option value="">-</option>
       <option for="year in years" value=":year"
               selected=":field.isSelected(zobj, 'year', year, \
                                           rawValue)">:year</option>
      </select>

      <!-- The icon for displaying the calendar popup -->
      <x if="field.calendar">
       <input type="hidden" id=":name" name=":name"/>
       <img id=":'%s_img' % name" src=":url('calendar.gif')"/>
       <script type="text/javascript">::field.getJsInit(name, years)</script>
      </x>

      <!-- Hour and minutes -->
      <x if="field.format == 0">
       <select var="hours=range(0,24)" name=":'%s_hour' % name"
               id=":'%s_hour' % name">
        <option value="">-</option>
        <option for="hour in hours"
                var2="zHour=str(hour).zfill(2)" value=":zHour"
                selected=":field.isSelected(zobj, 'hour', hour, \
                                            rawValue)">:zHour</option>
       </select> :
       <select var="minutes=range(0,60,5)" name=":'%s_minute' % name"
               id=":'%s_minute' % name">
        <option value="">-</option>
        <option for="minute in minutes"
                var2="zMinute=str(minute).zfill(2)" value=":zMinute"
                selected=":field.isSelected(zobj, 'minute', minute,\
                                            rawValue)">:zMinute</option>
       </select>
      </x>
     </x>''')

    pxSearch = Px('''<table var="years=range(field.startYear, field.endYear+1)">
       <!-- From -->
       <tr var="fromName='%s_from' % name;
                dayFromName='%s_from_day' % name;
                monthFromName='%s_from_month' % name;
                yearFromName='%s*date' % widgetName">
        <td width="10px">&nbsp;</td>
        <td><label>:_('search_from')</label></td>
        <td>
         <select id=":dayFromName" name=":dayFromName">
          <option value="">--</option>
          <option for="value in [str(v).zfill(2) for v in range(1, 32)]"
                  value=":value">:value</option>
         </select> /
         <select id=":monthFromName" name=":monthFromName">
          <option value="">--</option>
          <option for="value in [str(v).zfill(2) for v in range(1, 13)]"
                  value=":value">:value</option>
         </select> /
         <select id=":yearFromName" name=":yearFromName">
          <option value="">--</option>
          <option for="value in range(field.startYear, field.endYear+1)"
                  value=":value">:value</option>
         </select>
         <!-- The icon for displaying the calendar popup -->
         <x if="field.calendar">
          <input type="hidden" id=":fromName" name=":fromName"/>
          <img id=":'%s_img' % fromName" src=":url('calendar.gif')"/>
          <script type="text/javascript">::field.getJsInit(fromName, years)
          </script>
         </x>
        </td>
       </tr>

       <!-- To -->
       <tr var="toName='%s_to' % name;
                dayToName='%s_to_day' % name;
                monthToName='%s_to_month' % name;
                yearToName='%s_to_year' % name">
        <td></td>
        <td><label>:_('search_to')</label>&nbsp;&nbsp;&nbsp;&nbsp;</td>
        <td height="20px">
         <select id=":dayToName" name=":dayToName">
          <option value="">--</option>
          <option for="value in [str(v).zfill(2) for v in range(1, 32)]"
                  value=":value">:value</option>
         </select> /
         <select id=":monthToName" name=":monthToName">
          <option value="">--</option>
          <option for="value in [str(v).zfill(2) for v in range(1, 13)]"
                  value=":value">:value</option>
         </select> /
         <select id=":yearToName" name=":yearToName">
          <option value="">--</option>
          <option for="value in range(field.startYear, field.endYear+1)"
                  value=":value">:value</option>
         </select>
         <!-- The icon for displaying the calendar popup -->
         <x if="field.calendar">
          <input type="hidden" id=":toName" name=":toName"/>
          <img id=":'%s_img' % toName" src=":url('calendar.gif')"/>
          <script type="text/javascript">::field.getJsInit(toName, years)
          </script>
         </x>
        </td>
       </tr>
      </table>''')

    # Required CSS and Javascript files for this type.
    cssFiles = {'edit': ('jscalendar/calendar-blue.css',)}
    jsFiles = {'edit': ('jscalendar/calendar.js',
                        'jscalendar/lang/calendar-en.js',
                        'jscalendar/calendar-setup.js')}
    # Possible values for "format"
    WITH_HOUR = 0
    WITHOUT_HOUR = 1
    dateParts = ('year', 'month', 'day')
    hourParts = ('hour', 'minute')

    def __init__(self, validator=None, multiplicity=(0,1), default=None,
                 format=WITH_HOUR, dateFormat=None, hourFormat=None,
                 calendar=True, startYear=time.localtime()[0]-10,
                 endYear=time.localtime()[0]+10, reverseYears=False,
                 show=True, page='main', group=None, layouts=None, move=0,
                 indexed=False, mustIndex=True, searchable=False,
                 specificReadPermission=False, specificWritePermission=False,
                 width=None, height=None, maxChars=None, colspan=1, master=None,
                 masterValue=None, focus=False, historized=False, mapping=None,
                 label=None, sdefault=None, scolspan=1, swidth=None,
                 sheight=None, persist=True, view=None, xml=None, showDay=True):
        self.format = format
        self.calendar = calendar
        self.startYear = startYear
        self.endYear = endYear
        # If reverseYears is True, in the selection box, available years, from
        # self.startYear to self.endYear will be listed in reverse order.
        self.reverseYears = reverseYears
        # If p_showDay is False, the list for choosing a day will be hidden.
        self.showDay = showDay
        # If no p_dateFormat/p_hourFormat is specified, the application-wide
        # tool.dateFormat/tool.hourFormat instead.
        self.dateFormat = dateFormat
        self.hourFormat = hourFormat
        Field.__init__(self, validator, multiplicity, default, show, page,
                       group, layouts, move, indexed, mustIndex, searchable,
                       specificReadPermission, specificWritePermission, width,
                       height, None, colspan, master, masterValue, focus,
                       historized, mapping, label, sdefault, scolspan, swidth,
                       sheight, persist, False, view, xml)

    def getCss(self, layoutType, res, config):
        # CSS files are only required if the calendar must be shown
        if self.calendar: Field.getCss(self, layoutType, res, config)

    def getJs(self, layoutType, res, config):
        # Javascript files are only required if the calendar must be shown
        if self.calendar: Field.getJs(self, layoutType, res, config)

    def getSelectableYears(self):
        '''Gets the list of years one may select for this field.'''
        res = range(self.startYear, self.endYear + 1)
        if self.reverseYears: res.reverse()
        return res

    def validateValue(self, obj, value):
        DateTime = obj.getProductConfig().DateTime
        try:
            value = DateTime(value)
        except DateTime.DateError, ValueError:
            return obj.translate('bad_date')

    def getFormattedValue(self, obj, value, layoutType='view',
                          showChanges=False, language=None):
        if self.isEmptyValue(obj, value): return ''
        # Get the applicable date format
        tool = obj.getTool().appy()
        dateFormat = self.dateFormat or tool.dateFormat
        # A problem may occur with some extreme year values. Replace the "year"
        # part "by hand".
        if '%Y' in dateFormat:
            dateFormat = dateFormat.replace('%Y', str(value.year()))
        res = tool.o.formatDate(value, dateFormat, withHour=False)
        if self.format == Date.WITH_HOUR:
            res += ' %s' % value.strftime(self.hourFormat or tool.hourFormat)
        return res

    def getRequestValue(self, obj, requestName=None):
        request = obj.REQUEST
        name = requestName or self.name
        # Manage the "date" part
        value = ''
        for part in self.dateParts:
            # The "day" part may be hidden. Use "1" by default.
            if (part == 'day') and not self.showDay:
                valuePart = '01'
            else:
                valuePart = request.get('%s_%s' % (name, part), None)
            if not valuePart: return
            value += valuePart + '/'
        value = value[:-1]
        # Manage the "hour" part
        if self.format == self.WITH_HOUR:
            value += ' '
            for part in self.hourParts:
                valuePart = request.get('%s_%s' % (name, part), None)
                if not valuePart: return
                value += valuePart + ':'
            value = value[:-1]
        return value

    def getStorableValue(self, obj, value):
        if not self.isEmptyValue(obj, value):
            import DateTime
            return DateTime.DateTime(value)

    def getIndexType(self): return 'DateIndex'

    def isSelected(self, obj, fieldPart, dateValue, dbValue):
        '''When displaying this field, must the particular p_dateValue be
           selected in the sub-field p_fieldPart corresponding to the date
           part?'''
        # Get the value we must compare (from request or from database)
        rq = obj.REQUEST
        partName = '%s_%s' % (self.name, fieldPart)
        if rq.has_key(partName):
            compValue = rq.get(partName)
            if compValue.isdigit():
                compValue = int(compValue)
        else:
            compValue = dbValue
            if compValue:
                compValue = getattr(compValue, fieldPart)()
        # Compare the value
        return compValue == dateValue

    def getJsInit(self, name, years):
        '''Gets the Javascript init code for displaying a calendar popup for
           this field, for an input named p_name (which can be different from
           self.name if, ie, it is a search field).'''
        # Always express the range of years in chronological order.
        years = [years[0], years[-1]]
        years.sort()
        return 'Calendar.setup({inputField: "%s", button: "%s_img", ' \
               'onSelect: onSelectDate, range:%s})' % (name, name, str(years))
# ------------------------------------------------------------------------------
