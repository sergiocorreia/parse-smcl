# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------
import os
import re
import shlex

from lxml import etree # http://infohost.nmt.edu/~shipman/soft/pylxml/web/index.html
from lxml.builder import E


# -------------------------------------------------------------
# Custom tags
# -------------------------------------------------------------

class svg(etree.ElementBase):
    pass


# -------------------------------------------------------------
# Constants
# -------------------------------------------------------------

pclass = re.compile(r'p(std|see|hang\d?|more\d?|in\d?)')
opt_pat = re.compile("""
    (?P<outside>
        [^(]*
    )
    \(
    (?P<inside>
        [^)]*
    )
    \)
    """, re.VERBOSE)

# -------------------------------------------------------------
# Functions
# -------------------------------------------------------------

def parse_improvements(root):
    """Replace certain tables into lists or code blocks"""

    convert_code(root)

    for element in root.cssselect('table.standard'):
        if detect_ul(element):
            convert_ul(element)
        elif detect_ol(element):
            convert_ol(element)
    
    #ok_paras = {'std', 'see', 'hang', 'more', 'in', 'hang2', 'more2'}
    #for p in root.cssselect('p'):
    #    cl = p.attrib.get('class', None)
    #    if cl and cl not in ok_paras:
    #        print(cl)

    return root


def detect_ul(table):
    """Detect unordered list"""
    if not len(table):
        return False
    for tr in table:
        if len(tr)!=2:
            return False
        td1 = tr[0]
        if len(td1) or td1.text.strip()!='-':
            return False
    return True

def convert_ul(table):
    """Convert table to unordered list"""
    table.tag = 'ul'
    if table.get('class'):
        del table.attrib['class']
    for tr in table:
        tr.tag = 'li'
        tr.text = tr[1].text.lstrip()
        for el in tr[1]:
            tr.append(el)
        for td in tr[:2]:
            tr.remove(td)

def detect_ol(table):
    """Detect ordered list"""
    if not len(table):
        return False
    for tr in table:
        if len(tr)!=2:
            return False
        td1 = tr[0]

        # Only keep plausible ordered lists
        if td1.text is None:
            return False
        text = td1.text.strip()
        if not text or len(text)>3:
            return False
        if text[-1] not in ('.', ')'):
            return False
        if not text[:-1].isalpha() and not text[:-1].isdigit():
            return False
        if len(td1):
            return False
    return True

def convert_ol(table):
    """Convert table to ordered list"""
    table.tag = 'ol'
    if table.get('class'):
        del table.attrib['class']
    for tr in table:
        tr.tag = 'li'
        tr.text = tr[1].text.lstrip()
        for el in tr[1]:
            tr.append(el)
        for td in tr[:2]:
            tr.remove(td)

def convert_code(root):
    candidates = root.cssselect('p.hang2 > code.command')
    last_pos = -1
    last_valid_code = last_valid_pre = None
    for candidate in candidates:
        p = candidate.getparent()
        empty_tail = candidate.tail is None or not candidate.tail.strip()
        starts_with_dot = candidate.text and (candidate.text.startswith('. ') or candidate.text=='.')
        valid = p.text is None and empty_tail and candidate.text is not None and starts_with_dot

        if valid:
            pos = root.index(p)
            assert pos>last_pos
            candidate.text = candidate.text[2:] # Remove dot and add that in CSS so people can copy easily

            # Move to pre block
            if pos == last_pos + 1:
                append_to_tail(last_valid_pre[-1], '\n')
                candidate.set('class', 'language-stata')
                last_valid_pre.append(candidate)

                if p.tail is not None:
                    append_to_tail(last_valid_pre, p.tail)
                root.remove(p)

            # Start new pre block
            else:
                p.tag = 'pre'
                del p.attrib["class"]
                candidate.set('class', 'language-stata')
                last_valid_code = candidate
                last_valid_pre = p
                last_pos = pos

