#!/usr/bin/python3

# Notwendige Bibliotheken importieren
# import necessary libraries
import time
import threading
import logging
import signal
import os.path
import RPi.GPIO as GPIO

# Logging-Format definieren; Letztes Wort aendern: DEBUG, INFO, WARNING, etc.
# Define logging-format; Change last word: DEBUG, INFO, WARNING
logging.basicConfig(filename='/var/log/umschalt.log', format='%(asctime)s : %(levelname)s : %(message)s',
                    level=logging.INFO)

# RPi.GPIO Layout vewenden (wie Pin-Nummern)
# use RPi.GPIO layout (use pin-numbers)
GPIO.setmode(GPIO.BOARD)


# Variablen setzen
# Set variables

# Bei Programmstart Status von Solus abrufen
# Get state from Solus at startup
# !!!! muss noch geschrieben werden
# !!!! to be writen
def getstate():
    global onair
    pass


# Variablen setzen
# Set variables
# Status aus Datei von letztem Programmaufruf holen
# Get state from last programme-run
def setstate():
    logging.info("Setstate: checking if we can get variables from file")
    global onair, give, take, nexton, sofort, sofortgive, sofortto, ledchange
    defvar = False
    if os.path.isfile("statesave.txt"):
        statesave = open("statesave.txt", "r")
        logging.debug("Setstate: statesave-file exists")
        variables = statesave.read()
        timeend = variables.split(';')[0]
        timestart = time.strftime('%Y%m%d%H')
        if timeend == timestart:
            logging.debug("Setstate: statesave has been saved in the current hour, so we'll take variables from it")
            onair = variables.split(';')[1]
            give = variables.split(';')[2]
            if give == 'True':
                give = True
            else:
                give = False
            take = variables.split(';')[3]
            if take == 'True':
                take = True
            else:
                take = False
            nexton = variables.split(';')[4]
            logging.debug("onair: {}, give: {}, take: {}, next: {}".format(onair, give, take, nexton))
        else:
            logging.debug("Setstate: statesave is older then an hour, won't use it. using default-variables.")
            defvar = True
    else:
        logging.debug("Setstate: no statesave-file present. using default-variables")
        defvar = True

    if defvar == True:
        # Was ist auf Sendung? What's on air? 1 = Studio 1; 2 = Studio 2; 3 = Aussenstudio/ other studio; 0 = Automation
        onair = '0'
        # Freigabe erteilt? Already give away signal? (Standard ist False, aber bei Automation True; Standard's False, but True with automation)
        give = True
        # Uebernahme angefordert? Any studio already wants signal?
        take = False
        # Was wird geschehen? What's going to happen? 1 = Freigabe/ want to give; 2 = Uebernahme/ want to take; 3 = Uebergabe/ will switch; 9 = Sofort-Uebergabe/ will switch immediately
        # dowhat = '0'
        # Was wird als naechstes auf Sendung sein? What will be on air next? 1 = Studio 1; 2 = Studio 2; 3 = Aussenstudio/ other Studio; 0 = Automation
        nexton = '0'

    # Welches Studio hat "Sofort"-Button gedrueckt? Which studio hast pressed the "immediate"-button? 0 = keins/none; 1 = Studio 1; 2 = Studio 2; 3 = Aussenstudio/ other Studio 
    sofort = '0'
    # Wurde im Sofort-Studio Freigabe erteilt? Did the Studio which issued the "immediate"-call also issue "give"?
    sofortgive = False
    # Welches Studio will sofort uebernehmen? Which studio wants to take over the Signal immediately?
    sofortto = '0'
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

    # Abfrage des Buttons und ggf. Aenderung des Status
    # check button and change state if neccesary
    def buttoncheck(self):
        global onair, give, take, nexton, sofort, sofortgive, sofortto, ledchange
        # In Variable schreiben, wenn Button gedrueckt (also Strom kommt am Pin an)
        # write to variable if button is pressed (theres electricity at the pin)
        if GPIO.input(self.pin) == GPIO.HIGH:
            self.nowon = True
        #            logging.debug("Button {}{}, pin {} pressed".format(self.studio, self.function, self.pin))
        else:
            self.nowon = False
        # Pruefen, ob sich etwas gegenueber letzter Abfrage geaendert hat
        # see if state has changed since last check
        if self.laston != self.nowon:
            # Wenn vorher an war (und jetzt also aus), dann nichts tun (ausser "vorher" auf aus setzen)
            # if it was on (which means that it's off now) then do nothing (except set laston to false)
            if self.laston == True:
                self.laston = False
            #                logging.debug("Button studio {} function {} pin {} not pressed any more".format(self.studio, self.function, self.pin))
            # Wenn vorher aus war (und jetzt also an), dann Code ausfuehren (und "vorher" auf an setzen)
            # if it was off (which means that it's on now) then run the code (and set laston to true)
            else:
                self.laston = True
                logging.info("Button: button {}, studio {} pressed".format(self.function, self.studio))
                logging.debug("**** pre-button - old state ****")
                logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, nexton))
                logging.debug(
                    "immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(
                        sofort, sofortgive, sofortto))
                logging.debug("ledchange: {}".format(ledchange))
                logging.debug("issuing changestate-call to see if something has to change")
                changestate(self.studio, self.function)
                savestate()
                logging.debug("**** post-button - new state ****")
                logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, nexton))
                logging.debug(
                    "immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(
                        sofort, sofortgive, sofortto))
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
        # Falls die LED nicht geblinkt hat: Einschalten
        # If LED didn't blink, turn on
        if self.blinkind == False:
            self.onind = True
            GPIO.output(self.pin, GPIO.HIGH)
            logging.debug(
                "LED-State: Now on: LED {}, Studio {}, Pin {}, on-indicator = {}".format(self.color, self.studio,
                                                                                         self.pin, self.onind))
        # Falls die LED vorher geblinkt hat: Blinken ausschalten, LED dauerhaft einschalten
        # If LED did blink: Turn blinking off, turn on LED
        else:
            self.blinkstop.set()
            self.blinkind = False
            self.onind = True
            GPIO.output(self.pin, GPIO.HIGH)
            logging.debug(
                "LED-State: Now on after blinking: LED {}, Studio {}, Pin {}, on-inidicator = {}".format(self.color,
                                                                                                         self.studio,
                                                                                                         self.pin,
                                                                                                         self.onind))

    # Blinken
    # Blink
    def blink(self):
        # Nur was machen, wenn nicht schon (langsam) blinkend
        # Only do something if not already blinking slow
        if self.blinkind != 'slow':
            if self.blinkind == 'fast':
                self.blinkstop.set()
                self.blinkind = False
            # Variable, die sagt, ob geblinkt wird
            # Variable which tells if there's blinking to do
            self.blinkind = 'slow'
            # Stopp-Signal fuer blink-Thread definieren
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
            logging.debug("LED-State: Now blinking: LED {}, Studio {}, Pin {}, blink-indicator = {}".format(self.color,
                                                                                                            self.studio,
                                                                                                            self.pin,
                                                                                                            self.blinkind))

    # Schnell blinken
    # Blink fast
    def blinkfast(self):
        # Nur was machen, wenn nicht schon schnell blinkend
        # Only do something if not already blinking fast
        if self.blinkind != 'fast':
            if self.blinkind == 'slow':
                self.blinkstop.set()
                self.blinkind = False
            # Variable, die sagt, ob geblinkt wird
            # Variable which tells if there's blinking to do
            self.blinkind = 'fast'
            # Stopp-Signal fuer blink-Thread definieren
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
            logging.debug(
                "LED-State: Now blinking fast: LED {}, Studio {}, Pin {}, blink-indicator = {}".format(self.color,
                                                                                                       self.studio,
                                                                                                       self.pin,
                                                                                                       self.blinkind))

    # Ausschalten
    # Turn off
    def off(self):
        if self.onind == True:
            GPIO.output(self.pin, GPIO.LOW)
            self.onind = False
            logging.debug(
                "LED-State: Now off: LED {}, Studio {}, Pin {}, on-indicator = {}".format(self.color, self.studio,
                                                                                          self.pin, self.onind))
        if self.blinkind != False:
            self.blinkind = False
            self.blinkstop.set()
            # Zur Sicherheit; Blinken koennte ja auch aufhoeren, wenn LED gerade an
            # To be sure that its really off and didnt stop blinking while led was on
            GPIO.output(self.pin, GPIO.LOW)
            logging.debug(
                "LED-State: Now not blinking any more: LED {}, Studio {}, Pin {}, blink-indicator = {}".format(
                    self.color, self.studio, self.pin, self.blinkind))

    # Thread fuer's Blinken definieren
    # Define Thread for blinking
    class blinkbase(threading.Thread):
        def __init__(self, pin, delay, stop_event):
            threading.Thread.__init__(self)
            self.pin = pin
            self.delay = delay
            self.stop_event = stop_event

        def run(self):
            logging.debug("LED-State: blink-thread startet")
            while not self.stop_event.is_set():
                GPIO.output(self.pin, GPIO.HIGH)
                time.sleep(self.delay)
                if self.stop_event.is_set():
                    logging.debug("LED-State: blink-thread finished by break-statement")
                    break
                GPIO.output(self.pin, GPIO.LOW)
                time.sleep(self.delay)
            logging.debug("LED-State: blink-thread finished")

    # Sehen, ob was an den LEDs geaendert werden muss
    # Check, if LEDs have to change
    def ledcheck(self):
        # die globalen Variablen muessen in die Funktion geholt werden
        # global variables have to be declared as such
        global onair, give, take, nexton, sofort, sofortgive, sofortto, ledchange
        # Fuer die gruenen LEDs
        # For the green LEDs
        if self.color == 'g':
            logging.debug("LED-Check: Lg1 - LED-color is {}, studio is {}".format(self.color, self.studio))
            # Anschalten, wenn das eigene Studio on Air ist
            # On, if own studio's on air
            if (onair == self.studio):
                logging.debug("LED-Check: Lg2 - own studio is on air, so shine!")
                self.on()
            # Schnell blinken, wenn das eigene Studio 'sofort' on Air gehen wird, sollte nur fuer Automation relevant sein
            # Blink fast, if own Studio will be on Air 'immediately', should only be relevant for automation
            elif (sofortgive == True) and (sofortto == self.studio):
                logging.debug("LED-Check: Lg4 - own studio will be on air immediately, so blink fast!")
                self.blinkfast()
            # Blinken, wenn das eigene Studio zur naechsten Stunde on Air sein wird
            # Blink, if own studio will be on air at next hour
            elif (nexton == self.studio) and (give == True):
                logging.debug("LED-Check: Lg3 - own studio will be next, other studio already released, so blink!")
                self.blink()
            # In allen anderen Faellen aus
            # Off in any other case
            else:
                logging.debug("LED-Check: Lg5 - own studio does not and wont do anything, so im off!")
                self.off()
        # Fuer die gelben LEDs
        # For the yellow LEDs
        if self.color == 'y':
            logging.debug("LED-Check: Ly1 - LED-color is {}, studio is {}".format(self.color, self.studio))
            # Blinken, wenn das eigene Studio Uebernahme angefordert hat (aber noch keine Freigabe erhalten)
            # Blink, if own studio wants to take (and other studio hasn't already pressed give)
            if (nexton == self.studio) and (give == False):
                logging.debug("LED-Check: Ly2 - own studio claimed but other studio didnt release yet, so blink!")
                self.blink()
            # Sonst aus
            # Otherwise off
            else:
                logging.debug("LED-Check: Ly3 - no unanswered claim, so im off!")
                self.off()
        # Fuer die roten LEDs
        # For the red LEDs
        if self.color == 'r':
            logging.debug("LED-Check: Lr1 - LED-color is {}, studio is {}".format(self.color, self.studio))
            # Falls das eigene Studio 'sofort' gedrueckt hat
            # If own studio has pressed 'sofort'
            if sofort == self.studio:
                logging.debug("LED-Check: Lr2 - own studio acquired immediate-state, so shine!")
                self.on()
            else:
                logging.debug("LED-Check: Lr3 - own studio didn't acquire immediate-state, so im off!")
                self.off()


