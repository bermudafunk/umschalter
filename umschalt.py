
# Notwendige Bibliotheken importieren
# import necessary libraries
import time
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

# Was ist auf Sendung? What's on air? 1 = Studio 1; 2 = Studio 2; 3 = Aussenstudio/ other studio; 9 = Automation
onair = '9'
# Freigabe erteilt? Already give away signal? (Standard ist False, aber bei Automation True; Standard's False, but True with automation)
give = True
# Uebernahme angefordert? Any studio already wants signal?
take = False
# Was wird geschehen? What's going to happen? 1 = Freigabe/ want to give; 2 = Uebernahme/ want to take; 3 = Uebergabe/ will switch; 9 = Sofort-Uebergabe/ will switch immediately
#dowhat = 0
# Was wird als naechstes auf Sendung sein? What will be on air next? 1 = Studio 1; 2 = Studio 2; 3 = Aussenstudio/ other Studio; 0 = Automation
next = '0'
# Welches Studio hat "Sofort"-Button gedrueckt? Which studio hast pressed the "immediate"-button? 0 = keins/none; 1 = Studio 1; 2 = Studio 2; 3 = Aussenstudio/ other Studio 
sofort = '0'

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
	global onair, give, take, next, sofort
	# Fuer Freigabe-Button
	# For "Give"-Button
	if self.function == 'F':
	    # Fuer das eigene Studio
	    # For the own studio
	    if onair == self.studio:
		# Wenn noch nicht freigegeben: freigeben
		# If not yet set to give, set to give
		if give == False:
		    give = True
		# Wenn schon freigeben, dann wieder "zuruecknehmen", wenn noch kein anderes Studio will
		# If already set to give, then take back, if no other studio wants to take
		else:
		    if take == False:
			give = False
	    # Fuer anderes Studio; for other studio
	    # Mit Freigabe die eigene Uebernahme-Anforderung zuruecksetzen
	    # give to reset own wish to take
	    else:
		if (take == True) and (next == self.studio):
		    take = False
		    next = 0
	# Fuer Uebernahme-Button
	# For "Take"-Button
	if self.function == 'U':
	    # Fuer das eigene Studio (-> Reset) und nur falls noch keine andere Uebernahme-Anforderung
	    # For own studio (-> reset) and only if no other studio already wants to take
	    if (onair == self.studio) and (give == True) and (take == False):
		give = False 
	    # Uebernahme von anderem Studio
	    # Take from other Studio
	    if onair != self.studio:
		# Noch keine andere Uebernahme-Anforderung
		# No other studio want's to take yet
		if take == False:
		    take = True
		    next = self.studio
		# Es gibt schon eine eigene Uebernahme-Anforderung -> Reset
		# The own studio already wanted to take -> Reset
		else:
		    if next == self.studio:
			take = False
			next = 0
	# Fuer Sofort-Button
	# For "immediate"-Button
	if self.function == 'S':
	    # Wenn das eigene Studio oder die Automation on Air ist
	    # If own studio or automation is on air
	    if onair == '9' or self.studio:
		sofort = self.studio
	    # Sofort-Reset; reset "immediate"-State
	    if sofort == self.studio:
		sofort = 0
    # Abfrage des Buttons und ggf. Aenderung des Status
    # check button and change state if neccesary
    def check(self):
	# wird nur fuer die print-funktionen gebraucht, kann spaeter also wieder weg!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	global onair, give, take, next, sofort
        # In Variable schreiben, wenn Button gedrueckt (also Strom kommt am Pin an)
        # write to variable if button is pressed (theres electricity at the pin)
        if GPIO.input(self.pin) == GPIO.HIGH:
            self.nowon = True
	    print 'Button {}{}, pin {} pressed'.format(self.studio, self.function, self.pin)
        else:
            self.nowon = False
        # Pruefen, ob sich etwas gegenueber letzter Abfrage geaendert hat
        # see if state has changed since last check
        if self.laston != self.nowon:
            # Wenn vorher an war (und jetzt also aus), dann nichts tun (ausser "vorher" auf aus setzen)
            # if it was on (which means that it's off now) then do nothing (except set laston to false)
            if self.laston == True:
                self.laston = False
		print 'Button studio {} function {} pin {} not pressed any more'.format(self.studio, self.function, self.pin)
            # Wenn vorher aus war (und jetzt also an), dann Code ausfuehren (und "vorher" auf an setzen)
            # if it was off (which means that it's on now) then run the code (and set laston to true)
            else:
                self.laston = True
		print 'Noticed: Button studio {} function {} pin {} newly pressed'.format(self.studio, self.function, self.pin)
		print "On air:", onair, "Freigabe:", give, "Uebernahme:", take, "Als naechstes:", next, "Sofort gedrueckt:", sofort
                self.changestate()
		print "On air:", onair, "Freigabe:", give, "Uebernahme:", take, "Als naechstes:", next, "Sofort gedrueckt:", sofort
		change = True



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

print "On air:", onair, "Freigabe:", give, "Uebernahme:", take, "Als naechstes:", next, "Sofort gedrueckt:", sofort

print 'Lets listen to the buttons'
while True:
    for B in [B1F, B1U, B1S, B2F, B2U, B2S]: 
	B.check()
    time.sleep(0.1)





#class LED(object):
#    def __init__(self):
#	self.pin =
#	self.on = False
#	self.blink = False


#class Signal:
#	pass
