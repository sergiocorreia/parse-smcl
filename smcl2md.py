"""Convert an SMCL file into Markdown

This modules converts an SMCL file into Markdown/HTML.
It does so in three passes:

    1) Parse SMCL directives line-by-line, creating a list of
       nested directive objects.
    2) Replace Directive objects with Node objects, with better
       abstraction (e.g. tables, syntax tables, etc.)
    3) Walk through the Directive tree and write Markdown
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------
import shlex
#import os
#import sys
#import csv
#import re
#import time

# -------------------------------------------------------------
# Classes
# -------------------------------------------------------------

class Directive(list):
    """Directive objects that map the Stata SMCL ones

    Every SMCL directive {directive args: text} gets mapped
    into one such object. Two special directives will be the
    -text- directive (for plain text) and the -newline- 
    directive.

    Directives can contain other directives inside
    the -text- option. In fact, the text option can contain
    only: i) nothing (empty list), ii) list of other directives
    where the most common one is text
    """

    def __init__(self, tag='', args='', text=None):

        if tag == '*':
            tag = 'comment'
        elif tag == '...':
            tag = 'nobreak'

        assert tag

        self.tag = tag
        self.args = args if args is not None else ''
        self.text = text if text is not None else []

        if self.tag == "text":
            assert self.text != ''

    def __repr__(self):
        return '<' + self.tag.upper() + '>'

    def __str__(self):
        text = self.text if self.tag != 'text' else '<' + self.text + '>'
        return '{}({}) = {}'.format(self.tag.upper(), self.args, text)


class Node(list):
    """Node is a Metaclass, don't create instances of this but of the block/inline subclasses"""

    def __init__(self, content=None, options=None):
        self.options = options if options is not None else dict()
        self.content = content if content is not None else list()
        assert 'tag' in self.__class__.__dict__

    def __repr__(self):
        return '<' + self.tag.upper() + '>'
        
    def __str__(self):
        opt = repr(self.options)[1:-1] #', '.join(self.options.items())
        return '{}({}) = {}'.format(self.tag, opt, list.__repr__(self.content))

# Create classes dynamically
def node_class(tag, two_parts=False):
    return type(tag, (Node,), {'tag':tag})

# Block Tags
SMCL = node_class('SMCL') # Root node
Break = node_class('Break') # <br/>

Line = node_class('Line') # Default
Para = node_class('Para')
Title = node_class('Title')
Table = node_class('Table')
Rule = node_class('Rule') # Horizontal rule
Meta = node_class('Meta')
Syntab = node_class('Syntab') # Syntax Table

# Inline Tags
Text = node_class('Text') # Default

# -------------------------------------------------------------
# Functions
# -------------------------------------------------------------

def convert_scml(input_fn, output_fn):
    lines = read_smcl(input_fn)
    directives = parse_lines(lines)
    #for directive in directives:
    #    walk(directive)
    smcl = parse_directives(directives)

def read_smcl(fn):
    with open(fn, 'r') as f:
        smcl = f.readline().strip()
        assert smcl == '{smcl}', 'First line must be "{smcl}"'
        lines = [line.rstrip() for line in f]
    return lines

def parse_lines(lines):
    directives = []
    newline = Directive('newline')
    for line in lines:
        #print('[LINE]   ', line)
        line = 'line:' + line + '}'
        line_directive, _ = parse_directive(line)
        directives.extend(line_directive.text + [newline])
    return directives

def parse_directive(line, i=0, level=0):
    pos = 1 # # {tag args : text} so 1=tag 2=args 3=text
    assert i < len(line)
    tag = None
    args = None
    text = []
    update = False

    j = i
    n = len(line)
    while i < n:
        c = line[i]

        if pos == 1 and c in (' ', ':', '}'):
            tag = line[j:i]
            update = True

        if pos == 2 and c in (':', '}'):
            args = line[j:i]
            update = True

        if pos == 3 and (c == '}'):
            if i > j:
                directive = Directive('text', '', line[j:i])
                #print('    ' * (level+1), directive)
                text.append(directive)
            update = True

        if update:
            update = False
            j = i + 1

            if c == ' ':
                pos = 2
            elif c == ':':
                pos = 3
            else:
                directive = Directive(tag, args, text)
                #print('    ' * level, directive)
                return directive, j
        elif (pos == 3) and (c == '{'):
            if i > j:
                directive = Directive('text', '', line[j:i])
                #print('    ' * (level+1), directive)
                text.append(directive)
            directive, i = parse_directive(line, i+1, level+1)
            text.append(directive)
            j = i
        else:
            i += 1

def walk(d, level=0):
    print(' '*4*level, d)
    if d.text and d.tag != 'text':
        for dd in d.text:
            walk(dd, level+1)

def parse_directives(directives):
    smcl = SMCL()
    last_tag = None
    hold_break = False
    for directive in directives:
        
        # Add some meta directives as options of the SMCL root node
        if directive.tag == 'comment' and directive.args.startswith('*! '):
            k, v = directive.args[2:].strip().split(maxsplit=1)
            smcl.options[k] = v
            continue

        if directive.tag.startswith('viewer'):
            k = directive.tag[6:]
            v = shlex.split(directive.args)
            if k in smcl.options:
                smcl.options[k].append(v)
            else:
                smcl.options[k] = [v]

        if directive.tag == 'nobreak':
            hold_break = True

        if directive.tag == 'newline' and hold_break:
            hold_break = False
            continue

        if directive.tag == 'newline' :
            smcl.content.append(Break())
        

    print(smcl)
    return smcl


# -------------------------------------------------------------
# Main
# -------------------------------------------------------------

if __name__ == '__main__':

    # Parse opts here
    # ...
    fn = r'C:\bin\Stata14\ado\base\b\bayesmh.sthlp'
    fn = r'c:\ado\plus\r\reghdfe.sthlp'

    convert_scml(fn, '')
