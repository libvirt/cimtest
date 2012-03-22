#!/usr/bin/python
# Copyright IBM Corp. 2007-2012
#
# indication_tester.py - Tool for testing indication subscription and
#                        delivery against a CIMOM
# Author: Dan Smith <danms@us.ibm.com>
# SSL support added by Dave Heller <hellerda@us.ibm.com>
#
# This file is both a module of the cimtest "libvirt-cim" suite and a standalone
# program for indication testing.  The following notes describe the usage of the
# standalone program.
#
# USAGE:
#
# Use the -h or --help option to see the complete list of command line options.
#
# Although the script supports http or https indications to the handler
# Destination, it currently does not support https connections to the CIMOM.
# All communication to the CIMOM is over http, so the CIMOM must have a http
# port open for the script to work.
#
# Note there is some inconsistency between the --url option (CIMOM URL) and the
# --dest option (handler Destination URL).  The --dest option is a true URL in
# which you may specify scheme (http or https), user and password, in addition
# to server and port.  The --url option accepts only server and port.  Use the
# --user and --pass options to specify CIMOM credentials.
#
# Use the --interop option to override the default interop namespace
# (root/interop).  You may specify the full namespace name (with '/') or an
# abbreviated name (no '/').  In the latter case, the script will prepend
# "root/" to the name.  (Example: --interop PG_InterOp)
#
# Use the --ns option to override the indication namespace (which by default is
# the same as the interop namespace).  Note this option currently does not
# support abbreviations; you must specify the full namespace name.
#
# Use the --print-ind option to see responses from the CIMOM.  Use the --verbose
# option to see additional debug info such as details of the CIMOM SSL
# certificates when https indications are received.
#
# Use --certFile and --keyFile to specify the indications receiver's (i.e.
# the script's) SSL certificate and key in PEM format.  If --keyFile is not
# provided, the --certFile must contain the key.
#
# Use --trustStore to specify CA certificate(s) to be used to verify the CIMOM's
# certificate, or use --noverify to skip this verification.
#
# Use --trigger to cause the CIMOM to send a test indication.  Currently this
# feature only supports the SFCB Test_Indication provider.  (Build SFCB with
# "configure --enable-tests" before running "make".)  Otherwise, the indication
# must be triggered through some independent method.
#
# EXAMPLES:
#
# Start a listener for indication class "Test_Indication" using all default
# values.  The CIMOM and the listener are both running on localhost; the interop
# and indication namespaces are both: root/interop:
#
# $ indication_tester.py Test_Indication
#
# Start a listener for class "CIM_Alerts" in root/mynamespace using the
# OpenPegasus CIMOM:
#
# $ indication_tester.py --interop PG_InterOp --ns root/mynamespace CIM_Alerts
#
# Start a listener on the local host but register the subscription to a CIMOM on
# a remote host.  Note the handler Destination must point to the local host in a
# manner that is resolvable to the CIMOM:
#
# $ indication_tester.py --url remotesys.mydomain.com:5988 --dest \
#   http://localsys.mydomain.com:8000 Test_Indication
#
# Start a listener to receive an indication via https, do not verify the CIMOM
# certificate:
#
# $ indication_tester.py --noverify --certFile mycert.pem --keyFile mykey.pem \
#   Test_Indication
#
# Same as above but additionally verify the CIMOM cert against known CA certs:
#
# $ indication_tester.py --trustStore CAcerts.pem --certFile mycert.pem
#   --keyFile mykey.pem Test_Indication
#
# Trigger an indication using the SFCB Test_Indication provider.  Note this is a
# *separate invocation* of the script, independent of the listener (presumably
# already started per the examples above).  In trigger mode, the script sends
# the appropriate method call to the CIMOM and exits.  If successful, the
# indication will be received at the listener:
#
# $ indication_tester.py --trigger
#
# Same as above but the CIMOM is running on a remote system:
#
# $ indication_tester.py --url remotesys:5988 --trigger

import sys
from optparse import OptionParser
from urlparse import urlparse, urlunparse
from xml.dom.minidom import parse, parseString
import httplib
import base64
import errno, os, re
import socket
from SocketServer import BaseServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from OpenSSL import SSL

