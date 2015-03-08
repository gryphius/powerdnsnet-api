try:
    from setuptools import setup
except ImportError:
    from distutils import setup




setup(name = "powerdnsnet",
    version = '0.0.1',
    description = "Python client API implementation for powerdns.net DNS hosting",
    author = "O. Schacher",
    url='https://github.com/gryphius/powerdnsnet-api',
    author_email = "oli@wgwh.ch",
    package_dir={'powerdnsnet':'powerdnsnet'},
    packages = ['powerdnsnet',],

    long_description = """Python client API implementation for powerdns.net DNS hosting""" ,

)
