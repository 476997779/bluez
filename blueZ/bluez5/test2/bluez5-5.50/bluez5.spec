Name:       bluez5

%define _system_groupadd() getent group %{1} >/dev/null || groupadd -g 1002 %{1}

Summary:    Bluetooth daemon
Version:    5.50+git1
Release:    1.1.9
Group:      Applications/System
License:    GPLv2+
URL:        http://www.bluez.org/
Source0:    http://www.kernel.org/pub/linux/bluetooth/%{name}-%{version}.tar.gz
Source1:    obexd-wrapper
Source2:    obexd.conf
Source3:    bluez.tracing
Source4:    obexd.tracing
Requires:   bluez5-libs = %{version}
Requires:   dbus >= 0.60
Requires:   hwdata >= 0.215
Requires:   bluez5-configs
Requires:   systemd
Requires:   oneshot
# /etc/obexd.conf requires find
Requires:   findutils
Requires(pre): /usr/sbin/groupadd
Requires(preun): systemd
Requires(post): systemd
Requires(postun): systemd
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(libusb)
BuildRequires:  pkgconfig(udev)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(check)
BuildRequires:  pkgconfig(libical)
BuildRequires:  bison
BuildRequires:  flex
BuildRequires:  readline
BuildRequires:  readline-devel
BuildRequires:  automake
BuildRequires:  autoconf
Conflicts: bluez

%description
%{summary}.

%package configs-mer
Summary:    Bluetooth (bluez5) default configuration
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}
Provides:   bluez5-configs
Conflicts:  bluez-configs-mer
%description configs-mer
%{summary}.

%package cups
Summary:    Bluetooth (bluez5) CUPS support
Group:      System/Daemons
Requires:   %{name} = %{version}-%{release}
Requires:   cups
Conflicts:  bluez-cups
%description cups
%{summary}.

%package doc
Summary:    Bluetooth (bluez5) daemon documentation
Group:      Documentation
Requires:   %{name} = %{version}-%{release}
Conflicts:  bluez-doc
%description doc
%{summary}.

%package hcidump
Summary:    Bluetooth (bluez5) packet analyzer
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}
Conflicts:  bluez-hcidump
%description hcidump
%{summary}.

%package libs
Summary:    Bluetooth (bluez5) library
Group:      System/Libraries
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig
Conflicts:  bluez-libs
%description libs
%{summary}.

%package libs-devel
Summary:    Bluetooth (bluez5) library development package
Group:      Development/Libraries
Requires:   bluez5-libs = %{version}
Conflicts:  bluez-libs-devel
%description libs-devel
%{summary}.

%package test
Summary:    Test utilities for Bluetooth (bluez5)
Group:      Development/Tools
Requires:   %{name} = %{version}-%{release}
Requires:   %{name}-libs = %{version}
Requires:   dbus-python
Requires:   pygobject2 >= 3.10.2
Conflicts:  bluez-test
%description test
%{summary}.

%package tools
Summary:    Command line tools for Bluetooth (bluez5)
Group:      Applications/System
Requires:   %{name} = %{version}-%{release}
Conflicts:  bluez-tools
%description tools
%{summary}.

%package obexd
Summary:    OBEX server (bluez5)
Group:      System/Daemons
Requires:   %{name} = %{version}-%{release}
Requires:   obex-capability
Conflicts:  obexd
Conflicts:  obexd-server
%description obexd
%{summary}.

%package obexd-tools
Summary:    Command line tools for OBEX (bluez5)
Group:      Applications/System
%description obexd-tools
%{summary}.

%package tracing
Summary:    Configuration for bluez5 to enable tracing
Group:      Development/Tools
Requires:   %{name} = %{version}-%{release}
Conflicts:  bluez-tracing
%description tracing
Will enable tracing for BlueZ 5

%package obexd-tracing
Summary:    Configuration for bluez5-obexd to enable tracing
Group:      Development/Tools
%description obexd-tracing
Will enable tracing for BlueZ 5 OBEX daemon

%prep
%setup -q -n %{name}-%{version}

./bootstrap

%build
autoreconf --force --install

