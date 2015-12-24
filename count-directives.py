#---------------------------------------------------------------
# Count SMCL files in a help file
#---------------------------------------------------------------

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------
import os, sys, csv, re, time
from collections import Counter


# -------------------------------------------------------------
# Constants
# -------------------------------------------------------------
fn = r'c:\ado\plus\r\reghdfe.sthlp'
fn = r'C:\bin\Stata14\ado\base\b\bayesmh.sthlp'

# -------------------------------------------------------------
# Functions
# -------------------------------------------------------------

# -------------------------------------------------------------
# Main
# -------------------------------------------------------------

if __name__=='__main__':

    with open(fn,'r') as fh:
        text = fh.readlines()

    c = Counter()

    for line in text:
        # regex = re.findall('\{([^} :]+)[^}]*\}', line)
        regex = re.findall('\{([^} :,]+)', line)
        for match in regex:
            c[match] += 1

    fh = open('directives_count.csv','w')
    fh.write('directive,n\n')
    for directive in c:
        print(directive,c[directive])
        fh.write('{},{}\n'.format(directive, c[directive]))
    fh.close
    print('Done!')