# Missing Features

## Missing components

- Align paragraph based on their margins (both standard ones such as `pmore` and custom ones such as `8-11-2-0` are set as classes). This is done for standard and most special cases, but for the unusual ones we should write directly on the style attribute.
- Add the contents of the version comment at the end? As "(version x.y date abc") (?)

## Missing directives

- `space`: just replace this with nonbreaking space?
- `findalias`: extract all instances in the official ADOs and run a script to replace them
- `comment` (in some cases): Comments in unexpected cases are ignored. Soln: Add them to the div as part of a "comment" attribute
- `c`: to add special chars such as spaces