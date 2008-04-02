#!/usr/bin/python
# Copyright IBM Corp. 2007
#
# indication_tester.py - Tool for testing indication subscription and
#                        delivery against a CIMOM
# Author: Dan Smith <danms@us.ibm.com>

import sys
from optparse import OptionParser
import BaseHTTPServer
import httplib
import base64
from xml.dom.minidom import parse, parseString

def filter_xml(name, type, ns, sysname):
    return """
    <?xml version="1.0" encoding="utf-8"?> 
    <CIM CIMVERSION="2.0" DTDVERSION="2.0"> 
    <MESSAGE ID="4711" PROTOCOLVERSION="1.0"> 
      <SIMPLEREQ> 
        <IMETHODCALL NAME="CreateInstance"> 
          <LOCALNAMESPACEPATH> 
            <NAMESPACE NAME="root"/> 
            <NAMESPACE NAME="PG_InterOp"/> 
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
    """ % (sysname, name, type, ns)

def handler_xml(name, port, sysname):
    return """
    <?xml version="1.0" encoding="utf-8"?> 
    <CIM CIMVERSION="2.0" DTDVERSION="2.0"> 
      <MESSAGE ID="4711" PROTOCOLVERSION="1.0"> 
        <SIMPLEREQ> 
        <IMETHODCALL NAME="CreateInstance"> 
            <LOCALNAMESPACEPATH> 
              <NAMESPACE NAME="root"/> 
              <NAMESPACE NAME="PG_InterOp"/> 
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
                  <VALUE>localhost:%i</VALUE> 
                </PROPERTY> 
              </INSTANCE> 
            </IPARAMVALUE> 
          </IMETHODCALL> 
        </SIMPLEREQ> 
      </MESSAGE> 
      </CIM>
      """ % (sysname, name, port)

def subscription_xml(name, sysname):
    return """
    <?xml version="1.0" encoding="utf-8"?> 
    <CIM CIMVERSION="2.0" DTDVERSION="2.0"> 
      <MESSAGE ID="4711" PROTOCOLVERSION="1.0"> 
        <SIMPLEREQ> 
          <IMETHODCALL NAME="CreateInstance"> 
            <LOCALNAMESPACEPATH> 
              <NAMESPACE NAME="root"/> 
              <NAMESPACE NAME="PG_InterOp"/> 
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
      """ % (sysname, name, sysname, name)

def delete_inst_xml(name, type, sysname):
    return """
    <?xml version="1.0" encoding="utf-8"?> 
    <CIM CIMVERSION="2.0" DTDVERSION="2.0"> 
      <MESSAGE ID="4711" PROTOCOLVERSION="1.0"> 
        <SIMPLEREQ> 
          <IMETHODCALL NAME="DeleteInstance"> 
            <LOCALNAMESPACEPATH> 
              <NAMESPACE NAME="root"/> 
              <NAMESPACE NAME="PG_InterOp"/> 
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
                  <KEYVALUE>%s%s</KEYVALUE> 
                </KEYBINDING> 
              </INSTANCENAME> 
            </IPARAMVALUE> 
          </IMETHODCALL> 
        </SIMPLEREQ> 
      </MESSAGE> 
    </CIM>;
    """ % (type, sysname, type, name, type);

def delete_sub_xml(name, sysname):
    return """
    <?xml version="1.0" encoding="utf-8"?> 
    <CIM CIMVERSION="2.0" DTDVERSION="2.0"> 
      <MESSAGE ID="4711" PROTOCOLVERSION="1.0"> 
        <SIMPLEREQ> 
          <IMETHODCALL NAME="DeleteInstance"> 
            <LOCALNAMESPACEPATH> 
              <NAMESPACE NAME="root"/> 
              <NAMESPACE NAME="PG_InterOp"/> 
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
    """ % (sysname, name, sysname, name)

class CIMIndication:
    def __init__(self, xmldata):
        dom = parseString(xmldata)

        instances = dom.getElementsByTagName("INSTANCE")
        attrs = instances[0].attributes.items()
        self.name = attrs[0][1]

    def __str__(self):
        return self.name

class CIMSocketHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        length = self.headers.getheader('content-length')
        data = self.rfile.read(int(length))

        indication = CIMIndication(data)
        print "Got indication: %s" % indication
        if self.server.print_ind:
            print "%s\n\n" % data
        self.server.indications.append(indication)

