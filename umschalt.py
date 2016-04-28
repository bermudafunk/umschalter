
# Notwendige Bibliotheken importieren
# import necessary libraries
import time
import threading
import logging
import RPi.GPIO as GPIO

# Logging-Format definieren; Letztes Wort aendern: DEBUG, INFO, WARNING, etc.
# Define logging-format; Change last word: DEBUG, INFO, WARNING
logging.basicConfig(filename='umschalt.log', format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)

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
	    logging.debug("F1 - release-button in studio {} pressed".format(self.studio))
	    # Fuer das eigene Studio
	    # For the own studio
	    if onair == self.studio:
		logging.debug("F2 - own studio is on air")
		# Fuer Kombinationen mit sofort
		# For combinations with immediate
		if sofort == self.studio:
		    logging.debug("F3 - immediate-state already acquired for own studio (not other studio)")
		    # Sofort-Freigabe erteilen
		    # Set immediate-release
		    if sofortgive != True:
			logging.debug("F4 - immediate-release not yet triggered -> triggering immediate-release")
			sofortgive = True
			soforttimer()
			ledchange = True
		    else:
			# Sofort-Freigabe zuruecknehmen, wenn nicht von anderem Studio schon angefordert
			# Reset sofort-give, if no other studio claimed the signal
			logging.debug("F5 - immediate-release has already been triggered")
			if sofortto == 0:
			    logging.debug("F5a - and no other studio claimed -> resetting immediate-release")
			    sofortgive = False
			    sofort = 0
			    soforttimerstop()
			    ledchange = True
		# Normale Freigaben
		# Regular release
		else:
		    logging.debug("F6 - no 'immediate' involved, we want a regular release")
		    # Wenn noch nicht freigegeben: freigeben
		    # If not yet set to give, set to give
		    if give == False:
			logging.debug("F7 - no release triggered yet, triggering release")
			give = True
			ledchange = True
		    # Wenn schon freigeben, dann wieder "zuruecknehmen", wenn noch kein anderes Studio will
		    # If already set to give, then take back, if no other studio wants to take
		    else:
			logging.debug("F8 - release already triggered")
			if take == False:
			    logging.debug("F8a - but no other studio claimed -> resetting release")
			    give = False
			    ledchange = True
	    # Fuer anderes Studio; for other studio
	    # Mit Freigabe die eigene Uebernahme-Anforderung zuruecksetzen
	    # give to reset own wish to take
	    else:
		logging.debug("F10 - other studio is on air")
		if (take == True) and (next == self.studio):
		    logging.debug("F11 - did already claim -> resetting claim")
		    take = False
		    next = 0
		    ledchange = True
	# Fuer Uebernahme-Button
	# For Claim-Button
	if self.function == 'U':
	    logging.debug("U1 - claim-button in studio {} pressed".format(self.studio))
            # Fuer Kombinationen mit sofort
            # For combinations with immediate
	    if sofort != 0:
		logging.debug("U2 - immediate-state already pressed")
		# Sofort uebernehmen von Automat
		# Switch immediately from automation
		if (onair == 0) and (sofort == self.studio):
		    logging.debug("U3 - automations on air, immediate-state already acquired for own studio -> switching to own studio immediately")
		    sofortto = self.studio
		    umschaltsofort()
		    ledchange = True
		# Sofort uebernehmen von anderem Studio
		# Switch immediately from other studio
		if (sofort != self.studio) and (sofortgive == True):
		    logging.debug("U4 - other studio on air which issued immediate release -> switching to own studio immediately")
		    sofortto = self.studio
		    soforttimerstop()
		    umschaltsofort()
		    ledchange = True
		# Reset bei eigener Sofort-Uebergabe
		# Reset own immediate-release
		if (sofort == self.studio) and (sofortgive == True):
		    logging.debug("U5 - own studio on air, immediate-release already triggered -> resetting immediate-release")
		    sofort = 0
		    sofortgive = False
		    soforttimerstop()
		    ledchange = True
	    # Normale Uebernahmen
	    # Regular claim
	    else:
		logging.debug("U6 - no 'immediate' involved - regular claim")
		# Fuer das eigene Studio (-> Reset) und nur falls noch keine andere Uebernahme-Anforderung
		# For own studio (-> reset) and only if no other studio already wants to take
		if (onair == self.studio) and (give == True) and (take == False):
		    logging.debug("U7 - own studios on air, already issued release but no other studio claimed -> resettig release")
		    give = False 
		    ledchange = True
		# Uebernahme von anderem Studio
		# Take from other Studio
		if onair != self.studio:
		    logging.debug("U8 - other studio on air")
		    # Noch keine andere Uebernahme-Anforderung
		    # No other studio wants to take yet
		    if take == False:
			logging.debug("U9 - no other studio claimed yet -> claiming for own studio")
			take = True
			next = self.studio
			ledchange = True
		    # Es gibt schon eine eigene Uebernahme-Anforderung -> Reset
		    # The own studio already wanted to take -> Reset
		    else:
			logging.debug("U10 - some studio already claimed")
			if next == self.studio:
			    logging.debug("U11 - but it was the own studio -> resetting claim")
			    take = False
			    next = 0
			    ledchange = True
	# Fuer Sofort-Button
	# For "immediate"-Button
	if self.function == 'S':
	    logging.debug("S1 - immediate-button in studio {} pressed".format(self.studio))
	    # Wenn das eigene Studio oder die Automation on Air ist
	    # If own studio or automation is on air
	    if (onair == 0) or (onair == self.studio):
		logging.debug("S2 - automation or own studio is on air")
		# Wenn sofort noch nicht aktiviert, fuer das eigene Studio aktivieren
		# If sofort isn't alredy activated, activate it for own studio
		if sofort == 0: 
		    logging.debug("S3 - no other studio set immediate-state yet -> setting immediate-state for own studio")
		    sofort = self.studio
		    ledchange = True
		# Reset, wenn es schon das eigene Studio ist
		# Reset, if it's already own studio
		elif (sofort == self.studio) and (sofortto == 0): 
		    logging.debug("S4 - own studio had set immediate-state -> resetting immediate-state")
		    sofort = 0
		    if sofortgive == True:
			logging.debug("S5 - own studio had already issued immediate-release -> taking that back too")
			sofortgive = False
			soforttimerstop()
		    ledchange = True
    # Abfrage des Buttons und ggf. Aenderung des Status
    # check button and change state if neccesary
    def buttoncheck(self):
	global onair, give, take, next, sofort, sofortgive, sofortto, ledchange
        # In Variable schreiben, wenn Button gedrueckt (also Strom kommt am Pin an)
        # write to variable if button is pressed (theres electricity at the pin)
        if GPIO.input(self.pin) == GPIO.HIGH:
            self.nowon = True
