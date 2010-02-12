import sys

def GetPythonVersion():
    version = 0
    for i, v in enumerate(sys.version_info[2::-1]):
        version += (10 ** i) * v
    return version

PYTHON_VERSION = GetPythonVersion()

# Import the standard modules.
import stackless
import urlparse, cStringIO, cgi, logging
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn

logger = logging.getLogger("www")


class RequestHandler(BaseHTTPRequestHandler):
    # Respect keep alive requests.
    protocol_version = "HTTP/1.1"
    useChunked = True

    def do_GET(self):
        scheme, netloc, path, parameters, query, fragment = urlparse.urlparse(self.path, "http")
        self.handle_command(path, query, "")

    def do_POST(self):
        scheme, netloc, path, parameters, query, fragment = urlparse.urlparse(self.path, "http")
        contentType, contentTypeParameters = cgi.parse_header(self.headers.getheader('content-type'))
        contentLength = int(self.headers.get("content-length", -1))

        content = ""
        kwargs = None
        if contentType == "multipart/form-data":
            content, multiparts = self.ExtractMultiparts(contentTypeParameters, contentLength)
        elif contentType == "application/x-www-form-urlencoded":
            query = self.rfile.read(contentLength)

        self.handle_command(path, query, content)

    def handle_command(self, path, query, content):
        kwargs = cgi.parse_qs(query, keep_blank_values=1)
        transferEncoding = self.headers.get("transfer-encoding")
        
        if transferEncoding == "chunked":
            # As I understand it the additional headers should be incorporated into
            # self.headers and "chunked" cleared from the transfer-encoding header.
            additionalHeaders, content = self.ReadChunks()

        #if False:
        #    if path == "/mud-push":
        #        cometType = int(kwargs["PICometMethod"][0])
        #        self.mud_push(cometType)
        #    elif path == "/mud-send":
        #        self.mud_send(kwargs["nickname"][0], kwargs["text"][0])
        if path in self.server.pages:
            body = open(self.server.pages[path], "r").read()

            insert = ""
            for k, v in self.headers.items():
                insert += "%s: %s<br>" % (k, v)
            # insert += str((scheme, netloc, path, parameters, query, fragment)) +"<br>"

            body = body.replace("--BODY--", insert)

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            if self.useChunked:
                self.send_header("Transfer-Encoding", "chunked")
            else:
                self.send_header("Content-Length", len(body))
            self.end_headers()

            if self.useChunked:
                halfLen = int(len(body) / 2)
                chunk1 = body[:halfLen]
                chunk2 = body[halfLen:]

                self.WriteChunk(chunk1)
                self.WriteChunk(chunk2)
                self.WriteChunk()
            else:
                self.wfile.write(body)
        else:
            # Page not found.
            self.send_response(404,"Page not found")
            body = "404 - Page '%s' not found." % path
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Length", len(body))
            self.end_headers()

            self.wfile.write(body)

    if False:
        def mud_push(self, cometType):
            cometName = "PI-RPC"

            pi = pi_comet.PIComet(cometType)

            self.send_response(200)
            self.send_header("Content-type", pi.contentType)
            if self.useChunked:
                self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            global piChatMessages, waitChannel

            while True:
                output = "["
                first = True
                for x in piChatMessages:
                    if first==False:output+=","
                    else: first = False
                    output += "{ id:%i, 'text':'%s', 'nickname':'%s' }"%(x[2],x[0],x[1])
                output += "];" 
                s = pi.push(output)
                if self.useChunked:
                    self.WriteChunk(s)
                else:
                    self.wfile.write(s)

                waitChannel.receive()

        def mud_send(self, nickname, text):
            # These messages come in through an XHR connection.  The web page
            # creates a new one of these and therefore new connection each
            # time it needs to send a message.  So in order to respect the
            # limitation the browser has (if it is IE or Firefox) of only
            # being able to have two open connections to a site, we need to
            # make sure the send connection is closed so that a new one can
            # arrive.
            self.close_connection = 1

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            global piChatMessages, waitChannel
            piChatMessages.append((text, nickname, len(piChatMessages)))

            # With normal channel behaviour, calling this would block this tasklet as
            # each blocked subscriber channel was sent to and immediately received.
            # Instead because each subscriber channel has had its preference changed
            # each send will schedule the tasklet waiting on the other side of the
            while waitChannel.balance < 0:
                waitChannel.send(None)

    def ExtractMultiparts(self, contentTypeParameters, contentLength):
        # Possible improvement: Ditch early parts of 'rawData' as we know we have
        #                       finished with it.  Reduce memory consumption..
        # Possible improvement: Does not handle nested multiparts yet.  But that
        #                       should be a matter of recursion.

        initialPartBoundary = "--"+ contentTypeParameters["boundary"] +"\r\n"
        interimPartBoundary = "\r\n"+ initialPartBoundary
        finalPartBoundary = "\r\n--"+ contentTypeParameters["boundary"] +"--\r\n"
        partBoundary = initialPartBoundary

        content = ""
        contentRead = 0
        multiparts = []

        rawData = ""
        rawDataOffset = 0

        # We assume that there may be leading data before the first boundary.
        lastDataStart = 0
        while contentRead < contentLength:
            readSize = min(contentLength - contentRead, 98304)
            rawData += self.rfile.read(readSize)
            contentRead += readSize

            while 1:
                # Do we have another part header in the read data?
                headerOffset = rawData.find(partBoundary, rawDataOffset)
                if headerOffset == -1:
                    break # Read more data.

                if headerOffset > lastDataStart:
                    if lastDataStart == 0:
                        content = rawData[lastDataStart:headerOffset]
                    else:
                        multiparts[-1][1] = rawData[lastDataStart:headerOffset]

                headerOffset += len(partBoundary)
                partBoundary = interimPartBoundary

                # Do we have the end of the part header in the read data?
                dataOffset = rawData.find("\r\n\r\n", headerOffset)
                if dataOffset == -1:
                    break # Read more data.

                # Skip past the header end to the start of the data.
                dataOffset += 4
                lastDataStart = dataOffset

                # Extract the headers into a file-like object.
                sio = cStringIO.StringIO()
                sio.write(rawData[headerOffset:dataOffset])
                sio.seek(0)

                multiparts.append([ self.MessageClass(sio), None ])

                rawDataOffset = headerOffset

        # Extract the last bit of data.
        headerOffset = rawData.find(finalPartBoundary, lastDataStart)
        if headerOffset != -1:
            multiparts[-1][1] = rawData[lastDataStart:headerOffset]

        return content, multiparts

    def ReadChunks(self):
        # Possible improvement: Work out what to do with these extensions.

        def ReadChunkHeader():
            # HEX-LENGTH[;x=y]\r\n
            line = self.rfile.readline()
            bits = [ bit.strip() for bit in line.split(";") ]
            extension = None
            if len(bits) == 2:
                extension = bits[1].split("=")
            return int(bits[1], 16), extension

        data = cStringIO.StringIO()
        chunkSize, extension = ReadChunkHeader()
        while chunkSize > 0:
            data.write(self.rfile.read(chunkSize))
            self.rfile.read(2)
            chunkSize, extension = ReadChunkHeader()
        # Optional chunk trailer after the last one.
        headers = self.MessageClass(self.rfile, 0)
        return headers, data.getvalue()

    def WriteChunk(self, data=None, **kwargs):
        """
            Write a chunk of data.
            Requires that a chunked Transfer-Encoding header was set.
            If used, chunks should be finalised with a final one with no data.
        """
        xtra = ""
        for k, v in kwargs.iteritems():
            xtra += ";%s=%s"
        chunkSize = data and len(data) or 0
        self.wfile.write("%X%s\r\n" % (chunkSize, xtra))
        if data:
            self.wfile.write(data)
        self.wfile.write("\r\n")