def filter_xml(name, type, ns, sysname, interopNS):
    return """
    <?xml version="1.0" encoding="utf-8"?>
    <CIM CIMVERSION="2.0" DTDVERSION="2.0">
    <MESSAGE ID="4711" PROTOCOLVERSION="1.0">
      <SIMPLEREQ>
        <IMETHODCALL NAME="CreateInstance">
          <LOCALNAMESPACEPATH>
            <NAMESPACE NAME="%s"/>
            <NAMESPACE NAME="%s"/>
          </LOCALNAMESPACEPATH>
          <IPARAMVALUE NAME="NewInstance">
              <INSTANCE CLASSNAME="CIM_IndicationFilter">
                <PROPERTY NAME="SystemCreationClassName" TYPE="string">
                  <VALUE>CIM_ComputerSystem</VALUE>
                </PROPERTY>
                <PROPERTY NAME="SystemName" TYPE="string">
                  <VALUE>%s</VALUE>
                </PROPERTY>
                <PROPERTY NAME="CreationClassName" TYPE="string">
                  <VALUE>CIM_IndicationFilter</VALUE>
                </PROPERTY>
                <PROPERTY NAME="Name" TYPE="string">
                  <VALUE>%sFilter</VALUE>
                </PROPERTY>
                <PROPERTY NAME="Query" TYPE="string">
                  <VALUE> SELECT * FROM %s
                  </VALUE>
                </PROPERTY>
                <PROPERTY NAME="QueryLanguage" TYPE="string">
                  <VALUE>WQL</VALUE>
                </PROPERTY>
                <PROPERTY NAME="SourceNamespace" TYPE="string">
                  <VALUE>%s</VALUE>
                </PROPERTY>
              </INSTANCE>
            </IPARAMVALUE>
          </IMETHODCALL>
        </SIMPLEREQ>
      </MESSAGE>
    </CIM>
    """ % (interopNS[0], interopNS[1], sysname, name, type, ns)

def handler_xml(name, destUrl, sysname, interopNS):
    return """
    <?xml version="1.0" encoding="utf-8"?>
    <CIM CIMVERSION="2.0" DTDVERSION="2.0">
      <MESSAGE ID="4711" PROTOCOLVERSION="1.0">
        <SIMPLEREQ>
        <IMETHODCALL NAME="CreateInstance">
            <LOCALNAMESPACEPATH>
              <NAMESPACE NAME="%s"/>
              <NAMESPACE NAME="%s"/>
            </LOCALNAMESPACEPATH>
            <IPARAMVALUE NAME="NewInstance">
              <INSTANCE CLASSNAME="CIM_IndicationHandlerCIMXML">
                <PROPERTY NAME="SystemCreationClassName" TYPE="string">
                  <VALUE>CIM_ComputerSystem</VALUE>
                </PROPERTY>
                <PROPERTY NAME="SystemName" TYPE="string">
                  <VALUE>%s</VALUE>
                </PROPERTY>
                <PROPERTY NAME="CreationClassName" TYPE="string">
                  <VALUE>CIM_IndicationHandlerCIMXML</VALUE>
                </PROPERTY>
                <PROPERTY NAME="Name" TYPE="string">
                  <VALUE>%sHandler</VALUE>
                </PROPERTY>
                <PROPERTY NAME="Destination" TYPE="string">
                  <VALUE>%s</VALUE>
                </PROPERTY>
              </INSTANCE>
            </IPARAMVALUE>
          </IMETHODCALL>
        </SIMPLEREQ>
      </MESSAGE>
      </CIM>
      """ % (interopNS[0], interopNS[1], sysname, name, destUrl)

