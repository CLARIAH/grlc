import setuptools


with open("README.md", "r") as f:
    long_description = f.read()


setuptools.setup(
    name="grlc_fork",                                                 # This is the name of the package
    version="0.1.0",                                                  # The initial release version
    author="Mihari RANAIVOSON",                                       # Full name of the author
    author_email="mihari.ranaivoson@orange.com",
    description="Create an API and UI for executiong SPARQL query",    
    long_description=long_description,                               # Long description read from the the readme file
    long_description_content_type="text/markdown",                   #
    packages=setuptools.find_packages(),                             # List of all python modules to be installed
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],                                                               # Information to filter the project on PyPi website
    python_requires='>=3.6',                                         # Minimum version requirement of the package
    package_data={
        '': [
            '*',
            'static/css/*', 
            'static/js/*',
            'static/*',
            'templates/*'
        ]
    },
    include_package_data=True,
    install_requires=[
        "Flask",
        "Flask-Cors",
        "requests",
        "pyparsing",
        "rdflib",
        "SPARQLTransformer",
        "SPARQLWrapper",
        "PyGithub",
        "python-gitlab",
        "pyaml",
        "PyYAML"
    ]
)