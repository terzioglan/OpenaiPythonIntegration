# python 2 and 3
import json, socket, time

import config as CONFIG

def structureDataPackage(message: str, context: str) -> dict:
    msgID = str(time.time())
    dataDict = {
        "msg_id": msgID,
        "message": message,
        "context": context
        }
    return dataDict, msgID

class Server(object):
    def __init__(
            self, 
            host: str, 
            port: int, 
            size: int ):
        print( "initializing server..." )
        assert size >= 42, f"Minimum allowed package size is 42 for {type(self)}."
        self.__host = host
        self.__port = port
        self.__size = size
        self.__encoding = CONFIG.ENCODING
        self.__receiveTimeout = CONFIG.RECEIVE_PACKAGE_TIMEOUT
        self.__terminationByte = CONFIG.TERMINATION_BYTE
       
        self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.__socket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
        self.__socket.bind( (self.__host, self.__port) )
        self.__socket.listen(1)
        self.__conn, self.__addr = self.__socket.accept()
        print( "...server initialized." )
    
    def __reconnect(self,):
        print("Server attempting to reestablish connection.")
        try:
            self.__socket.listen(1)
            self.__conn, self.__addr = self.__socket.accept()
        except Exception as e:
            print(e)
        finally:
            time.sleep(1.0)

    def __sendAcknowledge( self, ack: bool, msgID: bytes ) -> None:
        # print("Server sending acknowledgement ", ack)
        if ack:
            self.__conn.sendall( msgID )
        else:
            self.__conn.sendall( str( 0.0 ).encode( self.__encoding ) )
    
    def __requestAcknowledge( self, msgID: bytes ) -> bool:
        # print("Server requesting acknowledgement ", msgID)
        ackMsgID = self.__conn.recv( self.__size )
        print("Ack: ", ackMsgID == msgID)
        return ackMsgID == msgID

    def send( self,  message: str, context: str = None ) -> None:
        dataDict, msgID = structureDataPackage( message, context )
        dataString = json.dumps( dataDict ).encode( self.__encoding ) + self.__terminationByte
        dataStringChunks = [ dataString[ i:i+self.__size ] for i in range( 0, len(dataString), self.__size )]
        packageCount = len( dataStringChunks )
        acknowledged = False
        while not acknowledged:
            i = 0
            while i < packageCount:
                try:
                    self.__conn.sendall( dataStringChunks[i] )
                except Exception as e:
                    print( e )
                    self.__reconnect()
                    i = 0
                else:
                    i += 1
            try:
                acknowledged = self.__requestAcknowledge( msgID.encode( self.__encoding ) )
            except Exception as e:
                print( e )
                self.__reconnect()
                i = 0

    def receive(self,) -> dict:
        terminationReceived = False
        dataString = b''
        acknowledged = False
        while not acknowledged:
            while not terminationReceived:
                try:
                    dataStringChunk = self.__conn.recv( self.__size )
                except Exception as e:
                    print(e)
                    self.__reconnect()
                else: 
                    if not dataStringChunk:
                        self.__reconnect()
                        return None
                    else:
                        dataString += dataStringChunk
                        terminationReceived = (dataString[-1:] == self.__terminationByte)
            try:
                data = dataString[:-1].decode(self.__encoding) # strip the termination byte
                dataDict = json.loads(data)
            except:
                self.__sendAcknowledge( False, "0.0".encode( self.__encoding ) )
            else:
                self.__sendAcknowledge( True, dataDict["msg_id"].encode( self.__encoding ) )
                acknowledged = True
        return dataDict
    
    def exit(self,):
        self.__conn.close()
        self.__socket.shutdown(socket.SHUT_RDWR)
        self.__socket.close()

class Client(object):
    def __init__(
            self,
            host: str, 
            port: int, 
            size: int ):
        assert size >= 42, f"Minimum allowed package size is 42 for {type(self)}."
        self.__host = host
        self.__port = port
        self.__size = size
        self.__encoding = CONFIG.ENCODING
        self.__receiveTimeout = CONFIG.RECEIVE_PACKAGE_TIMEOUT
        self.__terminationByte = CONFIG.TERMINATION_BYTE
    
        self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.__connected = False
        while not self.__connected :
            try:
                print("Waiting to connect to the server...")
                self.__socket.connect( (self.__host, self.__port) )
            except Exception as e:
                print(e)
                time.sleep(1.0)
            else:
                print("...connected to the server.")
                self.__connected = True
        if not self.__connected:
            print("cannot connect to a server to publish activities. Exiting.")
            self.__exit()
    
    def __reconnect( self ):
        print("Client attempting to reconnect")
        try:
            self.__socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            self.__socket.connect( (self.__host, self.__port) )
        except Exception as e:
            print(e)
        finally:
            time.sleep(1.0)

    def __sendAcknowledge( self, ack: bool, msgID: bytes ) -> None:
        # print("Client sending acknowledgement ", ack, msgID)
        if ack:
            self.__socket.sendall( msgID )
        else:
            self.__socket.sendall( str( 0.0 ).encode( self.__encoding ) )
    
    def __requestAcknowledge( self, msgID: bytes ) -> bool:
        # print("Client requesting acknowledgement ", msgID)
        ackMsgID = self.__socket.recv( self.__size )
        return ackMsgID == msgID

    def send( self,  message: str, context: str = None ) -> None:
        dataDict, msgID = structureDataPackage( message, context )
        dataString = json.dumps( dataDict ).encode( self.__encoding ) + self.__terminationByte
        dataStringChunks = [ dataString[ i:i+self.__size ] for i in range( 0, len(dataString), self.__size )]
        packageCount = len( dataStringChunks )
        acknowledged = False
        while not acknowledged:
            i = 0
            while i < packageCount:
                try:
                    self.__socket.sendall( dataStringChunks[i] )
                except Exception as e:
                    print( e )
                    self.__reconnect()
                    i = 0
                else:
                    i += 1
            try:
                acknowledged = self.__requestAcknowledge( msgID.encode( self.__encoding ) )
            except Exception as e:
                print( e )
                self.__reconnect()
                i = 0

    def receive(self,) -> dict:
        terminationReceived = False
        dataString = b''
        acknowledged = False
        while not acknowledged:
            while not terminationReceived:
                try:
                    dataStringChunk = self.__socket.recv( self.__size )
                except Exception as e:
                    print(e)
                    self.__reconnect()
                else:
                    if not dataStringChunk:
                        self.__reconnect()
                    else:
                        dataString += dataStringChunk
                        terminationReceived = (dataString[-1:] == self.__terminationByte)
            try:
                data = dataString[:-1].decode(self.__encoding) # strip the termination byte
                dataDict = json.loads(data)
            except:
                self.__sendAcknowledge( False, "0.0".encode( self.__encoding ) )
            else:
                self.__sendAcknowledge( True, dataDict["msg_id"].encode( self.__encoding ) )
                acknowledged = True
        return dataDict

    def exit( self, ):
        if self.__connected:
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
            self.__connected = False