# Timer definieren, der ggf. zur vollen Stunde umschaltet
# Define timer that switches at the full hour if necessary
def timecheck():
    if time.strftime('%M%S') == '0000':
        global now, then
        # gmtime, damit Zeitumstellung keine Rolle spielt
        # gmtime, so that daylight-saving-time won't do any harm
        now = time.strftime('%H%M%S', time.gmtime())
        if 'then' not in globals():
            then = '999999'
        if now != then:
            logging.info("Time-Check: the time to switch is now")
            umschalt()
            then = now


# Status-Aenderungs-Logik
# Logic to change states
def changestate(studio, function):
    studio = studio
    function = function
    # die globalen Variablen muessen in die Funktion geholt werden
    # global variables have to be declared as such
    global onair, give, take, nexton, sofort, sofortgive, sofortto, ledchange
    # Fuer Freigabe-Button
    # For release-button
    if function == 'F':
        logging.debug("Logic: F1 - release-button in studio {} pressed".format(studio))
        # Fuer das eigene Studio
        # For the own studio
        if onair == studio:
            logging.debug("Logic: F2 - own studio is on air")
            # Fuer Kombinationen mit sofort
            # For combinations with immediate
            if sofort == studio:
                logging.debug("Logic: F3 - immediate-state already acquired for own studio (not other studio)")
                # Sofort-Freigabe erteilen
                # Set immediate-release
                if sofortgive != True:
                    logging.info("Logic: F4 - immediate-release not yet triggered -> triggering immediate-release")
                    sofortgive = True
                    soforttimerstart()
                    ledchange = True
                else:
                    # Sofort-Freigabe zuruecknehmen, wenn nicht von anderem Studio schon angefordert
                    # Reset sofort-give, if no other studio claimed the signal
                    logging.debug("Logic: F5 - immediate-release has already been triggered")
                    if sofortto == '0':
                        logging.info("Logic: F5a - immediate release already set but no other studio claimed -> resetting immediate-release")
                        sofortgive = False
                        sofort = '0'
                        soforttimerstop()
                        ledchange = True
            # Normale Freigaben
            # Regular release
            else:
                logging.debug("Logic: F6 - no 'immediate' involved, we want a regular release")
                # Wenn noch nicht freigegeben: freigeben
                # If not yet set to give, set to give
                if give == False:
                    logging.info("Logic: F7 - no release triggered yet, triggering release")
                    give = True
                    ledchange = True
                # Wenn schon freigeben, dann wieder "zuruecknehmen", wenn noch kein anderes Studio will
                # If already set to give, then take back, if no other studio wants to take
                else:
                    logging.debug("Logic: F8 - release already triggered")
                    if take == False:
                        logging.info("Logic: F8a - already set release but no other studio claimed -> resetting release")
                        give = False
                        ledchange = True
        # Fuer anderes Studio; for other studio
        # Mit Freigabe die eigene Uebernahme-Anforderung zuruecksetzen
        # give to reset own wish to take
        else:
            logging.debug("Logic: F10 - other studio is on air")
            if (take == True) and (nexton == studio):
                logging.info("Logic: F11 - did already claim -> resetting claim")
                take = False
                nexton = '0'
                ledchange = True
    # Fuer Uebernahme-Button
    # For Claim-Button
    if function == 'U':
        logging.debug("Logic: U1 - claim-button in studio {} pressed".format(studio))
        # Fuer Kombinationen mit sofort
        # For combinations with immediate
        if sofort != '0':
            logging.debug("Logic: U2 - immediate-state already pressed")
            # Sofort uebernehmen von Automat
            # Switch immediately from automation
            if (onair == '0') and (sofort == studio):
                logging.info(
                    "Logic: U3 - automations on air, immediate-state already acquired for own studio -> switching to own studio immediately")
                sofortto = studio
                umschaltsofort()
                ledchange = True
            # Sofort uebernehmen von anderem Studio
            # Switch immediately from other studio
            if (sofort != studio) and (sofortgive == True):
                logging.info(
                    "Logic: U4 - other studio on air which issued immediate release -> switching to own studio immediately")
                sofortto = studio
                soforttimerstop()
                umschaltsofort()
                ledchange = True
            # Reset bei eigener Sofort-Uebergabe
            # Reset own immediate-release
            if (sofort == studio) and (sofortgive == True):
                logging.info(
                    "Logic: U5 - own studio on air, immediate-release already triggered -> resetting immediate-release")
                sofort = '0'
                sofortgive = False
                soforttimerstop()
                ledchange = True
        # Normale Uebernahmen
        # Regular claim
        else:
            logging.debug("Logic: U6 - no 'immediate' involved - regular claim")
            # Fuer das eigene Studio (-> Reset) und nur falls noch keine andere Uebernahme-Anforderung
            # For own studio (-> reset) and only if no other studio already wants to take
            if (onair == studio) and (give == True) and (take == False):
                logging.info(
                    "Logic: U7 - own studios on air, already issued release but no other studio claimed -> resettig release")
                give = False
                ledchange = True
            # Uebernahme von anderem Studio
            # Take from other Studio
            if onair != studio:
                logging.debug("Logic: U8 - other studio on air")
                # Noch keine andere Uebernahme-Anforderung
                # No other studio wants to take yet
                if take == False:
                    logging.info("Logic: U9 - no other studio claimed yet -> claiming for own studio")
                    take = True
                    nexton = studio
                    ledchange = True
                # Es gibt schon eine eigene Uebernahme-Anforderung -> Reset
                # The own studio already wanted to take -> Reset
                else:
                    logging.debug("Logic: U10 - some studio already claimed")
                    if nexton == studio:
                        logging.info("Logic: U11 - own studio already claimed -> resetting claim")
                        take = False
                        nexton = '0'
                        ledchange = True
    # Fuer Sofort-Button
    # For "immediate"-Button
    if function == 'S':
        logging.debug("Logic: S1 - immediate-button in studio {} pressed".format(studio))
        # Wenn das eigene Studio oder die Automation on Air ist
        # If own studio or automation is on air
        if (onair == '0') or (onair == studio):
            logging.debug("Logic: S2 - automation or own studio is on air")
            # Wenn sofort noch nicht aktiviert, fuer das eigene Studio aktivieren
            # If sofort isn't alredy activated, activate it for own studio
            if sofort == '0':
                logging.info("Logic: S3 - no other studio set immediate-state yet -> setting immediate-state for own studio")
                sofort = studio
                ledchange = True
            # Reset, wenn es schon das eigene Studio ist
            # Reset, if it's already own studio
            elif (sofort == studio) and (sofortto == '0'):
                logging.info("Logic: S4 - own studio had set immediate-state -> resetting immediate-state")
                sofort = '0'
                if sofortgive == True:
                    logging.info("Logic: S5 - own studio had already issued immediate-release -> taking that back too")
                    sofortgive = False
                    soforttimerstop()
                ledchange = True


