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
# Import stuff from appy.fields (and from a few other places too).
# This way, when an app gets "from appy.gen import *", everything is available.
from appy import Object
from appy.px import Px
from appy.fields import Field
from appy.fields.action import Action
from appy.fields.boolean import Boolean
from appy.fields.computed import Computed
from appy.fields.date import Date
from appy.fields.file import File
from appy.fields.float import Float
from appy.fields.info import Info
from appy.fields.integer import Integer
from appy.fields.list import List
from appy.fields.dict import Dict
from appy.fields.pod import Pod
from appy.fields.ref import Ref, autoref
from appy.fields.string import String, Selection
from appy.fields.search import Search, UiSearch
from appy.fields.group import Group, Column
from appy.fields.page import Page
from appy.fields.phase import Phase
from appy.fields.workflow import *
from appy.gen.layout import Table
from appy.gen.utils import No, Tool, User, MessageException
from appy.gen.monitoring import Monitoring

# Make the following classes available here: people may need to override some
# of their PXs (defined as static attributes).
from appy.gen.wrappers import AbstractWrapper as BaseObject
from appy.gen.wrappers.ToolWrapper import ToolWrapper as BaseTool

# ------------------------------------------------------------------------------
class Config:
    '''If you want to specify some configuration parameters for appy.gen and
       your application, please create a class named "Config" in the __init__.py
       file of your application and override some of the attributes defined
       here, ie:

       import appy.gen
       class Config(appy.gen.Config):
           langages = ('en', 'fr')
    '''
    # What skin to use for the web interface? Appy has 2 skins: the default
    # one (with a fixed width) and the "wide" skin (takes the whole page width).
    skin = None # None means: the default one. Could be "wide".
    # For every language code that you specify in this list, appy.gen will
    # produce and maintain translation files.
    languages = ['en']
    # If languageSelector is True, on (almost) every page, a language selector
    # will allow to switch between languages defined in self.languages. Else,
    # the browser-defined language will be used for choosing the language
    # of returned pages.
    languageSelector = False
    # If "forceLanguage" is set, Appy will not take care of the browser
    # language, will always use the forced language and will hide the language
    # selector, even if "languageSelector" hereabove is True.
    forcedLanguage = None
    # Show the link to the user profile in the user strip
    userLink = True
    # If you want to distinguish a test site from a production site, set the
    # "test" parameter to some text (lie "TEST SYTEM" or
    # "VALIDATION ENVIRONMENT". This text will be shown on every page.
    test = None
    # People having one of these roles will be able to create instances
    # of classes defined in your application.
    defaultCreators = ['Manager']
    # Roles in use in a Appy application are identified at generation time from
    # workflows or class attributes like "creators": it is not needed to declare
    # them somewhere. If you want roles that Appy will be unabled to detect, add
    # them in the following list. Every role can be a Role instance or a string.
    additionalRoles = []
    # The "root" classes are those that will get their menu in the user
    # interface. Put their names in the list below. If you leave the list empty,
    # all gen-classes will be considered root classes (the default). If
    # rootClasses is None, no class will be considered as root.
    rootClasses = []
    # Number of translations for every page on a Translation object
    translationsPerPage = 30
    # Language that will be used as a basis for translating to other
    # languages.
    sourceLanguage = 'en'
    # Activate or not the button on home page for asking a new password
    activateForgotPassword = True
    # Enable session timeout?
    enableSessionTimeout = False
    # If the following field is True, the login/password widget will be
    # discreet. This is for sites where authentication is not foreseen for
    # the majority of visitors (just for some administrators).
    discreetLogin = False
    # When using Ogone, place an instance of appy.gen.ogone.OgoneConfig in
    # the field below.
    ogone = None
    # When using Google analytics, specify here the Analytics ID
    googleAnalyticsId = None
    # Create a group for every global role ?
    groupsForGlobalRoles = False
    # When using a LDAP for authenticating users, place an instance of class
    # appy.shared.ldap.LdapConfig in the field below.
    ldap = None
    # When using, in front of an Appy server, a reverse proxy for authentication
    # for achieving single-sign-on (SSO), place an instance of
    # appy.shared.sso.SsoConfig in the field below.
    sso = None
    # When using a SMTP mail server for sending emails from your app, place an
    # instance of class appy.gen.mail.MailConfig in the field below.
    mail = None
    # For an app, the default folder where to look for static content for the
    # user interface (CSS, Javascript and image files) is folder "ui" within
    # this app.
    uiFolders = ['ui']
    # CK editor configuration. Appy integrates CK editor via CDN (see
    # http://cdn.ckeditor.com). Do not change "ckVersion" hereafter, excepted
    # if you are sure that the customized configuration files config.js,
    # contents.css and styles.js stored in appy/gen/ui/ckeditor will be
    # compatible with the version you want to use.
    ckVersion = '4.4.7'
    # ckDistribution can be "basic", "standard", "standard-all", "full" or
    # "full-all" (see doc in http://cdn.ckeditor.com).
    ckDistribution = 'standard'
    # CK toolbars are not configurable yet. So toolbar "Appy", defined in
    # appy/gen/ui/ckeditor/config.js, will always be used.

    # If the python interpreter running this app is UNO-enabled, set None to
    # the following parameter. Else, specify the path to a UNO-enabled
    # interpreter. On Ubuntu, /usr/bin/python (or /usr/bin/python3 if >=14.04)
    # is UNO-enabled.
    unoEnabledPython = '/usr/bin/python'
    # On what port does LibreOffice run ?
    libreOfficePort = 2002
    # Monitoring configuration. Update this instance (whose class is in
    # appy.gen.monitoring)) for changing the default configuration.
    monitoring = Monitoring()
# ------------------------------------------------------------------------------
