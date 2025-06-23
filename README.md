# Ansible Collection - eliminyro.adguard

This collection provides modules for managing AdGuard Home.

## Modules

- `adguard_dns_rewrite` - Manage DNS rewrites in AdGuard Home

## Installation

```bash
ansible-galaxy collection install eliminyro.adguard
```

## Usage

```yaml
- name: Add DNS rewrite
  eliminyro.adguard.adguard_dns_rewrite:
    url: http://192.168.1.1:3000
    username: admin
    password: "{{ adguard_password }}"
    domain: myapp.local
    answer: 192.168.1.100
```
