You're a senior devops and datacenter engineer with 20 years of experience. 

I am working on making an ansible setup. I would like to make a prompt for an llm that will take my existing project and add the missing pieces. For now I think that I need to document what I imagine the vision of the project is. I would like you to ask for more details if you wouldn't know how to implement things or areas where there is more information needed. I am curious if for helping to configure some of these projects you will need to have the documentation posted into the context window?

So the basic over view:

configuration: done with ansible
continuous deployment done with: argoCD
container management done with: suse rancher
VM management: suse harvester
DNS: control-d
router: vyos
ipxe: ipxe
storage: truenas
switches: mikrotik

hardware:
uninterrutbable power supply: eaton 5px1500

"nexus"
- lenovo thin client + intel ethernet card

"epyc server"
- 6 6tb sata HDDs to pcie sas/sata card
- 1 4tb HDD to pcie sas card
- 1 sata SSD
- 1 u.3 SSD
- 3 nvme m.2 ssds in a pcie card
- amd GPU
- 256gb ram
- epyc 7532

"fast server"
- 128gb ram
- 5950x amd ryzen
- no extras

"mid server"
- amd 5700G
- 64gb ram

2 hp thin clients

raspberry pi

all connected to a 24 port mikrotik switch and the eaton ups

The plan as it stands is to have this setup:

on the lenovo thin client have libvirt running that will have 2 vm's. one VM will have the router vyos and connect from the modem to the switch that connects the house. The over VM will have control-d the DNS service, ipxe, and DHCP. It will also have an argo cd deployment service so it can deploy harvester to all the nodes correctly
- I really need a better name for this system but as it does so many jobs I am unsure what name to give it

ipxe:
all nodes should be able to automatically request their image from the ipxe server and then be auto started by argocd. So reinstalls are easy. There should be a way to make sure that when the epyc server redeploys that it doesn't erase the data on the u.3 drive or truenas

Secrets:
Secrets will be stored in 2 places. Secrets for basic configuration before harvester stands up in the process will be pulled from the cloud "infisical" service. All containers can pull their secrets from the local instance of infisical that will be running. Using the starbucks method for doing initial key storage. Each server will have a tpm. The tpm will store a key. on startup each server will pull an individual encrypted file from the lenovo thin client named after the server. the server will use the key stored in its tpm to decrypt the file which will have the key for cloud infisical so that it can then pull down the other crucial secrets for bootstrapping. Once harvester is started and infisical is started locally every service can use infisical to get the secrets it needs and has access too

Harvester will be running on:
- 1 thin client
- "mid server"
- "epyc server"