# Umschalt-Logik definieren
# Wird aufgerufen von timecheck oder von umschaltsofort
# Define what's going to happen when it's time to switch
# Is called by timecheck or by umschaltsofort
def umschalt():
    # die globalen Variablen muessen in die Funktion geholt werden
    # global variables have to be declared as such
    global onair, give, take, nexton, sofort, sofortgive, sofortto, ledchange
    logging.info("++++++ switching now (if neccesary) ++++++")
    logging.debug("**** pre-switch - old state ****")
    logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, nexton))
    logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort,
                                                                                                                sofortgive,
                                                                                                                sofortto))
    logging.debug("ledchange: {}".format(ledchange))
    # Es muss nur was getan werden, wenn auch Freigegeben wurde
    # Switch only if "give" was set
    if give == True:
        logging.debug("Switch: release issued")
        if take == True:
            logging.debug("Swith: claim issued, too")
            umschaltsignal(nexton)
            logging.info("Switch: switching {} -> {}".format(onair, nexton))
            onair = nexton
            give = False
            take = False
            nexton = '0'
        else:
            logging.debug("Switch: no claim issued")
            if onair != '0':
                logging.debug("Switch: but i dont want to be on air any more, so well switch to automation")
                umschaltsignal('0')
                logging.info("Switch: switching {} -> {}".format(onair, nexton))
                onair = '0'
                give = True
        ledchange = True
        sofort = '0'
        sofortgive = False
        sofortto = '0'
    logging.debug("**** post-switch - new state ****")
    logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, nexton))
    logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort,
                                                                                                                sofortgive,
                                                                                                                sofortto))
    logging.debug("ledchange: {}".format(ledchange))


