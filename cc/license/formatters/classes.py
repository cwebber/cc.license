"""
Formatters take a License instance and a dictionary of work metadata about
the licensed work. The keys of this work_dict are as follows:

 - format
   The format of the work, values can be one of:
     - Audio (Sound)
     - Video (MovingImage)
     - Image (StillImage)
     - Text (Text)
     - Interactive (InteractiveResource)

 - worktitle
   Title of work

 - attribution_name
   Attribute work to name

 - attribution_url
   Attribute work to URL

 - source_work
   Source work URL

 - more_permissions_url
   More permissions URL
"""

import os
from cc.license._lib.interfaces import ILicenseFormatter
from cc.license._lib.exceptions import CCLicenseError
import zope.interface
from genshi.template import TemplateLoader
from filters import Source, Permissions
from enum import Enum

# template loader, which is reused in a few places
LOADER = TemplateLoader(
             os.path.join(os.path.dirname(__file__), 'templates'),
             auto_reload=False)

class HTMLFormatter(object):
    zope.interface.implements(ILicenseFormatter)

    def __init__(self):
        self.tmpltypes = Enum('default', 'desc', 'attr', 'desc_attr')

    def __repr__(self):
        return "<LicenseFormatter object '%s'>" % self.id

    def __str__(self):
        return '(%s)' % self.title

    @property
    def id(self):
        return 'html+rdfa'

    @property
    def title(self):
        return "HTML + RDFa formatter"

    def _template_type(self, w):
        """Takes a work_dict and returns an Enum corresponding to the type."""
        type = self.tmpltypes.default
        if w.has_key('format') or w.has_key('worktitle'):
            type = self.tmpltypes.desc
        if w.has_key('attribution_name') or w.has_key('attribution_url'):
            if type == self.tmpltypes.default:
                type = self.tmpltypes.attr
            else: # was already self.tmpltypes.desc
                type = self.tmpltypes.desc_attr
        return type

    def _translate_dctype(self, format):
        return { # let it throw a KeyError
                 None : None,
                 'audio' : 'Sound',
                 'video' : 'MovingImage',
                 'image' : 'StillImage',
                 'text' : 'Text',
                 'interactive' : 'InteractiveResource',
               }[format]

    def format(self, license, work_dict={}, locale='en'):
        """Return an HTML + RDFa string serialization for the license,
            optionally incorporating the work metadata and locale."""
        w = work_dict # alias work_dict for brevity

        tmpl_type = self._template_type(w) # decide which templates to use

        chosen_tmpl = None
        kwargs = {}

        # general kwarg packing
        kwargs['license'] = license
        kwargs['locale'] = locale

        # dctype and format, if they exist
        format = None
        dctype = None
        if w.has_key('format'):
            format = w['format'].lower()
            dctype = self._translate_dctype(format)
        kwargs['dctype'] = dctype

        # general recipe:
        #  - pick a template
        #  - pack a set of kwargs
        #  - profit!
        if tmpl_type == self.tmpltypes.default:
            chosen_tmpl = 'default.xml'

        elif tmpl_type == self.tmpltypes.desc:
            if w.has_key('worktitle'):
                kwargs['worktitle'] = w['worktitle']
                chosen_tmpl = 'worktitle.xml'
            else: # must just have format
                chosen_tmpl = 'work_%s.xml' % format # XXX does not scrub input
                if w.has_key('worktitle'):
                    kwargs['worktitle'] = w['worktitle']

        elif tmpl_type == self.tmpltypes.attr:
            chosen_tmpl = 'title_attribution.xml'

        elif tmpl_type == self.tmpltypes.desc_attr:
            pass

        self.tmpl = LOADER.load(chosen_tmpl)
        stream = self.tmpl.generate(**kwargs)
            # XXX worry about filter logic later
        stream = stream | Source(work_dict) | Permissions(work_dict)
        return stream.render('xhtml')
