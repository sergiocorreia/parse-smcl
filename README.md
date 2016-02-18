# PARSE-SMCL | Parse SMCL Help Files into Markdown and HTML

This project contains a Python script that cconverts a Stata help file in SMCL format
(usually with the .sthlp or .hlp extensions) into a proper HTML5 file.

It has multiple advantages compared to the current best alternative, [log2html](https://ideas.repec.org/c/boc/bocode/s422801.html), such as:

- Instead of copying the text in monospaced font and forgetting about most of the structure and meaning of the document, it preserves it.
- Links, anchors, headings, etc. are preserved and tagged, so it's very easy to change their look with CSS files
- Tables are automatically generated (standard tables as well as syntax tables)
- Navigation menus ("see also" and "jump to") are preserved
- In several cases, excerpts that represents code or ordered/unordered lists are translated into those.
- Because it uses CSS, you can change the styles a lot, and for instance add/remove heading numeration, add syntax coloring for code samples, etc.

## Usage

To use them, install Python 3 and then run `smcl2html.py`:

```
> smcl2html
usage: smcl2html.py [-h] [--output OUTPUT] [--adopath ADOPATH] [--standalone]
                    [--view] [--xml]
                    filename
```

A typical command line would be:

```
smcl2html.py somehelpfile.sthlp --adopath=C:\Stata13\ado\base --view --standalone
```

In this case, we are using three flags:

1. `adopath` is used to replace the `INCLUDE xyz` directives
2. `view` opens the resulting file in the browser
3. `standalone` wraps the output in a proper html file with links to a CSS file, so it looks nice

## Examples

Some examples include:
- [generate](http://scorreia.com/demo/generate.html) and [summarize](http://scorreia.com/demo/summarize.html) by StataCorp. They work without problems.
- [regress](http://scorreia.com/demo/regress.html) and [var](http://scorreia.com/demo/var.html) by StataCorp work well, but are missing a few directives.
- [reghdfe](http://scorreia.com/demo/reghdfe.html) and [hdfe](http://scorreia.com/demo/hdfe.html; work without problems.
- [psmatch2](http://scorreia.com/demo/psmatch2.html) by Ewin Leuven and Barbara Sianesi.
- [a2reg](http://scorreia.com/demo/a2reg.html) by Amine Ouazad. Even though it uses the old version of the help files, it still works.
- [bayesmh](http://scorreia.com/demo/bayesmh.html) by StataCorp. It uses many advanced (Stata 14) directives but is still quite readable.

(*Note: I do not own the copyright of the original files, they are used merely as an example of the use case*)

# Missing Features

Since this is work-in-progress, there are still a few limitations:

- The existing CSS is a proof-of-concept, and can be improved **a lot** more
- Some SMCL directives are not supported. For instance, `{c}` and `{space}`. However, these are relatively minor and easy to implement.
- Some advanced directives such as `{findalias}` are still not supported, but implementing them is quite doable
