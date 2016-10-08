#Xen Back

##Description
Scripts for backup vdi from running vms on XenServer

##Author
dkhru (Dmitriy Khristianov)

##Requirements
####XenServer 7 xe tools
####Python 2.7
####Modules:
* argparse
* commands
* json
* time 


## Configuration

Run `./init_config.py > your_config.json`
Edit `your_config.json`
Choice one storage item from `backup_srs` and write it in to `backup_sr`
Remove VM's items that not should be backed up from `vms`
#### Configuration parameters:
* `backup_sr` is Storage where your vdi should be backed up
* `backup_srs` - list of Storages. This parameter not used by backup, it's used for configuration purpose only and after choice `backup_sr` you can remove it.
* `vms` - list of VM's that should be backed up.

## Run backup
After configuration complete you may run `./backup.py --config /path/to/your_config.json`
