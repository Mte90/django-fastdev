from django.apps import AppConfig
from django.template.base import (
    FilterExpression,
    render_value_in_context,
    Variable,
    VariableDoesNotExist,
)
from django.template.defaulttags import FirstOfNode


class FastDevConfig(AppConfig):
    name = 'django_fastdev'
    verbose_name = 'django-fastdev'

    def ready(self):
        orig_resolve = FilterExpression.resolve

        def resolve_override(self, context, ignore_failures=False, ignore_failures_for_real=False):
            if ignore_failures_for_real:
                return orig_resolve(self, context, ignore_failures=True)

            if isinstance(self.var, Variable):
                try:

                    self.var.resolve(context)
                except VariableDoesNotExist as e:
                    if len(self.var.lookups) == 1:
                        available = '\n    '.join(sorted(context.flatten().keys()))
                        raise VariableDoesNotExist(f'''{self.var} does not exist in context. Available top level variables:

    {available}
''')
                    else:
                        full_name = '.'.join(self.var.lookups)
                        bit, current = e.params
                        extra = ''

                        if isinstance(current, dict):
                            available_keys = '\n    '.join(sorted(current.keys()))
                            extra = f'\nYou can access keys in the dict by their name. Available keys:\n\n    {available_keys}\n'
                            error = f"dict does not have a key '{bit}', and does not have a member {bit}"
                        else:
                            name = f'{type(current).__module__}.{type(current).__name__}'
                            error = f'{name} does not have a member {bit}'
                        available = '\n    '.join(sorted(x for x in dir(current) if not x.startswith('_')))

                        raise VariableDoesNotExist(f'''Tried looking up {full_name} in context

{error}
{extra}
Available attributes:

    {available}

The object was: {current!r}
''')

            return orig_resolve(self, context, ignore_failures)

        FilterExpression.resolve = resolve_override

        def first_of_render_override(self, context):
            first = ''
            for var in self.vars:
                value = var.resolve(context, ignore_failures_for_real=True)
                if value:
                    first = render_value_in_context(value, context)
                    break
            if self.asvar:
                context[self.asvar] = first
                return ''
            return first

        FirstOfNode.render = first_of_render_override
