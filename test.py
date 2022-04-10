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

def err(text):

	global allPassed
	global testFailed
	testFailed = True
	allPassed = False
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
		if showOut and testFailed:
			note("Printing ./proj2.out to terminal:")
			if exists("./proj2.out"):
				with open('./proj2.out', 'r') as f:
					print(f.read())
			else:
				err("File ./proj2.out doesn't exists")
	testRunning = False
	testFailed = False

for x in sys.argv[1:]:
	if x=="--show-out":
		showOut = True
	else:
		err(f"Unknown argument {x}")


note("Test script has started")

if not exists("./proj2"):
	err("Script has to be in same directory as ./proj2")
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
	if not exists("proj2.out"):
		err("Missing file proj2.out")
	else:
		dataFile = open("proj2.out")
		lineCnt = 0
		moleculeCnt = 0
		oarr = [0]*NO
		harr = [0]*NH
		for line in dataFile.readlines():
			line = line.strip()
			fields = line.split(": ")
			if len(fields) != 3:
				err("Wrong format of line (expected \"xxx: xxx: xxx\") got:")
				note(line)
				break
			lineCnt += 1
			if fields[0] != str(lineCnt):
				err(f"Wrong id of line, expected {lineCnt}")
				note("Line: " + line)
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
				note("Line: " + line)
				continue
			if int(id)>len(arr):
				err(f"Too big id of atom (max is {len(arr)}, found {int(id)})")
				note("Line: " + line)
				continue
			cmd = fields[2].split(" ")[0]
			id = int(id)-1
			if cmd == "started":
				if fields[2] != "started":
					err("Text should be \"started\", found \"{fields[2]}\"")
					note("Line: " + line)
				if arr[id] != 0:
					err("Starting atom which was already started")
					note("Line: " + line)
					continue
				arr[id] = 1
			elif cmd == "going":
				if arr[id] < 1:
					err("Trying to put atom into queue, which wasn't started")
					note("Line: " + line)
					continue
				if arr[id]>1:
					err("Trying to put atom into queue, which was already in queue")
					note("Line: " + line)
					continue
				arr[id] = 2
			elif cmd == "creating":
				if arr[id] < 2:
					err("Trying to create molecule with atom, which wasn't in queue")
					note("Line: " + line)
					continue
				if arr[id] > 2:
					err("Trying to create molecule with atom, which was already used to create molecle")
					note("Line: " + line)
				arr[id] = 3
			elif cmd == "molecule":
				if arr[id] < 3:
					err("Trying to finnish creation of molecule which hasn't yet started")
					note("Line: " + line)
					continue
				if arr[id] > 3:
					err("Trying to finnish creation of molecule which was already created")
					note("Line: " + line)
					continue
				arr[id] = 4
			elif cmd == "not":
				if arr[id] < 2:
					err("Atom needs to be in queue before figuring out it can't make molecule")
					note("Line: " + line)
					continue
				if arr[id] > 2:
					err("Atom failed making molecule after it started")
					note("Line: " + line)
					continue
				arr[id] = 4
			else:
				err("Unknown action of atom")
				note("Line: " + line)
		faults = ["wasn't started", "didn't went to queue", "didn't attempted to create molecule", "didn't finnished forming of molecule"]
		for i, x in enumerate(oarr):
			if x<4:
				err(f"Oxygen {i+1} {faults[x]}")
		for i, x in enumerate(harr):
			if x<4:
				err(f"Hydrogen {i+1} {faults[x]}")
		dataFile.close()
	proc.wait()
	postclean()
	if proc.returncode != 0:
		err("Wrong return code, should be set to 0")

test("Makefile")
if not exists("./Makefile"):
	err("Makefile doesn't exists")
else:
	note("Automatically running make")
	if os.system("make"):
		err("Error while executing make")

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
processSucess(0, 0, 100, 100)

test("Not enough of atoms for molecule (1, 1, 100, 100)")
processSucess(1, 1, 100, 100)

test("Creating one molecule (1, 2, 100, 100)")
processSucess(1, 2, 100, 100)

testEnd()
note("Test script has finnished")
note(f"Total of {testCnt} tests were run, {failedCnt} failed")

if allPassed:
	print(Fore.GREEN + "All tests have passed!!! :)" + Fore.WHITE)
else:
	if not showOut:
		note("You can try running the script as ./test.py --show-out to show ./proj2.out on failed tests")
	print(Fore.RED + "Some tests have failed :(" + Fore.WHITE)