#	    logging.debug("Button {}{}, pin {} pressed".format(self.studio, self.function, self.pin))
        else:
            self.nowon = False
        # Pruefen, ob sich etwas gegenueber letzter Abfrage geaendert hat
        # see if state has changed since last check
        if self.laston != self.nowon:
            # Wenn vorher an war (und jetzt also aus), dann nichts tun (ausser "vorher" auf aus setzen)
            # if it was on (which means that it's off now) then do nothing (except set laston to false)
            if self.laston == True:
		self.laston = False
#		logging.debug("Button studio {} function {} pin {} not pressed any more".format(self.studio, self.function, self.pin))
            # Wenn vorher aus war (und jetzt also an), dann Code ausfuehren (und "vorher" auf an setzen)
            # if it was off (which means that it's on now) then run the code (and set laston to true)
            else:
                self.laston = True
		logging.info("noticed: button studio {}, function {}, pin {} pressed".format(self.studio, self.function, self.pin))
		logging.debug("**** pre-button - old state ****")
		logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, next))
		logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort, sofortgive, sofortto))
		logging.debug("ledchange: {}".format(ledchange))
		logging.debug("issuing changestate-call to see if something has to change")
                self.changestate()
                logging.debug("**** post-button - new state ****")
		logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, next))
		logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort, sofortgive, sofortto))
		logging.debug("ledchange: {}".format(ledchange))


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
	if self.blinkind == False:
	    self.onind = True
	    GPIO.output(self.pin, GPIO.HIGH)
	    logging.debug("Now on: LED {}, Studio {}, Pin {}, on-indicator = {}".format(self.color, self.studio, self.pin, self.onind))
	else:
            self.blinkstop.set()
            self.blinkind = False
            # Wenn die LED geblinkt hat, braucht sie Zeit, um den letzten Blink-Zyklus zu beenden
	    # Deshalb einen Timer anwerfen, um in einer Sekunde erneut einen LED-Check durchzufuerhren (und die LED anzuschalten)
	    # if LED was blinking, we need to wait for the thread to end
	    # so we call a timer which waits for one second to ledcheck again (and turn on the LED)
	    logging.debug("LED {}, Studio {} did blink and should be on. Turned blinking off and called a timer to ledcheck again in a second".format(self.color, self.studio))
	    blinkstopcountdown = threading.Timer(1, specialledcheck)
	    blinkstopcountdown.daemon = True
	    blinkstopcountdown.start()
    # Blinken
    # Blink
    def blink(self):
	if self.blinkind != 'slow':
	    # Variable, die sagt, ob geblinkt wird
	    # Variable which tells if there's blinking to do
	    self.blinkind = 'slow'
	    # Stopp-Signal fuers blink-Thread definieren
	    # Define stop-signal for blink-Thread
	    self.blinkstop = threading.Event()
	    # Thread erstellen
	    # Create thread
	    b = self.blinkbase(self.pin, 0.5, self.blinkstop)
	    # Thread als Daemon aufrufen (endet mit Programmende)
	    # Create thread as daemon, so that it ends when the main programm ends
	    b.daemon = True
	    # Thread starten
	    # Start thread
	    b.start()
	    logging.debug("Now blinking: LED {}, Studio {}, Pin {}, blink-indicator = {}".format(self.color, self.studio, self.pin, self.blinkind))
        else:
            self.blinkstop.set()
            self.blinkind = False
            # Wenn die LED geblinkt hat, braucht sie Zeit, um den letzten Blink-Zyklus zu beenden
            # Deshalb einen Timer anwerfen, um in einer Sekunde erneut einen LED-Check durchzufuerhren (und die LED anzuschalten)
            # if LED was blinking, we need to wait for the thread to end
            # so we call a timer which waits for one second to ledcheck again (and turn on the LED)
            logging.debug("LED {}, Studio {} did blink and should be on. Turned blinking off and called a timer to ledcheck again in a second".format(self.color, self.studio))
            blinkstopcountdown = threading.Timer(1, specialledcheck)
            blinkstopcountdown.daemon = True
            blinkstopcountdown.start()
    # Schnell blinken
    # Blink fast
    def blinkfast(self):
	if self.blinkind != 'fast':
	    # Variable, die sagt, ob geblinkt wird
	    # Variable which tells if there's blinking to do
	    self.blinkind = 'fast'
	    # Stopp-Signal fuers blink-Thread definieren
	    # Define stop-signal for blink-Thread
	    self.blinkstop = threading.Event()
	    # Thread erstellen
	    # Create thread
	    b = self.blinkbase(self.pin, 0.25, self.blinkstop)
	    # Thread als Daemon aufrufen (endet mit Programmende)
	    # Create thread as daemon, so that it ends when the main programm ends
	    b.daemon = True
	    # Thread starten
	    # Start thread
	    b.start()
            logging.debug("Now blinking fast: LED {}, Studio {}, Pin {}, blink-indicator = {}".format(self.color, self.studio, self.pin, self.blinkind))
        else:
            self.blinkstop.set()
            self.blinkind = False
            # Wenn die LED geblinkt hat, braucht sie Zeit, um den letzten Blink-Zyklus zu beenden
            # Deshalb einen Timer anwerfen, um in einer Sekunde erneut einen LED-Check durchzufuerhren (und die LED anzuschalten)
            # if LED was blinking, we need to wait for the thread to end
            # so we call a timer which waits for one second to ledcheck again (and turn on the LED)
            logging.debug("LED {}, Studio {} did blink and should be on. Turned blinking off and called a timer to ledcheck again in a second".format(self.color, self.studio))
            blinkstopcountdown = threading.Timer(1, specialledcheck)
            blinkstopcountdown.daemon = True
            blinkstopcountdown.start()
    # Ausschalten
    # Turn off
    def off(self):
	if self.onind == True:
	    GPIO.output(self.pin, GPIO.LOW)
	    self.onind = False
	    logging.debug("Now off: LED {}, Studio {}, Pin {}, on-indicator = {}".format(self.color, self.studio, self.pin, self.onind))
	if self.blinkind != False:
	    self.blinkind = False
	    self.blinkstop.set()
	    # Zur Sicherheit; Blinken koennte ja auch aufhoeren, wenn LED gerade an
	    # To be sure that its really off and didnt stop blinking while led was on
            GPIO.output(self.pin, GPIO.LOW)
	    logging.debug("Now not blinking any more: LED {}, Studio {}, Pin {}, blink-indicator = {}".format(self.color, self.studio, self.pin, self.blinkind))
    # Thread fuer's Blinken definieren
    # Define Thread for blinking
    class blinkbase(threading.Thread):
	def __init__(self, pin, delay, stop_event):
	    threading.Thread.__init__(self)
	    self.pin = pin
	    self.delay = delay
	    self.stop_event = stop_event
	def run(self):
	    logging.debug("blink-thread startet")
	    while not self.stop_event.is_set():
		GPIO.output(self.pin, GPIO.HIGH)
		time.sleep(self.delay)
		GPIO.output(self.pin, GPIO.LOW)
		time.sleep(self.delay)
	    logging.debug("blink-thread finished")
    # Sehen, ob was an den LEDs geaendert werden muss
    # Check, if LEDs have to change
    def ledcheck(self):
	# die globalen Variablen muessen in die Funktion geholt werden
	# global variables have to be declared as such
	global onair, give, take, next, sofort, sofortgive, sofortto, ledchange
	# Fuer die gruenen LEDs
	# For the green LEDs
	if self.color == 'g':
	    logging.debug("Lg1 - LED-color is {}, studio is {}".format(self.color, self.studio))
	    # Anschalten, wenn das eigene Studio on Air ist
	    # On, if own studio's on air
	    if (onair == self.studio):
		logging.debug("Lg2 - own studio is on air, so shine!")
		self.on()
	    # Blinken, wenn das eigene Studio zur naechsten Stunde on Air sein wird
	    # Blink, if own studio will be on air at next hour
	    elif (next == self.studio) and (give == True):
		logging.debug("Lg3 - own studio will be next, other studio already released, so blink!")
		self.blink()
	    # Schnell blinken, wenn das eigene Studio 'sofort' on Air gehen wird, sollte nur fuer Automation relevant sein
	    # Blink fast, if own Studio will be on Air 'immediately', should only be relevant for automation
	    elif (sofortgive == True) and (sofortto == self.studio):
		logging.debug("Lg4 - own studio will be on air immediately, so blink fast!")
		self.blinkfast()
	    # In allen anderen Faellen aus
	    # Off in any other case
	    else: 
		logging.debug("Lg5 - own studio does not and wont do anything, so im off!")
		self.off()
	# Fuer die gelben LEDs
	# For the yellow LEDs
	if self.color == 'y':
	    logging.debug("Ly1 - LED-color is {}, studio is {}".format(self.color, self.studio))
	    # Blinken, wenn das eigene Studio Uebernahme angefordert hat (aber noch keine Freigabe erhalten)
	    # Blink, if own studio wants to take (and other studio hasn't already pressed give)
	    if (next == self.studio) and (give == False):
		logging.debug("Ly2 - own studio claimed but other studio didnt release yet, so blink!")
		self.blink()
	    # Sonst aus
	    # Otherwise off
	    else:
		logging.debug("Ly3 - no unanswered claim, so im off!")
		self.off()
	# Fuer die roten LEDs
	# For the red LEDs
	if self.color == 'r':
	    logging.debug("Lr1 - LED-color is {}, studio is {}".format(self.color, self.studio))
	    # Falls das eigene Studio 'sofort' gedrueckt hat
	    # If own studio has pressed 'sofort'
	    if sofort == self.studio: 
		logging.debug("Lr2 - own studio acquired immediate-state, so shine!")
		self.on()
	    else:
		logging.debug("Lr3 - own studio didn't acquire immediate-state, so im off!")
		self.off()