epyc server:
the epic server will host harvester with the following vm's
- truenas VM, it will have the sas pcie card and nvme m.2 pcie card passed through for setting up truenas
- GPU instance. I don't know if I can just do this through containers instead of vm's but need to pass the GPU through so that I can create llm containers (or vm's?)
The epyc server will also have the u.3 SSD as the longhorn storage for containers so it can be used for the llm containers, unsure if that should be passed through to a VM for llm's or if its okay to have it as longhorn storage
gpu - I want the gpu instances managed by rancher, so however is the easiest to manage via rancher is what I want. I don't know if that is a container vm, which I would like if possible since it could be a "llm node". but I don't know if rancher can run containers inside a vm that it manages

vyos:
will host all internetwork traffic, can boost to stronger server if need more power for all vlan traffic. There will be port forwarding to the dmz vlan. There will also need to be a vpn. unsure what the vpn options are what one is good to choose or if vyos already has one

harvester:
there are 3 cluster nodes: mid, epyc, and thin. epyc will be the primary server, as much as possible have services run on the epyc server. (if there is a way to bind certain services to certain nodes that would be awesome, some of the smaller services would be good on the mid node to not eat up memory that might be used for the llm service) most services will connect to the dmz for their service and the secure network for the mangement interface. the fileshares will only be available from the secure network. The fileshares will not be availbe to the other services directly (there is the question of how to have the services connect to the file share to store their data. I assume there will have to be some fancy routing?)


truenas:
truenas configuration will be having 5 6tb drives setup as a zfs raidz2 for 2 drive redundancy. The 6th drive will be a hot spare. The remaining 4 tb hard drive will be for ephemeral storage like movies that need no data loss protection. both volumes will be available to the network so that containers can connect to them for storage. There are the 3 pcie nvme drives, 1 drive for the zslog for the raidz2, then there will be 1 for the read cache for the raidz2. There will be a read cache infront of the 1 4tb drive since it will often be used for streaming. There are no performance requirements other than to be able to saturate a 1gbps network connection. any high peformance stuff should be added later with an additional u.3 drive. True nas will live on the secure vlan
- need a more creative name for the raidz2

there will be a folder in the truenas raidz2 volume that will be backed up to Backblaze on the b2 instances. because of the way that Backblaze charges we don't want to have the entire useable 18tb backed up. Just important files, like all medical documents (there is software for this but where that is storing files should be for the service that hosts medical documents) all configuration files will be stored in gitlab. there are other things like photos that will need to be backed up.
- does truenas need to be partially block storage so that various databases for the different services can use the one raidz2?

fast server
this should be dormant other than for specific instances where high compute is needed so it should be something that can be turned on automatically when requested and shutdown automatically after idle for a certain amount of time (probably 30 mins) this is where I might put the gpu for llm's

external dns:
done by cloudflare, all traffic rerouted to 443, various domain names

There will be a few vlans:
1: nothing
10: DMZ
- demilitarized zone for all traffic that has any access to the outside, any externally facing services. cannot be accessed from other vlans
can access:
- none
20: unsecured wifi
- for devices that I don't really trust, like friends and roommates phones
can access:
- none
30: secured wifi
- for my phones and ipad
can access:
- secure: yes (might want to lock down because phones are skeptical)

40: iot
- for all iot devices
can access: 
- no other network
j
50: secure
- for all devices that I think I can trust, will be my main network. This is what my vpn will connect to
can access:
- secured wifi: yes
- mangement: through jump station, (probably on raspbery pi?)

60: management
- for all servers and their management, I don't want any unauthorized applications to accidentally get access to configure my servers
can access:
- no other network, only accessble via jump station


services in harvester:
- (argocd)[https://github.com/argoproj/argo-cd]
will run the continous deployment process. want all pieces to be deployable by argocd, unsure if that means that each service needs its own repo? or if argo can redeploy on updated services, it will have all services. There should be a second copy of argocd that runs on the 
- traefik
there will need to be a reverse proxy in the dmz and in the secure vlan to add https certs to the webpages.
the reverse proxy that I have seen used a lot. If there as a reverse proxy that you recommend I would love to hear about your options.
as cloudflare will route all traffic to port 443 only opening port 443 from the dmz to the wan. All external services will be connected via this path: cloudflare - vyos firewall - dmz vlan - reverse proxy - service
- (privatebin)[https://github.com/PrivateBin/PrivateBin]
a place I can use as a private pastebin to store things, access to secure vlan
- (Lychee)[https://github.com/LycheeOrg/Lychee]
I would like this available both externally so that I can share pictures as well as internally so I can view them. so on the dmz vlan and the secure, unsure if its just best to access the external link from the secure vlan
- pusher (cloud https://pusher.com/beams/)
for push notifications, is cloud but makes push notifications easier
- (ntfy)[https://github.com/binwiederhier/ntfy]
a self hosted alternative to pusher beam which would be nice but have to see how much phone battery it uses, would be good to try
- (homebox)[https://github.com/sysadminsmedia/homebox/tree/main]
for storing all information about items I have, will be available only on the secure network, needs to be backed to backblaze
- (immich)[https://github.com/immich-app/immich]
other app for photos that is more for managing photos rather than showing them like lychee. Also needs to be accessable to external, so put in dmz
- (authentick)[https://github.com/goauthentik/authentik]
does the single sign on for all the services. Needs to be avaiable both on the dmz and the secure network
- (restic)[https://github.com/restic/restic]
does the backup to backblaze from truenas
- (ageis)[https://github.com/beemdevelopment/aegis]
this is a totp system that manages totp codes from devices and syncs them. its database will also need to be backed up to backblaze
- (zimit)[https://github.com/openzim/zimit]
stores webpages for future use, will need a version for "interesting" webpages and for ones I want to be backed up to backblaze
- (omnitools)[https://github.com/iib0011/omni-tools]
this has all sorts of useful tools like timezone conversion, calculator etc. Want this accessable on secure and dmz
- (victoriaMetrics)[https://github.com/VictoriaMetrics/VictoriaMetrics]
This is a log agregator needs to combine all data from every service, so needs to be on secure, management at the minimum
- (grocy)[https://github.com/grocy/grocy]
my food management program, has recipies and manages what food items I have and shows what recipies I can make with ingredients I have on hand

need ideas:
- git server to host all items so that I can launch argocd when there is a new commit to main, unsure if argocd can pull from gitlab directly


Unsure between:
stats monitoring:
- (netdata)[https://github.com/netdata/netdata]
- (zabbix)[https://github.com/zabbix/zabbix]