class CIMIndicationSubscription:
    def __init__(self, name, typ, ns, print_ind, sysname):
        self.name = name
        self.type = typ
        self.ns = ns
        self.sysname = sysname

        self.server = BaseHTTPServer.HTTPServer(('', 8000), CIMSocketHandler)
        self.server.print_ind = print_ind
        self.port = 8000
        self.server.indications = []

        self.filter_xml = filter_xml(name, typ, ns, sysname)
        self.handler_xml = handler_xml(name, self.port, sysname)
        self.subscription_xml = subscription_xml(name, sysname)

    def __do_cimpost(self, conn, body, method, auth_hdr=None):
        headers = {"CIMOperation" : "MethodCall",
                   "CIMMethod"    : method,
                   "CIMObject"    : "root/PG_Interop",
                   "Content-Type" : "text/cimxml"}
 
        if auth_hdr:
            headers["Authorization"] = "Basic %s" % auth_hdr

        conn.request("POST", "/cimom", body, headers)
        resp = conn.getresponse()
        if not resp.getheader("content-length"):
            raise Exception("Authentication (or request) Failed!")

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

    def unsubscribe(self, cred=None):
        if cred:
            (u, p) = cred
            auth_hdr = base64.b64encode("%s:%s" % (u, p))
        else:
            auth_hdr = None

        xml = delete_sub_xml(self.name, self.sysname)
        self.__do_cimpost(self.conn, xml,
                          "DeleteInstance", auth_hdr)
        xml = delete_inst_xml(self.name, "Handler", self.sysname)
        self.__do_cimpost(self.conn, xml,
                          "DeleteInstance", auth_hdr)
        xml = delete_inst_xml(self.name, "Filter", self.sysname)
        self.__do_cimpost(self.conn, xml,
                          "DeleteInstance", auth_hdr)

def dump_xml(name, typ, ns, sysname):
    filter_str = filter_xml(name, typ, ns, sysname)
    handler_str = handler_xml(name, 8000, sysname)
    subscript_str = subscription_xml(name, sysname)
    del_filter_str = delete_inst_xml(name, "Filter", sysname)
    del_handler_str = delete_inst_xml(name, "Handler", sysname)
    del_subscript_str = delete_sub_xml(name, sysname)

    print "CreateFilter:\n%s\n" % filter_str
    print "DeleteFilter:\n%s\n" % del_filter_str
    print "CreateHandler:\n%s\n" % handler_str
    print "DeleteHandler:\n%s\n" % del_handler_str
    print "CreateSubscription:\n%s\n" % subscript_str
    print "DeleteSubscription:\n%s\n" % del_subscript_str
    
def main():
    usage = "usage: %prog [options] provider\nex: %prog CIM_InstModification"
    parser = OptionParser(usage)
    
    parser.add_option("-u", "--url", dest="url", default="localhost:5988",
                      help="URL of CIMOM to connect to (host:port)")
    parser.add_option("-N", "--ns", dest="ns", default="root/virt",
                      help="Namespace (default is root/virt)")
    parser.add_option("-n", "--name", dest="name", default="Test",
                      help="Name for filter, handler, subscription \
                      (default: Test)")
    parser.add_option("-d", "--dump-xml", dest="dump", default=False,
                      action="store_true",
                      help="Dump the xml that would be used and quit.")
    parser.add_option("-p", "--print-ind", dest="print_ind", default=False,
                      action="store_true",
                      help="Print received indications to stdout.")
    parser.add_option("-U", "--user", dest="username", default=None,
                      help="HTTP Auth username", dest="username")
    parser.add_option("-P", "--pass", dest="password", default=None,
                      help="HTTP Auth password", dest="password")

    (options, args) = parser.parse_args()

    if len(args) == 0:
        print "Fatal: no indication type provided."
        sys.exit(1)
    
    if options.username:
        auth = (options.username, options.password)
    else:
        auth = None
    
    if ":" in options.url:
        (sysname, port) = options.url.split(":")
    else:
        sysname = url
    
    if options.dump:
        dump_xml(options.name, args[0], options.ns, sysname)
        sys.exit(0)

    sub = CIMIndicationSubscription(options.name, args[0], options.ns,
                                    options.print_ind, sysname)
    sub.subscribe(options.url, auth)
    print "Watching for %s" % args[0]

    try:
        sub.server.serve_forever()
    except KeyboardInterrupt,e:
        sub.unsubscribe(auth)
        print "Cancelling subscription for %s" % args[0]

if __name__=="__main__":
    sys.exit(main())
