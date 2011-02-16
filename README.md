# metastore README

This module provides a basic persistent key-value store. Can be used in-process for local operations, and remotely through XML-RPC. Makes use of sqlite for persisting data.

It was written to gather simulation metrics from a distributed simulation, with convenience and ease of use as its only requirement. This is not a high performance datastore in any sense.

# Usage

The `metastore` module can either be used as a local in-process store, or as a remote store.

## Local use

If running everything in one process, it is easiest just to import the `metastore` module, and start getting and putting values. This is what I use when testing locally, it imports `sqlite3` and writes directly to the sqlite database.

    import metastore
    metastore.put("foo", "bar")
    metastore.get("foo")
  
Optionally, to specify the sqlite database:

    import metastore
    metastore.get_store("path/to/store.sdb")
    metastore.put("foo", "bar")
    metastore.get("foo")
  
## Remote usage

If running on multiple machines (or in multiple processes), running a central `metastore` server process may be desirable (see below how to start a server). Worker machines/processes can then connect to the remote server by invoking the `use_remote` method.

    import metastore
    metastore.use_remote("machine.running.metastore.server.com")
    metastore.put("foo", "bar")
    metastore.get("foo")

## Start a server from command line

    $ python metastore/__init__.py
  
Optionally, to specify the sqlite database:

    $ python metastore/__init__.py path/to/store.sdb

Optionally, to specify the listening port:

    $ python metastore/__init__.py path/to/store.sdb 1234

In case you want to run the server on a machine behind a firewall, consider taking a look at [PageKite](http://pagekite.net/).

## Start a server from within Python

    import metastore
    s = metastore.MetaServer()
    s.serve()

Optionally, to specify the sqlite database:

    import metastore
    s = metastore.MetaServer(datafile="path/to/store.sdb")
    s.serve()

Optionally, to specify the listening port:

    import metastore
    s = metastore.MetaServer(port=1234)
    s.serve()

# Example usage on the DAS3

This module was originally written to gather some simulation metrics on the  [DAS3](http://www.cs.vu.nl/das3/) cluster. Nothing fancy, but beats writing metrics to text files and parsing them later.

First, make sure you have a Python module loaded. I use Python/2.5.2

    module load python/2.5.2

Started the `metastore` server on the head node:

    $ python metastore/__init__.py simulation_123.sdb 1234

Have each worker process write to the head node:

    import metastore
    metastore.use_remote("fs0.das3.cs.vu.nl", 1234)
    metastore.put("foo", "bar")

## Running the server on a worker node

The [DAS usage policy](http://www.cs.vu.nl/das3/usage.shtml) states:

> Program execution MUST be done on the compute nodes, NEVER on a headnode.

Therefore, you should ideally run the `metastore` server on a compute node, or
designate one of your worker processes to also run the `metastore` server.

In my experience, the `metastore` server process uses limited resources - at least under my workload (<10 req/sec). So, I decided to run the server on the head node. If you are on the DAS3, do what ever you think is best. If in doubt, consult with the DAS3 admins.

The following should work, but I haven't tested it. Make sure that the `metastore` server job you submit won't expire before the workers that are writing to the store. Here I use the anti-social switch and a timeout of two hours (which the DAS admins won't like during working hours).

    prun -asocial -t 2:00:00 -np 1 -v python metastore/__init__.py simulation_123.sdb 1234

This should output something like:
    
    Run on 1 hosts for 7200 seconds from Wed Feb 16 17:07:13 2011
    : node083/0

And then you point your worker nodes to `node083`:

    import metastore
    metastore.use_remote("node083", 1234)
    metastore.put("foo", "bar")

# Credits and licence

Written by Bjorn Patrick Swift <bjorn@swift.is> in February 2011.

Licensed under a [Creative Commons Attribution 3.0 Unported License](http://creativecommons.org/licenses/by/3.0/).
