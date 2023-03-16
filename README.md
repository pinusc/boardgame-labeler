# Boardgame Labeler

# Running

The distributed binaries will automatically start a GUI. 

Running from source code follows standard python install:

```
$ git checkout https://github.com/pinusc/bgg-labeler.git
$ cd bgg-labeler
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

And then use the CLI:
```
$ ./bgg-labeler.py --help
```

# The Template

The label template **must be edited in [inkscape](https://inkscape.org/)**, as the templating system uses inkscape-specific xml tags.

The following properties are currently supported:

- name
- time
- player-n
- recommended-n (with subproperty not-recommended-n)
- weight
- avgscore
- rank
- tags 

Each of the textual properties is placed in a `text` tag labeled `$property-text`, inside a group labeled `$property-group`. For example, `weight-text` is a text element (containing a nameless tspan) inside `weight-group`.

The `name` property is special, as it supports multiline with a hack. Inside `name-group` there is a `name-text` which will be used for games with a name fitting in one line, and then two other text elements: `name-text-line1` and `name-text-line2`, which will instead be used for other elements. **It is important that the template contains the widest string allowed inside `name-text`**, as it will be used to determine which strings fit. This is hacky and I hate it, but it is how to do things in generated SVG.

Furthermore, if a `weight-bg` rectangel is found inside the `weight-group`, its fill color will be set to green-orange-red according to weight.

