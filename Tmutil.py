import subprocess
import plistlib
import re
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime

class Tmutil:

  def __init__(self):
    self.binpath = '/usr/bin/tmutil'
    self.dateformat = '%Y-%m-%d-%H%M%S' # For use with 'datetime'


  """ _command:
    Returns: standard out, standard error, and the exit code
    stdout, stderr, exitcode = _command(['/usr/bin/tmutil', verb, options])
      verb:    Main options in 'tmutil'.
      options: Should be a list, even if only one item
  """
  def _command(self, verb, options = []):
    args = [ self.binpath ]
    args.append(verb)
    args.extend(options)
    out = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    (stdout, stderr) = out.communicate()
    return stdout, stderr, out.returncode


  """ _ec_to_bool:
    Returns True or False
    Converts exit code from 'tmutil' to Success(True) or Failure(False)
  """
  def _ec_to_bool(self, ec):
    if ec == 0:
      return True
    else:
      return False


  """ _remove_empty_string_from_list:
    Returns list without empty fields
    Provide: list
  """
  def _remove_empty_string_from_list(self, list):
    return [i for i in list if i]


  """ _remove_value_from_list:
    Returns a list without the value you specified
    Provide: list, item to be removed
    Returns: list without all occurences of 'item'
  """
  def _remove_value_from_list(self, list, item):
    return [i for i in list if i != item]


  """ version:
    Returns string with version
  """
  def version(self):
    stdout, stderr, ec = self._command('version')
    if isinstance(stdout, bytes) and self._ec_to_bool(ec):
      version = stdout.decode("utf-8")
      # Sample: tmutil version 4.0.0 (built Feb 22 2019)\n
      result = re.sub(r'^tmutil version ([0-9].*) \(built.*\)\n$',  r'\1', version)
      return result
    else:
      return False


  """ status:
    Returns dictionary of the current status
  """
  def status(self):
    stdout, stderr, ec = self._command('status', ['-X'])
    if self._ec_to_bool(ec):
      return plistlib.loads(stdout, fmt=plistlib.FMT_XML)
    else:
      return False


  """ enable:
    Returns command success(True) or failure(False)
  """
  def enable(self):
    stdout, stderr, ec = self._command('enable')
    return self._ec_to_bool(ec)


  """ disable:
    Returns command success(True) or failure(False)
  """
  def disable(self):
    stdout, stderr, ec = self._command('disable')
    return self._ec_to_bool(ec)


  """ startbackup:
    Returns Success(True) or Failure(False)
    Useage: tmutil startbackup [-a | --auto] [-b | --block] [-r | --rotation] [-d | --destination dest_id]
  """
  def startbackup(self, auto=False, block=False, rotation=False, destination=None):
    options = []
    if auto:
      options.append('--auto')
    if block:
      options.append('--block')
    if rotation:
      options.append('--rotation')
    if destination is not None:
      if destid in self.destinationsearch(destid):
        options.extend(['--destination', destid])

    stdout, stderr, ec = self._command('startbackup', options)
    return self._ec_to_bool(ec)


  """ stopbackup:
    Returns: Success(True) or Failure(False)
  """
  def stopbackup(self):
    stdout, stderr, ec = self._command('stopbackup')
    return self._ec_to_bool(ec)


  """ delete:
    Returns: Success(True) or Failure(False)
             If only some fail we return a list of the ones that failed.
    Provide: a list of paths you wish to remove
    Usage: tmutil delete snapshot_path ...
    TODO: test
  """
  def delete(self, snapshot_path_list):
    if isinstance(snapshot_path_list, list) and snapshot_path_list:
      allbackups = self.listbackups()
      to_be_deleted = []
      does_not_exist = []
      for path in snapshot_path_list:
        if path in allbackups:
          to_be_deleted.append(path)
        else:
          does_not_exist.append(path)

      stdout, stderr, ec = self._command('delete', to_be_deleted)

      if not does_not_exist and self._ec_to_bool(ec):
        return True
      elif does_not_exist and self._ec_to_bool(ec):
        return does_not_exist
      else:
        return False


  """ restore: Not supported
  """
  def restore(self):
    return False


  """ compare: Not supported
  """
  def compare(self):
    return False


  """ setdestination:
    Returns:
    Provide:
    Usage: tmutil setdestination [-a]  mount_point
           tmutil setdestination [-ap] afp://user[:pass]@host/share
      -a: append (True, False)
          True: append to the current list of destinations
          False: Replace all existing destinations
      -p: provide password at prompt. => Unsupported
    TODO: Add folder as a destination option
  """
  def setdestination(self, path, append=False):
    allowed_schemes = [ 'afp', 'smb' ]
    o = urlparse(path)
    if o.scheme and (o.scheme in allowed_schemes):
      # means remote
      if append:
        p = [ '-a', path ]
      else:
        p = [ path ]

      # does this destination already exist?
      # tmutil will happily add a destination as many times as you want without checking
      destinations = self.destinationinfo()
      match = False
      submitted_url = "%s://%s@%s%s" % (o.scheme, o.username, o.netloc, o.path)

      if 'Destinations' in destinations.keys():
        for dest in destinations['Destinations']:
          try:
            if submitted_url == dest['URL']:
              match = True
          except KeyError as e:
            # Local backup destinations do not have an "URL"
            pass

      # if not already a destination
      if not match:
        stdout, stderr, ec = self._command('setdestination', p )
        if self._ec_to_bool(ec):
          return True
        else:
          # At this point we might be able to figure out if
          # you need to give tmutil full disk access
          # and let the caller know what to do.
          return False
      else:
        return True

    elif o.scheme == '':
      # local directory
      # Unsupported ATM
      return False
    else:
      # We shouldn't get here
      return False


  """ removedestination:
    Returns: Success(True) or Failure(False)
    Provide: destination ID to be deleted
    Usage: tmutil removedestination destination_id
  """
  def removedestination(self, id):
    # Safety: Does this destination even exist?
    destinations = self.destinationinfo()
    match = False
    if 'Destinations' in destinations.keys():
      for dest in destinations['Destinations']:
        if id == dest['ID']:
          match = True

    if match:
      stdout, stderr, ec = self._command('removedestination', [id])
      if self._ec_to_bool(ec):
        return True

    return False


  """ destinationsearch:
    Returns: a list of destination IDs where the search term matches the URL
      May return an empty list
    Provide: string to match on
    This is not in 'tmutil'
  """
  def destinationsearch(self, match):
    ids = []
    destinations = self.destinationinfo()
    if 'Destinations' in destinations.keys():
      for dest in destinations['Destinations']:
        #print(dest)
        try:
          if re.findall(match, dest['URL']):
            ids.append(dest['ID'])
        except KeyError as e:
          # Local backup destinations do not have an "URL"
          pass

    return ids


  """ destinationinfo:
    Returns: dict
  """
  def destinationinfo(self, destid=None):
    if destid is not None:
      stdout, stderr, ec = self._command('destinationinfo', ['-X', destid])
    else:
      stdout, stderr, ec = self._command('destinationinfo', ['-X'])

    if isinstance(stdout, bytes) and self._ec_to_bool(ec):
      destinations = plistlib.loads(stdout, fmt=plistlib.FMT_XML)
      return destinations
    else:
      return False


  """ addexclusion: Not tested
    Usage:  [-pv] item ...
  """
  def addexclusion(self, items = [], volume=False, fixedpath=False):
    options = []
    # One or the other only
    if fixedpath and volume:
      raise Exception("You may only enable 'volume' or 'fixedpath' or neither.")
      #return False
    else:
      if fixedpath:
        options.append('-p')
      elif volume:
        options.append('-v')

    if items:
      options.extend(items)
      stdout, stderr, ec = self._command('addexclusion', options)
      if self._ec_to_bool(ec):
        return True

    return False


  """ removeexclusion: Not tested
  """
  def removeexclusion(self, items = [], volume=False, fixedpath=False):
    options = []
    # One or the other only
    if fixedpath and volume:
      raise Exception("You may only enable 'volume' or 'fixedpath' or neither.")
      #return False
    else:
      if fixedpath:
        options.append('-p')
      elif volume:
        options.append('-v')

    if items:
      options.extend(items)
      stdout, stderr, ec = self._command('removeexclusion', options)

      if self._ec_to_bool(ec):
        return True
      #/: The operation couldn’t be completed. Invalid argument

    return False

  """ isexcluded: Not tested
  """
  def isexcluded(self, items = []):
    options = ['-X'] # we need XML output
    if items:
      options.extend(items)
      stdout, stderr, ec = self._command('isexcluded', options)
      return plistlib.loads(stdout, fmt=plistlib.FMT_XML)
    else:
      #raise Exception('Provide a list of items to check if excluded, even if the list only contains one item.')
      return []


  """ inheritbackup: Not supported
  """
  def inheritbackup(self):
    return False

  """ associatedisk: Not supported
  """
  def associatedisk(self):
    return False


  """ latestbackup:
    Returns list of 1 item
  """
  def latestbackup(self):
    stdout, stderr, ec = self._command('latestbackup')
    if isinstance(stdout, bytes) and self._ec_to_bool(ec):
      return self._remove_empty_string_from_list(stdout.decode("utf-8").split('\n'))
    else:
      return False


  """ listbackups:
    Returns list
  """
  def listbackups(self):
    if self.machinedirectory():
      stdout, stderr, ec = self._command('listbackups')
      if isinstance(stdout, bytes) and self._ec_to_bool(ec):
        return self._remove_empty_string_from_list(stdout.decode("utf-8").split('\n'))
      else:
        return False
    else:
      return False


  """ machinedirectory:
    Print the path to the current machine directory for this computer.
    Returns: pathlib.PosixPath
  """
  def machinedirectory(self):
    stdout, stderr, ec = self._command('machinedirectory')
    if isinstance(stdout, bytes) and self._ec_to_bool(ec):
      return Path(stdout.decode("utf-8").rstrip())
    else:
      return False


  """ calculatedrift: Not supported
      Usage: calculatedrift machine_directory
  """
  def calculatedrift(self):
    o = self.machinedirectory
    if o:
      stdout, stderr, ec = self._command('calculatedrift', [str(o)])
      if _ec_to_bool(ec):
        return stdout
      else:
        return False
    else:
      return False

  """ uniquesize: Not supported
  """
  def uniquesize(self):
    return False

  """ verifychecksums: Not supported
  """
  def verifychecksums(self):
    return False


  """ localsnapshot:
    Usage: tmutil localsnapshot
      Create local snapshot
    Returns: date as a string
  """
  def localsnapshot(self):
    stdout, stderr, ec = self._command('localsnapshot')
    if isinstance(stdout, bytes) and self._ec_to_bool(ec):
      result = re.sub(r'^Created local snapshot with date: ([0-9].*)\n$', r'\1', stdout.decode("utf-8") )
      # TODO: Should this return a date object?
      return result
    else:
      return False


  """ listlocalsnapshots: Not supported
    Usage: tmutil listlocalsnapshots <mount_point>
    Returns: list of local snapshots
    Provide: mount_point
  """
  def listlocalsnapshots(self, mount_point='/'):
    stdout, stderr, ec = self._command('listlocalsnapshots', [ mount_point ])

    if isinstance(stdout, bytes) and self._ec_to_bool(ec):
      l = stdout.decode("utf-8").split('\n')
      return self._remove_empty_string_from_list(l)
    else:
      return False


  """ listlocalsnapshotdates: Not supported
    Usage: tmutil listlocalsnapshotdates [<mount_point>]
    Provide: mount_point if applicable
    Returns: list of dates or False
  """
  def listlocalsnapshotdates(self, mount_point=None):
    if mount_point:
      stdout, stderr, ec = self._command('listlocalsnapshotdates', [ mount_point ])
    else:
      stdout, stderr, ec = self._command('listlocalsnapshotdates')

    if isinstance(stdout, bytes) and self._ec_to_bool(ec):
      l = stdout.decode("utf-8").split('\n')
      # removing ux output
      l.remove(l[0])
      return self._remove_empty_string_from_list(l)
    else:
      return False


  """ deletelocalsnapshots:
    Usage: tmutil deletelocalsnapshots <snapshot_date>
    Provide: date as a string
    Returns: Success(True) or Failure(False)
  """
  def deletelocalsnapshots(self, datestr):
    stdout, stderr, ec = self._command('deletelocalsnapshots', [ datestr ])
    if isinstance(stdout, bytes) and self._ec_to_bool(ec):
      # Sample output when delete worked:
      #   Deleted local snapshot '2020-05-14-104500'
      # TODO: Should we regex the output string to confirm?
      return True
    else:
      return False


  """ thinlocalsnapshots: Not supported
    Usage: tmutil thinlocalsnapshots <mount_point> [purgeamount] [urgency]
    Provide:
       mount_point (our default is '/')
       purgeamount in bytes (optional)
       urgency: 1,2,3,4 (optional)
                1 = High; 4 = low; => This is a guess, manpage doesn't specify.
    Returns: list or False
  """
  def thinlocalsnapshots(self, mount_point='/', purgeamount=None, urgency=None):
    options = self._remove_value_from_list([ mount_point, purgeamount, urgency ], None)
    stdout, stderr, ec = self._command('thinlocalsnapshots', options)

    if isinstance(stdout, bytes) and self._ec_to_bool(ec):
      l = stdout.decode("utf-8").split('\n')
      # removing ux output
      l.remove(l[0])
      return self._remove_empty_string_from_list(l)
    else:
      return False