def parse_inlines(root, current_file):
    assert root.tag=='div'
    valid_tags = ('h1', 'h2', 'h3', 'h4', 'p', 
                  'table', 'thead', 'tbody', 'tfoot', 'tr', 'td',
                  'a', 'nav', 'ul', 'li', 'hr',
                  'code', 'kbd', 'var', 'samp', 'br', 'span', 'strong', 'b')

    custom_tags = ('newvar', 'var', 'vars', 'depvar', 'depvars', 'indepvars',
                   'varname', 'varlist', 'depvarlist',
                   'ifin', 'weight', 'dtype')

    formatting_directives = ('sf', 'it', 'bf',
                             'input', 'error', 'result', 'text',
                             'inp', 'err', 'res', 'txt',
                             'hilite', 'hi', 'ul')

    for element in root.iterdescendants():
        tag = element.tag
        opt = element.get('options')
        if tag in valid_tags:
            continue
        
        if tag == 'cmd' and (element.text or len(element)):
            parse_cmd(element)
        elif tag == 'cmdab':
            parse_cmdab(element)
        elif tag == 'opt':
            parse_opt(element, current_file)
        elif tag == 'opth':
            parse_opt(element, current_file, help=True)
        elif tag == 'help':
            parse_browse(element, current_file, is_help=True)
        elif tag == 'helpb':
            parse_browse(element, current_file, is_help=True, is_bold=True)
        elif tag == 'manhelp':
            parse_browse(element, current_file, is_help=True, is_man=True)
        elif tag == 'manhelpi':
            parse_browse(element, current_file, is_help=True, is_man=True, is_italics=True)
        elif tag == 'browse':
            parse_browse(element, current_file)
        elif tag == 'manpage':
            parse_pdf_link(element, is_manpage=True)
        elif tag == 'mansection':
            parse_pdf_link(element, is_mansection=True)
        elif tag == 'manlink':
            parse_pdf_link(element, is_manlink=True)
        elif tag == 'manlinki':
            parse_pdf_link(element, is_manlink=True, is_italics=True)
        elif tag == 'break':
            parse_break(element)
        elif tag in custom_tags:
            parse_custom(element)
        elif tag in formatting_directives and (element.text or len(element)):
            parse_formatting(element)
        elif tag == 'hline' and opt is not None:
            parse_hline(element, opt)
        elif tag == 'stata':
            parse_stata(element, opt)
        elif tag == 'bind':
            parse_bind(element)
        else:
            print('UNUSED INLINE:', etree.tostring(element))
            element.tag = 'span'
            if element.text is None:
                element.text = ''
            element.text = '{{{} {}{}{}}}'.format(tag, opt, ':' if element.text else '', element.text)

    return root

