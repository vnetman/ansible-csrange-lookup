# ansible-csrange-lookup
csrange is an ansible lookup plugin that listifies ranges of the form "Gi1/1-8,Te1/1-4", "11-20,4001-4095" etc.

E.g. this play

```
---
- name: test the csrange plugin
  gather_facts: no
  hosts: localhost
  tasks:
    - debug:
        msg: "{{ item }}"
      with_csrange:
        - 'Fo1/1/1-4,Gi1-3,Te1/3'
```

will result in:

```
ok: [localhost] => (item=Fo1/1/1) => {
    "msg": "Fo1/1/1"
}
ok: [localhost] => (item=Fo1/1/2) => {
    "msg": "Fo1/1/2"
}
ok: [localhost] => (item=Fo1/1/3) => {
    "msg": "Fo1/1/3"
}
ok: [localhost] => (item=Fo1/1/4) => {
    "msg": "Fo1/1/4"
}
ok: [localhost] => (item=Gi1) => {
    "msg": "Gi1"
}
ok: [localhost] => (item=Gi2) => {
    "msg": "Gi2"
}
ok: [localhost] => (item=Gi3) => {
    "msg": "Gi3"
}
ok: [localhost] => (item=Te1/3) => {
    "msg": "Te1/3"
}

```
Examples of legal strings:
* `'1-10,21-40,50,71-110,'` # integers (e.g. vlan ids)
* `'Gi1/1- 48'`             # "Gi1/" is assumed. Also note spaces allowed anywhere, will be stripped before processing; 
* `'Te3/1-Te3/4'`           # "Te3/" can be explicitly mentioned on the right-hand side of the "-", if you prefer
* `'Te3/1-4,,Te 4/1-4'`     # extraneous "," will be ignored
* `'Te2/1-12, Gig 5/37-48,'`# Can mix and match "Te2/" and "Gi5/"
* `'Gi1-3'`                 # Interfaces don't need to have a slot, i.e. no "/" is OK
* `'Fo2/2/1-4'`             # Three-number format (e.g. chassis/slot/port)

Not supported:
* `'Te3/1-Te4/48'`  # Terms on either side of the "-" must have the same spelling and case ("Te3/" vs "Te4/")
* `'Te3/1-te3/4'`   # Terms on either side of the "-" must have the same spelling and case ("Te" vs "te")
* `'Te3/1-Ten3/4'`  # Terms on either side of the "-" must have the same spelling and case ("Te" vs "Ten")
* `'Te3/1.101-108'` # Subinterface support
