from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSlider, getConfigListEntry

config.plugins.OSDPositionSetup = ConfigSubsection()
config.plugins.OSDPositionSetup.dst_left = ConfigInteger(default = 0)
config.plugins.OSDPositionSetup.dst_width = ConfigInteger(default = 720)
config.plugins.OSDPositionSetup.dst_top = ConfigInteger(default = 0)
config.plugins.OSDPositionSetup.dst_height = ConfigInteger(default = 576)

def setPosition(dst_left, dst_width, dst_top, dst_height):
	if dst_left + dst_width > 720:
		dst_width = 720 - dst_left
	if dst_top + dst_height > 576:
		dst_height = 576 - dst_top
	try:
		open("/proc/stb/fb/dst_left", "w").write('%X' % dst_left)
		open("/proc/stb/fb/dst_width", "w").write('%X' % dst_width)
		open("/proc/stb/fb/dst_top", "w").write('%X' % dst_top)
		open("/proc/stb/fb/dst_height", "w").write('%X' % dst_height)
	except:
		return

def setConfiguredPosition():
	setPosition(int(config.plugins.OSDPositionSetup.dst_left.value), int(config.plugins.OSDPositionSetup.dst_width.value), int(config.plugins.OSDPositionSetup.dst_top.value), int(config.plugins.OSDPositionSetup.dst_height.value))

def main(session, **kwargs):
	from overscanwizard import OverscanWizard
	session.open(OverscanWizard, timeOut=False)

def startup(reason, **kwargs):
	setConfiguredPosition()

def OSDPosSetup(menuid, **kwargs):
	if menuid == "ui_menu":
		return [(_("Position and size"), main, "osd_position_setup", 80)]
	else:
		return []

def Plugins(**kwargs):
	from os import path
	if path.exists("/proc/stb/fb/dst_left"):
		from Plugins.Plugin import PluginDescriptor
		return [PluginDescriptor(name = _("OSD position setup"), description = _("Compensate for overscan"), where = PluginDescriptor.WHERE_MENU, needsRestart = False, fnc=OSDPosSetup),
					PluginDescriptor(name = "Overscan Wizard", description = "", where = PluginDescriptor.WHERE_SESSIONSTART, fnc = startup)]
	return []
