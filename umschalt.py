
# Notwendige Bibliotheken importieren
# import necessary libraries
import time
import threading
import RPi.GPIO as GPIO

# RPi.GPIO Layout vewenden (wie Pin-Nummern)
# use RPi.GPIO layout (use pin-numbers)
GPIO.setmode(GPIO.BOARD)

# bei Programmstart Status von Solus abrufen
# get state from Solus at startup
## !!!! muss noch geschrieben werden
## !!!! to write

# falls kein Status ausgelesen werden kann?! Zumindest zum testen
# if we can't get the state?! At least to test this script

# Was ist auf Sendung? What's on air? 1 = Studio 1; 2 = Studio 2; 3 = Aussenstudio/ other studio; 0 = Automation
onair = 0
# Freigabe erteilt? Already give away signal? (Standard ist False, aber bei Automation True; Standard's False, but True with automation)
give = True
# Uebernahme angefordert? Any studio already wants signal?
take = False
# Was wird geschehen? What's going to happen? 1 = Freigabe/ want to give; 2 = Uebernahme/ want to take; 3 = Uebergabe/ will switch; 9 = Sofort-Uebergabe/ will switch immediately
#dowhat = 0
# Was wird als naechstes auf Sendung sein? What will be on air next? 1 = Studio 1; 2 = Studio 2; 3 = Aussenstudio/ other Studio; 0 = Automation
next = 0
# Welches Studio hat "Sofort"-Button gedrueckt? Which studio hast pressed the "immediate"-button? 0 = keins/none; 1 = Studio 1; 2 = Studio 2; 3 = Aussenstudio/ other Studio 
sofort = 0
# Wurde im Sofort-Studio Freigabe erteilt? Did the Studio which issued the "immediate"-call also issue "give"?
sofortgive = False
# Welches Studio will sofort uebernehmen? Which studio wants to take over the Signal immediately?
sofortto = 0
# LED-Check initlialisieren/ Initialize LED-Check
ledchange = True


