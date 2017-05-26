# -*- mode: ruby -*-
# vi: set ft=ruby :
VAGRANTFILE_API_VERSION = "2"

PROD = (ENV['PROD'] || 0).to_i
HOME = ENV['HOME']

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.ssh.insert_key = false

  config.vm.provider "virtualbox" do |vbox, override|
    override.vm.box = "centos/7"
    if PROD == 1
        vbox.memory = 1024
    else
        vbox.memory = 2048
    end
    vbox.cpus = 2

    # Enable multiple guest CPUs if available
    vbox.customize ["modifyvm", :id, "--ioapic", "on"]
  end

  config.vm.provider "libvirt" do |libvirt, override|
    libvirt.cpus = 2
    if PROD == 1
        libvirt.memory = 1024
    else
        libvirt.memory = 2048
    end
    libvirt.driver = 'kvm'
    override.vm.box = "centos/7"
    override.vm.box_download_checksum = "b2a9f7421e04e73a5acad6fbaf4e9aba78b5aeabf4230eebacc9942e577c1e05"
    override.vm.box_download_checksum_type = "sha256"
  end

  # vagrant-cachier setup
  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
    config.cache.synced_folder_opts = {
      type: :nfs,
      mount_options: ['rw', 'vers=3', 'tcp', 'nolock']
    }
  end

  config.vm.synced_folder ".", "/home/vagrant/sync", disabled: true

  if PROD == 1
      num_nodes = 2
      inventory_path = "provisions/hosts.vagrant"
  else
      inventory_path = "provisions/hosts.vagrant.minimal"
      num_nodes = 1
  end

  # Ensure Jenkins SSH keys exist
  system('if [ ! -f /tmp/cccp-jenkins.key ]; then ssh-keygen -t rsa -N "" -f /tmp/cccp-jenkins.key; fi')

  rsync_ssh_opts = "-e 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i " + HOME + "/.vagrant.d/insecure_private_key'"

  config.vm.define "master" do |master|
    master.vm.hostname = "cccp"
    master.vm.network :private_network, ip: "192.168.100.100"
    master.vm.network :forwarded_port, guest: 8443, host: 8443
    config.vm.provision "shell", inline: "nmcli connection reload; systemctl restart NetworkManager.service; setenforce 0"
    config.vm.synced_folder "./", "/opt/cccp-service", type: "rsync"
    master.vm.provision "ansible" do |ansible|
      ansible.limit = 'all'
      ansible.sudo = true
      ansible.inventory_path = inventory_path
      ansible.playbook = "provisions/vagrant.yml"
      ansible.raw_arguments = [
          "-u",
          "vagrant",
          "--extra-vars",
          '{"rsync_ssh_opts": "' + rsync_ssh_opts + '"}',
      ]
    end
  end

  if PROD != 1
    config.vm.synced_folder "./", "/opt/cccp-service", type: "rsync"
    config.vm.synced_folder "./", "/home/vagrant/cccp-service", type: "rsync"
  end

  num_nodes.times do |n|
    node_index = n+1
    config.vm.define "node#{node_index}" do |node|
      node.vm.hostname = "cccp-#{node_index}"
      node.vm.network :private_network, ip: "192.168.100.#{200 + n}"
      node.vm.synced_folder ".", "/home/vagrant/sync", disabled: true
      node.vm.synced_folder "./", "/opt/cccp-service", type: "rsync"
      node.vm.synced_folder "./", "/home/vagrant/cccp-service", type: "rsync"
      node.vm.provision "shell", inline: "setenforce 0"
      # config.vm.provision "shell", inline: "nmcli connection reload; systemctl restart NetworkManager.service"
    end
  end

  if PROD == 1
      config.vm.post_up_message = <<-EOF
You have successfully setup CentOS Community Container Pipeline
Endpoints:
=================Registry================
https://192.168.100.200:5000/
=================Jenkins=================
http://192.168.100.100:8080/
User: admin Password: admin
================Openshift================
https://192.168.100.201:8443
User: test-admin Password: test
"Happy hacking!
EOF
  else
      config.vm.post_up_message = <<-EOF
You have successfully setup CentOS Community Container Pipeline
Endpoints:
=================Registry================
https://192.168.100.100:5000/
=================Jenkins=================
http://192.168.100.100:8080/
User: admin Password: admin
================Openshift================
https://192.168.100.200:8443
User: test-admin Password: test
"Happy hacking!
EOF
  end
end
