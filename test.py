#!/usr/bin/env python3

from Tmutil import *
import json
import sys
from secrets import *

# For testing
from distutils.version import LooseVersion
from datetime import datetime
from pathlib import Path

tm = Tmutil()

def print_json(dict):
  print(json.dumps(dict, indent=2))

def test_status(function, bool):
  if bool:
    print("%s: pass" % function)
  else:
    print("%s: fail" % function)



# tm.setdestination()
o = tm.setdestination(url)
o = tm.setdestination(url2, append=True)

# tm.status()
status = tm.status()

# {
#   'BackupPhase': 'Copying',
#   'ClientID': 'com.apple.backupd',
#   'DateOfStateChange': datetime.datetime(2020, 6, 3, 17, 50, 29),
#   'DestinationID': '2171D002-000C-4756-9197-2A311100BBEE',
#   'DestinationMountPoint': '/Volumes/Time Machine Backups',
#   'FirstBackup': True,
#   'Percent': 0.5471264777146045,
#   'Progress': {
#     'TimeRemaining': 3341,
#     '_raw_totalBytes': 148612509696,
#     'bytes': 90344265527,
#     'files': 539625,
#     'totalBytes': 163473760665,
#     'totalFiles': 618801
#   },
#   'Running': True,
#   'Stopping': False,
#   '_raw_Percent': 0.6079183085717829
# }
print(status['Running'])


sys.exit()

# tm.version()
if LooseVersion(tm.version()):
  test_status('version', True)
else:
  test_status('version', False)



# tm.setdestination()
o = tm.setdestination(url)
test_status('setdestination', o)

# exclude all the things
# tm.addexclusion()
#   tmutil addexclusion -p /Library /Applications /bin /cores /etc /opt /private /sbin /tmp /usr /var /Users/kauffman
system_exclude = [ '/Library', '/Applications', '/bin', '/cores', '/etc', '/opt', '/private', '/sbin', '/tmp', '/usr', '/var' ]
user_exclude = [ '/Users/kauffman' ]
exclusions = []
exclusions.extend(system_exclude)
exclusions.extend(user_exclude)
options = [ '-p' ]
options.extend(exclusions)
test_status('addexclusion', tm.addexclusion(options))

# tm.isexcluded()
l = tm.isexcluded(['/Users/kauffman', '/foo/bar', '/Library'])
m = tm.isexcluded([])
if isinstance(l, list) and isinstance(m, list):
  test_status('isexcluded', True)
else:
  test_status('isexcluded', False)


# tm.removeexclusion()
test_status('removeexlusion', tm.removeexclusion(user_exclude) )


# add user exclude back
tm.addexclusion(user_exclude)


# tm.enable()
test_status('enable', tm.enable())


# tm.startbackup()
test_status('startbackup', tm.startbackup())


# tm.localsnapshot()
localsnapshot = tm.localsnapshot()
deleteme = datetime.strptime(localsnapshot, tm.dateformat)
if isinstance(deleteme, datetime):
  test_status('localsnapshot', True)
else:
  test_status('localsnapshot', False)


# tm.latestbackup()
latest_backup = tm.latestbackup()
if isinstance(latest_backup, list) and latest_backup:
  test_status('latestbackup', True)
else:
  test_status('latestbackup', False)


# tm.listbackups()
backuplist = tm.listbackups()
if isinstance(backuplist, list) and latest_backup:
  test_status('listbackups', True)
else:
  test_status('listbackups', False)


# tm.destinationinfo()
di = tm.destinationinfo()
if isinstance(di, dict):
  test_status('destinationinfo', True)
else:
  test_status('destinationinfo', False)


# tm.listlocalsnapshotdates()
li = tm.listlocalsnapshotdates()
if isinstance(li, list):
  test_status('listlocalsnapshotdates', True)
else:
  test_status('listlocalsnapshotdates', False)


# tm.machinedirectory()
path = tm.machinedirectory()
if isinstance(path, Path):
  test_status('machinedirectory', True)
else:
  test_status('machinedirectory', False)


# tm.thinlocalsnapshots()
f = tm.thinlocalsnapshots('/')
if isinstance(f, list):
  test_status('thinlocalsnapshots', True)
else:
  test_status('thinlocalsnapshots', False)


# tm.deletelocalsnapshots()
tostr = deleteme.strftime(tm.dateformat)
if isinstance(tostr, str) and tm.deletelocalsnapshots(tostr):
  test_status('deletelocalsnapshots', True)
else:
  test_status('deletelocalsnapshots', False)


# tm.inheritbackup()
# tm.associatedisk()
# tm.calculatedrift()
# tm.uniquesize()
# tm.verifychecksums()
# tm.destinationsearch()
# tm.delete()
# tm.restore()
# tm.compare()


sys.exit()
# tm.removedestination()
#   remove all destinations
successfull = False
destinations = tm.destinationinfo()['Destinations']
for dest in destinations:
  if tm.removedestination(dest['ID']):
    successfull = True
test_status('removedestinations', successfull)

# tm.stopbackup()
test_status('stopbackup', tm.stopbackup())

# tm.disable()
test_status('disable', tm.disable())