def subscription_xml(name, sysname, interopNS):
    return """
    <?xml version="1.0" encoding="utf-8"?>
    <CIM CIMVERSION="2.0" DTDVERSION="2.0">
      <MESSAGE ID="4711" PROTOCOLVERSION="1.0">
        <SIMPLEREQ>
          <IMETHODCALL NAME="CreateInstance">
            <LOCALNAMESPACEPATH>
              <NAMESPACE NAME="%s"/>
              <NAMESPACE NAME="%s"/>
            </LOCALNAMESPACEPATH>
            <IPARAMVALUE NAME="NewInstance">
              <INSTANCE CLASSNAME="CIM_IndicationSubscription">
                <PROPERTY.REFERENCE NAME="Filter"
                                    REFERENCECLASS="CIM_IndicationFilter">
                  <VALUE.REFERENCE>
                    <INSTANCENAME CLASSNAME="CIM_IndicationFilter">
                      <KEYBINDING NAME="SystemCreationClassName">
                        <KEYVALUE VALUETYPE="string">
                        CIM_ComputerSystem
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="SystemName">
                        <KEYVALUE VALUETYPE="string">
                        %s
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="CreationClassName">
                        <KEYVALUE VALUETYPE="string">
                        CIM_IndicationFilter
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="Name">
                        <KEYVALUE VALUETYPE="string">
                        %sFilter
                        </KEYVALUE>
                      </KEYBINDING>
                    </INSTANCENAME>
                  </VALUE.REFERENCE>
                </PROPERTY.REFERENCE>
                <PROPERTY.REFERENCE NAME="Handler"
                                    REFERENCECLASS="CIM_IndicationHandler">
                  <VALUE.REFERENCE>
                    <INSTANCENAME CLASSNAME="CIM_IndicationHandlerCIMXML">
                      <KEYBINDING NAME="SystemCreationClassName">
                        <KEYVALUE VALUETYPE="string">
                        CIM_ComputerSystem
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="SystemName">
                        <KEYVALUE VALUETYPE="string">
                        %s
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="CreationClassName">
                        <KEYVALUE VALUETYPE="string">
                        CIM_IndicationHandlerCIMXML
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="Name">
                        <KEYVALUE VALUETYPE="string">
                        %sHandler
                        </KEYVALUE>
                      </KEYBINDING>
                    </INSTANCENAME>
                  </VALUE.REFERENCE>
                </PROPERTY.REFERENCE>
                <PROPERTY NAME="SubscriptionState" TYPE="uint16">
                  <VALUE> 2 </VALUE>
                </PROPERTY>
              </INSTANCE>
            </IPARAMVALUE>
          </IMETHODCALL>
        </SIMPLEREQ>
      </MESSAGE>
      </CIM>
      """ % (interopNS[0], interopNS[1], sysname, name, sysname, name)

def delete_inst_xml(name, type, sysname, inst_name, interopNS):
    return """
    <?xml version="1.0" encoding="utf-8"?>
    <CIM CIMVERSION="2.0" DTDVERSION="2.0">
      <MESSAGE ID="4711" PROTOCOLVERSION="1.0">
        <SIMPLEREQ>
          <IMETHODCALL NAME="DeleteInstance">
            <LOCALNAMESPACEPATH>
              <NAMESPACE NAME="%s"/>
              <NAMESPACE NAME="%s"/>
            </LOCALNAMESPACEPATH>
            <IPARAMVALUE NAME="InstanceName">
              <INSTANCENAME CLASSNAME="CIM_Indication%s">
                <KEYBINDING NAME="SystemCreationClassName">
                  <KEYVALUE>CIM_ComputerSystem</KEYVALUE>
                </KEYBINDING>
                <KEYBINDING NAME="SystemName">
                  <KEYVALUE>%s</KEYVALUE>
                </KEYBINDING>
                <KEYBINDING NAME="CreationClassName">
                  <KEYVALUE>CIM_Indication%s</KEYVALUE>
                </KEYBINDING>
                <KEYBINDING NAME="Name">
                  <KEYVALUE>%s</KEYVALUE>
                </KEYBINDING>
              </INSTANCENAME>
            </IPARAMVALUE>
          </IMETHODCALL>
        </SIMPLEREQ>
      </MESSAGE>
    </CIM>;
    """ % (interopNS[0], interopNS[1], type, sysname, type, inst_name);

