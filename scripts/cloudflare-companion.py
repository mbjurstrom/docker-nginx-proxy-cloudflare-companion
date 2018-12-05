import os
import docker
import CloudFlare
from datetime import datetime

#TODO make it a class
#TODO make it update if it already exists
# TODO make an option to auto delete domain if it stops
# TODO add suppor for domain specific options (mainly proxies)

#extract all pair of domain and domain_zone ids from enviromental variables
def get_domains():
    domains = []
    for env_key in os.environ:
        if env_key.startswith('DOMAIN') and not env_key.endswith('ZONE_ID') and not env_key.endswith('PROXIED') : #ugly hack with endswith
            domain = {}
            domain['domain'] = os.getenv(env_key)
            try:
                domain['zone_id'] = os.environ['{}_ZONE_ID'.format(env_key.strip())]
            except KeyError as e:
                exit('{}_ZONE_ID is not defined'.format(env_key.strip()))
            try:
                if os.environ['{}_PROXIED'.format(env_key.strip())].upper() == 'TRUE':
                    proxied = True
                else:
                    proxied = False
            except KeyError:
                print('{}_PROXIED is not defined defaulting to False'.format(env_key.strip()))
                proxied = False
                
            domain['proxied'] =  proxied 
            domains.append(domain)
    return domains
            
        # print('{} = {}'.format(env_key, os.getenv(env_key)))
    
def point_domain(name,domains, **kwargs):
    try:
        for domain in domains:
            if name.find(domain['domain']) != -1:
                proxied = kwargs.get('proxied', domain['proxied']) 
                r = cf.zones.dns_records.post(domain['zone_id'],data={u'type': u'CNAME', u'name': name, u'content': domain['domain'], u'ttl': 120, u'proxied': proxied} )
            #TODO add better error checking here 
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        print '/zones.dns_records.post %s - %d %s' % (name, e, e)


def check_container(c, domains):
    virtual_domains = []
    proxied = None
    for prop in c.attrs.get(u'Config').get(u'Env'):
        virtual_hosts = {}
        if u'VIRTUAL_HOST' in prop or u'DNS_NAME' in prop:#todo add other parameters here like container specific proxy setting and ttl setting
            value = prop.split("=")[1].strip()
            if ',' in value:
                for v in value.split(","):
                    virtual_domains.append(v)
            else:
                virtual_domains.append(value)
        elif u'CF_PROXIED' in prop:
            value = prop.split("=")[1].strip()
            if value.upper() == 'TRUE':
                proxied = True
            elif value.upper() == 'False':
                proxied = False
            else:
                print('Invalid CF_PROXIED VALUE for container {}'.format('TODO find way to get name'))
    for virtual_domain in virtual_domains:
        point_domain(virtual_domain, domains, {'proxied': proxied})

def init(domains):
    for c in client.containers.list(all=True):
        check_container(c,domains)

        
#loop through enviromental variablesfor
domains = get_domains()
if not domains:
    exit('No DOMAIN defined. You need to define at least one DOMAINX and DOMAINX_ZONE_ID')

try:
    email = os.environ['CF_EMAIL']
except KeyError as e:
    exit('CF_EMAIL not defined')

try:
    token = os.environ['CF_TOKEN']
except KeyError as e:
    exit('CF_TOKEN not defined')

cf = CloudFlare.CloudFlare(email=email, token=token)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

init(domains)

t = datetime.now().time().strftime("%s")

for event in client.events(since=t, filters={'status': u'start'}, decode=True):
    if event.get(u'status') == u'start':
        try:
            print u'started %s' % event.get(u'id')
            check_container(client.containers.get(event.get(u'id')),domains)
        except docker.errors.NotFound as e:
            print 'Ignoring %s' % event.get(u'from')
