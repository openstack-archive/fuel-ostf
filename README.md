Team and repository tags
========================

[![Team and repository tags](http://governance.openstack.org/badges/fuel-ostf.svg)](http://governance.openstack.org/reference/tags/index.html)

<!-- Change things from this point on -->

Fuel OSTF tests
===============
After OpenStack installation via Fuel, it is very important to understand whether it was successful and if it is ready for work. Fuel-ostf provides a set of health checks to be run against from Fuel console check the proper operation of all system components in typical conditions.

Details of Fuel OSTF tests
==========================
Tests are included to Fuel, so they will be accessible as soon as you install Fuel on your lab. Fuel ostf  architecture is quite simple, it consists of two main packages:
<ul>
  <li>fuel_health which contains the test set itself and related modules</li>
  <li>fuel_plugin which contains OSTF-adapter that forms necessary test list in context of cluster deployment options and transfers them to UI using REST_API</li>
</ul>

On the other hand, there is some information necessary for test execution itself. There are several modules that gather information and parse them into objects which will be used in the tests themselves.
All information is gathered from Nailgun component.

Python REST API interface
=========================
Fuel-ostf module provides not only testing, but also RESTful interface, a means for interaction with the components.

In terms of REST, all types of OSTF entities are managed by three HTTP verbs: GET, POST and PUT.

The following basic URL is used to make requests to OSTF:

    {ostf_host}:{ostf_port}/v1/{requested_entity}/{cluster_id}

Currently, you can get information about testsets, tests and testruns via GET request on corresponding URLs for ostf_plugin.

To get information about testsets, make the following GET request on:

    {ostf_host}:{ostf_port}/v1/testsets/{cluster_id}

To get information about tests, make GET request on:

    {ostf_host}:{ostf_port}/v1/tests/{cluster_id}

To get information about executed tests, make the following GET requests:

for the whole set of testruns:

    {ostf_host}:{ostf_port}/v1/testruns/

for the particular testrun:

    {ostf_host}:{ostf_port}/v1/testruns/{testrun_id}

for the list of testruns executed on the particular cluster:

    {ostf_host}:{ostf_port}/v1/testruns/last/{cluster_id}

To start test execution, make the following POST request on this URL:

    {ostf_host}:{ostf_port}/v1/testruns/


The body must consist of JSON data structure with testsets and the list of tests belonging to it that must be executed. It should also have metadata with the information about the cluster (the key with the “cluster_id” name is used to store the parameter’s value):

    [
        {
            "testset": "test_set_name",
            "tests": ["module.path.to.test.1", ..., "module.path.to.test.n"],
            "metadata": {"cluster_id": id}
        },

    ...,

    {...}, # info for another testrun
    {...},

    ...,

    {...}
    ]

If succeeded, OSTF adapter returns attributes of created testrun entities in JSON format. If you want to launch only one test, put its id into the list. To launch all tests, leave the list empty (by default). Example of the response:

    [
    {
        "status": "running",
        "testset": "sanity",
        "meta": null,
        "ended_at": "2014-12-12 15:31:54.528773",
        "started_at": "2014-12-12 15:31:41.481071",
        "cluster_id": 1,
        "id": 1,
        "tests": [.....info on tests.....]
    },

    ....
    ]

You can also stop and restart testruns. To do that, make a PUT request on testruns. The request body must contain the list of the testruns and tests to be stopped or restarted. Example:

    [
    {
        "id": test_run_id,
        "status": ("stopped" | "restarted"),
        "tests": ["module.path.to.test.1", ..., "module.path.to.test.n"]
    },

    ...,

    {...}, # info for another testrun
    {...},

    ...,

    {...}
    ]


Testing
==========
There are next test targets that can be run to validate the code.

    tox -e pep8 - style guidelines enforcement
    tox -e py27 - unit and integration testing