class MicrothreadingMixIn(ThreadingMixIn):
    def process_request(self, request, client_address):
        stackless.tasklet(self.process_request_thread)(request, client_address)

    def _process_request_thread(self, *args, **kwargs):
        try:
            self.process_request_thread(request, client_address)
        except Exception:
            logger.exception("Error processing request")


class StacklessHTTPServer(MicrothreadingMixIn, HTTPServer):
    pages = {}

    if PYTHON_VERSION >= 260:
        # We need to identify when the socket is no longer accepting connections
        # so that we can have our 'serve_forever' replacement also exit.
        def get_request(self):
            try:
                return HTTPServer.get_request(self)
            except socket.error:
                self._BaseServer__serving = False
                # Reraise, this is caught by the invoking method.
                raise

        def serve_forever(self):
            # 'serve_forever' is dead to us as it has been rewritten to invoke 'select' directly.
            self._BaseServer__serving = True
            while self._BaseServer__serving:
                self._handle_request_noblock()

    def handle_error(self, *args, **kwargs):
        # Prevent HTTPServer from displaying normal exceptions.
        if sys.exc_type is not TaskletExit:
            HTTPServer.handle_error(self, *args, **kwargs)


if __name__ == "__main__":
    def Run():
        address = ('127.0.0.1', 9000)
        print "Starting web server on %s port %d" % address
        server = StacklessHTTPServer(address, RequestHandler)
        server.serve_forever()

    import stacklesssocket
    stacklesssocket.install()

    stackless.tasklet(Run)()
    stackless.run()