def parse_blocks(root, current_file):

    # New tree
    div = etree.Element('div')
    div.set('class', 'smcl')
    div.text = root.text
    div.tail = root.tail

    # Title
    title = etree.SubElement(div, 'h1')
    title.text = 'Help for ' + current_file

    # Navigation menus
    nav_internal = etree.Element('nav', id='table-of-contents')
    nav_internal.set('class', 'smcl-nav')
    ul_internal = etree.SubElement(nav_internal, 'ul')
    etree.SubElement(ul_internal, 'li', attrib={'class':'description'}).text = 'Jump to:'
    div.append(nav_internal)

    nav_external = etree.Element('nav', id='related-content')
    nav_external.set('class', 'smcl-nav')
    ul_external = etree.SubElement(nav_external, 'ul')
    etree.SubElement(ul_external, 'li', attrib={'class':'description'}).text = 'Also see:'
    div.append(nav_external)
    
    # Misc
    table_margins = {'active':'', 'default': [0, 31, 35, 0]}
    syntab_margins = {'active':'', 'default': [20]}
    nobreak = False
    link_id = None
    remaining = 0

    while len(root):
        element = root[0]
        tag = element.tag
        opt = element.get('options')

        syntab_bug = tag=='p2col' and len(root)>4 \
            and root[1].tag=='p_end' and root[2].tag=='newline' and root[3].tag=='synopt'

        # Meta directives
        if tag == 'comment' and opt.startswith('*! '):
            parse_starbang(div, element, opt)

        elif tag == 'viewerjumpto':
            parse_viewer(ul_internal, element, opt, current_file)

        elif tag == 'vieweralsosee':
            parse_viewer(ul_external, element, opt, current_file)

        elif tag == 'viewerdialog':
            remove(element, div, nested=True) # Can't access dialog tabs

        # Margins (don't get saved into tree but affect subsequent blocks)
        elif tag in ('p2colset','p2colreset','synoptset'):
            parse_margins(table_margins, syntab_margins, element, opt, div)

        # Line breaks
        elif tag == 'nobreak':
            nobreak = True
            remove(element, div, nested=True)

        elif nobreak and tag == 'newline':
            nobreak = False
            remove(element, div, nested=True)

        # Marker tags are added as id's for the next block
        elif tag == 'marker':
            link_id = opt.strip()
            remove(element, div, nested=True)

        # Heading blocks (title and dlgtab)
        elif tag in ('title', 'dlgtab'):
            parse_heading(div, element, opt)
            link_id = add_id(div, link_id)

        # Horizontal rules
        elif tag == 'hline':
            parse_thematic_break(div, element)

        # Para blocks (paragraphs)
        elif tag == 'p' or pclass.match(tag):
            parse_para(div, element, opt)
            link_id = add_id(div, link_id)

        # Table blocks (2 cols)
        elif tag == 'p2col' and not syntab_bug:
            parse_table(div, element, opt, table_margins, syntab_margins)
            link_id = add_id(div, link_id)

        # Syntax Table blocks (3 cols)
        elif tag in ('synopthdr', 'synoptline', 'syntab', 'synopt', 'p2coldent') or syntab_bug:
            if syntab_bug:
                element.tag = 'syntab'
                root.remove(root[1])
            parse_syntab(div, element, opt, table_margins, syntab_margins)
            link_id = add_id(div, link_id)

        elif tag == 'newline':
            if element.tail is None:
                element.tail = ''
            remove(element, div, nested=True, prefix='\n')

        elif tag =='col':
            parse_col(div, element, opt)
            link_id = add_id(div, link_id)
            
        else:
            #print('UNUSED BLOCK', etree.tostring(element))
            div.append(element)
            remaining += 1

    # Remove navigation menus if not needed
    if len(ul_internal)==1:
        remove(nav_internal, div, nested=True) # Attach to previous element div<nav
    if len(ul_external)==1:
        remove(nav_external, div, nested=True) # Attach to previous element div<nav

    #print('[TODO] Remaining elements:', remaining)
    return div

# -------------------------------------------------------------

def parse_starbang(div, element, opt):
    """Store *! comments in SMCL root node"""
    k, v = opt[2:].strip().split(maxsplit=1)
    div.set(k, v)
    remove(element, div, nested=True)

def parse_viewer(ul, element, opt, current_file):
    assert opt is not None, etree.tostring(element)
    try:
        text, link = shlex.split(opt)
    except ValueError:
        print(etree.tostring(element))
        assert 0
    if link != '--':
        li = etree.SubElement(ul, 'li', attrib={'class':'link'})

        if link.startswith('manpage '):
            href = resolve_pdf_link(link.split(' ', maxsplit=1)[1], is_manpage=True)
        elif link.startswith('mansection '):
            href = resolve_pdf_link(link.split(' ', maxsplit=1)[1], is_mansection=True)
        elif link.startswith('manlink '):
            href = resolve_pdf_link(link.split(' ', maxsplit=1)[1], is_manlink=True)
        elif link.startswith('manlinki '):
            href = resolve_pdf_link(link.split(' ', maxsplit=1)[1], is_manlinki=True)
        else:
            href = fix_link(link, current_file)

        a = etree.SubElement(li, 'a', href=href)
        a.text = text

    remove(element, ul, nested=False)

def parse_margins(table_margins, syntab_margins, element, opt, destination):
    if element.tag=='p2colset':
       table_margins['active'] = [int(subopt) for subopt in opt.split()]
    elif element.tag=='p2colreset':
        # Restore margins
       table_margins['active'] = table_margins['default']
    elif element.tag=='synoptset':
        syntab_margins['active'] = opt.split()
    remove(element, destination, nested=True)

def parse_heading(div, element, opt):
    element.tag ='h2' if element.tag=='title' else 'h3'
    
    if opt:
        element.set('margins', opt.strip())

    # Discard first newline after title, use subsequent to leave larger bottom margins
    eat_blank_lines(element, num_discard=1)
    
    div.append(element) # Must be at the end

