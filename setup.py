from distutils.core import setup

HTDOCS = "htdocs"
TEMPL = "templates"
STAT = "static"
TARGET = "idpproxy/metadata/files"

setup(
    name='verify_entcat',
    version='0.1',
    url='',
    #license='LICENSE.txt',
    author='Roland Hedberg, Hans Hoerberg',
    author_email='roland.hedberg@umu.se, hans.horberg@umu.se',
    description='Op to Saml proxy based on the projects pyoidc and pysaml.',
        install_requires=[
        'pysaml2',
        'mako'
    ],
    license="Apache 2.0",
    classifiers=[
        "Development Status :: 0.1 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    data_files=[
            ("%s" % HTDOCS, ["%s/check_result.mako" % HTDOCS,
                             "%s/test.mako" % HTDOCS]),
            ("%s" % STAT, ["%s/arrowDown.png" % STAT,
                           "%s/arrowLeft.png" % STAT,
                           "%s/" % STAT,
                           "%s/" % STAT,
                           "%s/" % STAT,
                           "%s/" % STAT,
                           "%s/" % STAT,
                           "%s/" % STAT,
                           "%s/" % STAT,
                           "%s/" % STAT]),
            ("%s/bootstrap/css/" % STAT, ["%s/bootstrap/css/bootstrap.css" % STAT,
                                          "%s/bootstrap/css/bootstrap.min.css" % STAT,
                                          "%s/bootstrap/css/bootstrap-theme.css" % STAT,
                                          "%s/bootstrap/css/bootstrap-theme.min.css" % STAT]),
            ("%s/bootstrap/fonts/" % STAT, ["%s/bootstrap/fonts/glyphicons-halflings-regular.eot" % STAT,
                                            "%s/bootstrap/fonts/glyphicons-halflings-regular.svg" % STAT,
                                            "%s/bootstrap/fonts/glyphicons-halflings-regular.ttf" % STAT,
                                            "%s/bootstrap/fonts/glyphicons-halflings-regular.woff" % STAT]),
            ("%s/bootstrap/js/" % STAT, ["%s/bootstrap/js/bootstrap.js" % STAT,
                                         "%s/bootstrap/js/bootstrap.min.js" % STAT])

        ]
)
