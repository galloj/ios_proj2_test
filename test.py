#!/usr/bin/python3
import subprocess
from colorama import Fore
from os.path import exists
import os
import sys

timeout = 10
timeouted = False

allPassed = True

testCnt = 0
failedCnt = 0
testFailed = False
testRunning = False
showOut = False
lineError = False
isTestError = False
testErrorCount = 0

maxTestErrorCount = 15

def err(text):
	global lineError
	global allPassed
	global testFailed
	global testErrorCount
	testFailed = True
	allPassed = False
	lineError = True
	if not isTestError or testErrorCount < maxTestErrorCount:
		print("[" + Fore.RED + "ERR" + Fore.WHITE + "] " + text)
	if isTestError:
		if testErrorCount == maxTestErrorCount:
			note("Reached maximum number of errors to display, showing no more")
		testErrorCount += 1

def note(text,ignorable=False):
	if not ignorable or not isTestError or testErrorCount < maxTestErrorCount:
		print("[ " + Fore.CYAN + "*" + Fore.WHITE + " ] " + text)

def succ(text):
	print("[" + Fore.GREEN + "OK" + Fore.WHITE + " ] " + text);

def test(text):
	global testFailed
	global testCnt
	global testRunning
	global isTestError
	global testErrorCount
	testErrorCount = 0
	testEnd()
	isTestError = False
	testFailed = False
	testRunning = True
	testCnt+=1
	print("[ " + Fore.BLUE + "T" + Fore.WHITE + " ] " + "Test for: " + text)
	preclean()

def testEnd():
	global testFailed
	global testRunning
	global failedCnt
	global isTestError
	isTestError = False
	if testRunning:
		if testFailed:
			err("Test failed")
			failedCnt += 1
		else:
			succ("Test passed")
	testRunning = False
	testFailed = False

useStrace=1

argvInd = 1
while argvInd < len(sys.argv):
	x = sys.argv[argvInd]
	if x=="--show-out":
		showOut = True
	elif x=="--timeout":
		argvInd+=1
		timeout = int(sys.argv[argvInd])
	elif x=="--no-strace":
		useStrace = 0
	else:
		err(f"Unknown argument {x}")
	argvInd+=1


note("Test script has started")

pkillSwitch = ""

if os.system("which id >/dev/null") != 0:
	note("Missing id command, test might try to kill processes from other users")
else:
	uid = int(os.popen("id -u").read())
	pkillSwitch = f"-U {uid}"

if os.system("which strace >/dev/null") != 0:
	err("Program strace is recommended dependency, please install it using \"sudo apt install strace\"")
	useStrace = 0

if not exists("./proj2") and not exists("./Makefile"):
	err("Script has to be in same directory as ./proj2 or ./Makefile")
	exit(1)

def preclean():
	os.system(f"pkill {pkillSwitch} proj2")
	os.system("rm proj2.out 2>/dev/null")
	os.system("rm proj2.out.strace 2>/dev/null")

def postclean():
	if "proj2" in subprocess.check_output(["ps"]).decode("utf-8"):
		err("Proj2 is still running after process exited (unterminated childs)")
		os.system(f"pkill {pkillSwitch} proj2")
		note("Proj2 is killed automatically now")
	os.popen("""ipcs -ts | grep "$(whoami)" 2>/dev/null | awk '{print $1};' 2>/dev/null | xargs -L1 ipcrm -s 2>/dev/null""").read()
	os.popen("""find /dev/shm -user "$(whoami)" -delete 2>/dev/null""").read()
	os.popen("""find /dev/shm/* -user "$(whoami)" -delete 2>/dev/null""").read()
	os.popen("""ipcs -tm | grep "$(whoami)" 2>/dev/null | awk '{print $1};' 2>/dev/null | xargs -L1 ipcrm -m 2>/dev/null""").read()

