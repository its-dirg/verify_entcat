.. _Setup:

Setup
=====

This is a SAML IdP test utility for entity categories.

The service can verify how a IdP responds dependent on which
entity categories that are defined.

Start by installing pysaml2 and understand how to setup an SP with pysaml2.

Then start with the settings for verify_entcat.

#) Import the metadata this service should use.
    To do this you can use update_metadata.sh suitably modified

#) Change the name of conf.example to conf.py.
    Make any necessary changes (3)-(7)
#) In conf.py verify that the path in xmlsec_path is correct.
#) BASE should be the URL where you publish verify_entcat. The port must be the same as in server_conf.py.
#) attribute_map_dir must point to the pysaml2 directory.
#) Set the correct path for key_file and cert_file in conf.py
#) metadata must point to your metadata file.
#) Run build_conf.py

#) Rename the file server_conf.example to server_conf.py.
#) PORT must match with the settings for BASE in conf.py.
#) HTTPS should be True if you want to run the server as HTTPS, otherwise False.
  If you use HTTPS you need to do 12-14
#) POLICY contains the policies for the entity categories. View pysaml2 for more information.
#) RT contains the path the certificate
#) SERVER_KEY contains the path for the private key
#) CERT_CHAIN is the certificate chain that the HTTP server can use to
  verify server certificates. If it's empty (=None) no server certificate
  verification will be made.

#) Modify build.json so it reflects the combinations of entity categories
  you want to test
#) Build the SP configuration to cover all variants using build_conf.py
#) Build the metadata for all the SPs using build_metadata.py, you may
    want to change the name format.
#) Export your SPs metadata to you federation and you're ready to go