# Timer definieren, der ggf. zur vollen Stunde umschaltet
# Define timer that switches at the full hour if necessary
def timecheck():
    if time.strftime('%M%S') == '0000':
	global now, then
        # gmtime, damit Zeitumstellung keine Rolle spielt
        # gmtime, so that dst won't do any harm
        now = time.strftime('%H%M%S', time.gmtime())
        if 'then' not in globals():
            then = '999999'
        if now != then:
	    logging.info("++++++ the time to switch is now ++++++")
            umschalt()
            then = now


# Umschalt-Logik definieren
# Define what's going to happen when it's time to switch
def umschalt():
    # die globalen Variablen muessen in die Funktion geholt werden
    # global variables have to be declared as such
    global onair, give, take, next, sofort, sofortgive, sofortto, ledchange
    logging.info("++++++ switching now (if neccesary) ++++++")
    logging.debug("**** pre-switch - old state ****")
    logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, next))
    logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort, sofortgive, sofortto))
    logging.debug("ledchange: {}".format(ledchange))
    # Es muss nur was getan werden, wenn auch Freigegeben wurde
    # Switch only if "give" was set
    if give == True:
	logging.debug("release issued")
	if take == True:
	    logging.debug("claim issued, too")
	    umschaltsignal(next)
	    logging.info("switching {} -> {}".format(onair, next))
	    onair = next
	    give = False
	    take = False
	    next = 0
	else:
	    logging.debug("no claim issued")
	    if onair != 0: 
		logging.debug("but i dont want to be on air any more, so well switch to automation")
		umschaltsignal(0)
		logging.info("switching {} -> {}".format(onair, next))
		onair = 0
		give = True
	ledchange = True
	sofort = 0
	sofortgive = False
	sofortto = 0
    logging.debug("**** post-switch - new state ****")
    logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, next))
    logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort, sofortgive, sofortto))
    logging.debug("ledchange: {}".format(ledchange))