# Sofort-Umschalt-Logik definieren: sofort-Stati werden in normale Stati uebersetzt und der normale Umschalt-Vorgang gestartet
# Wird aufgerufen von verschiedenen Knopf-Druck-Events oder am Ende des Sofort-Timers
# define immediate-switch-logik: will translate immediate-states to regular states and call regular switch process
# Is called by some button-press-events and at end of sofort-countdown
def umschaltsofort():
    # die globalen Variablen muessen in die Funktion geholt werden
    # global variables have to be declared as such
    global onair, give, take, nexton, sofort, sofortgive, sofortto, ledchange
    logging.info("++++++ immediate switch happening ++++++")
    logging.debug("**** pre-immediate - old state ****")
    logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, nexton))
    logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort,
                                                                                                                sofortgive,
                                                                                                                sofortto))
    logging.debug("ledchange: {}".format(ledchange))
    logging.debug("Sofort-switch: setting variables")
    give = True
    if sofortto == '0':
        take = False
    else:
        take = True
    nexton = sofortto
    sofort = '0'
    sofortgive = False
    sofortto = '0'
    logging.debug("**** post-immediate - new state ****")
    logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, nexton))
    logging.debug("immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort,
                                                                                                                sofortgive,
                                                                                                                sofortto))
    logging.debug("ledchange: {}".format(ledchange))
    logging.debug("Sofort-switch: calling regular switch")
    umschalt()