# Klasse "Button" (Schalter) definieren
# define class "Button"
class Button:
    # Eigenschaften der Buttons definieren und pin initialisieren
    # define properties of buttons and initialize pin
    def __init__(self, pin, studio, function):
        # Pin-Nummer/ pin-number on raspi
        self.pin = pin
        # Studio Nummer/ number (s. oben/ see above)
        self.studio = studio
        # Funktion des/ function of Button(s): Freigabe/ Give = F; Uebernahme/ want = U; SOFORT/ imediate = S
        self.function = function
        # fuer unten/ see below
        self.laston = False
        self.nowon = False
        # Pin auf raspi initialisieren/ initialise pin on raspi
        GPIO.setup(self.pin, GPIO.IN)
    # Status-Aenderung
    # Change state
    def changestate(self):
	# die globalen Variablen muessen in die Funktion geholt werden
	# global variables have to be declared as such
	global onair, give, take, next, sofort, sofortgive, sofortto, ledchange
	# Fuer Freigabe-Button
	# For release-button
	if self.function == 'F':
	    print "F1"
	    # Fuer das eigene Studio
	    # For the own studio
	    if onair == self.studio:
		print "F2"
		# Fuer Kombinationen mit sofort
		# For combinations with immediate
		if sofort == self.studio:
		    print "F3"
		    # Sofort-Freigabe erteilen
		    # Set immediate-release
		    if sofortgive != True:
			print "F4"
			sofortgive = True
			ledchange = True
		    else:
			# Sofort-Freigabe zuruecknehmen, wenn nicht von anderem Studio schon angefordert
			# Reset sofort-give, if no other studio claimed the signal
			print "F5"
			if sofortto == 0:
			    sofortgive = False
			    sofort = 0
			    ledchange = True
		# Normale Freigaben
		# Regular release
		else:
		    print "F6"
		    # Wenn noch nicht freigegeben: freigeben
		    # If not yet set to give, set to give
		    if give == False:
			print "F7"
			give = True
			ledchange = True
		    # Wenn schon freigeben, dann wieder "zuruecknehmen", wenn noch kein anderes Studio will
		    # If already set to give, then take back, if no other studio wants to take
		    else:
			print "F8"
			if take == False:
			    print "F9"
			    give = False
			    ledchange = True
	    # Fuer anderes Studio; for other studio
	    # Mit Freigabe die eigene Uebernahme-Anforderung zuruecksetzen
	    # give to reset own wish to take
	    else:
		print "F10"
		if (take == True) and (next == self.studio):
		    print "F11"
		    take = False
		    next = 0
		    ledchange = True
	# Fuer Uebernahme-Button
	# For Claim-Button
	if self.function == 'U':
	    print "U1"
            # Fuer Kombinationen mit sofort
            # For combinations with immediate
            # Sofort uebernehmen von Automat
            # Switch immediately from automation
	    if sofort != 0:
		print "U2"
		if (onair == 0) and (sofort == self.studio):
		    print "U3"
		    sofortto = self.studio
		    umschaltsofort()
		    ledchange = True
		# Sofort uebernehmen von anderem Studio
		# Switch immediately from other studio
		if (sofort != self.studio) and (sofortgive == True):
		    print "U4"
		    sofortto = self.studio
		    umschaltsofort()
		    ledchange = True
		# Reset bei eigener Sofort-Uebergabe
		# Reset own immediate-release
		if (sofort == self.studio) and (sofortgive == True):
		    print "U5"
		    sofort = 0
		    sofortgive = False
		    ledchange = True
	    # Normale Uebernahmen
	    # Regular claim
	    else:
		print "U6"
		# Fuer das eigene Studio (-> Reset) und nur falls noch keine andere Uebernahme-Anforderung
		# For own studio (-> reset) and only if no other studio already wants to take
		if (onair == self.studio) and (give == True) and (take == False):
		    print "U7"
		    give = False 
		    ledchange = True
		# Uebernahme von anderem Studio
		# Take from other Studio
		if onair != self.studio:
		    print "U8"
		    # Noch keine andere Uebernahme-Anforderung
		    # No other studio wants to take yet
		    if take == False:
			print "U9"
			take = True
			next = self.studio
			ledchange = True
		    # Es gibt schon eine eigene Uebernahme-Anforderung -> Reset
		    # The own studio already wanted to take -> Reset
		    else:
			print "U10"
			if next == self.studio:
			    print "U11"
			    take = False
			    next = 0
			    ledchange = True
	# Fuer Sofort-Button
	# For "immediate"-Button
	if self.function == 'S':
	    print "S1"
	    # Wenn das eigene Studio oder die Automation on Air ist
	    # If own studio or automation is on air
	    if (onair == 0) or (onair == self.studio):
		print "S2"
		# Wenn sofort noch nicht aktiviert, fuer das eigene Studio aktivieren
		# If sofort isn't alredy activated, activate it for own studio
		if sofort == 0: 
		    print "S4"
		    sofort = self.studio
		    ledchange = True
		# Reset, wenn es schon das eigene Studio ist
		# Reset, if it's already own studio
		elif (sofort == self.studio) and (sofortto == 0): 
		    print "S5"
		    sofort = 0
		    sofortgive = False
		    ledchange = True
    # Abfrage des Buttons und ggf. Aenderung des Status
    # check button and change state if neccesary
    def buttoncheck(self):
	# wird nur fuer die print-funktionen gebraucht, kann spaeter also wieder weg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	global onair, give, take, next, sofort, sofortgive, sofortto, ledchange
        # In Variable schreiben, wenn Button gedrueckt (also Strom kommt am Pin an)
        # write to variable if button is pressed (theres electricity at the pin)
        if GPIO.input(self.pin) == GPIO.HIGH:
            self.nowon = True
#	    print 'Button {}{}, pin {} pressed'.format(self.studio, self.function, self.pin)
        else:
            self.nowon = False
        # Pruefen, ob sich etwas gegenueber letzter Abfrage geaendert hat
        # see if state has changed since last check
        if self.laston != self.nowon:
            # Wenn vorher an war (und jetzt also aus), dann nichts tun (ausser "vorher" auf aus setzen)
            # if it was on (which means that it's off now) then do nothing (except set laston to false)
            if self.laston == True:
		self.laston = False
