import xml.etree.cElementTree as et
import urllib2
import datetime

class PowerdnsNet(object):
    def __init__(self,apikey):
        self.apikey=apikey
        self.baseurl="https://www.powerdns.net/services/express.asmx"
        self.cache_zonename_id=None
        self.debug=False

    def add_native_domain(self,zonename):
        """Create domain, returns Zone object"""
        result = self.soap_request('addNativeDomain',dict(domainName=zonename))
        self.clear_cache() # invalidate zone map. In the future we might check for existing map and add the new zone
        return self._node_to_zone(result)

    def add_record_to_zone(self,zone,name,content,rtype='A',ttl=3600,prio=0):
        """Add record to zone, returns new record object"""
        zoneid=self.expect_zone_id(zone)
        args={
            'zoneId':zoneid,
            'Name':name,
            'Type':rtype,
            'Content':content,
            'TimeToLive':ttl,
            'Priority':prio,
        }
        result=self.soap_request('addRecordToZone',args)
        record=self._node_to_record(result)
        return record

    def delete_all_records_for_domain(self,zone):
        zoneid=self.expect_zone_id(zone)
        result=self.soap_request('deleteAllRecordsForDomain',dict(zoneId=zoneid))

    def delete_record(self,record):
        """Delete a record (by id)"""
        recordid=self._expect_record_id(record)
        result=self.soap_request('deleteRecordById',dict(recordId=recordid))

    def delete_zone(self,zone):
        """Delete a zone (by name or id)"""
        zoneid=self.expect_zone_id(zone)
        result=self.soap_request('deleteZoneById',dict(zoneId=zoneid))

    def update_record(self,recordobject):
        """Rewrite a record based on recordid"""
        assert type(recordobject)==Record
        args={
            'recordId':recordobject.id,
            'Name':recordobject.name,
            'Type':recordobject.type.upper(),
            'Content':recordobject.content,
            'TimeToLive':recordobject.ttl,
            'Priority':recordobject.prio,
        }
        result=self.soap_request('updateRecord',args)

    def list_records(self,zone,rtype=None):
        """Returns a list of all records in a zone. If rtype is specified, only returns that record type. Return value is a list of Record objects"""
        zoneid=self.expect_zone_id(zone)
        if rtype!=None: # TODO: doesn't work yet... argument order doesn't seem to be the prob. what else?
            recordlist = self.soap_request("listRecordsByType",dict(zoneId=zoneid,Type=rtype.upper()))
        else:
            recordlist = self.soap_request("listRecords",dict(zoneId=zoneid))

        retlist=[]

        for rec in recordlist:
            record=self._node_to_record(rec)
            retlist.append(record)
        return retlist

    def list_zones(self,updatecache=True):
        """Returns a list of all zone names"""
        zoneids={}
        zonelist=self.soap_request("listZones")

        zones=[]
        for zonenode in zonelist:
            zoneobj=self._node_to_zone(zonenode)
            zones.append(zoneobj)
            zoneid=zoneobj.id
            zonename=zoneobj.name

            if zoneid!=None and zonename!=None:
                zoneids[zonename]=zoneid
        self.cache_zonename_id= zoneids
        return zones

    def renew_zone(self,zone):
        zoneid=self.expect_zone_id(zone)
        result=self.soap_request('renewZone',dict(zoneId=zoneid))

    def clear_cache(self):
        """forget everything we've cached from previous calls"""
        self.cache_zonenames=None

    def expect_zone_id(self,value):
        if type(value)==int:
            return value
        elif type(value) in (str,unicode):
            return self.zoneid_by_name(value)
        elif type(value)==Zone:
            return value.id
        else:
            raise ValueError("Expecting Zone object/zone name/zone id")

    def _expect_record_id(self,value):
        if type(value)==int:
            return value
        elif type(value)==Record:
            return value.id
        else:
            raise ValueError("Expecting Record object or record id")

    def zoneid_by_name(self,zonename):
        if self.cache_zonename_id==None:
            self.list_zones(updatecache=True)
        assert type(self.cache_zonename_id)==dict
        if zonename in self.cache_zonename_id:
            return self.cache_zonename_id[zonename]
        else:
            raise Exception("Zone not found: %s"%zonename)

    def _build_soap_request(self,method,arguments=None):
        if arguments==None:
            arguments=dict()

        data = """<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>"""
        data+="""<%s xmlns="http://powerdns.net/express">"""%method
        for name,value in arguments.iteritems():
             data+="""<%s>%s</%s>
             """%(name,value,name)
        data+="</%s>"%method
        data+="""</soap12:Body>
</soap12:Envelope>"""
        return data

    def soap_request(self,method,arguments=None):
        url = self.baseurl+'?apikey='+self.apikey
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8'
        }
        data = self._build_soap_request(method,arguments)
        if self.debug:
            self.debug_out("Request: \n%s"%data)

        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        the_page = response.read()

        if self.debug:
            self.debug_out("Response: \n%s"%the_page)

        tree=et.fromstring(the_page)
        body=tree[0]
        xmlresponse = body[0]
        xmlresult = xmlresponse[0]
        code = xmlresult[0]
        description = xmlresult[1]
        if code.text!='100':
            ex=APIException()
            ex.code=int(code.text)
            ex.description=description.text
            raise ex

        if len(xmlresult)>2:
            interestingpart=xmlresult[2]
            return interestingpart
        else:
            return None

    def debug_out(self,msg):
        print msg

    def _node_to_record(self,node):
        """Transform xml node into Record object"""
        record=Record()
        record.id=int(node[0].text)
        record.zoneid=node[1].text
        record.name=node[2].text
        record.type=node[3].text
        record.content=node[4].text
        record.ttl=node[5].text
        record.priority=node[6].text
        return record

    def _node_to_zone(self,node):
        """Transform xml node into Zone object"""
        zone=Zone()
        zone.id=int(node[0].text)
        zone.name=node[1].text
        zone.master=node[2].text
        #zone.last_check=... looks broken
        zone.type=node[4].text
        #notified_serial= .. always 0)
        zone.account=node[6].text
        zone.active=bool(int(node[7].text))
        datestr=node[8].text
        zone.expires=datetime.datetime.strptime(datestr,"%Y-%m-%dT%H:%M:%S")
        zone.level=node[9].text
        zone.validdns= (node[10].text=='true')
        return zone

class APIException(Exception):
    pass

class Record(object):
    def __init__(self):
        self.id=None
        self.zone_id=None
        self.name=None
        self.type=None
        self.content=None
        self.ttl=0
        self.prio=0
        self.flags=0
        self.active=1

    def __str__(self):
        prio=""
        if self.type in ['SRV','MX']:
            prio=self.prio
        return "%s %s %s %s"%(self.name,self.type,prio,self.content)

class Zone(object):
    def __init__(self):
        self.id=None
        self.name=None
        self.master=None
        self.type=None
        self.account=None
        self.active=True
        self.expires=None
        self.level=None
        self.validdns=None