def processFail(params):
	proc = subprocess.Popen(["./proj2"] + params, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
	try:
		outs, errs = proc.communicate(timeout=timeout)
		if outs != "":
			err("There shouldnt be any text on stdout")
		if errs.strip() == "":
			err("Missing error output on stderr")
	except subprocess.TimeoutExpired:
		global timeouted
		timeouted=True
		proc.kill()
		err("Process timed out")
		postclean()
		return
	proc.wait()
	postclean()
	if proc.returncode != 1:
		err("Wrong return code, should be set to 1")

def processSucess(NO, NH, TI, TB):
	expectedMoleculeCnt = min(NO, NH//2)
	proc = subprocess.Popen(["strace", "-f", "-o", "proj2.out.strace"]*useStrace + ["./proj2", str(NO), str(NH), str(TI), str(TB)], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
	try:
		outs, errs = proc.communicate(timeout=timeout)
		if outs != "":
			err("There shouldnt be any text on stdout")
		if errs != "":
			err("There shouldnt be any errors on stderr")
	except subprocess.TimeoutExpired:
		global timeouted
		timeouted=True
		proc.kill()
		err("Process timed out")
		if showOut:
			note("Printing output file before process was killed")
			print(open("proj2.out").read())
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
		omol = [0]*NO
		hmol = [0]*NH
		atomsUsed = 0
		global lineError
		lineError = False
		for line in dataFile.readlines():
			prevLine=line
			lineCnt += 1
			if lineError:
				note("Line: " + prevLine, True)
				wrongLines.append(lineCnt-1)
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
				atomsUsed += 1
				if atomsUsed % 3 == 1:
					moleculeCnt += 1
				if not creatingMolecule:
					creatingMolecule = True
				if fields[2] != f"creating molecule {moleculeCnt}":
					err(f"Text should be \"creating molecule {moleculeCnt}\", found \"{fields[2]}\"")
				if moleculeCreated:
					err("Trying to join molecule when molecule was already created")
				if type == "O":
					omol[id] = moleculeCnt
					moleculeO.append(id)
					if len(moleculeO) > 1:
						err("Too much of oxygens is trying to create same molecule")
				else:
					hmol[id] = moleculeCnt
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
				emid = -1
				if type == "O":
					emid = omol[id]
				else:
					emid = hmol[id]
				if fields[2] != f"molecule {emid} created":
					err(f"Text should be \"molecule {emid} created\", found \"{fields[2]}\"")
				if type == "O":
					if id in moleculeO:
						if not moleculeCreated:
							err("Not all atoms joined molecule before \"molecule created\" messages started appearing")
						else:
							moleculeO = []
							moleculeH = []
				else:
					if id in moleculeH:
						if not moleculeCreated:
							err("Not all atoms joined molecule before \"molecule created\" messages started appearing")
						else:
							moleculeO = []
							moleculeH = []
				if len(moleculeO) == 0 and len(moleculeH) == 0:
					moleculeCreated = False
					creatingMolecule = False
				arr[id] = 4
			elif cmd == "not":
				if type == "O":
					if fields[2] != "not enough H":
						err(f"Text should be \"not enough H\", found \"{fields[2]}\"")
				else:
					if fields[2] != "not enough O or H":
						err(f"Text should be \"not enough O or H\", found \"{fields[2]}\"")
				if arr[id] < 2:
					err("Atom needs to be in queue before figuring out it can't make molecule")
					continue
				if arr[id] > 2:
					err("Atom failed making molecule after it started")
					continue
				if moleculeCnt != expectedMoleculeCnt:
					err("Atoms shouldn't report not enough of other atoms, before all molecules are created")
				arr[id] = 4
			else:
				err("Unknown action of atom")
			if lineError:
				lineError = False
				note("Line: " + line, True)
				wrongLines.append(lineCnt)
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

	if not exists("proj2.out.strace"):
		if useStrace:
			note("Missing file proj2.out.strace - not performing strace checks")
	else:
		dataFile = open("proj2.out.strace")
		forks = 0
		sleeps = 0
		sleepTimes = []
		for line in dataFile.readlines():
			if "clone" in line and "resumed" not in line:
				forks += 1
			if "nanosleep" in line and "resumed" not in line:
				sleeps += 1
			if "nanosleep" in line and "tv_nsec=" in line:
				sleepTimes.append(int(line.split("tv_nsec=")[1].split("}")[0]))
		if forks != NO+NH:
			err(f"Wrong amount of forks: expected {NO+NH}, found {forks}")
		if sleeps != NO+NH+expectedMoleculeCnt:
			err(f"Wrong amount of sleeps: expected {NO+NH+expectedMoleculeCnt}, found {sleeps}")
		if any(x%1000000 != 0 for x in sleepTimes):
			err("Sleeps should be in miliseconds, but found some in microseconds")
		if len(sleepTimes) > 10 and min(TI, TB) > 40:
			maxNoRand = max([sleepTimes.count(x), x] for x in {*sleepTimes})
			if maxNoRand[0] > len(sleepTimes)/3:
				err(f"Low entropy of randomnes found: {maxNoRand[0]} of {len(sleepTimes)} sleeps had value {maxNoRand[1]//1000}us")
		if any(x//1000000>max(TI, TB) for x in sleepTimes):
			err("Found longer length of sleep than value of TI and TB")
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

test("No atoms (0, 0, 100, 100)")
processFail(["0", "0", "100", "100"])

note("Following tests expect program to succeed")

test("Not enough of atoms for molecule (1, 1, 100, 100)")
processSucess(1, 1, 100, 100)

test("Creating one molecule (1, 2, 100, 100)")
processSucess(1, 2, 100, 100)

test("Maximal sleep (1, 2, 1000, 1000)")
processSucess(1, 2, 1000, 1000)

test("Minimal sleep (1, 2, 0, 0)")
processSucess(1, 2, 0, 0)

test("Test from assigment (3, 5, 100, 100)")
processSucess(3, 5, 100, 100)

test("One additional hydrogen and oxygen (2, 3, 0, 0)")
processSucess(2, 3, 0, 0)

test("Stress test 1 (100, 100, 30, 30)")
processSucess(100, 100, 30, 30)

test("Stress test 2 (150, 50, 30, 30)")
processSucess(150, 50, 30, 30)

test("Stress test 3 (50, 150, 30, 30)")
processSucess(50, 150, 30, 30)

test("Stress test 4 (100, 101, 0, 0)")
processSucess(100, 101, 0, 0)

test("Stress test 5 (1000, 1001, 0, 0)")
processSucess(100, 101, 0, 0)


testEnd()
note("Test script has finnished")
note(f"Total of {testCnt} tests were run, {failedCnt} failed")

if allPassed:
	print(Fore.GREEN + "All tests have passed!!! :)" + Fore.WHITE)
else:
	if timeouted:
		note("You can try running the script as ./test.py --timeout 999 to increase timeout of process (value in seconds)")
	if not showOut:
		note("You can try running the script as ./test.py --show-out to show ./proj2.out on failed tests")
	print(Fore.RED + "Some tests have failed :(" + Fore.WHITE)