#		print 'Button studio {} function {} pin {} not pressed any more'.format(self.studio, self.function, self.pin)
            # Wenn vorher aus war (und jetzt also an), dann Code ausfuehren (und "vorher" auf an setzen)
            # if it was off (which means that it's on now) then run the code (and set laston to true)
            else:
                self.laston = True
		print 'Noticed: Button studio {} function {} pin {} newly pressed'.format(self.studio, self.function, self.pin)
		print "**** Old State ****"
		print "On air:", onair, "Freigabe:", give, "Uebernahme:", take, "Als naechstes:", next
		print "Sofort gedrueckt:", sofort, "sofortgive:", sofortgive, "sofortto:", sofortto
		print "ledchange:", ledchange
                self.changestate()
		print "**** New State ****"
		print "On air:", onair, "Freigabe:", give, "Uebernahme:", take, "Als naechstes:", next 
		print "Sofort gedrueckt:", sofort, "sofortgive:", sofortgive, "sofortto:", sofortto  
                print "ledchange:", ledchange



# Klasse "LED" definieren
# define class "LED"
class LED:
    # Eigenschaften der LEDs definieren und Pins initialisieren
    # define properties of LEDs and initialize pins
    def __init__(self, pin, studio, color):
        # Pin-Nummer/ pin-number on raspi
        self.pin = pin
        # Studio Nummer/ number (s. oben/ see above)
        self.studio = studio
        # Farbe des/ color of LED(s): gruen/green = g; gelb/yellow = y; rot/red = r
        self.color = color
        # Pin auf raspi initialisieren und ausmachen/ initialise pin on raspi and switch off
        GPIO.setup(self.pin, GPIO.OUT)
	GPIO.output(self.pin, GPIO.LOW)
        # Variable, damit das Programm weiss, ob LED an
	# Variable to let the script know, if LED is on
        self.onind = False
	# s.o. nur fuer Blinken
	# see above, only for blink
	self.blinkind = False
    # Anschalten
    # Turn on
    def on(self):
	GPIO.output(self.pin, GPIO.HIGH)
	self.onind = True
	print "LED", self.color, "Studio", self.studio, "Pin", self.pin, "on, on-indicator =", self.onind
    # Blinken
    # Blink
    def blink(self):
#	# Variable fuer die Benennung festlegen
#	# Setting up variable for naming thread
#	name = self.pin
	# Variable, die sagt, ob geblinkt wird
	# Variable which tells if there's blinking to do
	self.blinkind = True
	# Thread erstellen
	# Create thread
	b = self.blinkbase(self.pin, self.pin, 0.5)
	# Thread starten
	# Start thread
	b.start()
    # Schnell blinken
    # Blink fast
    def blinkfast(self):
#        # Variable fuer die Benennung festlegen
#        # Setting up variable for naming thread
#        name = self.pin
	# Variable, die sagt, ob geblinkt wird
	# Variable which tells if there's blinking to do
	self.blinkind = True
	# Thread erstellen
	# Create thread
	b = self.blinkbase(self.pin, self.pin, 0.25)
	# Thread starten
	# Start thread
	b.start()
    # Ausschalten
    # Turn off
    def off(self):
	if self.onind == True:
	    GPIO.output(self.pin, GPIO.LOW)
	    self.onind = False
	    print "LED", self.color, "Studio", self.studio, "Pin", self.pin, "off, on-indicator =", self.onind
	if self.blinkind == True:
#	    self.pin.onsignal = False #-> Funktioniert so nicht
	    self.blinkind = False
	    print "LED", self.color, "Studio", self.studio, "Pin", self.pin, "blink-off, blink-indicator=", self.blinkind
    # Was ist blinken?
    # Define, how to blink
#    def blinkforever(self, delay):
#	self.delay = delay
#	while self.blinkind == True:
#	    GPIO.output(self.pin, GPIO.HIGH)
#	    time.sleep(self.delay)
#	    GPIO.output(self.pin, GPIO.LOW)
#	    time.sleep(self.delay)		
    # Thread fuer's Blinken definieren
    # Define Thread for blinking
    class blinkbase(threading.Thread):
	def __init__(self, name, pin, delay):
	    threading.Thread.__init__(self)
	    self.name = name
	    self.pin = pin
	    self.delay = delay
	    self.onsignal = True
	def run(self):
