#!/usr/local/bin/python2.6
import sys
import os
import string
import re
import getpass

#
#--- reading directory list
#

path = '/proj/web-cxc/cgi-gen/mta/Obscat/ocat/Info_save/dir_list_new'           #---- test directory list path
#path = '/data/udoc1/ocat/Info_save/dir_list'                                #---- live directory list path

f    = open(path, 'r')
data = [line.strip() for line in f.readlines()]
f.close()

for ent in data:
    atemp = re.split(':', ent)
    var  = atemp[1].strip()
    line = atemp[0].strip()
    exec "%s = %s" %(var, line)

#
#--- append path to a private folder
#

sys.path.append(bin_dir)

import readSQL         as tdsql
import tooddtFunctions as tdfnc


#------------------------------------------------------------------------------------------------------------------
#-- comp_two_obsid_lists: compare two lists and extract data with obsids only in the first list                 ---
#------------------------------------------------------------------------------------------------------------------

def comp_two_obsid_lists(list1, list2):

    """
    compare two lists and extract data with obsids only in the first list
    input: two lists such as too_list and too_list~
    """

    f     = open(list1, 'r')
    data1 = [line.strip() for line in f.readlines()]
    f.close()

    f     = open(list2, 'r')
    data2 = [line.strip() for line in f.readlines()]
    f.close()

    obsidList1 = tdfnc.read_current_obsid(list1)
    obsidList2 = tdfnc.read_current_obsid(list2)

    newobsids  = list(set(obsidList1).difference(set(obsidList2)))

    newentry   = pick_lines(data1, newobsids)

    return newentry

#------------------------------------------------------------------------------------------------------------------
#--- get_obsid_from_list: extreact obsid from a list in the format of too_list                                  ---
#------------------------------------------------------------------------------------------------------------------

def get_obsid_from_list(list):

    """
     extreact obsid from a list in the format of too_list
     input: list (e.g., too_list, ddt_list)
    """

    obsidList = []
    for ent in list:
        atemp = re.split('\s+|\t+', ent)
        obsidList.append(atemp[2])
    obsidList.sort()

    return obsidList

#------------------------------------------------------------------------------------------------------------------
#--- pick_lines: choose line from list with entries of tag list                                                 ---
#------------------------------------------------------------------------------------------------------------------

def pick_lines(list, tags):

    """
    choose lines from a list with entries in tag list
    input: list example: too_list, tags: obsid list
    """

    newentry = []
    for ent in list:
        atemp = re.split('\s+|\t+', ent)
        for comp in tags:
            if str(atemp[2]) == str(comp):
                newentry.append(ent)


    return newentry

#----------------------------------------------------------


if __name__ == '__main__':

    list1 = too_dir + 'test_list'
    list2 = too_dir + 'test_list~'
    out  = comp_two_obsid_lists(list1, list2)

    for ent in out:
        print ent
