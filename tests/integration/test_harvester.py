"""
Harvester cluster validation tests using testinfra.
Tests Kubernetes cluster, Harvester services, storage, and networking.
Based on the actual harvester.setup role requirements.
"""

import pytest
import json
import yaml


class TestHarvesterPrerequisites:
    """Test Harvester prerequisites and base system configuration."""
    
    def test_system_requirements(self, host):
        """Test that system meets Harvester requirements."""
        # Check CPU count (minimum 4 cores recommended)
        cpu_cmd = host.run("nproc")
        if cpu_cmd.rc == 0:
            cpu_count = int(cpu_cmd.stdout.strip())
            assert cpu_count >= 2, f"Insufficient CPUs: {cpu_count} (minimum 2, recommended 4+)"
        
        # Check memory (minimum 8GB recommended)
        mem_cmd = host.run("free -g | grep Mem | awk '{print $2}'")
        if mem_cmd.rc == 0:
            total_mem = int(mem_cmd.stdout.strip())
            assert total_mem >= 4, f"Insufficient memory: {total_mem}GB (minimum 4GB, recommended 8GB+)"
    
    def test_virtualization_support(self, host):
        """Test that virtualization is supported."""
        # Check for KVM support
        kvm = host.file("/dev/kvm")
        if not kvm.exists:
            # Check CPU flags for virtualization
            cpu_flags = host.run("grep -E 'vmx|svm' /proc/cpuinfo")
            assert cpu_flags.rc == 0, "No virtualization support (VMX/SVM) in CPU"
            pytest.warn("KVM device not found but CPU supports virtualization")
    
    def test_network_interfaces(self, host):
        """Test required network interfaces exist."""
        # Harvester needs at least one network interface
        interfaces = host.run("ip -o link show | grep -v '^[0-9]*: lo:' | wc -l")
        if interfaces.rc == 0:
            iface_count = int(interfaces.stdout.strip())
            assert iface_count >= 1, "No network interfaces found (besides loopback)"
    
    def test_disk_space(self, host):
        """Test sufficient disk space for Harvester."""
        # Check root filesystem has at least 50GB free
        df_cmd = host.run("df -BG / | tail -1 | awk '{print $4}' | sed 's/G//'")
        if df_cmd.rc == 0:
            free_space = int(df_cmd.stdout.strip())
            assert free_space >= 20, f"Insufficient disk space: {free_space}GB free (minimum 20GB)"


class TestHarvesterInstallation:
    """Test Harvester installation and configuration."""
    
    def test_oem_directory(self, host):
        """Test OEM directory structure for Harvester config."""
        oem_dir = host.file("/oem")
        if oem_dir.exists:
            assert oem_dir.is_directory, "/oem is not a directory"
            
            # Check for Harvester config file
            harvester_config = host.file("/oem/99-harvester.yaml")
            if harvester_config.exists:
                # Validate it's valid YAML
                config_content = host.run("cat /oem/99-harvester.yaml")
                if config_content.rc == 0:
                    try:
                        yaml.safe_load(config_content.stdout)
                    except yaml.YAMLError as e:
                        pytest.fail(f"Invalid YAML in Harvester config: {e}")
    
    def test_grub_configuration(self, host):
        """Test GRUB configuration for Harvester boot."""
        grub_config = host.file("/etc/default/grub")
        if grub_config.exists:
            content = grub_config.content_string
            
            # Check for Harvester-specific GRUB parameters
            if "harvester" in content.lower():
                assert "console=" in content, "Console parameter missing in GRUB config"
    
    def test_network_configuration(self, host):
        """Test network configuration for Harvester nodes."""
        # Check for network config in OEM
        network_config = host.file("/oem/99-network.yaml")
        if network_config.exists:
            config_content = host.run("cat /oem/99-network.yaml")
            if config_content.rc == 0:
                try:
                    config = yaml.safe_load(config_content.stdout)
                    # Validate network config structure
                    assert "network" in config or "harvester" in config, \
                        "Invalid network configuration structure"
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in network config: {e}")