def parse_thematic_break(div, element):
    # the <hr> element is now more akin to a thematic break:
    # http://html5doctor.com/small-hr-element/
    element.tag = 'hr'
    eat_blank_lines(element, num_discard=1)
    div.append(element) # Must be at the end

def parse_para(div, para, opt):
    if opt:
        del para.attrib['options']
    opt = parse_options(opt, 'para') if para.tag=='p' else para.tag[1:]
    para.tag = 'p'
    para.set('class', opt)
    move_tail_inside(para)
    root = para.getparent()
    last_was_empty = False

    while len(root)>1:
        element = root[1]
        tag = element.tag

        # End the paragraph
        if tag == 'p_end' or (tag == 'newline' and last_was_empty):
            safe_remove(element, para)
            # Pop newline if it follows {p_end}
            if len(root)>1 and root[1].tag=='newline':
                remove(root[1], para, nested=False)
            break

        last_was_empty = False

        # Replace new lines with spaces
        if tag == 'newline':
            if element.tail is None or not len(element.tail.strip()):
                last_was_empty = True
                element.tail = ''

            remove(element, para, nested=True, prefix = ' ')
        else:
            para.append(element)

    # Remove leading spaces; no real effect
    if para.text is not None:
        para.text = para.text.lstrip()

    ## We can use subsequent newlines to leave wider bottom margins
    eat_blank_lines(element, num_discard=0)
    div.append(para)

def parse_table(div, element, opt, table_margins, syntab_margins):
    root = element.getparent()
    table = etree.Element('table') #, border='1')
    table.set('class', 'standard')
    last_tag = None

    if opt is not None:
        opt = parse_options(opt, 'table')
        table.set('margins', str(opt))
        del element.attrib['options']

    last_was_empty = False

    while len(root):
        element = root[0]
        tag = element.tag
        opt = element.get('options')

        # First column of a new row
        if tag == 'p2col': 
            tr = etree.SubElement(table, 'tr')

            td1 = element
            td1.tag = 'td'
            tr.append(td1) # First column
            td2 = etree.SubElement(tr, 'td') # Second column
            
            if td1.tail is not None:
                td2.text = td1.tail
                td1.tail = None

        # END OF TABLE?
        elif tag==last_tag=='newline' and last_was_empty:
            if len(root)==1 or root[1].tag not in ('p_end', 'p2col', 'p2colset', 'p2colreset'):
                safe_remove(element, table)
                break
            else:
                safe_remove(element, table[-1] if len(table) else table)

        # End of the second column
        elif tag == 'p_end': 
            remove(element, td2)

        # Update margins
        elif tag in ('p2colset','p2colreset','synoptset'):
            parse_margins(table_margins, syntab_margins, element, opt, table)
        
        elif tag=='newline':
            if element.tail is None or not len(element.tail.strip()):
                last_was_empty = True
            else:
                last_was_empty = False


            td2 = table[-1][1]
            if element.tail is None:
                element.tail = ''
            remove(element, table[-1][1], nested=True, prefix=' ')

        elif tag=='nobreak':
            remove(element, table, nested=True)

        # Attach to second column of active row
        else:
            table[-1][1].append(element)
        
        last_tag = tag
        if tag!='newline': last_was_empty = False

    # We can use subsequent newlines to leave wider bottom margins
    eat_blank_lines(table)
    div.append(table)

