#!/usr/bin/env python

import unittest
import os
import subprocess
import shutil
import tempfile
import sys
import stat
import imp
import inspect

def checkPresentA(myA,myStream):
    for l in myStream:
        for d in  myA:
            name=d['name'].split(':')[0]
            tag=d['name'].split(':')[1]
            if name in l and tag in l :
                d['found']=True
    present=True
    for d in  myA:
        present &= d['found']
    return present

def printDockerImagesSad(hdr,myA):
    cmd="docker images"
    p=subprocess.Popen(cmd.split(), stderr=sys.stderr, stdout=subprocess.PIPE,
                       shell=False)
    print("\n\nFAILURE--%s-- Images ->"%(hdr))
    for l in p.stdout:
        print ("%s",l)
    print ("Looking for:")
    for d in myA:
        if not d['found']:
            print("%s found = %s"%(d['name'],d['found']))

class TestContainersBuilt(unittest.TestCase):
    def setUp(self):
        self.sdkTargets = os.environ['TARGETS'].split()
        self.sdkYPRelease = os.environ['YP_RELEASE']
        self.sdkCropsRelease = os.environ['CROPS_RELEASE']
        self.containers=[]

        for t in self.sdkTargets:
            c={}
            c['name']="toolchain-%s:%s"%(t,self.sdkYPRelease)
            c['found']=False
            self.containers.append(c)

    def tearDown(self):
        self.containers=None
        pass


    def test_deps_containers_built(self):
        cmd = """docker  images """
        p=subprocess.Popen(cmd.split(),stderr=sys.stderr, stdout=subprocess.PIPE,
                           shell=False)
        checkA=self.containers
        allBuilt=checkPresentA(checkA,p.stdout)
        if not allBuilt:
            # error information is more useful than true is not false
            printDockerImagesSad(inspect.stack()[0][3],checkA)

        self.assertTrue(allBuilt)



if __name__ == '__main__':
    unittest.main()
