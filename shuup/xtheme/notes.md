Notes on Xtheme architecture
============================

Parsing
-------

Three Jinja2 extensions manage parsing placeholders and default plugin layouts:

* `PlaceholderExtension`: `{% placeholder <NAME> %}` ... `{% endplaceholder %}`
  * Name can be any Jinja2 expression that can be folded into a constant, with the addition
    of bare variable names such as `name` meaning the same as `"name"`. This makes it slightly
    easier to write templates.
  * The body of this block is actually discarded; only the inner `column`, `row` and `plugin`
    directives have any meaning.  (A parser-time `Layout` object is created and populated during parsing
    of this block.)
* `LayoutExtension`: `{% row %}`..`{% endrow %}` and `{% column [SIZES] %}`..`{% endcolumn %}`
  * `row`s map to `LayoutRow` objects and `column`s map to `LayoutCell`s.
  * For a single-cell layout, these are not necessary.  `{% plugin %}` invocations without preceding
    `{% row %}`/`{% column %}` directives imply a single row and a single column.
* `PluginExtension`: `{% plugin <NAME> %}`..`{% endplugin %}`
  * The (optional) body of the `plugin` block is expected to be a Jinja2 AST that can be folded
    into a constant.  Generally this means a single block of text (`{% raw %}`/`{% endraw %}` is okay!).
  * The contents of the body, if set, must be valid [TOML](https://github.com/toml-lang/toml) markup.
    The TOML is parsed during Jinja2 parse time into a dict, which in turn is folded into the layout description
    object.  This means only the initial parsing of the template incurs whatever performance hit there is in
    parsing TOML; the Jinja2 bccache should take care of the rest.
    
In addition, there's a [special](http://i.imgur.com/dFpwkCb.jpg) postprocessing mechanism in
`shuup.xtheme.engine.XthemeTemplate` which processes HTML source to add injected additional resources.  This can't
be done via simple tags, as we don't want to go to two-or-more-pass rendering to first figure out a set of resources,
then render the actual content.

Runtime
-------

* Placeholders are rendered to static Bootstrap row>col* structures by `shuup.xtheme.rendering.PlaceholderRenderer`.
  * (Well, Bootstrap by default. Not like that's written in stone. :-) )

Editing
-------

* Editing placeholders is only available for placeholders declared in the "base" template, i.e.
  one that is not an `extend` parent.  Declaring placeholders in `include`d templates is fine,
  but their configuration will not be shared among different uses of the same include.