def parse_syntab(div, element, opt, table_margins, syntab_margins):

    root = element.getparent()
    table = etree.Element('table') #, border='1')
    table.set('class', 'syntab')
    tfoot = etree.Element('tfoot')
    last_tag = None

    while len(root):
        element = root[0]
        tag = element.tag
        opt = element.get('options')

        # TABLE HEADINGS - {synopthdr} or {synopthdr:Col1}
        if tag=='synopthdr':
            
            thead = etree.SubElement(table, 'thead')
            tr = etree.SubElement(thead, 'tr')

            td1 = element
            td1.tag = 'td'
            if not len(td1) and td1.text is None:
                td1.text = 'Options'
            td1.set('colspan', '2')
            tr.append(td1) # First column

            td2 = etree.SubElement(tr, 'td') # Second column
            td2.text = 'Description'
            if td1.tail is not None:
                td2.text += td1.tail
                td1.tail = None

        elif tag=='synoptline':
            pass # we shouldn't need to set the table lines explicitly
            safe_remove(element, table[-1] if len(table) else table)

        # SECTION HEADINGS - {syntab:text}
        elif tag=='syntab':
            tbody = etree.SubElement(table, 'tbody')
            tr = etree.SubElement(tbody, 'tr', {'class': 'section'})
            td = element
            td.tag = 'td'
            td.set('colspan', '3')
            move_tail_inside(td) # BUGBUG (not what Stata does)
            tr.append(td) # Only column

        # STANDARD ROWS - {synopt:text1}text2
        elif tag=='synopt':

            if not (len(table) and table[-1].tag=='tbody'):
                tbody = etree.SubElement(table, 'tbody')

            tr = etree.SubElement(tbody, 'tr')
            
            # Column 1 is empty
            etree.SubElement(tr, 'td', {'class': 'normal'})

            # Column 2 is text1
            td2 = element
            td2.tag = 'td'
            tr.append(td2)

            # Column 3 is text2
            td3 = etree.Element('td')
            if td2.tail is not None:
                td3.text = td2.tail
                td2.tail = None
            eat_row(root, td3)
            tr.append(td3)

        # MARGIN DIRECTIVES
        elif tag in ('p2colset','p2colreset','synoptset'):
            parse_margins(table_margins, syntab_margins, element, opt, table)

        # END OF TABLE?
        elif tag==last_tag=='newline':
            if len(root)==1 or root[1].tag not in ('syntab', 'synopt'):
                safe_remove(element, table)
                break # End the table
            else:
                safe_remove(element, table[-1] if len(table) else table)

        elif tag=='newline':
            # Add a space with newline
            add_leading_space_to_tail(element)
            safe_remove(element, table[-1] if len(table) else table)

        elif tag=='nobreak':
            safe_remove(element, table[-1] if len(table) else table)

        # {p2coldent char text1}text2
        elif tag=='p2coldent':

            if not (len(table) and table[-1].tag=='tbody'):
                tbody = etree.SubElement(table, 'tbody')
            
            tr = etree.SubElement(tbody, 'tr')

            text = element.text.strip() if element.text is not None else ''
            has_footnote = len(text) and len(text[:2].strip())==1
            if has_footnote:
                tr.set('style', 'has_footnote')
                footnote = text[:2].strip()
                element.text = text[2:].strip()
                td1 = etree.SubElement(tr, 'td')
                td1.text = footnote

            td2 = element
            td2.tag = 'td'
            tr.append(td2)

            if not has_footnote:
                td2.set('colspan', '2')

            # Column 3 is text2
            td3 = etree.Element('td')
            if td2.tail is not None:
                td3.text = td2.tail
                td2.tail = None
            eat_row(root, td3)
            tr.append(td3)

        # Para blocks will be treated as footnotes
        elif tag=='p' or pclass.match(tag):

            tr = etree.SubElement(tfoot, 'tr', {'class': 'footnote'})
            td = etree.SubElement(tr, 'td', colspan='3')
            remove(element, td) # Will always append to text b/c td.text is empty

            # We'll ignore the paragraph margins and just align with table, so we can discard the current directive
            while len(root):
                subelement = root[0]
                subtag = subelement.tag
                subopt = subelement.get('options')

                if subtag=='p_end': # Only use {p_end} to stop, not line breaks (and don't allow them!)
                    safe_remove(subelement, tr)
                    break # End the paragraph

                elif subtag=='newline':
                    if subelement.tail is None:
                        subelement.tail = ''
                    remove(subelement, td, nested=True, prefix=' ')
                else:
                   td.append(subelement)

        else:
            print('UNUSED IN SYNTAB:', etree.tostring(element))
            safe_remove(element, table[-1] if len(table) else table)
        
        last_tag = tag

    if len(tfoot):
        table.append(tfoot)
    
    # We can use subsequent newlines to leave wider bottom margins
    eat_blank_lines(table)

    div.append(table)

