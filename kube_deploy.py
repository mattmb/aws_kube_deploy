import yaml
import sys
from pykube.objects import Service
from pykube.objects import Pod
from pykube.config import KubeConfig
from pykube.http import HTTPClient
import get_service_lb
import create_cname
import os
import utils
import boto3
import time

def deploy_service(template_pod, template_service, branch, domain_zone):
    #api = HTTPClient(KubeConfig.from_file("{0}/.kube/config".format(os.environ['HOME'])))
    api = HTTPClient(KubeConfig.from_service_account())
    with open(template_service) as t_file:
        ts = yaml.load(t_file)
    svc_name = ts['metadata']['name']
    name = "{0}-{1}".format(svc_name, branch)
    ts['spec']['type'] = 'LoadBalancer'
    ts['spec']['selector']['name'] = name
    ts['metadata']['name'] = name
    ts['metadata']['labels']['name'] = name
    new = Service(api, ts)
    new.create()
    print "New service created"
    with open(template_pod) as t_file:
        tp = yaml.load(t_file)
    name = tp['metadata']['name']
    name = "{0}-{1}".format(name, branch)
    image = tp['spec']['containers'][0]['image']
    image = "{0}:{1}".format(image, branch)
    tp['spec']['containers'][0]['image'] = image
    tp['spec']['containers'][0]['name'] = name
    tp['metadata']['name'] = name
    tp['metadata']['labels']['name'] = name
    new = Pod(api, tp)
    new.create()
    print "New pod created"
    print "Waiting for ELB to spawn"
    lb_name = get_service_lb.wait_for_lb_name(name)
    print "Got ELB {0}".format(lb_name)
    return lb_name, svc_name

def set_healthcheck(lb_name):
    short_name = lb_name.split('-')[0]
    elb = boto3.client('elb', region_name='eu-west-1')
    lb = elb.describe_load_balancers(
        LoadBalancerNames=[
            short_name])
    hc = lb['LoadBalancerDescriptions'][0]['HealthCheck']
    port = lb['LoadBalancerDescriptions'][0]['ListenerDescriptions'][0]['Listener']['LoadBalancerPort']
    hc['Interval'] = 5
    hc['Timeout'] = 4
    hc['HealthyThreshold'] = 2
    elb.configure_health_check(
        LoadBalancerName=short_name,
        HealthCheck=hc
    )
    print "Set ELB healthcheck"
    return port

def is_elb_up(lb_name):
    short_name = lb_name.split('-')[0]
    elb = boto3.client('elb', region_name='eu-west-1')
    instances = elb.describe_instance_health(LoadBalancerName=short_name)
    up = [True for x in instances['InstanceStates'] if x['State'] == 'InService']
    return any(up)

def deploy_branch(template_pod, template_service, branch, domain_zone):
    svc = deploy_service(template_pod, template_service, branch, domain_zone)
    svc_name = svc[1]
    lb_name = svc[0]
    port = set_healthcheck(lb_name)
    fqdn = "{0}-{1}.{2}".format(svc_name, branch, domain_zone)
    change_id = create_cname.create_rr(fqdn, lb_name)
    print "Creating DNS record and waiting for sync"
    result = utils.timeout(120, 2)(create_cname.is_change_complete)(change_id)
    print "Created DNS record"
    print "Waiting for ELB healthcheck to pass"
    result = utils.timeout(240, 2)(is_elb_up)(lb_name)
    print "Service up at: {0}".format(fqdn)
    print "DONE"
    return "http://{0}:{1}".format(fqdn, port)

if __name__ == "__main__":
    template_pod = sys.argv[1]
    template_service = sys.argv[2]
    branch = sys.argv[3]
    domain_zone = sys.argv[4]
    deploy_branch(template_pod, template_service, branch, domain_zone)
