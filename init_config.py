#!/usr/bin/python

import commands, json

def get_vms():
   result = []
   cmd = "xe vm-list is-control-domain=false is-a-snapshot=false"
   output = commands.getoutput(cmd)

   for vm in output.split("\n\n\n"):
      lines = vm.splitlines()
      uuid = lines[0].split(":")[1][1:]
      name = lines[1].split(":")[1][1:]
      result += [{'uuid':uuid, 'name':name}]
   return result

def get_srs():
   result = []
   cmd = "xe sr-list type=lvmoiscsi"
   output = commands.getoutput(cmd)
   for vm in output.split("\n\n\n"):
      lines = vm.splitlines()
      uuid = lines[0].split(":")[1][1:]
      name = lines[1].split(":")[1][1:]
      result += [{'uuid':uuid, 'name':name}]
   return result

print json.dumps({ 'backup_sr':{}, 'backup_srs':get_srs(), 'vms':get_vms()} , sort_keys=True, indent=4)
