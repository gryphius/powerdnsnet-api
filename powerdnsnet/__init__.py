import xml.etree.cElementTree as et
import urllib2


class PowerdnsNet(object):
    def __init__(self,apikey):
        self.apikey=apikey
        self.baseurl="https://www.powerdns.net/services/express.asmx"

        self.cache_zonename_id=None

        self.debug=False

    def add_native_domain(self,zone_name):
        raise Exception("not implemented")

    def add_record_to_zone(self,zone,name,content,rtype='A',ttl=3600,prio=0):
        """Add record to zone, returns ID of the new record"""
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
        for child in result:
            if child.tag=='{http://powerdns.net/express}Id':
                return int(child.text)

    def delete_all_records_for_domain(self):
        raise Exception("not implemented")

    def delete_record_by_id(self,recordid):
        result=self.soap_request('deleteRecordById',dict(recordId=recordid))

    def delete_zone_by_id(self):
        raise Exception("not implemented")

    def delete_zone_by_name(self):
        raise Exception("not implemented")

    def update_record(self):
        raise Exception("not implemented")

    def list_records(self,zone,rtype=None):
        """Returns a list of all records in a zone. If rtype is specified, only returns that record type. Return value is a list of Record objects"""
        zoneid=self.expect_zone_id(zone)
        if rtype!=None: # TODO: doesn't work yet... argument order doesn't seem to be the prob. what else?
            recordlist = self.soap_request("listRecordsByType",dict(zoneId=zoneid,Type=rtype.upper()))
        else:
            recordlist = self.soap_request("listRecords",dict(zoneId=zoneid))

        retlist=[]

        for rec in recordlist:
            record=Record()
            record.id=rec[0].text
            record.zoneid=rec[1].text
            record.name=rec[2].text
            record.type=rec[3].text
            record.content=rec[4].text
            record.ttl=rec[5].text
            record.priority=rec[6].text
            retlist.append(record)
        return retlist

    #def list_records_by_type(self): # included in list_records
    #    raise Exception("not implemented")

    def list_zones(self,updatecache=True):
        """Returns a list of all zone names"""
        zoneids={}
        zonelist=self.soap_request("listZones")
        for zone in zonelist:
            zoneid=None
            zonename=None
            for child in zone:
                if child.tag=='{http://powerdns.net/express}Id':
                    zoneid=child.text
                if child.tag=='{http://powerdns.net/express}Name':
                    zonename=child.text
            if zoneid!=None and zonename!=None:
                zoneids[zonename]=zoneid
            else:
                #should we warn here?
                continue
        self.cache_zonename_id= zoneids
        return sorted(zoneids.keys())

    def renew_zone(self):
        raise Exception("not implemented")


    def clear_cache(self):
        """forget everything we've cached from previous calls"""
        self.cache_zonenames=None

    def expect_zone_id(self,value):
        if type(value)==int:
            return value
        else:
            return self.zoneid_by_name(value)

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
        self.hostnaster=None
        self.serial=0
        self.flags=0
        self.active=1
        self.ttl=0
        self.ownerid=0
        self.master=None
        self.expired=None
        self.created=None


class BaseResponse(object):
    def __init__(self):
        self.code=0
        self.description=''

class AddNativeDomain_Response(BaseResponse):
    def __init__(self):
        pass
