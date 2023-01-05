# filters.py

from jinja2 import Environment

def zip_filter(env: Environment):
    env.filters['zip'] = zip

# Register the filter
zip_filter(Environment())

# Export the filter
filters = {
    'zip': zip_filter
}
