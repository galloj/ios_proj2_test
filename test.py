#!/usr/bin/python3
import subprocess
from colorama import Fore
from os.path import exists
import os
import sys

allPassed = True

testCnt = 0
failedCnt = 0
testFailed = False
testRunning = False
showOut = False
lineError = False

def err(text):
	global lineError
	global allPassed
	global testFailed
	testFailed = True
	allPassed = False
	lineError = True
	print("[" + Fore.RED + "ERR" + Fore.WHITE + "] " + text)

def note(text):
	print("[ " + Fore.CYAN + "*" + Fore.WHITE + " ] " + text)

def succ(text):
	print("[" + Fore.GREEN + "OK" + Fore.WHITE + " ] " + text);

def test(text):
	global testFailed
	global testCnt
	global testRunning
	testEnd()
	testFailed = False
	testRunning = True
	testCnt+=1
	print("[ " + Fore.BLUE + "T" + Fore.WHITE + " ] " + "Test for: " + text)
	preclean()

def testEnd():
	global testFailed
	global testRunning
	global failedCnt
	if testRunning:
		if testFailed:
			err("Test failed")
			failedCnt += 1
		else:
			succ("Test passed")
	testRunning = False
	testFailed = False

for x in sys.argv[1:]:
	if x=="--show-out":
		showOut = True
	else:
		err(f"Unknown argument {x}")


note("Test script has started")

if not exists("./proj2") and not exists("./Makefile"):
	err("Script has to be in same directory as ./proj2 or ./Makefile")
	exit(1)

def preclean():
	os.system("pkill proj2")
	os.system("rm proj2.out 2>/dev/null")

def postclean():
	if "proj2" in subprocess.check_output(["ps"]).decode("utf-8"):
		err("Proj2 is still running after process exited (unterminated childs)")
		os.system("pkill proj2")
		note("Proj2 is killed automatically now")

