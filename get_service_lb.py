#!/usr/bin/env python
from pykube.objects import Service
from pykube.config import KubeConfig
from pykube.http import HTTPClient
import sys
import os
import utils

def get_lb_from_service(service_name):
    #api = HTTPClient(KubeConfig.from_file("{0}/.kube/config".format(os.environ['HOME'])))
    api = HTTPClient(KubeConfig.from_service_account())
    s = Service.objects(api).filter(namespace="default")
    try:
        lb_name = s.get_by_name(service_name).obj['status']['loadBalancer']['ingress'][0]['hostname']
    except KeyError:
        return False
    return lb_name

def wait_for_lb_name(service_name):
    return utils.timeout(120, 2)(get_lb_from_service)(service_name)

if __name__ == "__main__":
    print get_lb_from_service(sys.argv[1])
