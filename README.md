# Ansible Collection - eliminyro.adguard

[![CI](https://github.com/eliminyro/eliminyro.adguard/actions/workflows/main.yml/badge.svg)](https://github.com/eliminyro/eliminyro.adguard/actions)
[![Ansible Galaxy](https://img.shields.io/badge/galaxy-eliminyro.adguard-blue.svg)](https://galaxy.ansible.com/eliminyro/adguard)

This Ansible collection provides modules for managing AdGuard Home DNS server configuration.

## Description

AdGuard Home is a network-wide software for blocking ads and tracking. This collection allows you to automate the management of DNS rewrite rules, making it easy to configure local domain resolution for your services and applications.

## Requirements

- Ansible >= 2.16.0
- AdGuard Home instance with API access enabled
- Network connectivity to AdGuard Home admin interface

## Installation

### From Ansible Galaxy

```bash
ansible-galaxy collection install eliminyro.adguard
```

### From Source

```bash
git clone https://github.com/eliminyro/eliminyro.adguard.git
cd eliminyro.adguard
ansible-galaxy collection build
ansible-galaxy collection install eliminyro-adguard-*.tar.gz
```

## Modules

### adguard_dns_rewrite

Manage DNS rewrite rules in AdGuard Home. This module allows you to:
- Create new DNS rewrite entries
- Update existing rewrite rules  
- Delete DNS rewrite entries
- Ensure idempotent operations

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | str | yes | - | AdGuard Home URL (e.g., `http://192.168.1.1:3000`) |
| `username` | str | yes | - | AdGuard Home admin username |
| `password` | str | yes | - | AdGuard Home admin password |
| `domain` | str | yes | - | Domain name to rewrite |
| `answer` | str | no | - | IP address or CNAME target (required when `state=present`) |
| `state` | str | no | `present` | Whether the rewrite should exist (`present`/`absent`) |
| `validate_certs` | bool | no | `true` | Whether to validate SSL certificates |

## Usage Examples

### Basic Examples

#### Create a simple DNS rewrite

```yaml
- name: Add DNS rewrite for local service
  eliminyro.adguard.adguard_dns_rewrite:
    url: http://192.168.1.1:3000
    username: admin
    password: "{{ adguard_password }}"
    domain: myapp.local
    answer: 192.168.1.100
    state: present
```

#### Remove a DNS rewrite

```yaml
- name: Remove DNS rewrite
  eliminyro.adguard.adguard_dns_rewrite:
    url: http://192.168.1.1:3000
    username: admin
    password: "{{ adguard_password }}"
    domain: myapp.local
    state: absent
```

#### Update an existing DNS rewrite

```yaml
- name: Update DNS rewrite to new IP
  eliminyro.adguard.adguard_dns_rewrite:
    url: http://192.168.1.1:3000
    username: admin
    password: "{{ adguard_password }}"
    domain: myapp.local
    answer: 192.168.1.200
    state: present
```

### Advanced Examples

#### Manage multiple DNS rewrites

```yaml
- name: Configure local development environment
  eliminyro.adguard.adguard_dns_rewrite:
    url: "{{ adguard_url }}"
    username: "{{ adguard_username }}"
    password: "{{ adguard_password }}"
    domain: "{{ item.domain }}"
    answer: "{{ item.ip }}"
    state: present
  loop:
    - { domain: "api.local", ip: "192.168.1.100" }
    - { domain: "web.local", ip: "192.168.1.101" }
    - { domain: "db.local", ip: "192.168.1.102" }
    - { domain: "cache.local", ip: "192.168.1.103" }
```

#### Conditional DNS rewrites

```yaml
- name: Add DNS rewrite only for development environment
  eliminyro.adguard.adguard_dns_rewrite:
    url: "{{ adguard_url }}"
    username: "{{ adguard_username }}"
    password: "{{ adguard_password }}"
    domain: "{{ item.domain }}"
    answer: "{{ item.ip }}"
    state: present
  loop: "{{ dev_services }}"
  when: 
    - environment == "development"
    - item.enabled | default(true)
```

#### Using with check mode

```yaml
- name: Check what DNS rewrites would be created
  eliminyro.adguard.adguard_dns_rewrite:
    url: "{{ adguard_url }}"
    username: "{{ adguard_username }}"
    password: "{{ adguard_password }}"
    domain: test.local
    answer: 192.168.1.50
    state: present
  check_mode: yes
  register: rewrite_check
  
- name: Display check mode results
  debug:
    msg: "Would create rewrite: {{ rewrite_check.changed }}"
```

#### Error handling

```yaml
- name: Create DNS rewrite with error handling
  eliminyro.adguard.adguard_dns_rewrite:
    url: "{{ adguard_url }}"
    username: "{{ adguard_username }}"
    password: "{{ adguard_password }}"
    domain: service.local
    answer: 192.168.1.100
    state: present
    validate_certs: false
  register: result
  failed_when: false
  
- name: Handle connection errors
  debug:
    msg: "Failed to connect to AdGuard: {{ result.msg }}"
  when: result.failed and 'connection' in result.msg | lower

- name: Handle authentication errors  
  debug:
    msg: "Authentication failed - check credentials"
  when: result.failed and 'unauthorized' in result.msg | lower
```

### Playbook Examples

#### Complete AdGuard setup playbook

```yaml
---
- name: Configure AdGuard Home DNS rewrites
  hosts: localhost
  gather_facts: false
  vars:
    adguard_url: "http://{{ adguard_host }}:3000"
    adguard_username: admin
    # Store password in vault: ansible-vault encrypt_string 'password' --name 'adguard_password'

    # Define your local services
    local_services:
      - domain: homeassistant.local
        ip: 192.168.1.50
        description: "Home Assistant"
      - domain: plex.local  
        ip: 192.168.1.51
        description: "Plex Media Server"
      - domain: nas.local
        ip: 192.168.1.52
        description: "Network Attached Storage"
      - domain: pihole.local
        ip: 192.168.1.53
        description: "Pi-hole DNS"

  tasks:
    - name: Create DNS rewrites for local services
      eliminyro.adguard.adguard_dns_rewrite:
        url: "{{ adguard_url }}"
        username: "{{ adguard_username }}"
        password: "{{ adguard_password }}"
        domain: "{{ item.domain }}"
        answer: "{{ item.ip }}"
        state: present
      loop: "{{ local_services }}"
      register: rewrite_results
      
    - name: Display created rewrites
      debug:
        msg: "{{ item.item.description }}: {{ item.item.domain }} -> {{ item.item.ip }}"
      loop: "{{ rewrite_results.results }}"
      when: item.changed
```

#### Cleanup playbook

```yaml
---
- name: Remove development DNS rewrites
  hosts: localhost
  gather_facts: false
  vars:
    adguard_url: "http://{{ adguard_host }}:3000"

    # Development domains to remove
    dev_domains:
      - api-dev.local
      - staging.local
      - test.local
      - debug.local

  tasks:
    - name: Remove development DNS rewrites
      eliminyro.adguard.adguard_dns_rewrite:
        url: "{{ adguard_url }}"
        username: "{{ adguard_username }}"
        password: "{{ adguard_password }}"
        domain: "{{ item }}"
        state: absent
      loop: "{{ dev_domains }}"
```

## Best Practices

### Security

- Store AdGuard credentials in Ansible Vault:
  ```bash
  ansible-vault encrypt_string 'your_password' --name 'adguard_password'
  ```

- Use `no_log: true` when debugging tasks with passwords:
  ```yaml
  - name: Debug without exposing password
    debug:
      var: adguard_result
    no_log: true
  ```

### Performance

- Use `check_mode` to preview changes before applying
- Group multiple rewrites in a single task with loops
- Set `validate_certs: false` only for internal/test environments

### Idempotency

- The module is idempotent - running the same task multiple times will not create duplicates
- Use `changed_when` conditions if you need custom change detection
- Leverage `register` to capture results for conditional tasks

## Troubleshooting

### Common Issues

1. **Connection refused**: Ensure AdGuard Home is running and accessible
2. **Authentication failed**: Verify username and password
3. **SSL errors**: Set `validate_certs: false` for self-signed certificates
4. **Permission denied**: Ensure the user has admin privileges in AdGuard Home

### Debug Mode

Enable debug output to troubleshoot issues:

```yaml
- name: Debug DNS rewrite creation
  eliminyro.adguard.adguard_dns_rewrite:
    url: "{{ adguard_url }}"
    username: "{{ adguard_username }}"
    password: "{{ adguard_password }}"
    domain: debug.local
    answer: 192.168.1.100
    state: present
  register: debug_result
  
- name: Show debug information
  debug:
    var: debug_result
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

GNU General Public License v3.0 or later

See [COPYING](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.

## Author

Pavel Eliminyro (@eliminyro)

## Links

- [GitHub Repository](https://github.com/eliminyro/eliminyro.adguard)
- [Issue Tracker](https://github.com/eliminyro/eliminyro.adguard/issues)
- [AdGuard Home Documentation](https://github.com/AdguardTeam/AdGuardHome)
- [Ansible Collections Documentation](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)