#	    blinkforever(self.delay)
	    while self.onsignal == True:
		GPIO.output(self.pin, GPIO.HIGH)
		time.sleep(self.delay)
		GPIO.output(self.pin, GPIO.LOW)
		time.sleep(self.delay)

    # Sehen, ob was an den LEDs geaendert werden muss
    # Check, if LEDs have to change
    def ledcheck(self):
	# die globalen Variablen muessen in die Funktion geholt werden
	# global variables have to be declared as such
	global onair, give, take, next, sofort, sofortgive, sofortto, ledchange
	# Fuer die gruenen LEDs
	# For the green LEDs
	if self.color == 'g':
	    print self.studio, self.color, "Lg1"
	    # Anschalten, wenn das eigene Studio on Air ist
	    # On, if own studio's on air
	    if (onair == self.studio):
		print self.studio, self.color, "Lg2"
		print "LED", self.studio, "color", self.color, "on"
		self.on()
	    # Blinken, wenn das eigene Studio zur naechsten Stunde on Air sein wird
	    # Blink, if own studio will be on air at next hour
	    elif (next == self.studio) and (give == True):
		print self.studio, self.color, "Lg3"
                print "LED", self.studio, "color", self.color, "blink"
		self.blink()
#		self.on()
	    # Schnell blinken, wenn das eigene Studio 'sofort' on Air gehen wird, sollte nur fuer Automation relevant sein
	    # Blink fast, if own Studio will be on Air 'immediately', should only be relevant for automation
	    elif (sofortto == self.studio):
		print self.studio, self.color, "Lg4"
                print "LED", self.studio, "color", self.color, "blinkfast"
		self.blinkfast()
#		self.on()
	    # In allen anderen Faellen aus
	    # Off in any other case
	    else: 
		self.off()
		print self.studio, self.color, "Lg5"
#                print "LED", self.studio, "color", self.color, "off"
	# Fuer die gelben LEDs
	# For the yellow LEDs
	if self.color == 'y':
	    print self.studio, self.color, "Ly1"
	    # Blinken, wenn das eigene Studio Uebernahme angefordert hat (aber noch keine Freigabe erhalten)
	    # Blink, if own studio wants to take (and other studio hasn't already pressed give)
	    if (next == self.studio) and (give == False):
		print self.studio, self.color, "Ly2"
                print "LED", self.studio, "color", self.color, "blink"
		self.blink()
#		self.on()
	    # Sonst aus
	    # Otherwise off
	    else:
		print self.studio, self.color, "Ly3"
#		print "LED", self.studio, "color", self.color, "off"
		self.off()
	# Fuer die roten LEDs
	# For the red LEDs
	if self.color == 'r':
	    print self.studio, self.color, "Lr1"
	    # Falls das eigene Studio 'sofort' gedrueckt hat
	    # If own studio has pressed 'sofort'
	    if sofort == self.studio: 
		print self.studio, self.color, "Lr2"
                print "LED", self.studio, "color", self.color, "on"
		self.on()
	    else:
		print self.studio, self.color, "Lr3"
#		print "LED", self.studio, "color", self.color, "off"
		self.off()



# Umschalt-Logik definieren
# Define what's going to happen when it's time to switch
def umschalt():
    # die globalen Variablen muessen in die Funktion geholt werden
    # global variables have to be declared as such
    global onair, give, take, next, sofort, sofortgive, sofortto, ledchange
    print "++++++ Umschalt-Zeit! ++++++"
    print "**** Old State ****"
    print "On air:", onair, "Freigabe:", give, "Uebernahme:", take, "Als naechstes:", next
    print "Sofort gedrueckt:", sofort, "sofortgive:", sofortgive, "sofortto:", sofortto
    print "ledchange:", ledchange
    # Es muss nur was getan werden, wenn auch Freigegeben wurde
    # Switch only if "give" was set
    if give == True:
	if take == True:
	    umschaltsignal(next)
	    print "Switching", onair, "->", next
	    onair = next
	    give = False
	    take = False
	    next = 0
	else:
	    if onair != 0: 
		umschaltsignal(0)
		print "Switching", onair, "->", next
		onair = 0
		give = True
	ledchange = True
	sofort = 0
	sofortgive = False
	sofortto = 0
    print "**** New State ****"
    print "On air:", onair, "Freigabe:", give, "Uebernahme:", take, "Als naechstes:", next
    print "Sofort gedrueckt:", sofort, "sofortgive:", sofortgive, "sofortto:", sofortto
    print "ledchange:", ledchange


# Sofort-Umschalt-Logik definieren
# Define immediate-switch-logik

##### Only for immediate give (immediate take switches immediately)
#### Has to be own thread which counts down time (or waits for countdown-thread to end) until: 
### another studio wants to take
### countdown is reset by calling studio
### at the end of countdown switches to automation
#### Method: Changing "normal" variables and calling umschalt()

