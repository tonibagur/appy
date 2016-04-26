# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Appy is a framework for building applications in the Python language.
# Copyright (C) 2007 Gaetan Delannay

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,USA.

# ------------------------------------------------------------------------------
import os, os.path, re, time, sys, subprocess, traceback, unicodedata, shutil, \
       mimetypes
sequenceTypes = (list, tuple)

# ------------------------------------------------------------------------------
class FolderDeleter:
    @staticmethod
    def delete(dirName):
        '''Recursively deletes p_dirName.'''
        dirName = os.path.abspath(dirName)
        for root, dirs, files in os.walk(dirName, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(dirName)

    @staticmethod
    def deleteEmpty(dirName):
        '''Deletes p_dirName and its parent dirs if they are empty.'''
        while True:
            try:
                if not os.listdir(dirName):
                    os.rmdir(dirName)
                    dirName = os.path.dirname(dirName)
                else:
                    break
            except OSError, oe:
                break

# ------------------------------------------------------------------------------
extsToClean = ('.pyc', '.pyo', '.fsz', '.deltafsz', '.dat', '.log')
def cleanFolder(folder, exts=extsToClean, folders=(), verbose=False):
    '''This function allows to remove, in p_folder and subfolders, any file
       whose extension is in p_exts, and any folder whose name is in
       p_folders.'''
    if verbose: print('Cleaning folder %s...' % folder)
    # Remove files with an extension listed in p_exts
    if exts:
        for root, dirs, files in os.walk(folder):
            for fileName in files:
                ext = os.path.splitext(fileName)[1]
                if (ext in exts) or ext.endswith('~'):
                    fileToRemove = os.path.join(root, fileName)
                    if verbose: print('Removing file %s...' % fileToRemove)
                    os.remove(fileToRemove)
    # Remove folders whose names are in p_folders.
    if folders:
        for root, dirs, files in os.walk(folder):
            for folderName in dirs:
                if folderName in folders:
                    toDelete = os.path.join(root, folderName)
                    if verbose: print('Removing folder %s...' % toDelete)
                    FolderDeleter.delete(toDelete)

# ------------------------------------------------------------------------------
def resolvePath(path):
    '''p_path is a file path that can contain occurences of "." and "..". This
       function resolves them and procuces a minimal path.'''
    res = []
    for elem in path.split(os.sep):
        if elem == '.': pass
        elif elem == '..': res.pop()
        else: res.append(elem)
    return os.sep.join(res)

# ------------------------------------------------------------------------------
def copyFolder(source, dest, cleanDest=False):
    '''Copies the content of folder p_source to folder p_dest. p_dest is
       created, with intermediary subfolders if required. If p_cleanDest is
       True, it removes completely p_dest if it existed. Else, content of
       p_source will be added to possibly existing content in p_dest, excepted
       if file names corresponds. In this case, file in p_source will overwrite
       file in p_dest.'''
    dest = os.path.abspath(dest)
    # Delete the dest folder if required
    if os.path.exists(dest) and cleanDest:
        FolderDeleter.delete(dest)
    # Create the dest folder if it does not exist
    if not os.path.exists(dest):
        os.makedirs(dest)
    # Copy the content of p_source to p_dest.
    for name in os.listdir(source):
        sourceName = os.path.join(source, name)
        destName = os.path.join(dest, name)
        if os.path.isfile(sourceName):
            # Copy a single file
            shutil.copy(sourceName, destName)
        elif os.path.isdir(sourceName):
            # Copy a subfolder (recursively)
            copyFolder(sourceName, destName)

# ------------------------------------------------------------------------------
def encodeData(data, encoding=None):
    '''Applies some p_encoding to string p_data, but only if an p_encoding is
       specified.'''
    if not encoding: return data
    return data.encode(encoding)

# ------------------------------------------------------------------------------
def copyData(data, target, targetMethod, type='string', encoding=None,
             chunkSize=1024):
    '''Copies p_data to a p_target, using p_targetMethod. For example, it copies
       p_data which is a string containing the binary content of a file, to
       p_target, which can be a HTTP connection or a file object.

       p_targetMethod can be "write" (files) or "send" (HTTP connections) or ...
       p_type can be "string", "file" or "zope". In the latter case it is an
       instance of OFS.Image.File. If p_type is "file", one may, in p_chunkSize,
       specify the amount of bytes transmitted at a time.

       If an p_encoding is specified, it is applied on p_data before copying.

       Note that if the p_target is a Python file, it must be opened in a way
       that is compatible with the content of p_data, ie file('myFile.doc','wb')
       if content is binary.'''
    dump = getattr(target, targetMethod)
    if not type or (type == 'string'): dump(encodeData(data, encoding))
    elif type == 'file':
        while True:
            chunk = data.read(chunkSize)
            if not chunk: break
            dump(encodeData(chunk, encoding))
    elif type == 'zope':
        # A OFS.Image.File instance can be split into several chunks
        if isinstance(data.data, basestring): # One chunk
            dump(encodeData(data.data, encoding))
        else:
            # Several chunks
            data = data.data
            while data is not None:
                dump(encodeData(data.data, encoding))
                data = data.next

# ------------------------------------------------------------------------------
def splitList(l, sub):
    '''Returns a list that was build from list p_l whose elements were
       re-grouped into sub-lists of p_sub elements.

       For example, if l = [1,2,3,4,5] and sub = 3, the method returns
       [ [1,2,3], [4,5] ].'''
    res = []
    i = -1
    for elem in l:
        i += 1
        if (i % sub) == 0:
            # A new sub-list must be created
            res.append([elem])
        else:
            res[-1].append(elem)
    return res

class IterSub:
    '''Iterator over a list of lists.'''
    def __init__(self, l):
        self.l = l
        self.i = 0 # The current index in the main list
        self.j = 0 # The current index in the current sub-list
    def __iter__(self): return self
    def next(self):
        # Get the next ith sub-list
        if (self.i + 1) > len(self.l): raise StopIteration
        sub = self.l[self.i]
        if (self.j + 1) > len(sub):
            self.i += 1
            self.j = 0
            return self.next()
        else:
            elem = sub[self.j]
            self.j += 1
            return elem

def getElementAt(l, cyclicIndex):
    '''Gets the element within list/tuple p_l that is at index p_cyclicIndex
       (int). If the index out of range, we do not raise IndexError: we continue
       to loop over the list until we reach this index.'''
    return l[cyclicIndex % len(l)]

# ------------------------------------------------------------------------------
def flipDict(d):
    '''Flips dict p_d: keys become values, values become keys. p_d is left
       untouched: a new, flipped, dict is returned.'''
    res = {}
    for k, v in d.iteritems(): res[v] = k
    return res

def addPair(name, value, d=None):
    '''Adds key-value pair (name, value) to dict p_d. If this dict is None, it
       returns a newly created dict.'''
    if d: d[name] = value
    else: d = {name: value}
    return d

# ------------------------------------------------------------------------------
class Traceback:
    '''Dumps the last traceback into a string'''
    @staticmethod
    def get(last=None):
        '''Gets the traceback as a string. If p_last is given (must be an
           integer value), only the p_last lines of the traceback will be
           included. It can be useful for pod/px tracebacks: when an exception
           occurs while evaluating a complex tree of buffers, most of the
           traceback lines concern uninteresting buffer/action-related recursive
           calls.'''
        res = []
        excType, excValue, tb = sys.exc_info()
        tbLines = traceback.format_tb(tb)
        for tbLine in tbLines: res.append(' %s' % tbLine)
        # Get the error message
        try:
            message = str(excValue)
        except UnicodeEncodeError, uer:
            message = excValue.args[0].encode('utf-8')
        res.append(' %s: %s' % (str(excType), message))
        if last: res = res[-last:]
        return ''.join(res)

# ------------------------------------------------------------------------------
def getOsTempFolder():
    tmp = '/tmp'
    if os.path.exists(tmp) and os.path.isdir(tmp):
        res = tmp
    elif os.environ.has_key('TMP'):
        res = os.environ['TMP']
    elif os.environ.has_key('TEMP'):
        res = os.environ['TEMP']
    else:
        raise "Sorry, I can't find a temp folder on your machine."
    return res

def getTempFileName(prefix='', extension=''):
    '''Returns the absolute path to a unique file name in the OS temp folder.
       The caller will then be able to create a file with this name.

       A p_prefix to this file can be provided. If an p_extension is provided,
       it will be appended to the name. Both dotted and not dotted versions
       of p_extension are allowed (ie, ".pdf" or "pdf").'''
    res = '%s/%s_%f' % (getOsTempFolder(), prefix, time.time())
    if extension:
        if extension.startswith('.'): res += extension
        else: res += '.' + extension
    return res

# ------------------------------------------------------------------------------
def executeCommand(cmd):
    '''Executes command p_cmd and returns a tuple (s_stdout, s_stderr)
       containing the data output by the subprocesss on stdout and stderr. p_cmd
       should be a list of args (the 1st arg being the command in itself, the
       remaining args being the parameters), but it can also be a string, too
       (see subprocess.Popen doc).'''
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.communicate()

# ------------------------------------------------------------------------------
charsIgnore = u'.,:;*+=~?%^\'’"<>{}[]|\t\\°-'
fileNameIgnore = charsIgnore + u' $£€/\r\n'
extractIgnore = charsIgnore + '/()'
alphaRex = re.compile('[a-zA-Z]')
alphanumRex = re.compile('[a-zA-Z0-9]')

def normalizeString(s, usage='fileName'):
    '''Returns a version of string p_s whose special chars (like accents) have
       been replaced with normal chars. Moreover, if p_usage is:
       * fileName: it removes any char that can't be part of a file name;
       * alphanum: it removes any non-alphanumeric char;
       * alpha: it removes any non-letter char.
    '''
    strNeeded = isinstance(s, str)
    # We work in unicode. Convert p_s to unicode if not unicode.
    if isinstance(s, str):
        try:
            s = s.decode('utf-8')
        except UnicodeDecodeError:
            # Another encoding may be in use
            s = s.decode('latin-1')
    elif not isinstance(s, unicode): s = unicode(s)
    # For extracted text, replace any unwanted char with a blank
    if usage == 'extractedText':
        res = u''
        for char in s:
            if char not in extractIgnore: res += char
            else: res += ' '
        s = res
    # Standardize special chars like accents
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    # Remove any other char, depending on p_usage
    if usage == 'fileName':
        # Remove any char that can't be found within a file name under Windows
        # or that could lead to problems with LibreOffice.
        res = ''
        for char in s:
            if char not in fileNameIgnore: res += char
    elif usage.startswith('alpha'):
        exec 'rex = %sRex' % usage
        res = ''
        for char in s:
            if rex.match(char): res += char
    elif usage == 'noAccents':
        res = s
    else:
        res = s
    # Re-code the result as a str if a str was given
    if strNeeded: res = res.encode('utf-8')
    return res

def normalizeText(s):
    '''Normalizes p_s: remove special chars, lowerizes it, etc, for indexing
       purposes.'''
    return normalizeString(s, usage='extractedText').strip().lower()

def keepDigits(s):
    '''Returns string p_s whose non-number chars have been removed'''
    if s is None: return s
    res = ''
    for c in s:
        if c.isdigit(): res += c
    return res

def getStringList(l):
    '''Gets the string literal corresponding to list p_l'''
    res = []
    for v in l:
        if type(v) not in sequenceTypes:
            if not isinstance(v, basestring): v = str(v)
            value = "'%s'" % (v.replace("'", "\\'"))
        else:
            value = getStringList(v)
        res.append(value)
    return '[%s]' % ','.join(res)

def getStringDict(d):
    '''Gets the string literal corresponding to dict p_d'''
    res = []
    for k, v in d.iteritems():
        if type(v) not in sequenceTypes:
            if not isinstance(k, basestring): k = str(k)
            if not isinstance(v, basestring): v = str(v)
            value = "'%s':'%s'" % (k, v.replace("'", "\\'"))
        else:
            value = "'%s':%s" % (k, getStringList(v))
        res.append(value)
    return '{%s}' % ','.join(res)

def stretchText(s, pattern, char=' '):
    '''Inserts occurrences of p_char within p_s according to p_pattern.
       Example: stretchText("475123456", (3,2,2,2)) returns '475 12 34 56'.'''
    res = ''
    i = 0
    for nb in pattern:
        j = 0
        while j < nb:
            res += s[i+j]
            j += 1
        res += char
        i += nb
    return res

# ------------------------------------------------------------------------------
def formatNumber(n, sep=',', precision=2, tsep=' ', removeTrailingZeros=False):
    '''Returns a string representation of number p_n, which can be a float
       or integer. p_sep is the decimal separator to use. p_precision is the
       number of digits to keep in the decimal part for producing a nice rounded
       string representation. p_tsep is the "thousands" separator.'''
    if n == None: return ''
    # Manage precision
    if precision == None:
        res = str(n)
    else:
        format = '%%.%df' % precision
        res = format % n
    # Use the correct decimal separator
    res = res.replace('.', sep)
    # Insert p_tsep every 3 chars in the integer part of the number
    splitted = res.split(sep)
    res = ''
    if len(splitted[0]) < 4: res = splitted[0]
    else:
        i = len(splitted[0])-1
        j = 0
        while i >= 0:
            j += 1
            res = splitted[0][i] + res
            if (j % 3) == 0:
                res = tsep + res
            i -= 1
    # Add the decimal part if not 0
    if len(splitted) > 1:
        try:
            decPart = int(splitted[1])
            if decPart != 0:
                res += sep + splitted[1]
            if removeTrailingZeros: res = res.rstrip('0')
        except ValueError:
            # This exception may occur when the float value has an "exp"
            # part, like in this example: 4.345e-05
            res += sep + splitted[1]
    return res

# ------------------------------------------------------------------------------
def lower(s):
    '''French-accents-aware variant of string.lower.'''
    isUnicode = isinstance(s, unicode)
    if not isUnicode: s = s.decode('utf-8')
    res = s.lower()
    if not isUnicode: res = res.encode('utf-8')
    return res

def upper(s):
    '''French-accents-aware variant of string.upper.'''
    isUnicode = isinstance(s, unicode)
    if not isUnicode: s = s.decode('utf-8')
    res = s.upper()
    if not isUnicode: res = res.encode('utf-8')
    return res

# ------------------------------------------------------------------------------
typeLetters = {'b': bool, 'i': int, 'j': long, 'f':float, 's':str, 'u':unicode,
               'l': list, 'd': dict}

# ------------------------------------------------------------------------------
class CodeAnalysis:
    '''This class holds information about some code analysis (line counts) that
       spans some folder hierarchy.'''
    def __init__(self, name):
        self.name = name # Let's give a name for the analysis
        self.numberOfFiles = 0 # The total number of analysed files
        self.emptyLines = 0 # The number of empty lines within those files
        self.commentLines = 0 # The number of comment lines
        # A code line is anything not being an empty or comment line
        self.codeLines = 0

    def numberOfLines(self):
        '''Computes the total number of lines within analysed files.'''
        return self.emptyLines + self.commentLines + self.codeLines

    def _analyseFile(self, f, start, end, single=None):
        '''Analyses file p_f. p_start and p_end are delimiters for multi-line
           comments, while p_single is the symbol representing a single-line
           comment.'''
        inDoc = False
        firstDoc = False
        for line in f:
            stripped = line.strip()
            # Manage a single-line comment
            if not inDoc and single and line.startswith(single):
                self.commentLines += 1
                continue
            # Manage a comment
            if not inDoc and (start in line):
                if line.startswith(start):
                    self.commentLines += 1
                else:
                    self.codeLines += 1
                inDoc = True
                firstDoc = True
            if inDoc:
                if not firstDoc:
                    self.commentLines += 1
                if end in line:
                    inDoc = False
                firstDoc = False
                continue
            # Manage an empty line
            if not stripped:
                self.emptyLines += 1
            else:
                self.codeLines += 1

    def analyseJs(self, f): return self._analyseFile(f, '/*', '*/', single='//')
    analyseCss = analyseJs
    def analyseXml(self, f): return self._analyseFile(f, '<!--', '-->')

    docSeps = ('"""', "'''")
    def isPythonDoc(self, line, start, isStart=False):
        '''Returns True if we find, in p_line, the start of a docstring (if
           p_start is True) or the end of a docstring (if p_start is False).
           p_isStart indicates if p_line is the start of the docstring.'''
        if start:
            res = line.startswith(self.docSeps[0]) or \
                  line.startswith(self.docSeps[1])
        else:
            sepOnly = (line == self.docSeps[0]) or (line == self.docSeps[1])
            if sepOnly:
                # If the line contains the separator only, is this the start or
                # the end of the docstring?
                if isStart: res = False
                else: res = True
            else:
                res = line.endswith(self.docSeps[0]) or \
                      line.endswith(self.docSeps[1])
        return res

    def analysePy(self, f):
        '''Analyses the Python file p_f'''
        # Are we in a docstring ?
        inDoc = False
        for line in f:
            stripped = line.strip()
            # Manage a line that is within a docstring
            inDocStart = False
            if not inDoc and self.isPythonDoc(stripped, start=True):
                inDoc = True
                inDocStart = True
            if inDoc:
                self.commentLines += 1
                if self.isPythonDoc(stripped, start=False, isStart=inDocStart):
                    inDoc = False
                continue
            # Manage an empty line
            if not stripped:
                self.emptyLines += 1
                continue
            # Manage a comment line
            if line.startswith('#'):
                self.commentLines += 1
                continue
            # If we are here, we have a code line
            self.codeLines += 1

    def analyseFile(self, path, ext):
        '''Analyses file named p_path'''
        self.numberOfFiles += 1
        f = file(path)
        getattr(self, 'analyse%s' % ext.capitalize())(f)
        f.close()

    def printReport(self):
        '''Returns the analysis report as a string, only if there is at least
           one analysed line.'''
        lines = self.numberOfLines()
        if not lines: return
        commentRate = (self.commentLines / float(lines)) * 100.0
        blankRate = (self.emptyLines / float(lines)) * 100.0
        print('%s: %d files, %d lines (%.0f%% comments, %.0f%% blank)' % \
              (self.name, self.numberOfFiles, lines, commentRate, blankRate))

# ------------------------------------------------------------------------------
class LinesCounter:
    '''Counts and classifies the lines of code within a folder hierarchy'''
    defaultExcludes = ('%s.svn' % os.sep, '%stmp' % os.sep, '%stemp' % os.sep,
                       '%sjscalendar' % os.sep, '%sdoc' % os.sep)
    fileTypes = {'py': 'Python', 'xml': 'XML', 'css': 'CSS', 'js': 'Javascript'}

    def __init__(self, folderOrModule, excludes=None):
        if isinstance(folderOrModule, basestring):
            # It is the path of some folder
            self.folder = folderOrModule
        else:
            # It is a Python module
            self.folder = os.path.dirname(folderOrModule.__file__)
        # These dict will hold information about analysed files
        self.analysed = {}
        for ext, name in self.fileTypes.iteritems():
            self.analysed[ext] = { False: CodeAnalysis(name),
                                   True:  CodeAnalysis('%s (test)' % name)}
        # Are we currently analysing real or test code ?
        self.inTest = False
        # Which paths to exclude from the analysis?
        self.excludes = list(self.defaultExcludes)
        if excludes: self.excludes += excludes

    def printReport(self):
        '''Displays on stdout a small analysis report about self.folder'''
        total = 0
        for ext, name in self.fileTypes.iteritems():
            for zone in (False, True):
                analyser = self.analysed[ext][zone]
                if analyser.numberOfFiles:
                    analyser.printReport()
                    total += analyser.numberOfLines()
        print 'Total (including commented and blank): ***', total, '***'

    def isExcluded(self, path):
        '''Must p_path be excluded from the analysis?'''
        for excl in self.excludes:
            if excl in path: return True

    def run(self):
        '''Let's start the analysis of self.folder'''
        # The test markers will allow us to know if we are analysing test code
        # or real code within a given part of self.folder code hierarchy.
        testMarker1 = '%stest%s' % (os.sep, os.sep)
        testMarker2 = '%stest' % os.sep
        testMarker3 = '%stests%s' % (os.sep, os.sep)
        testMarker4 = '%stests' % os.sep
        for root, folders, files in os.walk(self.folder):
            if self.isExcluded(root): continue
            # Are we in real code or in test code ?
            self.inTest = False
            if root.endswith(testMarker2) or (root.find(testMarker1) != -1) or \
               root.endswith(testMarker4) or (root.find(testMarker3) != -1):
                self.inTest = True
            # Scan the files in this folder
            for fileName in files:
                ext = os.path.splitext(fileName)[1]
                if ext: ext = ext[1:]
                if ext not in self.analysed: continue
                path = os.path.join(root, fileName)
                self.analysed[ext][self.inTest].analyseFile(path, ext)
        self.printReport()

# ------------------------------------------------------------------------------
CONVERSION_ERROR = 'An error occurred. %s'
class FileWrapper:
    '''When you get, from an appy object, the value of a File attribute, you
       get an instance of this class.'''
    def __init__(self, zopeFile):
        '''This constructor is only used by Appy to create a nice File instance
           from a Zope corresponding instance (p_zopeFile). If you need to
           create a new file and assign it to a File attribute, use the
           attribute setter, do not create yourself an instance of this
           class.'''
        d = self.__dict__
        d['_zopeFile'] = zopeFile # Not for you!
        d['name'] = zopeFile.filename
        d['content'] = zopeFile.data
        d['mimeType'] = zopeFile.content_type
        d['size'] = zopeFile.size # In bytes

    def __setattr__(self, name, v):
        d = self.__dict__
        if name == 'name':
            self._zopeFile.filename = v
            d['name'] = v
        elif name == 'content':
            self._zopeFile.update_data(v, self.mimeType, len(v))
            d['content'] = v
            d['size'] = len(v)
        elif name == 'mimeType':
            self._zopeFile.content_type = self.mimeType = v
        else:
            raise 'Impossible to set attribute %s. "Settable" attributes ' \
                  'are "name", "content" and "mimeType".' % name

    def dump(self, filePath=None, format=None, tool=None):
        '''Writes the file on disk. If p_filePath is specified, it is the
           path name where the file will be dumped; folders mentioned in it
           must exist. If not, the file will be dumped in the OS temp folder.
           The absolute path name of the dumped file is returned.
           If an error occurs, the method returns None. If p_format is
           specified, LibreOffice will be called for converting the dumped file
           to the desired format. In this case, p_tool, a Appy tool, must be
           provided. Indeed, any Appy tool contains parameters for contacting
           LibreOffice in server mode.'''
        if not filePath:
            filePath = '%s/file%f.%s' % (getOsTempFolder(), time.time(),
                normalizeString(self.name))
        f = file(filePath, 'w')
        if self.content.__class__.__name__ == 'Pdata':
            # The file content is splitted in several chunks.
            f.write(self.content.data)
            nextPart = self.content.next
            while nextPart:
                f.write(nextPart.data)
                nextPart = nextPart.next
        else:
            # Only one chunk
            f.write(self.content)
        f.close()
        if format:
            if not tool: return
            # Convert the dumped file using OpenOffice
            out, err = tool.convert(filePath, format)
            # Even if we have an "error" message, it could be a simple warning.
            # So we will continue here and, as a subsequent check for knowing if
            # an error occurred or not, we will test the existence of the
            # converted file (see below).
            os.remove(filePath)
            # Return the name of the converted file.
            baseName, ext = os.path.splitext(filePath)
            if (ext == '.%s' % format):
                filePath = '%s.res.%s' % (baseName, format)
            else:
                filePath = '%s.%s' % (baseName, format)
            if not os.path.exists(filePath):
                tool.log(CONVERSION_ERROR % err, type='error')
                return
        return filePath

    def copy(self):
        '''Returns a copy of this file'''
        return FileWrapper(self._zopeFile._getCopy(self._zopeFile))

# ------------------------------------------------------------------------------
def getMimeType(fileName):
    '''Tries to guess mime type from p_fileName'''
    res, encoding = mimetypes.guess_type(fileName)
    if not res:
        if fileName.endswith('.po'):
            res = 'text/plain'
            encoding = 'utf-8'
    if not res: return ''
    if not encoding: return res
    return '%s;;charset=%s' % (res, encoding)

# ------------------------------------------------------------------------------
class WhitespaceCruncher:
    '''Takes care of removing unnecessary whitespace in several contexts'''
    whitechars = u' \r\t\n' # Chars considered as whitespace
    allWhitechars = whitechars + u' ' # nbsp
    @staticmethod
    def crunch(s, previous=None):
        '''Return a version of p_s (expected to be a unicode string) where all
           "whitechars" are:
           * converted to real whitespace;
           * reduced in such a way that there cannot be 2 consecutive
             whitespace chars.
           If p_previous is given, those rules must also apply globally to
           previous+s.'''
        res = ''
        # Initialise the previous char
        if previous:
            previousChar = previous[-1]
        else:
            previousChar = u''
        for char in s:
            if char in WhitespaceCruncher.whitechars:
                # Include the current whitechar in the result if the previous
                # char is not a whitespace or nbsp.
                if not previousChar or \
                   (previousChar not in WhitespaceCruncher.allWhitechars):
                    res += u' '
            else: res += char
            previousChar = char
        # "res" can be a single whitespace. It is up to the caller method to
        # identify when this single whitespace must be kept or crunched.
        return res
# ------------------------------------------------------------------------------
