import requests, base64, re
import getpass
import xml.etree.cElementTree as ET
import inquirer

# Variables

org = raw_input("organization: [System]") or "System"
user = raw_input("username: ")
passw = getpass.getpass()
creds = ''.join(["%s@%s:%s" % (user, org, passw)])
b64Val = base64.b64encode(creds)


# Run URL
url = "https://chc.cloud.concepts.co.nz/api/sessions"
headers = {'Accept': 'application/*+xml;version=20.0', "Authorization": "Basic %s" % b64Val}

# Make request and pass creds
myResponse = requests.post(url, headers=headers)
if(myResponse.ok):
    print ("Autheticated successfully to Org %s as %s" % (org, user))
else:
  # If response code is not ok (200), print the resulting http error code with description
    myResponse.raise_for_status()


# Grab stuff from response

auth_token = myResponse.headers["x-vcloud-authorization"]
print ("Your Auth Token is: %s" % (auth_token))
tree = ET.fromstring(myResponse.content)
#print(myResponse.content)

# Get a list of Organizations registered on this vCloud Server instance

orgurl = ('https://chc.cloud.concepts.co.nz/api/org')
orgheaders = {'Accept': 'application/*+xml;version=5.6', 'x-vcloud-authorization': '%s' % auth_token}
orgResponse = requests.get(orgurl, headers=orgheaders)
#print(orgResponse.content)

## Parse XML and all the crappy namespaces
tree = ET.fromstring(orgResponse.content)
### Create an empty array
org_name_array = []
 
for child in tree:
	org_name = (child.attrib['name'])
	org_url = (child.attrib['href'])
	org_name_array.append(([org_name, org_url]))
	#print(org_name_array[0:1])
	#print(org_name_array[1:2])

#### Pick an Org to work with

questions = [
  inquirer.List('Orgs',
                message="What Org do you want to work with?",
                choices= org_name_array,
            ),
]
org_answer = inquirer.prompt(questions)
#print(org_answer)

##### Bit of massaging
regex = """\[(.*?)]"""
orglist = """%s""" % org_answer
orgmatch = re.compile(regex).search(orglist).group(1)
org_array = orgmatch.split(',')
selorg_name = (org_array[0].strip("'"))
selorg_url = ((org_array[1].strip()).strip("'"))
#print(selorg_name)
#print(selorg_url)

# Get a list of vDC in this Org

vdcurl = ('%s' % selorg_url)
vdcheaders = {'Accept': 'application/*+xml;version=5.6', 'x-vcloud-authorization': '%s' % auth_token}
vdcResponse = requests.get(vdcurl, headers=vdcheaders)
#print(vdcResponse.content)

## Parse XML and all the crappy namespaces
vdctree = ET.fromstring(vdcResponse.content)
vdcarray = []

for child in vdctree:
	if 'href' in child.attrib and 'name' in child.attrib:
		if '/vdc/' in (child.attrib['href']):
			vdc_url = (child.attrib['href'])
			vdc_name = (child.attrib['name'])
			vdcarray.append(([vdc_name, vdc_url]))
#print(vdcarray)

#### Pick an vDC to work with within this Org

questions = [
  inquirer.List('Virtual Data Center',
                message="What vDC do you want to work with?",
                choices= vdcarray,
            ),
]
vdc_answer = inquirer.prompt(questions)
#print(vdc_answer)

##### Bit of massaging

regex = """\[(.*?)]"""
vdclist = """%s""" % vdc_answer
vdcmatch = re.compile(regex).search(vdclist).group(1)
vdc_array = vdcmatch.split(',')
selvdc_name = (vdc_array[0].strip("'"))
selvdc_url = ((vdc_array[1].strip()).strip("'"))
#print(selvdc_name)
#print(selvdc_url)

# Get a list of vCenter Servers

vcurl = ('https://chc.cloud.concepts.co.nz/api/admin/extension/vimServerReferences')
vcheaders = {'Accept': 'application/*+xml;version=5.6', 'x-vcloud-authorization': '%s' % auth_token}
vcResponse = requests.get(vcurl, headers=vcheaders)
#print(vcResponse.content)

## Parse XML and all the crappy namespaces
vctree = ET.fromstring(vcResponse.content)
### Create an empty array
vc_name_array = []

for i, child in enumerate(vctree):
	if 'href' in child.attrib and 'name' in child.attrib:
		vc_url =  (child.attrib['href'])
		vc_name = (child.attrib['name'])
		vc_name_array.append(([vc_name, vc_url]))
		#print(vc_name_array[0:1])
		#print(vc_name_array[1:2])

#### Pick a vCenter to work with

questions = [
  inquirer.List('vCenter',
                message="What vCenter do you want to work with?",
                choices= vc_name_array,
            ),
]
vc_answer = inquirer.prompt(questions)
#print(vc_answer)

