#!/usr/bin/python3
import subprocess
from colorama import Fore
from os.path import exists
import os

allPassed = True

testCnt = 0
failedCnt = 0
testFailed = False
testRunning = False

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
	print("[ " + Fore.BLUE + "T" + Fore.WHITE + " ] " + text)
	note("Test for: " + text)
	preclean()

def testEnd():
	global testFailed
	global testRunning
	if testRunning:
		if testFailed:
			err("Test failed")
			failedCnt += 1
		else:
			succ("Test passed")
	testRunning = False
	testFailed = False

note("Test script has started")

if not exists("./proj2"):
	err("Script has to be in same directory as ./proj2")


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
		for line in dataFile.readlines():
			pass
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

test("Basic test (2, 1, 100, 100)")
processSucess(2, 1, 100, 100)

testEnd()
note("Test script has finnished")
note(f"Total of {testCnt} tests were run, {failedCnt} failed")

if allPassed:
	print(Fore.GREEN + "All test have passed!!! :)" + Fore.WHITE)
else:
	print(Fore.RED + "Some tests have failed :(" + Fore.WHITE)
