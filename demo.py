#!/usr/bin/python
import os
from powerdnsnet import PowerdnsNet


if __name__=='__main__':
    apikey=open(os.path.expanduser("~/powerdnsnet-api-key.txt"),'r').read().strip()
    api=PowerdnsNet(apikey)

    zonenames=api.list_zones()
    print zonenames

    for name in zonenames:
        print "### %s ###"""%name
        print "Zoneid: %s"%api.zoneid_by_name(name)
        print "Records"
        records=api.list_records(name)
        for r in records:
            print r
        print ""
