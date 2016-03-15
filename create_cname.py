#!/usr/bin/env python
import sys
import boto3
import utils
import time

def create_rr(record, val):
    client = boto3.client('route53')
    c = {'Changes': [{'Action':
                      "UPSERT",
                      'ResourceRecordSet': {"Name": record,
                                            'Type': "CNAME",
                                            'TTL': 60,
                                            "ResourceRecords": [{"Value": val}]}}]}
    
    zone = ".".join(record.split(".")[1:])
    zones = client.list_hosted_zones()['HostedZones']
    zid = [z['Id'] for z in zones if z['Name'] == "{0}.".format(zone)][0]
    change = client.change_resource_record_sets(HostedZoneId=zid, ChangeBatch=c)
    return change['ChangeInfo']['Id']

def is_change_complete(change_id):
    client = boto3.client('route53')
    change = client.get_change(Id=change_id)
    if change['ChangeInfo']['Status'] == "INSYNC":
        return True
    return False

if __name__ == "__main__":
    record = sys.argv[1]
    val = sys.argv[2]
    change_id = create_rr(record, val)
    result = utils.timeout(120, 2)(is_change_complete)(change_id)
    sys.exit(0)
