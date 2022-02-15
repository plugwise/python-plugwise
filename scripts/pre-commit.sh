#!/usr/bin/env bash
grep -r --include="*.xml" '<short_id>' userdata/* | grep -v 'abcdefgh' && echo "COMMIT REJECTED, found a real short_id, modify domain_objects and set short_id to abcdefgh!" && exit 1
grep -r --include="*.xml" '<wifi_ip>' userdata/* | grep -v '_ip></wifi' | grep -v '127.0.0.' && echo "COMMIT REJECTED, found a WIFI ip address, modify domain_objects and set wifi_ip to 127.0.0.1!" && exit 1
grep -r --include="*.xml" 'lan_ip>' userdata/* | grep -v '_ip></lan' | grep -v '127.0.0.' && echo "COMMIT REJECTED, found a LAN ip address, modify domain_objects and set lan_ip to 127.0.0.1!" && exit 1
grep -Er --include="*.xml" "([0-9]{1,3}[\.]){3}[0-9]{1,3}" userdata/* | grep -Ev '127.0.0.|0.0.0.0' && echo "COMMIT REJECTED, found ip addresses in the logging, modify domain_objects and set them to 127.0.0.1!" && exit 1
grep -r --include="*.xml" '<hostname>' userdata/* | grep -v 'smile000000' | grep -v 'stretch000000' && echo "COMMIT REJECTED, found a Smile(/Stretch) hostname, modify system_status or domain_objects and set hostname to smile000000!" && exit 1
grep -r --include="*.xml" '<longitude>' userdata/* | grep -v '4.49' && echo "COMMIT REJECTED, found your hometown, modify domain_objects and set longitude to 4.49 (that is: Plugwise HQ)!" && exit 1
grep -r --include="*.xml" '<latitude>' userdata/* | grep -v '52.21' && echo "COMMIT REJECTED, found your hometown, modify domain_objects and set latitude to 52.21 (that is: Plugwise HQ)!" && exit 1
grep -r --include="*.xml" '<city>' userdata/* | grep -v 'Sassenheim' && echo "COMMIT REJECTED, found your hometown, modify domain_objects and set city to Sassenheim (that is: Plugwise HQ)!" && exit 1
grep -r --include="*.xml" '<postal_code>' userdata/* | grep -v '2171' && echo "COMMIT REJECTED, found your hometown, modify domain_objects and set postal_code to 2171 (that is: Plugwise HQ)!" && exit 1
# No problems found
exit 0