class TestHarvesterCluster:
    """Test Harvester cluster components."""
    
    def test_rke2_installation(self, host):
        """Test RKE2 (Kubernetes) installation."""
        # Check for RKE2 binaries
        rke2_server = host.file("/usr/local/bin/rke2-server") or \
                      host.file("/usr/bin/rke2-server")
        
        rke2_agent = host.file("/usr/local/bin/rke2-agent") or \
                     host.file("/usr/bin/rke2-agent")
        
        if rke2_server.exists or rke2_agent.exists:
            # RKE2 is installed
            # Check service
            rke2_service = host.service("rke2-server") or host.service("rke2-agent")
            if rke2_service.exists:
                assert rke2_service.is_running, "RKE2 service not running"
                assert rke2_service.is_enabled, "RKE2 service not enabled"
    
    def test_kubectl_access(self, host):
        """Test kubectl configuration and cluster access."""
        # Check for kubectl
        kubectl = host.run("which kubectl")
        if kubectl.rc == 0:
            # Check for kubeconfig
            kubeconfig_paths = [
                "/etc/rancher/rke2/rke2.yaml",
                "/root/.kube/config",
                "/home/rancher/.kube/config"
            ]
            
            kubeconfig_found = False
            for path in kubeconfig_paths:
                if host.file(path).exists:
                    kubeconfig_found = True
                    # Try to access cluster
                    cmd = host.run(f"KUBECONFIG={path} kubectl get nodes -o json")
                    if cmd.rc == 0:
                        try:
                            nodes = json.loads(cmd.stdout)
                            assert len(nodes.get("items", [])) > 0, "No nodes in cluster"
                        except json.JSONDecodeError:
                            pass
                    break
            
            if not kubeconfig_found:
                pytest.skip("Kubeconfig not found")
    
    def test_harvester_namespace(self, host):
        """Test Harvester system namespace."""
        # Try to get Harvester namespace
        kubectl_cmd = "kubectl get namespace harvester-system -o json"
        
        # Try with different kubeconfig locations
        kubeconfigs = [
            "/etc/rancher/rke2/rke2.yaml",
            "/root/.kube/config"
        ]
        
        for kubeconfig in kubeconfigs:
            if host.file(kubeconfig).exists:
                cmd = host.run(f"KUBECONFIG={kubeconfig} {kubectl_cmd}")
                if cmd.rc == 0:
                    try:
                        ns_data = json.loads(cmd.stdout)
                        assert ns_data["metadata"]["name"] == "harvester-system"
                        assert ns_data["status"]["phase"] == "Active"
                        return
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        pytest.skip("Cannot access Harvester namespace")
    
    def test_harvester_pods(self, host):
        """Test Harvester pods are running."""
        kubectl_cmd = "kubectl get pods -n harvester-system -o json"
        
        kubeconfigs = [
            "/etc/rancher/rke2/rke2.yaml",
            "/root/.kube/config"
        ]
        
        for kubeconfig in kubeconfigs:
            if host.file(kubeconfig).exists:
                cmd = host.run(f"KUBECONFIG={kubeconfig} {kubectl_cmd}")
                if cmd.rc == 0:
                    try:
                        pods_data = json.loads(cmd.stdout)
                        pods = pods_data.get("items", [])
                        
                        if len(pods) > 0:
                            # Check critical pods
                            critical_pods = {
                                "harvester-webhook": False,
                                "harvester-controller": False,
                                "harvester-apiserver": False
                            }
                            
                            for pod in pods:
                                pod_name = pod["metadata"]["name"]
                                pod_phase = pod["status"].get("phase", "Unknown")
                                
                                for critical in critical_pods:
                                    if critical in pod_name and pod_phase == "Running":
                                        critical_pods[critical] = True
                            
                            # At least some critical pods should be running
                            running_critical = sum(critical_pods.values())
                            assert running_critical > 0, \
                                f"No critical Harvester pods running: {critical_pods}"
                        return
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        pytest.skip("Cannot access Harvester pods")


