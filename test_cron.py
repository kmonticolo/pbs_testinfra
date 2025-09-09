def test_crontab_contains_entry(host):
    expected_entry = "0 */3 * * * make -C /root/testinfra > /tmp/test_check_pve_backups.log 2>&1"
    
    crontab = host.check_output("crontab -l -u root")
    assert expected_entry in crontab, "Cron entry has not been found"