def delete_sub_xml(name, sysname, interopNS):
    return """
    <?xml version="1.0" encoding="utf-8"?>
    <CIM CIMVERSION="2.0" DTDVERSION="2.0">
      <MESSAGE ID="4711" PROTOCOLVERSION="1.0">
        <SIMPLEREQ>
          <IMETHODCALL NAME="DeleteInstance">
            <LOCALNAMESPACEPATH>
              <NAMESPACE NAME="%s"/>
              <NAMESPACE NAME="%s"/>
            </LOCALNAMESPACEPATH>
            <IPARAMVALUE NAME="InstanceName">
              <INSTANCENAME CLASSNAME="CIM_IndicationSubscription">
                <KEYBINDING NAME="Filter">
                  <VALUE.REFERENCE>
                    <INSTANCENAME CLASSNAME="CIM_IndicationFilter">
                      <KEYBINDING NAME="SystemCreationClassName">
                        <KEYVALUE VALUETYPE="string">
                        CIM_ComputerSystem
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="SystemName">
                        <KEYVALUE VALUETYPE="string">
                        %s
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="CreationClassName">
                        <KEYVALUE VALUETYPE="string">
                        CIM_IndicationFilter
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="Name">
                        <KEYVALUE VALUETYPE="string">
                        %sFilter
                        </KEYVALUE>
                      </KEYBINDING>
                    </INSTANCENAME>
                  </VALUE.REFERENCE>
                </KEYBINDING>
                <KEYBINDING NAME="Handler">
                  <VALUE.REFERENCE>
                    <INSTANCENAME CLASSNAME="CIM_IndicationHandlerCIMXML">
                      <KEYBINDING NAME="SystemCreationClassName">
                        <KEYVALUE VALUETYPE="string">
                        CIM_ComputerSystem
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="SystemName">
                        <KEYVALUE VALUETYPE="string">
                        %s
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="CreationClassName">
                        <KEYVALUE VALUETYPE="string">
                        CIM_IndicationHandlerCIMXML
                        </KEYVALUE>
                      </KEYBINDING>
                      <KEYBINDING NAME="Name">
                        <KEYVALUE VALUETYPE="string">
                        %sHandler
                        </KEYVALUE>
                      </KEYBINDING>
                    </INSTANCENAME>
                  </VALUE.REFERENCE>
                </KEYBINDING>
              </INSTANCENAME>
            </IPARAMVALUE>
          </IMETHODCALL>
        </SIMPLEREQ>
      </MESSAGE>
    </CIM>;
    """ % (interopNS[0], interopNS[1], sysname, name, sysname, name)

def trigger_xml(type, interopNS):
    return """
    <?xml version="1.0" encoding="utf-8"?>
    <CIM CIMVERSION="2.0" DTDVERSION="2.0">
      <MESSAGE ID="4711" PROTOCOLVERSION="1.0">
        <SIMPLEREQ>
          <METHODCALL NAME="SendTestIndication">
            <LOCALCLASSPATH>
              <LOCALNAMESPACEPATH>
                <NAMESPACE NAME="%s"/>
                <NAMESPACE NAME="%s"/>
              </LOCALNAMESPACEPATH>
              <CLASSNAME NAME="%s"/>
            </LOCALCLASSPATH>
          </METHODCALL>
        </SIMPLEREQ>
      </MESSAGE>
    </CIM>
    """ % (interopNS[0], interopNS[1], type)
    # FIXME: this should really use indication NS, not interop NS.

def update_url_port(parsedUrl, port):
    # Must manually reconstruct netloc to update the port value.
    if isinstance(parsedUrl.username, basestring):
      if isinstance(parsedUrl.password, basestring):
        netloc = "%s:%s@%s:%s" % (parsedUrl.username, parsedUrl.password,
                                  parsedUrl.hostname, port)
      else:
        netloc = "%s@%s:%s" % (parsedUrl.username,
                               parsedUrl.hostname, port)
    else:
      netloc = "%s:%s" % (parsedUrl.hostname, port)

    # Reassemble url with the updated netloc. return a string.
    return urlunparse((parsedUrl.scheme, netloc,
                       parsedUrl.path, parsedUrl.params,
                       parsedUrl.query, parsedUrl.fragment))

class CIMIndication:
    def __init__(self, xmldata):
        dom = parseString(xmldata)

        instances = dom.getElementsByTagName("INSTANCE")
        attrs = instances[0].attributes.items()
        self.name = attrs[0][1]

    def __str__(self):
        return self.name

def socket_handler_wrapper(*parms):
    try:
        CIMSocketHandler(*parms)
    except Exception as e:
        print "SSL error: %s" % str(e)