%configure \
    --enable-option-checking \
    --enable-library \
    --enable-sixaxis \
    --enable-test \
    --with-systemdsystemunitdir=/lib/systemd/system \
    --with-systemduserunitdir=/usr/lib/systemd/user \
    --enable-jolla-dbus-access \
    --enable-jolla-did \
    --enable-jolla-logcontrol \
    --enable-sailfish-exclude \
    --with-phonebook=sailfish \
    --with-contentfilter=helperapp \
    --enable-jolla-blacklist \
    --disable-hostname \
    --enable-deprecated \
    --disable-autopair

make %{?jobs:-j%jobs}

%check
# run unit tests
#make check

%install
rm -rf %{buildroot}
%make_install


# bluez systemd integration
mkdir -p $RPM_BUILD_ROOT/%{_lib}/systemd/system/network.target.wants
ln -s ../bluetooth.service $RPM_BUILD_ROOT/%{_lib}/systemd/system/network.target.wants/bluetooth.service
(cd $RPM_BUILD_ROOT/%{_lib}/systemd/system && ln -s bluetooth.service dbus-org.bluez.service)

# bluez runtime files
install -d -m 0755 $RPM_BUILD_ROOT/%{_localstatedir}/lib/bluetooth

# bluez configuration
mkdir -p ${RPM_BUILD_ROOT}%{_sysconfdir}/bluetooth
for CONFFILE in profiles/input/input.conf profiles/network/network.conf src/main.conf ; do
install -v -m644 ${CONFFILE} ${RPM_BUILD_ROOT}%{_sysconfdir}/bluetooth/`basename ${CONFFILE}`
done

mkdir -p %{buildroot}%{_sysconfdir}/tracing/bluez/
cp -a %{SOURCE3} %{buildroot}%{_sysconfdir}/tracing/bluez/

# obexd systemd/D-Bus integration
(cd $RPM_BUILD_ROOT/%{_libdir}/systemd/user && ln -s obex.service dbus-org.bluez.obex.service)

# obexd wrapper
install -m755 -D %{SOURCE1} ${RPM_BUILD_ROOT}/%{_libexecdir}/obexd-wrapper
install -m644 -D %{SOURCE2} ${RPM_BUILD_ROOT}/%{_sysconfdir}/obexd.conf
sed -i 's,Exec=.*,Exec=/usr/libexec/obexd-wrapper,' \
    ${RPM_BUILD_ROOT}/%{_datadir}/dbus-1/services/org.bluez.obex.service
sed -i 's,ExecStart=.*,ExecStart=/usr/libexec/obexd-wrapper,' \
${RPM_BUILD_ROOT}/%{_libdir}/systemd/user/obex.service

# obexd configuration
mkdir -p ${RPM_BUILD_ROOT}/%{_sysconfdir}/obexd/{plugins,noplugins}

# HACK!! copy manually missing tools
cp -a tools/bluetooth-player %{buildroot}%{_bindir}/
cp -a tools/btmgmt %{buildroot}%{_bindir}/
cp -a attrib/gatttool %{buildroot}%{_bindir}/
cp -a tools/obex-client-tool %{buildroot}%{_bindir}/
cp -a tools/obex-server-tool %{buildroot}%{_bindir}/
cp -a tools/obexctl %{buildroot}%{_bindir}/

# HACK!! copy manually missing test scripts
cp -a test/exchange-business-cards %{buildroot}%{_libdir}/bluez/test/
cp -a test/get-managed-objects %{buildroot}%{_libdir}/bluez/test/
cp -a test/get-obex-capabilities %{buildroot}%{_libdir}/bluez/test/
cp -a test/list-folders %{buildroot}%{_libdir}/bluez/test/
cp -a test/simple-obex-agent %{buildroot}%{_libdir}/bluez/test/

mkdir -p %{buildroot}%{_sysconfdir}/tracing/obexd/
cp -a %{SOURCE4} %{buildroot}%{_sysconfdir}/tracing/obexd/

# Rename pkg-config file to differentiate from BlueZ 4.x
mv %{buildroot}%{_libdir}/pkgconfig/bluez.pc %{buildroot}%{_libdir}/pkgconfig/bluez5.pc

%pre
%_system_groupadd bluetooth

%preun
if [ "$1" -eq 0 ]; then
systemctl stop bluetooth.service ||:
fi

%post
%{_bindir}/groupadd-user bluetooth
systemctl daemon-reload ||:
systemctl reload-or-try-restart bluetooth.service ||:

