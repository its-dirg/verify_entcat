from setuptools import setup, find_packages

setup(
    name='verify_entcat',
    version='0.2',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        'service_provider': [
            'templates/*.html',
            'site/static/*'
        ]
    },
    author='Roland Hedberg, Hans Hoerberg, Rebecka Gulliksson',
    author_email='roland.hedberg@umu.se, hans.horberg@umu.se, rebecka.gulliksson@umu.se',
    description='SAML IdP test utility for entity categories.',
    install_requires=[
        'pysaml2',
        'requests',
        'PyYAML'
    ],
    url='https://github.com/its-dirg/verify_entcat',
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 0.2 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ]
)
