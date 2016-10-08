#!/usr/bin/python

import json, commands, time, argparse

def deunicodify_hook(pairs):
    new_pairs = []
    for key, value in pairs:
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        new_pairs.append((key, value))
    return dict(new_pairs)

def get_config():
   parser = argparse.ArgumentParser(description='Scripts for backup vdi from running vms on XenServer')
   parser.add_argument(
        '--config',
        required=True,
        type=argparse.FileType('r'),
        help='The config file in json format')
   args = parser.parse_args()
   # f=open('backup.json','r')
   result = json.load(args.config, object_pairs_hook=deunicodify_hook)
   return  result

def get_vms():
   result = []

   cmd = "xe vm-list is-control-domain=false is-a-snapshot=false"
   output = commands.getoutput(cmd)

   for vm in output.split("\n\n\n"):
      lines = vm.splitlines()
      uuid = lines[0].split(":")[1][1:]
      name = lines[1].split(":")[1][1:]
      result += [(uuid, name)]

   return result

def get_vm_vdis(uuid):
    result = []
    cmd = "xe vbd-list empty=false vm-uuid="+uuid
    output = commands.getoutput(cmd)
    for vbd in output.split("\n\n\n"):
       lines = vbd.splitlines()
       vdi_uuid = lines[3].split(":")[1][1:]
       cmd = "xe vdi-param-get param-name=name-label uuid="+vdi_uuid
       vdi_name = commands.getoutput(cmd)
       result += [{'uuid':vdi_uuid, 'name':vdi_name}]
    return result


def backup_vm(vm,sr):
   timestamp = time.strftime("%Y-%m-%d %H:%M", time.gmtime())

   cmd = "xe vm-snapshot uuid=" + vm.get("uuid") + " new-name-label="+vm.get("name")+' '+timestamp
   snapshot_uuid = commands.getoutput(cmd)

   cmd = "xe template-param-set is-a-template=false ha-always-run=false uuid="+snapshot_uuid
   commands.getoutput(cmd)

   for vdi in get_vm_vdis(snapshot_uuid) :
       cmd = "xe vdi-param-set name-label="+vdi.get("name")+" "+timestamp+" uuid="+vdi.get("uuid")
       cmd = "xe vdi-copy sr-uuid="+sr.get("uuid")+" uuid="+vdi.get("uuid")
       commands.getoutput(cmd)

   cmd = "xe vm-uninstall uuid=" + snapshot_uuid + " force=true"
   commands.getoutput(cmd)

conf = get_config()

for vm in conf.get('vms') :
    backup_vm(vm, conf.get("backup_sr"))