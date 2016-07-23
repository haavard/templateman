#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import collections

import click
import jinja2


def find_names(root):
    """
    Find all names in an AST that should be provided when rendering.
    """
    names = []
    seen_names = set()

    # find all names with context "load"
    for node in root.find_all(jinja2.nodes.Name):
        if node.ctx == "load" and node.name not in seen_names:
            names.append(node.name)
        seen_names.add(node.name)

    return names


def find_iterables(root):
    """
    Find all names that are used as iterables in the template.
    """
    iterables = set()

    # identify names that are iterables
    for for_node in root.find_all(jinja2.nodes.For):
        if type(for_node.iter) == jinja2.nodes.Name:
            iterables.add(for_node.iter.name)

    return iterables


def find_default_values(root):
    """
    Find default values from occurrences of the 'default' filter.
    """
    defaults = collections.defaultdict(str)

    # find names with default values
    for filter_node in root.find_all(jinja2.nodes.Filter):
        if filter_node.name == "default" \
         and type(filter_node.node) == jinja2.nodes.Name \
         and type(filter_node.args[0]) == jinja2.nodes.Const:
            defaults[filter_node.node.name] = filter_node.args[0].value

    return defaults


@click.command(context_settings={"help_option_names": ("-h", "--help")})
@click.argument("template_name")
@click.argument("output_file", required=False, type=click.File(mode="w"))
@click.option("--template-dir", "-d", multiple=True,
              type=click.Path(file_okay=False, resolve_path=True),
              help="Specify directories used to find template files.")
@click.option("--builtin", is_flag=True, default=False,
              help="Look for built-in templates before looking in other "
              "directories.")
@click.option("--interactive/--batch", default=True,
              help="Interactively prompt for template values, or use default "
              "values for all fields.")
def main(template_name, output_file, template_dir, builtin, interactive):
    """
    Render TEMPLATE_NAME to OUTPUT_FILE or stdout.

    TEMPLATE_NAME must be a Jinja2 template file either included with this
    program or located in any of the template search directories.

    \b
    Templates are looked for in the following locations:
        1. Directories specified with the -d option
        2. ~/.templateman/
        3. Built-in templates included with the program
    """
    search_dirs = template_dir + (os.path.expanduser("~/.templateman/"),)

    fs_loader = jinja2.FileSystemLoader(searchpath=search_dirs,
                                        followlinks=True)
    pkg_loader = jinja2.PackageLoader("templateman", "templates")

    loaders = (pkg_loader, fs_loader) if builtin else (fs_loader, pkg_loader)

    loader = jinja2.ChoiceLoader(loaders)
    environment = jinja2.Environment(loader=loader, trim_blocks=True)

    # load template
    try:
        template = environment.get_template(template_name)
        source = loader.get_source(environment, template_name)
    except jinja2.exceptions.TemplateNotFound:
        raise click.FileError(template_name, hint="template not found")
    except jinja2.exceptions.TemplateSyntaxError as e:
        err = "Syntax error in template {}: {}".format(template_name, e)
        raise click.ClickException(err)

    # extract user-provided names from template
    ast = environment.parse(source)
    names = find_names(ast)
    iterables = find_iterables(ast)
    defaults = find_default_values(ast)

    # prompt user for values
    values = {}
    if interactive:
        for name in names:
            value = click.prompt(name, default=defaults[name], err=True)
            if name in iterables:
                values[name] = list(re.split("\s+", value))
            else:
                values[name] = value

    # output rendered template
    click.echo(template.render(values), output_file)


if __name__ == "__main__":
    main()
