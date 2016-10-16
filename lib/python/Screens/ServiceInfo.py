from Components.HTMLComponent import HTMLComponent
from Components.GUIComponent import GUIComponent
from Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from ServiceReference import ServiceReference
from enigma import eListboxPythonMultiContent, eListbox, gFont, iServiceInformation, eServiceCenter
from Tools.Transponder import ConvertToHumanReadable, getChannelNumber
import skin
from Components.ScrollLabel import ScrollLabel

RT_HALIGN_LEFT = 0

TYPE_TEXT = 0
TYPE_VALUE_HEX = 1
TYPE_VALUE_DEC = 2
TYPE_VALUE_HEX_DEC = 3
TYPE_SLIDER = 4
TYPE_VALUE_ORBIT_DEC = 5
TYPE_VALUE_FREQ = 6
TYPE_VALUE_FREQ_FLOAT = 7
TYPE_VALUE_BITRATE = 8

def to_unsigned(x):
	return x & 0xFFFFFFFF

def ServiceInfoListEntry(a, b, valueType=TYPE_TEXT, param=4):
	print "b:", b
	if not isinstance(b, str):
		if valueType == TYPE_VALUE_HEX:
			b = ("0x%0" + str(param) + "x") % to_unsigned(b)
		elif valueType == TYPE_VALUE_FREQ:
			b = "%s MHz" % (b / 1000)
		elif valueType == TYPE_VALUE_FREQ_FLOAT:
			b = "%.3f MHz" % (b / 1000.0)
		elif valueType == TYPE_VALUE_BITRATE:
			b = "%s KSymbols/s" % (b / 1000)
		elif valueType == TYPE_VALUE_HEX_DEC:
			b = ("0x%0" + str(param) + "x (%dd)") % (to_unsigned(b), b)
		elif valueType == TYPE_VALUE_ORBIT_DEC:
			direction = 'E'
			if b > 1800:
				b = 3600 - b
				direction = 'W'
			b = ("%d.%d%s") % (b // 10, b % 10, direction)
		else:
			b = str(b)
	x, y, w, h = skin.parameters.get("ServiceInfo",(0, 0, 300, 30))
	xa, ya, wa, ha = skin.parameters.get("ServiceInfoLeft",(0, 0, 300, 25))
	xb, yb, wb, hb = skin.parameters.get("ServiceInfoRight",(300, 0, 600, 25))
	return [
		#PyObject *type, *px, *py, *pwidth, *pheight, *pfnt, *pstring, *pflags;
		(eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_HALIGN_LEFT, ""),
		(eListboxPythonMultiContent.TYPE_TEXT, xa, ya, wa, ha, 0, RT_HALIGN_LEFT, a),
		(eListboxPythonMultiContent.TYPE_TEXT, xb, yb, wb, hb, 0, RT_HALIGN_LEFT, b)
	]

class ServiceInfoList(HTMLComponent, GUIComponent):
	def __init__(self, source):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.list = source
		self.l.setList(self.list)
		font = skin.fonts.get("ServiceInfo", ("Regular", 23, 25))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		self.instance.setContent(self.l)

TYPE_SERVICE_INFO = 1
TYPE_TRANSPONDER_INFO = 2

class ServiceInfo(Screen):
	def __init__(self, session, serviceref=None):
		Screen.__init__(self, session)

		self.setTitle(_("Service info"))
		self["infotext"] = ScrollLabel()
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.close,
			"cancel": self.close,
			"red": self.information,
			"green": self.pids,
			"yellow": self.transponder,
			"blue": self.tuner
		}, -1)

		if serviceref:
			Screen.setTitle(self, _("Transponder Information"))
			self.type = TYPE_TRANSPONDER_INFO
			self.skinName="ServiceInfoSimple"
			info = eServiceCenter.getInstance().info(serviceref)
			self.transponder_info = info.getInfoObject(serviceref, iServiceInformation.sTransponderData)
			# info is a iStaticServiceInformation, not a iServiceInformation
			self.info = None
			self.feinfo = None
		else:
			Screen.setTitle(self, _("Service Information"))
			self.type = TYPE_SERVICE_INFO
			self["key_red"] = self["red"] = Label(_("Service"))
			self["key_green"] = self["green"] = Label(_("PIDs"))
			self["key_yellow"] = self["yellow"] = Label(_("Multiplex"))
			self["key_blue"] = self["blue"] = Label(_("Tuner status"))
			service = session.nav.getCurrentService()
			if service is not None:
				self.info = service.info()
				self.feinfo = service.frontendInfo()
			else:
				self.info = None
				self.feinfo = None

		tlist = [ ]

		self["infolist"] = ServiceInfoList(tlist)
		self.onShown.append(self.information)

	def information(self):
		if self.type == TYPE_SERVICE_INFO:
			if self.session.nav.getCurrentlyPlayingServiceOrGroup():
				name = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference()).getServiceName()
				refstr = self.session.nav.getCurrentlyPlayingServiceReference().toString()
			else:
				name = _("N/A")
				refstr = _("N/A")
			aspect = "-"
			videocodec = "-"
			resolution = "-"
			if self.info:
				videocodec =  ("MPEG2", "AVC", "MPEG1", "MPEG4-VC", "VC1", "VC1-SM", "HEVC", "-")[self.info.getInfo(iServiceInformation.sVideoType)]
				width = self.info.getInfo(iServiceInformation.sVideoWidth)
				height = self.info.getInfo(iServiceInformation.sVideoHeight)
				if width > 0 and height > 0:
					resolution = "%dx%d" % (width,height)
					resolution += ("i", "p", "")[self.info.getInfo(iServiceInformation.sProgressive)]
					resolution += str((self.info.getInfo(iServiceInformation.sFrameRate) + 500) / 1000)
					aspect = self.getServiceInfoValue(iServiceInformation.sAspect)
					if aspect in ( 1, 2, 5, 6, 9, 0xA, 0xD, 0xE ):
						aspect = "4:3"
					else:
						aspect = "16:9"

			Labels = ( (_("Name"), name, TYPE_TEXT),
					(_("Provider"), self.getServiceInfoValue(iServiceInformation.sProvider), TYPE_TEXT),
					(_("Videoformat"), aspect, TYPE_TEXT),
					(_("Videosize"), resolution, TYPE_TEXT),
					(_("Videocodec"), videocodec, TYPE_TEXT),
					(_("Namespace"), self.getServiceInfoValue(iServiceInformation.sNamespace), TYPE_VALUE_HEX, 8),
					(_("Service reference"), refstr, TYPE_TEXT))

			self.fillList(Labels)
		else:
			if self.transponder_info:
				tp_info = ConvertToHumanReadable(self.transponder_info)
				conv = { "tuner_type" 		: _("Transponder type"),
						 "system"			: _("System"),
						 "modulation"		: _("Modulation"),
						 "orbital_position" : _("Orbital position"),
						 "frequency"		: _("Frequency"),
						 "symbol_rate"		: _("Symbol rate"),
						 "bandwidth"		: _("Bandwidth"),
						 "polarization"		: _("Polarization"),
						 "inversion"		: _("Inversion"),
						 "pilot"			: _("Pilot"),
						 "rolloff"			: _("Roll-off"),
						 "fec_inner"		: _("FEC"),
						 "code_rate_lp"		: _("Coderate LP"),
						 "code_rate_hp"		: _("Coderate HP"),
						 "constellation"	: _("Constellation"),
						 "transmission_mode": _("Transmission mode"),
						 "guard_interval" 	: _("Guard interval"),
						 "hierarchy_information": _("Hierarchy information") }
				Labels = [(conv[i], tp_info[i], i == "orbital_position" and TYPE_VALUE_ORBIT_DEC or TYPE_VALUE_DEC) for i in tp_info.keys() if i in conv]
				self.fillList(Labels)

	def pids(self):
		if self.type == TYPE_SERVICE_INFO:
			Labels = ( (_("Video PID"), self.getServiceInfoValue(iServiceInformation.sVideoPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("Audio PID"), self.getServiceInfoValue(iServiceInformation.sAudioPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("PCR PID"), self.getServiceInfoValue(iServiceInformation.sPCRPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("PMT PID"), self.getServiceInfoValue(iServiceInformation.sPMTPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("TXT PID"), self.getServiceInfoValue(iServiceInformation.sTXTPID), TYPE_VALUE_HEX_DEC, 4),
					   (_("TSID"), self.getServiceInfoValue(iServiceInformation.sTSID), TYPE_VALUE_HEX_DEC, 4),
					   (_("ONID"), self.getServiceInfoValue(iServiceInformation.sONID), TYPE_VALUE_HEX_DEC, 4),
					   (_("SID"), self.getServiceInfoValue(iServiceInformation.sSID), TYPE_VALUE_HEX_DEC, 4))
			self.fillList(Labels)

	def showFrontendData(self, real):
		if self.type == TYPE_SERVICE_INFO:
			frontendData = self.feinfo and self.feinfo.getAll(real)
			Labels = self.getFEData(frontendData)
			self.fillList(Labels)

	def transponder(self):
		if self.type == TYPE_SERVICE_INFO:
			self.showFrontendData(True)

	def tuner(self):
		if self.type == TYPE_SERVICE_INFO:
			self.showFrontendData(False)

	def getFEData(self, frontendDataOrg):
		if frontendDataOrg and len(frontendDataOrg):
			frontendData = ConvertToHumanReadable(frontendDataOrg)
			if frontendDataOrg["tuner_type"] == "DVB-S":
				if frontendData["frequency"] > 11699999 :
					band = "High"
				else:
					band = "Low"
				return (( _("NIM"), chr(ord('A') + frontendData["tuner_number"]), TYPE_TEXT),
						(_("Type"), frontendData["tuner_type"], TYPE_TEXT),
						(_("System"), frontendData["system"], TYPE_TEXT),
						(_("Modulation"), frontendData["modulation"], TYPE_TEXT),
						(_("Orbital position"), frontendData["orbital_position"], TYPE_VALUE_DEC),
						(_("Frequency"), frontendData["frequency"] / 1000, TYPE_VALUE_FREQ),
						(_("Symbol rate"), frontendData["symbol_rate"] / 1000, TYPE_VALUE_BITRATE),
						(_("Polarization"), frontendData["polarization"], TYPE_TEXT),
						(_("Band"), band, TYPE_TEXT),
						(_("Inversion"), frontendData["inversion"], TYPE_TEXT),
						(_("FEC"), frontendData["fec_inner"], TYPE_TEXT),
						(_("Pilot"), frontendData.get("pilot", None), TYPE_TEXT),
						(_("Roll-off"), frontendData.get("rolloff", None), TYPE_TEXT))
			elif frontendDataOrg["tuner_type"] == "DVB-C":
				return ((_("NIM"), chr(ord('A') + frontendData["tuner_number"]), TYPE_TEXT),
						(_("Type"), frontendData["tuner_type"], TYPE_TEXT),
						(_("Modulation"), frontendData["modulation"], TYPE_TEXT),
						(_("Frequency"), frontendData["frequency"] / 1000, TYPE_VALUE_FREQ_FLOAT),
						(_("Symbol rate"), frontendData["symbol_rate"] / 1000, TYPE_VALUE_BITRATE),
						(_("Inversion"), frontendData["inversion"], TYPE_TEXT),
						(_("FEC"), frontendData["fec_inner"], TYPE_TEXT))
			elif frontendDataOrg["tuner_type"] == "DVB-T":
				return ((_("NIM"), chr(ord('A') + frontendData["tuner_number"]), TYPE_TEXT),
						(_("Type"), frontendData["tuner_type"], TYPE_TEXT),
						(_("Frequency"), frontendData["frequency"] / 1000 / 1000, TYPE_VALUE_FREQ_FLOAT),
						(_("Channel"), getChannelNumber(frontendData["frequency"], frontendData["tuner_number"]), TYPE_VALUE_DEC),
						(_("Inversion"), frontendData["inversion"], TYPE_TEXT),
						(_("Bandwidth"), frontendData["bandwidth"], TYPE_VALUE_DEC),
						(_("Code rate LP"), frontendData["code_rate_lp"], TYPE_TEXT),
						(_("Code rate HP"), frontendData["code_rate_hp"], TYPE_TEXT),
						(_("Constellation"), frontendData["constellation"], TYPE_TEXT),
						(_("Transmission mode"), frontendData["transmission_mode"], TYPE_TEXT),
						(_("Guard interval"), frontendData["guard_interval"], TYPE_TEXT),
						(_("Hierarchy info"), frontendData["hierarchy_information"], TYPE_TEXT))
			elif frontendDataOrg["tuner_type"] == "ATSC":
				return ((_("NIM"), chr(ord('A') + frontendData["tuner_number"]), TYPE_TEXT),
						(_("Type"), frontendData["tuner_type"], TYPE_TEXT),
						(_("System"), frontendData["system"], TYPE_TEXT),
						(_("Modulation"), frontendData["modulation"], TYPE_TEXT),
						(_("Frequency"), frontendData["frequency"] / 1000, TYPE_VALUE_FREQ_FLOAT),
						(_("Inversion"), frontendData["inversion"], TYPE_TEXT))
		return [ ]

	def fillList(self, Labels):
		tlist = [ ]
		serviceinfotxt = ""
		streaminfotxt = ""
		for item in Labels:
			if item[1] is None:
				continue;
			value = item[1]
			if item[0] == _("Frequency"):
				value = str(value) + ' MHz'
			sref = value

			if item[0] == _("Service reference"):
				if self.getConvertServiceref(sref)[1] is not False:
					value = str(self.getConvertServiceref(sref)[0])
					streaminfotxt = _("Location:") + self.getConvertServiceref(sref)[1][:45] + "\n"
			if len(item) < 4:
				tlist.append(ServiceInfoListEntry(item[0]+":", value, item[2]))
				if item[2] ==1 or item[2] ==3:
					hexhex = self.converthex(item[2],value)
					serviceinfotxt += str(item[0]) + ":" + hexhex + "\n" 
				else:
					serviceinfotxt += str(item[0]) + ":" + str(value)[:50] + "\n"
			else:
				tlist.append(ServiceInfoListEntry(item[0]+":", value, item[2], item[3]))
				if item[2] ==1 or item[2] ==3:
					hexhex = self.converthex(item[2],value)
					serviceinfotxt += str(item[0]) + ":" + hexhex + "\n" 
				else:
					serviceinfotxt += str(item[0]) + ":" + str(value)[:50] + "\n"
			if streaminfotxt != "":
				serviceinfotxt += streaminfotxt + "\n"
				self["key_yellow"].setText("")
				self["key_blue"].setText("")
				self["key_red"].setText(_("Stream"))
				self["key_green"].setText("")
		self["infotext"].setText(serviceinfotxt)
		self["infolist"].l.setList(tlist)

	def getServiceInfoValue(self, what):
		if self.info is None:
			return ""
		v = self.info.getInfo(what)
		if v == -2:
			v = self.info.getInfoString(what)
		elif v == -1:
			v = _("N/A")
		return v

	def converthex(self, item,value):
		if type(value) != int:
			return '-'
		if value == 0 or value == 'N/V':
			return "-"
		if item == 1: #TYPE_VALUE_HEX = 1 #Namespace
			return str("0x%0" + str(4) + "x") % to_unsigned(value)
		elif item == 2: #
			return "item=2"
		elif item == 3: #TYPE_VALUE_HEX_DEC	#SID PIDS
			return (("(%d) ") % value)  + '  ' + ((( "%04" + "x") % (value)).upper())
			#return str("0x%0" + str(4) + "x (%dd)") % (to_unsigned(value), value)
		else:
			return _("not avaible")

	def getConvertServiceref(self, sref):
		try:
			stream="";ref=""
			if '%3a//' in str(sref) and sref[:4] == '4097':
				sref = sref.upper().split('%3A//')
				url = str(sref[1])[:50].split("/")[0].replace('%3A',":").lower()
				if "@" in url:
					url = '<user:pass>'+ url.split("@")[1]
				stream = sref[0].split(":")[len(sref[0].split(":"))-1].lower() + "://" + url
				ref = sref[0].replace(':'+sref[0].split(":")[len(sref[0].split(":"))-1],'')
				return ref, stream
			elif ':0:0:0:0:0:0:0:0:0:' in str(sref):
				ref  = sref.split(":/")[0]
				stream = sref.split(":/")[1]
				x = stream.split('/')
				rm = x[len(x) -1]
				stream = "/" + stream.replace(rm,'')
				return ref, stream
			elif '%3a//' in str(sref):
				sref = sref.upper().split('%3A//')
				url = str(sref[1])[:50].split("/")[0].replace('%3A',":").lower()
				if "@" in url:
					url = '<user:pass>'+ url.split("@")[1]
				stream = sref[0].split(":")[len(sref[0].split(":"))-1].lower() + "://" + url
				ref = sref[0].replace(':'+sref[0].split(":")[len(sref[0].split(":"))-1],'')
				return ref, stream
			else:
				ref = ''
				stream = False
				return ref, stream
		except:
			ref = ''
			stream = False
			return ref, stream