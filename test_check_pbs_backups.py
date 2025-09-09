import datetime
import pytest
import testinfra

BACKUP_STORAGE = "backup1"

def collect_vmids(host):
    """Collect VM and CT ID"""
    vmids = []

    qm = host.run("/usr/sbin/qm list | awk 'NR>1 {print $1}'")
    if qm.rc == 0:
        vmids.extend(qm.stdout.strip().split())

    pct = host.run("/usr/sbin/pct list | awk 'NR>1 {print $1}'")
    if pct.rc == 0:
        vmids.extend(pct.stdout.strip().split())

    return vmids

def pytest_generate_tests(metafunc):
    if "vmid" in metafunc.fixturenames:
        host = testinfra.get_host("local://")
        vmids = collect_vmids(host)
        metafunc.parametrize("vmid", vmids)

def test_backup_is_fresh(host, vmid):
    """Checks whether a backup has been performed for a given VM/CT within the last 24 hours"""
    now = datetime.datetime.utcnow()

    cmd = host.run(f"/usr/sbin/pvesm list {BACKUP_STORAGE} --vmid {vmid} | tail -1")
    assert cmd.rc == 0, f"{vmid}: command error `pvesm`"
    
    line = cmd.stdout.strip()
    assert line, f"{vmid}: no backup"

    try:
        date_str = line.split()[0].split("/")[-1]  # ex. 2025-05-15T19:00:04Z
        backup_time = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        pytest.fail(f"{vmid}: error parsing backup date: {e}")

    delta = now - backup_time
    assert delta.total_seconds() <= 87400, f"{vmid}: backup older than 24h ({delta})"

def test_log_file_size(host):
    log_file = host.file("/tmp/test_check_pve_backups.log")

    assert log_file.exists, "File does not exists"
    assert log_file.is_file, "This is not a file"
    assert log_file.size >= 1024, f"The file only has {log_file.size} bytes – not enough"