# Sofort-Umschalt-Timer starten
# Start timer for immediate-switch	
def soforttimerstart():
    global sofortcountdown
    sofortcountdown = threading.Timer(30, umschaltsofort)
    sofortcountdown.daemon = True
    sofortcountdown.start()
    logging.debug("Sofort: sofort-countdown-thread started")


# Abbruch Sofort-Umschalt-Timer
# Cancel timer for immediate-switch
def soforttimerstop():
    global sofortcountdown
    sofortcountdown.cancel()
    logging.debug("Sofort: sofort-countdown-thread canceled")



# Umschalt-Signal fuer den Audio-Router definieren
# Define the signal that is sent to the audio-router
def umschaltsignal(switchto):
    # !!!!! muss noch definiert werden
    # !!!!! to be defined
    logging.info("Signal: telling audio routing-machine what has to be on air next")
    pass


# Aktuellen Zustand in Datei schreiben
# Save state to file
def savestate():
    statesave = open("statesave.txt", "w")
    timeend = time.strftime('%Y%m%d%H')
    statesave.write("{};{};{};{};{};".format(timeend, str(onair), give, take, str(nexton)))
    statesave.close()


# Bei Programmende
# If programme is terminated
def end(signal, frame):
    logging.info("End: programme terminated by signal: {}, cleaning up and exiting.".format(signal))
    savestate()
    GPIO.cleanup()
    raise SystemExit


