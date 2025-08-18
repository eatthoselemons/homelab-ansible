"""
Harvester cluster validation tests using testinfra.
Tests Kubernetes cluster, Harvester services, and storage.
"""

import pytest
import json


class TestHarvester:
    """Test Harvester cluster configuration."""
    
    def test_kubectl_installed(self, host):
        """Test that kubectl is installed and configured."""
        kubectl = host.run("which kubectl")
        assert kubectl.rc == 0, "kubectl is not installed"
        
        # Check kubectl version
        version = host.run("kubectl version --client --output=json")
        if version.rc == 0:
            try:
                version_data = json.loads(version.stdout)
                assert "clientVersion" in version_data, "Cannot get kubectl version"
            except json.JSONDecodeError:
                # Older kubectl might not support JSON output
                pass
    
    def test_kubernetes_service(self, host):
        """Test that Kubernetes services are running."""
        # Harvester uses RKE2
        k8s_services = [
            "rke2-server",
            "rke2-agent",
            "k3s",
            "k3s-agent"
        ]
        
        found_service = None
        for service in k8s_services:
            svc = host.service(service)
            if svc.exists and svc.is_running:
                found_service = service
                break
        
        assert found_service, "No Kubernetes service running (rke2/k3s)"
        
        # Check service is enabled
        svc = host.service(found_service)
        assert svc.is_enabled, f"{found_service} is not enabled"
    
    def test_cluster_access(self, host):
        """Test access to Kubernetes cluster."""
        # Try to get nodes
        nodes_cmd = host.run("kubectl get nodes -o json")
        
        if nodes_cmd.rc != 0:
            # Might need sudo or different kubeconfig
            nodes_cmd = host.run("sudo kubectl get nodes -o json")
        
        assert nodes_cmd.rc == 0, f"Cannot access cluster: {nodes_cmd.stderr}"
        
        try:
            nodes_data = json.loads(nodes_cmd.stdout)
            node_count = len(nodes_data.get("items", []))
            assert node_count > 0, "No nodes in cluster"
            
            # Check node status
            not_ready = []
            for node in nodes_data.get("items", []):
                node_name = node["metadata"]["name"]
                conditions = node["status"].get("conditions", [])
                
                ready = False
                for condition in conditions:
                    if condition["type"] == "Ready" and condition["status"] == "True":
                        ready = True
                        break
                
                if not ready:
                    not_ready.append(node_name)
            
            assert not not_ready, f"Nodes not ready: {not_ready}"
            
        except (json.JSONDecodeError, KeyError) as e:
            pytest.fail(f"Cannot parse nodes data: {e}")
    
    def test_harvester_namespace(self, host):
        """Test that Harvester namespace exists."""
        ns_cmd = host.run("kubectl get namespace harvester-system -o json")
        
        if ns_cmd.rc != 0:
            ns_cmd = host.run("sudo kubectl get namespace harvester-system -o json")
        
        if ns_cmd.rc == 0:
            # Harvester namespace exists
            try:
                ns_data = json.loads(ns_cmd.stdout)
                assert ns_data["metadata"]["name"] == "harvester-system"
                assert ns_data["status"]["phase"] == "Active"
            except (json.JSONDecodeError, KeyError):
                pass
        else:
            pytest.skip("Harvester namespace not found (might not be fully deployed)")
    
    def test_harvester_pods(self, host):
        """Test that Harvester pods are running."""
        pods_cmd = host.run("kubectl get pods -n harvester-system -o json")
        
        if pods_cmd.rc != 0:
            pods_cmd = host.run("sudo kubectl get pods -n harvester-system -o json")
        
        if pods_cmd.rc == 0:
            try:
                pods_data = json.loads(pods_cmd.stdout)
                pod_count = len(pods_data.get("items", []))
                
                if pod_count > 0:
                    # Check pod status
                    not_running = []
                    for pod in pods_data.get("items", []):
                        pod_name = pod["metadata"]["name"]
                        phase = pod["status"].get("phase", "Unknown")
                        
                        if phase not in ["Running", "Succeeded"]:
                            not_running.append(f"{pod_name} ({phase})")
                    
                    assert not not_running, f"Pods not running: {not_running}"
                else:
                    pytest.skip("No Harvester pods found")
                    
            except (json.JSONDecodeError, KeyError) as e:
                pytest.warn(f"Cannot parse pods data: {e}")
        else:
            pytest.skip("Cannot access Harvester pods")
    
    def test_storage_class(self, host):
        """Test that storage classes are configured."""
        sc_cmd = host.run("kubectl get storageclass -o json")
        
        if sc_cmd.rc != 0:
            sc_cmd = host.run("sudo kubectl get storageclass -o json")
        
        if sc_cmd.rc == 0:
            try:
                sc_data = json.loads(sc_cmd.stdout)
                storage_classes = sc_data.get("items", [])
                
                assert len(storage_classes) > 0, "No storage classes configured"
                
                # Check for default storage class
                has_default = False
                for sc in storage_classes:
                    annotations = sc["metadata"].get("annotations", {})
                    if annotations.get("storageclass.kubernetes.io/is-default-class") == "true":
                        has_default = True
                        break
                
                assert has_default, "No default storage class configured"
                
            except (json.JSONDecodeError, KeyError) as e:
                pytest.warn(f"Cannot parse storage class data: {e}")
    
    def test_container_runtime(self, host):
        """Test that container runtime is installed and running."""
        # Check for containerd (used by RKE2/K3s)
        containerd = host.service("containerd")
        if containerd.exists:
            assert containerd.is_running, "containerd is not running"
            assert containerd.is_enabled, "containerd is not enabled"
        else:
            # Check for docker
            docker = host.service("docker")
            if docker.exists:
                assert docker.is_running, "docker is not running"
                assert docker.is_enabled, "docker is not enabled"
            else:
                pytest.fail("No container runtime found (containerd/docker)")
    
    def test_cluster_networking(self, host):
        """Test cluster networking components."""
        # Check for CNI plugins
        cni_dir = host.file("/opt/cni/bin")
        if cni_dir.exists:
            assert cni_dir.is_directory, "/opt/cni/bin is not a directory"
            
            # Check for common CNI plugins
            cni_plugins = ["bridge", "flannel", "host-local", "loopback"]
            for plugin in cni_plugins:
                plugin_file = host.file(f"/opt/cni/bin/{plugin}")
                if plugin_file.exists:
                    assert plugin_file.mode == 0o755 or plugin_file.mode == 0o775, \
                        f"CNI plugin {plugin} is not executable"
    
    def test_longhorn_if_configured(self, host):
        """Test Longhorn storage if configured."""
        longhorn_ns = host.run("kubectl get namespace longhorn-system")
        
        if longhorn_ns.rc != 0:
            longhorn_ns = host.run("sudo kubectl get namespace longhorn-system")
        
        if longhorn_ns.rc == 0:
            # Longhorn is deployed
            pods_cmd = host.run("kubectl get pods -n longhorn-system -o json")
            if pods_cmd.rc != 0:
                pods_cmd = host.run("sudo kubectl get pods -n longhorn-system -o json")
            
            if pods_cmd.rc == 0:
                try:
                    pods_data = json.loads(pods_cmd.stdout)
                    
                    # Check for essential Longhorn components
                    components = {
                        "longhorn-manager": False,
                        "longhorn-driver": False,
                        "longhorn-ui": False
                    }
                    
                    for pod in pods_data.get("items", []):
                        pod_name = pod["metadata"]["name"]
                        for component in components:
                            if component in pod_name:
                                if pod["status"].get("phase") == "Running":
                                    components[component] = True
                    
                    missing = [k for k, v in components.items() if not v]
                    assert not missing, f"Missing Longhorn components: {missing}"
                    
                except (json.JSONDecodeError, KeyError) as e:
                    pytest.warn(f"Cannot validate Longhorn: {e}")
    
    def test_rancher_if_configured(self, host):
        """Test Rancher if configured."""
        rancher_ns = host.run("kubectl get namespace cattle-system")
        
        if rancher_ns.rc != 0:
            rancher_ns = host.run("sudo kubectl get namespace cattle-system")
        
        if rancher_ns.rc == 0:
            # Rancher is deployed
            rancher_pod = host.run("kubectl get pods -n cattle-system -l app=rancher -o json")
            if rancher_pod.rc != 0:
                rancher_pod = host.run("sudo kubectl get pods -n cattle-system -l app=rancher -o json")
            
            if rancher_pod.rc == 0:
                try:
                    pods_data = json.loads(rancher_pod.stdout)
                    pod_count = len(pods_data.get("items", []))
                    assert pod_count > 0, "No Rancher pods found"
                    
                    # Check if Rancher pods are running
                    for pod in pods_data.get("items", []):
                        phase = pod["status"].get("phase")
                        assert phase == "Running", f"Rancher pod not running: {phase}"
                        
                except (json.JSONDecodeError, KeyError) as e:
                    pytest.warn(f"Cannot validate Rancher: {e}")
    
    @pytest.mark.parametrize("port", [6443, 9345])
    def test_api_server_ports(self, host, port):
        """Test that Kubernetes API server ports are listening."""
        # Check if port is listening
        socket = host.socket(f"tcp://0.0.0.0:{port}")
        if not socket.is_listening:
            # Try localhost
            socket = host.socket(f"tcp://127.0.0.1:{port}")
        
        assert socket.is_listening, f"Kubernetes API port {port} is not listening"