def parse_col(div, para, opt):

    def calculate_offset(opt):
        return opt * 0.5

    assert opt and opt.isdigit()
    opt = int(opt)
    para.tag = 'p'
    move_tail_inside(para)
    root = para.getparent()

    offset = calculate_offset(opt)
    if offset:
        para.set('style', 'padding-left: {}rem;'.format(offset))
    del para.attrib['options']

    while len(root)>1:
        element = root[1]
        tag = element.tag
        opt = int(element.get('options')) if tag == 'col' else None

        # End the paragraph
        if tag == 'newline':
            safe_remove(element, para)
            break

        # Attach
        elif tag == 'col':
            element.tag = 'span'
            delta = calculate_offset(opt) - offset # New Offset - Old Offset
            offset += delta # This is just New Offset
            element.set('style', 'padding-left: {}rem;'.format(offset))
            del element.attrib['options']
            para.append(element)
        else:
            para.append(element)

    div.append(para)

# -------------------------------------------------------------

def parse_cmd(element):
    element.tag = 'code'
    element.attrib['class'] = 'command'

def parse_cmdab(element):
    element.tag = 'code'
    element.attrib['class'] = 'command'

    # Deal with abbreviation
    split_text = element.text.split(sep=':', maxsplit=1)
    if len(split_text)==2:
        element.text = ''
        abbrev = etree.Element('u')
        abbrev.text = split_text[0]
        abbrev.tail = split_text[1]
        element.insert(0, abbrev)

def parse_opt(element, current_file, help=False):
    assert len(element)==0, "An {opt} directives cannot contain other directives: " + etree.tostring(element).decode('utf8')

    element.tag = 'code'
    element.attrib['class'] = 'command'

    # Move options to text for simplicity
    if element.text is None:
        element.text = ''
    if element.get('options') is not None:
        element.text = element.get('options') + (':' + element.text if element.text else '')

    # Create subelements contained inside parens
    if '(' in element.text:
        m = opt_pat.match(element.text)
        element.text = m.group('outside') + '('

        inside = m.group('inside')
        sep = ',' if ',' in inside else '|'
        inside = inside.split(sep)

        for subtext in inside:
            subelement = etree.SubElement(element, 'var')

            if help:
                split_subtext = subtext.split(sep=':', maxsplit=1)
                if len(split_subtext)==2:
                    link = split_subtext[0]
                    subtext = split_subtext[1]
                else:
                    link = subtext

                link = 'help ' + link
                a = etree.SubElement(subelement, 'a', href=fix_link(link, current_file))
                a.text = subtext
            else:
                subelement.text = subtext

            subelement.tail = ','

        element[-1].tail = ')'

    # Deal with abbreviation
    split_text = element.text.split(sep=':', maxsplit=1)
    if len(split_text)==2:
        element.text = ''
        abbrev = etree.Element('u')
        abbrev.text = split_text[0]
        abbrev.tail = split_text[1]
        element.insert(0, abbrev)

def resolve_pdf_link(link, is_manlink=False, is_mansection=False, is_manpage=False):
    assert is_mansection + is_manpage + is_manlink == 1
    page = ''
    if is_manlink:
        href = link.lower()
        for char in (' ', '`', "'", '#', '$', '~', '{', '}', '[', ']'):
            href = href.replace(char, '')
    elif is_mansection:
        href = link.replace(' ', '').lower()
    elif is_manpage:
        href, page = link.split(maxsplit=1)
        page = page.strip()
        assert page.isdigit()
    href = fix_link('pdf ' + href, '', page=page)
    return href

def parse_pdf_link(element, is_mansection=False, is_manpage=False, is_manlink=False, is_italics=False):
    """Parse {mansection} {manpage} {manlink} {manlinki}"""
    assert is_mansection + is_manpage + is_manlink == 1
    element.tag = 'a'
    link = element.get('options')
    del element.attrib['options']

    if is_manlink:
        assert element.text is None

    # Resolve link
    href = resolve_pdf_link(link, is_manlink=is_manlink, is_mansection=is_mansection, is_manpage=is_manpage)

    element.set('href', href)

    text = element.text if element.text is not None else link
    element.text = None

    if is_manlink:
        bold = etree.SubElement(element, 'b')
        manual, entry = link.split(maxsplit=1)
        if is_italics:
            bold.text = '[{}]'.format(manual)
            italics = etree.SubElement(bold, 'i')
            italics.text = entry
        else:
            bold.text = '[{}] {}'.format(manual, entry)
    else:
        element.text = text