# Signal-Verarbeiten
# How to handle signals
signal.signal(signal.SIGHUP, end)
signal.signal(signal.SIGTERM, end)
signal.signal(signal.SIGINT, end)

logging.info("Main: starting programm")
logging.info("Main: setting variables")
setstate()
logging.info("Main: setting up buttons")
# Buttons anlegen; make buttons
B1F = Button(33, '1', 'F')
B1U = Button(35, '1', 'U')
B1S = Button(37, '1', 'S')
B2F = Button(36, '2', 'F')
B2U = Button(38, '2', 'U')
B2S = Button(40, '2', 'S')

logging.info("Main: setting up leds")
# LEDs anlegen; make LEDs
L1G = LED(7, '1', 'g')
L1Y = LED(11, '1', 'y')
L1R = LED(29, '1', 'r')
L2G = LED(13, '2', 'g')
L2Y = LED(15, '2', 'y')
L2R = LED(31, '2', 'r')
L3G = LED(19, '3', 'g')
L3Y = LED(21, '3', 'y')
L0G = LED(23, '0', 'g')


def shinebright(timeshine):
    for L in [L1G, L1Y, L1R, L2G, L2Y, L2R, L3G, L3Y, L0G]:
        L.on()
    time.sleep(timeshine)
    for L in [L1G, L1Y, L1R, L2G, L2Y, L2R, L3G, L3Y, L0G]:
        L.off()

shinebright(1)


logging.debug("++++++ initial states ++++++")
logging.debug("on air: {}, release: {}, claim: {}, on air next: {}".format(onair, give, take, nexton))
logging.debug(
    "immediate-state called by studio: {}, immediate-release: {}, immediate switch to: {}".format(sofort, sofortgive,
                                                                                                  sofortto))
logging.debug("ledchange: {}".format(ledchange))

logging.info("Main: starting main process")
while True:
    timecheck()
    for B in [B1F, B1U, B1S, B2F, B2U, B2S]:
        B.buttoncheck()
        if ledchange == True:
            logging.debug("LEDs: checking and setting led-states")
            for L in [L1G, L1Y, L1R, L2G, L2Y, L2R, L3G, L3Y, L0G]:
                L.ledcheck()
            ledchange = False
    time.sleep(0.05)
