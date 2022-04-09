#!/usr/bin/python3
import subprocess
from colorama import Fore
from os.path import exists
import os

allPassed = True

def err(text):
	global allPassed
	allPassed = False
	print("[" + Fore.RED + "ERR" + Fore.WHITE + "] " + text)

def note(text):
	print("[ " + Fore.CYAN + "*" + Fore.WHITE + " ] " + text)

def succ(text):
	print("[" + Fore.GREEN + "OK" + Fore.WHITE + " ] " + text);

def test(text):
	note("Test for: " + text)

note("Test script has started")

if not exists("./proj2"):
	err("Script has to be in same directory as ./proj2")


def preclean():
	os.system("rm proj2.out")

def postclean():
	failed = False
	if "proj2" in subprocess.check_output(["ps"]).decode("utf-8"):
		err("Proj2 is still running after process exited (unterminated childs)")
		os.system("pkill proj2")
		note("Proj2 is killed automatically now")
		failed = True
	return failed

def processFail(params):
	proc = subprocess.Popen(["./proj2"] + params, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
	failed = False
	try:
		outs, errs = proc.communicate(timeout=5)
		if outs != "":
			err("There shouldnt be any text on stdout")
			failed = True
		if errs.strip() == "":
			err("Missing error output on stderr")
			failed = True
	except subprocess.TimeoutExpired:
		proc.kill()
		err("Process timed out")
		postclean()
		return
	proc.wait()
	failed |= postclean()
	if proc.returncode != 1:
		err("Wrong return code, should be set to 1")
		failed = True
	if failed:
		err("Test failed")
	else:
		succ("Test passed")

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
test("Negative NH")
processFail(["1", "-1", "1", "1"])
test("NH not a number")
processFail(["1", "1a", "1", "1"])
test("Negative TI")
processFail(["1", "1", "-1", "1"])
test("Too big TI")
processFail(["1", "1", "1001", "1"])
test("Negative TB")
processFail(["1", "1", "1", "-1"])
test("Too big TB")
processFail(["1", "1", "1", "1001"])


note("Test script has finnished")

if allPassed:
	print(Fore.GREEN + "All test have passed!!! :)" + Fore.WHITE)
else:
	print(Fore.RED + "Some tests have failed :(" + Fore.WHITE)