def parse_browse(element, current_file, is_help=False, is_bold=True, is_man=False, is_italics=False):
    """Parse {help} {helpb} {browse} {manhelp} {manhelpi}"""
    element.tag = 'a'
    link = element.get('options')
    del element.attrib['options']

    if is_man:
        link, manual = link.split(maxsplit=1)
        is_bold = True
        extra = ' ' + (element.text if element.text is not None else link)
        element.text = '[' + manual + ']'
    element.attrib['class'] = 'command'
    prefix = 'help ' if is_help else ''
    element.set('href', fix_link(prefix + link, current_file))

    if element.text is None and len(element)==0:
        element.text = link

    if is_bold: # {helpb} and first part of {manhelp[i]}
        bold = etree.SubElement(element, 'b')
        bold.text = element.text
        element.text = None

    if is_man: # {manhelp} and {manhelpi}
        if is_italics:
            italics = etree.SubElement(element, 'i')
            italics.text = extra
        else:
            bold.tail = extra

def parse_break(element):
    assert len(element)==0
    if element.text is not None:
        append_to_tail(element, element.text)
        element.text = None
    element.tag = 'br'

def parse_custom(element):
    element.attrib['class'] = 'command'
    shortcuts = {'var': 'varname', 'vars': 'varlist', 'depvars': 'depvarlist'}
    tag = element.tag
    tag = shortcuts.get(tag, tag)

    standard_list = ('newvar', 'varname', 'varlist', 'depvar', 'depvarlist', 'indepvars')
    element.tag = 'a' if tag in standard_list else 'span'

    if tag in standard_list:
        element.set('href', fix_link('help ' + tag, ''))
        element.text = tag + element.text if element.text else tag

    elif tag=='ifin':
        element.text = '['
        var = etree.SubElement(element, 'var')
        a = etree.SubElement(var, 'a', href=fix_link('help if', ''))
        a.text = 'if'
        var.tail = '] ['

        var = etree.SubElement(element, 'var')
        a = etree.SubElement(var, 'a', href=fix_link('help in', ''))
        a.text = 'in'
        var.tail = ']'

    elif tag=='weight':
        element.text = '['
        var = etree.SubElement(element, 'var')
        a = etree.SubElement(var, 'a', href=fix_link('help weight', ''))
        a.text = 'weight'
        var.tail = ']'

    elif tag=='dtype':
        element.text = '['
        var = etree.SubElement(element, 'var')
        a = etree.SubElement(var, 'a', href=fix_link('help datatypes', ''))
        a.text = 'type'
        var.tail = '] ['

    else:
        raise Exception

def parse_formatting(element):
    shortcuts = {'inp': 'input', 'err': 'error', 'res': 'result', 'hi': 'hilite'}
    tag = shortcuts.get(element.tag, element.tag)

    if tag == 'input':
        element.tag = 'kbd' # for keyboard or command line input
    elif tag == 'error':
        element.tag = 'samp'
        element.set('class', 'error')
    elif tag == 'result':
        element.tag = 'samp'
        element.set('class', 'result')
    elif tag == 'hilite':
        element.tag = 'strong' # strong is like bold but semantic, fits with the defn in the smcl help file
    elif tag == 'ul':
        element.tag = 'u'
    elif tag == 'it':
        # Not sure if 'var', 'i', or 'em' are better
        element.tag = 'var'
        element.set('class', 'command')
    elif tag == 'bf':
        element.tag = 'b'
    elif tag == 'sf':
        element.tag = 'span'
        element.set('class', 'no-format')
    else:
        assert 0

def parse_hline(element, options):
    # Do not confuse with parse_thematic_break !!
    # This is for inline hlines
    element.tag = 'span'
    if options=='2':
        del element.attrib['options']
        element.append(etree.Entity('#8212')) # Decimal code for em dash

