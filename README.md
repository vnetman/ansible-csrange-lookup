# ansible-csrange-lookup
csrange is an ansible lookup plugin that listifies ranges of the form "Gi1/1-8,Te1/1-4", "11-20,4001-4095" etc.

In addition, abbreviated interface types e.g. "Te" will be expanded to "TenGigabitEthernet". The following interface types are recognized:

* 'Ethernet'
* 'FastEthernet'
* 'FortyGigabitEthernet'
* 'GigabitEthernet'
* 'HundredGigabitEthernet'
* 'Loopback'
* 'Port-channel'
* 'TenGigabitEthernet'
* 'Tunnel'
* 'TwentyfiveGigabitEthernet'
* 'Vlan'

## Example 1:

    - name: Test case 1
      debug:
        msg: "{{ item }}"
      with_csrange:
        - 'Fo2/1/4-14,Te3/12'

will result in:

```
TASK [Test case 1] *******************************************************************************************************************************************
ok: [localhost] => (item=FortyGigabitEthernet2/1/4) => {
    "msg": "FortyGigabitEthernet2/1/4"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/5) => {
    "msg": "FortyGigabitEthernet2/1/5"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/6) => {
    "msg": "FortyGigabitEthernet2/1/6"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/7) => {
    "msg": "FortyGigabitEthernet2/1/7"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/8) => {
    "msg": "FortyGigabitEthernet2/1/8"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/9) => {
    "msg": "FortyGigabitEthernet2/1/9"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/10) => {
    "msg": "FortyGigabitEthernet2/1/10"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/11) => {
    "msg": "FortyGigabitEthernet2/1/11"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/12) => {
    "msg": "FortyGigabitEthernet2/1/12"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/13) => {
    "msg": "FortyGigabitEthernet2/1/13"
}
ok: [localhost] => (item=FortyGigabitEthernet2/1/14) => {
    "msg": "FortyGigabitEthernet2/1/14"
}
ok: [localhost] => (item=TenGigabitEthernet3/12) => {
    "msg": "TenGigabitEthernet3/12"
}
```

## Example 2

### Playbook:
    - name: Test case 2
      vars:
        ip_prefix: 10.133
        ip_mask: 255.255.255.0
        svi_list: '1-5,11-15'
      template: src=svi_gen.j2 dest=svi_gen.cfg

### Jinja2 template:

```
#jinja2:lstrip_blocks: True

{% for svi in lookup('csrange', svi_list, wantlist=True) %}
interface Vlan{{ svi }}
no shut
ip address {{ ip_prefix }}.{{ svi }}.1 {{ ip_mask }}
{% endfor %}
```

### Generated configuration (svi_gen.cfg)
```
interface Vlan1
no shut
ip address 10.133.1.1 255.255.255.0
interface Vlan2
no shut
ip address 10.133.2.1 255.255.255.0
interface Vlan3
no shut
ip address 10.133.3.1 255.255.255.0
interface Vlan4
no shut
ip address 10.133.4.1 255.255.255.0
interface Vlan5
no shut
ip address 10.133.5.1 255.255.255.0
interface Vlan11
no shut
ip address 10.133.11.1 255.255.255.0
interface Vlan12
no shut
ip address 10.133.12.1 255.255.255.0
interface Vlan13
no shut
ip address 10.133.13.1 255.255.255.0
interface Vlan14
no shut
ip address 10.133.14.1 255.255.255.0
interface Vlan15
no shut
ip address 10.133.15.1 255.255.255.0
```

## More information

Examples of legal strings:
* `'1-10,21-40,50,71-110,'` # integers (e.g. vlan ids)
* `'Gi1/1- 48'`             # "Gi1/" is assumed. Also note spaces allowed anywhere, will be stripped before processing; 
* `'Te3/1-Te3/4'`           # "Te3/" can be explicitly mentioned on the right-hand side of the "-", if you prefer
* `'Te3/1-4,,Te 4/1-4'`     # extraneous "," will be ignored
* `'Te2/1-12, Gig 5/37-48,'`# Can mix and match "Te2/" and "Gi5/"
* `'Gi1-3'`                 # Interfaces don't need to have a slot, i.e. no "/" is OK
* `'Fo2/2/1-4'`             # Three-number format (e.g. chassis/slot/port)
* `'Te3/1-1'`               # Not really a range, but syntax is legal; will just return the single item "Te3/1"
* `'Te3/1-te3/4'`           # Terms on either side of the "-" need not have the same spelling and case ("Te" vs "te"); both will be expanded to "TenGigabitEthernet"
* `'Te3/1-Ten3/4'`          # Terms on either side of the "-" need not have the same spelling and case ("Te" vs "Ten"); both will be expanded to "TenGigabitEthernet"

Not supported:
* `'Te3/1-Te4/48'`  # Terms on either side of the "-" must have the same prefix ("Te3/" vs "Te4/")
* `'Te3/4-1'`       # Range has to be ascending ("4-1" is in descending order)
* `'Te3/1.101-108'` # Subinterface support

