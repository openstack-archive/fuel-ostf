fuel-ostf-tests
===============

In order to start tests you will need to perform next commands:
    fab unit
    fab testall

Ideally tests should be runned with tox, e.g:
    tox -e py27

    or

    tox

OSTF with Murano
----------------

If you want to test Murano with OSTF, you need to prepare your environment.  
To run tests you will need an image, which contains murano-agent.  
You can download the image here:  

    http://murano-files.mirantis.com/ubuntu_14_04-murano-agent_stable_juno.qcow2
    
Or you can create your own using this diskimage-builder:  

    git clone https://git.openstack.org/openstack/diskimage-builder.git
    git clone https://git.openstack.org/stackforge/murano-agent.git
    export ELEMENTS_PATH=murano-agent/contrib/elements
    diskimage-builder/bin/disk-image-create vm ubuntu murano-agent -o ubuntu-murano-agent.qcow2
  
After these steps, you will need import your image into your environment via  
glance or using Horizon Dashboard.

If you want to use glance from console:  
1. SCP your image to node, where located OS controller.
2. SSH to node. 
3. Use these commands:  
    
    . openrc
    glance image-create --disk-format qcow2 --container-format bare --name ubuntu-murano < ubuntu-murano.qcow2
    
If you want to use Horizon Dashboard:  
1. Login into Horizon Dashboard  
2. Navigate to Project-Compute-Images  
3. Click "Create image"  
4. Specify parameters and select image source.

Then you should navigate to Murano-Manage-Images and mark your uploaded image 
with murano tag.

Now, you can start OSTF tests that using Murano component.
