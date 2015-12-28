"""Convert an SMCL file into Markdown

This modules converts an SMCL file into Markdown/HTML.
It does so in three passes:

    1) Parse SMCL directives line-by-line, creating a list of
       nested directive objects.
    2) Replace Directive objects with Node objects, with better
       abstraction (e.g. tables, syntax tables, etc.)
    3) Walk through the Directive tree and write Markdown

An SMCL directive is of the form
    {directive [options] [:items]}
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------
import shlex
import re
#import os
#import sys
#import csv
#import time

# -------------------------------------------------------------
# Constants
# -------------------------------------------------------------
pclass = re.compile(r'p(std|see|hang\d?|more\d?|in\d?)')
num_tags = num_directives = 0

# -------------------------------------------------------------
# Classes
# -------------------------------------------------------------

class Directive(list):
    """Augmented lists that map to SMCL directives

    - SMCL directives are of the form {tag options: content}
    - The content goes in the embedded list, and can contain
      other directives or text strings
    - The .tag and .options attributes contain strings
    - The tag 'newline' is special as it maps a carrier return
    """

    def __init__(self, tag='', options='', items=None, num_line=None, line_content=None):

        list.__init__(self, [] if items is None else items)

        assert tag
        tag_aliases = {'*':'comment', '...':'nobreak'}
        self.tag = tag_aliases.get(tag, tag)

        self.options = options
        self.num_line = num_line
        self.line_content = line_content

    def textify(self):
        opt = '' if not self.options else '; {}'.format(self.options)
        return 'Directive({}{})'.format(self.tag, opt)

    def __repr__(self):
        return self.textify()

    def __str__(self):
        return self.textify()

# -------------------------------------------------------------

class Node(list):
    """Augmented lists that map to Document objects (tables, paragraphs, etc.)

    - Use Node() as a metaclass, don't create instances of 
      this but of the block/inline subclasses!!!
    - The content goes in the embedded list, and can contain
      other directives or text strings
    """

    def __init__(self, options=None, items=None):
        list.__init__(self, [] if items is None else items)

        self.options = options if options is not None else dict()
        self.link_id = None # Id for the next block to attach
        
        # Set margins based on active margins (unless already set in options)
        if 'margins' not in self.options:
            try:
                self.options['margins'] = self.active_margins
            except AttributeError: # No active margins
                pass

    def __repr__(self):
        opt = '{}'.format(repr(self.options)[1:-1] if self.options else '')
        name = type(self).__name__
        return '{}({})'.format(name, opt)

    def __str__(self):
        return repr(self)

    def append(self, item):
        if self.link_id:
            try:
                item.options['id'] = self.link_id
            except (TypeError, IOError):
                anchor = Anchor(options={'id':self.link_id})
                super(Node, self).append(anchor)
            self.link_id = None
        super(Node, self).append(item)

#def repr_trimmed(obj, maxlen=80):
#    text = repr(obj)[1:-1]
#    if len(text)>maxlen:
#        text = text[:maxlen-3] + '...'
#    return text

# -------------------------------------------------------------

# Create classes dynamically
def node_class(tag, opt=None):
    if opt is None:
        opt = {}
    return type(tag, (Node,), opt)
    #return type(tag, (Node,), {})

# Block Tags
SMCL = node_class('SMCL') # Root node
Break = node_class('Break') # <br/>
Heading = node_class('Heading')
Para = node_class('Para')

Table = node_class('Table')
Table.active_margins = Table.default_margins = [0, 31, 35, 0]
SyntaxTable = node_class('SyntaxTable')
SyntaxTable.active_margins = SyntaxTable.default_margins = [20]
TableHead = node_class('TableHead')
TableBody = node_class('TableBody')
TableFoot = node_class('TableFoot')
TableRow = node_class('TableRow')
TableData = node_class('TableData')

Meta = node_class('Meta')
Anchor = node_class('Anchor')

#Line = node_class('Line') # Default
#Rule = node_class('Rule') # Horizontal rule

# Inline Tags
#Text = node_class('Text') # Default

# -------------------------------------------------------------
# Functions
# -------------------------------------------------------------

def convert_scml(input_fn, output_fn):
    lines = read_smcl(input_fn)
    directives = parse_lines(lines)
    #walk(directives)
    smcl = build_tree(directives)
    walk(smcl)
    print('Tags:', num_tags)
    print('Directives:', num_directives)
    print('Ratio of done:', '{:4.3f}'.format(1 - num_directives / num_tags))

def read_smcl(fn):
    with open(fn, 'r') as f:
        smcl = f.readline().strip()
        assert smcl == '{smcl}', 'First line must be "{smcl}"'
        lines = [line.rstrip() for line in f]
    return lines

# -------------------------------------------------------------

def parse_lines(lines):
    
    smcl = Directive('smcl')

    # Count from 2 b/c of the first line with the {smcl} that was popped
    for num_line, line in enumerate(lines, 2):
        line = 'line:' + line + '}'
        line_directive, _ = parse_directive(num_line, line)
        smcl.extend(line_directive)
        newline = Directive('newline', num_line=num_line, line_content=line)
        smcl.append(newline)

    return smcl

def parse_directive(num_line, line, i=0, level=0):
    pos = 1 # {tag options : items} so 1=tag 2=options 3=items
    assert i < len(line)
    tag = None
    options = None
    items = []
    update = False

    j = i
    n = len(line)
    while i < n:
        c = line[i]
        # BUGBUG: When I do line[...].strip() I should not do it when tag is line

        if pos == 1 and c in (' ', ':', '}'):
            tag = line[j:i]
            update = True

        if pos == 2 and c in (':', '}'):
            options = line[j:i].strip()
            update = True

        if pos == 3 and (c == '}'):
            if i > j:
                d = Directive('text', line[j:i])
                items.append(d)
            update = True

        if update:
            update = False
            j = i + 1

            if c == ' ':
                pos = 2
            elif c == ':':
                pos = 3
            else:
                directive = Directive(tag, options, items, num_line=num_line, line_content=line)
                #print('    ' * level, directive)
                return directive, j
        elif (pos == 3) and (c == '{'):
            if i > j:
                d = Directive('text', line[j:i])
                items.append(d)
            directive, i = parse_directive(num_line, line, i+1, level+1)
            items.append(directive)
            j = i
        else:
            i += 1

# -------------------------------------------------------------

def walk(d, level=0):
    global num_tags
    global num_directives
    num_tags += 1

    if type(d)==Directive and d.tag=='text':
        print(' ' * 4 * (level), 'TextDirective("{}")'.format(d.options), sep='')
    elif isinstance(d,str):
        print(' ' * 4 * (level), 'Text("{}")'.format(d), sep='')
    else:
        num_directives += 1
        print(' ' * 4 * level, d, sep='')
        for dd in d:
            walk(dd, level+1)

# -------------------------------------------------------------

def build_tree(directives):
    
    smcl = SMCL() # Root
    nobreak = False

    remaining = 0

    while directives:
    
        d = directives[0]
        tag = d.tag
        options = d.options
        items = list(d)

        #print()
        #print(d)
        #print('Tag:', tag)
        #print('Options:', options)
        #print('Items:', items)

        # Meta directives
        if tag == 'comment' and options.startswith('*! '):
            build_meta_starbang(smcl, directives)

        elif tag.startswith('viewer'):
            build_meta_viewer(smcl, directives)

        # Margins (don't get saved into tree but affect subsequent blocks)
        elif tag in ('p2colset','p2colreset','synoptset'):
            build_margins(directives.pop(0))

        # Line breaks
        elif tag=='nobreak':
            directives.pop(0)
            nobreak = True

        elif nobreak and tag=='newline':
            directives.pop(0)
            nobreak = False

        # Marker tags are added as id's for the next block
        elif tag=='marker':
            build_marker(smcl, directives)
            smcl.link_id = options.strip()

        # Heading blocks
        elif tag=='title':
            build_heading(smcl, directives)

        # Para blocks (paragraphs)
        elif tag=='p' or pclass.match(tag):
            build_para(smcl, directives)

        # Table blocks (2 cols)
        elif tag=='p2col':
            build_table(smcl, directives)

        # Syntax Table blocks (3 cols)
        elif tag in ('synopthdr', 'synoptline', 'syntab', 'synopt', 'p2coldent'):
            build_syntab(smcl, directives)

        else:
            remaining += 1
            print('Discarded:', d, d.__dict__) # Need to add these cases
            directives.pop(0)

    print('REMAINING:', remaining)
    return smcl

def build_meta_starbang(smcl, directives):
    """Store *! comments in SMCL root node"""

    d = directives.pop(0)
    k, v = d.options[2:].strip().split(maxsplit=1)
    smcl.options.setdefault(k, []).append(v)

def build_meta_viewer(smcl, directives):
    """Store vieweralso and similar in SMCL root node"""

    d = directives.pop(0)
    k = d.tag[6:]
    v = shlex.split(d.options)
    smcl.options.setdefault(k, []).append(v)

def build_margins(d):
    if d.tag=='p2colset':
        Table.active_margins = [int(opt) for opt in d.options.split()]

    elif d.tag=='p2colreset':
        # Restore margins
        assert Table.default_margins is not None
        Table.active_margins = Table.default_margins

    elif d.tag=='synoptset':
        SyntaxTable.active_margins = d.options.split()

    else:
        # Note: there is no restore margins cmd for SyntaxTable
        assert 0, d.__dict__

def build_marker(smcl, directives):
    d = directives.pop(0)
    smcl.link_id = d.options.strip()

def build_heading(smcl, directives):
    d = directives.pop(0)
    node = Heading(items=list(d), options={'level':1})
    smcl.append(node)
    directives.pop(0) # Newline

def build_para(smcl, directives):
    d = directives.pop(0)
    opt = parse_options(d.options) if d.tag=='p' else d.tag[1:]
    items = []

    while directives:
        last_tag = d.tag
        d = directives.pop(0)
        if d.tag=='p_end' or d.tag==last_tag=='newline':
            # Pop newline if it follows {p_end}
            if directives[0].tag=='newline':
                directives.pop(0)
            # End the paragraph
            break

        elif d.tag=='newline':
            d = Directive('text', ' ')
        else:
            items.append(d)

    node = Para(items=items, options={'margins':opt})
    smcl.append(node)

def build_table(smcl, directives):
    opt = parse_options(directives[0].options)
    table = Table(items=[], options={'margins':opt})
    last_tag = None

    while directives:
        d = directives.pop(0)
        
        if d.tag=='p2col': # First column of a new row
            td1 = TableData(items=list(d))
            td2 = TableData(items=[])
            tr = TableRow(items=[td1, td2])
        elif d.tag==last_tag=='newline':
            break # End the paragraph
        elif (d.tag=='p_end'): # End of the second column, attach it to table
            table.append(tr)
        elif (last_tag=='p_end' and d.tag=='newline'):
            pass
        else: # Attach to second column of active row
            tr[-1].append(d)
        
        last_tag = d.tag

    smcl.append(table)

def build_syntab(smcl, directives):
    last_tag = None
    table_items = []
    tfoot = None

    while directives:
        d = directives.pop(0)

        if d.tag=='synopthdr': # {synopthdr} or {synopthdr:Col1}
            td1 = TableData(items=[d] if len(d) else ['options'], options={'colspan':2})
            td2 = TableData(items=['Description'])
            tr = TableRow(items=[td1, td2])
            thead = TableHead(items=[tr])
            table_items.insert(0, thead)
            
        elif d.tag=='synoptline':
            pass # we shouldn't need to set the table lines explicitly

        elif d.tag=='syntab': # {syntab:text} Sections inside a table, create a new table body
            td = TableData(items=list(d), options={'colspan':3}) # BUGBUG items or options
            tr = TableRow(items=[td], options={'style':'section'})
            tbody = TableBody(items=[tr])
            table_items.append(tbody)

        elif d.tag=='synopt': # {synopt text1} text2
            td1 = TableData(items=[''])
            td2 = TableData(items=list(d))
            td3_items = eat_row(directives)
            td3 = TableData(items=td3_items)
            tr = TableRow(items=[td1,td2,td3], options={'style':'normal'})

            if not table_items or type(table_items[-1])!=TableBody:
                table_items.append( TableBody(items=[]) )

            table_items[-1].append(tr)

        elif d.tag in ('p2colset','p2colreset','synoptset'):
            build_margins(d)

        elif d.tag==last_tag=='newline':
            break # End the paragraph

        elif d.tag=='newline':
            pass

        elif d.tag=='nobreak':
            pass

        elif d.tag=='p2coldent': # {p2coldent char text1} text2

            has_footnote = len(d)>0 and len(d[0].options.strip())>0 and len(d[0].options.strip()[:2].strip())==1

            td3_items = eat_row(directives)
            td3 = TableData(items=td3_items)

            if has_footnote:
                footnote = d[0].options.strip()[0]
                d[0].options = d[0].options.strip()[1:].strip()
                
                # Remove possible empty strings
                if not d[0].options:
                    d.pop(0)

                td1 = TableData(items=[footnote])
                td2 = TableData(items=list(d))
                tds = [td1, td2, td3]
            else:
                td2 = TableData(items=list(d), options={'colspan':2})
                tds = [td2, td3]            

            tr = TableRow(items=[td1, td2, td3], options={'style':'has_footnote'})

            if not table_items or type(table_items[-1])!=TableBody:
                table_items.append( TableBody(items=[]) )
                
            table_items[-1].append(tr)

        # Para blocks will be treated as footnotes
        elif d.tag=='p' or pclass.match(d.tag):

            if tfoot is None:
                tfoot = TableFoot(items=[])

            # We'll ignore the paragraph margins and just align with table, so we can discard the current directive
            foot_items = []
            while directives:
                d = directives.pop(0)
                if d.tag=='p_end': # Only use {p_end} to stop, not line breaks (and don't allow them!)
                    break # End the paragraph
                elif d.tag=='newline':
                    d = Directive('text', ' ')
                else:
                    foot_items.append(d)

            td = TableData(items=foot_items)    
            tr = TableRow(items=[td], options={'style':'footnote'})
            tfoot.append(tr)

        else:
            print('NOT USED:', str(d), list(d))
        
        last_tag = d.tag

    if tfoot is not None:
        table_items.append(tfoot)
    table = SyntaxTable(items=table_items)
    smcl.append(table)

def eat_row(directives):
    """Append until we encounter {p_end}"""
    ans = []
    while directives:
        d = directives.pop(0)
        if d.tag=='p_end':
            break
        else:
            ans.append(d)
    return ans

def parse_block_directives(directives):

    # Root of our tree
    smcl = SMCL()

    tag = None
    hold_break = False
    block = None # None (line blocks), Para (p pmore etc), Table (p2col), SyntaxTable

    p2col_active = p2col_default = [0, 31, 35, 0]
    synopt_active = synopt_default = [20]

    for d in directives:

        ##if not isinstance(d, str) and d.tag!='newline':
        ##    print(d, d.num_line)
        ##elif isinstance(d, str):
        ##    print('string:', d)

        # Directive syntax: {tag options : items}
        last_tag = tag
        tag = d.tag if type(d)==Directive else ''
        options = d.options if type(d)==Directive else None
        items = list(d) if type(d)==Directive else [d]
        
        # Meta directives into options of the SMCL root node
        if tag == 'comment' and options.startswith('*! '):
            k, v = options[2:].strip().split(maxsplit=1)
            smcl.options.setdefault(k, []).append(v)
        elif tag.startswith('viewer'):
            k = tag[6:]
            v = shlex.split(options)
            smcl.options.setdefault(k, []).append(v)



        # Line breaks (and when are they ignored)
        elif tag == 'nobreak':
            hold_break = True
        elif tag == 'newline' and hold_break:
            hold_break = False

  
        # Remaining and inline directives
        else:
            smcl.append(d)
            # TODO: Add these cases to fake containers (span maybe)

    return smcl

def parse_options(options):
    ans = [int(opt) for opt in options.split()]
    return ans

# -------------------------------------------------------------
# Main
# -------------------------------------------------------------

if __name__ == '__main__':

    # Parse opts
    # ...
    fn = r'C:\bin\Stata14\ado\base\b\bayesmh.sthlp'
    fn = r'c:\ado\plus\r\reghdfe.sthlp'
    fn = r'C:\Git\reghdfe\source\reghdfe.sthlp'

    # Call converter
    convert_scml(fn, '')

    # Write output
    # ...
