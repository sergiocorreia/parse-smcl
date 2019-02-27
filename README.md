# PARSE-SMCL | Parse SMCL Help Files into Markdown and HTML

This project contains a Python script that converts Stata help files in SMCL format
(usually with the .sthlp or .hlp extensions) into proper HTML5 files.

It has multiple advantages to the current best alternative, [log2html](https://ideas.repec.org/c/boc/bocode/s422801.html), such as:

- Instead of copying the text in monospaced font and forgetting about most of the structure and meaning of the document, it preserves it.
- Links, anchors, headings, etc. are preserved and tagged, so it's very easy to change their look with CSS files.
- Tables are automatically generated (standard tables as well as syntax tables).
- Navigation menus ("see also" and "jump to") are preserved.
- When possible, fragments that contain enumerations are translated into actual or ordered/unordered lists. Similarly, code samples are translated into `pre` tags.
- Because it uses CSS, you can change the styles freely, and for instance add/remove heading numeration, add syntax coloring for code samples, etc.
- It uses responsive CSS so it's easier to read on tablets, large screens, etc. Similarly, it's easier to print.

## Sample Output

Some examples include:
- [generate](http://scorreia.com/demo/generate.html) and [summarize](http://scorreia.com/demo/summarize.html) by StataCorp. They work without problems.
- [regress](http://scorreia.com/demo/regress.html) and [var](http://scorreia.com/demo/var.html) by StataCorp work well, but are missing a few directives.
- [reghdfe](http://scorreia.com/demo/reghdfe.html) and [hdfe](http://scorreia.com/demo/hdfe.html); work without problems.
- [psmatch2](http://scorreia.com/demo/psmatch2.html) by Ewin Leuven and Barbara Sianesi.
- [a2reg](http://scorreia.com/demo/a2reg.html) by Amine Ouazad. Even though it uses the old version of the help files, it still works.
- [bayesmh](http://scorreia.com/demo/bayesmh.html) by StataCorp. It uses many advanced (Stata 14) directives but is still quite readable.

(*Note: I do not own the copyright of the original files, they are used merely as an example of the use case*)

## Usage

To use this script, just run `smcl2html.py`:

```
> smcl2html
usage: smcl2html.py [-h] [--output OUTPUT] [--adopath ADOPATH] [--standalone]
                    [--view] [--xml]
                    filename
```

The arguments and flags are:

- `filename`: the name of the file with .sthlp or .hlp extension.
- `output`: (optional) the name of the output file. If not given, same as filename but with a .html extension.
- `adopath`: the path of the `stata/ado/base` folder. Needed to replace the `INCLUDE xyz` directives.
- `standalone` instead of outputting a simple <div>-contained file, it will wrap the output with full html tags, including CSS and font links. Always use this option unless you want to embed the results into another page.
- `view`: opens the resulting file in the browser.
- `xml`: outputs an intermediate file, only for debug purposes.
- `help`: shows this information

A typical command line would be:

```
smcl2html.py somehelpfile.sthlp --adopath=C:\Stata13\ado\base --view --standalone
```

## Installation

1. Download the latest Python 3.x: https://www.python.org/downloads/
2. Install the `lxml` library: http://lxml.de/installation.html (or http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml for Windows; read [this](http://stackoverflow.com/questions/27885397/how-do-i-install-a-python-package-with-a-whl-file) if you get stuck).

## Missing Features

Since this is work-in-progress, there are still a few limitations:

- The existing CSS is a proof-of-concept, and can be improved **a lot** more
- Some SMCL directives are not supported. For instance, `{c}` and `{space}`. However, these are relatively minor and easy to implement.
- Some advanced directives such as `{findalias}` are still not supported, but implementing them is quite doable

