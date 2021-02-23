#!/usr/bin/env python3

from Tmutil import *
import json
import sys
from secrets import *

tm = Tmutil()

# Remove 'tm2.example.com' dest so we can test
ids = tm.destinationsearch('tm2.example.com')
if ids:
  print('Removing tm2.example.com: %s' % ids[0])
  tm.removedestination(ids[0])

# search for our destination
ids = tm.destinationsearch('tm2.example.com')
if ids:
  print('We already added our destination')
else:
  dests = tm.destinationinfo()
  if 'Destinations' in dests.keys():
    # Our destination is not added but there are other destinations.
    #   We'll want to append ours
    append = True
    print("append: %s" % append)
  else:
    # no destinations exist
    append = False
    print("append: %s" % append)

  print('Adding new destination')
  # Add our destination
  o = tm.setdestination(url, append=append)
