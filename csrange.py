# (c) 2018, vnetman@zoho.com
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: csrange
    author: vnetman@zoho.com
    version_added: "2.7"
    short_description: return a list of individual items from a comma-separated list of ranges
    description:
      - given a comma-separated list of ranges of items (vlan ids, interface names), return a list of individual items
    options:
      _terms:
        description: csrangestring
        required: True
    notes:
      - Spaces are not significant i.e., input string can have any number of spaces
      - Interface names are case-sensitive, i.e. both halves of a range must use the same spelling and case
"""

EXAMPLES = """
- name: "Get the list of vlan ids"
  debug: msg="VLANs {{lookup('csrange', '1-10,21-30')}}"

- name: "Get the list of interfaces"
  debug: msg="Interfaces {{lookup('csrange', 'Te3/1-4,Te4/1-4')}}"
"""

RETURN = """
  _raw:
    description:
      - list of items
    type: list
"""
from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms

import re

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

# The regex we use for parsing each 'subrange', i.e. the stuff delimited
# by commas, e.g. 'Gi5/37-Gi5/48'
# Create it upfront here since it never changes.
re_subrange = re.compile(
    r'''(
    ^(?P<left_context>[A-Za-z0-9/]*[^\d])? # The first 'Gi5/'
    (?P<left_port_number>\d+)              # 37
    -                                      # -
    (?P<right_context>[A-Za-z0-9/]*[^\d])? # The second 'Gi5/'
    (?P<right_port_number>\d+)$            # 48
    )''', re.VERBOSE)
    
class LookupModule(LookupBase):
    def _do_process_csrange(self, terms, variables):
        ret = []

        ques = str(terms[0])
        
        # Strip whitespace
        ques = ''.join(ques.split())

        subranges = ques.split(',')
        for sr in subranges:
            if sr == '':
                continue
        
            if '-' not in sr:
                # singleton, i.e. not a range; return as is
                ret.append(sr)
                continue
            
            # Apply the regex
            mo = re_subrange.search(sr)
            if not mo:
                raise AnsibleError('\"{}\" cannot be parsed'.format(sr))
        
            if mo.group('right_context'):
                if mo.group('left_context') != mo.group('right_context'):
                    raise AnsibleError('Failed to parse "{}": '
                                       'left hand side context "{}" is '
                                       'different from right hand side '
                                       'context "{}"'.
                                       format(sr, mo.group('left_context'),
                                              mo.group('right_context')))
                
            context = ''
            if mo.group('left_context'):
                context = mo.group('left_context')
            
            po_left = int(mo.group('left_port_number'))
            po_right = int(mo.group('right_port_number'))
            for po in range(po_left, po_right + 1):
                ret.append('{}{}'.format(context, po))

        return ret
    #---

    def run(self, terms, variables, **kwargs):
        return self._do_process_csrange(terms, variables)
    #---
