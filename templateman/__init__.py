import os
import sys
import re
import collections

import click
import jinja2

DEFAULT_TEMPLATE_DIR = os.path.expanduser("~/.templates/")


def find_user_bindings(root):
    """
    Find all names in an AST that should be provided when rendering.

    Return a list of names, a set of names that should be iterable, and a
    dictionary of values extracted from the Jinja 'default' filter.
    """
    names = []
    seen_names = set()
    iterables = set()
    defaults = collections.defaultdict(str)

    # find all names with context "load"
    for node in root.find_all(jinja2.nodes.Name):
        if node.ctx == "load" and node.name not in seen_names:
            names.append(node.name)
        seen_names.add(node.name)

    # identify names that are iterables
    for for_node in root.find_all(jinja2.nodes.For):
        if type(for_node.iter) == jinja2.nodes.Name:
            iterables.add(for_node.iter.name)

    # find names with default values
    for filter_node in root.find_all(jinja2.nodes.Filter):
        if filter_node.name == "default" \
         and type(filter_node.node) == jinja2.nodes.Name \
         and type(filter_node.args[0]) == jinja2.nodes.Const:
            defaults[filter_node.node.name] = filter_node.args[0].value

    return names, iterables, defaults


@click.command(context_settings={"help_option_names": ("-h", "--help")})
@click.argument("template_name")
@click.argument("output_file", required=False, type=click.File(mode="w"))
@click.option("--template-dir", "-d", multiple=True,
              type=click.Path(file_okay=False, resolve_path=True),
              help="Specify directories used to find template files.")
@click.option("--builtin", is_flag=True, default=False,
              help="Look for built-in templates before searching other "
              "directories.")
@click.option("--prompt/--no-prompt", default=True,
              help="Toggle questions about template values.")
def main(template_name, output_file, template_dir, builtin, prompt):
    """
    Render TEMPLATE_NAME to OUTPUT_FILE or stdout.

    TEMPLATE_NAME must be a Jinja2 template file either included with this
    program or located in any of the template search directories.

    \b
    Templates are looked for in the following locations:
        1. Directories specified with the -d option
        2. ~/.templates/
        3. Built-in templates included with the program
    """
    search_dirs = template_dir + (DEFAULT_TEMPLATE_DIR,)
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
        err = None
    except jinja2.exceptions.TemplateNotFound:
        err = "Error: template '{}' not found".format(template_name)
    except jinja2.exceptions.TemplateSyntaxError as e:
        err = "Syntax error in template '{}': {}".format(template_name, e)

    # exit on error
    if err:
        click.echo(err, err=True)
        sys.exit(1)

    # extract user-provided names from template
    ast = environment.parse(source)
    names, iterables, defaults = find_user_bindings(ast)

    # prompt user for values
    values = {}
    if prompt:
        for name in names:
            value = click.prompt(name, default=defaults[name], err=True)
            if name in iterables:
                values[name] = list(filter(None, re.split("\s+", value)))
            else:
                values[name] = value

    # output rendered template
    click.echo(template.render(values), output_file)


if __name__ == "__main__":
    main()
