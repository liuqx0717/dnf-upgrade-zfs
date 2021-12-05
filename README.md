# Auto upgrade ZFS packages on Fedora

Installing OpenZFS on Fedora is easy ([instructions](
https://openzfs.github.io/openzfs-docs/Getting%20Started/Fedora/index.html)),
but *upgrading* the packages can be cumbersome.

The ZFS kernel modules are managed by dkms on Fedora. Sometimes running `dnf
upgrade` may cause issues, because the newest kernel on Fedora might be not
yet supported by OpenZFS. Also it's suggested that zfs packages should be
upgraded *before* kernel upgrades (see [this comment on GitHub](
https://github.com/openzfs/zfs/issues/9891#issuecomment-761979624)).

This little script is aimed to eliminate all the laborious manual work and do
the upgrades **just in one shot**.

## Steps involved in this script

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
  DNFOPTS        additional options for dnf, e.g. dnf-upgrade-zfs.py -- -y

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  verbose mode

```

Examples:

```
# By default the user's confirmation is required before doing any upgrades
sudo ./dnf-upgrade-zfs.py

# Do the upgrades directly (by passing -y to dnf)
sudo ./dnf-upgrade-zfs.py -- -y
```

Sample output:

```
$ sudo ./dnf-upgrade-zfs.py -- -y
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

## Compatibility

Tested on Fedora 34. But it should work on any distro with `dnf` (e.g. CentOS).