class CIMSocketHandler(SimpleHTTPRequestHandler):
    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

    def do_POST(self):
        length = self.headers.getheader('content-length')
        data = self.rfile.read(int(length))

        indication = CIMIndication(data)
        print "Got indication: %s from %s" % (indication, self.client_address)
        if self.server.print_ind:
            print "%s\n" % data
        self.server.indications.append(indication)
        # Silence the unwanted log output from send_response()
        realStderr = sys.stderr
        sys.stderr = open(os.devnull,'a')
        self.send_response(200)
        sys.stderr = realStderr

class SecureHTTPServer(HTTPServer):
    def __init__(self, server_address, HandlerClass):
        BaseServer.__init__(self, server_address, HandlerClass)

        def verify_cb(conn, cert, errnum, depth, ok):
          if options.verbose:
            print('Verify peer certificate chain: level %d:' % depth)
            print('subject=%s' % cert.get_subject())
            print('issuer =%s' % cert.get_issuer())
          return ok

        ctx = SSL.Context(SSL.SSLv23_METHOD)
        #ctx.use_certificate_file(options.certFile)
        ctx.use_certificate_chain_file(options.certFile)
        ctx.use_privatekey_file(options.keyFile)

        if options.noverify:
            ctx.set_verify(SSL.VERIFY_NONE, verify_cb)
        else:
            #ctx.set_verify(SSL.VERIFY_PEER, verify_cb)
            ctx.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
                           verify_cb)
            ctx.load_verify_locations(options.trustStore)

        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                        self.socket_type))
        self.server_bind()
        self.server_activate()

# The param defaults allow new options from main() w/o losing compat w/ cimtest.
class CIMIndicationSubscription:
    def __init__(self, name, typ, ns, print_ind, sysname, port=0,
            interopNS=('root','PG_InterOp'), destUrl="http://localhost:8000",
            triggermode=False):
        self.name = name
        self.type = typ
        self.ns = ns
        self.sysname = sysname
        self.interopNS = interopNS
        self.print_ind = print_ind

        # We do not want to open a listener socket in trigger mode.
        if triggermode:
          self.trigger_xml = trigger_xml(typ, interopNS)
          return

        parsedUrl = urlparse(destUrl)

        # Increment the listener port by the offset value.
        if isinstance(parsedUrl.port, int):
          listenerPort = parsedUrl.port + port
        else:
          listenerPort = 8000 + port

        destUrl = update_url_port(parsedUrl, listenerPort)

        try:
            if parsedUrl.scheme == "http":
                self.server = HTTPServer((parsedUrl.hostname,
                                          listenerPort),
                                          CIMSocketHandler)
            elif parsedUrl.scheme == "https":
                self.server = SecureHTTPServer((parsedUrl.hostname,
                                                listenerPort),
                                                socket_handler_wrapper)
        except IOError as e:
            print "Error creating listener socket: %s" % str(e)
            exit(e.errno)

        self.server.print_ind = print_ind
        self.server.indications = []

        self.filter_xml = filter_xml(name, typ, ns, sysname, interopNS)
        self.handler_xml = handler_xml(name, destUrl, sysname, interopNS)
        self.subscription_xml = subscription_xml(name, sysname, interopNS)

    def __do_cimpost(self, conn, body, method, auth_hdr=None):
        headers = {"CIMOperation" : "MethodCall",
                   "CIMMethod"    : method,
                  #"CIMObject"    : "root/PG_Interop",
                   "CIMObject"    : "%s/%s" % self.interopNS,
                   "Content-Type" : 'application/xml; charset="utf-8"'}

        if auth_hdr:
            headers["Authorization"] = "Basic %s" % auth_hdr

        try:
            conn.request("POST", "/cimom", body, headers)
            resp = conn.getresponse()
            if not resp.getheader("content-length"):
                raise Exception("Request Failed: %d %s" %
                                (resp.status, resp.reason))
        except IOError as e:
            print "Error connecting to CIMOM: %s" % str(e)
            exit(e.errno)

        if self.print_ind:
            print "=== Reply from CIMOM ==="
            #print resp.msg
            print resp.read()
        else:
            resp.read()

    def subscribe(self, url, cred=None):
        self.conn = httplib.HTTPConnection(url)
        if cred:
            (u, p) = cred
            auth_hdr = base64.b64encode("%s:%s" % (u, p))
        else:
            auth_hdr = None

        self.__do_cimpost(self.conn, self.filter_xml,
                          "CreateInstance", auth_hdr)
        self.__do_cimpost(self.conn, self.handler_xml,
                          "CreateInstance", auth_hdr)
        self.__do_cimpost(self.conn, self.subscription_xml,
                          "CreateInstance", auth_hdr)

    # Note, param order is different here to maintain compat with cimtest.
    # Better way would be to update cimtest 'indications.py' module.
    def unsubscribe(self, cred=None, url=None):
        # Without this, can get BadStatusLine exception in SFCB in some cases.
        if url:
            self.conn = httplib.HTTPConnection(url)

        if cred:
            (u, p) = cred
            auth_hdr = base64.b64encode("%s:%s" % (u, p))
        else:
            auth_hdr = None

        xml = delete_sub_xml(self.name, self.sysname, self.interopNS)
        self.__do_cimpost(self.conn, xml,
                          "DeleteInstance", auth_hdr)
        xml = delete_inst_xml(self.name, "HandlerCIMXML", self.sysname,
                              "%sHandler" % self.name, self.interopNS)
        self.__do_cimpost(self.conn, xml,
                          "DeleteInstance", auth_hdr)
        xml = delete_inst_xml(self.name, "Filter", self.sysname,
                              "%sFilter" % self.name, self.interopNS)
        self.__do_cimpost(self.conn, xml,
                          "DeleteInstance", auth_hdr)

    def trigger(self, url, cred=None):
        self.conn = httplib.HTTPConnection(url)
        if cred:
            (u, p) = cred
            auth_hdr = base64.b64encode("%s:%s" % (u, p))
        else:
            auth_hdr = None

        self.__do_cimpost(self.conn, self.trigger_xml,
                          "SendTestIndication", auth_hdr)