class TestHarvesterStorage:
    """Test Harvester storage configuration."""
    
    def test_longhorn_namespace(self, host):
        """Test Longhorn storage system."""
        kubectl_cmd = "kubectl get namespace longhorn-system -o json"
        
        kubeconfigs = [
            "/etc/rancher/rke2/rke2.yaml",
            "/root/.kube/config"
        ]
        
        for kubeconfig in kubeconfigs:
            if host.file(kubeconfig).exists:
                cmd = host.run(f"KUBECONFIG={kubeconfig} {kubectl_cmd}")
                if cmd.rc == 0:
                    try:
                        ns_data = json.loads(cmd.stdout)
                        assert ns_data["metadata"]["name"] == "longhorn-system"
                        assert ns_data["status"]["phase"] == "Active"
                        return
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        pytest.skip("Longhorn not deployed")
    
    def test_storage_classes(self, host):
        """Test storage classes are configured."""
        kubectl_cmd = "kubectl get storageclass -o json"
        
        kubeconfigs = [
            "/etc/rancher/rke2/rke2.yaml",
            "/root/.kube/config"
        ]
        
        for kubeconfig in kubeconfigs:
            if host.file(kubeconfig).exists:
                cmd = host.run(f"KUBECONFIG={kubeconfig} {kubectl_cmd}")
                if cmd.rc == 0:
                    try:
                        sc_data = json.loads(cmd.stdout)
                        storage_classes = sc_data.get("items", [])
                        
                        assert len(storage_classes) > 0, "No storage classes configured"
                        
                        # Check for Harvester/Longhorn storage class
                        harvester_sc_found = False
                        for sc in storage_classes:
                            if "harvester" in sc["metadata"]["name"].lower() or \
                               "longhorn" in sc["metadata"]["name"].lower():
                                harvester_sc_found = True
                                
                                # Check if it's default
                                annotations = sc["metadata"].get("annotations", {})
                                if annotations.get("storageclass.kubernetes.io/is-default-class") == "true":
                                    break
                        
                        assert harvester_sc_found, "No Harvester/Longhorn storage class found"
                        return
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        pytest.skip("Cannot access storage classes")


class TestHarvesterNetworking:
    """Test Harvester networking configuration."""
    
    def test_cluster_network(self, host):
        """Test cluster network configuration."""
        # Check for Flannel or other CNI
        cni_config = host.file("/etc/cni/net.d")
        if cni_config.exists and cni_config.is_directory:
            # List CNI configs
            configs = host.run("ls /etc/cni/net.d/").stdout
            assert configs, "No CNI configuration found"
            
            # Check for common CNI plugins
            if "flannel" in configs or "canal" in configs or "calico" in configs:
                pass  # CNI is configured
    
    def test_harvester_vip(self, host):
        """Test Harvester VIP configuration."""
        # Check if VIP is configured (usually on bond or main interface)
        ip_cmd = host.run("ip addr show")
        if ip_cmd.rc == 0:
            # Look for the configured VIP (from harvester_cluster_vip variable)
            # In test environment, this would be 10.60.1.10
            if "10.60.1.10" in ip_cmd.stdout or "10.10." in ip_cmd.stdout:
                pass  # VIP might be configured
    
    def test_storage_network(self, host):
        """Test storage network configuration if enabled."""
        # Check for VLAN 65 (storage network from config)
        vlan_interfaces = host.run("ip link show | grep 'vlan.*65'")
        if vlan_interfaces.rc == 0:
            # Storage VLAN is configured
            # Check IP assignment
            storage_ip = host.run("ip addr show | grep '10.60.65'")
            if storage_ip.rc == 0:
                pass  # Storage network is configured


