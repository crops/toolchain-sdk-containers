#!/usr/bin/env python

# if you want to run the tests outside of Travis (aka local linux box):
# 1) populate a fresh bash shell with the necessary env variables:
#    $>base/scripts/setupTravisEnv.sh
# 2) run the tests:
#    $>CROPS_CODI_PORT="tcp://172.17.0.11:10000" PYTHONPATH=$PYTHONPATH:`pwd`/base/tests/unit/ python tests.py
#    the CROPS_CODI_PORT is whatever ip address docker uses for linked containers. You check it by
#     running a linked container and doing a printenv
#    the tests utils are in base so I find it easiest to extend my pythonpath for those.

import unittest
import os
import subprocess
import shutil
import tempfile
import sys
import stat
import imp
import inspect
from utils.testutils import *
import time
import requests

# our Target names and the target architecture names do not always match
TtoA={'core2-64':'x86_64',
      'i586':'i586',
      'aarch64':'aarch64',
      'armv5e':'arm',
      'mips64':'mips64'}

def runAndLog(cmd):
    p=subprocess.Popen(cmd.split(), shell=False)
    sout,serr = p.communicate()
    if p.returncode:
        print("SAD cmd = <%s>"%(cmd))
        print("p.returncode=%d sout = <%s> serr = <%s>\n"%(p.returncode,sout,serr))
    return p.returncode

def startTargetToolchain(t,cName):

    cmd = "docker  run -d  -v /var/run/docker.sock:/var/run/docker.sock --link crops-codi --name=tc-%s   %s" % (t.lower(),cName)
    if runAndLog(cmd):
        cmd="docker logs tc-%s"%(t.lower())
        runAndLog(cmd)

class TestToolchainsRegistered(unittest.TestCase):
    def setUp(self):
        self.codiAddr = os.environ['CODI_ADDR']
        self.codiPort=os.environ['CODI_PORT']
        self.dockerhubRepo=os.environ['DOCKERHUB_REPO']
        self.ypRelease=os.environ['YP_RELEASE']
        self.ok=True
        #cmd = "docker  run -d  -v /var/run/docker.sock:/var/run/docker.sock  -p %s:%s  --name=crops-codi crops/codi" % \
        #      (self.codiPort,self.codiPort)
        #if runAndLog(cmd):
        #    cmd = "docker logs crops-codi"
        #    runAndLog(cmd)
        # getting rethinkdb and codi up can take a bit
        #time.sleep(10)
        self.targets = os.environ['TARGETS']
        self.toolchainContainers=[]
        for t in self.targets.split():
            toolchainContainer="%s/toolchain-%s:%s" % (self.dockerhubRepo,t,self.ypRelease)
            self.toolchainContainers.append(toolchainContainer)
            #startTargetToolchain(t,toolchainContainer)
        # we need to give the containers time to register
        time.sleep(10)
    def tearDown(self):
        if not self.ok:
            print("Teardown: FAIL logs to follow")
            # print out the logs of what went wrong
            print "crops-codi log:"
            cmd = "docker logs --tail=all crops-codi"
            runAndLog(cmd)
            for t in self.targets.split():
                print ("%s log:"%(t))
                cmd = "docker logs tc-%s"%(t.lower())
                runAndLog(cmd)

        # clean up the containers
        cmd = "docker rm -f crops-codi"
        runAndLog(cmd)
        for t in self.targets.split():
            cmd = "docker rm -f tc-%s"%(t.lower())
            runAndLog(cmd)
        pass


    def test_toolchains_registered(self):
        found=True
        for t in self.targets.split():
            time.sleep(1)
            try:
                myFilter={'filter':'{\"target\":{\"arch\":\"%s\"}}'%(TtoA[t])}
            except:
                myFilter={'filter':'{\"target\":{\"arch\":\"%s\"}}'%(t)}

            myUrl = "http://%s:%s/codi/list-toolchains"%(self.codiAddr,self.codiPort)
            r=requests.get(myUrl,params=myFilter)
            myFound=(r.status_code==200)
            found &= myFound
            if not myFound:
                print("Bad status code %d from: %s"%(r.status_code,r.url))
                continue
            try:
                j=r.json()[0]
                myFound = TtoA[t] in j['target']['arch']
            except:
                myFound=False
            if not myFound:
                print("Bad arch. Failed to find arch toolchain for target :%s\n"%(t))
                print ("rText=%s\n"%(r.text))
                if len(r.json()) > 0:
                    print ("returned json was %s\n"%(r.json()[0]))
                print("from CODI server url=<%s>,filter=<%s>\n"%(myUrl,myFilter))

            found &= myFound

        self.ok &= found
        self.assertTrue(found)



if __name__ == '__main__':
    unittest.main()
