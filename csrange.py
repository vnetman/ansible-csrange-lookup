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
    - name: Debug messages
      debug:
        msg: "{{ item }}"
      with_csrange:
        - 'Fo1/4-14,Te3/12'

    - name: SVI creation
      vars:
        ip_prefix: 10.133
        ip_mask: 255.255.255.0
        svi_list: '1-5,11-15'
      template: src=svi_gen.j2 dest=svi_gen.cfg

where the template code in svi_gen.j2 looks like:

{% for svi in lookup('csrange', svi_list, wantlist=True) %}
interface Vlan{{ svi }}
no shut
ip address {{ ip_prefix }}.{{ svi }}.1 {{ ip_mask }}
{% endfor %}
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
from ansible.module_utils._text import to_native

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

# Regex to grab the interface type from the left/right context (e.g. "Gi"
# from "Gi5/"). This is needed for the "expansion" functionality
re_abbrev_intf_type = re.compile(
    r'''(
    ^(?P<intf_context>[A-Za-z]+)
    (?P<context_tail>.*)$
    )''', re.VERBOSE)

# Known interface types
known_interface_types = ('Ethernet',
                         'FastEthernet',
                         'FortyGigabitEthernet',
                         'GigabitEthernet',
                         'HundredGigabitEthernet',
                         'Loopback',
                         'Port-channel',
                         'TenGigabitEthernet',
                         'Tunnel',
                         'TwentyfiveGigabitEthernet',
                         'Vlan',)
    
class LookupModule(LookupBase):
    
    def _maybe_expand_interface_name(self, abbrev):
        """Take something like 'Gi5/' or 'gig5/' via the 'abbrev' parameter 
        and return the expanded version, like 'GigabitEthernet5/'. If the
        expansion is not possible (e.g. if the abbrev is an empty string)
        or if the expanded version is ambiguous (e.g. 'F3/1' can be either
        'FortyGigabitEthernet3/1' or 'FastEthernet3/1'), return abbrev 
        itself."""
        
        mo = re_abbrev_intf_type.search(abbrev)
        if not mo:
            return abbrev

        intf_context = mo.group('intf_context')
        context_tail = mo.group('context_tail')

        # Do a case-insensitive "startswith" test against the intf_context
        # for all the known interface types.
        re_to_match = re.compile('^{}.*$'.format(intf_context), re.I)
        found = []
        for ki in known_interface_types:
            if re_to_match.match(ki):
                found.append(ki)

        # If there were no matches, or if there was more than one match,
        # return the given abbrev argument unmodified.
        if len(found) != 1:
            return abbrev
        
        return found[0] + context_tail
    #---
    
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
                ret.append(to_native(self._maybe_expand_interface_name(sr)))
                continue
            
            # Apply the regex
            mo = re_subrange.search(sr)
            if not mo:
                raise AnsibleError('"{}" cannot be parsed'.format(sr))

            left_context = ''
            if mo.group('left_context'):
                left_context = self._maybe_expand_interface_name(mo.group('left_context'))
                
            if mo.group('right_context'):
                right_context = self._maybe_expand_interface_name(mo.group('right_context'))
                if left_context != right_context:
                    raise AnsibleError('Failed to parse "{}": '
                                       'left hand side context "{}" is '
                                       'different from right hand side '
                                       'context "{}"'.
                                       format(sr, mo.group('left_context'),
                                              mo.group('right_context')))
                
            try:
                po_left = int(mo.group('left_port_number'))
                po_right = int(mo.group('right_port_number'))
            except ValueError as e:
                raise AnsibleError('Failed to parse "{}": '
                                   'ValueError "{}"'.
                                   format(sr, to_native(e)))

            if po_right < po_left:
                raise AnsibleError('Failed to parse "{}": '
                                   'range from {} to {} is not obvious'.
                                   format(sr, po_left, po_right))
            
            for po in range(po_left, po_right + 1):
                ret.append(to_native('{}{}'.format(left_context, po)))

        return ret
    #---

    def run(self, terms, variables, **kwargs):
        return self._do_process_csrange(terms, variables)
    #---
