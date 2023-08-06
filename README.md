# Auto upgrade ZFS packages on Fedora

Installing OpenZFS on Fedora is easy ([instructions](
https://openzfs.github.io/openzfs-docs/Getting%20Started/Fedora/index.html)),
but *upgrading* the packages can be cumbersome.

The ZFS kernel modules are managed by dkms on Fedora. Sometimes running `dnf
upgrade` may cause issues, because the newest kernel on Fedora might be not
yet supported by OpenZFS. Also it's suggested that zfs packages should be
upgraded *before* kernel upgrades (see [this comment on GitHub](
https://github.com/openzfs/zfs/issues/9891#issuecomment-761979624)).

This tiny script aims to eliminate all the laborious manual work and do
the upgrades **in one shot**.

## Steps taken in this script

1. If zfs *can* be upgraded, run `dnf upgrade zfs*`.
2. If the target kernel version is not supported by the newest zfs package
   available on this system, run `dnf --exclude=kernel* upgrade`; otherwise
   run `dnf upgrade`.

The max kernel version supported by OpenZFS is retrieved from this link:

```
https://raw.githubusercontent.com/openzfs/zfs/zfs-<version>/META
```

dkms/dracut will be automatically invoked when installing/removing a kernel.
See these hooks:

```
/etc/kernel/install.d/dkms
/usr/lib/kernel/install.d/40-dkms.install
/usr/lib/kernel/install.d/50-dracut.install
```

## Usage

```
usage: dnf-upgrade-zfs.py [OPTIONS] [-- DNFOPTS...]

positional arguments:
  DNFOPTS               additional options for dnf, e.g. dnf-upgrade-zfs.py --
                        -y

options:
  -h, --help            show this help message and exit
  -v, --verbose         verbose mode
  -x PROXY, --proxy PROXY
                        proxy url, e.g. 'socks5h://127.0.0.1:8080'. See the
                        curl man page for details. Note that only requests
                        initiated by this script are affected by this option.
                        For requests initiated inside dnf, use the proxy=
                        setting in dnf.conf.

```

Examples:

```
# By default the user's confirmation is required before doing any upgrades
sudo ./dnf-upgrade-zfs.py

# Do the upgrades directly (by passing -y to dnf)
sudo ./dnf-upgrade-zfs.py -- -y
```

### Sample output

Skipped kernel updates because zfs 2.1.1 doesn't support kernel 5.15 in its
META file:

```
$ sudo ./dnf-upgrade-zfs.py
[INFO] __main__: Initializing dnf...
[INFO] dnf: Last metadata expiration check: 0:58:59 ago on Sat 04 Dec 2021 09:50:08 PM PST.
[INFO] __main__: Successfully initialized dnf
[INFO] __main__: Target version of 'zfs': None
[INFO] __main__: Installed versions of 'zfs': ['2.1.1']
[INFO] __main__: zfsMaxKernelVer=5.14
[INFO] __main__: Target version of 'kernel': 5.15.6
[INFO] __main__: Excluding kernel upgrades, because 5.15.6 > 5.14
[INFO] __main__: Upgrading all the packages...
Last metadata expiration check: 0:59:00 ago on Sat 04 Dec 2021 09:50:08 PM PST.
Dependencies resolved.
Nothing to do.
Complete!
```

Now zfs can be upgraded to 2.1.2 and it supports 5.15. So upgrade zfs first,
then upgrade kernel (the user's confirmation is required):

```
$ sudo ./dnf-upgrade-zfs.py
[INFO] __main__: Initializing dnf...
[INFO] dnf: Last metadata expiration check: 1:06:54 ago on Sun 19 Dec 2021 09:34:10 PM PST.
[INFO] __main__: Successfully initialized dnf
[INFO] __main__: Target version of 'zfs': 2.1.2
[INFO] __main__: Installed versions of 'zfs': ['2.1.1']
[INFO] __main__: zfsMaxKernelVer=5.15
[INFO] __main__: Target version of 'kernel': 5.15.8
[INFO] __main__: Upgrading zfs...
Last metadata expiration check: 1:06:57 ago on Sun 19 Dec 2021 09:34:10 PM PST.
Dependencies resolved.
=========================================================================
 Package          Architecture     Version           Repository     Size
=========================================================================
Upgrading:
 libnvpair3       x86_64           2.1.2-1.fc34      zfs            40 k
 libuutil3        x86_64           2.1.2-1.fc34      zfs            34 k
 libzfs5          x86_64           2.1.2-1.fc34      zfs           232 k
 libzpool5        x86_64           2.1.2-1.fc34      zfs           1.3 M
 zfs              x86_64           2.1.2-1.fc34      zfs           651 k
 zfs-dkms         noarch           2.1.2-1.fc34      zfs            29 M

Transaction Summary
=========================================================================
Upgrade  6 Packages

Total download size: 32 M
Is this ok [y/N]: y
Downloading Packages:
...
-------------------------------------------------------------------------
Total                                     23 MB/s |  32 MB     00:01
...
Running transaction
...

Loading new zfs-2.1.2 DKMS files...
Building for 5.14.18-200.fc34.x86_64
Building initial module for 5.14.18-200.fc34.x86_64
Done.

zavl.ko.xz:
Running module version sanity check.
 - Original module
   - This kernel never originally had a module by this name
 - Installation
   - Installing to /lib/modules/5.14.18-200.fc34.x86_64/extra/

znvpair.ko.xz:
Running module version sanity check.
 - Original module
   - This kernel never originally had a module by this name
 - Installation
   - Installing to /lib/modules/5.14.18-200.fc34.x86_64/extra/

...

depmod.....

...

Uninstall of zfs module (zfs-2.1.1-1) beginning:
Module zfs-2.1.1 for kernel 5.14.18-200.fc34.x86_64 (x86_64).
This module version was INACTIVE for this kernel.
depmod.....
Deleting module zfs-2.1.1 completely from the DKMS tree.

...

Upgraded:
  libnvpair3-2.1.2-1.fc34.x86_64    libuutil3-2.1.2-1.fc34.x86_64
  libzpool5-2.1.2-1.fc34.x86_64     zfs-2.1.2-1.fc34.x86_64
  libzfs5-2.1.2-1.fc34.x86_64       zfs-dkms-2.1.2-1.fc34.noarch

Complete!
[INFO] __main__: Upgrading all the packages...
Last metadata expiration check: 1:09:04 ago on Sun 19 Dec 2021 09:34:10 PM PST.
Dependencies resolved.
=============================================================================
 Package                Architecture Version             Repository     Size
=============================================================================
Installing:
 kernel                 x86_64       5.15.8-100.fc34     updates        14 k
 kernel-core            x86_64       5.15.8-100.fc34     updates        35 M
 kernel-devel           x86_64       5.15.8-100.fc34     updates        15 M
 kernel-modules         x86_64       5.15.8-100.fc34     updates        32 M
 kernel-modules-extra   x86_64       5.15.8-100.fc34     updates       2.0 M
Upgrading:
 ImageMagick            x86_64       1:6.9.12.32-1.fc34  updates       164 k
...
Removing:
 kernel                 x86_64       5.14.16-201.fc34    @updates        0
 kernel-core            x86_64       5.14.16-201.fc34    @updates       76 M
 kernel-devel           x86_64       5.14.16-201.fc34    @updates       60 M
 kernel-modules         x86_64       5.14.16-201.fc34    @updates       31 M
 kernel-modules-extra   x86_64       5.14.16-201.fc34    @updates      1.9 M

Transaction Summary
=============================================================================
Install   6 Packages
Upgrade  81 Packages
Remove    5 Packages

Total download size: 464 M
Is this ok [y/N]: y
Downloading Packages:
...
Running transaction
...

dkms: running auto installation service for kernel 5.15.8-100.fc34.x86_64

Kernel preparation unnecessary for this kernel. Skipping...

Running the pre_build script:
...

Building module:
cleaning build area....
make -j12 KERNELRELEASE=5.15.8-100.fc34.x86_64.............

Running the post_build script:
cleaning build area....

zavl.ko.xz:
Running module version sanity check.
 - Original module
   - No original module exists within this kernel
 - Installation
   - Installing to /lib/modules/5.15.8-100.fc34.x86_64/extra/

znvpair.ko.xz:
Running module version sanity check.
 - Original module
   - No original module exists within this kernel
 - Installation
   - Installing to /lib/modules/5.15.8-100.fc34.x86_64/extra/

...

depmod.....
 Done.
dkms: running auto installation service for kernel 5.15.8-100.fc34.x86_64
 Done.

...

Upgraded:
...
Installed:
  kernel-5.15.8-100.fc34.x86_64
  kernel-devel-5.15.8-100.fc34.x86_64
  kernel-modules-extra-5.15.8-100.fc34.x86_64
  kernel-core-5.15.8-100.fc34.x86_64
  kernel-modules-5.15.8-100.fc34.x86_64

Removed:
  kernel-5.14.16-201.fc34.x86_64
  kernel-devel-5.14.16-201.fc34.x86_64
  kernel-modules-extra-5.14.16-201.fc34.x86_64
  kernel-core-5.14.16-201.fc34.x86_64
  kernel-modules-5.14.16-201.fc34.x86_64

Complete!
```

## Compatibility

Tested on Fedora 34. But it should work on any distro with `dnf` (e.g. CentOS).