# Sofort-Umschalt-Logik definieren: sofort-Stati werden in normale Stati uebersetzt und der normale Umschalt-Vorgang gestartet
# define immediate-switch-logik: will translate immediate-states to regular states and call regular switch process
def umschaltsofort():
    # die globalen Variablen muessen in die Funktion geholt werden
    # global variables have to be declared as such
    global onair, give, take, next, sofort, sofortgive, sofortto, ledchange
    logging.info("++++++ immediate switch happening ++++++")
    logging.debug("**** pre-immediate - old state ****")
    logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, next))
    logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort, sofortgive, sofortto))
    logging.debug("ledchange: {}".format(ledchange))
    give = True
    if sofortto == 0:
	take = False
    else:
	take = True
    next = sofortto
    sofort = 0
    sofortgive = False
    sofortto = 0
    logging.debug("**** post-immediate - new state ****")
    logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, next))
    logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort, sofortgive, sofortto))
    logging.debug("ledchange: {}".format(ledchange))
    logging.debug("calling switch-logic")
    umschalt()



# Sofort-Umschalt-Timer starten
# Start timer for immediate-switch	
def soforttimer():
    sofortcountdown = threading.Timer(30, umschaltsofort)
    global sofortcountdown
    sofortcountdown.daemon = True
    sofortcountdown.start()
    logging.debug("immediate-countdown started")