#def umschaltsofort():
    # die globalen Variablen muessen in die Funktion geholt werden
    # global variables have to be declared as such
#    global onair, give, take, next, sofort, sofortgive, sofortto, ledchange
#    print "++++++ Waiting for the right buttons to be pushed ++++++"
#
#    print "++++++ Sofort-Umschalt-Zeit ++++++"
#    print "**** Old State ****"
#    print "On air:", onair, "Freigabe:", give, "Uebernahme:", take, "Als naechstes:", next
#    print "Sofort gedrueckt:", sofort, "sofortgive:", sofortgive, "sofortto:", sofortto
#    print "ledchange:", ledchange
    # Fuer sofort-Aufruf
    # For call with sofort (immediate)
#    if sofortgive == True:
	# Wenn anderes Studio sofort uebernehmen will
	# If other Studio wants to take immediately
#	if sofortto != 0: 
#	    umschaltsignal(sofortto)
#	    print "Switching", onair, "->", sofortto
#	    onair = sofortto
#	else: 
	    # Hier Counter als gesonderten Thread einfuehren, nach Ablauf umschalten auf Automat
	    # Need Counter as own Thread; If Counter's finished (and nothing's changed), 
#	    if onair == 0:
#	        give = True
#	    else:
#	        give = False
#	take = False
#	ledchange = True
#	sofort = 0
#	sofortto = 0
#	sofortgive = False


# Umschalt-Signal fuer den Audio-Router definieren
# Define the signal that is sent to the audio-router
def umschaltsignal(switchto):
    # muss noch definiert werden
    # to be defined
    print "switching to:", switchto


print 'Initialize buttons:'
# Buttons anlegen; make buttons
B1F = Button(33, 1, 'F')
print 'Button 1F initialised'
B1U = Button(35, 1, 'U')
print 'Button 1U initialised'
B1S = Button(37, 1, 'S')
print 'Button 1S initialised'
B2F = Button(36, 2, 'F')
print 'Button 2F initialised'
B2U = Button(38, 2, 'U')
print 'Button 2U initialised'
B2S = Button(40, 2, 'S')
print 'Button 2S initialised'

print 'Initialize LEDs:'
# LEDs anlegen; make LEDs
L1G = LED(7, 1, 'g')
L1G.on()
time.sleep(0.5)
L1Y = LED(11, 1, 'y')
L1Y.on()
time.sleep(0.5)
L1R = LED(29, 1, 'r')
L1R.on()
time.sleep(0.5)
L2G = LED(13, 2, 'g')
L2G.on()
time.sleep(0.5)
L2Y = LED(15, 2, 'y')
L2Y.on()
time.sleep(0.5)
L2R = LED(31, 2, 'r')
L2R.on()
time.sleep(0.5)
L3G = LED(19, 3, 'g')
L3G.on()
time.sleep(0.5)
L3Y = LED(21, 3, 'y')
L3Y.on()
time.sleep(0.5)
L0G = LED(23, 0, 'g')
L0G.on()

time.sleep(0.5)

for L in [L1G, L1Y, L1R, L2G, L2Y, L2R, L3G, L3Y, L0G]:
    L.off()


print "**** State ****"
print "On air:", onair, "Freigabe:", give, "Uebernahme:", take, "Als naechstes:", next
print "Sofort gedrueckt:", sofort, "sofortgive:", sofortgive, "sofortto:", sofortto
print "ledchange:", ledchange


print 'Lets listen to the buttons and light some LEDs'
while True:
    if time.strftime('%M%S') == '0000':
	# gmtime, damit Zeitumstellung keine Rolle spielt
	# gmtime, so that dst won't do any harm
	time = time.strftime('%H%M%S', time.gmtime())
	if 'lasttime' not in locals():
	    lasttime = '000000'
	if time != lasttime:
	    umschalt()
	    lasttime = time
    for B in [B1F, B1U, B1S, B2F, B2U, B2S]: 
	B.buttoncheck()
	if ledchange  == True:
	    for L in [L1G, L1Y, L1R, L2G, L2Y, L2R, L3G, L3Y, L0G]:
		L.ledcheck()
	    ledchange=False
    time.sleep(0.05)


GPIO.cleanup()
