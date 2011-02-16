"""
This work is licensed under a Creative Commons Attribution 3.0 Unported License.

Please see README.md for intended use.

https://github.com/bjornswift/metastore
"""
import os

# By default, we create a sqlite3 database in the current working directory,
# named after the local machine.
DEFAULT_DATAFILE = "%s.sdb" % os.uname()[1]
DEFAULT_PORT = 8077

class LocalStore(object):
    """
    A local persistent key-value store, using sqlite3 as a backend.
    """
    def __init__(self, datafile=None):
        import sqlite3
        datafile = datafile if datafile else DEFAULT_DATAFILE
        self.conn = sqlite3.connect(datafile)
        self.bootstrap(datafile)
        
    def bootstrap(self, datafile):
        """
        Prepares the sqlite3 metastore table, if it doesn't exist.
        """
        import sqlite3
        # Try fetching a value from the table, if we get an OperationalError
        # we assume that the table doesn't exist, and create it.
        try:
            self.get("foo")
            return
        except KeyError:
            return
        except sqlite3.OperationalError:
            print " >> Bootstrapping local store: %s" % datafile
            c = self.conn.cursor()
            c.execute("CREATE TABLE metastore (k varchar(255), v "
                "text, primary key(k));")
            self.conn.commit()
    
    def get(self, key):
        """
        Fetch value for `key` from local store. Raises KeyError if `key` is
        not found.
        """
        c = self.conn.cursor()
        c.execute("SELECT v FROM metastore WHERE k = ?", (key, ))
        row = c.fetchone()
        if row:
            return row[0]
        raise KeyError
    
    def put(self, key, value):
        """
        Write `value` for `key` in local store. Overrides a previous value for
        `key`.
        """
        c = self.conn.cursor()
        c.execute("REPLACE INTO metastore (k, v) VALUES (?, ?)", (key, value))
        self.conn.commit()
        return True

    def multiget(self, keys):
        """
        Fetch values for multiple keys from a local store in a single request.
        Raises KeyError if *any* of the keys is not found.
        """
        result = {}
        for key in keys:
            result[key] = self.get(key)
        return result

class MetaServer(object):
    """
    XML-RPC server that allows remote clients to access the local metastore.
    """
    def __init__(self, datafile=None, port=None):
        self.store = LocalStore(datafile=datafile)
        self.port = port if port else DEFAULT_PORT
    
    def serve(self):
        """
        Start a metastore server which initiates a local store and serves
        remote clients on port `DEFAULT_PORT` over XML-RPC.
        """
        
        print ("Starting metastore server on port %d, use ctrl-c "
            "to quit" % self.port)
        
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        server = SimpleXMLRPCServer(("0.0.0.0", self.port))
        server.register_function(self.store.get)
        server.register_function(self.store.put)
        server.register_function(self.store.multiget)
        server.serve_forever()

class RemoteStore(object):
    """
    Proxy to a remote metastore.
    """

    # This class is not really needed, could change use_remote() so that it
    # just assigns the xmlrpclib.ServerProxy to _store. We leave it like this,
    # for now, to add doc strings to methods - and for the cases where we want
    # to temporarily add print statements or whatnot for debugging :)

    def __init__(self, remote_addr, port=None):
        import xmlrpclib
        port = port if port else DEFAULT_PORT
        self.sp = xmlrpclib.ServerProxy("http://%s:%s" %
            (remote_addr, port))
    
    def get(self, key):
        """
        Fetch value for `key` from a remote metastore.
        """
        return self.sp.get(key)

    
    def put(self, key, value):
        """
        Write `value` for `key` to a remote metastore.
        """
        return self.sp.put(key, value)

    def multiget(self, keys):
        """
        Fetch multiple `keys` from a remote metastore in a single request.
        This can reduce query time, when querying multiple keys.
        """
        return self.sp.multiget(keys)


# The following functions are just convenience functions for using the classes
# above. They allow for setting the datastore on the metastore module itself,
# providing the developer with a fairly easy way of globally setting which
# store to use. For example:
#
#  local:
#    import metastore
#    metastore.put("foo", "bar")
#
#  remote:
#    import metastore
#    metastore.use_remote("server.com")
#    metastore.put("foo", "bar")

_store = None
def get_store(datafile=None):
    """
    Get the current datastore, or initialize one if needed. Note that the
    datafile argument is only used the first time that `get_store` is invoked.
    That is get_store("a.sdb") and get_store("b.sdb") with both return a
    reference to "a.sdb"!
    """
    global _store
    if _store is None:
        _store = LocalStore(datafile=datafile)
    return _store

def use_remote(addr, port=None):
    """
    Create a proxy to a remote metastore
    """
    global _store
    if _store is not None:
        raise RuntimeError("Already using a local metastore! "
            "Use the metastore classes directly if you want to use multiple "
            "metastores.")
        pass
    print "Connecting to remote datastore (%s)" % (addr, )
    _store = RemoteStore(addr, port)

# Helper functions, so people can use metastore.get() and metastore.put()
def get(key):
    return get_store().get(key)
    
def put(key, value):
    get_store().put(key, value)

def multiget(key):
    return get_store().multiget(key)
    

# If invoked using command line, read datafile and port as optional arguments
# and start a metastore server
if __name__ == '__main__':
    import sys

    datafile = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATAFILE
    port     = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PORT

    s = MetaServer(datafile, int(port))
    s.serve()