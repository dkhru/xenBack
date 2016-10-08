#!/usr/bin/python

import sys, json, commands, time, argparse

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
   parser.add_argument(
       '--stopOnError',
        type=bool,
       default=False,
       help="If True exit program on first occurred, otherwise backap next VM.")
   args = parser.parse_args()
   result = json.load(args.config, object_pairs_hook=deunicodify_hook)
   result.update({'stopOnError':args.stopOnError})
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

def log(message):
    print time.strftime("%Y-%m-%d %H:%M", time.gmtime())+' '+message

def delete_old_vdi(vm,sr):
    cmd="xe vdi-list sr-uuid="+sr.get("uuid")+" tags:contains="+vm.get("uuid")
    output = commands.getoutput(cmd)
    for vdi in output.split("\n\n\n"):
      lines = vm.splitlines()
      uuid = lines[0].split(":")[1][1:]
      cmd = "xe vdi-destroy uuid="+uuid
      log(cmd)
      commands.getoutput(cmd)

def backup_vm(vm,sr):
   cmd="xe vm-param-get param-name=power-state uuid="+vm.get("uuid")
   vmps=commands.getoutput(cmd)
   if vmps!="running":
       log("Skip backup for "+vm.get("name")+" UUID:"+vm.get("uuid")+" power-state is "+vmps)
       return False
   timestamp = time.strftime("%Y-%m-%d %H:%M", time.gmtime())
   log("Creating snapshot for "+vm.get("name")+" UUID:"+vm.get("uuid"))
   cmd = "xe vm-snapshot uuid=" + vm.get("uuid") + " new-name-label="+vm.get("name")+' '+timestamp
   log(cmd)
   (status, snapshot_uuid) = commands.getstatusoutput(cmd)
   if status!=0 :
       log("Can not create snapshot for "+ vm.get("name")+" UUID:"+vm.get("uuid")+" "+snapshot_uuid)
       return False
   log("Convert snapshot to template "+vm.get("name")+" UUID:"+snapshot_uuid)
   cmd = "xe template-param-set is-a-template=false ha-always-run=false uuid="+snapshot_uuid
   log(cmd)
   commands.getoutput(cmd)
   delete_old_vdi(vm,sr)
   for vdi in get_vm_vdis(snapshot_uuid) :
       cmd = "xe vdi-copy sr-uuid="+sr.get("uuid")+" uuid="+vdi.get("uuid")
       log(cmd)
       (status, vdi_uuid) = commands.getstatusoutput(cmd) #backup vdi uuid
       if status!=0 :
            log(
                "Can not copy vdi for "+ vm.get("name")+" UUID:"+vm.get("uuid")+" "
                +snapshot_uuid
                +" VDI_name:"+vdi.get("name"))
            return False
       cmd = "xe vdi-param-set name-description=Backup VM:"+vm.get("name")+" VDI:" +vdi.get("name")+" on "+timestamp+" uuid="+vdi_uuid
       log(cmd)
       commands.getoutput(cmd)
       log(cmd)
       cmd = "xe vdi-param-add param-name=tags uuid="+vdi_uuid+" param-key="+vm.get("uuid")
       log(cmd)
       commands.getoutput(cmd)
   cmd = "xe vm-uninstall uuid=" + snapshot_uuid + " force=true"
   log(cmd)
   commands.getoutput(cmd)
   return True

conf = get_config()
cnt_v = 0
cnt_e = 0
log(conf)
for vm in conf.get('vms') :
    res=backup_vm(vm, conf.get("backup_sr"))
    if res:
        cnt_v+=1
    else:
        cnt_e+=1
        if conf.get("stopOnError"):
         sys.exit(1)
log("Backup complete Backed up "+cnt_v+" VM's, "+cnt_e+" occurred.")