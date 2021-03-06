#!/usr/bin/env python

# Python script to extract a lightcurve from the PN camera
import subprocess
import glob
import os
import shutil

# EDIT HERE ===================================================================
os.environ['SAS_ODF'] = os.path.abspath(glob.glob('../../rpcdata/*SUM.SAS')[0])
os.environ['SAS_CCF'] = os.path.abspath(glob.glob('../../rpcdata/ccf.cif')[0])

# To use cleaned event file:
# shutil.copyfile('../pn_clean.ds', 'pn_clean_barycen.ds')
# subprocess.call(['barycen', 'table=pn_clean_barycen.ds:EVENTS'])
# table = 'pn_clean_barycen.ds'

# Use original baricentric corrected event file
table = '../../rpcdata/pnevents_barycen.ds'

srcregionfile = 'src.reg'
bkgregionfile = 'bkg.reg'

# maximum pattern
pattern = 4

tstart = float(input("Enter initial time: "))
tstop = float(input("Enter final time: "))

bins = [10, 50, 100, 150, 200, 300, 350]
emins = [300, 300, 2000, 4500, 2000]
emaxs = [10000, 2000, 4500, 10000, 10000]
strin = ['0.3-10keV', '0.3-2keV', '2-4.5keV', '4.5-10keV', '2-10keV']

# ++++++++++++++++++++++ Edit only if necessary +++++++++++++++++++++++++++++++
# srcregion = 'circle(10000,20000,200)'
src = open(srcregionfile, 'r')
srcregion = src.readlines()[-1].strip()
src.close()

# bkgregion = 'circle(10000,20000,200)'
bkg = open(bkgregionfile, 'r')
bkgregion = bkg.readlines()[-1].strip()
bkg.close()
# ========================================== END of EDIT block ================

for bin in bins:
    for i, energy in enumerate(zip(emins, emaxs)):
        # define output filenames
        srclc = 'pn_lc_src_{0}_bin{1}.ds'.format(strin[i], bin)
        bkglc = 'pn_lc_bkg_{0}_bin{1}.ds'.format(strin[i], bin)
        netlc = 'pn_lc_net_{0}_bin{1}.ds'.format(strin[i], bin)
        srcimg = 'pn_src_img_{0}_bin{1}.ds'.format(strin[i], bin)
        bkgimg = 'pn_bkg_img_{0}_bin{1}.ds'.format(strin[i], bin)
        psimg = 'pn_lc_net_{0}_bin{1}.ps'.format(strin[i], bin)

        # selection exprssion
        srcexp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <={3} \
&& FLAG==0 && ((X,Y) IN {2})'.format(energy[0], energy[1], srcregion, pattern)
        bkgexp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <={3} \
&& FLAG==0 && ((X,Y) IN {2})'.format(energy[0], energy[1], bkgregion, pattern)

        # Extract a lightcurve for the src+bkg region, single and double events
        subprocess.call(
            ['evselect', 'table={0}'.format(table),
             'energycolumn=PI', 'withrateset=yes', 'rateset={0}'.format(srclc),
             'timebinsize={0}'.format(bin), 'maketimecolumn=yes',
             'makeratecolumn=yes', 'withimageset=yes',
             'imageset={0}'.format(srcimg), 'xcolumn=X', 'ycolumn=Y',
             'timemin={0}'.format(tstart),
             'timemax={0}'.format(tstop), srcexp])

        # Extract a lightcurve for the bkg region for single and double events
        subprocess.call(
            ['evselect', 'table={0}'.format(table),
             'energycolumn=PI', 'withrateset=yes', 'rateset={0}'.format(bkglc),
             'timebinsize={0}'.format(bin), 'maketimecolumn=yes',
             'makeratecolumn=yes', 'withimageset=yes',
             'imageset={0}'.format(bkgimg), 'xcolumn=X', 'ycolumn=Y',
             'timemin={0}'.format(tstart),
             'timemax={0}'.format(tstop), bkgexp])

        # Apply corrections and creates the net lightcurve
        subprocess.call(
            ['epiclccorr', 'eventlist={0}'.format(table),
             'outset={0}'.format(netlc), 'srctslist={0}'.format(srclc),
             'applyabsolutecorrections=yes', 'withbkgset=yes',
             'bkgtslist={0}'.format(bkglc)])

        # Save the net lightcurve visualization
        subprocess.call(
            ['dsplot', 'table={0}'.format(netlc), 'withx=yes',
             'withy=yes', 'x=TIME', 'y=RATE',
             'plotter=xmgrace -hardcopy -printfile {0}'.format(psimg)])