%postun
systemctl daemon-reload ||:

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig


%preun obexd
if [ "$1" -eq 0 ]; then
systemctl-user stop obex.service ||:
fi

%post obexd
systemctl-user daemon-reload ||:
systemctl-user reload-or-try-restart obex.service ||:

%postun obexd
systemctl-user daemon-reload ||:

%files
%defattr(-,root,root,-)
%{_libexecdir}/bluetooth/bluetoothd
%{_libdir}/bluetooth/plugins/sixaxis.so
%{_datadir}/dbus-1/system-services/org.bluez.service
/%{_lib}/systemd/system/bluetooth.service
/%{_lib}/systemd/system/network.target.wants/bluetooth.service
/%{_lib}/systemd/system/dbus-org.bluez.service
%config %{_sysconfdir}/dbus-1/system.d/bluetooth.conf
%dir %{_localstatedir}/lib/bluetooth

%files configs-mer
%defattr(-,root,root,-)
%config %{_sysconfdir}/bluetooth/*

%files cups
%defattr(-,root,root,-)
%{_libdir}/cups/backend/bluetooth

%files doc
%defattr(-,root,root,-)
%doc %{_mandir}/man1/*.1.gz
%doc %{_mandir}/man8/*.8.gz

%files hcidump
%defattr(-,root,root,-)
%{_bindir}/hcidump

%files libs
%defattr(-,root,root,-)
%{_libdir}/libbluetooth.so.*

%files libs-devel
%defattr(-,root,root,-)
%{_libdir}/libbluetooth.so
%dir %{_includedir}/bluetooth
%{_includedir}/bluetooth/*
%{_libdir}/pkgconfig/bluez5.pc

%files test
%defattr(-,root,root,-)
%{_libdir}/bluez/test/*

%files tools
%defattr(-,root,root,-)
%{_bindir}/bccmd
%{_bindir}/bluetooth-player
%{_bindir}/bluemoon
%{_bindir}/bluetoothctl
%{_bindir}/btattach
%{_bindir}/btmgmt
%{_bindir}/btmon
%{_bindir}/ciptool
%{_bindir}/gatttool
%{_bindir}/hciattach
%{_bindir}/hciconfig
%{_bindir}/hcitool
%{_bindir}/hex2hcd
%{_bindir}/l2ping
%{_bindir}/l2test
%{_bindir}/mpris-proxy
%{_bindir}/rctest
%{_bindir}/rfcomm
%{_bindir}/sdptool
/%{_lib}/udev/hid2hci
/%{_lib}/udev/rules.d/97-hid2hci.rules

%files obexd
%defattr(-,root,root,-)
%config %{_sysconfdir}/obexd.conf
%dir %{_sysconfdir}/obexd/
%dir %{_sysconfdir}/obexd/plugins/
%dir %{_sysconfdir}/obexd/noplugins/
%attr(2755,root,privileged) %{_libexecdir}/bluetooth/obexd
%{_libexecdir}/obexd-wrapper
%{_datadir}/dbus-1/services/org.bluez.obex.service
%{_libdir}/systemd/user/obex.service
%{_libdir}/systemd/user/dbus-org.bluez.obex.service

%files obexd-tools
%defattr(-,root,root,-)
%{_bindir}/obex-client-tool
%{_bindir}/obex-server-tool
%{_bindir}/obexctl

%files tracing
%defattr(-,root,root,-)
%dir %{_sysconfdir}/tracing/bluez
%config %{_sysconfdir}/tracing/bluez/bluez.tracing

%files obexd-tracing
%defattr(-,root,root,-)
%dir %{_sysconfdir}/tracing/obexd
%config %{_sysconfdir}/tracing/obexd/obexd.tracing
%changelog
* Mon May  6 2019 Juho Hamalainen <jusa@hilvi.org> - 5.50+git1
- [bluetooth]#
- [bluetooth]# advertise.
- [bluetooth]# advertise.data 0x26 0x01 0x00
- [bluetooth]# advertise.discoverable on
- [bluetooth]# advertise.discoverable-timeout 10
- [bluetooth]# advertise.name blah
- [bluetooth]# advertise on
- [bluetooth]# advertise.uuids 0x1820
- [bluetooth]# appearance
- [bluetooth]# appearance 0x0001
- [bluetooth]# clear
- [bluetooth]# connect 9C:5C:F9:AB:C5:82
- [bluetooth]# data 0x26 0x01 0x01 0x00
- [bluetooth]# disconnect 9C:5C:F9:AB:C5:82
- [bluetooth]# disconnect dis5C:F9:AB:C5:82
- [bluetooth]# disconnect discoverable on
- [bluetooth]# discoverable on
- [bluetooth]# duplicate-data
- [bluetooth]# duplicate-data on
- [bluetooth]# duration
- [bluetooth]# duration 1
- [bluetooth]# manufacturer
- [bluetooth]# manufacturer 2 00
- [bluetooth]# menu gatt
- [bluetooth]# menu scan
- [bluetooth]# name
- [bluetooth]# name blah
- [bluetooth]# pathloss
- [bluetooth]# pathloss 0
- [bluetooth]# rssi
- [bluetooth]# rssi 0
- [bluetooth]# service
- [bluetooth]# service 0x1820 00 00 00
- [bluetooth]# set-advertise-duration 4
- [bluetooth]# set-advertise-manufacturer 0x75 0x02 0x03 0x04
- [bluetooth]# set-advertise-name Test
- [bluetooth]# set-advertise-timeout 4
- [bluetooth]# set-advertise-uuids 0x1824
- [bluetooth]# timeout
- [bluetooth]# timeout 1
- [bluetooth]# transport
- [bluetooth]# transport le
- [bluetooth]# tx-power
- [bluetooth]# tx-power on
- [bluetooth]# uuids
- [bluetooth]# uuids 0x1820
- [CHG] Controller 00:19:0E:11:55:44 ActiveInstances: 0x01
- [CHG] Controller 00:19:0E:11:55:44 SupportedInstances: 0x04
- [CHG] Controller 00:1B:DC:07:31:88 ActiveInstances: 0x01
- [CHG] Controller 00:1B:DC:07:31:88 SupportedInstances: 0x04
- [CHG] Controller 5C:E0:C5:34:AE:1C Discoverable: yes
- [CHG] Controller B8:8A:60:D8:17:D7 ActiveInstances: 0x00
- [CHG] Controller B8:8A:60:D8:17:D7 ActiveInstances: 0x01
- [CHG] Controller B8:8A:60:D8:17:D7 SupportedInstances: 0x04
- [CHG] Controller B8:8A:60:D8:17:D7 SupportedInstances: 0x05
- [CHG] Device 00:1B:DC:07:31:88 AdvertisingData Key: 0x26
- [CHG] Device 00:1B:DC:07:31:88 AdvertisingData Value:
- [config: Target = 0100]# app-get 0100 1000
- [config: Target = 0100]# composition-get 0
- [config: Target = 0100]# hb-pub-get
- [config: Target = 0100]# hb-set 0100 0 0 0 0
- [config: Target = 0100]# hb-sub-get
- [config: Target = 0100]# hb-sub-set 0077 0100 2
- [config: Target = 0100]# ident-get 0
- [config: Target = 0100]# ident-set 0 1
- [config: Target = 0100]# proxy-get
- [config: Target = 0100]# proxy-set 1
- [config: Target = 0100]# pub-get 0100 1001
- [config: Target = 0100]# relay-get
- [config: Target = 0100]# relay-set 1 0 0
- [config: Target = 0100]# sub-add 0100 c000 1000
- [config: Target = 0100]# sub-get 0100 1000
- [mgmt]# add-adv --help
- [mgmt]# add-adv -u 180d -u 180f -d 080954657374204C45 1
- [sailfish] Backport GATT related fixes.
- [sailfish] Backport security and crash fixes.
- [sailfish] Update to BlueZ 5.50. Fixes JB#45383
* Fri Mar 15 2019 Juho Hamalainen <jusa.mer@hilvi.org> - 5.47+git11
- [sailfish] Add option to autodetect HIDP type. JB#44201
* Fri Jan 18 2019 Juho Hamalainen <jusa.mer@hilvi.org> - 5.47+git10
- [sailfish] Fix segfault when filtering service. JB#42087
- [sailfish] Handle uninitialized target safely on avrcp browse list. Fixes JB#41933
* Wed Jan  9 2019 Juho Hamalainen <jusa.mer@hilvi.org> - 5.47+git9
- [sailfish] New plugin for filtering services based on active profiles. JB#42087
* Thu Apr 12 2018 sage <marko.saukko@gmail.com> - 5.47+git8
- [packaging] Depend on findutils. Contributes to JB#41628
- [sailfish] Depend on findutils. Contributes to JB#41628
* Thu Mar 29 2018 Juho Hamalainen <jusa.mer@hilvi.org> - 5.47+git6
- [sailfish] avctp: Make avctp session reference counted. JB#41269
* Thu Mar  1 2018 jpoutiai <jarko.poutiainen@jollamobile.com> - 5.47+git5
- [sailfish] backporting upstream fixes. Contributes JB#40534
* Mon Feb 26 2018 jpoutiai <jarko.poutiainen@jollamobile.com> - 5.47+git4
- [sailfish] Enable mgmt tracing in tracing package. Fixes JB#41247
* Thu Dec 21 2017 jpoutiai <jarko.poutiainen@jollamobile.com> - 5.47+git3
- [bluez5] Bluez claims connected when remote not paired. JB#40534
* Fri Dec  8 2017 jpoutiai <jarko.poutiainen@jollamobile.com> - 5.47+git2
- [bluez5] Disable autopair plugin. JB#40419
* Thu Oct  5 2017 Juho Hämäläinen <juho.hamalainen@jolla.com> - 5.47+git1
- [...]
- [00:1B:DC:07:33:4E]# pull /home/vcard.vcf
- [12] for message waiting indication group types)."
- [168988.557647] input: bluez-input-device as /devices/virtual/misc/uhid/input54
- [1]: http://0pointer.de/public/systemd-man/machine-info.html
- [1] https://github.com/ftonello/bluez/
- [1] "The service definition ends before the next service declaration
- [2]: http://www.freedesktop.org/wiki/Software/systemd/hostnamed
- [40:88:05:14:3A:7A]# cp * /tmp/all.vcf
- [40:88:05:14:3A:7A]# cp *.vcf /tmp/all.vcf
- [Attributes]
- [bluetooth]# advertise
- [bluetooth]# advertise off
- [bluetooth]# advertise on
- [bluetooth]# connect 7B:3F:2C:2B:D0:06
- [bluetooth]# power on
- [bluetooth]# register-application
- [bluetooth]# register-application 12345678-1234-5678-1234-56789abcdef1
- [bluetooth]# register-service 00001820-0000-1000-8000-00805f9b34fb
- [bluetooth]# scan off
- [bluetooth]# scan on
- [bluetooth]# set-advertise-appearance 128
- [bluetooth]# set-advertise-appearance on
- [bluetooth]# set-advertise-manufacturer 0xffff 0x00 0x01 0x02 0x03
- [bluetooth]# set-advertise-name blah
- [bluetooth]# set-advertise-name bleh
- [bluetooth]# set-advertise-name on
- [bluetooth]# set-advertise-service 180D 0xff 0xff
- [bluetooth]# set-advertise-tx-power on
- [bluetooth]# set-advertise-uuids 180D 180F
- [bluetooth]# set-scan-filter-reset-data on
- [bluetooth]# set-scan-filter-rssi -69
- [bluetooth]# set-scan-filter-rssi -90
- [bluetooth]# set-scan-filter-transport le
- [bluetooth]# set-scan-filter-uuids babe
- [bluetooth]# unregister-application
- [bluetooth]# unregister-service /org/bluez/app/service0x92a150
- [CHG] Attribute /org/bluez/hci1/dev_00_1B_DC_07_31_88/service001f/char0020 WriteAcquired: no
- [CHG] Attribute /org/bluez/hci1/dev_00_1B_DC_07_31_88/service001f/char0020 WriteAcquired: yes
- [CHG] Attribute /org/bluez/hci1/dev_56_A0_AA_D0_12_FF/service001f/char0020 NotifyAcquired: yes
- [CHG] Attribute /org/bluez/hci1/dev_69_16_5B_9A_06_CD/service001f/char0020 NotifyAcquired: no
- [CHG] Controller 00:1A:7D:DA:71:13 Discovering: no
- [CHG] Controller 00:1A:7D:DA:71:13 Discovering: yes
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 0000110a-0000-1000-8000-00805f9b34fb
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 0000110b-0000-1000-8000-00805f9b34fb
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 0000110c-0000-1000-8000-00805f9b34fb
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 0000110e-0000-1000-8000-00805f9b34fb
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 00001112-0000-1000-8000-00805f9b34fb
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 0000112d-0000-1000-8000-00805f9b34fb
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 00001200-0000-1000-8000-00805f9b34fb
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 00001800-0000-1000-8000-00805f9b34fb
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 00001801-0000-1000-8000-00805f9b34fb
- [CHG] Controller 00:1B:DC:07:31:88 UUIDs: 00001820-0000-1000-8000-00805f9b34fb
- [CHG] Controller B8:8A:60:D8:17:D7 AdvertisementInstances: 0x04
- [CHG] Controller B8:8A:60:D8:17:D7 AdvertisementInstances: 0x05
- [CHG] Controller B8:8A:60:D8:17:D7 Discovering: yes
- [CHG] Device 00:1B:DC:07:31:88 RSSI: -27
- [CHG] Device 00:1B:DC:07:31:88 RSSI: -31
- [CHG] Device 00:1B:DC:07:31:88 ServiceData Key: 00001827-0000-1000-8000-00805f9b34fb
- [CHG] Device 00:1B:DC:07:31:88 ServiceData Value: 0x00
- [CHG] Device 00:1B:DC:07:31:88 ServiceData Value: 0xdd
- [CHG] Device 14:99:E2:0E:AC:6B ManufacturerData Key: 0x004c
- [CHG] Device 14:99:E2:0E:AC:6B ManufacturerData Value: 0x00
- [CHG] Device 14:99:E2:0E:AC:6B ManufacturerData Value: 0x03
- [CHG] Device 14:99:E2:0E:AC:6B ManufacturerData Value: 0x06
- [CHG] Device 14:99:E2:0E:AC:6B ManufacturerData Value: 0x09
- [CHG] Device 14:99:E2:0E:AC:6B ManufacturerData Value: 0x19
- [CHG] Device 14:99:E2:0E:AC:6B RSSI: -75
- [CHG] Device 14:99:E2:0E:AC:6B RSSI: -80
- [CHG] Device 39:5B:8F:12:84:2E RSSI: -30
- [CHG] Device 44:89:1C:C5:67:94 RSSI: -58
- [CHG] Device 44:89:1C:C5:67:94 RSSI: -59
- [CHG] Device 44:89:1C:C5:67:94 RSSI: -64
- [CHG] Device 44:89:1C:C5:67:94 RSSI: -65
- [CHG] Device 44:89:1C:C5:67:94 RSSI: -66
- [CHG] Device 44:89:1C:C5:67:94 RSSI: -75
- [CHG] Device 44:89:1C:C5:67:94 RSSI: -76
- [CHG] Device 44:89:1C:C5:67:94 RSSI: -81
- [CHG] Device 44:89:1C:C5:67:94 RSSI: -82
- [CHG] Device 44:89:1C:C5:67:94 RSSI is nil
- [CHG] Device 44:89:1C:C5:67:94 TxPower: -21
- [CHG] Device 44:89:1C:C5:67:94 TxPower is nil
- [CHG] Device 7B:3F:2C:2B:D0:06 Connected: yes
- [CHG] Device 7B:3F:2C:2B:D0:06 ServicesResolved: yes
- [CHG] Device 7B:3F:2C:2B:D0:06 UUIDs: 00001800-0000-1000-8000-00805f9b34fb
- [CHG] Device 7B:3F:2C:2B:D0:06 UUIDs: 00001801-0000-1000-8000-00805f9b34fb
- [CHG] Device 7B:3F:2C:2B:D0:06 UUIDs: 0000180f-0000-1000-8000-00805f9b34fb
- [CHG] Device F0:79:59:2F:D6:5A RSSI: -86
- [CHG] Device F0:79:59:2F:D6:5A RSSI: -87
- [CHG] Device XX:XX:XX:XX:XX:XX UUIDs:
- [CHG] Device XX:XX:XX:XX:XX:XX UUIDs has unsupported type
- [CHG] /org/bluez/hci1/dev_56_A0_AA_D0_12_FF/service001f/char0020 Notification:
- [CHG] Player /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX/player0 Position: 0x000000
- [CHG] Player /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX/player0 Position: 0xffffffff
- [CHG] Player /org/bluez/hci0/dev_XX_XX_XX_XX_XX_XX/player0 Status: playing
- [CHG] Transfer /org/bluez/obex/client/session0/transfer0 Status: complete
- [CHG] Transfer /org/bluez/obex/client/session7/transfer29 Status: error
- [CHG] Transfer /org/bluez/obex/client/session7/transfer30 Status: active
- [CHG] Transfer /org/bluez/obex/client/session7/transfer30 Status: complete
- [CHG] Transfer /org/bluez/obex/client/session7/transfer30 Transferred: 12255 (@4KB/s)
- [CHG] Transfer /org/bluez/obex/client/session7/transfer30 Transferred: 20425 (@8KB/s)
- [CHG] Transfer /org/bluez/obex/client/session7/transfer30 Transferred: 24510 (@4KB/s)
- [CHG] Transfer /org/bluez/obex/client/session7/transfer30 Transferred: 4085 (@4KB/s)
- [CHG] Transfer /org/bluez/obex/client/session7/transfer30 Transferred: 8170 (@4KB/s)
- [DEL] Characteristic
- [DEL] Descriptor
- [DEL] ObjectPush /org/bluez/obex/client/session0
- [DEL] Primary Service
- [DEL] Session /org/bluez/obex/client/session0 [default]
- [DEL] Transfer /org/bluez/obex/client/session0/transfer0
- [DEL] Transfer /org/bluez/obex/client/session7/transfer29
- [DEL] Transfer /org/bluez/obex/client/session7/transfer30
- [GATT client]#
- [GATT client]# read-value 0x00D9
- [GATT client]# read-value 0x01E2
- [GATT client]# set-security 2
- [hci1]# find --help
- [   ][                 ][LE]> '
- [meshctl]# security
- [meshctl]# security 2
- [mgmt]# ==2224== Invalid read of size 1
- [NEW] Characteristic
- [NEW] Descriptor
- [NEW] Device 39:5B:8F:12:84:2E 39-5B-8F-12-84-2E
- [NEW] ObjectPush /org/bluez/obex/client/session0
- [NEW] Primary Service
- [NEW] Session /org/bluez/obex/client/session0 [default]
- [NEW] Transfer /org/bluez/obex/client/session0/transfer0
- [NEW] Transfer /org/bluez/obex/client/session7/transfer29
- [NEW] Transfer /org/bluez/obex/client/session7/transfer30
- [obex]# connect 00:1B:DC:07:33:4E 00001105-0000-1000-8000-00805f9b34fb
- [/org/bluez/app/service0x8c2610] Primary (yes/no): yes
- [/org/bluez/app/service0x902610/chrc0x91d690/desc0x9095a0] Enter value: 00
- [PHILIPS BTM2180]# disconnect
- [sailfish] sdp: Fix Out-of-bounds heap read in service_search_attr_req function. Fixes JB#39703
- [sailfish] Update packaging and update to Bluez 5.47.
- [sys-assert]cs timestr 1358524835
- [sys_assert]END of sighandler
- [sys-assert]exepath = bluetoothd
- [sys-assert]processname = bluetoothd
- [sys_assert]START of sighandler
- [sys-assert]start print_node_to_file
- [sys_assert]this thread is main thread. pid=3353
- [Test peripheral:/service001f/char0020]# acquire-notify
- [Test peripheral:/service001f/char0020]# acquire-write
- [Test peripheral:/service001f/char0020]# release-notify
- [Test peripheral:/service001f/char0020]# release-write
- [Test peripheral:/service001f/char0020]# write 00
- [up to 126 bytes of Provider Name][whitespace][up to 127 bytes of
- [up to 127 bytes of Provider Name][whitespace + Service Description,
- [-Werror=override-init]
- [-Werror,-Waddress-of-packed-member]
- [-Werror,-Wcast-align]
- [-Werror,-Wformat]
- [-Werror,-Wincompatible-pointer-types-discards-qualifiers]
- [-Werror,-Wsometimes-uninitialized]
- [-Werror,-Wstrncat-size]
- [-Werror,-Wtautological-constant-out-of-range-compare]
- [-Wimplicit-function-declaration]
