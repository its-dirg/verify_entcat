============
verify_encat
============
This is a SAML IdP test utility for entity categories.

The service can verify how a IdP responds dependent on which
entity categories that are defined.

Start by installing pysaml2 and understand how to setup an SP with pysaml2.

Then start with the settings for verify_ecat.

1) Create the metadata for this service and name it metadata.xml.
2) Change the name of conf.example to conf.py.
3) In conf.py verify that the path in xmlsec_path is correct.
4) BASE should be the URL where you publish verify_encat. The port must be the same as in server_conf.py.
5) attribute_map_dir must point to the pysaml2 directory.
6) metadata must point to your metadata file.
7) key_file and cert_file must be initiated.
8) Rename the file server_conf.exmaple to server_conf.py.
9) PORT must match with the settings for BASE in conf.py.
10) HTTPS should be True if you want to run the server as HTTPS, otherwise False.
  If you use HTTPS you need to do 12-14
11) POLICY contains the policies for the entity categories. View pysaml2 for more information.
12) SERVER_CERT contains the path the certificate
13) SERVER_KEY contains the path for the private key
14) CERT_CHAIN is the certificate chain that the HTTP server can use to
  verify server certificates. If it's empty (=None) no server certificate
  verification will be made.
