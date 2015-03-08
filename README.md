python client API implementation for powerdns.net DNS hosting

Notes:
 * instantiate the PowerdnsNet object with the API key found in your powerdns control panel (MYPOWERDNS -> API Access)
 * if a method expects a 'zone' argument this can be either a Zone object as returned by list_zones/add_native_domain, a zone name or the zone id
 * if a method expects a 'record' argument this can be either a Record object as returned by list_records/add_record_to_zone or a record id
 * the API does not to any client-side input validation

Example usage

```python

#!/usr/bin/python
import os
from powerdnsnet import PowerdnsNet

apikey=open(os.path.expanduser("~/powerdnsnet-api-key.txt"),'r').read().strip()
api=PowerdnsNet(apikey)
zones=api.list_zones()

for zone in zones:
    print "### %s ###"""%zone.name
    print "Zone id: %s"%api.zoneid_by_name(zone.name)
    print "Records"
    records=api.list_records(zone)
    for r in records:
        print r
    print ""

## create zone
# api.add_native_domain('example.com')

## renew (add one year)
# api.renew_zone('example.com')

## add record
#record=api.add_record_to_zone('example.com','www.example.com','127.0.0.2')

## update record
#record.content='3.2.1.0'
#api.update_record(record)

## delete record
#api.delete_record(record)

## clear zone
#api.delete_all_records_for_domain('example.com')

## delete zone
#api.delete_zone('example.com')

```