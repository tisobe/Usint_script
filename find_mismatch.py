#!/usr/local/bin/python2.6

#########################################################################################################################
#                                                                                                                       #
#   find_mismatch.py:  check update_table.list and check whether a phantom entry is created in the list                 #
#                                                                                                                       #
#           author: t. isobe (tisobe@cfa.harvard.edu)                                                                   #
#                                                                                                                       #
#           last update: Jan 25, 2013                                                                                   #
#                                                                                                                       #
#########################################################################################################################
import math
import re
import sys
import os
import string

#
#--- set a few global parameters
#

admin_mail = 'isobe@head.cfa.harvard.edu'
saved_file = '/data/udoc1/ocat/Info_save/past_mismatch'
temp_file  = '/data/udoc1/ocat/Working_dir/cus/mismatch_check'

#-------------------------------------------------------------------------------------------------------------------------
#---find_mismatch: check update_table.list and check whether a phantom entry is created in the list                   ----
#-------------------------------------------------------------------------------------------------------------------------


def find_mismatch():
    """
    this script reads /data/udoc1/ocat/updates_table.list and compares files created in /data/udoc1/ocat/updates/
    if there are any mismatchs, the script reports the fact to admin.
    input: no
    output: email to admin, update saved_file (past mismatched list)
    """
#
#--- read the past mismatch entries
#
    f = open(saved_file, 'r')
    temp_list = [line.strip() for line in f.readlines()]
    f.close()
    past_list = []
    for ent in temp_list:
        try:
            val = float(ent)
            past_list.append(val)
        except:
            pass

#
#--- read names of files 
#
    line = 'ls /data/udoc1/ocat/updates/* > ' + temp_file
    os.system(line)

    f = open(temp_file, 'r')
    temp_list = [line.strip() for line in f.readlines()]
    f.close()

    file_list = []
    for ent in temp_list:
        atemp =  re.split('/data/udoc1/ocat/updates/', ent)
        try:
            val = float(atemp[1])
            file_list.append(val)
        except:
            pass

    file_list.sort()

    line = 'rm  ' + temp_file
    os.system(line)
#
#---- read the names on the list
#

    f = open('/data/udoc1/ocat/updates_table.list')
    list = [line.strip() for line in f.readlines()]
    f.close()

    entry_list =[]
    for ent in list:
        atemp = re.split('\s+|\t+', ent)
        try:
            val = float(atemp[0])
            entry_list.append(float(atemp[0]))
        except:
            pass

    entry_list.sort()

#
#---- find entry which exists in entry_list, but not in file_list
#
    mismatch_list = []
    dcnt = len(file_list)
    i    = 0

    for ent in entry_list:
        chk = 0
        for j in range(i, dcnt):
            if ent == file_list[j]:
                i = j
                chk = 1
                break

        if chk == 0:
            mismatch_list.append(ent)
#
#--- compare with the past mismatch list and check whether any of them are new
#
    new_mismatch = []
    for ent in mismatch_list:
        chk = 0
        for ent2 in past_list:
            if ent == ent2:
                chk = 1
                break
        if chk == 0:
            new_mismatch.append(ent)

#
#--- if there is a new entry, send warning to admin and also append that entry to the past_mismatched list
#
    if len(new_mismatch) > 0:
        f  = open(temp_file,  'w')
        f2 = open(saved_file, 'a')
        f.write('The following entry in /data/udoc1/ocat/updates_table.list does not have a counter part.\n\n')
        for ent in mismatch_list:
            f.write(str(ent))
            f.write('\n')

            f2.write(str(ent))
            f2.write('\n')
        f.close()
        f2.close()

        line = 'cat '+ temp_file + '| mailx -s "Subject: Mismatch in updates_table.list" ' +  admin_mail
        os.system(line)
        line = 'rm ' + temp_file
        os.system(line)


#---------------------------------------------------------------------

if __name__ == '__main__':
    
    find_mismatch()


