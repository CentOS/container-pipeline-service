# -*- mode: ruby -*-
# vi: set ft=ruby :
VAGRANTFILE_API_VERSION = "2"

unless Vagrant.has_plugin?("vagrant-hostmanager")
  raise 'vagrant-hostmanager plugin is required'
end

ALLINONE = (ENV['ALLINONE'] || 0).to_i

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.provision :hostmanager
  config.hostmanager.manage_host = true
  config.hostmanager.include_offline = true
  config.ssh.insert_key = false

  config.vm.provider "virtualbox" do |vbox, override|
    override.vm.box = "centos/7"
    if ALLINONE == 1
        vbox.memory = 2048
    else
        vbox.memory = 1024
    end
    vbox.cpus = 2

    # Enable multiple guest CPUs if available
    vbox.customize ["modifyvm", :id, "--ioapic", "on"]
  end

  if Vagrant.has_plugin?("vagrant-cachier")
    # Configure cached packages to be shared between instances of the same base box.
    # More info on http://fgrehm.viewdocs.io/vagrant-cachier/usage
    config.cache.scope = :box

    # OPTIONAL: If you are using VirtualBox, you might want to use that to enable
    # NFS for shared folders. This is also very useful for vagrant-libvirt if you
    # want bi-directional sync
    config.cache.synced_folder_opts = {
      type: :nfs,
      # The nolock option can be useful for an NFSv3 client that wants to avoid the
      # NLM sideband protocol. Without this option, apt-get might hang if it tries
      # to lock files needed for /var/cache/* operations. All of this can be avoided
      # by using NFSv4 everywhere. Please note that the tcp option is not the default.
      mount_options: ['rw', 'vers=3', 'tcp', 'nolock']
    }
    # For more information please check http://docs.vagrantup.com/v2/synced-folders/basic_usage.html
  end

  config.vm.provider "libvirt" do |libvirt, override|
    libvirt.cpus = 2
    libvirt.memory = 1024
    libvirt.driver = 'kvm'
    override.vm.box = "centos/7"
    override.vm.box_download_checksum = "b2a9f7421e04e73a5acad6fbaf4e9aba78b5aeabf4230eebacc9942e577c1e05"
    override.vm.box_download_checksum_type = "sha256"
  end

  config.vm.synced_folder ".", "/home/vagrant/sync", disabled: true

  num_nodes = 2
  if ALLINONE == 1
      inventory_path = "provisions/hosts.vagrant.allinone"
      num_nodes = 0
  else
      inventory_path = "provisions/hosts.vagrant"
  end

  config.vm.define "master" do |master|
    master.vm.hostname = "cccp"
    master.vm.network :private_network, ip: "192.168.100.100"
    master.vm.network :forwarded_port, guest: 8443, host: 8443
    config.vm.provision "shell", inline: "nmcli connection reload; systemctl restart NetworkManager.service"
    master.vm.provision "ansible" do |ansible|
      ansible.limit = 'all'
      ansible.sudo = true
      ansible.inventory_path = inventory_path
      ansible.playbook = "provisions/vagrant.yml"
      ansible.raw_arguments = [
      ]
    end
  end

  if ALLINONE == 1
    config.vm.synced_folder "./", "/opt/cccp-service", type: "rsync"
    config.vm.synced_folder "./", "/home/vagrant/cccp-service", type: "rsync"
  end

  num_nodes.times do |n|
    node_index = n+1
    config.vm.define "node#{node_index}" do |node|
      node.vm.hostname = "cccp-#{node_index}"
      node.vm.network :private_network, ip: "192.168.100.#{200 + n}"
      node.vm.synced_folder ".", "/home/vagrant/sync", disabled: true
      if n == 0
        node.vm.synced_folder "./", "/opt/cccp-service", type: "rsync"
      end

      if n == 1
        node.vm.synced_folder "./", "/home/vagrant/cccp-service", type: "rsync"
      end
      # config.vm.provision "shell", inline: "nmcli connection reload; systemctl restart NetworkManager.service"
    end
  end

  if ALLINONE == 1
      config.vm.post_up_message = <<-EOF
You have successfully setup CentOS Community Container Pipeline
Endpoints:
=================Registry================
https://cccp:5000/
=================Jenkins=================
http://cccp:8080/
User: admin Password: admin
================Openshift================
https://cccp:8443
User: test-admin Password: test
"Happy hacking!
EOF
  else
      config.vm.post_up_message = <<-EOF
You have successfully setup CentOS Community Container Pipeline
Endpoints:
=================Registry================
https://cccp-1:5000/
=================Jenkins=================
http://cccp:8080/
User: admin Password: admin
================Openshift================
https://cccp-2:8443
User: test-admin Password: test
"Happy hacking!
EOF
  end
end