def parse_stata(element, opt):
    """Transform to p.hang2 > code.command so its picked by parse_improvements"""
    del element.attrib['options']
    parent = element.getparent()
    if parent.tag=='div':
        element.tag = 'p'
        element.set('class', 'hang2')
        element.text = None
        code = etree.SubElement(element, 'code')
        code.text = '. ' + opt.strip('"')
        code.set('class', 'command')
    elif parent.tag=='p' and parent.text is None and len(parent)==1:
        if parent.get('style'):
            del parent.attrib['style']
        parent.set('class', 'hang2')
        element.tag = 'code'
        element.set('class', 'command')
        element.text = '. ' + opt.strip('"')
    else:
        element.tag = 'code'
        element.set('class', 'command')
        element.text = '. ' + opt.strip('"')

def parse_bind(element):
    element.tag = 'span'
    element.set('class', 'nowrap') # .nowrap { white-space: nowrap; }

# -------------------------------------------------------------

def append_to_tail(element, text):
    if element.tail is None:
        element.tail = text
    else:
        element.tail += text

def append_to_text(element, text):
    if element.text is None:
        element.text = text
    else:
        element.text += text

def move_tail_inside(element):
    if element.tail is not None:
        if len(element):
            append_to_tail(element[-1], element.tail)
        else:
            append_to_text(element, element.tail)
        element.tail = None


def safe_remove(element, destination):
    if element.tail is not None:
        # Always append to tail; appending to text might be wrong
        # as the prev. element might be e.g. a title and then you add it inside
        append_to_tail(destination, element.tail)
    element.getparent().remove(element)

def remove(element, destination, nested=False, prefix=''):
    if element.tail is not None:
        try:
            pos = destination.index(element) - 1 # Previous element
        except ValueError:
            pos = -1 # Last element

        if len(destination) == 0 or pos == 0:
            append_to_text(destination, prefix + element.tail)
        elif nested:
            append_to_tail(destination[pos], prefix + element.tail)
        else:
            append_to_tail(destination, prefix + element.tail)
    element.getparent().remove(element)

def fix_link(link, current_file, page=''):
    is_help = link.startswith('help ')
    is_pdf = link.startswith('pdf ')
    if is_help:
        link = link[5:]
    elif is_pdf:
        link = link[4:]

    if '##' in link:
        base, anchor = link.split('##')
        if base==current_file:
            return '#' + anchor
        else:
            return link
    elif is_help:
        return 'http://www.stata.com/help.cgi?' + link
    elif is_pdf:
        if page:
            page = '#page={}'.format(page)
        return 'http://www.stata.com/manuals14/{}.pdf{}'.format(link, page)
    else:
        link = link.strip('"')
        return link

def eat_blank_lines(element, num_discard=0):
    margin_bottom = 0
    num_discarded = 0

    while True:
        active_element =  element.getnext()
        
        if active_element is not None and active_element.tag=='newline':
            if num_discarded<num_discard:
                num_discarded += 1
            else:
                margin_bottom += 1

            safe_remove(active_element, element)
        else:
            break

    if margin_bottom:
        element.set('margin_bottom', str(margin_bottom))

def parse_options(options, block):
    if options is None:
        options = ''
    ans = [int(opt) for opt in options.split()]
    if block=='para':

        # Ensure four elements
        ans.extend([0,0,0,0])
        ans = ans[:4]

        # Ignore redundant margins
        if sum(ans)==0:
            ans = []

        # Transform to a string
        ans = '-'.join(str(el) for el in ans)

    return ans

def eat_row(root, destination):
    """Append until we encounter {p_end}"""

    while len(root)>0:
        element = root[0]

        # Stop on p_end
        if element.tag=='p_end':
            remove(element, destination, nested=False)
            break
        # Replace newlines with spaces
        elif element.tag=='newline':
            add_leading_space_to_tail(element)
            remove(element, destination, nested=True)
        else:
            destination.append(element)

def add_id(div, link_id):
    if len(div)==0:
        return link_id
    if link_id is None:
        return None

    element = div[-1]
    element.set('id', link_id)

    return None

def add_leading_space_to_tail(element):
    tail = element.tail if element.tail is not None else ''
    element.tail = ' ' + tail

