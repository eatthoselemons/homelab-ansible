"""
Storage validation tests using testinfra.
Tests LVM, filesystems, mounts, and disk configuration.
"""

import pytest


class TestStorage:
    """Test storage configuration."""
    
    def test_lvm_installed(self, host):
        """Test that LVM tools are installed."""
        pkg = host.package("lvm2")
        assert pkg.is_installed, "LVM2 package is not installed"
    
    def test_volume_groups(self, host):
        """Test that volume groups are configured."""
        cmd = host.run("vgs --noheadings -o vg_name")
        
        if cmd.rc == 0 and cmd.stdout.strip():
            vgs = [vg.strip() for vg in cmd.stdout.strip().split('\n')]
            assert len(vgs) > 0, "No volume groups found"
            
            # Check each VG has some free space or allocated space
            for vg in vgs:
                vg_info = host.run(f"vgs {vg} --noheadings -o vg_free,vg_size --units g")
                assert vg_info.rc == 0, f"Cannot get info for VG {vg}"
        else:
            # LVM might not be used in all setups
            pytest.skip("No LVM volume groups configured (might be expected)")
    
    def test_logical_volumes(self, host):
        """Test logical volumes if LVM is used."""
        cmd = host.run("lvs --noheadings -o lv_name,vg_name")
        
        if cmd.rc == 0 and cmd.stdout.strip():
            lvs = cmd.stdout.strip().split('\n')
            assert len(lvs) > 0, "LVM configured but no logical volumes found"
    
    def test_filesystem_mounts(self, host):
        """Test that important filesystems are mounted."""
        critical_mounts = ["/", "/boot"]
        
        for mount_point in critical_mounts:
            mount = host.mount_point(mount_point)
            assert mount.exists, f"{mount_point} is not mounted"
            
            # Check filesystem type (should not be tmpfs for these)
            if mount_point == "/":
                assert mount.filesystem not in ["tmpfs", "devtmpfs"], \
                    f"Root filesystem is {mount.filesystem}, expected real filesystem"
    
    def test_disk_space(self, host):
        """Test that there is sufficient disk space."""
        # Check root filesystem
        root_mount = host.mount_point("/")
        if root_mount.exists:
            # Get disk usage percentage
            cmd = host.run("df -h / | tail -1 | awk '{print $5}' | sed 's/%//'")
            if cmd.rc == 0:
                usage = int(cmd.stdout.strip())
                assert usage < 90, f"Root filesystem is {usage}% full (critical)"
                
                if usage > 80:
                    pytest.warn(f"Root filesystem is {usage}% full (warning)")
    
    def test_swap_configured(self, host):
        """Test that swap is configured (optional)."""
        cmd = host.run("swapon --show --noheadings")
        
        if cmd.rc == 0 and cmd.stdout.strip():
            # Swap is configured
            swap_lines = cmd.stdout.strip().split('\n')
            total_swap = host.run("free -m | grep Swap | awk '{print $2}'")
            if total_swap.rc == 0:
                swap_mb = int(total_swap.stdout.strip())
                assert swap_mb > 0, "Swap is configured but has 0 size"
        else:
            # Swap might not be needed
            pytest.skip("No swap configured (might be intentional)")
    
    def test_filesystem_types(self, host):
        """Test that appropriate filesystems are used."""
        # Get all mounted filesystems
        cmd = host.run("mount -t ext4,xfs,btrfs,zfs")
        
        if cmd.rc == 0:
            # At least one proper filesystem should be mounted
            assert cmd.stdout.strip(), "No standard filesystems (ext4/xfs/btrfs/zfs) found"
    
    def test_zfs_if_configured(self, host):
        """Test ZFS configuration if ZFS is installed."""
        zfs_installed = host.run("which zfs").rc == 0
        
        if zfs_installed:
            # Check for ZFS pools
            pools_cmd = host.run("zpool list -H -o name")
            if pools_cmd.rc == 0 and pools_cmd.stdout.strip():
                pools = pools_cmd.stdout.strip().split('\n')
                assert len(pools) > 0, "ZFS installed but no pools configured"
                
                # Check pool health
                for pool in pools:
                    health_cmd = host.run(f"zpool status {pool} | grep 'state:' | awk '{{print $2}}'")
                    if health_cmd.rc == 0:
                        state = health_cmd.stdout.strip()
                        assert state == "ONLINE", f"ZFS pool {pool} is {state}, expected ONLINE"
        else:
            pytest.skip("ZFS not installed")
    
    def test_nfs_utils_if_needed(self, host):
        """Test NFS utilities if NFS mounts are configured."""
        nfs_mounts = host.run("mount -t nfs,nfs4 | wc -l")
        
        if nfs_mounts.rc == 0 and int(nfs_mounts.stdout.strip()) > 0:
            # NFS is being used, check tools
            pkg = host.package("nfs-common") or host.package("nfs-utils")
            assert pkg.is_installed, "NFS mounts exist but NFS utilities not installed"
    
    def test_fstab_syntax(self, host):
        """Test that /etc/fstab has valid syntax."""
        fstab = host.file("/etc/fstab")
        
        if fstab.exists:
            # Check syntax with mount command
            cmd = host.run("mount --fake --all")
            assert cmd.rc == 0, f"Invalid /etc/fstab syntax: {cmd.stderr}"
    
    def test_disk_encryption_if_configured(self, host):
        """Test disk encryption if LUKS is used."""
        luks_cmd = host.run("lsblk -o NAME,FSTYPE | grep crypto_LUKS")
        
        if luks_cmd.rc == 0 and luks_cmd.stdout.strip():
            # LUKS is configured
            cryptsetup = host.package("cryptsetup")
            assert cryptsetup.is_installed, "LUKS volumes exist but cryptsetup not installed"
            
            # Check that LUKS volumes are opened
            luks_status = host.run("dmsetup ls --target crypt")
            assert luks_status.rc == 0, "Cannot check LUKS device mapper status"
            assert luks_status.stdout.strip(), "LUKS configured but no volumes are opened"
    
    @pytest.mark.parametrize("important_dir", ["/var", "/tmp", "/home"])
    def test_important_directories_writable(self, host, important_dir):
        """Test that important directories are writable."""
        test_file = f"{important_dir}/.test_write_{host.system_info.hostname}"
        cmd = host.run(f"touch {test_file} && rm {test_file}")
        assert cmd.rc == 0, f"Cannot write to {important_dir}"