# Abbruch Sofort-Umschalt-Timer
# Cancelation of timer for immediate-switch
def soforttimerstop():
    global sofortcountdown
    sofortcountdown.cancel()
    logging.debug("immediate-countdown canceled")


# Um "gesondert" einen ledcheck zu initialisieren
# To initialize a special ledcheck
def specialledcheck():
    global ledchange
    ledchange = True


# Umschalt-Signal fuer den Audio-Router definieren
# Define the signal that is sent to the audio-router
def umschaltsignal(switchto):
    # muss noch definiert werden
    # to be defined
    logging.info("telling audio routing-machine what has to be on air next")
    pass


logging.info("starting programm")
logging.info("setting up buttons")
# Buttons anlegen; make buttons
B1F = Button(33, 1, 'F')
B1U = Button(35, 1, 'U')
B1S = Button(37, 1, 'S')
B2F = Button(36, 2, 'F')
B2U = Button(38, 2, 'U')
B2S = Button(40, 2, 'S')


logging.info("setting up leds")
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

logging.debug("++++++ initial states ++++++")
logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, next))
logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort, sofortgive, sofortto))
logging.debug("ledchange: {}".format(ledchange))


logging.info("++++++ starting main process ++++++")
while True:
    timecheck()
    for B in [B1F, B1U, B1S, B2F, B2U, B2S]: 
	B.buttoncheck()
	if ledchange  == True:
	    for L in [L1G, L1Y, L1R, L2G, L2Y, L2R, L3G, L3Y, L0G]:
		L.ledcheck()
	    ledchange=False
    time.sleep(0.05)


GPIO.cleanup()
