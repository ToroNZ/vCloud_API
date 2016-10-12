import requests, base64
import getpass
try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET
from picker import *
import curses
import curses.wrapper

# Picker Class

class Picker:
    """Allows you to select from a list with curses"""
    stdscr = None
    win = None
    title = ""
    arrow = ""
    footer = ""
    more = ""
    c_selected = ""
    c_empty = ""
    
    cursor = 0
    offset = 0
    selected = 0
    selcount = 0
    aborted = False
    
    window_height = 15
    window_width = 60
    all_options = []
    length = 0
    
    def curses_start(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.win = curses.newwin(
            5 + self.window_height,
            self.window_width,
            2,
            4
        )
    
    def curses_stop(self):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def getSelected(self):
        if self.aborted == True:
            return( False )

        ret_s = filter(lambda x: x["selected"], self.all_options)
        ret = map(lambda x: x["label"], ret_s)
        return( ret )
        
    def redraw(self):
        self.win.clear()
        self.win.border(
            self.border[0], self.border[1],
            self.border[2], self.border[3],
            self.border[4], self.border[5],
            self.border[6], self.border[7]
        )
        self.win.addstr(
            self.window_height + 4, 5, " " + self.footer + " "
        )
        
        position = 0
        range = self.all_options[self.offset:self.offset+self.window_height+1]
        for option in range:
            if option["selected"] == True:
                line_label = self.c_selected + " "
            else:
                line_label = self.c_empty + " "
            
            self.win.addstr(position + 2, 5, line_label + option["label"])
            position = position + 1
            
        # hint for more content above
        if self.offset > 0:
            self.win.addstr(1, 5, self.more)
        
        # hint for more content below
        if self.offset + self.window_height <= self.length - 2:
            self.win.addstr(self.window_height + 3, 5, self.more)
        
        self.win.addstr(0, 5, " " + self.title + " ")
        self.win.addstr(
            0, self.window_width - 8,
            " " + str(self.selcount) + "/" + str(self.length) + " "
        )
        self.win.addstr(self.cursor + 2,1, self.arrow)
        self.win.refresh()

    def check_cursor_up(self):
        if self.cursor < 0:
            self.cursor = 0
            if self.offset > 0:
                self.offset = self.offset - 1
    
    def check_cursor_down(self):
        if self.cursor >= self.length:
            self.cursor = self.cursor - 1
    
        if self.cursor > self.window_height:
            self.cursor = self.window_height
            self.offset = self.offset + 1
            
            if self.offset + self.cursor >= self.length:
                self.offset = self.offset - 1
    
    def curses_loop(self, stdscr):
        while 1:
            self.redraw()
            c = stdscr.getch()
            
            if c == ord('q') or c == ord('Q'):
                self.aborted = True
                break
            elif c == curses.KEY_UP:
                self.cursor = self.cursor - 1
            elif c == curses.KEY_DOWN:
                self.cursor = self.cursor + 1
            #elif c == curses.KEY_PPAGE:
            #elif c == curses.KEY_NPAGE:
            elif c == ord(' '):
                self.all_options[self.selected]["selected"] = \
                    not self.all_options[self.selected]["selected"]
            elif c == 10:
                break
                    
            # deal with interaction limits
            self.check_cursor_up()
            self.check_cursor_down()

            # compute selected position only after dealing with limits
            self.selected = self.cursor + self.offset
            
            temp = self.getSelected()
            self.selcount = len(temp)
    
    def __init__(
        self, 
        options, 
        title='Select', 
        arrow="-->",
        footer="Space = toggle, Enter = accept, q = cancel",
        more="...",
        border="||--++++",
        c_selected="[X]",
        c_empty="[ ]"
    ):
        self.title = title
        self.arrow = arrow
        self.footer = footer
        self.more = more
        self.border = border
        self.c_selected = c_selected
        self.c_empty = c_empty
        
        self.all_options = []
        
        for option in options:
            self.all_options.append({
                "label": option,
                "selected": False
            })
            self.length = len(self.all_options)
        
        self.curses_start()
        curses.wrapper( self.curses_loop )
        self.curses_stop()

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
print(myResponse.content)


# Get a list of Organizations registered on this vCloud Server instance

orgurl = ('https://chc.cloud.concepts.co.nz/api/org')
orgheaders = {'Accept': 'application/*+xml;version=5.6', 'x-vcloud-authorization': '%s' % auth_token}
orgResponse = requests.get(orgurl, headers=orgheaders)
print(orgResponse.content)

# Parse XML and all the crappy namespaces
tree = ET.fromstring(orgResponse.content)
root = tree.getroot()
iter = root.getiterator()

for element in iter:
	outputorgs = []
	for name, value in element.items():
		if 'application' not in value:
			if True:
				custname = value
				#print custname
				outputorgs.append(custname)

	#print output[0]
	print outputorgs


# Pick an Org to work with

opts = Picker(
    title = 'Select an Organization to work with',
    options = outputorgs
).getSelected()

if opts == False:
    print "Nothing was selected!"
else:
    print opts

# Get a list of vCenter Servers

vcurl = ('https://chc.cloud.concepts.co.nz/api/admin/extension/vimServerReferences')
vcheaders = {'Accept': 'application/*+xml;version=5.6', 'x-vcloud-authorization': '%s' % auth_token}
vcResponse = requests.get(vcurl, headers=vcheaders)
print(vcResponse.content)

# Get a list of VMs that can be seen by vCloud on the vCenter Server

#vmsurl = ("https://chc.cloud.concepts.co.nz/api/admin/extension/%s/%s/vmsList" % (vcenter, auth_token))
#vmsResponse = requests.get(vmsurl)
#print(vmsResponse.headers)
