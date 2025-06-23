#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Your Name <your.email@example.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: adguard_dns_rewrite

short_description: Manage DNS rewrites in AdGuard Home

version_added: "1.0.0"

description:
    - This module allows you to manage DNS rewrite rules in AdGuard Home
    - Supports creating, updating, and deleting DNS rewrite entries
    - Requires AdGuard Home API access

options:
    url:
        description:
            - URL of the AdGuard Home instance
            - Should include protocol and port (e.g., http://192.168.1.1:3000)
        required: true
        type: str
    username:
        description:
            - Username for AdGuard Home authentication
        required: true
        type: str
    password:
        description:
            - Password for AdGuard Home authentication
        required: true
        type: str
    domain:
        description:
            - Domain name to rewrite
        required: true
        type: str
    answer:
        description:
            - IP address or CNAME to resolve to
            - Required when state is 'present'
        required: false
        type: str
    state:
        description:
            - Whether the DNS rewrite should exist or not
        choices: ['present', 'absent']
        default: 'present'
        type: str
    validate_certs:
        description:
            - Whether to validate SSL certificates
        default: true
        type: bool

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = r'''
# Create a DNS rewrite
- name: Add DNS rewrite for local service
  adguard_dns_rewrite:
    url: http://192.168.1.1:3000
    username: admin
    password: secret
    domain: myservice.local
    answer: 192.168.1.100
    state: present

# Remove a DNS rewrite
- name: Remove DNS rewrite
  adguard_dns_rewrite:
    url: http://192.168.1.1:3000
    username: admin
    password: secret
    domain: myservice.local
    state: absent

# Update existing DNS rewrite
- name: Update DNS rewrite IP
  adguard_dns_rewrite:
    url: http://192.168.1.1:3000
    username: admin
    password: secret
    domain: myservice.local
    answer: 192.168.1.101
    state: present
'''

RETURN = r'''
msg:
    description: The output message that the module generates
    type: str
    returned: always
    sample: 'DNS rewrite created successfully'
changed:
    description: Whether the module made any changes
    type: bool
    returned: always
    sample: true
rewrite:
    description: The DNS rewrite entry details
    type: dict
    returned: when state is present
    sample: {
        "domain": "myservice.local",
        "answer": "192.168.1.100"
    }
'''

import base64
import json
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.basic import AnsibleModule


class AdGuardDNSRewrite:
    def __init__(self, module):
        self.module = module
        self.url = module.params['url'].rstrip('/')
        self.username = module.params['username']
        self.password = module.params['password']
        self.domain = module.params['domain']
        self.answer = module.params['answer']
        self.state = module.params['state']
        self.validate_certs = module.params['validate_certs']

        # Create basic auth header
        credentials = base64.b64encode(
            f"{self.username}:{self.password}".encode('utf-8')
        ).decode('utf-8')
        self.headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }

    def get_all_rewrites(self):
        """Get all DNS rewrites from AdGuard Home"""
        url = f"{self.url}/control/rewrite/list"

        response, info = fetch_url(
            self.module,
            url,
            headers=self.headers,
            method='GET'
        )

        if info['status'] != 200:
            self.module.fail_json(
                msg=f"Failed to get DNS rewrites: {info['msg']}",
                status_code=info['status']
            )

        try:
            data = json.loads(response.read())
            return data
        except Exception as e:
            self.module.fail_json(msg=f"Failed to parse response: {str(e)}")

    def find_rewrite(self):
        """Find existing DNS rewrite for the domain"""
        rewrites = self.get_all_rewrites()

        for rewrite in rewrites:
            if rewrite.get('domain') == self.domain:
                return rewrite

        return None

    def create_rewrite(self):
        """Create a new DNS rewrite"""
        if not self.answer:
            self.module.fail_json(
                msg="'answer' parameter is required when state is 'present'"
            )

        url = f"{self.url}/control/rewrite/add"
        data = {
            'domain': self.domain,
            'answer': self.answer
        }

        response, info = fetch_url(
            self.module,
            url,
            data=json.dumps(data),
            headers=self.headers,
            method='POST'
        )

        if info['status'] != 200:
            self.module.fail_json(
                msg=f"Failed to create DNS rewrite: {info['msg']}",
                status_code=info['status']
            )

        return True

    def delete_rewrite(self):
        """Delete an existing DNS rewrite"""
        url = f"{self.url}/control/rewrite/delete"
        data = {
            'domain': self.domain,
            'answer': self.answer
        }

        _unused, info = fetch_url(
            self.module,
            url,
            data=json.dumps(data),
            headers=self.headers,
            method='POST'
        )

        if info['status'] != 200:
            self.module.fail_json(
                msg=f"Failed to delete DNS rewrite: {info['msg']}",
                status_code=info['status']
            )

        return True

    def update_rewrite(self, existing_rewrite):
        """Update an existing DNS rewrite by deleting and recreating"""
        # AdGuard Home doesn't have a direct update API, so we delete and recreate
        # First, delete the old entry
        self.answer = existing_rewrite['answer']
        self.delete_rewrite()

        # Then create the new entry
        self.answer = self.module.params['answer']
        self.create_rewrite()

        return True

    def run(self):
        """Main execution logic"""
        result = {
            'changed': False,
            'msg': '',
            'rewrite': {}
        }

        # Find existing rewrite
        existing_rewrite = self.find_rewrite()

        if self.state == 'present':
            if not existing_rewrite:
                # Create new rewrite
                if not self.module.check_mode:
                    self.create_rewrite()
                result['changed'] = True
                result['msg'] = 'DNS rewrite created successfully'
                result['rewrite'] = {
                    'domain': self.domain,
                    'answer': self.answer
                }
            elif existing_rewrite['answer'] != self.answer:
                # Update existing rewrite
                if not self.module.check_mode:
                    self.update_rewrite(existing_rewrite)
                result['changed'] = True
                result['msg'] = 'DNS rewrite updated successfully'
                result['rewrite'] = {
                    'domain': self.domain,
                    'answer': self.answer
                }
            else:
                # No changes needed
                result['msg'] = 'DNS rewrite already exists with same values'
                result['rewrite'] = existing_rewrite

        elif self.state == 'absent':
            if existing_rewrite:
                # Delete existing rewrite
                if not self.module.check_mode:
                    self.answer = existing_rewrite['answer']
                    self.delete_rewrite()
                result['changed'] = True
                result['msg'] = 'DNS rewrite deleted successfully'
            else:
                # Already absent
                result['msg'] = 'DNS rewrite does not exist'

        return result


def main():
    module_args = dict(
        url=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        domain=dict(type='str', required=True),
        answer=dict(type='str', required=False),
        state=dict(
            type='str',
            choices=['present', 'absent'],
            default='present'
        ),
        validate_certs=dict(type='bool', default=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    # Create and run the AdGuard DNS rewrite handler
    adguard = AdGuardDNSRewrite(module)
    result = adguard.run()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