def dump_xml(name, typ, ns, sysname, interopNS, destUrl):
    filter_str = filter_xml(name, typ, ns, sysname, interopNS)
    handler_str = handler_xml(name, destUrl, sysname, interopNS)
    subscript_str = subscription_xml(name, sysname, interopNS)
    del_filter_str = delete_inst_xml(name, "Filter", sysname, "%sFilter" % name,
                                     interopNS)
    del_handler_str = delete_inst_xml(name, "HandlerCIMXML", sysname,
                                      "%sHandler" % name, interopNS)
    del_subscript_str = delete_sub_xml(name, sysname, interopNS)
    trigger_str = trigger_xml(typ, interopNS)

    print "CreateFilter:\n%s\n" % filter_str
    print "DeleteFilter:\n%s\n" % del_filter_str
    print "CreateHandler:\n%s\n" % handler_str
    print "DeleteHandler:\n%s\n" % del_handler_str
    print "CreateSubscription:\n%s\n" % subscript_str
    print "DeleteSubscription:\n%s\n" % del_subscript_str
    print "Indication trigger:\n%s\n" % trigger_str

def main():
    usage = "usage: %prog [options] provider\nex: %prog CIM_InstModification"
    parser = OptionParser(usage)

    # FIXME: SecureHTTPServer still relies on this, need a better way.
    global options

    parser.add_option("-u", "--url", dest="url", default="localhost:5988",
                      help="URL of CIMOM to connect to (host:port)")
    parser.add_option("-N", "--ns", dest="ns",
                      help="Namespace in which the register the indication \
                      (default is the same value as the interop namespace)")
    parser.add_option("-n", "--name", dest="name", default="Test",
                      help="Name for filter, handler, subscription \
                      (default: Test)")
    parser.add_option("-d", "--dump-xml", dest="dump", default=False,
                      action="store_true",
                      help="Dump the xml that would be used and quit.")
    parser.add_option("-p", "--print-ind", dest="print_ind", default=False,
                      action="store_true",
                      help="Print received indications to stdout.")
    parser.add_option("-v", "--verbose", dest="verbose", default=False,
                      action="store_true",
                      help="Print additional debug info.")
    parser.add_option("-U", "--user", dest="username", default=None,
                      help="HTTP Auth username (CIMOM)")
    parser.add_option("-P", "--pass", dest="password", default=None,
                      help="HTTP Auth password (CIMOM)")
    parser.add_option("--port", dest="port", default=0, type=int,
                      help="Port increment value (server default: 8000)")
    parser.add_option("--dest", dest="destUrl", default="localhost:8000",
                      help="URL of destination handler \
                      (default: http://localhost:8000)")
    parser.add_option("--certFile", dest="certFile", default=None,
                      help="File containing the local certificate to use")
    parser.add_option("--keyFile", dest="keyFile", default=None,
                      help="File containing private key for local cert \
                      (if none provided, assume key is in the certFile)")
    parser.add_option("--trustStore", dest="trustStore", default=None,
                      help="File containing trusted certificates for \
                      remote endpoint verification")
    parser.add_option("--noverify", dest="noverify", default=False,
                      action="store_true",
                      help="Skip verification of remote endpoint certificate \
                      for incoming https indications")
    parser.add_option("-i", "--interop", dest="interop",
                      default="root/interop",
                      help="Interop namespace name (default: root/interop)")
    parser.add_option("-t", "--trigger", dest="trigger", default=False,
                      action="store_true",
                      help="Trigger mode: send a request to CIMOM to trigger \
                      an indication via a method call ")

    (options, args) = parser.parse_args()

    if not options.trigger and len(args)==0:
        print "Fatal: no indication type provided."
        sys.exit(1)

    if options.username:
        auth = (options.username, options.password)
    else:
        auth = None

    if ":" in options.url:
        (sysname, port) = options.url.split(":")
    else:
        sysname = options.url

    if "/" in options.interop:
        options.interopNS = tuple(options.interop.split("/"))
    else:
        options.interopNS = ("root", options.interop)

    # If no value provided for indication NS, default is same as interopNS.
    if not options.ns:
        options.ns = "%s/%s" % options.interopNS

    if options.verbose:
        print "Interop namespace = %s/%s" % options.interopNS
        print "Indication namespace = %s" % options.ns

    # If url does not begin with http or https, assume http.
    parsedUrl = urlparse(options.destUrl)
    if not re.search(parsedUrl.scheme, "https"):
        destUrl = "http://" + options.destUrl
    else:
        destUrl = options.destUrl

    if parsedUrl.scheme == "https":
        if not options.trustStore and not options.noverify:
            print "Error: must provide --trustStore or --noverify with https."
            sys.exit(1)
        elif options.trustStore and options.noverify:
            print "Error: options --trustStore and --noverify are exclusive."
            sys.exit(1)
        if not options.certFile:
            print "Error: no certificate file provided."
            sys.exit(1)
        elif not options.keyFile:
            print "No keyFile provided; assuming private key \
            contained in certFile."
            options.keyFile = options.certFile

    if options.dump:
        if isinstance(parsedUrl.port, int):
          listenerPort = parsedUrl.port + options.port
        else:
          listenerPort = 8000 + options.port

        destUrl = update_url_port(parsedUrl, listenerPort)
        dump_xml(options.name, args[0], options.ns, sysname, options.interopNS,
                 destUrl)
        sys.exit(0)

    # Trigger mode: currently only supports SFCB Test_Indication provider.
    if options.trigger:
        classname = "Test_Indication"
        sub = CIMIndicationSubscription(options.name, classname, options.ns,
                                    options.print_ind, sysname, options.port,
                                    options.interopNS, destUrl, True)
        print "Triggering indication for %s" % classname
        sub.trigger(options.url, auth)
        sys.exit(0)

    sub = CIMIndicationSubscription(options.name, args[0], options.ns,
                                    options.print_ind, sysname, options.port,
                                    options.interopNS, destUrl)

    print "Creating subscription for %s" % args[0]
    sub.subscribe(options.url, auth)
    print "Watching for %s" % args[0]

    try:
        sub.server.serve_forever()
    except KeyboardInterrupt as e:
        print "Cancelling subscription for %s" % args[0]
        sub.unsubscribe(auth, options.url)

if __name__=="__main__":
    sys.exit(main())