#####Bit of massaging
vcregex = '''\[(.*?)]'''
vclist = '''%s''' % vc_answer
vcmatch = re.compile(vcregex).search(vclist).group(1)
vc_array = vcmatch.split(',')
selvc_name = (vc_array[0].strip("'"))
selvc_url = ((vc_array[1].strip()).strip("'"))
#print(selvc_name)
#print(selvc_url)

# Ask if VMs to be imported are powered on or not
vmpwr_question = [
  inquirer.List('Power state',
                message='Is the VM(s) you want to import powered on?',
                choices=['Yes', 'No'],
            ),
]
vmpwr_answer = inquirer.prompt(vmpwr_question)

# Get a list of VMs that can be seen by vCloud on the vCenter Server

if vmpwr_answer == {'Power state': 'No'}:
	vmurl = ('%s/vmsList' % selvc_url)
	vmheaders = {'Accept': 'application/*+xml;version=20.0', 'x-vcloud-authorization': '%s' % auth_token}
	vmResponse = requests.get(vmurl, headers=vmheaders)
	#print(vmResponse.content)

	## Parse XML and all the crappy namespaces
	vmtree = ET.fromstring(vmResponse.content)
	### Create an empty array
	vm_name_array = []

	vmroot = vmtree

	namespaces = {'vmext': 'http://www.vmware.com/vcloud/extension/v1.5'} # add more as needed
	VMS = vmroot.findall('vmext:VmObjectRef', namespaces)
	VMref = vmroot.findall('vmext:MoRef', namespaces)
	for vm in VMS:
		MoRef = vm.find('{http://www.vmware.com/vcloud/extension/v1.5}MoRef')
		vm_name =  (vm.attrib['name'])
		vm_ref = MoRef.text
		vm_name_array.append(([vm_name, vm_ref]))
		#print(vm_name_array)

	#### Pick the VMs to migrate

	vm_questions = [
	  inquirer.Checkbox('VMs List',
						message='Which VMs would you like to migrate into vCloud?',
						choices= vm_name_array,
						),
	]
	vm_answer = inquirer.prompt(vm_questions)
	##### Bit of massaging
	vmsel_array = []
	vmregex = '''\['(.*?)]'''
	vmlist = '''%s''' % vm_answer
	vmmatch = re.compile(vmregex).findall(vmlist)
	#print(vmmatch)
	for vm in vmmatch:
		array = vm.replace("'", "")
		#print((array).split(',')[0]).split()
		nameid = ((array).split(',')[0]).split()
		refid = ((array).split(',')[1]).split()
		vmsel_array.append(([refid, nameid]))
	#print(vmsel_array)
	vms2move = ( ", ".join( repr(e) for e in vmsel_array )).replace("'", "").replace('[', '').replace(']', '').split(',')
	#print(vms2move)
	arraygone = ( ", ".join( repr(e[0]) for e in vmsel_array )).replace("'", "").replace('[', '').replace(']', '').split(',')
	#print(arraygone)
	#for sel in arraygone:
		#print((sel).strip())
		
	###### Get vCloud to import this machine
	
	tasks_array = []
	impurl = ('%s/importVmAsVApp' % selvc_url)
	impheaders = {'Accept': 'application/*+xml;version=20.0','Content-type': 'application/vnd.vmware.admin.importVmAsVAppParams+xml', 'x-vcloud-authorization': '%s' % auth_token}
	
	for idx, val in enumerate(vmsel_array):
		vmname = str(val[1]).replace("'", "").replace('[', '').replace(']', '')
		vmid = str(val[0]).replace("'", "").replace('[', '').replace(']', '')
		xml = ('''<?xml version="1.0" encoding="UTF-8"?>
<ImportVmAsVAppParams xmlns="http://www.vmware.com/vcloud/extension/v1.5" name="%s" sourceMove="false">
	<VmMoRef>%s</VmMoRef>
   	<Vdc href="%s" />
</ImportVmAsVAppParams>''' % (vmname, vmid, selvdc_url))
		impResponse = requests.post(impurl, data=xml, headers=impheaders)
		print('Importing machine %s with refid %s into vCloud...' % (vmname, vmid))
		#print(impResponse.content)
		tsktree = ET.fromstring(impResponse.content)
		taskies = tsktree.getchildren()
		for task in taskies:
			tsk_children = task.getchildren()
			for tsk_child in tsk_children:
				if 'Task' in tsk_child.tag:
					taskurl = (tsk_child.attrib['href'])
					tasks_array.append(taskurl)
	print(tasks_array)



if vmpwr_answer == {'Power state': 'Yes'}:
	print('''Do something else cause vCloud API won't give you the list of running VMs''')