def processFail(params):
	proc = subprocess.Popen(["./proj2"] + params, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
	try:
		outs, errs = proc.communicate(timeout=5)
		if outs != "":
			err("There shouldnt be any text on stdout")
		if errs.strip() == "":
			err("Missing error output on stderr")
	except subprocess.TimeoutExpired:
		proc.kill()
		err("Process timed out")
		postclean()
		return
	proc.wait()
	postclean()
	if proc.returncode != 1:
		err("Wrong return code, should be set to 1")

def processSucess(NO, NH, TI, TB):
	proc = subprocess.Popen(["./proj2", str(NO), str(NH), str(TI), str(TB)], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
	try:
		outs, errs = proc.communicate(timeout=5)
		if outs != "":
			err("There shouldnt be any text on stdout")
		if errs != "":
			err("There shouldnt be any errors on stderr")
	except subprocess.TimeoutExpired:
		proc.kill()
		err("Process timed out")
		postclean()
		return
	wrongLines = []
	if not exists("proj2.out"):
		err("Missing file proj2.out")
	else:
		dataFile = open("proj2.out")
		lineCnt = 0
		moleculeCnt = 0
		creatingMolecule = False
		moleculeCreated = False
		moleculeO = [] # list of current oxygens in molecule
		moleculeH = [] # list of current hydrogens in molecule
		oarr = [0]*NO
		harr = [0]*NH
		for line in dataFile.readlines():
			lineCnt += 1
			global lineError
			lineError = False
			line = line.strip()
			fields = line.split(": ")
			if len(fields) != 3:
				err("Wrong format of line (expected \"xxx: xxx: xxx\") got:")
				break
			if fields[0] != str(lineCnt):
				err(f"Wrong id of line, expected {lineCnt}")
				break
			if len(fields[1].split(" ")) != 2:
				err(f"Expected atom type and id (ex. \"H 1\") got \"{fields[1]}\"")
				note("Line: " + line)
				break
			type, id = fields[1].split(" ")
			arr=None
			if type == "O":
				arr = oarr
			elif type == "H":
				arr = harr
			else:
				err(f"Unknown atom type \"{type}\" (expected \"O\" or \"H\")")
				continue
			if int(id)>len(arr):
				err(f"Too big id of atom (max is {len(arr)}, found {int(id)})")
				continue
			if int(id)<0:
				err(f"Too small id of atom (min is 0, found {int(id)})")
				continue
			cmd = fields[2].split(" ")[0]
			id = int(id)-1
			if cmd == "started":
				if fields[2] != "started":
					err("Text should be \"started\", found \"{fields[2]}\"")
				if arr[id] != 0:
					err("Starting atom which was already started")
					continue
				arr[id] = 1
			elif cmd == "going":
				if fields[2] != "going to queue":
					err(f"text should be \"going to queue\", found \"{fields[2]}\"")
				if arr[id] < 1:
					err("Trying to put atom into queue, which wasn't started")
					continue
				if arr[id]>1:
					err("Trying to put atom into queue, which was already in queue")
					continue
				arr[id] = 2
			elif cmd == "creating":
				if arr[id] < 2:
					err("Trying to create molecule with atom, which wasn't in queue")
					continue
				if arr[id] > 2:
					err("Trying to create molecule with atom, which was already used to create molecle")
					continue
				if not creatingMolecule:
					creatingMolecule = True
					moleculeCnt += 1
				if fields[2] != f"creating molecule {moleculeCnt}":
					err(f"Text should be \"creating molecule {moleculeCnt}\", found \"{fields[2]}\"")
				if moleculeCreated:
					err("Trying to join molecule when molecule was already created")
				if type == "O":
					moleculeO.append(id)
					if len(moleculeO) > 1:
						err("Too much of oxygens is trying to create same molecule")
				else:
					moleculeH.append(id)
					if len(moleculeH) > 2:
						err("Too much of hydrogens is trying to create same molecule")
				if len(moleculeO) == 1 and len(moleculeH) == 2:
					moleculeCreated = True
				arr[id] = 3
			elif cmd == "molecule":
				if arr[id] < 3:
					err("Trying to finnish creation of molecule which hasn't yet started")
					continue
				if arr[id] > 3:
					err("Trying to finnish creation of molecule which was already created")
					continue
				if fields[2] != f"molecule {moleculeCnt} created":
					err(f"Text should be \"molecule {moleculeCnt} created\", found \"{fields[2]}\"")
				if type == "O":
					if id not in moleculeO:
						err("Atom is trying to finnish creating of molecule which it isn't inside of")
					else:
						moleculeO.remove(id)
				else:
					if id not in moleculeH:
						err("Atom is trying to finnish creating of molecule which it isn't inside of")
					else:
						moleculeH.remove(id)
				if not moleculeCreated:
					err("Trying to finnish creating of molecule, before all atoms started creating molecule")
				if len(moleculeO) == 0 and len(moleculeH) == 0:
					moleculeCreated = False
					creatingMolecule = False
				arr[id] = 4
			elif cmd == "not":
				if type == "O":
					if fields[2] != "not enough H":
						err("Text should be \"not enough H\", found \"{fields[2]}\"")
				else:
					if fields[2] != "not enough O or H":
						err("Text should be \"not enough O or H\", found \"{fields[2]}\"")
				if arr[id] < 2:
					err("Atom needs to be in queue before figuring out it can't make molecule")
					continue
				if arr[id] > 2:
					err("Atom failed making molecule after it started")
					continue
				arr[id] = 4
			else:
				err("Unknown action of atom")
			if lineError:
				lineError = False
				note("Line: " + line)
				wrongLines.append(lineCnt)
		expectedMoleculeCnt = min(NO, NH//2)
		if moleculeCnt != expectedMoleculeCnt:
			err(f"Wrong amount of molecules created: found {moleculeCnt}, expected {expectedMoleculeCnt}")
		faults = ["wasn't started", "didn't went to queue", "didn't attempted to create molecule", "didn't finnished forming of molecule"]
		for i, x in enumerate(oarr):
			if x<4:
				err(f"Oxygen {i+1} {faults[x]}")
		for i, x in enumerate(harr):
			if x<4:
				err(f"Hydrogen {i+1} {faults[x]}")
		dataFile.close()
	proc.wait()
	if proc.returncode != 0:
		err("Wrong return code, should be set to 0")
	if showOut and testFailed:
			note("Printing ./proj2.out to terminal:")
			if exists("./proj2.out"):
				with open('./proj2.out', 'r') as f:
					for i, line in enumerate(f.readlines()):
						if i+1 in wrongLines:
							print(end=Fore.RED)
						print(end=line)
						print(end=Fore.WHITE)
			else:
				err("File ./proj2.out doesn't exists")
	postclean()

test("Makefile")
if not exists("./Makefile"):
	err("Makefile doesn't exists")
else:
	note("Automatically running make")
	if os.system("make"):
		err("Error while executing make")

note("Following tests expect program to fail")

test("No arguments")
processFail([])
test("Two arguments")
processFail(["1", "2"])
test("Three arguments")
processFail(["1", "2", "3"])
test("Five arguments")
processFail(["1", "2", "3", "4", "5"])


test("Negative NO")
processFail(["-1", "1", "1", "1"])
test("NO not a number")
processFail(["1a", "1", "1", "1"])
test("Missing NO")
processFail(["", "1", "1", "1"])

test("Negative NH")
processFail(["1", "-1", "1", "1"])
test("NH not a number")
processFail(["1", "1a", "1", "1"])
test("Missing NH")
processFail(["1", "", "1", "1"])

test("Negative TI")
processFail(["1", "1", "-1", "1"])
test("Too big TI")
processFail(["1", "1", "1001", "1"])
test("TI not a number")
processFail(["1", "1", "1a", "1"])
test("Missing TI")
processFail(["1", "1", "", "1"])

test("Negative TB")
processFail(["1", "1", "1", "-1"])
test("Too big TB")
processFail(["1", "1", "1", "1001"])
test("TB not a number")
processFail(["1", "1", "1", "1a"])
test("Missing TB")
processFail(["1", "1", "1", ""])


note("Following tests expect program to succeed")

test("No atoms (0, 0, 100, 100)")
processSucess(0, 0, 100, 100)

test("Not enough of atoms for molecule (1, 1, 100, 100)")
processSucess(1, 1, 100, 100)

test("Creating one molecule (1, 2, 100, 100)")
processSucess(1, 2, 100, 100)

test("Test from assigment (3, 5, 100, 100)")
processSucess(3, 5, 100, 100)

test("Stress test (100, 100, 100, 100)")
processSucess(100, 100, 100, 100)

testEnd()
note("Test script has finnished")
note(f"Total of {testCnt} tests were run, {failedCnt} failed")

if allPassed:
	print(Fore.GREEN + "All tests have passed!!! :)" + Fore.WHITE)
else:
	if not showOut:
		note("You can try running the script as ./test.py --show-out to show ./proj2.out on failed tests")
	print(Fore.RED + "Some tests have failed :(" + Fore.WHITE)