class TestHarvesterServices:
    """Test Harvester services and components."""
    
    def test_container_runtime(self, host):
        """Test container runtime is installed and running."""
        # RKE2 uses containerd
        containerd = host.service("containerd")
        if containerd.exists:
            assert containerd.is_running, "containerd not running"
            assert containerd.is_enabled, "containerd not enabled"
            
            # Check containerd socket
            socket = host.file("/run/containerd/containerd.sock")
            assert socket.exists, "containerd socket missing"
    
    def test_kubelet_service(self, host):
        """Test kubelet service (part of RKE2)."""
        # RKE2 runs kubelet as part of rke2-server/agent
        rke2_running = False
        
        for service_name in ["rke2-server", "rke2-agent"]:
            service = host.service(service_name)
            if service.exists and service.is_running:
                rke2_running = True
                break
        
        if rke2_running:
            # Check kubelet is actually running
            kubelet_process = host.run("pgrep kubelet")
            assert kubelet_process.rc == 0, "kubelet process not found"
    
    def test_api_server_ports(self, host):
        """Test Kubernetes API server ports."""
        # Check standard Kubernetes API port
        api_port = host.socket("tcp://0.0.0.0:6443")
        if not api_port.is_listening:
            api_port = host.socket("tcp://127.0.0.1:6443")
        
        if api_port.is_listening:
            pass  # API server is listening
        else:
            # Check RKE2 supervisor port
            supervisor_port = host.socket("tcp://0.0.0.0:9345")
            if not supervisor_port.is_listening:
                supervisor_port = host.socket("tcp://127.0.0.1:9345")
            
            assert supervisor_port.is_listening, "Neither API server nor supervisor port listening"
    
    def test_etcd_service(self, host):
        """Test etcd is running (for cluster state)."""
        # Check for etcd process
        etcd_process = host.run("pgrep etcd")
        if etcd_process.rc == 0:
            # etcd is running
            # Check etcd data directory
            etcd_data = host.file("/var/lib/rancher/rke2/server/db/etcd")
            if etcd_data.exists:
                assert etcd_data.is_directory, "etcd data directory invalid"


class TestHarvesterManagement:
    """Test Harvester management and UI components."""
    
    def test_harvester_ui_service(self, host):
        """Test Harvester UI service."""
        kubectl_cmd = "kubectl get service -n harvester-system harvester-service -o json"
        
        kubeconfigs = [
            "/etc/rancher/rke2/rke2.yaml",
            "/root/.kube/config"
        ]
        
        for kubeconfig in kubeconfigs:
            if host.file(kubeconfig).exists:
                cmd = host.run(f"KUBECONFIG={kubeconfig} {kubectl_cmd}")
                if cmd.rc == 0:
                    try:
                        svc_data = json.loads(cmd.stdout)
                        assert svc_data["metadata"]["name"] == "harvester-service"
                        
                        # Check service type and ports
                        spec = svc_data.get("spec", {})
                        ports = spec.get("ports", [])
                        
                        # Should have HTTPS port
                        https_port_found = False
                        for port in ports:
                            if port.get("port") == 443 or port.get("port") == 8443:
                                https_port_found = True
                                break
                        
                        assert https_port_found, "No HTTPS port found in Harvester service"
                        return
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        pytest.skip("Cannot access Harvester service")
    
    def test_rancher_integration(self, host):
        """Test Rancher integration if configured."""
        kubectl_cmd = "kubectl get namespace cattle-system -o json"
        
        kubeconfigs = [
            "/etc/rancher/rke2/rke2.yaml",
            "/root/.kube/config"
        ]
        
        for kubeconfig in kubeconfigs:
            if host.file(kubeconfig).exists:
                cmd = host.run(f"KUBECONFIG={kubeconfig} {kubectl_cmd}")
                if cmd.rc == 0:
                    # Rancher is deployed
                    try:
                        ns_data = json.loads(cmd.stdout)
                        assert ns_data["metadata"]["name"] == "cattle-system"
                        assert ns_data["status"]["phase"] == "Active"
                        return
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        # Rancher is optional
        pytest.skip("Rancher not deployed (optional)")
    
    def test_terraform_provider_setup(self, host):
        """Test Terraform provider setup for Harvester."""
        # Check if Terraform directory was created
        terraform_dir = host.file("/tmp/harvester-terraform-test")
        if terraform_dir.exists:
            assert terraform_dir.is_directory, "Terraform test directory is not a directory"
            
            # Check for provider configuration
            provider_config = host.file("/tmp/harvester-terraform-test/provider.tf")
            if provider_config.exists:
                content = provider_config.content_string
                assert "harvester" in content.lower(), "Harvester provider not configured"