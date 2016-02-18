"""Convert a SMCL file into Markdown

This modules converts a SMCL file into Markdown/HTML.
It does so in four passes:

1. Convert SMCL directives into XML elements (e.g. <title>..</title>)
2. Create a tree using lxml's ElementTree API
3. Modify the tree to create better abstractions
   (e.g. tables, syntax tables, etc.)
4. Walk through the tree and write Markdown

Notes:
 - A SMCL directive is of the form: {tag [options] [:content]}
 - Directives cannot span multiple lines

Not supported:
- Using the {col} directive to set up tables manually (maybe in v2)
- Multiple markers pointing to the same spot (can we have multiple ids in html5?)
- Indenting the first line of a para is not common practice on a webpage (but can be done: http://www.w3schools.com/cssref/pr_text_text-indent.asp)

Ideas:
- Right after creating the tree, iterate through every element and set .tail = '' if the tail is None
  This will simplify many lines.
  Note: don't do this for .text as when its none the result is <tag/> and when its empty its <tag></tag>
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------
import os
import re
import argparse # https://mkaz.com/2014/07/26/python-argparse-cookbook/
import webbrowser

from lxml import etree, html # http://infohost.nmt.edu/~shipman/soft/pylxml/web/etree-view.html
from lxml.builder import E # http://lxml.de/tutorial.html#the-e-factory

import smcl_parser

# -------------------------------------------------------------
# Constants
# -------------------------------------------------------------

directive_regex = re.compile("""
    (?P<head>[^}]*?) # Match as little as possible, excluding closing brackets
    {
    \ * # (optional spaces)
    (?P<tag>[\w]+) # Mandatory tag
    (?:
    \ + # (optional spaces)
    (?P<options>
        [^{}:"]+ # Text without quotes
        |
        "[^{}"]+" # Text in quotes
        |
        "[^{}"]*"\ "[^{}"]*" # Two texts each in quotes
        |
        [^{}"]*\ "[^{}"]*" # First text w/out quotes, second with quotes
    ) # Directive options
    )?
    (?:
    \ * # (optional spaces)
    : # Separator between options and content
    (?P<content>[^{}]+)? # Content (text, nested directives, etc)
    )?
    }
    (?P<tail>.*) # Tail text and unparsed directives; greedy
    """, re.VERBOSE)

# -------------------------------------------------------------
# Functions
# -------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="smcl2html: convert Stata help files into HTML files (higher-level and more semantic tags)")
    parser.add_argument('filename')
    parser.add_argument('--output','-o', action='store', help='output filename' )
    parser.add_argument('--adopath','-a', action='store', help='path of base ado files' )
    parser.add_argument('--standalone', '-s', action='store_true', help='inspect tex log' )
    parser.add_argument('--view', '-v', action='store_true', help='view html output in a browser' )
    parser.add_argument('--xml', action='store_true', help='save intermediate XML file instead' )
    args = parser.parse_args()

    # Check that file exists and has correct extension
    fn = args.filename
    assert fn, "File {} does not exist or pattern matches no file".format(fn)
    valid_extensions = ('.smcl', '.sthlp', '.hlp', '.log')
    assert os.path.splitext(fn)[-1] in valid_extensions, "File {} has an unexpected extension".format(fn)

    args.current_file = os.path.splitext(os.path.basename(args.filename))[0]

    if args.output is None:
        args.output = args.current_file + '.html'

    args.output = os.path.abspath(args.output)
    return args

# -------------------------------------------------------------

def read_smcl(fn):
    with open(fn, 'r') as f:
       smcl = f.readline().strip()
       assert smcl == '{smcl}', 'First line must be "{smcl}"'
       lines = f.readlines()
    return lines

def expand_includes(lines, adopath):
    includes = [ ( i , line[13:].strip() ) for (i,line) in enumerate(lines) if line.startswith('INCLUDE help ')]
    if os.path.exists(adopath):
        for i, cmd in reversed(includes):
            fn = os.path.join(adopath, cmd[0], cmd if cmd.endswith('.ihlp') else cmd + '.ihlp')
            with open(fn, 'r') as f:
                content = f.readlines()
            if content[0].startswith('{* *! version'):
                content.pop(0)
            lines[i:i+1] = content
    elif adopath:
        print('[Warning] Base adopath does not exist:', adopath)
    return lines

def newline_after_p_end(lines):
    # Iterate with while because I will be expanding -lines- on the go
    i = 0
    while i<len(lines):
        line = lines[i]
        if '{p_end}' in line and not line.strip().endswith('{p_end}'):
            newlines = line.split('{p_end}', 1) # Split line in two
            newlines[0] = newlines[0] + '{p_end}\n'
            lines[i:i+1] = newlines
        i += 1
    return lines

def smcl2xml(lines):
    lines = [parse_line(line) for line in lines]
    xml = '<smcl>' + '<newline/>'.join(lines) + '</smcl>'
    return xml

def parse_line(line):
    line = cleanup_line(line)

    while True:
        m = directive_regex.match(line)
        if not m:
            break
        opt = m.group('options')
        tag = m.group('tag')
        content = m.group('content')
        attrib = " options='{}'".format(opt) if opt else ''
        if content:
            element = '<{tag}{attrib}>{content}</{tag}>'.format(tag=tag, attrib=attrib, content=content)
        else:
            element = '<{tag}{attrib}/>'.format(tag=tag, attrib=attrib)
        line = m.group('head') + element + m.group('tail')
    return line

def cleanup_line(line):
    line = line.rstrip()
    line = line.replace('{...}', '{nobreak}')
    line = line.replace('{* ', '{comment ')
    line = line.replace('&','&amp;') # Else lxml crashes
    line = line.replace("'",'&apos;') # Else lxml crashes
    line = line.replace('<','&lt;') # Else lxml crashes
    line = line.replace('>','&gt;') # Else lxml crashes
    return line

def make_standalone(div, current_file):
    script = """
    hljs.configure({
        languages: ['']
    })
    hljs.initHighlightingOnLoad();
"""
    html = E.html(
        E.head(
            E.title('Stata help for ' + current_file),
            E.link(rel='stylesheet', type='text/css', href='css/smcl.css'),
            #
            #E.link(rel='stylesheet', type='text/css', href='js/styles/idea.css'), # Idea sunburst syntax style
            #E.script('', src='js/highlight.pack.js'),
            #E.script(script),
            #
            # E.link(rel='stylesheet', type='text/css', href='css/fonts.css'),
            E.link(rel='stylesheet', type='text/css', href='https://fonts.googleapis.com/css?family=Merriweather:900,400,400italic'),
            E.link(rel='stylesheet', type='text/css', href='https://fonts.googleapis.com/css?family=Source+Sans+Pro:600,600italic')
        ),
        E.body(div)
    )

    return html

def run_tests(input_path, output_path, adopath, standalone=True):
    all_fn = os.listdir(input_path)

    for base_fn in all_fn:
        fn = os.path.join(input_path, base_fn)
        current_file = os.path.splitext(os.path.basename(fn))[0]

        # Transform SMCL representation into XML representation
        lines = read_smcl(fn)
        lines = expand_includes(lines, adopath) # Replace lines like "INCLUDE help fvvarlist"
        lines = newline_after_p_end(lines)
        xml = smcl2xml(lines)

        # Construct tree
        root = etree.fromstring(xml)

        # Modify tree to create better abstractions
        root = smcl_parser.parse_blocks(root, current_file)
        root = smcl_parser.parse_inlines(root, current_file)
        root = smcl_parser.parse_improvements(root)

        # Create complete html file (standalone option)
        if standalone:
            doctype = '<!DOCTYPE html>'
            root = make_standalone(root, current_file)
        else:
            doctype = None

        # Export file
        out_fn = os.path.join(output_path, current_file + '.html')
        text = etree.tostring(root, encoding='utf-8', method='html', 
                              pretty_print=True, xml_declaration=True, doctype=doctype)
        with open(out_fn, mode='wb') as fh:
            fh.write(text)

# -------------------------------------------------------------
# Main
# -------------------------------------------------------------

if __name__ == '__main__':

    # Parse opts
    args = parse_args()

    # Transform SMCL representation into XML representation
    lines = read_smcl(args.filename)
    lines = expand_includes(lines, args.adopath) # Replace lines like "INCLUDE help fvvarlist"
    lines = newline_after_p_end(lines)
    xml = smcl2xml(lines)

    if args.xml:
        # Only save intermediate XML file
        xml = xml.replace('<newline/>', '<newline/>\n')
        with open(args.output, mode='w') as fh:
            fh.write(xml)
    else:
        # Construct tree
        root = etree.fromstring(xml)
        #tree = etree.ElementTree(root)

        # Modify tree to create better abstractions
        root = smcl_parser.parse_blocks(root, args.current_file)
        root = smcl_parser.parse_inlines(root, args.current_file)
        root = smcl_parser.parse_improvements(root)

        # Create complete html file (standalone option)
        if args.standalone:
            doctype = '<!DOCTYPE html>'
            root = make_standalone(root, args.current_file)
        else:
            doctype = None

        # Export file
        text = etree.tostring(root, encoding='utf-8', method='html', 
                              pretty_print=True, xml_declaration=True, doctype=doctype)
        with open(args.output, mode='wb') as fh:
            fh.write(text)
    
    if args.view:
        webbrowser.open(args.output)
